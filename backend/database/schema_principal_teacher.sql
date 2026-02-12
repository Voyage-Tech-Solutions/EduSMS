-- ============================================================
-- PRINCIPAL & TEACHER FEATURES - DATABASE SCHEMA
-- ============================================================

-- ============================================================
-- 1. APPROVAL SYSTEM (Principal Approvals Page)
-- ============================================================

CREATE TABLE IF NOT EXISTS approval_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL CHECK (type IN ('admission', 'transfer', 'writeoff', 'payment_plan', 'role_change', 'policy_override', 'risk_closure')),
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    requested_by UUID NOT NULL REFERENCES user_profiles(id),
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'escalated')),
    decision VARCHAR(20),
    decided_by UUID REFERENCES user_profiles(id),
    decided_at TIMESTAMPTZ,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_approval_requests_school ON approval_requests(school_id);
CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests(status);
CREATE INDEX IF NOT EXISTS idx_approval_requests_type ON approval_requests(type);
CREATE INDEX IF NOT EXISTS idx_approval_requests_priority ON approval_requests(priority);
CREATE INDEX IF NOT EXISTS idx_approval_requests_requested_by ON approval_requests(requested_by);

DO $$ BEGIN
    ALTER TABLE approval_requests ENABLE ROW LEVEL SECURITY;
    CREATE POLICY approval_requests_isolation ON approval_requests FOR ALL USING (school_id = get_user_school_id());
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================
-- 2. TEACHER PLANNING SYSTEM
-- ============================================================

-- Lesson Plans
CREATE TABLE IF NOT EXISTS lesson_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    teacher_id UUID NOT NULL REFERENCES user_profiles(id),
    class_id UUID NOT NULL REFERENCES classes(id),
    subject_id UUID NOT NULL REFERENCES subjects(id),
    term_id UUID REFERENCES terms(id),
    date DATE NOT NULL,
    time_slot VARCHAR(50),
    topic VARCHAR(200) NOT NULL,
    objectives TEXT,
    activities TEXT,
    homework TEXT,
    status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'delivered', 'missed', 'rescheduled')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lesson_plans_school ON lesson_plans(school_id);
CREATE INDEX IF NOT EXISTS idx_lesson_plans_teacher ON lesson_plans(teacher_id);
CREATE INDEX IF NOT EXISTS idx_lesson_plans_class ON lesson_plans(class_id);
CREATE INDEX IF NOT EXISTS idx_lesson_plans_date ON lesson_plans(date);

-- Assessment Plans (before converting to actual assessments)
CREATE TABLE IF NOT EXISTS assessment_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    teacher_id UUID NOT NULL REFERENCES user_profiles(id),
    class_id UUID NOT NULL REFERENCES classes(id),
    subject_id UUID NOT NULL REFERENCES subjects(id),
    term_id UUID REFERENCES terms(id),
    title VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,
    planned_date DATE,
    total_marks DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'planned' CHECK (status IN ('planned', 'converted', 'cancelled')),
    linked_assessment_id UUID REFERENCES assessments(id),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assessment_plans_school ON assessment_plans(school_id);
CREATE INDEX IF NOT EXISTS idx_assessment_plans_teacher ON assessment_plans(teacher_id);
CREATE INDEX IF NOT EXISTS idx_assessment_plans_class ON assessment_plans(class_id);

-- Resources Library
CREATE TABLE IF NOT EXISTS resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    uploaded_by UUID NOT NULL REFERENCES user_profiles(id),
    class_id UUID REFERENCES classes(id),
    subject_id UUID REFERENCES subjects(id),
    title VARCHAR(200) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('file', 'link', 'video', 'document')),
    url TEXT NOT NULL,
    file_size BIGINT,
    tags TEXT[],
    visibility VARCHAR(20) DEFAULT 'private' CHECK (visibility IN ('private', 'class', 'grade', 'school')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resources_school ON resources(school_id);
CREATE INDEX IF NOT EXISTS idx_resources_uploaded_by ON resources(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_resources_class ON resources(class_id);
CREATE INDEX IF NOT EXISTS idx_resources_subject ON resources(subject_id);

-- Curriculum Units (optional but powerful)
CREATE TABLE IF NOT EXISTS curriculum_units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id),
    grade_id UUID NOT NULL REFERENCES grades(id),
    unit_name VARCHAR(200) NOT NULL,
    description TEXT,
    order_index INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_curriculum_units_school ON curriculum_units(school_id);
CREATE INDEX IF NOT EXISTS idx_curriculum_units_subject ON curriculum_units(subject_id);
CREATE INDEX IF NOT EXISTS idx_curriculum_units_grade ON curriculum_units(grade_id);

-- Coverage Tracking
CREATE TABLE IF NOT EXISTS coverage_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    unit_id UUID NOT NULL REFERENCES curriculum_units(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id),
    term_id UUID REFERENCES terms(id),
    planned_date DATE,
    completed_date DATE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'skipped')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_coverage_tracking_school ON coverage_tracking(school_id);
CREATE INDEX IF NOT EXISTS idx_coverage_tracking_unit ON coverage_tracking(unit_id);
CREATE INDEX IF NOT EXISTS idx_coverage_tracking_class ON coverage_tracking(class_id);

DO $$ BEGIN
    ALTER TABLE lesson_plans ENABLE ROW LEVEL SECURITY;
    ALTER TABLE assessment_plans ENABLE ROW LEVEL SECURITY;
    ALTER TABLE resources ENABLE ROW LEVEL SECURITY;
    ALTER TABLE curriculum_units ENABLE ROW LEVEL SECURITY;
    ALTER TABLE coverage_tracking ENABLE ROW LEVEL SECURITY;
    
    CREATE POLICY lesson_plans_isolation ON lesson_plans FOR ALL USING (school_id = get_user_school_id());
    CREATE POLICY assessment_plans_isolation ON assessment_plans FOR ALL USING (school_id = get_user_school_id());
    CREATE POLICY resources_isolation ON resources FOR ALL USING (school_id = get_user_school_id());
    CREATE POLICY curriculum_units_isolation ON curriculum_units FOR ALL USING (school_id = get_user_school_id());
    CREATE POLICY coverage_tracking_isolation ON coverage_tracking FOR ALL USING (school_id = get_user_school_id());
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================
-- 3. GRADEBOOK ENHANCEMENTS
-- ============================================================

-- Gradebook Locks (prevent edits after finalization)
CREATE TABLE IF NOT EXISTS gradebook_locks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id),
    subject_id UUID NOT NULL REFERENCES subjects(id),
    term_id UUID REFERENCES terms(id),
    locked_by UUID NOT NULL REFERENCES user_profiles(id),
    locked_at TIMESTAMPTZ DEFAULT NOW(),
    unlock_requested BOOLEAN DEFAULT false,
    unlock_requested_at TIMESTAMPTZ,
    unlock_approved_by UUID REFERENCES user_profiles(id),
    unlock_approved_at TIMESTAMPTZ,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(class_id, subject_id, term_id)
);

CREATE INDEX IF NOT EXISTS idx_gradebook_locks_school ON gradebook_locks(school_id);
CREATE INDEX IF NOT EXISTS idx_gradebook_locks_class ON gradebook_locks(class_id);
CREATE INDEX IF NOT EXISTS idx_gradebook_locks_subject ON gradebook_locks(subject_id);

DO $$ BEGIN
    ALTER TABLE gradebook_locks ENABLE ROW LEVEL SECURITY;
    CREATE POLICY gradebook_locks_isolation ON gradebook_locks FOR ALL USING (school_id = get_user_school_id());
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================
-- 4. STUDENT NOTIFICATIONS (Principal Students Page)
-- ============================================================

CREATE TABLE IF NOT EXISTS parent_notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    sent_by UUID NOT NULL REFERENCES user_profiles(id),
    notification_type VARCHAR(50) NOT NULL,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('email', 'sms', 'app', 'portal')),
    template_id VARCHAR(100),
    subject VARCHAR(200),
    message TEXT NOT NULL,
    include_performance_summary BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'delivered', 'read')),
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_parent_notifications_school ON parent_notifications(school_id);
CREATE INDEX IF NOT EXISTS idx_parent_notifications_student ON parent_notifications(student_id);
CREATE INDEX IF NOT EXISTS idx_parent_notifications_status ON parent_notifications(status);

DO $$ BEGIN
    ALTER TABLE parent_notifications ENABLE ROW LEVEL SECURITY;
    CREATE POLICY parent_notifications_isolation ON parent_notifications FOR ALL USING (school_id = get_user_school_id());
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================
-- 5. AUDIT LOGGING (All approval decisions)
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_profiles(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    before_state JSONB,
    after_state JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_school ON audit_logs(school_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

DO $$ BEGIN
    ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
    CREATE POLICY audit_logs_isolation ON audit_logs FOR ALL USING (school_id = get_user_school_id());
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================
-- 6. TRIGGERS FOR UPDATED_AT
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$ BEGIN
    CREATE TRIGGER update_approval_requests_updated_at BEFORE UPDATE ON approval_requests FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    CREATE TRIGGER update_lesson_plans_updated_at BEFORE UPDATE ON lesson_plans FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    CREATE TRIGGER update_assessment_plans_updated_at BEFORE UPDATE ON assessment_plans FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    CREATE TRIGGER update_resources_updated_at BEFORE UPDATE ON resources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    CREATE TRIGGER update_curriculum_units_updated_at BEFORE UPDATE ON curriculum_units FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    CREATE TRIGGER update_coverage_tracking_updated_at BEFORE UPDATE ON coverage_tracking FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================
-- SCHEMA COMPLETE
-- ============================================================
