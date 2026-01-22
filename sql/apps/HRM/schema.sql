-- Dosya Adı: device_security_firewall_schema.sql
-- Açıklama: Cihaz güvenlik duvarı - İhlal loglama ve güvenlik olayları
-- Oluşturulma Tarihi: 2025-01-20
-- Geliştirici: EXFIN PDKS Team
-- Son Güncelleme: 2025-01-20

-- Güvenlik ihlali logları tablosu
CREATE TABLE IF NOT EXISTS public.device_security_violations (
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    device_id character varying(100) NOT NULL,
    employee_id uuid,
    violation_type character varying(50) NOT NULL, -- 'app_install', 'app_uninstall', 'settings_access', 'website_access', 'unauthorized_app', 'policy_bypass'
    violation_severity character varying(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    violation_description text,
    blocked_resource character varying(500), -- Engellenen uygulama/site adı
    resource_type character varying(50), -- 'app', 'website', 'setting'
    policy_id uuid,
    action_taken character varying(50) DEFAULT 'blocked', -- 'blocked', 'warned', 'logged', 'allowed'
    user_action text, -- Kullanıcının yapmaya çalıştığı işlem
    device_info jsonb, -- Cihaz bilgileri (model, OS, vb.)
    ip_address character varying(50),
    location_info jsonb, -- Konum bilgileri (lat, lng, address)
    timestamp timestamp with time zone DEFAULT now(),
    resolved boolean DEFAULT false,
    resolved_at timestamp with time zone,
    resolved_by character varying(100),
    resolution_notes text,
    CONSTRAINT device_security_violations_pkey PRIMARY KEY (id)
);

-- Güvenlik olayları tablosu (gerçek zamanlı izleme)
CREATE TABLE IF NOT EXISTS public.device_security_events (
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    device_id character varying(100) NOT NULL,
    employee_id uuid,
    event_type character varying(50) NOT NULL, -- 'policy_applied', 'policy_violation', 'app_blocked', 'website_blocked', 'settings_blocked'
    event_category character varying(50), -- 'firewall', 'policy', 'compliance'
    event_description text,
    event_data jsonb, -- Detaylı olay verileri
    severity character varying(20) DEFAULT 'info', -- 'info', 'warning', 'error', 'critical'
    source character varying(100), -- Olayın kaynağı
    timestamp timestamp with time zone DEFAULT now(),
    processed boolean DEFAULT false,
    CONSTRAINT device_security_events_pkey PRIMARY KEY (id)
);

-- Güvenlik istatistikleri tablosu (günlük özet)
CREATE TABLE IF NOT EXISTS public.device_security_stats (
    id uuid NOT NULL DEFAULT uuid_generate_v4(),
    device_id character varying(100) NOT NULL,
    employee_id uuid,
    stat_date date NOT NULL DEFAULT CURRENT_DATE,
    total_violations integer DEFAULT 0,
    blocked_apps integer DEFAULT 0,
    blocked_websites integer DEFAULT 0,
    blocked_settings_access integer DEFAULT 0,
    policy_bypass_attempts integer DEFAULT 0,
    critical_violations integer DEFAULT 0,
    high_violations integer DEFAULT 0,
    medium_violations integer DEFAULT 0,
    low_violations integer DEFAULT 0,
    compliance_score numeric(5,2) DEFAULT 100.00, -- 0-100 arası uyumluluk skoru
    last_violation_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT device_security_stats_pkey PRIMARY KEY (id),
    CONSTRAINT device_security_stats_unique UNIQUE (device_id, stat_date)
);

-- İndeksler
CREATE INDEX IF NOT EXISTS idx_security_violations_device_id ON public.device_security_violations(device_id);
CREATE INDEX IF NOT EXISTS idx_security_violations_employee_id ON public.device_security_violations(employee_id);
CREATE INDEX IF NOT EXISTS idx_security_violations_type ON public.device_security_violations(violation_type);
CREATE INDEX IF NOT EXISTS idx_security_violations_severity ON public.device_security_violations(violation_severity);
CREATE INDEX IF NOT EXISTS idx_security_violations_timestamp ON public.device_security_violations(timestamp);
CREATE INDEX IF NOT EXISTS idx_security_violations_resolved ON public.device_security_violations(resolved);

CREATE INDEX IF NOT EXISTS idx_security_events_device_id ON public.device_security_events(device_id);
CREATE INDEX IF NOT EXISTS idx_security_events_type ON public.device_security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON public.device_security_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_security_events_processed ON public.device_security_events(processed);

CREATE INDEX IF NOT EXISTS idx_security_stats_device_id ON public.device_security_stats(device_id);
CREATE INDEX IF NOT EXISTS idx_security_stats_date ON public.device_security_stats(stat_date);

-- Updated_at otomatik güncelleme trigger'ları
CREATE OR REPLACE FUNCTION update_device_security_stats_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger'ı sadece yoksa oluştur
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'device_security_stats_updated_at' 
        AND tgrelid = 'public.device_security_stats'::regclass
    ) THEN
        CREATE TRIGGER device_security_stats_updated_at
            BEFORE UPDATE ON public.device_security_stats
            FOR EACH ROW
            EXECUTE FUNCTION update_device_security_stats_updated_at();
    END IF;
END $$;

-- Foreign key constraint'leri (employees tablosu varsa)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'employees') THEN
        -- device_security_violations
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_schema = 'public' 
            AND constraint_name = 'device_security_violations_employee_id_fkey'
        ) THEN
            ALTER TABLE public.device_security_violations
            ADD CONSTRAINT device_security_violations_employee_id_fkey 
            FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE SET NULL;
        END IF;
        
        -- device_security_events
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_schema = 'public' 
            AND constraint_name = 'device_security_events_employee_id_fkey'
        ) THEN
            ALTER TABLE public.device_security_events
            ADD CONSTRAINT device_security_events_employee_id_fkey 
            FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE SET NULL;
        END IF;
        
        -- device_security_stats
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_schema = 'public' 
            AND constraint_name = 'device_security_stats_employee_id_fkey'
        ) THEN
            ALTER TABLE public.device_security_stats
            ADD CONSTRAINT device_security_stats_employee_id_fkey 
            FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE SET NULL;
        END IF;
    END IF;
END $$;

-- Yorumlar
COMMENT ON TABLE public.device_security_violations IS 'Cihaz güvenlik ihlali logları - Güvenlik duvarı ihlalleri';
COMMENT ON TABLE public.device_security_events IS 'Cihaz güvenlik olayları - Gerçek zamanlı güvenlik olayları';
COMMENT ON TABLE public.device_security_stats IS 'Cihaz güvenlik istatistikleri - Günlük güvenlik özetleri';

COMMENT ON COLUMN public.device_security_violations.violation_type IS 'İhlal türü: app_install, app_uninstall, settings_access, website_access, unauthorized_app, policy_bypass';
COMMENT ON COLUMN public.device_security_violations.violation_severity IS 'İhlal şiddeti: low, medium, high, critical';
COMMENT ON COLUMN public.device_security_violations.action_taken IS 'Alınan aksiyon: blocked, warned, logged, allowed';
COMMENT ON COLUMN public.device_security_stats.compliance_score IS 'Uyumluluk skoru: 0-100 arası (100 = tam uyumlu)';

