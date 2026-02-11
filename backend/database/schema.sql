-- ============================================================
-- EduCore SaaS - Database Schema with Supabase Auth Integration
-- Multi-Tenant School Management Platform
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- CORE TABLES
-- ============================================================

-- Schools (Tenants)
CREATE TABLE schools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL, -- Unique school code for registration
    address TEXT,
    phone VARCHAR(50),
    email VARCHAR(255),
    logo_url TEXT,
    is_active BOOLEAN DEFAULT true,
    allow_parent_registration BOOLEAN DEFAULT true,
    allow_student_registration BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User Profiles (linked to Supabase auth.users)
-- This table stores additional user data not in auth.users
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(50),
    role VARCHAR(50) NOT NULL CHECK (role IN ('system_admin', 'principal', 'office_admin', 'teacher', 'parent', 'student')),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    is_approved BOOLEAN DEFAULT false, -- Requires approval for parents/students
    avatar_url TEXT,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX idx_user_profiles_email ON user_profiles(email);
CREATE INDEX idx_user_profiles_school_id ON user_profiles(school_id);
CREATE INDEX idx_user_profiles_role ON user_profiles(role);

-- Invitations table for staff invited by principal
CREATE TABLE invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('office_admin', 'teacher')),
    invited_by UUID REFERENCES user_profiles(id),
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(school_id, email)
);

CREATE INDEX idx_invitations_token ON invitations(token);
CREATE INDEX idx_invitations_email ON invitations(email);

-- ============================================================
-- ACADEMIC STRUCTURE TABLES
-- ============================================================

-- Grades (Class levels: Grade 1, Grade 2, etc.)
CREATE TABLE grades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    "order" INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(school_id, name)
);

-- Classes (Sections: Grade 5A, Grade 5B)
CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    grade_id UUID NOT NULL REFERENCES grades(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    teacher_id UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(grade_id, name)
);

-- Subjects
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(school_id, code)
);

-- ============================================================
-- STUDENT TABLES
-- ============================================================

-- Students
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_profiles(id), -- Optional link to user account
    admission_number VARCHAR(50) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    grade_id UUID REFERENCES grades(id),
    class_id UUID REFERENCES classes(id),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'transferred', 'graduated')),
    admission_date DATE DEFAULT CURRENT_DATE,
    photo_url TEXT,
    medical_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(school_id, admission_number)
);

CREATE INDEX idx_students_school_id ON students(school_id);
CREATE INDEX idx_students_class_id ON students(class_id);

-- Guardians/Parents
CREATE TABLE guardians (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    user_id UUID REFERENCES user_profiles(id), -- Link to user account for portal access
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    relationship VARCHAR(50) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    email VARCHAR(255),
    address TEXT,
    is_primary BOOLEAN DEFAULT false,
    is_emergency_contact BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_guardians_student_id ON guardians(student_id);

-- ============================================================
-- FEE & BILLING TABLES
-- ============================================================

-- Fee Structures
CREATE TABLE fee_structures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    grade_id UUID REFERENCES grades(id), -- NULL means applies to all grades
    term VARCHAR(50),
    year INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Invoices
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    fee_structure_id UUID REFERENCES fee_structures(id),
    invoice_number VARCHAR(50) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    amount_paid DECIMAL(12,2) DEFAULT 0,
    due_date DATE NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'partial', 'overdue')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(school_id, invoice_number)
);

CREATE INDEX idx_invoices_student_id ON invoices(student_id);
CREATE INDEX idx_invoices_status ON invoices(status);

-- Payments
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    receipt_number VARCHAR(50) NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    reference VARCHAR(255),
    recorded_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ATTENDANCE TABLES
-- ============================================================

CREATE TABLE attendance_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('present', 'absent', 'late', 'excused')),
    notes TEXT,
    recorded_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(student_id, date)
);

CREATE INDEX idx_attendance_date ON attendance_records(date);
CREATE INDEX idx_attendance_student ON attendance_records(student_id);

-- ============================================================
-- ACADEMIC GRADES/MARKS TABLES
-- ============================================================

CREATE TABLE grade_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    term VARCHAR(50) NOT NULL,
    year INTEGER NOT NULL,
    assessment_type VARCHAR(50) NOT NULL,
    score DECIMAL(5,2) NOT NULL,
    max_score DECIMAL(5,2) DEFAULT 100,
    weight DECIMAL(3,2) DEFAULT 1.0,
    comments TEXT,
    entered_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_grade_entries_student ON grade_entries(student_id);

-- ============================================================
-- DISCIPLINE TABLES
-- ============================================================

CREATE TABLE discipline_incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    incident_date DATE NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(20) CHECK (severity IN ('minor', 'moderate', 'major')),
    action_taken TEXT,
    reported_by UUID REFERENCES user_profiles(id),
    parent_acknowledged BOOLEAN DEFAULT false,
    parent_acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TIMETABLE TABLES
-- ============================================================

CREATE TABLE timetable_slots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    teacher_id UUID REFERENCES user_profiles(id),
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6), -- 0=Monday
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    room VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(class_id, day_of_week, start_time)
);

CREATE INDEX idx_timetable_class ON timetable_slots(class_id);
CREATE INDEX idx_timetable_teacher ON timetable_slots(teacher_id);

-- ============================================================
-- ASSIGNMENTS TABLE
-- ============================================================

CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    teacher_id UUID REFERENCES user_profiles(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date DATE NOT NULL,
    max_score DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'closed', 'draft')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_assignments_class ON assignments(class_id);
CREATE INDEX idx_assignments_due ON assignments(due_date);

-- Assignment submissions by students
CREATE TABLE assignment_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assignment_id UUID NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    score DECIMAL(5,2),
    graded_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'submitted' CHECK (status IN ('submitted', 'graded', 'late', 'missing')),
    UNIQUE(assignment_id, student_id)
);

CREATE INDEX idx_submissions_student ON assignment_submissions(student_id);

-- ============================================================
-- ANNOUNCEMENTS TABLE
-- ============================================================

CREATE TABLE announcements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    audience VARCHAR(20) NOT NULL DEFAULT 'all' CHECK (audience IN ('all', 'parents', 'students', 'teachers', 'staff')),
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    published_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_announcements_school ON announcements(school_id);
CREATE INDEX idx_announcements_audience ON announcements(audience);

-- ============================================================
-- AUDIT LOG TABLE
-- ============================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID REFERENCES schools(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES user_profiles(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID,
    before_data JSONB,
    after_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_school ON audit_logs(school_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);

-- ============================================================
-- ROW LEVEL SECURITY POLICIES
-- ============================================================

-- Enable RLS on all tables
ALTER TABLE schools ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE grades ENABLE ROW LEVEL SECURITY;
ALTER TABLE classes ENABLE ROW LEVEL SECURITY;
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE guardians ENABLE ROW LEVEL SECURITY;
ALTER TABLE fee_structures ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE grade_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE discipline_incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE timetable_slots ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignment_submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE announcements ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Helper function to get current user's school_id
CREATE OR REPLACE FUNCTION get_user_school_id()
RETURNS UUID AS $$
BEGIN
    RETURN (SELECT school_id FROM user_profiles WHERE id = auth.uid());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Helper function to get current user's role
CREATE OR REPLACE FUNCTION get_user_role()
RETURNS TEXT AS $$
BEGIN
    RETURN (SELECT role FROM user_profiles WHERE id = auth.uid());
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Schools: Allow read for registration, full access for school members
CREATE POLICY schools_select_public ON schools
    FOR SELECT USING (is_active = true);

CREATE POLICY schools_all_members ON schools
    FOR ALL USING (
        get_user_role() = 'system_admin'
        OR id = get_user_school_id()
    );

-- User Profiles: System admins see all, others see users in their school
CREATE POLICY user_profiles_select ON user_profiles
    FOR SELECT USING (
        get_user_role() = 'system_admin'
        OR school_id = get_user_school_id()
        OR id = auth.uid()
    );

CREATE POLICY user_profiles_update_own ON user_profiles
    FOR UPDATE USING (id = auth.uid());

CREATE POLICY user_profiles_insert ON user_profiles
    FOR INSERT WITH CHECK (id = auth.uid());

-- Invitations: Visible to principals and invitees
CREATE POLICY invitations_select ON invitations
    FOR SELECT USING (
        school_id = get_user_school_id()
        AND get_user_role() IN ('principal', 'system_admin')
        OR email = (SELECT email FROM auth.users WHERE id = auth.uid())
    );

CREATE POLICY invitations_insert ON invitations
    FOR INSERT WITH CHECK (
        get_user_role() IN ('principal', 'system_admin')
        AND school_id = get_user_school_id()
    );

-- Generic school-based isolation policies
CREATE POLICY grade_isolation ON grades
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY class_isolation ON classes
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY subject_isolation ON subjects
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY student_isolation ON students
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY guardian_isolation ON guardians
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM students s 
            WHERE s.id = guardians.student_id 
            AND s.school_id = get_user_school_id()
        )
    );

CREATE POLICY fee_structure_isolation ON fee_structures
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY invoice_isolation ON invoices
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY payment_isolation ON payments
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM invoices i 
            WHERE i.id = payments.invoice_id 
            AND i.school_id = get_user_school_id()
        )
    );

CREATE POLICY attendance_isolation ON attendance_records
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY grade_entry_isolation ON grade_entries
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY discipline_isolation ON discipline_incidents
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY timetable_isolation ON timetable_slots
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY assignment_isolation ON assignments
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY submission_isolation ON assignment_submissions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM assignments a
            WHERE a.id = assignment_submissions.assignment_id
            AND a.school_id = get_user_school_id()
        )
    );

CREATE POLICY announcement_isolation ON announcements
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY audit_isolation ON audit_logs
    FOR ALL USING (
        get_user_role() = 'system_admin'
        OR school_id = get_user_school_id()
    );

-- ============================================================
-- TRIGGERS FOR USER PROFILE SYNC
-- ============================================================

-- Function to handle new user registration
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Profile is created from the frontend, not automatically
    -- This just ensures the user can access their own profile
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on Supabase auth.users
CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ============================================================
-- HELPER FUNCTIONS
-- ============================================================

-- Function to get chronic absentees
CREATE OR REPLACE FUNCTION get_chronic_absentees(
    p_school_id UUID,
    p_start_date DATE,
    p_threshold INTEGER
)
RETURNS TABLE (
    student_id UUID,
    student_name TEXT,
    class_name TEXT,
    absences BIGINT,
    attendance_rate NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id as student_id,
        s.first_name || ' ' || s.last_name as student_name,
        COALESCE(c.name, 'Unassigned') as class_name,
        COUNT(*) FILTER (WHERE ar.status = 'absent') as absences,
        ROUND(
            COUNT(*) FILTER (WHERE ar.status IN ('present', 'late'))::NUMERIC / 
            NULLIF(COUNT(*)::NUMERIC, 0) * 100, 
            1
        ) as attendance_rate
    FROM students s
    LEFT JOIN classes c ON s.class_id = c.id
    LEFT JOIN attendance_records ar ON s.id = ar.student_id AND ar.date >= p_start_date
    WHERE s.school_id = p_school_id
    AND s.status = 'active'
    GROUP BY s.id, s.first_name, s.last_name, c.name
    HAVING COUNT(*) FILTER (WHERE ar.status = 'absent') >= p_threshold
    ORDER BY absences DESC;
END;
$$;

-- Updated at trigger function
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all tables
CREATE TRIGGER update_schools_updated_at BEFORE UPDATE ON schools
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_grades_updated_at BEFORE UPDATE ON grades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_classes_updated_at BEFORE UPDATE ON classes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_invoices_updated_at BEFORE UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_attendance_updated_at BEFORE UPDATE ON attendance_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_timetable_updated_at BEFORE UPDATE ON timetable_slots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_assignments_updated_at BEFORE UPDATE ON assignments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_announcements_updated_at BEFORE UPDATE ON announcements
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- SEED DATA FOR DEMO
-- ============================================================

-- Insert a demo school
INSERT INTO schools (id, name, code, email, phone, address) VALUES
    ('11111111-1111-1111-1111-111111111111', 'Demo School', 'DEMO001', 'admin@demoschool.edu', '+1 555-123-4567', '123 Education Lane, Learning City');
