------------------------------------------------------------
-- FUNCTIONS
------------------------------------------------------------
-- Scalar function: calculates tax for an amount
CREATE FUNCTION AcmeERP.fn_CalculateTax (@Amount NUMERIC(12,2))
RETURNS NUMERIC(12,2)
AS
BEGIN
    RETURN @Amount * 0.15; -- 15% tax
END;
GO

-- Scalar function: gets order total and calls fn_CalculateTax
CREATE FUNCTION AcmeERP.fn_GetOrderTotalWithTax (@OrderID INT)
RETURNS NUMERIC(12,2)
AS
BEGIN
    DECLARE @BaseTotal NUMERIC(12,2), @WithTax NUMERIC(12,2);

    SELECT @BaseTotal = SUM(Amount) FROM OrderItems WHERE OrderID = @OrderID;

    IF @BaseTotal IS NULL
        RETURN 0;

    SET @WithTax = @BaseTotal + AcmeERP.fn_CalculateTax(@BaseTotal);

    RETURN @WithTax;
END;
GO

-- Table-valued function: returns all high-value orders
CREATE FUNCTION AcmeERP.fn_GetHighValueOrders (@Threshold NUMERIC(12,2))
RETURNS TABLE
AS
RETURN
    SELECT o.OrderID, o.CustomerID, o.OrderDate, SUM(oi.Amount) AS Total
    FROM Orders o
    JOIN OrderItems oi ON o.OrderID = oi.OrderID
    GROUP BY o.OrderID, o.CustomerID, o.OrderDate
    HAVING SUM(oi.Amount) > @Threshold;
GO

------------------------------------------------------------
-- STORED PROCEDURES
------------------------------------------------------------
-- Logs an audit entry
CREATE PROCEDURE AcmeERP.usp_LogAudit
    @Entity VARCHAR(50),
    @EntityID INT,
    @Message VARCHAR(200)
AS
BEGIN
    INSERT INTO AuditLog(Entity, EntityID, Message, CreatedAt)
    VALUES (@Entity, @EntityID, @Message, GETDATE());
END;
GO

-- Calculates FIFO cost (calls LogAudit)
CREATE PROCEDURE AcmeERP.usp_CalculateFifoCost
    @ProductID INT,
    @QuantityRequested INT
AS
BEGIN
    WITH CTE_FIFO AS (
        SELECT 
            MovementID,
            ProductID,
            Quantity,
            UnitCost,
            SUM(Quantity) OVER (PARTITION BY ProductID ORDER BY MovementDate ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS RunningTotal
        FROM AcmeERP.StockMovements
        WHERE ProductID = @ProductID AND Direction = 'IN'
    )
    SELECT AVG(UnitCost) AS FifoCostEstimate
    FROM CTE_FIFO
    WHERE RunningTotal <= @QuantityRequested;

    EXEC AcmeERP.usp_LogAudit 'Product', @ProductID, 'FIFO cost calculated';
END;
GO

-- Processes an order (calls function + LogAudit)
CREATE PROCEDURE AcmeERP.usp_ProcessOrder
    @OrderID INT,
    @Threshold NUMERIC(10,2)
AS
BEGIN
    DECLARE @OrderTotal NUMERIC(12,2), @Status VARCHAR(20);

    SET @OrderTotal = AcmeERP.fn_GetOrderTotalWithTax(@OrderID);

    IF @OrderTotal = 0
        SET @Status = 'Not Found';
    ELSE IF @OrderTotal >= @Threshold
        SET @Status = 'High Value';
    ELSE
        SET @Status = 'Normal';

    INSERT INTO OrderAudit (OrderID, Status, CheckedAt)
    VALUES (@OrderID, @Status, GETDATE());

    EXEC AcmeERP.usp_LogAudit 'Order', @OrderID, 'Order processed with status: ' + @Status;

    SELECT @OrderID AS OrderID, @OrderTotal AS Total, @Status AS Status;
END;
GO

-- Cursor example: prints customer orders
CREATE PROCEDURE AcmeERP.usp_PrintCustomerOrders
    @CustomerID INT
AS
BEGIN
    DECLARE @OrderID INT, @OrderDate DATETIME, @Total NUMERIC(12,2);

    DECLARE order_cursor CURSOR FOR
        SELECT OrderID, OrderDate, dbo.fn_GetOrderTotalWithTax(OrderID) AS Total
        FROM Orders
        WHERE CustomerID = @CustomerID;

    OPEN order_cursor;
    FETCH NEXT FROM order_cursor INTO @OrderID, @OrderDate, @Total;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        PRINT 'Order: ' + CAST(@OrderID AS VARCHAR) + ', Date: ' 
              + CAST(@OrderDate AS VARCHAR) + ', Total (with tax): ' + CAST(@Total AS VARCHAR);

        FETCH NEXT FROM order_cursor INTO @OrderID, @OrderDate, @Total;
    END;

    CLOSE order_cursor;
    DEALLOCATE order_cursor;
END;
GO

-- Bonus calculation with nested proc calls
CREATE PROCEDURE AcmeERP.usp_CalculateBonus
    @EmployeeID INT,
    @Year INT
AS
BEGIN
    DECLARE @Sales NUMERIC(12,2), @Bonus NUMERIC(12,2);

    SELECT @Sales = SUM(Amount)
    FROM Sales
    WHERE EmployeeID = @EmployeeID AND YEAR(SaleDate) = @Year;

    IF @Sales IS NULL
    BEGIN
        RAISERROR('No sales found for employee', 16, 1);
        RETURN 0;
    END
    ELSE IF @Sales > 100000
        SET @Bonus = @Sales * 0.10;
    ELSE IF @Sales > 50000
        SET @Bonus = @Sales * 0.05;
    ELSE
        SET @Bonus = 0;

    EXEC AcmeERP.usp_LogAudit 'Employee', @EmployeeID, 'Bonus calculated';

    RETURN @Bonus;
END;
GO

------------------------------------------------------------
-- TRIGGERS
------------------------------------------------------------
-- Trigger after order insert: calls procedure + function
CREATE TRIGGER trg_AfterInsertOrder
ON Orders
AFTER INSERT
AS
BEGIN
    DECLARE @OrderID INT, @TotalWithTax NUMERIC(12,2);

    SELECT @OrderID = OrderID FROM INSERTED;

    SET @TotalWithTax = AcmeERP.fn_GetOrderTotalWithTax(@OrderID);

    EXEC AcmeERP.usp_LogAudit 'Order', @OrderID, 
         'New order inserted. Total with tax: ' + CAST(@TotalWithTax AS VARCHAR);
END;
GO

-- Trigger after stock movement: calls FIFO procedure
CREATE TRIGGER trg_AfterStockMovement
ON StockMovements
AFTER INSERT
AS
BEGIN
    DECLARE @ProductID INT, @Qty INT;

    SELECT @ProductID = ProductID, @Qty = Quantity FROM INSERTED;

    -- Call FIFO cost calculation procedure
    EXEC AcmeERP.usp_CalculateFifoCost @ProductID, @Qty;
END;
GO
