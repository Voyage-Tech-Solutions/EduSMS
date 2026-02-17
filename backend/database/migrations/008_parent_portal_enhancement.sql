-- Phase 2: Parent Portal Enhancement Migration
-- Adds tables for conferences, notification preferences, documents, and calendar

-- ============================================================
-- CONFERENCE MANAGEMENT
-- ============================================================

-- Conference slots offered by teachers
-- Conference slots offered by teachers
CREATE TABLE IF NOT EXISTS conference_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    teacher_id UUID NOT NULL REFERENCES user_profiles(id), -- Changed from teachers(id)
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_minutes INTEGER DEFAULT 15,
    location VARCHAR(255),
    is_virtual BOOLEAN DEFAULT FALSE,
    meeting_link TEXT,
    is_available BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- If table exists (from 006), ensure columns exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'conference_slots' AND column_name = 'meeting_link') THEN
        ALTER TABLE conference_slots ADD COLUMN meeting_link TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'conference_slots' AND column_name = 'notes') THEN
        ALTER TABLE conference_slots ADD COLUMN notes TEXT;
    END IF;
END $$;

-- Conference bookings
-- Conference bookings
CREATE TABLE IF NOT EXISTS conference_bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    slot_id UUID NOT NULL REFERENCES conference_slots(id),
    parent_id UUID NOT NULL REFERENCES user_profiles(id),
    student_id UUID NOT NULL REFERENCES students(id),
    topics TEXT[],
    notes TEXT,
    status VARCHAR(50) DEFAULT 'confirmed', -- confirmed, cancelled, completed, no_show
    cancelled_at TIMESTAMPTZ,
    cancelled_reason TEXT,
    cancelled_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure columns exist if table exists (from migration 006)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'conference_bookings' AND column_name = 'topics') THEN
        ALTER TABLE conference_bookings ADD COLUMN topics TEXT[];
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'conference_bookings' AND column_name = 'cancelled_by') THEN
        ALTER TABLE conference_bookings ADD COLUMN cancelled_by UUID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'conference_bookings' AND column_name = 'school_id') THEN
        ALTER TABLE conference_bookings ADD COLUMN school_id UUID REFERENCES schools(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'conference_bookings' AND column_name = 'parent_id') THEN
        ALTER TABLE conference_bookings ADD COLUMN parent_id UUID REFERENCES user_profiles(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'conference_bookings' AND column_name = 'student_id') THEN
        ALTER TABLE conference_bookings ADD COLUMN student_id UUID REFERENCES students(id);
    END IF;
END $$;

-- ============================================================
-- NOTIFICATION PREFERENCES
-- ============================================================

-- Parent notification preferences
-- Parent notification preferences
CREATE TABLE IF NOT EXISTS parent_notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID NOT NULL UNIQUE,
    email_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT TRUE,

    -- Category preferences
    grade_notifications BOOLEAN DEFAULT TRUE,
    attendance_notifications BOOLEAN DEFAULT TRUE,
    fee_notifications BOOLEAN DEFAULT TRUE,
    announcement_notifications BOOLEAN DEFAULT TRUE,
    assignment_notifications BOOLEAN DEFAULT TRUE,
    behavior_notifications BOOLEAN DEFAULT TRUE,
    event_notifications BOOLEAN DEFAULT TRUE,
    report_card_notifications BOOLEAN DEFAULT TRUE,

    -- Timing preferences
    quiet_hours_enabled BOOLEAN DEFAULT FALSE,
    quiet_hours_start TIME,
    quiet_hours_end TIME,

    -- Digest preferences
    daily_digest_enabled BOOLEAN DEFAULT FALSE,
    weekly_digest_enabled BOOLEAN DEFAULT TRUE,
    digest_time TIME DEFAULT '18:00',

    -- Language
    language_preference VARCHAR(10) DEFAULT 'en',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure extended columns exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'parent_notification_preferences' AND column_name = 'report_card_notifications') THEN
        ALTER TABLE parent_notification_preferences ADD COLUMN report_card_notifications BOOLEAN DEFAULT TRUE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'parent_notification_preferences' AND column_name = 'daily_digest_enabled') THEN
        ALTER TABLE parent_notification_preferences ADD COLUMN daily_digest_enabled BOOLEAN DEFAULT FALSE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'parent_notification_preferences' AND column_name = 'weekly_digest_enabled') THEN
        ALTER TABLE parent_notification_preferences ADD COLUMN weekly_digest_enabled BOOLEAN DEFAULT TRUE;
    END IF;
     IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'parent_notification_preferences' AND column_name = 'digest_time') THEN
        ALTER TABLE parent_notification_preferences ADD COLUMN digest_time TIME DEFAULT '18:00';
    END IF;
END $$;

-- Per-notification-type channel preferences
CREATE TABLE IF NOT EXISTS parent_notification_channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID NOT NULL,
    notification_type VARCHAR(100) NOT NULL,
    email BOOLEAN DEFAULT TRUE,
    sms BOOLEAN DEFAULT FALSE,
    push BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(parent_id, notification_type)
);

-- Notification history
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id),
    user_id UUID NOT NULL,
    notification_type VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    message TEXT,
    data JSONB,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    channel VARCHAR(20), -- email, sms, push
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Push notification device tokens
CREATE TABLE IF NOT EXISTS push_device_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    token TEXT NOT NULL UNIQUE,
    device_type VARCHAR(20) DEFAULT 'web', -- web, ios, android
    device_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- PARENT DOCUMENTS
-- ============================================================

-- Documents uploaded by parents
CREATE TABLE IF NOT EXISTS parent_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    student_id UUID NOT NULL REFERENCES students(id),
    uploaded_by UUID NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    related_date DATE,
    file_url TEXT NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending', -- pending, approved, rejected
    reviewed_by UUID,
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Required documents configuration
CREATE TABLE IF NOT EXISTS required_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    document_type VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_required BOOLEAN DEFAULT TRUE,
    applies_to VARCHAR(50) DEFAULT 'all', -- all, new_students, grade_levels
    grade_levels TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- PAYMENT METHODS
-- ============================================================

-- Saved payment methods for parents
CREATE TABLE IF NOT EXISTS parent_payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID NOT NULL,
    method_type VARCHAR(50) NOT NULL, -- card, bank_account
    last_four VARCHAR(4) NOT NULL,
    card_brand VARCHAR(50),
    expiry_month INTEGER,
    expiry_year INTEGER,
    nickname VARCHAR(100),
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    stripe_payment_method_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- CALENDAR SYNC
-- ============================================================

-- Calendar sync tokens for iCal feeds
CREATE TABLE IF NOT EXISTS calendar_sync_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    token VARCHAR(100) NOT NULL UNIQUE,
    student_id UUID REFERENCES students(id),
    last_accessed TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- PROFESSIONAL DEVELOPMENT (Principal Strategic)
-- ============================================================

-- PD activities
-- PD activities
CREATE TABLE IF NOT EXISTS professional_development (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    staff_id UUID NOT NULL,
    academic_year_id UUID REFERENCES academic_years(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    provider VARCHAR(255),
    category VARCHAR(100) NOT NULL, -- workshop, conference, course, certification, webinar, mentoring
    start_date DATE NOT NULL,
    end_date DATE,
    hours DECIMAL(5,2) NOT NULL,
    credits DECIMAL(5,2),
    cost DECIMAL(10,2),
    paid_by_school BOOLEAN DEFAULT FALSE,
    certificate_url TEXT,
    notes TEXT,
    status VARCHAR(50) DEFAULT 'planned', -- planned, in_progress, completed, cancelled
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure extended columns exist for professional_development
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'professional_development' AND column_name = 'paid_by_school') THEN
        ALTER TABLE professional_development ADD COLUMN paid_by_school BOOLEAN DEFAULT FALSE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'professional_development' AND column_name = 'cost') THEN
        ALTER TABLE professional_development ADD COLUMN cost DECIMAL(10,2);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'professional_development' AND column_name = 'academic_year_id') THEN
        ALTER TABLE professional_development ADD COLUMN academic_year_id UUID REFERENCES academic_years(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'professional_development' AND column_name = 'category') THEN
        ALTER TABLE professional_development ADD COLUMN category VARCHAR(100);
    END IF;
END $$;

-- PD requirements
CREATE TABLE IF NOT EXISTS pd_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    required_hours DECIMAL(5,2) NOT NULL,
    required_credits DECIMAL(5,2),
    categories TEXT[],
    period_type VARCHAR(50) DEFAULT 'annual', -- annual, biennial, certification_cycle
    applies_to VARCHAR(50) DEFAULT 'all', -- all, teachers, staff, specific_roles
    role_ids UUID[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- PD goals
CREATE TABLE IF NOT EXISTS pd_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    staff_id UUID NOT NULL,
    goal_type VARCHAR(100) NOT NULL, -- certification, skill, leadership, content_area
    title VARCHAR(500) NOT NULL,
    description TEXT,
    target_date DATE,
    success_criteria TEXT,
    status VARCHAR(50) DEFAULT 'active', -- active, completed, cancelled
    completed_at TIMESTAMPTZ,
    reflection TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Staff certifications
CREATE TABLE IF NOT EXISTS staff_certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id),
    staff_id UUID NOT NULL,
    certification_name VARCHAR(255) NOT NULL,
    issuing_authority VARCHAR(255),
    certification_number VARCHAR(100),
    issue_date DATE,
    expiration_date DATE,
    renewal_requirements TEXT,
    document_url TEXT,
    status VARCHAR(50) DEFAULT 'active', -- active, expired, pending_renewal
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ENSURE ALL REQUIRED COLUMNS EXIST BEFORE INDEXES
-- ============================================================

DO $$
BEGIN
    -- Ensure parent_notification_preferences.parent_id exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'parent_notification_preferences' AND column_name = 'parent_id') THEN
        ALTER TABLE parent_notification_preferences ADD COLUMN parent_id UUID;
    END IF;

    -- Ensure conference_bookings columns exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'conference_bookings' AND column_name = 'parent_id') THEN
        ALTER TABLE conference_bookings ADD COLUMN parent_id UUID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'conference_bookings' AND column_name = 'slot_id') THEN
        ALTER TABLE conference_bookings ADD COLUMN slot_id UUID;
    END IF;

    -- Ensure conference_slots columns exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'conference_slots' AND column_name = 'teacher_id') THEN
        ALTER TABLE conference_slots ADD COLUMN teacher_id UUID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'conference_slots' AND column_name = 'date') THEN
        ALTER TABLE conference_slots ADD COLUMN date DATE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'conference_slots' AND column_name = 'school_id') THEN
        ALTER TABLE conference_slots ADD COLUMN school_id UUID;
    END IF;
END $$;

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_conference_slots_teacher_date ON conference_slots(teacher_id, date);
CREATE INDEX IF NOT EXISTS idx_conference_slots_school_date ON conference_slots(school_id, date);
CREATE INDEX IF NOT EXISTS idx_conference_bookings_parent ON conference_bookings(parent_id);
CREATE INDEX IF NOT EXISTS idx_conference_bookings_slot ON conference_bookings(slot_id);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at);

CREATE INDEX IF NOT EXISTS idx_parent_documents_student ON parent_documents(student_id);
CREATE INDEX IF NOT EXISTS idx_parent_documents_type ON parent_documents(document_type);

CREATE INDEX IF NOT EXISTS idx_professional_development_staff ON professional_development(staff_id);
CREATE INDEX IF NOT EXISTS idx_professional_development_school ON professional_development(school_id, academic_year_id);

CREATE INDEX IF NOT EXISTS idx_staff_certifications_staff ON staff_certifications(staff_id);
CREATE INDEX IF NOT EXISTS idx_staff_certifications_expiry ON staff_certifications(expiration_date);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE conference_slots ENABLE ROW LEVEL SECURITY;
ALTER TABLE conference_bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE parent_notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE parent_notification_channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE parent_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE professional_development ENABLE ROW LEVEL SECURITY;
ALTER TABLE pd_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE pd_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_certifications ENABLE ROW LEVEL SECURITY;

-- Parents can only see their own notifications
-- Parents can only see their own notifications
DROP POLICY IF EXISTS notifications_user_policy ON notifications;
CREATE POLICY notifications_user_policy ON notifications
    FOR ALL USING (user_id = auth.uid());

-- Parents can only manage their own preferences
DROP POLICY IF EXISTS notification_prefs_user_policy ON parent_notification_preferences;
CREATE POLICY notification_prefs_user_policy ON parent_notification_preferences
    FOR ALL USING (parent_id = auth.uid());

-- Parents can only see their own bookings
DROP POLICY IF EXISTS bookings_parent_policy ON conference_bookings;
CREATE POLICY bookings_parent_policy ON conference_bookings
    FOR ALL USING (parent_id = auth.uid());
