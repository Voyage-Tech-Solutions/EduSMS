-- ============================================================
-- INCREMENTAL MIGRATION SCRIPT
-- Safely adds missing tables without dropping existing ones
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- ADD MISSING TABLES ONLY
-- ============================================================

-- Academic Years (if not exists)
CREATE TABLE IF NOT EXISTS academic_years (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Terms (if not exists)
CREATE TABLE IF NOT EXISTS terms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID REFERENCES academic_years(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Teacher Assignments (if not exists)
CREATE TABLE IF NOT EXISTS teacher_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    effective_date DATE DEFAULT CURRENT_DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Guardians (if not exists)
CREATE TABLE IF NOT EXISTS guardians (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    relationship VARCHAR(50) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    address TEXT,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Student Guardians (if not exists)
CREATE TABLE IF NOT EXISTS student_guardians (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    guardian_id UUID NOT NULL REFERENCES guardians(id) ON DELETE CASCADE,
    relationship VARCHAR(50) NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    can_pickup BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_id, guardian_id)
);

-- Admissions (if not exists)
CREATE TABLE IF NOT EXISTS admissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    application_number VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20),
    grade_id UUID REFERENCES grades(id),
    guardian_name VARCHAR(255) NOT NULL,
    guardian_phone VARCHAR(20) NOT NULL,
    guardian_email VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'normal',
    application_date DATE DEFAULT CURRENT_DATE,
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Attendance Sessions (if not exists)
CREATE TABLE IF NOT EXISTS attendance_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    recorded_by UUID NOT NULL REFERENCES user_profiles(id),
    recorded_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    UNIQUE(class_id, date)
);

-- Payment Plans (if not exists)
CREATE TABLE IF NOT EXISTS payment_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    installment_count INTEGER NOT NULL,
    installment_amount DECIMAL(10,2) NOT NULL,
    start_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    notes TEXT,
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Invoice Adjustments (if not exists)
CREATE TABLE IF NOT EXISTS invoice_adjustments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    adjustment_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    reason TEXT NOT NULL,
    notes TEXT,
    approved_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Documents (if not exists)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL,
    file_url TEXT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER,
    status VARCHAR(50) DEFAULT 'pending',
    expiry_date DATE,
    uploaded_by UUID REFERENCES user_profiles(id),
    verified_by UUID REFERENCES user_profiles(id),
    verified_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Document Requirements (if not exists)
CREATE TABLE IF NOT EXISTS document_requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL,
    is_mandatory BOOLEAN DEFAULT true,
    applies_to VARCHAR(50) DEFAULT 'all',
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Risk Cases (if not exists)
CREATE TABLE IF NOT EXISTS risk_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    risk_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(50) DEFAULT 'open',
    opened_by UUID NOT NULL REFERENCES user_profiles(id),
    opened_at TIMESTAMP DEFAULT NOW(),
    closed_by UUID REFERENCES user_profiles(id),
    closed_at TIMESTAMP,
    notes TEXT
);

-- Interventions (if not exists)
CREATE TABLE IF NOT EXISTS interventions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    risk_case_id UUID NOT NULL REFERENCES risk_cases(id) ON DELETE CASCADE,
    intervention_type VARCHAR(100) NOT NULL,
    assigned_to UUID REFERENCES user_profiles(id),
    due_date DATE,
    status VARCHAR(50) DEFAULT 'pending',
    notes TEXT,
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Approval Requests (if not exists)
CREATE TABLE IF NOT EXISTS approval_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_name VARCHAR(255),
    description TEXT,
    requested_by UUID NOT NULL REFERENCES user_profiles(id),
    submitted_at TIMESTAMP DEFAULT NOW(),
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'pending',
    decision VARCHAR(20),
    decided_by UUID REFERENCES user_profiles(id),
    decided_at TIMESTAMP,
    notes TEXT
);

-- Lesson Plans (if not exists)
CREATE TABLE IF NOT EXISTS lesson_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    term_id UUID REFERENCES terms(id),
    date DATE NOT NULL,
    time_slot VARCHAR(50),
    topic VARCHAR(255) NOT NULL,
    objectives TEXT,
    activities TEXT,
    homework TEXT,
    status VARCHAR(50) DEFAULT 'planned',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Resources (if not exists)
CREATE TABLE IF NOT EXISTS resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    uploaded_by UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    url TEXT NOT NULL,
    tags TEXT[],
    visibility VARCHAR(50) DEFAULT 'private',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Messages (if not exists)
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    recipient_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    subject VARCHAR(255),
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP,
    parent_message_id UUID REFERENCES messages(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Notifications Log (if not exists)
CREATE TABLE IF NOT EXISTS notifications_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    recipient_type VARCHAR(50) NOT NULL,
    delivery_method VARCHAR(50) NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    subject VARCHAR(255),
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    sent_by UUID REFERENCES user_profiles(id),
    sent_at TIMESTAMP DEFAULT NOW()
);

-- School Settings (if not exists)
CREATE TABLE IF NOT EXISTS school_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50) DEFAULT 'string',
    updated_by UUID REFERENCES user_profiles(id),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(school_id, setting_key)
);

-- Audit Logs (if not exists)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Report Submissions (if not exists)
CREATE TABLE IF NOT EXISTS report_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    teacher_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    term_id UUID REFERENCES terms(id),
    grade_id UUID REFERENCES grades(id),
    report_type VARCHAR(50) NOT NULL,
    submitted_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'submitted',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Academic Targets (if not exists)
CREATE TABLE IF NOT EXISTS academic_targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    grade_id UUID REFERENCES grades(id),
    subject_id UUID REFERENCES subjects(id),
    pass_rate_target DECIMAL(5,2),
    completion_target DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Notification Templates (if not exists)
CREATE TABLE IF NOT EXISTS notification_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    template_type VARCHAR(50) NOT NULL,
    subject VARCHAR(255),
    body TEXT NOT NULL,
    variables TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- CREATE INDEXES (IF NOT EXISTS)
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_academic_years_school ON academic_years(school_id);
CREATE INDEX IF NOT EXISTS idx_terms_school ON terms(school_id);
CREATE INDEX IF NOT EXISTS idx_teacher_assignments_teacher ON teacher_assignments(teacher_id);
CREATE INDEX IF NOT EXISTS idx_teacher_assignments_class ON teacher_assignments(class_id);
CREATE INDEX IF NOT EXISTS idx_guardians_user ON guardians(user_id);
CREATE INDEX IF NOT EXISTS idx_student_guardians_student ON student_guardians(student_id);
CREATE INDEX IF NOT EXISTS idx_student_guardians_guardian ON student_guardians(guardian_id);
CREATE INDEX IF NOT EXISTS idx_admissions_school ON admissions(school_id);
CREATE INDEX IF NOT EXISTS idx_admissions_status ON admissions(status);
CREATE INDEX IF NOT EXISTS idx_attendance_sessions_class ON attendance_sessions(class_id);
CREATE INDEX IF NOT EXISTS idx_attendance_sessions_date ON attendance_sessions(date);
CREATE INDEX IF NOT EXISTS idx_payment_plans_invoice ON payment_plans(invoice_id);
CREATE INDEX IF NOT EXISTS idx_invoice_adjustments_invoice ON invoice_adjustments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_documents_school ON documents(school_id);
CREATE INDEX IF NOT EXISTS idx_documents_student ON documents(student_id);
CREATE INDEX IF NOT EXISTS idx_document_requirements_school ON document_requirements(school_id);
CREATE INDEX IF NOT EXISTS idx_risk_cases_school ON risk_cases(school_id);
CREATE INDEX IF NOT EXISTS idx_risk_cases_student ON risk_cases(student_id);
CREATE INDEX IF NOT EXISTS idx_risk_cases_status ON risk_cases(status);
CREATE INDEX IF NOT EXISTS idx_interventions_risk_case ON interventions(risk_case_id);
CREATE INDEX IF NOT EXISTS idx_approval_requests_school ON approval_requests(school_id);
CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests(status);
CREATE INDEX IF NOT EXISTS idx_approval_requests_priority ON approval_requests(priority);
CREATE INDEX IF NOT EXISTS idx_lesson_plans_teacher ON lesson_plans(teacher_id);
CREATE INDEX IF NOT EXISTS idx_lesson_plans_class ON lesson_plans(class_id);
CREATE INDEX IF NOT EXISTS idx_resources_uploaded_by ON resources(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_id);
CREATE INDEX IF NOT EXISTS idx_notifications_log_school ON notifications_log(school_id);
CREATE INDEX IF NOT EXISTS idx_school_settings_school ON school_settings(school_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_school ON audit_logs(school_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);

-- ============================================================
-- MIGRATION COMPLETE
-- ============================================================
