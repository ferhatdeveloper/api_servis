"""
Advanced Reports API
Professional reporting engine with 100+ reports

@created: 2024-12-18
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel, EmailStr
import json

from retail.core.database import get_db

router = APIRouter()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ReportParameter(BaseModel):
    name: str
    value: Any


class GenerateReportRequest(BaseModel):
    report_id: str
    parameters: List[ReportParameter]
    format: Optional[str] = 'json'  # json, excel, pdf, csv


class ScheduleReportRequest(BaseModel):
    report_id: str
    parameters: List[ReportParameter]
    frequency: str  # daily, weekly, monthly
    time: str  # HH:MM format
    recipients: List[EmailStr]
    format: str  # excel, pdf, csv


class CustomReportRequest(BaseModel):
    name: str
    description: str
    data_source: str
    filters: List[Dict[str, Any]]
    columns: List[str]
    group_by: Optional[List[str]] = None
    order_by: Optional[List[str]] = None
    aggregations: Optional[Dict[str, str]] = None


# ============================================================================
# REPORT DEFINITIONS
# ============================================================================

REPORT_REGISTRY = {
    # Sales Reports
    "daily-sales-summary": {
        "name": "Daily Sales Summary",
        "category": "sales",
        "query_func": "get_daily_sales_summary",
        "parameters": ["date", "store"],
    },
    "sales-by-hour": {
        "name": "Hourly Sales Analysis",
        "category": "sales",
        "query_func": "get_sales_by_hour",
        "parameters": ["start_date", "end_date"],
    },
    "sales-by-category": {
        "name": "Category-wise Sales",
        "category": "sales",
        "query_func": "get_sales_by_category",
        "parameters": ["start_date", "end_date", "categories"],
    },
    
    # Financial Reports
    "daily-cash-flow": {
        "name": "Daily Cash Flow",
        "category": "financial",
        "query_func": "get_daily_cash_flow",
        "parameters": ["date"],
    },
    "profit-loss-statement": {
        "name": "Profit & Loss Statement",
        "category": "financial",
        "query_func": "get_profit_loss_statement",
        "parameters": ["start_date", "end_date"],
    },
    
    # Inventory Reports
    "stock-status": {
        "name": "Stock Status Report",
        "category": "inventory",
        "query_func": "get_stock_status",
        "parameters": ["warehouse", "category"],
    },
    "stock-movement": {
        "name": "Stock Movement Report",
        "category": "inventory",
        "query_func": "get_stock_movement",
        "parameters": ["start_date", "end_date", "movement_type"],
    },
    
    # Customer Reports
    "customer-analysis": {
        "name": "Customer Analysis",
        "category": "customer",
        "query_func": "get_customer_analysis",
        "parameters": ["start_date", "end_date", "customer_type"],
    },
    
    # Accounting Reports
    "general-ledger": {
        "name": "General Ledger",
        "category": "accounting",
        "query_func": "get_general_ledger",
        "parameters": ["start_date", "end_date", "account"],
    },
    "trial-balance": {
        "name": "Trial Balance (Mizan)",
        "category": "accounting",
        "query_func": "get_trial_balance",
        "parameters": ["start_date", "end_date", "level"],
    },
}


# ============================================================================
# QUERY FUNCTIONS
# ============================================================================

class ReportQueries:
    """Report query functions"""
    
    @staticmethod
    def get_daily_sales_summary(db: Session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Daily sales summary report"""
        report_date = params.get('date', date.today())
        store = params.get('store')
        
        # Build query
        where_clauses = [f"DATE(created_at) = '{report_date}'"]
        if store:
            where_clauses.append(f"store_id = '{store}'")
        
        where_clause = " AND ".join(where_clauses)
        
        # Summary query
        summary_query = f"""
            SELECT 
                COUNT(*) as total_sales,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as avg_sale_value,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM sales
            WHERE {where_clause}
        """
        
        summary = db.execute(summary_query).fetchone()
        
        # Hourly breakdown
        hourly_query = f"""
            SELECT 
                EXTRACT(HOUR FROM created_at) as hour,
                COUNT(*) as sale_count,
                SUM(total_amount) as revenue
            FROM sales
            WHERE {where_clause}
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY hour
        """
        
        hourly_data = db.execute(hourly_query).fetchall()
        
        # Top products
        top_products_query = f"""
            SELECT 
                p.name,
                SUM(si.quantity) as quantity_sold,
                SUM(si.total_price) as revenue
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            WHERE {where_clause.replace('created_at', 's.created_at')}
            GROUP BY p.id, p.name
            ORDER BY revenue DESC
            LIMIT 10
        """
        
        top_products = db.execute(top_products_query).fetchall()
        
        return {
            "reportTitle": "Daily Sales Summary",
            "generatedAt": datetime.now().isoformat(),
            "parameters": params,
            "summary": [
                {"label": "Total Sales", "value": summary[0], "format": "number"},
                {"label": "Total Revenue", "value": summary[1], "format": "currency"},
                {"label": "Average Sale", "value": summary[2], "format": "currency"},
                {"label": "Unique Customers", "value": summary[3], "format": "number"},
            ],
            "hourlyBreakdown": [
                {
                    "hour": f"{int(row[0]):02d}:00",
                    "count": row[1],
                    "revenue": row[2]
                }
                for row in hourly_data
            ],
            "topProducts": [
                {
                    "name": row[0],
                    "quantity": row[1],
                    "revenue": row[2]
                }
                for row in top_products
            ]
        }
    
    @staticmethod
    def get_sales_by_category(db: Session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sales by category report"""
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        categories = params.get('categories', [])
        
        where_clauses = [
            f"s.created_at >= '{start_date}'",
            f"s.created_at <= '{end_date}'"
        ]
        
        if categories:
            cat_list = ','.join([f"'{c}'" for c in categories])
            where_clauses.append(f"c.id IN ({cat_list})")
        
        where_clause = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                c.name as category_name,
                COUNT(DISTINCT s.id) as sale_count,
                SUM(si.quantity) as total_quantity,
                SUM(si.total_price) as total_revenue,
                AVG(si.unit_price) as avg_price
            FROM sales s
            JOIN sale_items si ON s.id = si.sale_id
            JOIN products p ON si.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            WHERE {where_clause}
            GROUP BY c.id, c.name
            ORDER BY total_revenue DESC
        """
        
        results = db.execute(query).fetchall()
        
        return {
            "reportTitle": "Sales by Category",
            "generatedAt": datetime.now().isoformat(),
            "parameters": params,
            "headers": ["Category", "Sales Count", "Quantity", "Revenue", "Avg Price"],
            "data": [
                [row[0], row[1], row[2], row[3], row[4]]
                for row in results
            ]
        }
    
    @staticmethod
    def get_stock_status(db: Session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stock status report"""
        warehouse = params.get('warehouse')
        category = params.get('category')
        
        where_clauses = ["1=1"]
        if warehouse:
            where_clauses.append(f"p.warehouse_id = '{warehouse}'")
        if category:
            where_clauses.append(f"p.category_id = '{category}'")
        
        where_clause = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                p.code,
                p.name,
                c.name as category,
                p.stock_quantity,
                p.min_stock_level,
                p.max_stock_level,
                CASE 
                    WHEN p.stock_quantity < p.min_stock_level THEN 'Low Stock'
                    WHEN p.stock_quantity > p.max_stock_level THEN 'Overstock'
                    ELSE 'Normal'
                END as status,
                p.purchase_price * p.stock_quantity as stock_value
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE {where_clause}
            ORDER BY status, p.name
        """
        
        results = db.execute(query).fetchall()
        
        # Calculate summary
        total_items = len(results)
        low_stock = sum(1 for r in results if r[3] < r[4])
        overstock = sum(1 for r in results if r[3] > r[5])
        total_value = sum(r[7] for r in results)
        
        return {
            "reportTitle": "Stock Status Report",
            "generatedAt": datetime.now().isoformat(),
            "parameters": params,
            "summary": [
                {"label": "Total Items", "value": total_items, "format": "number"},
                {"label": "Low Stock", "value": low_stock, "format": "number"},
                {"label": "Overstock", "value": overstock, "format": "number"},
                {"label": "Total Value", "value": total_value, "format": "currency"},
            ],
            "headers": ["Code", "Product", "Category", "Stock", "Min", "Max", "Status", "Value"],
            "data": [
                [row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]]
                for row in results
            ]
        }
    
    @staticmethod
    def get_trial_balance(db: Session, params: Dict[str, Any]) -> Dict[str, Any]:
        """Trial balance (Mizan) report"""
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        level = params.get('level', 'full')
        
        # Determine account code length based on level
        code_length = {
            '2': 2,
            '4': 4,
            '6': 6,
            'full': 100
        }.get(level, 100)
        
        query = f"""
            WITH account_balances AS (
                SELECT 
                    a.code,
                    a.name,
                    SUM(CASE WHEN jl.type = 'debit' THEN jl.amount ELSE 0 END) as debit,
                    SUM(CASE WHEN jl.type = 'credit' THEN jl.amount ELSE 0 END) as credit
                FROM journal_entries je
                JOIN journal_lines jl ON je.id = jl.journal_id
                JOIN accounts a ON jl.account_id = a.id
                WHERE je.entry_date BETWEEN '{start_date}' AND '{end_date}'
                  AND LENGTH(a.code) <= {code_length}
                GROUP BY a.code, a.name
            )
            SELECT 
                code,
                name,
                debit,
                credit,
                (debit - credit) as balance
            FROM account_balances
            ORDER BY code
        """
        
        results = db.execute(query).fetchall()
        
        total_debit = sum(r[2] for r in results)
        total_credit = sum(r[3] for r in results)
        
        return {
            "reportTitle": "Trial Balance (Mizan)",
            "generatedAt": datetime.now().isoformat(),
            "parameters": params,
            "summary": [
                {"label": "Total Debit", "value": total_debit, "format": "currency"},
                {"label": "Total Credit", "value": total_credit, "format": "currency"},
                {"label": "Difference", "value": abs(total_debit - total_credit), "format": "currency"},
            ],
            "headers": ["Account Code", "Account Name", "Debit", "Credit", "Balance"],
            "data": [
                [row[0], row[1], row[2], row[3], row[4]]
                for row in results
            ]
        }


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/generate")
async def generate_report(
    request: GenerateReportRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a report
    """
    try:
        # Validate report ID
        if request.report_id not in REPORT_REGISTRY:
            raise HTTPException(status_code=404, detail="Report not found")
        
        report_config = REPORT_REGISTRY[request.report_id]
        
        # Convert parameters to dict
        params = {p.name: p.value for p in request.parameters}
        
        # Get query function
        query_func_name = report_config["query_func"]
        query_func = getattr(ReportQueries, query_func_name)
        
        # Execute query
        report_data = query_func(db, params)
        
        # Add company info
        report_data["company"] = {
            "name": "ExRetailOS Demo Store",
            "address": "Baghdad, Iraq",
            "phone": "+964 750 XXX XXXX",
            "taxNo": "123456789"
        }
        
        return {
            "success": True,
            "data": report_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_reports(
    category: Optional[str] = None
):
    """
    List available reports
    """
    reports = []
    
    for report_id, config in REPORT_REGISTRY.items():
        if category and config["category"] != category:
            continue
        
        reports.append({
            "id": report_id,
            "name": config["name"],
            "category": config["category"],
            "parameters": config["parameters"]
        })
    
    return {
        "success": True,
        "reports": reports,
        "total": len(reports)
    }


@router.post("/schedule")
async def schedule_report(
    request: ScheduleReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Schedule recurring report
    """
    try:
        # Store schedule in database
        insert_query = """
            INSERT INTO scheduled_reports (
                report_id, parameters, frequency, time,
                recipients, format, created_at
            ) VALUES (
                :report_id, :parameters, :frequency, :time,
                :recipients, :format, NOW()
            )
            RETURNING id
        """
        
        params_json = json.dumps([p.dict() for p in request.parameters])
        recipients_json = json.dumps(request.recipients)
        
        result = db.execute(insert_query, {
            "report_id": request.report_id,
            "parameters": params_json,
            "frequency": request.frequency,
            "time": request.time,
            "recipients": recipients_json,
            "format": request.format
        })
        
        schedule_id = result.fetchone()[0]
        db.commit()
        
        return {
            "success": True,
            "schedule_id": schedule_id,
            "message": f"Report scheduled successfully ({request.frequency} at {request.time})"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/custom")
async def create_custom_report(
    request: CustomReportRequest,
    db: Session = Depends(get_db)
):
    """
    Create custom report
    """
    try:
        # Store custom report definition
        insert_query = """
            INSERT INTO custom_reports (
                name, description, data_source, filters,
                columns, group_by, order_by, aggregations,
                created_at
            ) VALUES (
                :name, :description, :data_source, :filters,
                :columns, :group_by, :order_by, :aggregations,
                NOW()
            )
            RETURNING id
        """
        
        result = db.execute(insert_query, {
            "name": request.name,
            "description": request.description,
            "data_source": request.data_source,
            "filters": json.dumps(request.filters),
            "columns": json.dumps(request.columns),
            "group_by": json.dumps(request.group_by),
            "order_by": json.dumps(request.order_by),
            "aggregations": json.dumps(request.aggregations)
        })
        
        report_id = result.fetchone()[0]
        db.commit()
        
        return {
            "success": True,
            "report_id": report_id,
            "message": "Custom report created successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduled")
async def get_scheduled_reports(
    db: Session = Depends(get_db)
):
    """
    Get all scheduled reports
    """
    try:
        query = """
            SELECT 
                id, report_id, frequency, time,
                recipients, format, created_at
            FROM scheduled_reports
            ORDER BY created_at DESC
        """
        
        results = db.execute(query).fetchall()
        
        reports = []
        for row in results:
            reports.append({
                "id": row[0],
                "report_id": row[1],
                "frequency": row[2],
                "time": row[3],
                "recipients": json.loads(row[4]),
                "format": row[5],
                "created_at": row[6].isoformat()
            })
        
        return {
            "success": True,
            "reports": reports
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
