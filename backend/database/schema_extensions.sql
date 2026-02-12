-- ============================================================
-- Schema Extensions for Admissions & Documents
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
    parent_id UUID,
    status VARCHAR(20) DEFAULT 'incomplete' CHECK (status IN ('incomplete', 'pending', 'under_review', 'approved', 'enrolled', 'declined', 'withdrawn')),
    submitted_at TIMESTAMPTZ,
    reviewer_id UUID REFERENCES user_profiles(id),
    review_notes TEXT,
    decision_at TIMESTAMPTZ,
    decision_by UUID REFERENCES user_profiles(id),
    decision_reason TEXT,
    student_id UUID REFERENCES students(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_admissions_school ON admissions_applications(school_id);
CREATE INDEX idx_admissions_status ON admissions_applications(status);
CREATE INDEX idx_admissions_grade ON admissions_applications(grade_applied_id);

-- Admissions Documents Table
CREATE TABLE IF NOT EXISTS admissions_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID NOT NULL REFERENCES admissions_applications(id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL,
    file_url TEXT,
    uploaded BOOLEAN DEFAULT false,
    verified BOOLEAN DEFAULT false,
    verified_by UUID REFERENCES user_profiles(id),
    verified_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_admissions_docs_app ON admissions_documents(application_id);

-- Student Documents Table
CREATE TABLE IF NOT EXISTS student_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL,
    file_url TEXT,
    uploaded BOOLEAN DEFAULT false,
    verified BOOLEAN DEFAULT false,
    verified_by UUID REFERENCES user_profiles(id),
    verified_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_student_docs_student ON student_documents(student_id);

-- Terms Table (for academic terms/semesters)
CREATE TABLE IF NOT EXISTS terms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT false,
    year INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(school_id, name, year)
);

CREATE INDEX idx_terms_school ON terms(school_id);
CREATE INDEX idx_terms_active ON terms(is_active);

-- Enable RLS
ALTER TABLE admissions_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE admissions_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE terms ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY admissions_isolation ON admissions_applications
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY admissions_docs_isolation ON admissions_documents
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM admissions_applications a
            WHERE a.id = admissions_documents.application_id
            AND a.school_id = get_user_school_id()
        )
    );

CREATE POLICY student_docs_isolation ON student_documents
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM students s
            WHERE s.id = student_documents.student_id
            AND s.school_id = get_user_school_id()
        )
    );

CREATE POLICY terms_isolation ON terms
    FOR ALL USING (school_id = get_user_school_id());

-- Triggers
CREATE TRIGGER update_admissions_updated_at BEFORE UPDATE ON admissions_applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_admissions_docs_updated_at BEFORE UPDATE ON admissions_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_student_docs_updated_at BEFORE UPDATE ON student_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_terms_updated_at BEFORE UPDATE ON terms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- Documents & Compliance Extensions
-- ============================================================

-- Document Requirements Table
CREATE TABLE IF NOT EXISTS document_requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN ('student', 'parent', 'staff', 'application')),
    document_type VARCHAR(100) NOT NULL,
    required BOOLEAN DEFAULT true,
    grade_id UUID REFERENCES grades(id),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(school_id, entity_type, document_type, grade_id)
);

CREATE INDEX idx_doc_requirements_school ON document_requirements(school_id);
CREATE INDEX idx_doc_requirements_type ON document_requirements(entity_type);

-- Document Requests Table
CREATE TABLE IF NOT EXISTS document_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    requested_by UUID REFERENCES user_profiles(id),
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    message TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'ignored')),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_doc_requests_school ON document_requests(school_id);
CREATE INDEX idx_doc_requests_entity ON document_requests(entity_id);
CREATE INDEX idx_doc_requests_status ON document_requests(status);

-- School Settings Table
CREATE TABLE IF NOT EXISTS school_settings (
    school_id UUID PRIMARY KEY REFERENCES schools(id) ON DELETE CASCADE,
    timezone VARCHAR(50) DEFAULT 'UTC',
    currency VARCHAR(10) DEFAULT 'USD',
    country VARCHAR(100),
    primary_color VARCHAR(20) DEFAULT '#10b981',
    invoice_prefix VARCHAR(10) DEFAULT 'INV',
    invoice_next_number INTEGER DEFAULT 1,
    default_due_days INTEGER DEFAULT 30,
    allow_overpayment BOOLEAN DEFAULT false,
    allow_future_attendance BOOLEAN DEFAULT false,
    late_cutoff_time TIME DEFAULT '08:30:00',
    sms_enabled BOOLEAN DEFAULT false,
    email_enabled BOOLEAN DEFAULT true,
    updated_by UUID REFERENCES user_profiles(id),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE document_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_settings ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY doc_requirements_isolation ON document_requirements
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY doc_requests_isolation ON document_requests
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY school_settings_isolation ON school_settings
    FOR ALL USING (school_id = get_user_school_id());

-- Triggers
CREATE TRIGGER update_doc_requirements_updated_at BEFORE UPDATE ON document_requirements
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_school_settings_updated_at BEFORE UPDATE ON school_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Add expiry_date and status to student_documents
ALTER TABLE student_documents ADD COLUMN IF NOT EXISTS expiry_date DATE;
ALTER TABLE student_documents ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'uploaded' CHECK (status IN ('missing', 'uploaded', 'verified', 'expired', 'rejected'));
ALTER TABLE student_documents ADD COLUMN IF NOT EXISTS file_name VARCHAR(255);
ALTER TABLE student_documents ADD COLUMN IF NOT EXISTS file_size BIGINT;
ALTER TABLE student_documents ADD COLUMN IF NOT EXISTS mime_type VARCHAR(100);
ALTER TABLE student_documents ADD COLUMN IF NOT EXISTS uploaded_by UUID REFERENCES user_profiles(id);

-- Add same fields to admissions_documents
ALTER TABLE admissions_documents ADD COLUMN IF NOT EXISTS expiry_date DATE;
ALTER TABLE admissions_documents ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'uploaded' CHECK (status IN ('missing', 'uploaded', 'verified', 'expired', 'rejected'));
ALTER TABLE admissions_documents ADD COLUMN IF NOT EXISTS file_name VARCHAR(255);
ALTER TABLE admissions_documents ADD COLUMN IF NOT EXISTS file_size BIGINT;
ALTER TABLE admissions_documents ADD COLUMN IF NOT EXISTS mime_type VARCHAR(100);
ALTER TABLE admissions_documents ADD COLUMN IF NOT EXISTS uploaded_by UUID REFERENCES user_profiles(id);

CREATE INDEX idx_student_docs_status ON student_documents(status);
CREATE INDEX idx_student_docs_expiry ON student_documents(expiry_date);
CREATE INDEX idx_admissions_docs_status ON admissions_documents(status);
CREATE INDEX idx_admissions_docs_expiry ON admissions_documents(expiry_date);
