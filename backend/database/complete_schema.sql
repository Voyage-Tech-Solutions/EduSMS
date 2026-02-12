-- ============================================================
-- EDUCORE COMPLETE DATABASE SCHEMA
-- Production-ready Supabase schema with RLS, indexes, and triggers
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- CORE TABLES
-- ============================================================

-- Schools (Multi-tenant root)
CREATE TABLE schools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(255),
    logo_url TEXT,
    subscription_tier VARCHAR(50) DEFAULT 'basic',
    subscription_status VARCHAR(50) DEFAULT 'active',
    max_students INTEGER DEFAULT 500,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User Profiles (All users)
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(50) NOT NULL, -- system_admin, principal, teacher, office_admin, finance_officer, parent, student
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ACADEMIC STRUCTURE
-- ============================================================

-- Academic Years
CREATE TABLE academic_years (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Terms
CREATE TABLE terms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID REFERENCES academic_years(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Grades
CREATE TABLE grades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    level INTEGER NOT NULL,
    capacity INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Classes
CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    grade_id UUID NOT NULL REFERENCES grades(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    teacher_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    capacity INTEGER DEFAULT 40,
    room_number VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Subjects
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50),
    description TEXT,
    is_core BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Teacher Assignments
CREATE TABLE teacher_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    effective_date DATE DEFAULT CURRENT_DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- STUDENTS & ENROLLMENT
-- ============================================================

-- Students
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    admission_number VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20),
    grade_id UUID REFERENCES grades(id) ON DELETE SET NULL,
    class_id UUID REFERENCES classes(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'active', -- active, inactive, transferred, graduated
    admission_date DATE DEFAULT CURRENT_DATE,
    photo_url TEXT,
    address TEXT,
    medical_info TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Guardians
CREATE TABLE guardians (
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

-- Student Guardians (Many-to-Many)
CREATE TABLE student_guardians (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    guardian_id UUID NOT NULL REFERENCES guardians(id) ON DELETE CASCADE,
    relationship VARCHAR(50) NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    can_pickup BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(student_id, guardian_id)
);

-- Admissions
CREATE TABLE admissions (
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
    status VARCHAR(50) DEFAULT 'pending', -- pending, approved, rejected, enrolled
    priority VARCHAR(20) DEFAULT 'normal',
    application_date DATE DEFAULT CURRENT_DATE,
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ATTENDANCE
-- ============================================================

-- Attendance Sessions
CREATE TABLE attendance_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    recorded_by UUID NOT NULL REFERENCES user_profiles(id),
    recorded_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    UNIQUE(class_id, date)
);

-- Attendance Records
CREATE TABLE attendance_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    session_id UUID REFERENCES attendance_sessions(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    status VARCHAR(20) NOT NULL, -- present, absent, late, excused
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ASSESSMENTS & GRADES
-- ============================================================

-- Assessments
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    teacher_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    term_id UUID REFERENCES terms(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- test, exam, assignment, project
    total_marks DECIMAL(10,2) NOT NULL,
    pass_mark DECIMAL(10,2),
    weighting DECIMAL(5,2),
    date_assigned DATE,
    due_date DATE,
    status VARCHAR(50) DEFAULT 'draft', -- draft, published, closed
    locked BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Assessment Scores
CREATE TABLE assessment_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    score DECIMAL(10,2),
    percentage DECIMAL(5,2),
    submitted_at TIMESTAMP,
    marked_by UUID REFERENCES user_profiles(id),
    marked_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(assessment_id, student_id)
);

-- ============================================================
-- FEES & FINANCE
-- ============================================================

-- Fee Structures
CREATE TABLE fee_structures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    grade_id UUID REFERENCES grades(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    frequency VARCHAR(50) DEFAULT 'term', -- term, annual, monthly
    is_mandatory BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Invoices
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    amount_paid DECIMAL(10,2) DEFAULT 0,
    due_date DATE NOT NULL,
    term_id UUID REFERENCES terms(id),
    status VARCHAR(50) DEFAULT 'pending', -- pending, partial, paid, overdue, cancelled
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Payments
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    receipt_number VARCHAR(50) UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_date DATE DEFAULT CURRENT_DATE,
    reference_number VARCHAR(100),
    notes TEXT,
    recorded_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Payment Plans
CREATE TABLE payment_plans (
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

-- Invoice Adjustments
CREATE TABLE invoice_adjustments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    adjustment_type VARCHAR(50) NOT NULL, -- writeoff, discount, waiver
    amount DECIMAL(10,2) NOT NULL,
    reason TEXT NOT NULL,
    notes TEXT,
    approved_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- DOCUMENTS & COMPLIANCE
-- ============================================================

-- Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL,
    file_url TEXT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER,
    status VARCHAR(50) DEFAULT 'pending', -- pending, verified, rejected, expired
    expiry_date DATE,
    uploaded_by UUID REFERENCES user_profiles(id),
    verified_by UUID REFERENCES user_profiles(id),
    verified_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Document Requirements
CREATE TABLE document_requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL,
    is_mandatory BOOLEAN DEFAULT true,
    applies_to VARCHAR(50) DEFAULT 'all', -- all, new_admissions, specific_grade
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- RISK MANAGEMENT & INTERVENTIONS
-- ============================================================

-- Risk Cases
CREATE TABLE risk_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    risk_type VARCHAR(50) NOT NULL, -- attendance, academic, financial, behavioral
    severity VARCHAR(20) NOT NULL, -- low, medium, high, critical
    status VARCHAR(50) DEFAULT 'open', -- open, in_progress, resolved, closed
    opened_by UUID NOT NULL REFERENCES user_profiles(id),
    opened_at TIMESTAMP DEFAULT NOW(),
    closed_by UUID REFERENCES user_profiles(id),
    closed_at TIMESTAMP,
    notes TEXT
);

-- Interventions
CREATE TABLE interventions (
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

-- ============================================================
-- APPROVALS & GOVERNANCE
-- ============================================================

-- Approval Requests
CREATE TABLE approval_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- admission, transfer, writeoff, payment_plan, staff_role
    entity_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_name VARCHAR(255),
    description TEXT,
    requested_by UUID NOT NULL REFERENCES user_profiles(id),
    submitted_at TIMESTAMP DEFAULT NOW(),
    priority VARCHAR(20) DEFAULT 'medium', -- low, medium, high
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, rejected, more_info
    decision VARCHAR(20),
    decided_by UUID REFERENCES user_profiles(id),
    decided_at TIMESTAMP,
    notes TEXT
);

-- ============================================================
-- TEACHER PLANNING
-- ============================================================

-- Lesson Plans
CREATE TABLE lesson_plans (
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
    status VARCHAR(50) DEFAULT 'planned', -- planned, delivered, missed
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Resources
CREATE TABLE resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    uploaded_by UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- file, link
    url TEXT NOT NULL,
    tags TEXT[],
    visibility VARCHAR(50) DEFAULT 'private', -- private, shared
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- COMMUNICATION
-- ============================================================

-- Messages
CREATE TABLE messages (
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

-- Notifications Log
CREATE TABLE notifications_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    recipient_type VARCHAR(50) NOT NULL,
    delivery_method VARCHAR(50) NOT NULL, -- email, sms, push, in_app
    message_type VARCHAR(50) NOT NULL,
    subject VARCHAR(255),
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    sent_by UUID REFERENCES user_profiles(id),
    sent_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- SETTINGS & CONFIGURATION
-- ============================================================

-- School Settings
CREATE TABLE school_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50) DEFAULT 'string',
    updated_by UUID REFERENCES user_profiles(id),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(school_id, setting_key)
);

-- ============================================================
-- AUDIT & LOGGING
-- ============================================================

-- Audit Logs
CREATE TABLE audit_logs (
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

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================

-- User Profiles
CREATE INDEX idx_user_profiles_school ON user_profiles(school_id);
CREATE INDEX idx_user_profiles_role ON user_profiles(role);
CREATE INDEX idx_user_profiles_email ON user_profiles(email);

-- Students
CREATE INDEX idx_students_school ON students(school_id);
CREATE INDEX idx_students_grade ON students(grade_id);
CREATE INDEX idx_students_class ON students(class_id);
CREATE INDEX idx_students_status ON students(status);
CREATE INDEX idx_students_admission ON students(admission_number);

-- Attendance
CREATE INDEX idx_attendance_records_student ON attendance_records(student_id);
CREATE INDEX idx_attendance_records_date ON attendance_records(date);
CREATE INDEX idx_attendance_records_school ON attendance_records(school_id);

-- Assessments
CREATE INDEX idx_assessments_school ON assessments(school_id);
CREATE INDEX idx_assessments_teacher ON assessments(teacher_id);
CREATE INDEX idx_assessments_class ON assessments(class_id);
CREATE INDEX idx_assessment_scores_student ON assessment_scores(student_id);
CREATE INDEX idx_assessment_scores_assessment ON assessment_scores(assessment_id);

-- Finance
CREATE INDEX idx_invoices_school ON invoices(school_id);
CREATE INDEX idx_invoices_student ON invoices(student_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_due_date ON invoices(due_date);
CREATE INDEX idx_payments_invoice ON payments(invoice_id);

-- Risk Cases
CREATE INDEX idx_risk_cases_school ON risk_cases(school_id);
CREATE INDEX idx_risk_cases_student ON risk_cases(student_id);
CREATE INDEX idx_risk_cases_status ON risk_cases(status);

-- Approvals
CREATE INDEX idx_approval_requests_school ON approval_requests(school_id);
CREATE INDEX idx_approval_requests_status ON approval_requests(status);
CREATE INDEX idx_approval_requests_priority ON approval_requests(priority);

-- Audit Logs
CREATE INDEX idx_audit_logs_school ON audit_logs(school_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);

-- ============================================================
-- TRIGGERS
-- ============================================================

-- Update timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_schools_updated_at BEFORE UPDATE ON schools FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Auto-update invoice status
CREATE OR REPLACE FUNCTION update_invoice_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.amount_paid >= NEW.amount THEN
        NEW.status = 'paid';
    ELSIF NEW.amount_paid > 0 THEN
        NEW.status = 'partial';
    ELSIF NEW.due_date < CURRENT_DATE THEN
        NEW.status = 'overdue';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_invoice_status_trigger BEFORE UPDATE ON invoices FOR EACH ROW EXECUTE FUNCTION update_invoice_status();

-- ============================================================
-- SCHEMA COMPLETE
-- ============================================================
