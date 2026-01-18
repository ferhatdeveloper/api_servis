-- EXFIN Reports Offline Sync Infrastructure
-- This script creates the tables necessary for storing report snapshots and tracking versions.

CREATE TABLE IF NOT EXISTS report_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_code VARCHAR(100) NOT NULL,
    tenant_id VARCHAR(50) NOT NULL, -- Format: FIRMA_PERIOD (e.g., 001_01)
    snapshot_data JSONB NOT NULL,
    version_id BIGINT DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(report_code, tenant_id)
);

CREATE INDEX IF NOT EXISTS idx_report_snapshots_code_tenant ON report_snapshots(report_code, tenant_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_report_snapshots_modtime
    BEFORE UPDATE ON report_snapshots
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();
