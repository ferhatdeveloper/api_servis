from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime
from retail.core.database import get_db
from retail.models.accounting import JournalEntryPayload, TrialBalanceResult

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check for accounting DB"""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "accounting"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.post("/journal", status_code=status.HTTP_201_CREATED)
async def create_journal_entry(payload: JournalEntryPayload, db: AsyncSession = Depends(get_db)):
    """
    Saves a journal entry to the database (Idempotent)
    """
    firm_nr = payload.firmNr
    period_nr = payload.periodNr
    prefix = f"FN_{firm_nr:03d}_{period_nr:02d}"
    
    header = payload.header
    t_header = f"{prefix}_EMUHFICHE"
    t_lines = f"{prefix}_EMUHLINE"
    
    # Query for header
    query_header = text(f"""
        INSERT INTO "public"."{t_header}" 
        (fiche_no, date, fiche_type, description, doc_no, total_debit, total_credit, branch_id, idempotency_key)
        VALUES (:fiche_no, :date, :fiche_type, :description, :doc_no, :total_debit, :total_credit, :branch_id, :idempotency_key)
        RETURNING logicalref
    """)
    
    try:
        # 1. Insert Header
        result = await db.execute(
            query_header,
            {
                "fiche_no": header.fiche_no,
                "date": header.date,
                "fiche_type": header.fiche_type,
                "description": header.description,
                "doc_no": header.doc_no,
                "total_debit": header.total_debit,
                "total_credit": header.total_credit,
                "branch_id": header.branch_id,
                "idempotency_key": header.idempotency_key
            }
        )
        header_ref = result.scalar()
        
        # 2. Insert Lines
        query_line = text(f"""
            INSERT INTO "public"."{t_lines}"
            (fiche_ref, account_ref, line_nr, description, amount, sign, date, branch_id)
            VALUES (:fiche_ref, :account_ref, :line_nr, :description, :amount, :sign, :date, :branch_id)
        """)
        
        for index, line in enumerate(payload.lines):
            await db.execute(
                query_line,
                {
                    "fiche_ref": header_ref,
                    "account_ref": line.account_ref,
                    "line_nr": index + 1,
                    "description": line.description,
                    "amount": line.amount,
                    "sign": line.sign,
                    "date": header.date,
                    "branch_id": line.branch_id
                }
            )
        
        await db.commit()
        return {"status": "success", "message": "Journal Entry Saved", "logicalref": header_ref}
        
    except Exception as e:
        await db.rollback()
        # Check if it was a unique violation (asyncpg specific check would be needed for direct asyncpg, 
        # but here we might get a generic error from sqlalchemy)
        if "idempotency_key" in str(e).lower() and "unique" in str(e).lower():
             return {"status": "success", "message": "Already processed (Idempotent)", "duplicate": True}
        
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trial-balance")
async def get_trial_balance(firmNr: int, periodNr: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves the Trial Balance (Mizan) using the DB function
    """
    try:
        query = text("SELECT * FROM get_trial_balance(:firm_nr, :period_nr)")
        result = await db.execute(query, {"firm_nr": f"{firmNr:03d}", "period_nr": f"{periodNr:02d}"})
        rows = result.fetchall()
        
        return {
            "status": "success", 
            "data": [dict(row._mapping) for row in rows]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize")
async def optimize_db(db: AsyncSession = Depends(get_db)):
    """Triggers database optimization"""
    try:
        await db.execute(text("SELECT optimize_database();"))
        await db.commit()
        return {"status": "success", "message": "Database optimization triggered."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
