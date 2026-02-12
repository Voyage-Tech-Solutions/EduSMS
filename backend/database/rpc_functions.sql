-- ============================================================
-- RPC FUNCTIONS FOR PRINCIPAL & TEACHER FEATURES
-- ============================================================

-- Get student attendance percentage
CREATE OR REPLACE FUNCTION get_student_attendance_percentage(p_student_id UUID)
RETURNS DECIMAL AS $$
DECLARE
    total_days INTEGER;
    present_days INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_days
    FROM attendance
    WHERE student_id = p_student_id;
    
    IF total_days = 0 THEN
        RETURN 0;
    END IF;
    
    SELECT COUNT(*) INTO present_days
    FROM attendance
    WHERE student_id = p_student_id AND status = 'present';
    
    RETURN ROUND((present_days::DECIMAL / total_days::DECIMAL) * 100, 2);
END;
$$ LANGUAGE plpgsql;

-- Get student academic average
CREATE OR REPLACE FUNCTION get_student_academic_average(p_student_id UUID)
RETURNS DECIMAL AS $$
DECLARE
    avg_score DECIMAL;
BEGIN
    SELECT AVG(percentage) INTO avg_score
    FROM assessment_scores
    WHERE student_id = p_student_id AND score IS NOT NULL;
    
    RETURN COALESCE(ROUND(avg_score, 2), 0);
END;
$$ LANGUAGE plpgsql;

-- Get class attendance average
CREATE OR REPLACE FUNCTION get_class_attendance_average(p_class_id UUID)
RETURNS DECIMAL AS $$
DECLARE
    avg_attendance DECIMAL;
BEGIN
    SELECT AVG(
        (SELECT COUNT(*) FROM attendance a2 
         WHERE a2.student_id = s.id AND a2.status = 'present')::DECIMAL /
        NULLIF((SELECT COUNT(*) FROM attendance a3 
         WHERE a3.student_id = s.id), 0)::DECIMAL * 100
    ) INTO avg_attendance
    FROM students s
    WHERE s.class_id = p_class_id AND s.status = 'active';
    
    RETURN COALESCE(ROUND(avg_attendance, 2), 0);
END;
$$ LANGUAGE plpgsql;

-- Get class academic average
CREATE OR REPLACE FUNCTION get_class_academic_average(p_class_id UUID, p_subject_id UUID)
RETURNS DECIMAL AS $$
DECLARE
    avg_score DECIMAL;
BEGIN
    SELECT AVG(scores.percentage) INTO avg_score
    FROM assessment_scores scores
    JOIN assessments a ON a.id = scores.assessment_id
    WHERE a.class_id = p_class_id 
      AND a.subject_id = p_subject_id
      AND scores.score IS NOT NULL;
    
    RETURN COALESCE(ROUND(avg_score, 2), 0);
END;
$$ LANGUAGE plpgsql;

-- Get student risk level
CREATE OR REPLACE FUNCTION get_student_risk_level(p_student_id UUID)
RETURNS VARCHAR AS $$
DECLARE
    attendance_pct DECIMAL;
    academic_avg DECIMAL;
    outstanding_fees DECIMAL;
BEGIN
    attendance_pct := get_student_attendance_percentage(p_student_id);
    academic_avg := get_student_academic_average(p_student_id);
    
    SELECT COALESCE(SUM(amount - paid_amount), 0) INTO outstanding_fees
    FROM invoices
    WHERE student_id = p_student_id AND status = 'pending';
    
    IF attendance_pct < 75 THEN
        RETURN 'attendance';
    ELSIF academic_avg < 50 THEN
        RETURN 'academic';
    ELSIF outstanding_fees > 0 THEN
        RETURN 'financial';
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Get teacher ungraded count
CREATE OR REPLACE FUNCTION get_teacher_ungraded_count(p_teacher_id UUID)
RETURNS INTEGER AS $$
DECLARE
    ungraded_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO ungraded_count
    FROM assessment_scores scores
    JOIN assessments a ON a.id = scores.assessment_id
    WHERE a.teacher_id = p_teacher_id 
      AND scores.score IS NULL
      AND a.status = 'published';
    
    RETURN ungraded_count;
END;
$$ LANGUAGE plpgsql;

-- Get teacher classes with metrics
CREATE OR REPLACE FUNCTION get_teacher_classes_with_metrics(p_teacher_id UUID)
RETURNS TABLE(
    class_id UUID,
    class_name VARCHAR,
    subject_name VARCHAR,
    student_count BIGINT,
    attendance_avg DECIMAL,
    academic_avg DECIMAL,
    at_risk_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.name,
        s.name,
        COUNT(DISTINCT st.id),
        get_class_attendance_average(c.id),
        get_class_academic_average(c.id, s.id),
        COUNT(DISTINCT CASE WHEN get_student_risk_level(st.id) IS NOT NULL THEN st.id END)
    FROM classes c
    JOIN subjects s ON s.id = c.subject_id
    LEFT JOIN students st ON st.class_id = c.id AND st.status = 'active'
    WHERE c.teacher_id = p_teacher_id
    GROUP BY c.id, c.name, s.name, s.id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- PARENT DASHBOARD RPC FUNCTIONS
-- ============================================================

-- Get parent's children
CREATE OR REPLACE FUNCTION get_parent_children(p_parent_id UUID)
RETURNS TABLE(
    student_id UUID,
    student_name VARCHAR,
    grade_name VARCHAR,
    class_name VARCHAR,
    attendance_pct DECIMAL,
    academic_avg DECIMAL,
    outstanding_fees DECIMAL,
    status VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id,
        CONCAT(s.first_name, ' ', s.last_name),
        g.name,
        c.name,
        get_student_attendance_percentage(s.id),
        get_student_academic_average(s.id),
        COALESCE((SELECT SUM(amount - paid_amount) FROM invoices WHERE student_id = s.id AND status = 'pending'), 0),
        s.status
    FROM students s
    JOIN parent_student_links psl ON psl.student_id = s.id
    JOIN grades g ON g.id = s.grade_id
    LEFT JOIN classes c ON c.id = s.class_id
    WHERE psl.parent_id = p_parent_id;
END;
$$ LANGUAGE plpgsql;

-- Get today's attendance status
CREATE OR REPLACE FUNCTION get_student_today_attendance(p_student_id UUID)
RETURNS VARCHAR AS $$
DECLARE
    today_status VARCHAR;
BEGIN
    SELECT status INTO today_status
    FROM attendance
    WHERE student_id = p_student_id 
      AND date = CURRENT_DATE
    LIMIT 1;
    
    RETURN COALESCE(today_status, 'not_recorded');
END;
$$ LANGUAGE plpgsql;

-- Get missing assignments count
CREATE OR REPLACE FUNCTION get_student_missing_assignments(p_student_id UUID)
RETURNS INTEGER AS $$
DECLARE
    missing_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO missing_count
    FROM assignments a
    JOIN students s ON s.class_id = a.class_id
    LEFT JOIN assignment_submissions sub ON sub.assignment_id = a.id AND sub.student_id = p_student_id
    WHERE s.id = p_student_id
      AND a.status = 'active'
      AND a.due_date >= CURRENT_DATE
      AND (sub.id IS NULL OR sub.status = 'pending');
    
    RETURN missing_count;
END;
$$ LANGUAGE plpgsql;

-- Get unread messages count
CREATE OR REPLACE FUNCTION get_parent_unread_messages(p_parent_id UUID)
RETURNS INTEGER AS $$
DECLARE
    unread_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO unread_count
    FROM messages
    WHERE recipient_id = p_parent_id 
      AND is_read = false;
    
    RETURN unread_count;
END;
$$ LANGUAGE plpgsql;

-- Get active alerts for student
CREATE OR REPLACE FUNCTION get_student_alerts(p_student_id UUID)
RETURNS TABLE(
    alert_type VARCHAR,
    alert_message TEXT,
    severity VARCHAR,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    -- Consecutive absences
    SELECT 
        'attendance'::VARCHAR,
        'Student has 3+ consecutive absences'::TEXT,
        'high'::VARCHAR,
        NOW()::TIMESTAMPTZ
    WHERE (
        SELECT COUNT(*) 
        FROM attendance 
        WHERE student_id = p_student_id 
          AND status = 'absent' 
          AND date >= CURRENT_DATE - INTERVAL '3 days'
    ) >= 3
    
    UNION ALL
    
    -- Low performance
    SELECT 
        'academic'::VARCHAR,
        'Academic average below 50%'::TEXT,
        'high'::VARCHAR,
        NOW()::TIMESTAMPTZ
    WHERE get_student_academic_average(p_student_id) < 50
    
    UNION ALL
    
    -- Overdue fees
    SELECT 
        'financial'::VARCHAR,
        'Payment overdue'::TEXT,
        'medium'::VARCHAR,
        NOW()::TIMESTAMPTZ
    WHERE (
        SELECT COUNT(*) 
        FROM invoices 
        WHERE student_id = p_student_id 
          AND status = 'pending' 
          AND due_date < CURRENT_DATE
    ) > 0
    
    UNION ALL
    
    -- Missing documents
    SELECT 
        'document'::VARCHAR,
        'Required documents missing'::TEXT,
        'medium'::VARCHAR,
        NOW()::TIMESTAMPTZ
    WHERE (
        SELECT COUNT(*) 
        FROM student_documents 
        WHERE student_id = p_student_id 
          AND status = 'missing'
    ) > 0;
END;
$$ LANGUAGE plpgsql;
