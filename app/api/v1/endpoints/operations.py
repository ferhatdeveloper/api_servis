from fastapi import APIRouter, HTTPException
from app.core.database import db_manager
from pydantic import BaseModel
from typing import List

router = APIRouter()

class OrderLine(BaseModel):
    product_id: str
    quantity: float
    price: float

class OrderCreate(BaseModel):
    customer_id: str
    salesman_id: str
    items: List[OrderLine]

@router.post("/orders")
async def create_order(order: OrderCreate):
    # This would involve complex transaction handling
    # 1. Insert into sales_orders
    # 2. Insert into sales_order_lines
    return {"status": "success", "order_id": "new_order_uuid"}

@router.get("/visits")
async def get_visits(salesman_id: str = None):
    query = "SELECT * FROM field_visits"
    if salesman_id:
        query += f" WHERE salesman_id = '{salesman_id}'"
    return db_manager.execute_pg_query(query)
