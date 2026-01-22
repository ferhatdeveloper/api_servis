-- Dosya Adı: supabase_functions.sql
-- Açıklama: Supabase'de gerekli fonksiyonları oluşturmak için SQL komutları
-- Oluşturulma Tarihi: 2024-03-21
-- Geliştirici: Ferhat NAS
-- Son Güncelleme: 2024-03-21

-- UUID uzantısını etkinleştir
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- updated_at alanını otomatik güncelleyen fonksiyon
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Tablo varlığını kontrol eden fonksiyon
CREATE OR REPLACE FUNCTION check_table_exists(table_name text)
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name = $1
    );
END;
$$ LANGUAGE plpgsql
SECURITY DEFINER;

-- SQL komutunu çalıştıran fonksiyon
CREATE OR REPLACE FUNCTION execute_sql(sql text)
RETURNS void AS $$
BEGIN
    EXECUTE sql;
END;
$$ LANGUAGE plpgsql
SECURITY DEFINER;

-- Tablo oluşturan fonksiyon
CREATE OR REPLACE FUNCTION create_table_if_not_exists(
    table_name text,
    create_sql text
)
RETURNS void AS $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name = $1
    ) THEN
        EXECUTE create_sql;
        
        -- RLS'yi etkinleştir
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', $1);
    END IF;
END;
$$ LANGUAGE plpgsql
SECURITY DEFINER;

-- Onay durumu değişikliklerini kontrol eden fonksiyon
CREATE OR REPLACE FUNCTION check_approval_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Onay durumu değişmişse
    IF OLD.approval_status != NEW.approval_status THEN
        -- Sadece admin onay durumunu değiştirebilir
        IF NOT EXISTS (
            SELECT 1 FROM user_roles 
            WHERE user_id = auth.uid() 
            AND role = 'admin'
        ) THEN
            RAISE EXCEPTION 'Onay durumunu sadece admin değiştirebilir';
        END IF;

        -- Onaylanmış kayıt reddedilemez
        IF OLD.approval_status = 1 AND NEW.approval_status = 3 THEN
            RAISE EXCEPTION 'Onaylanmış kayıt reddedilemez';
        END IF;

        -- Senkronize edilmiş kayıt değiştirilemez
        IF OLD.approval_status = 2 THEN
            RAISE EXCEPTION 'Senkronize edilmiş kayıt değiştirilemez';
        END IF;
    END IF;

    -- Onaylanmış kayıt sadece admin tarafından güncellenebilir
    IF OLD.approval_status = 1 AND NOT EXISTS (
        SELECT 1 FROM user_roles 
        WHERE user_id = auth.uid() 
        AND role = 'admin'
    ) THEN
        RAISE EXCEPTION 'Onaylanmış kayıt sadece admin tarafından güncellenebilir';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Değişiklikleri loglayan fonksiyon
CREATE OR REPLACE FUNCTION log_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (
        table_name,
        record_id,
        operation,
        old_data,
        new_data,
        changed_by,
        changed_at
    ) VALUES (
        TG_TABLE_NAME,
        NEW.id,
        TG_OP,
        row_to_json(OLD),
        row_to_json(NEW),
        auth.uid(),
        NOW()
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Audit log tablosunu oluştur
CREATE TABLE IF NOT EXISTS audit_log (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name TEXT NOT NULL,
    record_id uuid NOT NULL,
    operation TEXT NOT NULL,
    old_data JSONB,
    new_data JSONB,
    changed_by uuid NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Audit log için RLS politikaları
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Sadece admin okuyabilir
CREATE POLICY "audit_log_select_policy"
    ON audit_log
    FOR SELECT
    USING (
        auth.role() = 'authenticated' AND
        auth.uid() IN (SELECT user_id FROM user_roles WHERE role = 'admin')
    );

-- Sadece sistem yazabilir
CREATE POLICY "audit_log_insert_policy"
    ON audit_log
    FOR INSERT
    WITH CHECK (true);

-- Kimse güncelleyemez veya silemez
CREATE POLICY "audit_log_update_policy"
    ON audit_log
    FOR UPDATE
    USING (false);

CREATE POLICY "audit_log_delete_policy"
    ON audit_log
    FOR DELETE
    USING (false); 