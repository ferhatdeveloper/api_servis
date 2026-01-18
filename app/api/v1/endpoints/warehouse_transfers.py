from fastapi import APIRouter, HTTPException
from loguru import logger
from app.core.database import db_manager
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# =====================================================
# SCHEMAS
# =====================================================

class TransferLine(BaseModel):
    line_number: int
    item_code: str
    item_name: str
    quantity: float
    unit_code: Optional[str]
    unit_name: Optional[str]
    unit_price: Optional[float]
    total_price: Optional[float]
    currency: Optional[str] = 'TRY'
    serial_numbers: Optional[List[str]]
    lot_number: Optional[str]
    notes: Optional[str]

class TransferCreate(BaseModel):
    user_id: int
    from_warehouse_id: int
    to_warehouse_id: int
    transfer_date: Optional[str]
    notes: Optional[str]
    lines: List[TransferLine]

class Transfer(BaseModel):
    id: int
    transfer_number: str
    user_id: int
    from_warehouse_id: int
    to_warehouse_id: int
    transfer_date: str
    status: str
    notes: Optional[str]
    logo_ref: Optional[int]
    synced_to_logo: bool

# =====================================================
# ENDPOINTS
# =====================================================

@router.post("/transfers")
async def create_transfer(transfer: TransferCreate):
    """
    Create a new warehouse transfer
    
    Creates a transfer document with lines.
    """
    try:
        # Validate warehouses are different
        if transfer.from_warehouse_id == transfer.to_warehouse_id:
            raise HTTPException(
                status_code=400,
                detail="Source and destination warehouses must be different"
            )
        
        # Create transfer header
        transfer_date = transfer.transfer_date or datetime.now().isoformat()
        
        header_query = f"""
            INSERT INTO warehouse_transfers (
                user_id, from_warehouse_id, to_warehouse_id, 
                transfer_date, notes, status
            )
            VALUES (
                {transfer.user_id},
                {transfer.from_warehouse_id},
                {transfer.to_warehouse_id},
                '{transfer_date}',
                '{transfer.notes or ''}',
                'pending'
            )
            RETURNING id, transfer_number
        """
        
        result = db_manager.execute_pg_query(header_query)
        transfer_id = result[0]['id']
        transfer_number = result[0]['transfer_number']
        
        # Create transfer lines
        for line in transfer.lines:
            line_query = f"""
                INSERT INTO warehouse_transfer_lines (
                    transfer_id, line_number, item_code, item_name,
                    quantity, unit_code, unit_name, unit_price, 
                    total_price, currency, lot_number, notes
                )
                VALUES (
                    {transfer_id},
                    {line.line_number},
                    '{line.item_code}',
                    '{line.item_name.replace("'", "''")}',
                    {line.quantity},
                    '{line.unit_code or ''}',
                    '{line.unit_name or ''}',
                    {line.unit_price or 0},
                    {line.total_price or 0},
                    '{line.currency}',
                    '{line.lot_number or ''}',
                    '{line.notes or ''}'
                )
            """
            db_manager.execute_pg_query(line_query)
        
        return {
            "success": True,
            "message": "Transfer created successfully",
            "transfer_id": transfer_id,
            "transfer_number": transfer_number
        }
        
    except Exception as e:
        logger.error(f"Create transfer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transfers")
async def get_transfers(
    user_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """
    Get warehouse transfers
    
    Filters:
    - user_id: Filter by user
    - warehouse_id: Filter by source or destination warehouse
    - status: Filter by status (pending, approved, completed, cancelled)
    """
    try:
        where_clauses = []
        
        if user_id:
            where_clauses.append(f"user_id = {user_id}")
        
        if warehouse_id:
            where_clauses.append(
                f"(from_warehouse_id = {warehouse_id} OR to_warehouse_id = {warehouse_id})"
            )
        
        if status:
            where_clauses.append(f"status = '{status}'")
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
            SELECT 
                t.id,
                t.transfer_number,
                t.user_id,
                t.from_warehouse_id,
                wf.name as from_warehouse_name,
                t.to_warehouse_id,
                wt.name as to_warehouse_name,
                t.transfer_date::text,
                t.status,
                t.notes,
                t.logo_ref,
                t.synced_to_logo,
                t.created_at::text
            FROM warehouse_transfers t
            JOIN warehouses wf ON wf.id = t.from_warehouse_id
            JOIN warehouses wt ON wt.id = t.to_warehouse_id
            WHERE {where_sql}
            ORDER BY t.transfer_date DESC
            LIMIT {limit}
        """
        
        results = db_manager.execute_pg_query(query)
        return {
            "success": True,
            "count": len(results),
            "transfers": results
        }
        
    except Exception as e:
        logger.error(f"Get transfers error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transfers/{transfer_id}")
async def get_transfer_detail(transfer_id: int):
    """
    Get transfer detail with lines
    """
    try:
        # Get header
        header_query = f"""
            SELECT 
                t.id,
                t.transfer_number,
                t.user_id,
                u.full_name as user_name,
                t.from_warehouse_id,
                wf.code as from_warehouse_code,
                wf.name as from_warehouse_name,
                t.to_warehouse_id,
                wt.code as to_warehouse_code,
                wt.name as to_warehouse_name,
                t.transfer_date::text,
                t.status,
                t.notes,
                t.logo_ref,
                t.synced_to_logo,
                t.approved_by,
                t.approved_at::text,
                t.created_at::text
            FROM warehouse_transfers t
            JOIN users u ON u.id = t.user_id
            JOIN warehouses wf ON wf.id = t.from_warehouse_id
            JOIN warehouses wt ON wt.id = t.to_warehouse_id
            WHERE t.id = {transfer_id}
        """
        
        header = db_manager.execute_pg_query(header_query)
        
        if not header:
            raise HTTPException(status_code=404, detail="Transfer not found")
        
        # Get lines
        lines_query = f"""
            SELECT 
                line_number,
                item_code,
                item_name,
                quantity,
                unit_code,
                unit_name,
                unit_price,
                total_price,
                currency,
                serial_numbers,
                lot_number,
                notes
            FROM warehouse_transfer_lines
            WHERE transfer_id = {transfer_id}
            ORDER BY line_number
        """
        
        lines = db_manager.execute_pg_query(lines_query)
        
        return {
            "success": True,
            "transfer": {
                **header[0],
                "lines": lines
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get transfer detail error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transfers/{transfer_id}/approve")
async def approve_transfer(transfer_id: int, approved_by: int):
    """
    Approve a transfer
    
    Changes status from pending to approved.
    """
    try:
        query = f"""
            UPDATE warehouse_transfers
            SET status = 'approved',
                approved_by = {approved_by},
                approved_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = {transfer_id} AND status = 'pending'
            RETURNING id, transfer_number, status
        """
        
        result = db_manager.execute_pg_query(query)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Transfer not found or already processed"
            )
        
        return {
            "success": True,
            "message": "Transfer approved",
            "transfer": result[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approve transfer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transfers/{transfer_id}/complete")
async def complete_transfer(transfer_id: int):
    """
    Mark transfer as completed
    
    Changes status from approved to completed.
    """
    try:
        query = f"""
            UPDATE warehouse_transfers
            SET status = 'completed',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = {transfer_id} AND status = 'approved'
            RETURNING id, transfer_number, status
        """
        
        result = db_manager.execute_pg_query(query)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Transfer not found or not approved"
            )
        
        return {
            "success": True,
            "message": "Transfer completed",
            "transfer": result[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete transfer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transfers/{transfer_id}/cancel")
async def cancel_transfer(transfer_id: int):
    """
    Cancel a transfer
    
    Only pending transfers can be cancelled.
    """
    try:
        query = f"""
            UPDATE warehouse_transfers
            SET status = 'cancelled',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = {transfer_id} AND status = 'pending'
            RETURNING id, transfer_number, status
        """
        
        result = db_manager.execute_pg_query(query)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Transfer not found or cannot be cancelled"
            )
        
        return {
            "success": True,
            "message": "Transfer cancelled",
            "transfer": result[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel transfer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/transfers/{transfer_id}")
async def delete_transfer(transfer_id: int):
    """
    Delete a transfer
    
    Only pending or cancelled transfers can be deleted.
    """
    try:
        query = f"""
            DELETE FROM warehouse_transfers
            WHERE id = {transfer_id} 
              AND status IN ('pending', 'cancelled')
            RETURNING id, transfer_number
        """
        
        result = db_manager.execute_pg_query(query)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Transfer not found or cannot be deleted"
            )
        
        return {
            "success": True,
            "message": "Transfer deleted",
            "transfer_number": result[0]['transfer_number']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete transfer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transfers/stats/summary")
async def get_transfer_stats(warehouse_id: Optional[int] = None):
    """
    Get transfer statistics
    
    Returns counts by status and warehouse.
    """
    try:
        where_sql = f"WHERE (from_warehouse_id = {warehouse_id} OR to_warehouse_id = {warehouse_id})" if warehouse_id else ""
        
        query = f"""
            SELECT 
                status,
                COUNT(*) as count,
                SUM(CASE WHEN from_warehouse_id = {warehouse_id or 0} THEN 1 ELSE 0 END) as outgoing,
                SUM(CASE WHEN to_warehouse_id = {warehouse_id or 0} THEN 1 ELSE 0 END) as incoming
            FROM warehouse_transfers
            {where_sql}
            GROUP BY status
        """
        
        results = db_manager.execute_pg_query(query)
        
        return {
            "success": True,
            "stats": results
        }
        
    except Exception as e:
        logger.error(f"Get transfer stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
