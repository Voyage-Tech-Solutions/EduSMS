-- Phase 3 & 4: Analytics, Communication, and System Tables
-- Analytics, Messaging, Audit Logging, System Health

-- ============================================================
-- ANALYTICS & REPORTING
-- ============================================================

-- Generated reports
CREATE TABLE IF NOT EXISTS generated_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    requested_by UUID NOT NULL,
    report_type VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    parameters JSONB,
    format VARCHAR(20) DEFAULT 'pdf',
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    data JSONB,
    file_url TEXT,
    file_size_bytes INTEGER,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scheduled reports
CREATE TABLE IF NOT EXISTS scheduled_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    created_by UUID NOT NULL,
    report_type VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    schedule VARCHAR(20) NOT NULL, -- daily, weekly, monthly
    day_of_week INTEGER, -- 0-6 for weekly
    day_of_month INTEGER, -- 1-31 for monthly
    time TIME DEFAULT '08:00',
    format VARCHAR(20) DEFAULT 'pdf',
    recipients TEXT[],
    filters JSONB,
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Export history
CREATE TABLE IF NOT EXISTS export_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    requested_by UUID NOT NULL,
    data_type VARCHAR(100) NOT NULL,
    format VARCHAR(20) NOT NULL,
    record_count INTEGER,
    file_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- MESSAGING SYSTEM
-- ============================================================

-- Message threads
CREATE TABLE IF NOT EXISTS message_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Messages
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    thread_id UUID REFERENCES message_threads(id),
    sender_id UUID NOT NULL,
    subject VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal', -- low, normal, high, urgent
    reply_to_id UUID REFERENCES messages(id),
    attachments TEXT[],
    is_draft BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Message recipients
CREATE TABLE IF NOT EXISTS message_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    recipient_id UUID NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    folder VARCHAR(50) DEFAULT 'inbox', -- inbox, archive, trash
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversations (group chats)
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    title VARCHAR(255),
    created_by UUID NOT NULL,
    last_message TEXT,
    last_message_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversation participants
CREATE TABLE IF NOT EXISTS conversation_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(conversation_id, user_id)
);

-- Conversation messages
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL,
    body TEXT NOT NULL,
    attachments TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ANNOUNCEMENTS
-- ============================================================

-- Announcements
CREATE TABLE IF NOT EXISTS announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    author_id UUID NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    priority VARCHAR(20) DEFAULT 'normal',
    target_audience TEXT[] DEFAULT ARRAY['all'],
    target_grade_ids UUID[],
    target_class_ids UUID[],
    publish_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    allow_comments BOOLEAN DEFAULT FALSE,
    attachments TEXT[],
    pin_to_top BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'published', -- draft, scheduled, published, archived
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Announcement views
CREATE TABLE IF NOT EXISTS announcement_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    announcement_id UUID NOT NULL REFERENCES announcements(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    viewed_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(announcement_id, user_id)
);

-- Announcement comments
CREATE TABLE IF NOT EXISTS announcement_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    announcement_id UUID NOT NULL REFERENCES announcements(id) ON DELETE CASCADE,
    author_id UUID NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- MESSAGE TEMPLATES
-- ============================================================

CREATE TABLE IF NOT EXISTS message_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    created_by UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subject VARCHAR(500),
    body TEXT NOT NULL,
    variables TEXT[],
    is_system BOOLEAN DEFAULT FALSE,
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- NOTIFICATION LOG
-- ============================================================

CREATE TABLE IF NOT EXISTS notification_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id),
    user_id UUID NOT NULL,
    notification_type VARCHAR(100) NOT NULL,
    channel VARCHAR(20) NOT NULL, -- push, email, sms, in_app
    title VARCHAR(500),
    message TEXT,
    data JSONB,
    status VARCHAR(50) DEFAULT 'sent', -- sent, delivered, failed
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,
    error TEXT
);

-- ============================================================
-- AUDIT LOGGING
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id),
    user_id UUID,
    action VARCHAR(50) NOT NULL, -- create, read, update, delete, login, logout, etc.
    resource_type VARCHAR(100) NOT NULL, -- student, teacher, grade, etc.
    resource_id VARCHAR(255),
    description TEXT,
    old_value JSONB,
    new_value JSONB,
    metadata JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Error logs
CREATE TABLE IF NOT EXISTS error_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id),
    user_id UUID,
    error_type VARCHAR(100),
    message TEXT,
    stack_trace TEXT,
    request_path VARCHAR(500),
    request_method VARCHAR(10),
    request_body JSONB,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SYSTEM ADMINISTRATION
-- ============================================================

-- System settings
CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(255) NOT NULL UNIQUE,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- System alerts
CREATE TABLE IF NOT EXISTS system_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL, -- low, medium, high, critical
    title VARCHAR(500) NOT NULL,
    message TEXT,
    data JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by UUID,
    acknowledged_at TIMESTAMPTZ,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID,
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Search history
CREATE TABLE IF NOT EXISTS search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    query VARCHAR(500) NOT NULL,
    result_count INTEGER DEFAULT 0,
    searched_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- BACKUP & RESTORE
-- ============================================================

-- Backups
CREATE TABLE IF NOT EXISTS backups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    created_by UUID NOT NULL,
    backup_type VARCHAR(50) DEFAULT 'full', -- full, incremental, selective
    description TEXT,
    include_files BOOLEAN DEFAULT TRUE,
    tables TEXT[],
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed, failed
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    record_count INTEGER,
    file_size_bytes BIGINT,
    file_url TEXT,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scheduled backups
CREATE TABLE IF NOT EXISTS scheduled_backups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    created_by UUID NOT NULL,
    schedule VARCHAR(20) NOT NULL, -- daily, weekly, monthly
    time TIME DEFAULT '02:00',
    day_of_week INTEGER,
    day_of_month INTEGER,
    backup_type VARCHAR(50) DEFAULT 'full',
    retention_days INTEGER DEFAULT 30,
    last_run_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Restore jobs
CREATE TABLE IF NOT EXISTS restore_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backup_id UUID NOT NULL REFERENCES backups(id),
    restored_by UUID NOT NULL,
    tables TEXT[],
    overwrite BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- CONSENT MANAGEMENT (GDPR)
-- ============================================================

CREATE TABLE IF NOT EXISTS consent_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    user_id UUID NOT NULL,
    consent_type VARCHAR(100) NOT NULL,
    granted BOOLEAN NOT NULL,
    granted_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ENSURE COLUMNS EXIST (if tables exist from previous migrations)
-- ============================================================

DO $$
BEGIN
    -- Ensure audit_logs columns exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'resource_type') THEN
        ALTER TABLE audit_logs ADD COLUMN resource_type VARCHAR(100);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'resource_id') THEN
        ALTER TABLE audit_logs ADD COLUMN resource_id VARCHAR(255);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'old_value') THEN
        ALTER TABLE audit_logs ADD COLUMN old_value JSONB;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'new_value') THEN
        ALTER TABLE audit_logs ADD COLUMN new_value JSONB;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'metadata') THEN
        ALTER TABLE audit_logs ADD COLUMN metadata JSONB;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'ip_address') THEN
        ALTER TABLE audit_logs ADD COLUMN ip_address INET;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'audit_logs' AND column_name = 'user_agent') THEN
        ALTER TABLE audit_logs ADD COLUMN user_agent TEXT;
    END IF;
END $$;

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_message_recipients_recipient ON message_recipients(recipient_id, folder);
CREATE INDEX IF NOT EXISTS idx_message_recipients_unread ON message_recipients(recipient_id, is_read) WHERE is_read = FALSE;

CREATE INDEX IF NOT EXISTS idx_announcements_school_status ON announcements(school_id, status);
CREATE INDEX IF NOT EXISTS idx_announcements_publish ON announcements(publish_at);

CREATE INDEX IF NOT EXISTS idx_audit_logs_school ON audit_logs(school_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

CREATE INDEX IF NOT EXISTS idx_generated_reports_school ON generated_reports(school_id, status);
CREATE INDEX IF NOT EXISTS idx_backups_school ON backups(school_id, status);

CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history(user_id, searched_at);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE message_recipients ENABLE ROW LEVEL SECURITY;
ALTER TABLE announcements ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE backups ENABLE ROW LEVEL SECURITY;

-- Users can only see their own messages
DROP POLICY IF EXISTS messages_sender_policy ON messages;
CREATE POLICY messages_sender_policy ON messages
    FOR SELECT USING (sender_id = auth.uid());

DROP POLICY IF EXISTS message_recipients_policy ON message_recipients;
CREATE POLICY message_recipients_policy ON message_recipients
    FOR ALL USING (recipient_id = auth.uid());

-- Audit logs visible to admins only (implemented in API)
DROP POLICY IF EXISTS audit_logs_school_policy ON audit_logs;
CREATE POLICY audit_logs_school_policy ON audit_logs
    FOR SELECT USING (school_id IN (
        SELECT school_id FROM user_profiles WHERE id = auth.uid() AND role IN ('system_admin', 'school_admin', 'principal')
    ));
