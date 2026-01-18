-- =====================================================
-- Year-over-Year (YoY) Comparison Views
-- Purpose: Compare current period vs same period last year
-- Periods: Daily, Weekly, Monthly
-- =====================================================

-- =====================================================
-- 1. YoY DAILY COMPARISON
-- Compare today vs same day last year
-- =====================================================
CREATE OR ALTER VIEW V_YOY_DAILY_COMPARISON AS
WITH CurrentDay AS (
    SELECT 
        -- Sales Metrics
        COUNT(DISTINCT I.LOGICALREF) AS invoice_count,
        ISNULL(SUM(I.NETTOTAL), 0) AS total_revenue,
        ISNULL(AVG(I.NETTOTAL), 0) AS avg_order_value,
        
        -- Customer Metrics
        COUNT(DISTINCT I.CLIENTREF) AS active_customers,
        
        -- Stock Movement
        COUNT(DISTINCT ST.LOGICALREF) AS stock_movement_count,
        ISNULL(SUM(ST.AMOUNT * ST.PRICE), 0) AS stock_movement_value
    FROM LG_001_01_INVOICE I WITH (NOLOCK)
    LEFT JOIN LG_001_01_STLINE ST WITH (NOLOCK) ON ST.DATE_ = CAST(GETDATE() AS DATE)
    WHERE CAST(I.DATE_ AS DATE) = CAST(GETDATE() AS DATE)
),
LastYearSameDay AS (
    SELECT 
        -- Sales Metrics
        COUNT(DISTINCT I.LOGICALREF) AS invoice_count,
        ISNULL(SUM(I.NETTOTAL), 0) AS total_revenue,
        ISNULL(AVG(I.NETTOTAL), 0) AS avg_order_value,
        
        -- Customer Metrics
        COUNT(DISTINCT I.CLIENTREF) AS active_customers,
        
        -- Stock Movement
        COUNT(DISTINCT ST.LOGICALREF) AS stock_movement_count,
        ISNULL(SUM(ST.AMOUNT * ST.PRICE), 0) AS stock_movement_value
    FROM LG_001_01_INVOICE I WITH (NOLOCK)
    LEFT JOIN LG_001_01_STLINE ST WITH (NOLOCK) ON ST.DATE_ = DATEADD(YEAR, -1, CAST(GETDATE() AS DATE))
    WHERE CAST(I.DATE_ AS DATE) = DATEADD(YEAR, -1, CAST(GETDATE() AS DATE))
)
SELECT 
    'DAILY' AS period_type,
    CAST(GETDATE() AS DATE) AS current_date,
    DATEADD(YEAR, -1, CAST(GETDATE() AS DATE)) AS last_year_date,
    
    -- Current Period
    C.invoice_count AS current_invoice_count,
    C.total_revenue AS current_revenue,
    C.avg_order_value AS current_avg_order,
    C.active_customers AS current_customers,
    C.stock_movement_count AS current_stock_movements,
    C.stock_movement_value AS current_stock_value,
    
    -- Last Year Same Period
    L.invoice_count AS ly_invoice_count,
    L.total_revenue AS ly_revenue,
    L.avg_order_value AS ly_avg_order,
    L.active_customers AS ly_customers,
    L.stock_movement_count AS ly_stock_movements,
    L.stock_movement_value AS ly_stock_value,
    
    -- Differences
    C.invoice_count - L.invoice_count AS diff_invoice_count,
    C.total_revenue - L.total_revenue AS diff_revenue,
    C.avg_order_value - L.avg_order_value AS diff_avg_order,
    C.active_customers - L.active_customers AS diff_customers,
    
    -- Percentage Changes
    CASE WHEN L.invoice_count = 0 THEN NULL 
         ELSE ((C.invoice_count - L.invoice_count) * 100.0 / L.invoice_count) END AS pct_change_invoices,
    CASE WHEN L.total_revenue = 0 THEN NULL 
         ELSE ((C.total_revenue - L.total_revenue) * 100.0 / L.total_revenue) END AS pct_change_revenue,
    CASE WHEN L.avg_order_value = 0 THEN NULL 
         ELSE ((C.avg_order_value - L.avg_order_value) * 100.0 / L.avg_order_value) END AS pct_change_avg_order,
    CASE WHEN L.active_customers = 0 THEN NULL 
         ELSE ((C.active_customers - L.active_customers) * 100.0 / L.active_customers) END AS pct_change_customers
FROM CurrentDay C
CROSS JOIN LastYearSameDay L;

GO

-- =====================================================
-- 2. YoY WEEKLY COMPARISON
-- Compare this week vs same week last year
-- =====================================================
CREATE OR ALTER VIEW V_YOY_WEEKLY_COMPARISON AS
WITH CurrentWeek AS (
    SELECT 
        -- Sales Metrics
        COUNT(DISTINCT I.LOGICALREF) AS invoice_count,
        ISNULL(SUM(I.NETTOTAL), 0) AS total_revenue,
        ISNULL(AVG(I.NETTOTAL), 0) AS avg_order_value,
        
        -- Customer Metrics
        COUNT(DISTINCT I.CLIENTREF) AS active_customers,
        
        -- Collection Metrics
        ISNULL(SUM(K.AMOUNT), 0) AS total_collections,
        COUNT(DISTINCT K.LOGICALREF) AS collection_count
    FROM LG_001_01_INVOICE I WITH (NOLOCK)
    LEFT JOIN LG_001_01_KSLINES K WITH (NOLOCK) 
        ON K.DATE_ BETWEEN DATEADD(DAY, 1-DATEPART(WEEKDAY, GETDATE()), CAST(GETDATE() AS DATE))
                       AND CAST(GETDATE() AS DATE)
    WHERE I.DATE_ BETWEEN DATEADD(DAY, 1-DATEPART(WEEKDAY, GETDATE()), CAST(GETDATE() AS DATE))
                      AND CAST(GETDATE() AS DATE)
),
LastYearSameWeek AS (
    SELECT 
        -- Sales Metrics
        COUNT(DISTINCT I.LOGICALREF) AS invoice_count,
        ISNULL(SUM(I.NETTOTAL), 0) AS total_revenue,
        ISNULL(AVG(I.NETTOTAL), 0) AS avg_order_value,
        
        -- Customer Metrics
        COUNT(DISTINCT I.CLIENTREF) AS active_customers,
        
        -- Collection Metrics
        ISNULL(SUM(K.AMOUNT), 0) AS total_collections,
        COUNT(DISTINCT K.LOGICALREF) AS collection_count
    FROM LG_001_01_INVOICE I WITH (NOLOCK)
    LEFT JOIN LG_001_01_KSLINES K WITH (NOLOCK) 
        ON K.DATE_ BETWEEN DATEADD(YEAR, -1, DATEADD(DAY, 1-DATEPART(WEEKDAY, GETDATE()), CAST(GETDATE() AS DATE)))
                       AND DATEADD(YEAR, -1, CAST(GETDATE() AS DATE))
    WHERE I.DATE_ BETWEEN DATEADD(YEAR, -1, DATEADD(DAY, 1-DATEPART(WEEKDAY, GETDATE()), CAST(GETDATE() AS DATE)))
                      AND DATEADD(YEAR, -1, CAST(GETDATE() AS DATE))
)
SELECT 
    'WEEKLY' AS period_type,
    DATEADD(DAY, 1-DATEPART(WEEKDAY, GETDATE()), CAST(GETDATE() AS DATE)) AS current_week_start,
    CAST(GETDATE() AS DATE) AS current_week_end,
    DATEADD(YEAR, -1, DATEADD(DAY, 1-DATEPART(WEEKDAY, GETDATE()), CAST(GETDATE() AS DATE))) AS ly_week_start,
    DATEADD(YEAR, -1, CAST(GETDATE() AS DATE)) AS ly_week_end,
    
    -- Current Period
    C.invoice_count AS current_invoice_count,
    C.total_revenue AS current_revenue,
    C.avg_order_value AS current_avg_order,
    C.active_customers AS current_customers,
    C.total_collections AS current_collections,
    C.collection_count AS current_collection_count,
    
    -- Last Year Same Period
    L.invoice_count AS ly_invoice_count,
    L.total_revenue AS ly_revenue,
    L.avg_order_value AS ly_avg_order,
    L.active_customers AS ly_customers,
    L.total_collections AS ly_collections,
    L.collection_count AS ly_collection_count,
    
    -- Differences
    C.invoice_count - L.invoice_count AS diff_invoice_count,
    C.total_revenue - L.total_revenue AS diff_revenue,
    C.total_collections - L.total_collections AS diff_collections,
    
    -- Percentage Changes
    CASE WHEN L.invoice_count = 0 THEN NULL 
         ELSE ((C.invoice_count - L.invoice_count) * 100.0 / L.invoice_count) END AS pct_change_invoices,
    CASE WHEN L.total_revenue = 0 THEN NULL 
         ELSE ((C.total_revenue - L.total_revenue) * 100.0 / L.total_revenue) END AS pct_change_revenue,
    CASE WHEN L.total_collections = 0 THEN NULL 
         ELSE ((C.total_collections - L.total_collections) * 100.0 / L.total_collections) END AS pct_change_collections
FROM CurrentWeek C
CROSS JOIN LastYearSameWeek L;

GO

-- =====================================================
-- 3. YoY MONTHLY COMPARISON
-- Compare this month vs same month last year
-- =====================================================
CREATE OR ALTER VIEW V_YOY_MONTHLY_COMPARISON AS
WITH CurrentMonth AS (
    SELECT 
        -- Sales Metrics
        COUNT(DISTINCT I.LOGICALREF) AS invoice_count,
        ISNULL(SUM(I.NETTOTAL), 0) AS total_revenue,
        ISNULL(AVG(I.NETTOTAL), 0) AS avg_order_value,
        
        -- Customer Metrics
        COUNT(DISTINCT I.CLIENTREF) AS active_customers,
        COUNT(DISTINCT CASE WHEN I.DATE_ >= DATEADD(MONTH, -1, GETDATE()) THEN I.CLIENTREF END) AS new_customers,
        
        -- Collection Metrics
        ISNULL(SUM(K.AMOUNT), 0) AS total_collections,
        COUNT(DISTINCT K.LOGICALREF) AS collection_count,
        
        -- Stock Metrics
        COUNT(DISTINCT ST.LOGICALREF) AS stock_movement_count,
        ISNULL(SUM(ST.AMOUNT * ST.PRICE), 0) AS stock_movement_value
    FROM LG_001_01_INVOICE I WITH (NOLOCK)
    LEFT JOIN LG_001_01_KSLINES K WITH (NOLOCK) 
        ON YEAR(K.DATE_) = YEAR(GETDATE()) AND MONTH(K.DATE_) = MONTH(GETDATE())
    LEFT JOIN LG_001_01_STLINE ST WITH (NOLOCK)
        ON YEAR(ST.DATE_) = YEAR(GETDATE()) AND MONTH(ST.DATE_) = MONTH(GETDATE())
    WHERE YEAR(I.DATE_) = YEAR(GETDATE()) AND MONTH(I.DATE_) = MONTH(GETDATE())
),
LastYearSameMonth AS (
    SELECT 
        -- Sales Metrics
        COUNT(DISTINCT I.LOGICALREF) AS invoice_count,
        ISNULL(SUM(I.NETTOTAL), 0) AS total_revenue,
        ISNULL(AVG(I.NETTOTAL), 0) AS avg_order_value,
        
        -- Customer Metrics
        COUNT(DISTINCT I.CLIENTREF) AS active_customers,
        COUNT(DISTINCT CASE WHEN I.DATE_ >= DATEADD(MONTH, -1, DATEADD(YEAR, -1, GETDATE())) THEN I.CLIENTREF END) AS new_customers,
        
        -- Collection Metrics
        ISNULL(SUM(K.AMOUNT), 0) AS total_collections,
        COUNT(DISTINCT K.LOGICALREF) AS collection_count,
        
        -- Stock Metrics
        COUNT(DISTINCT ST.LOGICALREF) AS stock_movement_count,
        ISNULL(SUM(ST.AMOUNT * ST.PRICE), 0) AS stock_movement_value
    FROM LG_001_01_INVOICE I WITH (NOLOCK)
    LEFT JOIN LG_001_01_KSLINES K WITH (NOLOCK) 
        ON YEAR(K.DATE_) = YEAR(DATEADD(YEAR, -1, GETDATE())) 
        AND MONTH(K.DATE_) = MONTH(GETDATE())
    LEFT JOIN LG_001_01_STLINE ST WITH (NOLOCK)
        ON YEAR(ST.DATE_) = YEAR(DATEADD(YEAR, -1, GETDATE())) 
        AND MONTH(ST.DATE_) = MONTH(GETDATE())
    WHERE YEAR(I.DATE_) = YEAR(DATEADD(YEAR, -1, GETDATE())) 
      AND MONTH(I.DATE_) = MONTH(GETDATE())
)
SELECT 
    'MONTHLY' AS period_type,
    DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1) AS current_month_start,
    EOMONTH(GETDATE()) AS current_month_end,
    DATEFROMPARTS(YEAR(DATEADD(YEAR, -1, GETDATE())), MONTH(GETDATE()), 1) AS ly_month_start,
    EOMONTH(DATEADD(YEAR, -1, GETDATE())) AS ly_month_end,
    
    -- Current Period
    C.invoice_count AS current_invoice_count,
    C.total_revenue AS current_revenue,
    C.avg_order_value AS current_avg_order,
    C.active_customers AS current_customers,
    C.new_customers AS current_new_customers,
    C.total_collections AS current_collections,
    C.collection_count AS current_collection_count,
    C.stock_movement_count AS current_stock_movements,
    C.stock_movement_value AS current_stock_value,
    
    -- Last Year Same Period
    L.invoice_count AS ly_invoice_count,
    L.total_revenue AS ly_revenue,
    L.avg_order_value AS ly_avg_order,
    L.active_customers AS ly_customers,
    L.new_customers AS ly_new_customers,
    L.total_collections AS ly_collections,
    L.collection_count AS ly_collection_count,
    L.stock_movement_count AS ly_stock_movements,
    L.stock_movement_value AS ly_stock_value,
    
    -- Differences
    C.invoice_count - L.invoice_count AS diff_invoice_count,
    C.total_revenue - L.total_revenue AS diff_revenue,
    C.total_collections - L.total_collections AS diff_collections,
    C.stock_movement_value - L.stock_movement_value AS diff_stock_value,
    
    -- Percentage Changes
    CASE WHEN L.invoice_count = 0 THEN NULL 
         ELSE ((C.invoice_count - L.invoice_count) * 100.0 / L.invoice_count) END AS pct_change_invoices,
    CASE WHEN L.total_revenue = 0 THEN NULL 
         ELSE ((C.total_revenue - L.total_revenue) * 100.0 / L.total_revenue) END AS pct_change_revenue,
    CASE WHEN L.total_collections = 0 THEN NULL 
         ELSE ((C.total_collections - L.total_collections) * 100.0 / L.total_collections) END AS pct_change_collections,
    CASE WHEN L.stock_movement_value = 0 THEN NULL 
         ELSE ((C.stock_movement_value - L.stock_movement_value) * 100.0 / L.stock_movement_value) END AS pct_change_stock_value
FROM CurrentMonth C
CROSS JOIN LastYearSameMonth L;

GO
