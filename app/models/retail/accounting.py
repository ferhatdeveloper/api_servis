from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class JournalEntryHeader(BaseModel):
    fiche_no: str
    date: str
    fiche_type: int
    description: Optional[str] = None
    doc_no: Optional[str] = None
    total_debit: float
    total_credit: float
    branch_id: Optional[int] = None
    idempotency_key: Optional[str] = None

class JournalEntryLine(BaseModel):
    account_ref: int
    line_nr: int
    description: Optional[str] = None
    amount: float
    sign: int
    branch_id: Optional[int] = None

class JournalEntryPayload(BaseModel):
    firmNr: int
    periodNr: int
    header: JournalEntryHeader
    lines: List[JournalEntryLine]

class TrialBalanceResult(BaseModel):
    account_code: str
    account_name: str
    debit_total: float
    credit_total: float
    balance_debit: float
    balance_credit: float
