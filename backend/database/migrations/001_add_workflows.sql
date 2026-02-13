-- ============================================================
-- ADMISSIONS, TRANSFERS & LIFECYCLE WORKFLOWS
-- ============================================================

-- Admissions Applications Table
CREATE TABLE IF NOT EXISTS admissions_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    application_no VARCHAR(50) UNIQUE NOT NULL,
    student_first_name VARCHAR(100) NOT NULL,
    student_last_name VARCHAR(100) NOT NULL,
    student_dob DATE NOT NULL,
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    grade_applied_id UUID REFERENCES grades(id),
    term_id UUID,
    status VARCHAR(20) DEFAULT 'incomplete' CHECK (status IN ('incomplete', 'pending', 'under_review', 'approved', 'declined', 'enrolled', 'withdrawn')),
    submitted_at TIMESTAMPTZ,
    reviewer_id UUID REFERENCES user_profiles(id),
    decision_by UUID REFERENCES user_profiles(id),
    decision_at TIMESTAMPTZ,
    decision_reason TEXT,
    review_notes TEXT,
    student_id UUID REFERENCES students(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_admissions_school ON admissions_applications(school_id);
CREATE INDEX IF NOT EXISTS idx_admissions_status ON admissions_applications(status);

-- Admissions Documents
CREATE TABLE IF NOT EXISTS admissions_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID NOT NULL REFERENCES admissions_applications(id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL,
    file_url TEXT,
    uploaded BOOLEAN DEFAULT false,
    verified BOOLEAN DEFAULT false,
    verified_by UUID REFERENCES user_profiles(id),
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Student Transfers Table
CREATE TABLE IF NOT EXISTS student_transfers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    transfer_type VARCHAR(20) NOT NULL CHECK (transfer_type IN ('incoming', 'outgoing', 'internal')),
    from_school VARCHAR(200),
    to_school VARCHAR(200),
    from_grade_id UUID REFERENCES grades(id),
    to_grade_id UUID REFERENCES grades(id),
    from_class_id UUID REFERENCES classes(id),
    to_class_id UUID REFERENCES classes(id),
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'completed', 'cancelled')),
    requested_by UUID REFERENCES user_profiles(id),
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    approved_by UUID REFERENCES user_profiles(id),
    approved_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transfers_student ON student_transfers(student_id);
CREATE INDEX IF NOT EXISTS idx_transfers_status ON student_transfers(status);

-- Student Lifecycle Events
CREATE TABLE IF NOT EXISTS student_lifecycle_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('admission', 'promotion', 'transfer', 'suspension', 'expulsion', 'withdrawal', 'graduation', 'status_change')),
    from_status VARCHAR(20),
    to_status VARCHAR(20),
    from_grade_id UUID REFERENCES grades(id),
    to_grade_id UUID REFERENCES grades(id),
    event_date DATE NOT NULL,
    reason TEXT,
    notes TEXT,
    recorded_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lifecycle_student ON student_lifecycle_events(student_id);
CREATE INDEX IF NOT EXISTS idx_lifecycle_type ON student_lifecycle_events(event_type);
CREATE INDEX IF NOT EXISTS idx_lifecycle_date ON student_lifecycle_events(event_date);

-- RLS Policies
ALTER TABLE admissions_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE admissions_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_transfers ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_lifecycle_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS admissions_isolation ON admissions_applications;
CREATE POLICY admissions_isolation ON admissions_applications
    FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS admissions_docs_isolation ON admissions_documents;
CREATE POLICY admissions_docs_isolation ON admissions_documents
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM admissions_applications a
            WHERE a.id = admissions_documents.application_id
            AND a.school_id = get_user_school_id()
        )
    );

DROP POLICY IF EXISTS transfers_isolation ON student_transfers;
CREATE POLICY transfers_isolation ON student_transfers
    FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS lifecycle_isolation ON student_lifecycle_events;
CREATE POLICY lifecycle_isolation ON student_lifecycle_events
    FOR ALL USING (school_id = get_user_school_id());

-- Triggers
DROP TRIGGER IF EXISTS update_admissions_updated_at ON admissions_applications;
CREATE TRIGGER update_admissions_updated_at BEFORE UPDATE ON admissions_applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS update_transfers_updated_at ON student_transfers;
CREATE TRIGGER update_transfers_updated_at BEFORE UPDATE ON student_transfers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
