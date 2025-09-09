# Summary

- **Total Procedures**: 4
- **Total Functions**: 3
- **Total Triggers**: 2
- **Total Tables**: 3
- **Most Called Object**: `usp_WriteAudit`

---

# Table of Contents

- Procedure: [usp_WriteAudit](#usp_writeaudit)
- Procedure: [usp_CreatePurchaseOrder](#usp_createpurchaseorder)
- Procedure: [usp_ReorderInventory](#usp_reorderinventory)
- Procedure: [usp_ProcessInventoryUpdate](#usp_processinventoryupdate)
- Function: [fn_GetStockLevelWithAudit](#fn_getstocklevelwithaudit)
- Function: [fn_CheckStockHealth](#fn_checkstockhealth)
- Function: [fn_GetInventoryReport](#fn_getinventoryreport)
- Trigger: [trg_AfterInventoryUpdate](#trg_afterinventoryupdate)
- Trigger: [trg_AfterPurchaseOrderInsert](#trg_afterpurchaseorderinsert)

---

## Procedure: usp_WriteAudit
<a name="usp_writeaudit"></a>

---

### Parameters

| Name | Type |
|------|------|
| @eventType | VARCHAR(50) |
| @details | VARCHAR(200) |

---

### Tables

- AuditTrail

---

### Calls


---

### Call Graph

```mermaid
graph TD
    usp_WriteAudit --> AuditTrail
```

---

### Business Logic

Description could not be generated due to an OpenRouter API error: 401 Client Error: Unauthorized for url: https://openrouter.ai/api/v1/chat/completions

---


## Procedure: usp_CreatePurchaseOrder
<a name="usp_createpurchaseorder"></a>

---

### Parameters

| Name | Type |
|------|------|
| @itemId | INT |
| @quantity | INT |

---

### Tables

- PurchaseOrders

---

### Calls

- usp_WriteAudit

---

### Call Graph

```mermaid
graph TD
    usp_CreatePurchaseOrder --> usp_WriteAudit
    usp_CreatePurchaseOrder --> PurchaseOrders
```

---

### Business Logic

Description could not be generated due to an OpenRouter API error: 401 Client Error: Unauthorized for url: https://openrouter.ai/api/v1/chat/completions

---


## Procedure: usp_ReorderInventory
<a name="usp_reorderinventory"></a>

---

### Parameters

| Name | Type |
|------|------|
| @itemId | INT |

---

### Tables

- Inventory

---

### Calls

- usp_CreatePurchaseOrder
- usp_WriteAudit

---

### Call Graph

```mermaid
graph TD
    usp_ReorderInventory --> usp_CreatePurchaseOrder
    usp_ReorderInventory --> usp_WriteAudit
    usp_ReorderInventory --> Inventory
```

---

### Business Logic

Description could not be generated due to an OpenRouter API error: 401 Client Error: Unauthorized for url: https://openrouter.ai/api/v1/chat/completions

---


## Procedure: usp_ProcessInventoryUpdate
<a name="usp_processinventoryupdate"></a>

---

### Parameters

| Name | Type |
|------|------|
| @itemId | INT |
| @adjustment | INT |

---

### Tables

- Inventory

---

### Calls

- usp_WriteAudit
- usp_ReorderInventory

---

### Call Graph

```mermaid
graph TD
    usp_ProcessInventoryUpdate --> usp_WriteAudit
    usp_ProcessInventoryUpdate --> usp_ReorderInventory
    usp_ProcessInventoryUpdate --> Inventory
```

---

### Business Logic

Description could not be generated due to an OpenRouter API error: 401 Client Error: Unauthorized for url: https://openrouter.ai/api/v1/chat/completions

---


## Function: fn_GetStockLevelWithAudit
<a name="fn_getstocklevelwithaudit"></a>

---

### Parameters

| Name | Type |
|------|------|
| @itemId | INT |

---

### Tables

- Inventory

---

### Calls

- usp_WriteAudit

---

### Call Graph

```mermaid
graph TD
    fn_GetStockLevelWithAudit --> usp_WriteAudit
    fn_GetStockLevelWithAudit --> Inventory
```

---

### Business Logic

Description could not be generated due to an OpenRouter API error: 401 Client Error: Unauthorized for url: https://openrouter.ai/api/v1/chat/completions

---


## Function: fn_CheckStockHealth
<a name="fn_checkstockhealth"></a>

---

### Parameters

| Name | Type |
|------|------|
| @itemId | INT |

---

### Tables


---

### Calls

- dbo.fn_GetStockLevelWithAudit
- usp_WriteAudit

---

### Call Graph

```mermaid
graph TD
    fn_CheckStockHealth --> dbo.fn_GetStockLevelWithAudit
    fn_CheckStockHealth --> usp_WriteAudit
```

---

### Business Logic

Description could not be generated due to an OpenRouter API error: 401 Client Error: Unauthorized for url: https://openrouter.ai/api/v1/chat/completions

---


## Function: fn_GetInventoryReport
<a name="fn_getinventoryreport"></a>

---

### Parameters

| Name | Type |
|------|------|
| @itemId | INT |

---

### Tables


---

### Calls

- dbo.fn_GetStockLevelWithAudit
- dbo.fn_CheckStockHealth
- usp_WriteAudit

---

### Call Graph

```mermaid
graph TD
    fn_GetInventoryReport --> dbo.fn_GetStockLevelWithAudit
    fn_GetInventoryReport --> dbo.fn_CheckStockHealth
    fn_GetInventoryReport --> usp_WriteAudit
```

---

### Business Logic

Description could not be generated due to an OpenRouter API error: 401 Client Error: Unauthorized for url: https://openrouter.ai/api/v1/chat/completions

---


## Trigger: trg_AfterInventoryUpdate
<a name="trg_afterinventoryupdate"></a>

---

### Tables


---

### Calls

- usp_ProcessInventoryUpdate
- dbo.fn_GetInventoryReport
- usp_WriteAudit

---

### Call Graph

```mermaid
graph TD
    trg_AfterInventoryUpdate --> usp_ProcessInventoryUpdate
    trg_AfterInventoryUpdate --> dbo.fn_GetInventoryReport
    trg_AfterInventoryUpdate --> usp_WriteAudit
```

---

### Business Logic

Description could not be generated due to an OpenRouter API error: 401 Client Error: Unauthorized for url: https://openrouter.ai/api/v1/chat/completions

---


## Trigger: trg_AfterPurchaseOrderInsert
<a name="trg_afterpurchaseorderinsert"></a>

---

### Tables


---

### Calls

- usp_WriteAudit
- dbo.fn_CheckStockHealth

---

### Call Graph

```mermaid
graph TD
    trg_AfterPurchaseOrderInsert --> usp_WriteAudit
    trg_AfterPurchaseOrderInsert --> dbo.fn_CheckStockHealth
```

---

### Business Logic

Description could not be generated due to an OpenRouter API error: 401 Client Error: Unauthorized for url: https://openrouter.ai/api/v1/chat/completions

---

