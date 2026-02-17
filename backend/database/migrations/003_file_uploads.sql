-- ============================================================
-- EduSMS File Uploads Migration
-- Migration 003 - File Upload Tracking
-- ============================================================

-- File uploads tracking table
CREATE TABLE IF NOT EXISTS file_uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    bucket VARCHAR(100) NOT NULL,
    file_path TEXT NOT NULL,
    original_name VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100),
    size BIGINT,
    hash VARCHAR(64), -- SHA-256 hash for deduplication
    metadata JSONB DEFAULT '{}',
    entity_type VARCHAR(100), -- What this file is attached to
    entity_id UUID, -- ID of the entity
    is_public BOOLEAN DEFAULT false,
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_file_uploads_school ON file_uploads(school_id);
CREATE INDEX IF NOT EXISTS idx_file_uploads_user ON file_uploads(user_id);
CREATE INDEX IF NOT EXISTS idx_file_uploads_entity ON file_uploads(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_file_uploads_hash ON file_uploads(hash);
CREATE INDEX IF NOT EXISTS idx_file_uploads_path ON file_uploads(file_path);
CREATE INDEX IF NOT EXISTS idx_file_uploads_created ON file_uploads(created_at);

-- Unique constraint on file path per bucket
CREATE UNIQUE INDEX IF NOT EXISTS idx_file_uploads_unique_path
    ON file_uploads(bucket, file_path) WHERE is_deleted = false;

-- RLS Policies
ALTER TABLE file_uploads ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS file_uploads_isolation ON file_uploads;
CREATE POLICY file_uploads_isolation ON file_uploads
    FOR ALL USING (school_id = get_user_school_id() OR is_public = true);

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_file_uploads_updated_at ON file_uploads;
CREATE TRIGGER update_file_uploads_updated_at
    BEFORE UPDATE ON file_uploads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Comment
COMMENT ON TABLE file_uploads IS 'Tracks all files uploaded to Supabase Storage for auditing and management';
