# Retail Integration Module (RetailOS)

This module integrates the RetailOS ecosystem capabilities into the main EXFIN API.

## Structure
- **Auth**: Retail-specific auth checks (re-uses core users).
- **Sales**: POS and Sales operations.
- **Products & Customers**: Master data management for retail.
- **Ecommerce**: Integration with external platforms.
- **AI Reports**: OpenAI-powered reporting analysis.

## Note
These endpoints were originally part of a separate microservice but are now fully integrated. 
Configuration settings are merged into `app/core/config.py`.
