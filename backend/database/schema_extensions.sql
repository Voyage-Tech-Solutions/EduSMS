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

-- Terms Table
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

ALTER TABLE admissions_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE admissions_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE terms ENABLE ROW LEVEL SECURITY;

CREATE POLICY admissions_isolation ON admissions_applications FOR ALL USING (school_id = get_user_school_id());
CREATE POLICY admissions_docs_isolation ON admissions_documents FOR ALL USING (EXISTS (SELECT 1 FROM admissions_applications a WHERE a.id = admissions_documents.application_id AND a.school_id = get_user_school_id()));
CREATE POLICY student_docs_isolation ON student_documents FOR ALL USING (EXISTS (SELECT 1 FROM students s WHERE s.id = student_documents.student_id AND s.school_id = get_user_school_id()));
CREATE POLICY terms_isolation ON terms FOR ALL USING (school_id = get_user_school_id());

CREATE TRIGGER update_admissions_updated_at BEFORE UPDATE ON admissions_applications FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_admissions_docs_updated_at BEFORE UPDATE ON admissions_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_student_docs_updated_at BEFORE UPDATE ON student_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_terms_updated_at BEFORE UPDATE ON terms FOR EACH ROW EXECUTE FUNCTION update_updated_at();

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

ALTER TABLE document_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY doc_requirements_isolation ON document_requirements FOR ALL USING (school_id = get_user_school_id());
CREATE POLICY doc_requests_isolation ON document_requests FOR ALL USING (school_id = get_user_school_id());
CREATE POLICY school_settings_isolation ON school_settings FOR ALL USING (school_id = get_user_school_id());

CREATE TRIGGER update_doc_requirements_updated_at BEFORE UPDATE ON document_requirements FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_school_settings_updated_at BEFORE UPDATE ON school_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at();

ALTER TABLE student_documents ADD COLUMN IF NOT EXISTS expiry_date DATE;
ALTER TABLE student_documents ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'uploaded' CHECK (status IN ('missing', 'uploaded', 'verified', 'expired', 'rejected'));
ALTER TABLE student_documents ADD COLUMN IF NOT EXISTS file_name VARCHAR(255);
ALTER TABLE student_documents ADD COLUMN IF NOT EXISTS file_size BIGINT;
ALTER TABLE student_documents ADD COLUMN IF NOT EXISTS mime_type VARCHAR(100);
ALTER TABLE student_documents ADD COLUMN IF NOT EXISTS uploaded_by UUID REFERENCES user_profiles(id);

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

-- Attendance Sessions
CREATE TABLE IF NOT EXISTS attendance_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    recorded_by UUID REFERENCES user_profiles(id),
    override_mode BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(class_id, date)
);

CREATE INDEX idx_attendance_sessions_school ON attendance_sessions(school_id);
CREATE INDEX idx_attendance_sessions_class_date ON attendance_sessions(class_id, date);
ALTER TABLE attendance_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY attendance_sessions_isolation ON attendance_sessions FOR ALL USING (school_id = get_user_school_id());
CREATE TRIGGER update_attendance_sessions_updated_at BEFORE UPDATE ON attendance_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Fee Structures
CREATE TABLE IF NOT EXISTS fee_structures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    grade_id UUID REFERENCES grades(id),
    term_id UUID REFERENCES terms(id),
    name VARCHAR(200) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    due_days_after_issue INTEGER DEFAULT 30,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_fee_structures_school ON fee_structures(school_id);
CREATE INDEX idx_fee_structures_grade ON fee_structures(grade_id);

CREATE TABLE IF NOT EXISTS payment_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    total_amount DECIMAL(10,2) NOT NULL,
    installment_count INTEGER NOT NULL,
    installment_amount DECIMAL(10,2) NOT NULL,
    start_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payment_plans_invoice ON payment_plans(invoice_id);

CREATE TABLE IF NOT EXISTS invoice_adjustments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    adjustment_type VARCHAR(50) NOT NULL CHECK (adjustment_type IN ('writeoff', 'discount', 'penalty', 'refund')),
    amount DECIMAL(10,2) NOT NULL,
    reason TEXT NOT NULL,
    approved_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_invoice_adjustments_invoice ON invoice_adjustments(invoice_id);

ALTER TABLE fee_structures ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_adjustments ENABLE ROW LEVEL SECURITY;

CREATE POLICY fee_structures_isolation ON fee_structures FOR ALL USING (school_id = get_user_school_id());
CREATE POLICY payment_plans_isolation ON payment_plans FOR ALL USING (EXISTS (SELECT 1 FROM invoices i WHERE i.id = payment_plans.invoice_id AND i.school_id = get_user_school_id()));
CREATE POLICY invoice_adjustments_isolation ON invoice_adjustments FOR ALL USING (EXISTS (SELECT 1 FROM invoices i WHERE i.id = invoice_adjustments.invoice_id AND i.school_id = get_user_school_id()));

-- Risk Cases
CREATE TABLE IF NOT EXISTS risk_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    risk_type VARCHAR(50) NOT NULL CHECK (risk_type IN ('attendance', 'academic', 'financial', 'behavior', 'manual')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    opened_by UUID REFERENCES user_profiles(id),
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_risk_cases_school ON risk_cases(school_id);
CREATE INDEX idx_risk_cases_student ON risk_cases(student_id);
CREATE INDEX idx_risk_cases_status ON risk_cases(status);

CREATE TABLE IF NOT EXISTS interventions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    risk_case_id UUID NOT NULL REFERENCES risk_cases(id) ON DELETE CASCADE,
    intervention_type VARCHAR(100) NOT NULL,
    assigned_to UUID REFERENCES user_profiles(id),
    due_date DATE,
    notes TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_interventions_case ON interventions(risk_case_id);
CREATE INDEX idx_interventions_assigned ON interventions(assigned_to);

CREATE TABLE IF NOT EXISTS report_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    teacher_id UUID NOT NULL REFERENCES user_profiles(id),
    term_id UUID REFERENCES terms(id),
    report_type VARCHAR(50) NOT NULL,
    submitted_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'submitted', 'late', 'approved')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_report_submissions_school ON report_submissions(school_id);
CREATE INDEX idx_report_submissions_teacher ON report_submissions(teacher_id);

ALTER TABLE risk_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE interventions ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_submissions ENABLE ROW LEVEL SECURITY;

CREATE POLICY risk_cases_isolation ON risk_cases FOR ALL USING (school_id = get_user_school_id());
CREATE POLICY interventions_isolation ON interventions FOR ALL USING (EXISTS (SELECT 1 FROM risk_cases rc WHERE rc.id = interventions.risk_case_id AND rc.school_id = get_user_school_id()));
CREATE POLICY report_submissions_isolation ON report_submissions FOR ALL USING (school_id = get_user_school_id());

-- Assessments
CREATE TABLE IF NOT EXISTS assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    term_id UUID REFERENCES terms(id),
    grade_id UUID REFERENCES grades(id),
    class_id UUID REFERENCES classes(id),
    subject_id UUID REFERENCES subjects(id),
    teacher_id UUID REFERENCES user_profiles(id),
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    total_marks DECIMAL(5,2) NOT NULL,
    date_assigned DATE,
    due_date DATE,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'closed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_assessments_school ON assessments(school_id);
CREATE INDEX idx_assessments_class ON assessments(class_id);
CREATE INDEX idx_assessments_teacher ON assessments(teacher_id);

CREATE TABLE IF NOT EXISTS assessment_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    score DECIMAL(5,2),
    percentage DECIMAL(5,2),
    submitted_at TIMESTAMPTZ,
    marked_by UUID REFERENCES user_profiles(id),
    marked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(assessment_id, student_id)
);

CREATE INDEX idx_assessment_scores_assessment ON assessment_scores(assessment_id);
CREATE INDEX idx_assessment_scores_student ON assessment_scores(student_id);

CREATE TABLE IF NOT EXISTS grade_targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    grade_id UUID REFERENCES grades(id),
    subject_id UUID REFERENCES subjects(id),
    pass_mark DECIMAL(5,2) DEFAULT 50.00,
    target_pass_rate DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_grade_targets_school ON grade_targets(school_id);

ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE grade_targets ENABLE ROW LEVEL SECURITY;

CREATE POLICY assessments_isolation ON assessments FOR ALL USING (school_id = get_user_school_id());
CREATE POLICY assessment_scores_isolation ON assessment_scores FOR ALL USING (EXISTS (SELECT 1 FROM assessments a WHERE a.id = assessment_scores.assessment_id AND a.school_id = get_user_school_id()));
CREATE POLICY grade_targets_isolation ON grade_targets FOR ALL USING (school_id = get_user_school_id());

CREATE TRIGGER update_assessments_updated_at BEFORE UPDATE ON assessments FOR EACH ROW EXECUTE FUNCTION update_updated_at();
