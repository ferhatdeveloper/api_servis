# Logo ERP Module

This module provides direct integration with Logo ERP systems (Tiger, Go3, etc.).

## Components
- **ERP**: Core ERP operations (Orders, Invoices) (`erp.py`).
- **Data**: Master data synchronization (Items, Clients) (`data.py`).

## Configuration
Requires `LOGO_DB` settings in `config.py` or environment variables.
Supports `DirectDB` (SQL) and `Objects` (COM) modes.
