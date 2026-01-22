# Core Module

This module contains the foundational components of the EXFIN OPS API.

## Components
- **Auth**: Unified JWT Authentication (`auth.py`). Handled by `app/core/security_jwt.py`.
- **System**: System management, updates, and backups (`system.py`).
- **Database**: Database management utilities (`database.py`).
- **Companies**: Company and period definitions (`companies.py`).

## Usage
All endpoints are prefixed with their respective domain (e.g., `/auth`, `/system`).
Authentication is required for most endpoints.
