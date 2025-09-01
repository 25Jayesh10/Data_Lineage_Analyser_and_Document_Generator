-----------------------------
-- Table Setup
-----------------------------
CREATE TABLE Orders (
    OrderID INT PRIMARY KEY,
    ClientID INT,
    OrderDate DATETIME,
    Amount DECIMAL(18,2),
    Status VARCHAR(20)
);

CREATE TABLE AuditLog (
    LogID INT IDENTITY PRIMARY KEY,
    EventType VARCHAR(50),
    EventMessage VARCHAR(200),
    CreatedAt DATETIME DEFAULT GETDATE()
);

-----------------------------
-- Base Procedures
-----------------------------
-- Logs an audit event
CREATE PROCEDURE usp_LogEvent
    @eventType VARCHAR(50),
    @message VARCHAR(200)
AS
BEGIN
    INSERT INTO AuditLog(EventType, EventMessage)
    VALUES (@eventType, @message);
END;
GO

-- Updates order status and logs it
CREATE PROCEDURE usp_UpdateOrderStatus
    @orderId INT,
    @newStatus VARCHAR(20)
AS
BEGIN
    UPDATE Orders
    SET Status = @newStatus
    WHERE OrderID = @orderId;

    EXEC usp_LogEvent 'ORDER_UPDATE', 
         'Order ' + CONVERT(VARCHAR, @orderId) + ' status changed to ' + @newStatus;
END;
GO

-- Procedure that calls another procedure
CREATE PROCEDURE usp_CloseOrder
    @orderId INT
AS
BEGIN
    -- Calls usp_UpdateOrderStatus
    EXEC usp_UpdateOrderStatus @orderId, 'CLOSED';
END;
GO

-----------------------------
-- Functions
-----------------------------
-- Function calls a procedure
CREATE FUNCTION fn_GetOrderTotalWithAudit(@orderId INT)
RETURNS DECIMAL(18,2)
AS
BEGIN
    DECLARE @amount DECIMAL(18,2);

    SELECT @amount = Amount FROM Orders WHERE OrderID = @orderId;

    -- Call a procedure from function (allowed in Sybase with workaround: procedure returns value into variable)
    EXEC usp_LogEvent 'FUNCTION_CALL', 
         'fn_GetOrderTotalWithAudit called for Order ' + CONVERT(VARCHAR, @orderId);

    RETURN @amount;
END;
GO

-- Function calls another function
CREATE FUNCTION fn_GetOrderWithTax(@orderId INT)
RETURNS DECIMAL(18,2)
AS
BEGIN
    DECLARE @baseAmount DECIMAL(18,2);
    DECLARE @withTax DECIMAL(18,2);

    SET @baseAmount = dbo.fn_GetOrderTotalWithAudit(@orderId);
    SET @withTax = @baseAmount * 1.1; -- 10% tax
    RETURN @withTax;
END;
GO

-----------------------------
-- Triggers
-----------------------------
-- Trigger that calls a procedure and a function
CREATE TRIGGER trg_AfterInsertOrder
ON Orders
AFTER INSERT
AS
BEGIN
    DECLARE @orderId INT, @amount DECIMAL(18,2);

    SELECT @orderId = OrderID, @amount = Amount FROM INSERTED;

    -- Call procedure
    EXEC usp_LogEvent 'TRIGGER_INSERT', 
         'New order ' + CONVERT(VARCHAR, @orderId) + ' inserted with amount ' + CONVERT(VARCHAR, @amount);

    -- Call function inside trigger
    DECLARE @totalWithTax DECIMAL(18,2);
    SET @totalWithTax = dbo.fn_GetOrderWithTax(@orderId);

    EXEC usp_LogEvent 'TRIGGER_FUNCTION_CALL', 
         'Order ' + CONVERT(VARCHAR, @orderId) + ' total with tax: ' + CONVERT(VARCHAR, @totalWithTax);
END;
GO
