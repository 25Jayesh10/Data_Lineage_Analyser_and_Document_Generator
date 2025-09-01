-----------------------------
-- Table Setup
-----------------------------
CREATE TABLE Inventory (
    ItemID INT PRIMARY KEY,
    ItemName VARCHAR(100),
    Quantity INT,
    ReorderLevel INT,
    LastUpdated DATETIME DEFAULT GETDATE()
);

CREATE TABLE PurchaseOrders (
    POID INT PRIMARY KEY,
    ItemID INT,
    Quantity INT,
    OrderDate DATETIME DEFAULT GETDATE(),
    Status VARCHAR(20)
);

CREATE TABLE AuditTrail (
    AuditID INT IDENTITY PRIMARY KEY,
    EventType VARCHAR(50),
    Details VARCHAR(200),
    CreatedAt DATETIME DEFAULT GETDATE()
);

-----------------------------
-- Base Procedures
-----------------------------
-- Generic logger
CREATE PROCEDURE usp_WriteAudit
    @eventType VARCHAR(50),
    @details VARCHAR(200)
AS
BEGIN
    INSERT INTO AuditTrail(EventType, Details)
    VALUES(@eventType, @details);
END;
GO

-- Creates a purchase order
CREATE PROCEDURE usp_CreatePurchaseOrder
    @itemId INT,
    @quantity INT
AS
BEGIN
    INSERT INTO PurchaseOrders(ItemID, Quantity, Status)
    VALUES(@itemId, @quantity, 'OPEN');

    EXEC usp_WriteAudit 'PURCHASE_ORDER',
        'PO created for Item ' + CONVERT(VARCHAR, @itemId) + ', Qty ' + CONVERT(VARCHAR, @quantity);
END;
GO

-- Reorders inventory if needed
CREATE PROCEDURE usp_ReorderInventory
    @itemId INT
AS
BEGIN
    DECLARE @qty INT, @reorderLevel INT;

    SELECT @qty = Quantity, @reorderLevel = ReorderLevel
    FROM Inventory WHERE ItemID = @itemId;

    IF @qty < @reorderLevel
    BEGIN
        EXEC usp_CreatePurchaseOrder @itemId, (@reorderLevel - @qty);
        EXEC usp_WriteAudit 'REORDER',
            'Item ' + CONVERT(VARCHAR, @itemId) + ' triggered reorder.';
    END
    ELSE
    BEGIN
        EXEC usp_WriteAudit 'REORDER_CHECK',
            'Item ' + CONVERT(VARCHAR, @itemId) + ' sufficient stock.';
    END
END;
GO

-- Master procedure that calls other procedures
CREATE PROCEDURE usp_ProcessInventoryUpdate
    @itemId INT,
    @adjustment INT
AS
BEGIN
    UPDATE Inventory
    SET Quantity = Quantity + @adjustment,
        LastUpdated = GETDATE()
    WHERE ItemID = @itemId;

    EXEC usp_WriteAudit 'INVENTORY_UPDATE',
        'Item ' + CONVERT(VARCHAR, @itemId) + ' adjusted by ' + CONVERT(VARCHAR, @adjustment);

    -- Nested call: reorder check inside update
    EXEC usp_ReorderInventory @itemId;
END;
GO

-----------------------------
-- Functions
-----------------------------
-- Function that calls a procedure
CREATE FUNCTION fn_GetStockLevelWithAudit(@itemId INT)
RETURNS INT
AS
BEGIN
    DECLARE @qty INT;
    SELECT @qty = Quantity FROM Inventory WHERE ItemID = @itemId;

    EXEC usp_WriteAudit 'FUNCTION_CALL',
        'fn_GetStockLevelWithAudit called for Item ' + CONVERT(VARCHAR, @itemId);

    RETURN @qty;
END;
GO

-- Function that calls another function and procedure
CREATE FUNCTION fn_CheckStockHealth(@itemId INT)
RETURNS VARCHAR(20)
AS
BEGIN
    DECLARE @qty INT, @status VARCHAR(20);

    SET @qty = dbo.fn_GetStockLevelWithAudit(@itemId);

    IF @qty < 10
    BEGIN
        SET @status = 'LOW';
        EXEC usp_WriteAudit 'STOCK_HEALTH',
            'Item ' + CONVERT(VARCHAR, @itemId) + ' flagged as LOW';
    END
    ELSE
    BEGIN
        SET @status = 'OK';
        EXEC usp_WriteAudit 'STOCK_HEALTH',
            'Item ' + CONVERT(VARCHAR, @itemId) + ' flagged as OK';
    END

    RETURN @status;
END;
GO

-- Function that nests multiple calls
CREATE FUNCTION fn_GetInventoryReport(@itemId INT)
RETURNS VARCHAR(200)
AS
BEGIN
    DECLARE @qty INT, @health VARCHAR(20), @report VARCHAR(200);

    SET @qty = dbo.fn_GetStockLevelWithAudit(@itemId);
    SET @health = dbo.fn_CheckStockHealth(@itemId);

    SET @report = 'Item ' + CONVERT(VARCHAR, @itemId) +
                  ' | Qty: ' + CONVERT(VARCHAR, @qty) +
                  ' | Health: ' + @health;

    EXEC usp_WriteAudit 'REPORT',
        'Report generated for Item ' + CONVERT(VARCHAR, @itemId);

    RETURN @report;
END;
GO

-----------------------------
-- Triggers
-----------------------------
-- Trigger with nested calls (proc + functions)
CREATE TRIGGER trg_AfterInventoryUpdate
ON Inventory
AFTER UPDATE
AS
BEGIN
    DECLARE @itemId INT, @report VARCHAR(200);

    SELECT @itemId = ItemID FROM INSERTED;

    -- Call master procedure
    EXEC usp_ProcessInventoryUpdate @itemId, 0;

    -- Call nested functions
    SET @report = dbo.fn_GetInventoryReport(@itemId);

    -- Log via procedure
    EXEC usp_WriteAudit 'TRIGGER',
        'Inventory updated for Item ' + CONVERT(VARCHAR, @itemId) + ' | ' + @report;
END;
GO

-- Trigger on PurchaseOrders to cascade
CREATE TRIGGER trg_AfterPurchaseOrderInsert
ON PurchaseOrders
AFTER INSERT
AS
BEGIN
    DECLARE @itemId INT, @qty INT;

    SELECT @itemId = ItemID, @qty = Quantity FROM INSERTED;

    EXEC usp_WriteAudit 'PO_TRIGGER',
        'Trigger fired for new PO of Item ' + CONVERT(VARCHAR, @itemId) +
        ', Qty ' + CONVERT(VARCHAR, @qty);

    -- Call stock health check inside trigger
    DECLARE @status VARCHAR(20);
    SET @status = dbo.fn_CheckStockHealth(@itemId);

    EXEC usp_WriteAudit 'PO_TRIGGER_HEALTH',
        'Item ' + CONVERT(VARCHAR, @itemId) + ' health status in PO trigger: ' + @status;
END;
GO
