from fastapi import APIRouter
from app.core.database import db_manager

router = APIRouter()

@router.get("/customers")
async def get_customers():
    query = "SELECT * FROM customers ORDER BY name"
    return db_manager.execute_pg_query(query)

@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    query = "SELECT * FROM customers WHERE id = %s"
    return db_manager.execute_pg_query(query, (customer_id,))
