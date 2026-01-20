"""
Cost Accounting API Endpoints
FIFO Inventory Valuation & Profitability Analysis

@created: 2024-12-18
@author: ExRetailOS Team
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

from retail.core.database import get_db
from retail.models.product import Product
from retail.models.customer import Customer

router = APIRouter()


# ============================================================================
# FIFO LAYERS MANAGEMENT
# ============================================================================

@router.post("/fifo/consume")
async def consume_fifo_stock(
    product_id: str,
    quantity: float,
    firma_id: str,
    donem_id: str,
    db: Session = Depends(get_db)
):
    """
    Consume stock using FIFO method
    Returns: total_cost, consumed_layers[]
    """
    try:
        # Query FIFO layers ordered by date (FIFO)
        query = """
            SELECT id, quantity, unit_cost, remaining_quantity
            FROM fifo_layers
            WHERE product_code = :product_id
              AND firma_id = :firma_id
              AND donem_id = :donem_id
              AND remaining_quantity > 0
            ORDER BY created_at ASC
        """
        
        result = db.execute(query, {
            "product_id": product_id,
            "firma_id": firma_id,
            "donem_id": donem_id
        })
        
        layers = result.fetchall()
        
        if not layers:
            raise HTTPException(
                status_code=400,
                detail=f"No FIFO layers available for product {product_id}"
            )
        
        total_cost = Decimal('0')
        consumed_layers = []
        remaining_qty = Decimal(str(quantity))
        
        for layer in layers:
            if remaining_qty <= 0:
                break
            
            layer_id = layer[0]
            layer_qty = Decimal(str(layer[2]))
            unit_cost = Decimal(str(layer[3]))
            layer_remaining = Decimal(str(layer[4]))
            
            # Calculate how much to consume from this layer
            consume_qty = min(remaining_qty, layer_remaining)
            layer_cost = consume_qty * unit_cost
            
            total_cost += layer_cost
            remaining_qty -= consume_qty
            
            # Update layer remaining quantity
            new_remaining = layer_remaining - consume_qty
            update_query = """
                UPDATE fifo_layers
                SET remaining_quantity = :new_remaining,
                    updated_at = NOW()
                WHERE id = :layer_id
            """
            db.execute(update_query, {
                "new_remaining": float(new_remaining),
                "layer_id": layer_id
            })
            
            consumed_layers.append({
                "layer_id": layer_id,
                "quantity": float(consume_qty),
                "unit_cost": float(unit_cost),
                "total_cost": float(layer_cost)
            })
        
        db.commit()
        
        if remaining_qty > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Missing: {float(remaining_qty)} units"
            )
        
        return {
            "success": True,
            "total_cost": float(total_cost),
            "consumed_layers": consumed_layers,
            "consumed_quantity": quantity
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fifo/add-layer")
async def add_fifo_layer(
    product_code: str,
    product_name: str,
    quantity: float,
    unit_cost: float,
    firma_id: str,
    donem_id: str,
    supplier_id: Optional[str] = None,
    invoice_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Add new FIFO layer (stock IN)
    """
    try:
        query = """
            INSERT INTO fifo_layers (
                product_code, product_name, quantity, unit_cost,
                remaining_quantity, firma_id, donem_id,
                supplier_id, invoice_id, created_at, updated_at
            ) VALUES (
                :product_code, :product_name, :quantity, :unit_cost,
                :quantity, :firma_id, :donem_id,
                :supplier_id, :invoice_id, NOW(), NOW()
            )
            RETURNING id
        """
        
        result = db.execute(query, {
            "product_code": product_code,
            "product_name": product_name,
            "quantity": quantity,
            "unit_cost": unit_cost,
            "firma_id": firma_id,
            "donem_id": donem_id,
            "supplier_id": supplier_id,
            "invoice_id": invoice_id
        })
        
        layer_id = result.fetchone()[0]
        db.commit()
        
        return {
            "success": True,
            "layer_id": layer_id,
            "message": "FIFO layer added successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fifo/layers/{product_id}")
async def get_fifo_layers(
    product_id: str,
    firma_id: str = Query(...),
    donem_id: str = Query(...),
    include_consumed: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Get FIFO layers for a product
    """
    try:
        where_clause = "WHERE product_code = :product_id AND firma_id = :firma_id AND donem_id = :donem_id"
        
        if not include_consumed:
            where_clause += " AND remaining_quantity > 0"
        
        query = f"""
            SELECT 
                id, product_code, product_name, quantity, unit_cost,
                remaining_quantity, supplier_id, invoice_id,
                created_at, updated_at
            FROM fifo_layers
            {where_clause}
            ORDER BY created_at ASC
        """
        
        result = db.execute(query, {
            "product_id": product_id,
            "firma_id": firma_id,
            "donem_id": donem_id
        })
        
        layers = []
        total_value = Decimal('0')
        total_remaining = Decimal('0')
        
        for row in result:
            remaining_qty = Decimal(str(row[5]))
            unit_cost = Decimal(str(row[4]))
            layer_value = remaining_qty * unit_cost
            
            total_remaining += remaining_qty
            total_value += layer_value
            
            layers.append({
                "id": row[0],
                "product_code": row[1],
                "product_name": row[2],
                "quantity": float(row[3]),
                "unit_cost": float(row[4]),
                "remaining_quantity": float(row[5]),
                "supplier_id": row[6],
                "invoice_id": row[7],
                "created_at": row[8].isoformat() if row[8] else None,
                "updated_at": row[9].isoformat() if row[9] else None,
                "layer_value": float(layer_value)
            })
        
        avg_cost = float(total_value / total_remaining) if total_remaining > 0 else 0
        
        return {
            "success": True,
            "layers": layers,
            "summary": {
                "total_layers": len(layers),
                "total_remaining_quantity": float(total_remaining),
                "total_value": float(total_value),
                "average_cost": avg_cost
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STOCK MOVEMENTS
# ============================================================================

@router.post("/stock-movements/record")
async def record_stock_movement(
    product_code: str,
    product_name: str,
    quantity: float,
    movement_type: str,  # IN or OUT
    unit_price: Optional[float] = None,
    unit_cost: Optional[float] = None,
    total_price: Optional[float] = None,
    total_cost: Optional[float] = None,
    firma_id: str = Query(...),
    donem_id: str = Query(...),
    invoice_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    supplier_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Record stock movement (IN/OUT)
    """
    try:
        query = """
            INSERT INTO stock_movements (
                product_code, product_name, quantity, movement_type,
                unit_price, unit_cost, total_price, total_cost,
                firma_id, donem_id, invoice_id, customer_id, supplier_id,
                movement_date, created_at
            ) VALUES (
                :product_code, :product_name, :quantity, :movement_type,
                :unit_price, :unit_cost, :total_price, :total_cost,
                :firma_id, :donem_id, :invoice_id, :customer_id, :supplier_id,
                NOW(), NOW()
            )
            RETURNING id
        """
        
        result = db.execute(query, {
            "product_code": product_code,
            "product_name": product_name,
            "quantity": quantity,
            "movement_type": movement_type,
            "unit_price": unit_price,
            "unit_cost": unit_cost,
            "total_price": total_price,
            "total_cost": total_cost,
            "firma_id": firma_id,
            "donem_id": donem_id,
            "invoice_id": invoice_id,
            "customer_id": customer_id,
            "supplier_id": supplier_id
        })
        
        movement_id = result.fetchone()[0]
        db.commit()
        
        return {
            "success": True,
            "movement_id": movement_id,
            "message": "Stock movement recorded successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock-movements")
async def get_stock_movements(
    firma_id: str = Query(...),
    donem_id: str = Query(...),
    product_code: Optional[str] = None,
    movement_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """
    Get stock movements with filters
    """
    try:
        where_clauses = ["firma_id = :firma_id", "donem_id = :donem_id"]
        params = {"firma_id": firma_id, "donem_id": donem_id}
        
        if product_code:
            where_clauses.append("product_code = :product_code")
            params["product_code"] = product_code
        
        if movement_type:
            where_clauses.append("movement_type = :movement_type")
            params["movement_type"] = movement_type
        
        if start_date:
            where_clauses.append("movement_date >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            where_clauses.append("movement_date <= :end_date")
            params["end_date"] = end_date
        
        where_clause = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                id, product_code, product_name, quantity, movement_type,
                unit_price, unit_cost, total_price, total_cost,
                invoice_id, customer_id, supplier_id, movement_date
            FROM stock_movements
            WHERE {where_clause}
            ORDER BY movement_date DESC
            LIMIT :limit OFFSET :offset
        """
        
        params["limit"] = limit
        params["offset"] = offset
        
        result = db.execute(query, params)
        
        movements = []
        for row in result:
            movements.append({
                "id": row[0],
                "product_code": row[1],
                "product_name": row[2],
                "quantity": float(row[3]),
                "movement_type": row[4],
                "unit_price": float(row[5]) if row[5] else None,
                "unit_cost": float(row[6]) if row[6] else None,
                "total_price": float(row[7]) if row[7] else None,
                "total_cost": float(row[8]) if row[8] else None,
                "invoice_id": row[9],
                "customer_id": row[10],
                "supplier_id": row[11],
                "movement_date": row[12].isoformat() if row[12] else None
            })
        
        return {
            "success": True,
            "movements": movements,
            "count": len(movements)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROFITABILITY ANALYSIS
# ============================================================================

@router.get("/profitability/product/{product_id}")
async def get_product_profitability(
    product_id: str,
    firma_id: str = Query(...),
    donem_id: str = Query(...),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get profitability analysis for a product
    """
    try:
        where_clause = """
            WHERE product_code = :product_id
              AND firma_id = :firma_id
              AND donem_id = :donem_id
              AND movement_type = 'OUT'
        """
        
        params = {
            "product_id": product_id,
            "firma_id": firma_id,
            "donem_id": donem_id
        }
        
        if start_date:
            where_clause += " AND movement_date >= :start_date"
            params["start_date"] = start_date
        
        if end_date:
            where_clause += " AND movement_date <= :end_date"
            params["end_date"] = end_date
        
        query = f"""
            SELECT 
                SUM(quantity) as total_quantity,
                SUM(total_price) as total_revenue,
                SUM(total_cost) as total_cost,
                AVG(unit_price) as avg_unit_price,
                AVG(unit_cost) as avg_unit_cost,
                COUNT(*) as transaction_count
            FROM stock_movements
            {where_clause}
        """
        
        result = db.execute(query, params).fetchone()
        
        if not result or not result[0]:
            return {
                "success": True,
                "product_id": product_id,
                "profitability": None,
                "message": "No sales data found"
            }
        
        total_quantity = Decimal(str(result[0])) if result[0] else Decimal('0')
        total_revenue = Decimal(str(result[1])) if result[1] else Decimal('0')
        total_cost = Decimal(str(result[2])) if result[2] else Decimal('0')
        avg_unit_price = Decimal(str(result[3])) if result[3] else Decimal('0')
        avg_unit_cost = Decimal(str(result[4])) if result[4] else Decimal('0')
        transaction_count = result[5] if result[5] else 0
        
        gross_profit = total_revenue - total_cost
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        
        return {
            "success": True,
            "product_id": product_id,
            "profitability": {
                "total_quantity_sold": float(total_quantity),
                "total_revenue": float(total_revenue),
                "total_cost": float(total_cost),
                "gross_profit": float(gross_profit),
                "profit_margin": float(profit_margin),
                "avg_unit_price": float(avg_unit_price),
                "avg_unit_cost": float(avg_unit_cost),
                "transaction_count": transaction_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profitability/customer/{customer_id}")
async def get_customer_profitability(
    customer_id: str,
    firma_id: str = Query(...),
    donem_id: str = Query(...),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get profitability analysis for a customer
    """
    try:
        where_clause = """
            WHERE customer_id = :customer_id
              AND firma_id = :firma_id
              AND donem_id = :donem_id
              AND movement_type = 'OUT'
        """
        
        params = {
            "customer_id": customer_id,
            "firma_id": firma_id,
            "donem_id": donem_id
        }
        
        if start_date:
            where_clause += " AND movement_date >= :start_date"
            params["start_date"] = start_date
        
        if end_date:
            where_clause += " AND movement_date <= :end_date"
            params["end_date"] = end_date
        
        query = f"""
            SELECT 
                COUNT(DISTINCT invoice_id) as transaction_count,
                SUM(quantity) as total_quantity,
                SUM(total_price) as total_revenue,
                SUM(total_cost) as total_cost
            FROM stock_movements
            {where_clause}
        """
        
        result = db.execute(query, params).fetchone()
        
        if not result or not result[0]:
            return {
                "success": True,
                "customer_id": customer_id,
                "profitability": None,
                "message": "No sales data found"
            }
        
        transaction_count = result[0] if result[0] else 0
        total_quantity = Decimal(str(result[1])) if result[1] else Decimal('0')
        total_revenue = Decimal(str(result[2])) if result[2] else Decimal('0')
        total_cost = Decimal(str(result[3])) if result[3] else Decimal('0')
        
        gross_profit = total_revenue - total_cost
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        avg_transaction_value = total_revenue / transaction_count if transaction_count > 0 else Decimal('0')
        
        return {
            "success": True,
            "customer_id": customer_id,
            "profitability": {
                "transaction_count": transaction_count,
                "total_quantity": float(total_quantity),
                "total_revenue": float(total_revenue),
                "total_cost": float(total_cost),
                "gross_profit": float(gross_profit),
                "profit_margin": float(profit_margin),
                "avg_transaction_value": float(avg_transaction_value)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profitability/summary")
async def get_profitability_summary(
    firma_id: str = Query(...),
    donem_id: str = Query(...),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get overall profitability summary
    """
    try:
        where_clause = """
            WHERE firma_id = :firma_id
              AND donem_id = :donem_id
              AND movement_type = 'OUT'
        """
        
        params = {
            "firma_id": firma_id,
            "donem_id": donem_id
        }
        
        if start_date:
            where_clause += " AND movement_date >= :start_date"
            params["start_date"] = start_date
        
        if end_date:
            where_clause += " AND movement_date <= :end_date"
            params["end_date"] = end_date
        
        # Overall summary
        query = f"""
            SELECT 
                COUNT(DISTINCT invoice_id) as total_transactions,
                COUNT(DISTINCT product_code) as total_products,
                COUNT(DISTINCT customer_id) as total_customers,
                SUM(quantity) as total_quantity,
                SUM(total_price) as total_revenue,
                SUM(total_cost) as total_cost
            FROM stock_movements
            {where_clause}
        """
        
        result = db.execute(query, params).fetchone()
        
        total_transactions = result[0] if result[0] else 0
        total_products = result[1] if result[1] else 0
        total_customers = result[2] if result[2] else 0
        total_quantity = Decimal(str(result[3])) if result[3] else Decimal('0')
        total_revenue = Decimal(str(result[4])) if result[4] else Decimal('0')
        total_cost = Decimal(str(result[5])) if result[5] else Decimal('0')
        
        gross_profit = total_revenue - total_cost
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        avg_transaction_value = total_revenue / total_transactions if total_transactions > 0 else Decimal('0')
        
        return {
            "success": True,
            "summary": {
                "total_transactions": total_transactions,
                "total_products": total_products,
                "total_customers": total_customers,
                "total_quantity": float(total_quantity),
                "total_revenue": float(total_revenue),
                "total_cost": float(total_cost),
                "gross_profit": float(gross_profit),
                "profit_margin": float(profit_margin),
                "avg_transaction_value": float(avg_transaction_value)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
