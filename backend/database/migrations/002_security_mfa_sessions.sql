-- ============================================================
-- EduSMS Security Migration: MFA, Sessions, and Security Tables
-- Migration 002 - Security Foundation for Phase 1
-- ============================================================

-- ============================================================
-- USER MFA (Multi-Factor Authentication)
-- Stores TOTP secrets and backup codes for 2FA
-- ============================================================

CREATE TABLE IF NOT EXISTS user_mfa (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    secret_key TEXT NOT NULL,
    is_enabled BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    backup_codes TEXT[], -- Hashed backup codes
    recovery_email VARCHAR(255),
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_mfa_user_id ON user_mfa(user_id);
CREATE INDEX IF NOT EXISTS idx_user_mfa_enabled ON user_mfa(is_enabled) WHERE is_enabled = true;

-- ============================================================
-- USER SESSIONS
-- Track active sessions for session management and security
-- ============================================================

CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL, -- SHA-256 hash of the session token
    refresh_token_hash TEXT, -- For JWT refresh tokens
    ip_address INET,
    user_agent TEXT,
    device_info JSONB DEFAULT '{}', -- {device_type, browser, os, etc.}
    location JSONB DEFAULT '{}', -- {city, country, lat, lon}
    is_active BOOLEAN DEFAULT true,
    is_mfa_verified BOOLEAN DEFAULT false, -- Whether MFA was completed for this session
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    revoked_reason VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token_hash ON user_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);

-- ============================================================
-- LOGIN ATTEMPTS
-- Track login attempts for brute-force protection
-- ============================================================

CREATE TABLE IF NOT EXISTS login_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(100), -- invalid_password, account_locked, mfa_failed, etc.
    user_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON login_attempts(email);
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX IF NOT EXISTS idx_login_attempts_created ON login_attempts(created_at);

-- Composite index for rate limiting queries
CREATE INDEX IF NOT EXISTS idx_login_attempts_email_time
    ON login_attempts(email, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip_time
    ON login_attempts(ip_address, created_at DESC);

-- ============================================================
-- ACCOUNT LOCKOUTS
-- Track account lockouts from failed login attempts
-- ============================================================

CREATE TABLE IF NOT EXISTS account_lockouts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    ip_address INET,
    lockout_type VARCHAR(50) NOT NULL, -- account, ip, email
    locked_at TIMESTAMPTZ DEFAULT NOW(),
    locked_until TIMESTAMPTZ NOT NULL,
    unlock_reason VARCHAR(100), -- auto_expired, admin_unlocked, user_reset
    unlocked_at TIMESTAMPTZ,
    unlocked_by UUID REFERENCES user_profiles(id),
    attempt_count INTEGER DEFAULT 0,
    UNIQUE(email, lockout_type) -- Only one active lockout per type
);

CREATE INDEX IF NOT EXISTS idx_account_lockouts_email ON account_lockouts(email);
CREATE INDEX IF NOT EXISTS idx_account_lockouts_locked_until ON account_lockouts(locked_until);

-- ============================================================
-- PASSWORD HISTORY
-- Track password history for password reuse prevention
-- ============================================================

CREATE TABLE IF NOT EXISTS password_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    password_hash TEXT NOT NULL, -- Hashed password for comparison
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_password_history_user_id ON password_history(user_id);
CREATE INDEX IF NOT EXISTS idx_password_history_created ON password_history(user_id, created_at DESC);

-- ============================================================
-- SECURITY EVENTS
-- Comprehensive security event logging
-- ============================================================

CREATE TABLE IF NOT EXISTS security_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    -- Event types: login_success, login_failed, logout, password_change,
    -- mfa_enabled, mfa_disabled, session_revoked, suspicious_activity,
    -- permission_denied, data_export, bulk_delete, etc.
    severity VARCHAR(20) DEFAULT 'info', -- info, warning, error, critical
    ip_address INET,
    user_agent TEXT,
    resource_type VARCHAR(100),
    resource_id UUID,
    details JSONB DEFAULT '{}',
    request_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_security_events_school ON security_events(school_id);
CREATE INDEX IF NOT EXISTS idx_security_events_user ON security_events(user_id);
CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity);
CREATE INDEX IF NOT EXISTS idx_security_events_created ON security_events(created_at);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_security_events_user_time
    ON security_events(user_id, created_at DESC);

-- ============================================================
-- TRUSTED DEVICES
-- Devices that have been verified and trusted for MFA bypass
-- ============================================================

CREATE TABLE IF NOT EXISTS trusted_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    device_fingerprint TEXT NOT NULL, -- Unique device identifier hash
    device_name VARCHAR(255), -- User-friendly name
    device_info JSONB DEFAULT '{}',
    ip_address INET,
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ, -- NULL means no expiration
    UNIQUE(user_id, device_fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_trusted_devices_user ON trusted_devices(user_id);
CREATE INDEX IF NOT EXISTS idx_trusted_devices_fingerprint ON trusted_devices(device_fingerprint);

-- ============================================================
-- API KEYS
-- For external integrations and API access
-- ============================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(10) NOT NULL, -- First 8 chars for identification (sk_live_abc...)
    key_hash TEXT NOT NULL, -- Full key hash
    permissions JSONB DEFAULT '[]', -- Array of permission strings
    rate_limit INTEGER DEFAULT 1000, -- Requests per hour
    allowed_ips TEXT[], -- IP whitelist
    last_used_at TIMESTAMPTZ,
    last_used_ip INET,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    revoked_by UUID REFERENCES user_profiles(id),
    revoked_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_api_keys_school ON api_keys(school_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active) WHERE is_active = true;

-- ============================================================
-- SECURITY SETTINGS
-- Per-school security configuration
-- ============================================================

CREATE TABLE IF NOT EXISTS security_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE UNIQUE,

    -- Password policies
    min_password_length INTEGER DEFAULT 8,
    require_uppercase BOOLEAN DEFAULT true,
    require_lowercase BOOLEAN DEFAULT true,
    require_numbers BOOLEAN DEFAULT true,
    require_special_chars BOOLEAN DEFAULT true,
    password_history_count INTEGER DEFAULT 5, -- How many old passwords to remember
    password_expiry_days INTEGER DEFAULT 0, -- 0 = never expire

    -- MFA settings
    mfa_required BOOLEAN DEFAULT false,
    mfa_required_roles TEXT[] DEFAULT '{}', -- Roles that require MFA
    mfa_grace_period_days INTEGER DEFAULT 7, -- Days to enable MFA after enforcement

    -- Session settings
    session_timeout_minutes INTEGER DEFAULT 60,
    max_concurrent_sessions INTEGER DEFAULT 5,
    single_session_per_device BOOLEAN DEFAULT false,

    -- Login settings
    max_login_attempts INTEGER DEFAULT 5,
    lockout_duration_minutes INTEGER DEFAULT 30,

    -- IP settings
    ip_whitelist_enabled BOOLEAN DEFAULT false,
    ip_whitelist TEXT[] DEFAULT '{}',
    ip_blacklist TEXT[] DEFAULT '{}',

    -- Notification settings
    notify_new_login BOOLEAN DEFAULT true,
    notify_password_change BOOLEAN DEFAULT true,
    notify_mfa_change BOOLEAN DEFAULT true,
    notify_suspicious_activity BOOLEAN DEFAULT true,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ENHANCED AUDIT_LOGS (Add columns if not exist)
-- ============================================================

-- Add category column for better organization
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'audit_logs' AND column_name = 'category') THEN
        ALTER TABLE audit_logs ADD COLUMN category VARCHAR(50);
    END IF;
END $$;

-- Add duration column for performance tracking
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'audit_logs' AND column_name = 'duration_ms') THEN
        ALTER TABLE audit_logs ADD COLUMN duration_ms INTEGER;
    END IF;
END $$;

-- Add status code column
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'audit_logs' AND column_name = 'status_code') THEN
        ALTER TABLE audit_logs ADD COLUMN status_code INTEGER;
    END IF;
END $$;

-- Add index for category
CREATE INDEX IF NOT EXISTS idx_audit_logs_category ON audit_logs(category);

-- ============================================================
-- ROW LEVEL SECURITY POLICIES
-- ============================================================

-- Enable RLS on all new tables
ALTER TABLE user_mfa ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE login_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_lockouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE password_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE trusted_devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_settings ENABLE ROW LEVEL SECURITY;

-- user_mfa: Users can only see their own MFA settings
DROP POLICY IF EXISTS user_mfa_own ON user_mfa;
CREATE POLICY user_mfa_own ON user_mfa
    FOR ALL USING (user_id = auth.uid());

-- user_sessions: Users can only see their own sessions
DROP POLICY IF EXISTS user_sessions_own ON user_sessions;
CREATE POLICY user_sessions_own ON user_sessions
    FOR ALL USING (user_id = auth.uid());

-- login_attempts: Only admins can view
DROP POLICY IF EXISTS login_attempts_admin ON login_attempts;
CREATE POLICY login_attempts_admin ON login_attempts
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid()
            AND role IN ('system_admin', 'principal')
        )
    );

-- account_lockouts: Only admins can view
DROP POLICY IF EXISTS account_lockouts_admin ON account_lockouts;
CREATE POLICY account_lockouts_admin ON account_lockouts
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid()
            AND role IN ('system_admin', 'principal')
        )
    );

-- password_history: Users can only see their own (for app use, not direct queries)
DROP POLICY IF EXISTS password_history_own ON password_history;
CREATE POLICY password_history_own ON password_history
    FOR ALL USING (user_id = auth.uid());

-- security_events: School-based access for admins
DROP POLICY IF EXISTS security_events_admin ON security_events;
CREATE POLICY security_events_admin ON security_events
    FOR SELECT USING (
        school_id IS NULL -- System-wide events for system_admin only
        OR school_id = get_user_school_id()
    );

-- trusted_devices: Users can only manage their own
DROP POLICY IF EXISTS trusted_devices_own ON trusted_devices;
CREATE POLICY trusted_devices_own ON trusted_devices
    FOR ALL USING (user_id = auth.uid());

-- api_keys: School-based access
DROP POLICY IF EXISTS api_keys_school ON api_keys;
CREATE POLICY api_keys_school ON api_keys
    FOR ALL USING (
        school_id IS NULL -- System-wide for system_admin
        OR school_id = get_user_school_id()
    );

-- security_settings: School-based access for admins
DROP POLICY IF EXISTS security_settings_school ON security_settings;
CREATE POLICY security_settings_school ON security_settings
    FOR ALL USING (school_id = get_user_school_id());

-- ============================================================
-- TRIGGERS
-- ============================================================

-- Update timestamp trigger for user_mfa
DROP TRIGGER IF EXISTS update_user_mfa_updated_at ON user_mfa;
CREATE TRIGGER update_user_mfa_updated_at
    BEFORE UPDATE ON user_mfa
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Update timestamp trigger for security_settings
DROP TRIGGER IF EXISTS update_security_settings_updated_at ON security_settings;
CREATE TRIGGER update_security_settings_updated_at
    BEFORE UPDATE ON security_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- HELPER FUNCTIONS
-- ============================================================

-- Function to check if user is locked out
CREATE OR REPLACE FUNCTION is_user_locked_out(check_email VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    lockout_record RECORD;
BEGIN
    SELECT * INTO lockout_record
    FROM account_lockouts
    WHERE email = check_email
      AND lockout_type = 'account'
      AND locked_until > NOW()
      AND unlocked_at IS NULL
    LIMIT 1;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get recent failed login attempts count
CREATE OR REPLACE FUNCTION get_failed_login_count(
    check_email VARCHAR,
    time_window_minutes INTEGER DEFAULT 30
)
RETURNS INTEGER AS $$
DECLARE
    count INTEGER;
BEGIN
    SELECT COUNT(*) INTO count
    FROM login_attempts
    WHERE email = check_email
      AND success = false
      AND created_at > NOW() - (time_window_minutes || ' minutes')::INTERVAL;

    RETURN count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to create account lockout
CREATE OR REPLACE FUNCTION create_account_lockout(
    lock_email VARCHAR,
    lock_user_id UUID DEFAULT NULL,
    lock_ip INET DEFAULT NULL,
    lock_type VARCHAR DEFAULT 'account',
    lock_duration_minutes INTEGER DEFAULT 30
)
RETURNS UUID AS $$
DECLARE
    lockout_id UUID;
BEGIN
    INSERT INTO account_lockouts (
        user_id, email, ip_address, lockout_type, locked_until
    ) VALUES (
        lock_user_id,
        lock_email,
        lock_ip,
        lock_type,
        NOW() + (lock_duration_minutes || ' minutes')::INTERVAL
    )
    ON CONFLICT (email, lockout_type)
    DO UPDATE SET
        locked_until = NOW() + (lock_duration_minutes || ' minutes')::INTERVAL,
        attempt_count = account_lockouts.attempt_count + 1
    RETURNING id INTO lockout_id;

    RETURN lockout_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions
    WHERE expires_at < NOW()
       OR (revoked_at IS NOT NULL AND revoked_at < NOW() - INTERVAL '7 days');

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to clean up old login attempts (older than 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_login_attempts()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM login_attempts
    WHERE created_at < NOW() - INTERVAL '90 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to log security event
CREATE OR REPLACE FUNCTION log_security_event(
    p_school_id UUID,
    p_user_id UUID,
    p_event_type VARCHAR,
    p_severity VARCHAR DEFAULT 'info',
    p_ip_address INET DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_resource_type VARCHAR DEFAULT NULL,
    p_resource_id UUID DEFAULT NULL,
    p_details JSONB DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
    event_id UUID;
BEGIN
    INSERT INTO security_events (
        school_id, user_id, event_type, severity,
        ip_address, user_agent, resource_type, resource_id, details
    ) VALUES (
        p_school_id, p_user_id, p_event_type, p_severity,
        p_ip_address, p_user_agent, p_resource_type, p_resource_id, p_details
    )
    RETURNING id INTO event_id;

    RETURN event_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- DEFAULT SECURITY SETTINGS FOR EXISTING SCHOOLS
-- ============================================================

-- Insert default security settings for all schools that don't have them
INSERT INTO security_settings (school_id)
SELECT id FROM schools
WHERE id NOT IN (SELECT school_id FROM security_settings)
ON CONFLICT (school_id) DO NOTHING;

-- ============================================================
-- COMMENTS
-- ============================================================

COMMENT ON TABLE user_mfa IS 'Stores TOTP MFA secrets and backup codes for two-factor authentication';
COMMENT ON TABLE user_sessions IS 'Tracks active user sessions for session management and security monitoring';
COMMENT ON TABLE login_attempts IS 'Records all login attempts for security analysis and brute-force protection';
COMMENT ON TABLE account_lockouts IS 'Manages account lockouts from failed login attempts';
COMMENT ON TABLE password_history IS 'Stores password hashes to prevent password reuse';
COMMENT ON TABLE security_events IS 'Comprehensive security event logging for audit and monitoring';
COMMENT ON TABLE trusted_devices IS 'Devices verified and trusted for MFA bypass';
COMMENT ON TABLE api_keys IS 'API keys for external integrations';
COMMENT ON TABLE security_settings IS 'Per-school security configuration settings';
