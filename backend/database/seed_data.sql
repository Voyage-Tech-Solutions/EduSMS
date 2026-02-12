-- ============================================================
-- SAMPLE SEED DATA
-- Test data for development and demonstration
-- ============================================================

-- ============================================================
-- 1. SCHOOLS
-- ============================================================

INSERT INTO schools (id, name, code, address, phone, email, subscription_tier, max_students) VALUES
('11111111-1111-1111-1111-111111111111', 'Greenwood High School', 'GHS001', '123 Education St, City', '+1234567890', 'admin@greenwood.edu', 'premium', 1000),
('22222222-2222-2222-2222-222222222222', 'Riverside Academy', 'RSA001', '456 Learning Ave, Town', '+0987654321', 'info@riverside.edu', 'basic', 500);

-- ============================================================
-- 2. ACADEMIC STRUCTURE
-- ============================================================

-- Academic Years
INSERT INTO academic_years (id, school_id, name, start_date, end_date, is_current) VALUES
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111', '2024-2025', '2024-09-01', '2025-06-30', true);

-- Terms
INSERT INTO terms (id, school_id, academic_year_id, name, start_date, end_date, is_current) VALUES
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '11111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Term 1', '2024-09-01', '2024-12-15', true),
('cccccccc-cccc-cccc-cccc-cccccccccccc', '11111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Term 2', '2025-01-05', '2025-04-15', false),
('dddddddd-dddd-dddd-dddd-dddddddddddd', '11111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Term 3', '2025-04-20', '2025-06-30', false);

-- Grades
INSERT INTO grades (id, school_id, name, level, capacity) VALUES
('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', '11111111-1111-1111-1111-111111111111', 'Grade 1', 1, 120),
('ffffffff-ffff-ffff-ffff-ffffffffffff', '11111111-1111-1111-1111-111111111111', 'Grade 2', 2, 120),
('10101010-1010-1010-1010-101010101010', '11111111-1111-1111-1111-111111111111', 'Grade 3', 3, 120),
('20202020-2020-2020-2020-202020202020', '11111111-1111-1111-1111-111111111111', 'Grade 4', 4, 120),
('30303030-3030-3030-3030-303030303030', '11111111-1111-1111-1111-111111111111', 'Grade 5', 5, 120);

-- Classes
INSERT INTO classes (id, school_id, grade_id, name, capacity, room_number) VALUES
('40404040-4040-4040-4040-404040404040', '11111111-1111-1111-1111-111111111111', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', '1A', 40, 'R101'),
('50505050-5050-5050-5050-505050505050', '11111111-1111-1111-1111-111111111111', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', '1B', 40, 'R102'),
('60606060-6060-6060-6060-606060606060', '11111111-1111-1111-1111-111111111111', 'ffffffff-ffff-ffff-ffff-ffffffffffff', '2A', 40, 'R201');

-- Subjects
INSERT INTO subjects (id, school_id, name, code, is_core) VALUES
('70707070-7070-7070-7070-707070707070', '11111111-1111-1111-1111-111111111111', 'Mathematics', 'MATH', true),
('80808080-8080-8080-8080-808080808080', '11111111-1111-1111-1111-111111111111', 'English', 'ENG', true),
('90909090-9090-9090-9090-909090909090', '11111111-1111-1111-1111-111111111111', 'Science', 'SCI', true),
('a0a0a0a0-a0a0-a0a0-a0a0-a0a0a0a0a0a0', '11111111-1111-1111-1111-111111111111', 'Social Studies', 'SS', true),
('b0b0b0b0-b0b0-b0b0-b0b0-b0b0b0b0b0b0', '11111111-1111-1111-1111-111111111111', 'Physical Education', 'PE', false);

-- ============================================================
-- 3. SAMPLE STUDENTS
-- ============================================================

INSERT INTO students (id, school_id, admission_number, first_name, last_name, date_of_birth, gender, grade_id, class_id, status) VALUES
('c0c0c0c0-c0c0-c0c0-c0c0-c0c0c0c0c0c0', '11111111-1111-1111-1111-111111111111', 'GHS2024001', 'John', 'Smith', '2017-05-15', 'Male', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', '40404040-4040-4040-4040-404040404040', 'active'),
('d0d0d0d0-d0d0-d0d0-d0d0-d0d0d0d0d0d0', '11111111-1111-1111-1111-111111111111', 'GHS2024002', 'Emma', 'Johnson', '2017-08-22', 'Female', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', '40404040-4040-4040-4040-404040404040', 'active'),
('e0e0e0e0-e0e0-e0e0-e0e0-e0e0e0e0e0e0', '11111111-1111-1111-1111-111111111111', 'GHS2024003', 'Michael', 'Williams', '2017-03-10', 'Male', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', '50505050-5050-5050-5050-505050505050', 'active'),
('f0f0f0f0-f0f0-f0f0-f0f0-f0f0f0f0f0f0', '11111111-1111-1111-1111-111111111111', 'GHS2024004', 'Sophia', 'Brown', '2016-11-30', 'Female', 'ffffffff-ffff-ffff-ffff-ffffffffffff', '60606060-6060-6060-6060-606060606060', 'active'),
('11111111-2222-3333-4444-555555555555', '11111111-1111-1111-1111-111111111111', 'GHS2024005', 'Oliver', 'Davis', '2017-07-18', 'Male', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', '40404040-4040-4040-4040-404040404040', 'active');

-- ============================================================
-- 4. FEE STRUCTURES
-- ============================================================

INSERT INTO fee_structures (id, school_id, name, grade_id, amount, frequency) VALUES
('22222222-3333-4444-5555-666666666666', '11111111-1111-1111-1111-111111111111', 'Tuition Fee - Grade 1', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 1500.00, 'term'),
('33333333-4444-5555-6666-777777777777', '11111111-1111-1111-1111-111111111111', 'Tuition Fee - Grade 2', 'ffffffff-ffff-ffff-ffff-ffffffffffff', 1600.00, 'term'),
('44444444-5555-6666-7777-888888888888', '11111111-1111-1111-1111-111111111111', 'Activity Fee', NULL, 200.00, 'term');

-- ============================================================
-- 5. SAMPLE INVOICES
-- ============================================================

INSERT INTO invoices (id, school_id, student_id, invoice_number, description, amount, amount_paid, due_date, term_id, status) VALUES
('55555555-6666-7777-8888-999999999999', '11111111-1111-1111-1111-111111111111', 'c0c0c0c0-c0c0-c0c0-c0c0-c0c0c0c0c0c0', 'INV-2024-001', 'Term 1 Tuition Fee', 1500.00, 1500.00, '2024-09-30', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'paid'),
('66666666-7777-8888-9999-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111', 'd0d0d0d0-d0d0-d0d0-d0d0-d0d0d0d0d0d0', 'INV-2024-002', 'Term 1 Tuition Fee', 1500.00, 750.00, '2024-09-30', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'partial'),
('77777777-8888-9999-aaaa-bbbbbbbbbbbb', '11111111-1111-1111-1111-111111111111', 'e0e0e0e0-e0e0-e0e0-e0e0-e0e0e0e0e0e0', 'INV-2024-003', 'Term 1 Tuition Fee', 1500.00, 0.00, '2024-09-30', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'overdue');

-- ============================================================
-- 6. SAMPLE ATTENDANCE RECORDS
-- ============================================================

-- Attendance Sessions
INSERT INTO attendance_sessions (id, school_id, class_id, date) VALUES
('88888888-9999-aaaa-bbbb-cccccccccccc', '11111111-1111-1111-1111-111111111111', '40404040-4040-4040-4040-404040404040', CURRENT_DATE),
('99999999-aaaa-bbbb-cccc-dddddddddddd', '11111111-1111-1111-1111-111111111111', '40404040-4040-4040-4040-404040404040', CURRENT_DATE - INTERVAL '1 day');

-- Attendance Records
INSERT INTO attendance_records (school_id, session_id, student_id, date, status) VALUES
('11111111-1111-1111-1111-111111111111', '88888888-9999-aaaa-bbbb-cccccccccccc', 'c0c0c0c0-c0c0-c0c0-c0c0-c0c0c0c0c0c0', CURRENT_DATE, 'present'),
('11111111-1111-1111-1111-111111111111', '88888888-9999-aaaa-bbbb-cccccccccccc', 'd0d0d0d0-d0d0-d0d0-d0d0-d0d0d0d0d0d0', CURRENT_DATE, 'present'),
('11111111-1111-1111-1111-111111111111', '88888888-9999-aaaa-bbbb-cccccccccccc', '11111111-2222-3333-4444-555555555555', CURRENT_DATE, 'absent'),
('11111111-1111-1111-1111-111111111111', '99999999-aaaa-bbbb-cccc-dddddddddddd', 'c0c0c0c0-c0c0-c0c0-c0c0-c0c0c0c0c0c0', CURRENT_DATE - INTERVAL '1 day', 'present'),
('11111111-1111-1111-1111-111111111111', '99999999-aaaa-bbbb-cccc-dddddddddddd', 'd0d0d0d0-d0d0-d0d0-d0d0-d0d0d0d0d0d0', CURRENT_DATE - INTERVAL '1 day', 'late'),
('11111111-1111-1111-1111-111111111111', '99999999-aaaa-bbbb-cccc-dddddddddddd', '11111111-2222-3333-4444-555555555555', CURRENT_DATE - INTERVAL '1 day', 'absent');

-- ============================================================
-- 7. SAMPLE ASSESSMENTS
-- ============================================================

INSERT INTO assessments (id, school_id, class_id, subject_id, term_id, title, type, total_marks, pass_mark, status) VALUES
('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '11111111-1111-1111-1111-111111111111', '40404040-4040-4040-4040-404040404040', '70707070-7070-7070-7070-707070707070', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Math Test 1', 'test', 100, 50, 'published'),
('bbbbbbbb-cccc-dddd-eeee-ffffffffffff', '11111111-1111-1111-1111-111111111111', '40404040-4040-4040-4040-404040404040', '80808080-8080-8080-8080-808080808080', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'English Test 1', 'test', 100, 50, 'published');

-- Assessment Scores
INSERT INTO assessment_scores (assessment_id, student_id, score, percentage) VALUES
('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'c0c0c0c0-c0c0-c0c0-c0c0-c0c0c0c0c0c0', 85, 85.00),
('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'd0d0d0d0-d0d0-d0d0-d0d0-d0d0d0d0d0d0', 92, 92.00),
('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', '11111111-2222-3333-4444-555555555555', 45, 45.00),
('bbbbbbbb-cccc-dddd-eeee-ffffffffffff', 'c0c0c0c0-c0c0-c0c0-c0c0-c0c0c0c0c0c0', 78, 78.00),
('bbbbbbbb-cccc-dddd-eeee-ffffffffffff', 'd0d0d0d0-d0d0-d0d0-d0d0-d0d0d0d0d0d0', 88, 88.00),
('bbbbbbbb-cccc-dddd-eeee-ffffffffffff', '11111111-2222-3333-4444-555555555555', 42, 42.00);

-- ============================================================
-- 8. SAMPLE ADMISSIONS
-- ============================================================

INSERT INTO admissions (id, school_id, application_number, first_name, last_name, date_of_birth, gender, grade_id, guardian_name, guardian_phone, guardian_email, status, priority) VALUES
('cccccccc-dddd-eeee-ffff-000000000000', '11111111-1111-1111-1111-111111111111', 'APP-2024-001', 'James', 'Wilson', '2017-09-12', 'Male', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'Robert Wilson', '+1234567891', 'rwilson@email.com', 'pending', 'high'),
('dddddddd-eeee-ffff-0000-111111111111', '11111111-1111-1111-1111-111111111111', 'APP-2024-002', 'Isabella', 'Martinez', '2017-04-25', 'Female', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'Maria Martinez', '+1234567892', 'mmartinez@email.com', 'pending', 'normal');

-- ============================================================
-- 9. SAMPLE RISK CASES
-- ============================================================

INSERT INTO risk_cases (id, school_id, student_id, risk_type, severity, status, notes) VALUES
('eeeeeeee-ffff-0000-1111-222222222222', '11111111-1111-1111-1111-111111111111', '11111111-2222-3333-4444-555555555555', 'attendance', 'high', 'open', 'Student has been absent 2 consecutive days'),
('ffffffff-0000-1111-2222-333333333333', '11111111-1111-1111-1111-111111111111', '11111111-2222-3333-4444-555555555555', 'academic', 'medium', 'open', 'Failing Math and English tests');

-- ============================================================
-- 10. DOCUMENT REQUIREMENTS
-- ============================================================

INSERT INTO document_requirements (school_id, document_type, is_mandatory, applies_to, description) VALUES
('11111111-1111-1111-1111-111111111111', 'Birth Certificate', true, 'all', 'Official birth certificate required for all students'),
('11111111-1111-1111-1111-111111111111', 'Medical Records', true, 'all', 'Immunization records and medical history'),
('11111111-1111-1111-1111-111111111111', 'Previous School Report', false, 'new_admissions', 'Report card from previous school if applicable'),
('11111111-1111-1111-1111-111111111111', 'Photo ID', true, 'all', 'Recent passport-size photograph');

-- ============================================================
-- SEED DATA COMPLETE
-- ============================================================

-- Summary of seed data:
-- - 2 schools
-- - 1 academic year with 3 terms
-- - 5 grades with 3 classes
-- - 5 subjects
-- - 5 students
-- - 3 fee structures
-- - 3 invoices (paid, partial, overdue)
-- - 2 attendance sessions with 6 records
-- - 2 assessments with 6 scores
-- - 2 pending admissions
-- - 2 risk cases
-- - 4 document requirements
