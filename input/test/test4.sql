---------------------------------------------------
-- TABLES
---------------------------------------------------
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY,
    CustomerName VARCHAR(100),
    Status VARCHAR(20),
    CreditLimit DECIMAL(10,2),
    Balance DECIMAL(10,2)
);

CREATE TABLE Orders (
    OrderID INT PRIMARY KEY,
    CustomerID INT,
    OrderDate DATETIME DEFAULT GETDATE(),
    Amount DECIMAL(10,2),
    Status VARCHAR(20)
);

CREATE TABLE Shipments (
    ShipmentID INT PRIMARY KEY,
    OrderID INT,
    ShipDate DATETIME,
    Carrier VARCHAR(50)
);

CREATE TABLE AuditTrail (
    AuditID INT IDENTITY PRIMARY KEY,
    EventType VARCHAR(50),
    Details VARCHAR(500),
    CreatedAt DATETIME DEFAULT GETDATE()
);

---------------------------------------------------
-- BASE PROCEDURE: Logger
---------------------------------------------------
CREATE PROCEDURE usp_LogEvent
    @eventType VARCHAR(50),
    @details VARCHAR(500)
AS
BEGIN
    INSERT INTO AuditTrail(EventType, Details)
    VALUES(@eventType, @details);
END;
GO

---------------------------------------------------
-- NESTED PROCEDURES
---------------------------------------------------
-- Shipment creation
CREATE PROCEDURE usp_CreateShipment
    @orderId INT,
    @carrier VARCHAR(50)
AS
BEGIN
    INSERT INTO Shipments(OrderID, ShipDate, Carrier)
    VALUES(@orderId, GETDATE(), @carrier);

    EXEC usp_LogEvent 'SHIPMENT',
        'Shipment created for Order ' + CONVERT(VARCHAR, @orderId);
END;
GO

-- Order finalization
CREATE PROCEDURE usp_FinalizeOrder
    @orderId INT
AS
BEGIN
    UPDATE Orders
    SET Status = 'FINALIZED'
    WHERE OrderID = @orderId;

    EXEC usp_CreateShipment @orderId, 'FedEx';
    EXEC usp_LogEvent 'ORDER',
        'Order ' + CONVERT(VARCHAR, @orderId) + ' finalized and shipment created';
END;
GO

-- Customer credit validation
CREATE PROCEDURE usp_ValidateCustomerCredit
    @customerId INT,
    @amount DECIMAL(10,2)
AS
BEGIN
    DECLARE @balance DECIMAL(10,2), @limit DECIMAL(10,2);

    SELECT @balance = Balance, @limit = CreditLimit
    FROM Customers WHERE CustomerID = @customerId;

    IF (@balance + @amount) > @limit
    BEGIN
        EXEC usp_LogEvent 'CREDIT_FAIL',
            'Customer ' + CONVERT(VARCHAR, @customerId) + ' exceeded credit limit';
        RAISERROR('Credit limit exceeded', 16, 1);
    END
    ELSE
    BEGIN
        EXEC usp_LogEvent 'CREDIT_OK',
            'Customer ' + CONVERT(VARCHAR, @customerId) + ' within credit limit';
    END
END;
GO

-- Master procedure: place an order
CREATE PROCEDURE usp_PlaceOrder
    @customerId INT,
    @amount DECIMAL(10,2)
AS
BEGIN
    BEGIN TRY
        BEGIN TRANSACTION;

        EXEC usp_ValidateCustomerCredit @customerId, @amount;

        DECLARE @orderId INT;
        SELECT @orderId = ISNULL(MAX(OrderID), 0) + 1 FROM Orders;

        INSERT INTO Orders(OrderID, CustomerID, Amount, Status)
        VALUES(@orderId, @customerId, @amount, 'NEW');

        EXEC usp_FinalizeOrder @orderId;

        COMMIT TRANSACTION;

        EXEC usp_LogEvent 'ORDER_PLACED',
            'Order ' + CONVERT(VARCHAR, @orderId) +
            ' placed for Customer ' + CONVERT(VARCHAR, @customerId);
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        EXEC usp_LogEvent 'ORDER_FAIL',
            'Order placement failed for Customer ' + CONVERT(VARCHAR, @customerId);
    END CATCH
END;
GO

---------------------------------------------------
-- FUNCTIONS (nested + calling procs)
---------------------------------------------------
-- Function with embedded procedure call
CREATE FUNCTION fn_GetCustomerBalanceWithAudit(@customerId INT)
RETURNS DECIMAL(10,2)
AS
BEGIN
    DECLARE @balance DECIMAL(10,2);

    SELECT @balance = Balance FROM Customers WHERE CustomerID = @customerId;

    EXEC usp_LogEvent 'FUNC_CALL',
        'fn_GetCustomerBalanceWithAudit for Customer ' + CONVERT(VARCHAR, @customerId);

    RETURN @balance;
END;
GO

-- Function chaining other function + procedure
CREATE FUNCTION fn_GetCreditStatus(@customerId INT)
RETURNS VARCHAR(20)
AS
BEGIN
    DECLARE @balance DECIMAL(10,2),
            @limit DECIMAL(10,2),
            @status VARCHAR(20);

    SET @balance = dbo.fn_GetCustomerBalanceWithAudit(@customerId);
    SELECT @limit = CreditLimit FROM Customers WHERE CustomerID = @customerId;

    IF @balance > @limit
    BEGIN
        SET @status = 'OVER_LIMIT';
        EXEC usp_LogEvent 'CREDIT_STATUS',
            'Customer ' + CONVERT(VARCHAR, @customerId) + ' is over limit';
    END
    ELSE
    BEGIN
        SET @status = 'OK';
        EXEC usp_LogEvent 'CREDIT_STATUS',
            'Customer ' + CONVERT(VARCHAR, @customerId) + ' is within limit';
    END

    RETURN @status;
END;
GO

-- Reporting function that nests both
CREATE FUNCTION fn_GetCustomerReport(@customerId INT)
RETURNS VARCHAR(500)
AS
BEGIN
    DECLARE @balance DECIMAL(10,2),
            @status VARCHAR(20),
            @report VARCHAR(500);

    SET @balance = dbo.fn_GetCustomerBalanceWithAudit(@customerId);
    SET @status = dbo.fn_GetCreditStatus(@customerId);

    SET @report = 'Customer ' + CONVERT(VARCHAR, @customerId) +
                  ' | Balance: ' + CONVERT(VARCHAR, @balance) +
                  ' | Credit Status: ' + @status;

    EXEC usp_LogEvent 'REPORT',
        'Generated report for Customer ' + CONVERT(VARCHAR, @customerId);

    RETURN @report;
END;
GO

---------------------------------------------------
-- TRIGGERS (deeply nested calls)
---------------------------------------------------
-- Trigger on Orders
CREATE TRIGGER trg_AfterOrderInsert
ON Orders
AFTER INSERT
AS
BEGIN
    DECLARE @orderId INT, @custId INT, @amount DECIMAL(10,2);

    SELECT @orderId = OrderID, @custId = CustomerID, @amount = Amount FROM INSERTED;

    EXEC usp_LogEvent 'TRIGGER_ORDER',
        'Order Insert Trigger fired for Order ' + CONVERT(VARCHAR, @orderId);

    -- Call procedure chain
    EXEC usp_FinalizeOrder @orderId;

    -- Call function chain
    DECLARE @report VARCHAR(500);
    SET @report = dbo.fn_GetCustomerReport(@custId);

    EXEC usp_LogEvent 'TRIGGER_REPORT',
        'Report in trigger: ' + @report;
END;
GO

-- Trigger on Shipments
CREATE TRIGGER trg_AfterShipmentInsert
ON Shipments
AFTER INSERT
AS
BEGIN
    DECLARE @shipId INT, @orderId INT;

    SELECT @shipId = ShipmentID, @orderId = OrderID FROM INSERTED;

    EXEC usp_LogEvent 'TRIGGER_SHIPMENT',
        'Shipment Trigger fired for Shipment ' + CONVERT(VARCHAR, @shipId);

    -- Cascade: trigger calls function which calls procedure
    DECLARE @custId INT;
    SELECT @custId = CustomerID FROM Orders WHERE OrderID = @orderId;

    DECLARE @status VARCHAR(20);
    SET @status = dbo.fn_GetCreditStatus(@custId);

    EXEC usp_LogEvent 'TRIGGER_CREDIT',
        'Customer ' + CONVERT(VARCHAR, @custId) + ' status after shipment: ' + @status;
END;
GO
