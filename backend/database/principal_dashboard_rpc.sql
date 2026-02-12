-- ============================================================
-- PRINCIPAL DASHBOARD RPC FUNCTIONS
-- Auto-detection, calculations, and aggregations
-- ============================================================

-- Auto-detect at-risk students
CREATE OR REPLACE FUNCTION detect_at_risk_students(p_school_id UUID)
RETURNS TABLE(
    student_id UUID,
    risk_type VARCHAR,
    severity VARCHAR,
    reason TEXT
) AS $$
BEGIN
    RETURN QUERY
    -- Attendance risk
    SELECT 
        s.id,
        'attendance'::VARCHAR,
        CASE 
            WHEN COUNT(CASE WHEN ar.status = 'absent' THEN 1 END) >= 5 THEN 'critical'
            WHEN COUNT(CASE WHEN ar.status = 'absent' THEN 1 END) >= 3 THEN 'high'
            ELSE 'medium'
        END::VARCHAR,
        'Attendance rate below 75% or 3+ consecutive absences'::TEXT
    FROM students s
    LEFT JOIN attendance_records ar ON s.id = ar.student_id 
        AND ar.date >= CURRENT_DATE - INTERVAL '30 days'
    WHERE s.school_id = p_school_id 
        AND s.status = 'active'
    GROUP BY s.id
    HAVING 
        (COUNT(CASE WHEN ar.status IN ('present', 'late') THEN 1 END)::DECIMAL / 
         NULLIF(COUNT(ar.id), 0) * 100) < 75
        OR COUNT(CASE WHEN ar.status = 'absent' THEN 1 END) >= 3
    
    UNION ALL
    
    -- Financial risk
    SELECT 
        i.student_id,
        'financial'::VARCHAR,
        CASE 
            WHEN (i.amount - i.amount_paid) > 1000 AND (CURRENT_DATE - i.due_date) > 90 THEN 'critical'
            WHEN (CURRENT_DATE - i.due_date) > 60 THEN 'high'
            WHEN (CURRENT_DATE - i.due_date) > 30 THEN 'medium'
            ELSE 'low'
        END::VARCHAR,
        'Overdue balance: $' || (i.amount - i.amount_paid)::TEXT || ' for ' || 
        (CURRENT_DATE - i.due_date)::TEXT || ' days'::TEXT
    FROM invoices i
    WHERE i.school_id = p_school_id
        AND i.amount_paid < i.amount
        AND i.due_date < CURRENT_DATE
        AND (CURRENT_DATE - i.due_date) >= 30;
END;
$$ LANGUAGE plpgsql;

-- Calculate overdue days for invoices
CREATE OR REPLACE FUNCTION calculate_invoice_risk(
    p_due_date DATE,
    p_balance DECIMAL
)
RETURNS VARCHAR AS $$
DECLARE
    v_days_overdue INT;
BEGIN
    v_days_overdue := CURRENT_DATE - p_due_date;
    
    IF v_days_overdue < 15 THEN
        RETURN 'low';
    ELSIF v_days_overdue < 30 THEN
        RETURN 'medium';
    ELSIF v_days_overdue < 90 THEN
        RETURN 'high';
    ELSE
        RETURN 'critical';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Get staff performance metrics
CREATE OR REPLACE FUNCTION get_staff_performance(
    p_school_id UUID,
    p_teacher_id UUID DEFAULT NULL
)
RETURNS TABLE(
    teacher_id UUID,
    teacher_name TEXT,
    assigned_assessments BIGINT,
    marked_assessments BIGINT,
    marking_completion DECIMAL,
    avg_turnaround_days DECIMAL,
    late_submissions BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        up.id,
        up.first_name || ' ' || up.last_name,
        COUNT(DISTINCT a.id),
        COUNT(DISTINCT CASE WHEN ascore.marked_at IS NOT NULL THEN ascore.assessment_id END),
        CASE 
            WHEN COUNT(DISTINCT a.id) > 0 THEN
                (COUNT(DISTINCT CASE WHEN ascore.marked_at IS NOT NULL THEN ascore.assessment_id END)::DECIMAL / 
                 COUNT(DISTINCT a.id) * 100)
            ELSE 0
        END,
        AVG(EXTRACT(DAY FROM (ascore.marked_at - a.created_at)))::DECIMAL,
        COUNT(CASE WHEN ascore.marked_at > a.created_at + INTERVAL '7 days' THEN 1 END)
    FROM user_profiles up
    LEFT JOIN assessments a ON a.teacher_id = up.id
    LEFT JOIN assessment_scores ascore ON ascore.assessment_id = a.id
    WHERE up.school_id = p_school_id
        AND up.role = 'teacher'
        AND up.is_active = true
        AND (p_teacher_id IS NULL OR up.id = p_teacher_id)
    GROUP BY up.id, up.first_name, up.last_name;
END;
$$ LANGUAGE plpgsql;

-- Get grade performance summary
CREATE OR REPLACE FUNCTION get_grade_performance(
    p_school_id UUID,
    p_term_id UUID DEFAULT NULL
)
RETURNS TABLE(
    grade_id UUID,
    grade_name VARCHAR,
    avg_percentage DECIMAL,
    pass_rate DECIMAL,
    completion_rate DECIMAL,
    top_subject VARCHAR,
    lowest_subject VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    WITH grade_scores AS (
        SELECT 
            s.grade_id,
            g.name as grade_name,
            ascore.percentage,
            CASE WHEN ascore.percentage >= 50 THEN 1 ELSE 0 END as passed,
            sub.name as subject_name,
            AVG(ascore.percentage) OVER (PARTITION BY s.grade_id, a.subject_id) as subject_avg
        FROM students s
        JOIN grades g ON g.id = s.grade_id
        JOIN assessment_scores ascore ON ascore.student_id = s.id
        JOIN assessments a ON a.id = ascore.assessment_id
        JOIN subjects sub ON sub.id = a.subject_id
        WHERE s.school_id = p_school_id
            AND s.status = 'active'
            AND (p_term_id IS NULL OR a.term_id = p_term_id)
    )
    SELECT 
        gs.grade_id,
        gs.grade_name,
        AVG(gs.percentage)::DECIMAL,
        (SUM(gs.passed)::DECIMAL / COUNT(*) * 100)::DECIMAL,
        100::DECIMAL, -- Placeholder for completion
        (SELECT subject_name FROM grade_scores WHERE grade_id = gs.grade_id ORDER BY subject_avg DESC LIMIT 1),
        (SELECT subject_name FROM grade_scores WHERE grade_id = gs.grade_id ORDER BY subject_avg ASC LIMIT 1)
    FROM grade_scores gs
    GROUP BY gs.grade_id, gs.grade_name;
END;
$$ LANGUAGE plpgsql;

-- Get subject performance rankings
CREATE OR REPLACE FUNCTION get_subject_rankings(
    p_school_id UUID,
    p_term_id UUID DEFAULT NULL
)
RETURNS TABLE(
    subject_id UUID,
    subject_name VARCHAR,
    avg_percentage DECIMAL,
    pass_rate DECIMAL,
    completion_rate DECIMAL,
    student_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sub.id,
        sub.name,
        AVG(ascore.percentage)::DECIMAL,
        (COUNT(CASE WHEN ascore.percentage >= 50 THEN 1 END)::DECIMAL / COUNT(*) * 100)::DECIMAL,
        100::DECIMAL, -- Placeholder
        COUNT(DISTINCT ascore.student_id)
    FROM subjects sub
    JOIN assessments a ON a.subject_id = sub.id
    JOIN assessment_scores ascore ON ascore.assessment_id = a.id
    WHERE sub.school_id = p_school_id
        AND (p_term_id IS NULL OR a.term_id = p_term_id)
    GROUP BY sub.id, sub.name
    ORDER BY AVG(ascore.percentage) DESC;
END;
$$ LANGUAGE plpgsql;

-- Get missing attendance submissions
CREATE OR REPLACE FUNCTION get_missing_attendance_submissions(
    p_school_id UUID,
    p_date DATE
)
RETURNS TABLE(
    class_id UUID,
    class_name VARCHAR,
    grade_name VARCHAR,
    teacher_name TEXT,
    expected_students BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.name,
        g.name,
        up.first_name || ' ' || up.last_name,
        COUNT(s.id)
    FROM classes c
    JOIN grades g ON g.id = c.grade_id
    LEFT JOIN user_profiles up ON up.id = c.teacher_id
    LEFT JOIN students s ON s.class_id = c.id AND s.status = 'active'
    WHERE c.school_id = p_school_id
        AND NOT EXISTS (
            SELECT 1 FROM attendance_sessions ats
            WHERE ats.class_id = c.id AND ats.date = p_date
        )
    GROUP BY c.id, c.name, g.name, up.first_name, up.last_name;
END;
$$ LANGUAGE plpgsql;
