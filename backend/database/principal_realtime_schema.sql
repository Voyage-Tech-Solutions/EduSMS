-- ============================================
-- PRINCIPAL DASHBOARD REAL-TIME SCHEMA
-- Rule: Every action writes to DB first
-- ============================================

-- ============================================
-- 1. RISK CASES (Student At Risk)
-- ============================================

CREATE TABLE IF NOT EXISTS risk_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    risk_type VARCHAR(50) NOT NULL CHECK (risk_type IN ('attendance', 'academic', 'finance', 'behavior', 'multi')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'moderate', 'high')),
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'monitoring', 'resolved')),
    assigned_to_user_id UUID REFERENCES user_profiles(id),
    notes TEXT,
    created_by UUID NOT NULL REFERENCES user_profiles(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_risk_cases_school ON risk_cases(school_id);
CREATE INDEX idx_risk_cases_student ON risk_cases(student_id, school_id);
CREATE INDEX idx_risk_cases_status ON risk_cases(status, school_id);
CREATE INDEX idx_risk_cases_severity ON risk_cases(severity, school_id);

-- ============================================
-- 2. MARKING REQUESTS (Academic Performance)
-- ============================================

CREATE TABLE IF NOT EXISTS marking_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    requested_by UUID NOT NULL REFERENCES user_profiles(id),
    target_scope VARCHAR(50) NOT NULL CHECK (target_scope IN ('teacher', 'class', 'grade', 'subject')),
    teacher_id UUID REFERENCES user_profiles(id),
    grade_id UUID REFERENCES grades(id),
    class_id UUID REFERENCES classes(id),
    subject_id UUID REFERENCES subjects(id),
    term_id UUID,
    message TEXT NOT NULL,
    due_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'acknowledged', 'completed', 'cancelled')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_marking_requests_school ON marking_requests(school_id);
CREATE INDEX idx_marking_requests_teacher ON marking_requests(teacher_id, school_id);
CREATE INDEX idx_marking_requests_status ON marking_requests(status, school_id);

-- ============================================
-- 3. NOTIFICATIONS (Real-time alerts)
-- ============================================

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT,
    entity_type VARCHAR(50),
    entity_id UUID,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, school_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, school_id) WHERE read_at IS NULL;
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);

-- ============================================
-- 4. KPI TARGETS (Performance targets)
-- ============================================

CREATE TABLE IF NOT EXISTS kpi_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    pass_rate_target NUMERIC(5,2) DEFAULT 75.00,
    assessment_completion_target NUMERIC(5,2) DEFAULT 95.00,
    attendance_target NUMERIC(5,2) DEFAULT 90.00,
    created_by UUID NOT NULL REFERENCES user_profiles(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(school_id, year)
);

CREATE INDEX idx_kpi_targets_school_year ON kpi_targets(school_id, year);

-- ============================================
-- 5. STUDENT SEARCH INDEXES
-- ============================================

-- Full-text search on student names
CREATE INDEX IF NOT EXISTS idx_students_name_search ON students 
USING gin(to_tsvector('simple', first_name || ' ' || last_name));

CREATE INDEX IF NOT EXISTS idx_students_first_name ON students(first_name, school_id);
CREATE INDEX IF NOT EXISTS idx_students_last_name ON students(last_name, school_id);
CREATE INDEX IF NOT EXISTS idx_students_grade ON students(grade_id, school_id);
CREATE INDEX IF NOT EXISTS idx_students_status ON students(status, school_id);

-- ============================================
-- 6. VIEWS: Student Performance
-- ============================================

CREATE OR REPLACE VIEW v_student_performance AS
SELECT 
    s.school_id,
    s.id AS student_id,
    s.first_name,
    s.last_name,
    s.grade_id,
    s.class_id,
    sub.id AS subject_id,
    sub.name AS subject_name,
    COALESCE(AVG(asc.percentage), 0) AS avg_percent,
    COUNT(asc.id) AS assessments_count,
    MAX(asc.created_at) AS last_assessed_at,
    CASE 
        WHEN AVG(asc.percentage) >= 75 THEN 'high'
        WHEN AVG(asc.percentage) >= 50 THEN 'moderate'
        ELSE 'low'
    END AS performance_band
FROM students s
CROSS JOIN subjects sub
LEFT JOIN assessment_scores asc ON asc.student_id = s.id AND asc.subject_id = sub.id
WHERE s.status = 'active' AND sub.school_id = s.school_id
GROUP BY s.school_id, s.id, s.first_name, s.last_name, s.grade_id, s.class_id, sub.id, sub.name;

-- ============================================
-- 7. VIEWS: Performance Bands Summary
-- ============================================

CREATE OR REPLACE VIEW v_performance_bands AS
SELECT 
    school_id,
    grade_id,
    subject_id,
    subject_name,
    COUNT(*) FILTER (WHERE performance_band = 'high') AS high_count,
    COUNT(*) FILTER (WHERE performance_band = 'moderate') AS moderate_count,
    COUNT(*) FILTER (WHERE performance_band = 'low') AS low_count,
    AVG(avg_percent) AS avg_percent
FROM v_student_performance
GROUP BY school_id, grade_id, subject_id, subject_name;

-- ============================================
-- 8. VIEWS: Academic KPIs
-- ============================================

CREATE OR REPLACE VIEW v_kpi_academics AS
SELECT 
    s.school_id,
    COUNT(DISTINCT s.id) AS total_students,
    COUNT(DISTINCT s.id) FILTER (WHERE vsp.avg_percent >= 50) AS students_passing,
    ROUND(
        (COUNT(DISTINCT s.id) FILTER (WHERE vsp.avg_percent >= 50)::NUMERIC / 
        NULLIF(COUNT(DISTINCT s.id), 0) * 100), 2
    ) AS pass_rate_actual,
    COUNT(DISTINCT asc.id) AS total_assessments_taken,
    ROUND(
        (COUNT(DISTINCT asc.id)::NUMERIC / 
        NULLIF(COUNT(DISTINCT s.id) * COUNT(DISTINCT sub.id), 0) * 100), 2
    ) AS assessment_completion_actual
FROM students s
CROSS JOIN subjects sub
LEFT JOIN v_student_performance vsp ON vsp.student_id = s.id AND vsp.subject_id = sub.id
LEFT JOIN assessment_scores asc ON asc.student_id = s.id AND asc.subject_id = sub.id
WHERE s.status = 'active' AND sub.school_id = s.school_id
GROUP BY s.school_id;

-- ============================================
-- 9. VIEWS: Finance KPIs (Principal)
-- ============================================

CREATE OR REPLACE VIEW v_finance_kpis_principal AS
SELECT 
    i.school_id,
    SUM(i.amount) AS total_billed,
    SUM(CASE WHEN i.status = 'paid' THEN i.amount ELSE 0 END) AS total_collected,
    SUM(CASE WHEN i.status != 'paid' THEN i.amount ELSE 0 END) AS outstanding,
    SUM(CASE WHEN i.status != 'paid' AND i.due_date < NOW() - INTERVAL '30 days' THEN i.amount ELSE 0 END) AS overdue_30
FROM invoices i
GROUP BY i.school_id;

-- ============================================
-- 10. VIEWS: Arrears List
-- ============================================

CREATE OR REPLACE VIEW v_arrears_list AS
SELECT 
    i.school_id,
    s.id AS student_id,
    s.first_name,
    s.last_name,
    s.grade_id,
    SUM(i.amount) AS total_owed,
    MIN(i.due_date) AS oldest_due_date,
    EXTRACT(DAY FROM NOW() - MIN(i.due_date)) AS days_overdue
FROM invoices i
JOIN students s ON s.id = i.student_id
WHERE i.status != 'paid'
GROUP BY i.school_id, s.id, s.first_name, s.last_name, s.grade_id
HAVING SUM(i.amount) > 0
ORDER BY days_overdue DESC;

-- ============================================
-- 11. VIEWS: Reports KPIs
-- ============================================

CREATE OR REPLACE VIEW v_reports_kpis_principal AS
SELECT 
    s.school_id,
    COUNT(DISTINCT s.id) FILTER (WHERE s.status = 'active') AS total_enrollment,
    ROUND(AVG(att.attendance_rate), 2) AS avg_attendance,
    fkpi.total_collected AS fee_collection,
    akpi.pass_rate_actual AS academic_avg
FROM students s
LEFT JOIN (
    SELECT student_id, AVG(CASE WHEN status = 'present' THEN 100 ELSE 0 END) AS attendance_rate
    FROM attendance_records
    GROUP BY student_id
) att ON att.student_id = s.id
LEFT JOIN v_finance_kpis_principal fkpi ON fkpi.school_id = s.school_id
LEFT JOIN v_kpi_academics akpi ON akpi.school_id = s.school_id
GROUP BY s.school_id, fkpi.total_collected, akpi.pass_rate_actual;

-- ============================================
-- 12. TRIGGER: Create notifications for marking requests
-- ============================================

CREATE OR REPLACE FUNCTION notify_marking_request()
RETURNS TRIGGER AS $$
DECLARE
    teacher_record RECORD;
BEGIN
    -- Determine target teachers based on scope
    IF NEW.target_scope = 'teacher' AND NEW.teacher_id IS NOT NULL THEN
        -- Single teacher
        INSERT INTO notifications (school_id, user_id, type, title, body, entity_type, entity_id)
        VALUES (
            NEW.school_id,
            NEW.teacher_id,
            'marking_request',
            'Marking Completion Request',
            NEW.message,
            'marking_requests',
            NEW.id
        );
    ELSIF NEW.target_scope = 'class' AND NEW.class_id IS NOT NULL THEN
        -- Teachers assigned to this class
        FOR teacher_record IN 
            SELECT DISTINCT user_id FROM class_teachers WHERE class_id = NEW.class_id
        LOOP
            INSERT INTO notifications (school_id, user_id, type, title, body, entity_type, entity_id)
            VALUES (
                NEW.school_id,
                teacher_record.user_id,
                'marking_request',
                'Marking Completion Request',
                NEW.message,
                'marking_requests',
                NEW.id
            );
        END LOOP;
    ELSIF NEW.target_scope = 'grade' AND NEW.grade_id IS NOT NULL THEN
        -- Teachers with classes in this grade
        FOR teacher_record IN 
            SELECT DISTINCT ct.user_id 
            FROM class_teachers ct
            JOIN classes c ON c.id = ct.class_id
            WHERE c.grade_id = NEW.grade_id
        LOOP
            INSERT INTO notifications (school_id, user_id, type, title, body, entity_type, entity_id)
            VALUES (
                NEW.school_id,
                teacher_record.user_id,
                'marking_request',
                'Marking Completion Request',
                NEW.message,
                'marking_requests',
                NEW.id
            );
        END LOOP;
    ELSIF NEW.target_scope = 'subject' AND NEW.subject_id IS NOT NULL THEN
        -- Teachers teaching this subject
        FOR teacher_record IN 
            SELECT DISTINCT user_id FROM subject_teachers WHERE subject_id = NEW.subject_id
        LOOP
            INSERT INTO notifications (school_id, user_id, type, title, body, entity_type, entity_id)
            VALUES (
                NEW.school_id,
                teacher_record.user_id,
                'marking_request',
                'Marking Completion Request',
                NEW.message,
                'marking_requests',
                NEW.id
            );
        END LOOP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_notify_marking_request ON marking_requests;
CREATE TRIGGER trigger_notify_marking_request
    AFTER INSERT ON marking_requests
    FOR EACH ROW
    EXECUTE FUNCTION notify_marking_request();

-- ============================================
-- 13. RLS POLICIES
-- ============================================

ALTER TABLE risk_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE marking_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE kpi_targets ENABLE ROW LEVEL SECURITY;

-- Risk cases: principal can manage, teachers can view
CREATE POLICY risk_cases_principal ON risk_cases
    FOR ALL USING (
        school_id = (SELECT school_id FROM user_profiles WHERE id = auth.uid())
        AND (SELECT role FROM user_profiles WHERE id = auth.uid()) IN ('principal', 'office_admin')
    );

CREATE POLICY risk_cases_teacher_view ON risk_cases
    FOR SELECT USING (
        school_id = (SELECT school_id FROM user_profiles WHERE id = auth.uid())
        AND (SELECT role FROM user_profiles WHERE id = auth.uid()) = 'teacher'
    );

-- Marking requests: principal creates, teachers view
CREATE POLICY marking_requests_principal ON marking_requests
    FOR ALL USING (
        school_id = (SELECT school_id FROM user_profiles WHERE id = auth.uid())
        AND (SELECT role FROM user_profiles WHERE id = auth.uid()) = 'principal'
    );

CREATE POLICY marking_requests_teacher_view ON marking_requests
    FOR SELECT USING (
        school_id = (SELECT school_id FROM user_profiles WHERE id = auth.uid())
        AND (SELECT role FROM user_profiles WHERE id = auth.uid()) = 'teacher'
    );

-- Notifications: users see their own
CREATE POLICY notifications_own ON notifications
    FOR ALL USING (user_id = auth.uid());

-- KPI targets: principal only
CREATE POLICY kpi_targets_principal ON kpi_targets
    FOR ALL USING (
        school_id = (SELECT school_id FROM user_profiles WHERE id = auth.uid())
        AND (SELECT role FROM user_profiles WHERE id = auth.uid()) = 'principal'
    );

-- ============================================
-- 14. HELPER TABLES (if missing)
-- ============================================

CREATE TABLE IF NOT EXISTS class_teachers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(class_id, user_id)
);

CREATE TABLE IF NOT EXISTS subject_teachers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(subject_id, user_id)
);

CREATE INDEX idx_class_teachers_class ON class_teachers(class_id);
CREATE INDEX idx_class_teachers_user ON class_teachers(user_id);
CREATE INDEX idx_subject_teachers_subject ON subject_teachers(subject_id);
CREATE INDEX idx_subject_teachers_user ON subject_teachers(user_id);
