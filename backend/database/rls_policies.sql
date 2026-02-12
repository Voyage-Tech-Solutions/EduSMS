-- ============================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Multi-tenant data isolation and role-based access control
-- ============================================================

-- Enable RLS on all tables
ALTER TABLE schools ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE academic_years ENABLE ROW LEVEL SECURITY;
ALTER TABLE terms ENABLE ROW LEVEL SECURITY;
ALTER TABLE grades ENABLE ROW LEVEL SECURITY;
ALTER TABLE classes ENABLE ROW LEVEL SECURITY;
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE teacher_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE guardians ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_guardians ENABLE ROW LEVEL SECURITY;
ALTER TABLE admissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE fee_structures ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_adjustments ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE interventions ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE resources ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- HELPER FUNCTIONS
-- ============================================================

-- Get current user's school_id
CREATE OR REPLACE FUNCTION get_user_school_id()
RETURNS UUID AS $$
    SELECT school_id FROM user_profiles WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER;

-- Get current user's role
CREATE OR REPLACE FUNCTION get_user_role()
RETURNS VARCHAR AS $$
    SELECT role FROM user_profiles WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER;

-- Check if user is system admin
CREATE OR REPLACE FUNCTION is_system_admin()
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM user_profiles 
        WHERE id = auth.uid() AND role = 'system_admin'
    );
$$ LANGUAGE sql SECURITY DEFINER;

-- Check if user is principal
CREATE OR REPLACE FUNCTION is_principal()
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM user_profiles 
        WHERE id = auth.uid() AND role = 'principal'
    );
$$ LANGUAGE sql SECURITY DEFINER;

-- ============================================================
-- SCHOOLS POLICIES
-- ============================================================

-- System admins can see all schools
CREATE POLICY schools_system_admin_all ON schools
    FOR ALL USING (is_system_admin());

-- Users can see their own school
CREATE POLICY schools_users_own ON schools
    FOR SELECT USING (id = get_user_school_id());

-- ============================================================
-- USER PROFILES POLICIES
-- ============================================================

-- Users can see their own profile
CREATE POLICY user_profiles_own ON user_profiles
    FOR SELECT USING (id = auth.uid());

-- Users can see profiles in their school
CREATE POLICY user_profiles_same_school ON user_profiles
    FOR SELECT USING (school_id = get_user_school_id());

-- System admins can manage all profiles
CREATE POLICY user_profiles_system_admin ON user_profiles
    FOR ALL USING (is_system_admin());

-- Principals can manage profiles in their school
CREATE POLICY user_profiles_principal_manage ON user_profiles
    FOR ALL USING (
        is_principal() AND school_id = get_user_school_id()
    );

-- ============================================================
-- STUDENTS POLICIES
-- ============================================================

-- Users can see students in their school
CREATE POLICY students_same_school ON students
    FOR SELECT USING (school_id = get_user_school_id());

-- Office admin and principal can manage students
CREATE POLICY students_admin_manage ON students
    FOR ALL USING (
        school_id = get_user_school_id() AND
        get_user_role() IN ('office_admin', 'principal', 'system_admin')
    );

-- Teachers can see students in their classes
CREATE POLICY students_teacher_view ON students
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM teacher_assignments ta
            WHERE ta.teacher_id = auth.uid()
            AND ta.class_id = students.class_id
        )
    );

-- Parents can see their own children
CREATE POLICY students_parent_view ON students
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM student_guardians sg
            JOIN guardians g ON g.id = sg.guardian_id
            WHERE sg.student_id = students.id
            AND g.user_id = auth.uid()
        )
    );

-- ============================================================
-- ATTENDANCE POLICIES
-- ============================================================

-- Users can see attendance in their school
CREATE POLICY attendance_records_same_school ON attendance_records
    FOR SELECT USING (school_id = get_user_school_id());

-- Teachers can record attendance for their classes
CREATE POLICY attendance_records_teacher_manage ON attendance_records
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM attendance_sessions ats
            JOIN classes c ON c.id = ats.class_id
            WHERE ats.id = attendance_records.session_id
            AND c.teacher_id = auth.uid()
        )
    );

-- Office admin and principal can manage all attendance
CREATE POLICY attendance_records_admin_manage ON attendance_records
    FOR ALL USING (
        school_id = get_user_school_id() AND
        get_user_role() IN ('office_admin', 'principal', 'system_admin')
    );

-- Parents can see their children's attendance
CREATE POLICY attendance_records_parent_view ON attendance_records
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM student_guardians sg
            JOIN guardians g ON g.id = sg.guardian_id
            WHERE sg.student_id = attendance_records.student_id
            AND g.user_id = auth.uid()
        )
    );

-- ============================================================
-- ASSESSMENTS POLICIES
-- ============================================================

-- Teachers can manage their own assessments
CREATE POLICY assessments_teacher_manage ON assessments
    FOR ALL USING (teacher_id = auth.uid());

-- Users can see assessments in their school
CREATE POLICY assessments_same_school ON assessments
    FOR SELECT USING (school_id = get_user_school_id());

-- Assessment scores - teachers can manage
CREATE POLICY assessment_scores_teacher_manage ON assessment_scores
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM assessments a
            WHERE a.id = assessment_scores.assessment_id
            AND a.teacher_id = auth.uid()
        )
    );

-- Students can see their own scores
CREATE POLICY assessment_scores_student_view ON assessment_scores
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM students s
            WHERE s.id = assessment_scores.student_id
            AND s.user_id = auth.uid()
        )
    );

-- Parents can see their children's scores
CREATE POLICY assessment_scores_parent_view ON assessment_scores
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM student_guardians sg
            JOIN guardians g ON g.id = sg.guardian_id
            WHERE sg.student_id = assessment_scores.student_id
            AND g.user_id = auth.uid()
        )
    );

-- ============================================================
-- FINANCE POLICIES
-- ============================================================

-- Finance officers can manage invoices and payments
CREATE POLICY invoices_finance_manage ON invoices
    FOR ALL USING (
        school_id = get_user_school_id() AND
        get_user_role() IN ('finance_officer', 'office_admin', 'principal', 'system_admin')
    );

-- Parents can see their children's invoices
CREATE POLICY invoices_parent_view ON invoices
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM student_guardians sg
            JOIN guardians g ON g.id = sg.guardian_id
            WHERE sg.student_id = invoices.student_id
            AND g.user_id = auth.uid()
        )
    );

-- Payments policies (same as invoices)
CREATE POLICY payments_finance_manage ON payments
    FOR ALL USING (
        school_id = get_user_school_id() AND
        get_user_role() IN ('finance_officer', 'office_admin', 'principal', 'system_admin')
    );

CREATE POLICY payments_parent_view ON payments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM invoices i
            JOIN student_guardians sg ON sg.student_id = i.student_id
            JOIN guardians g ON g.id = sg.guardian_id
            WHERE i.id = payments.invoice_id
            AND g.user_id = auth.uid()
        )
    );

-- ============================================================
-- DOCUMENTS POLICIES
-- ============================================================

-- Office admin can manage all documents
CREATE POLICY documents_admin_manage ON documents
    FOR ALL USING (
        school_id = get_user_school_id() AND
        get_user_role() IN ('office_admin', 'principal', 'system_admin')
    );

-- Parents can upload and see their children's documents
CREATE POLICY documents_parent_manage ON documents
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM student_guardians sg
            JOIN guardians g ON g.id = sg.guardian_id
            WHERE sg.student_id = documents.student_id
            AND g.user_id = auth.uid()
        )
    );

-- ============================================================
-- RISK CASES & INTERVENTIONS POLICIES
-- ============================================================

-- Principal and office admin can manage risk cases
CREATE POLICY risk_cases_admin_manage ON risk_cases
    FOR ALL USING (
        school_id = get_user_school_id() AND
        get_user_role() IN ('principal', 'office_admin', 'system_admin')
    );

-- Teachers can view risk cases for their students
CREATE POLICY risk_cases_teacher_view ON risk_cases
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM students s
            JOIN classes c ON c.id = s.class_id
            WHERE s.id = risk_cases.student_id
            AND c.teacher_id = auth.uid()
        )
    );

-- Interventions follow risk cases policies
CREATE POLICY interventions_admin_manage ON interventions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM risk_cases rc
            WHERE rc.id = interventions.risk_case_id
            AND rc.school_id = get_user_school_id()
            AND get_user_role() IN ('principal', 'office_admin', 'system_admin')
        )
    );

-- ============================================================
-- APPROVALS POLICIES
-- ============================================================

-- Principal can manage all approvals
CREATE POLICY approval_requests_principal_manage ON approval_requests
    FOR ALL USING (
        school_id = get_user_school_id() AND
        is_principal()
    );

-- Users can see approvals they requested
CREATE POLICY approval_requests_requester_view ON approval_requests
    FOR SELECT USING (requested_by = auth.uid());

-- ============================================================
-- MESSAGES POLICIES
-- ============================================================

-- Users can see messages they sent or received
CREATE POLICY messages_sender_receiver ON messages
    FOR SELECT USING (
        sender_id = auth.uid() OR recipient_id = auth.uid()
    );

-- Users can send messages within their school
CREATE POLICY messages_send ON messages
    FOR INSERT WITH CHECK (
        sender_id = auth.uid() AND
        school_id = get_user_school_id()
    );

-- ============================================================
-- AUDIT LOGS POLICIES
-- ============================================================

-- System admins can see all audit logs
CREATE POLICY audit_logs_system_admin ON audit_logs
    FOR SELECT USING (is_system_admin());

-- Principals can see audit logs for their school
CREATE POLICY audit_logs_principal ON audit_logs
    FOR SELECT USING (
        school_id = get_user_school_id() AND
        is_principal()
    );

-- ============================================================
-- DEFAULT POLICIES FOR REMAINING TABLES
-- ============================================================

-- Academic structure tables (same school access)
CREATE POLICY academic_years_same_school ON academic_years FOR ALL USING (school_id = get_user_school_id());
CREATE POLICY terms_same_school ON terms FOR ALL USING (school_id = get_user_school_id());
CREATE POLICY grades_same_school ON grades FOR ALL USING (school_id = get_user_school_id());
CREATE POLICY classes_same_school ON classes FOR ALL USING (school_id = get_user_school_id());
CREATE POLICY subjects_same_school ON subjects FOR ALL USING (school_id = get_user_school_id());

-- Teacher planning
CREATE POLICY lesson_plans_teacher_manage ON lesson_plans FOR ALL USING (teacher_id = auth.uid());
CREATE POLICY resources_teacher_manage ON resources FOR ALL USING (uploaded_by = auth.uid());

-- Settings
CREATE POLICY school_settings_same_school ON school_settings FOR ALL USING (school_id = get_user_school_id());

-- Admissions
CREATE POLICY admissions_same_school ON admissions FOR ALL USING (
    school_id = get_user_school_id() AND
    get_user_role() IN ('office_admin', 'principal', 'system_admin')
);

-- ============================================================
-- RLS POLICIES COMPLETE
-- ============================================================
