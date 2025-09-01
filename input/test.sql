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
END;
GO


CREATE PROCEDURE sp_process_order
    @OrderID INT,
    @Threshold NUMERIC(10,2)
AS
BEGIN
    DECLARE @OrderTotal NUMERIC(10,2)
    DECLARE @Status VARCHAR(20)

    SELECT @OrderTotal = SUM(Amount)
    FROM OrderItems
    WHERE OrderID = @OrderID

    IF @OrderTotal IS NULL
    BEGIN
        SET @Status = 'Order Not Found'
    END
    ELSE IF @OrderTotal >= @Threshold
    BEGIN
        SET @Status = 'High Value'
    END
    ELSE
    BEGIN
        SET @Status = 'Normal'
    END

    INSERT INTO OrderAudit (OrderID, Status, CheckedAt)
    VALUES (@OrderID, @Status, GETDATE())

    SELECT @OrderID AS OrderID, @OrderTotal AS Total, @Status AS Status
END
GO


CREATE PROCEDURE sp_print_customer_orders
    @CustomerID INT
AS
BEGIN
    DECLARE @OrderID INT, @OrderDate DATETIME, @Total NUMERIC(10,2)

    DECLARE order_cursor CURSOR FOR
        SELECT OrderID, OrderDate, Total
        FROM Orders
        WHERE CustomerID = @CustomerID

    OPEN order_cursor
    FETCH NEXT FROM order_cursor INTO @OrderID, @OrderDate, @Total

    WHILE @@FETCH_STATUS = 0
    BEGIN
        PRINT 'Order: ' + CAST(@OrderID AS VARCHAR) + ', Date: ' + CAST(@OrderDate AS VARCHAR) + ', Total: ' + CAST(@Total AS VARCHAR)
        FETCH NEXT FROM order_cursor INTO @OrderID, @OrderDate, @Total
    END

    CLOSE order_cursor
    DEALLOCATE order_cursor
END
GO


CREATE PROCEDURE sp_calculate_bonus
    @EmployeeID INT,
    @Year INT
AS
BEGIN
    DECLARE @Sales NUMERIC(12,2)
    DECLARE @Bonus NUMERIC(12,2)

    SELECT @Sales = SUM(Amount)
    FROM Sales
    WHERE EmployeeID = @EmployeeID AND YEAR(SaleDate) = @Year

    IF @Sales IS NULL
    BEGIN
        RAISERROR('No sales found for employee', 16, 1)
        RETURN 0
    END
    ELSE IF @Sales > 100000
    BEGIN
        SET @Bonus = @Sales * 0.10
    END
    ELSE IF @Sales > 50000
    BEGIN
        SET @Bonus = @Sales * 0.05
    END
    ELSE
    BEGIN
        SET @Bonus = 0
    END

    RETURN @Bonus
END
GO