-- ============================================================
-- RPC FUNCTIONS FOR OFFICE DASHBOARD
-- ============================================================

-- Count unverified payments
CREATE OR REPLACE FUNCTION count_unverified_payments(p_school_id UUID)
RETURNS INTEGER AS $$
DECLARE
    unverified_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO unverified_count
    FROM payments p
    JOIN invoices i ON i.id = p.invoice_id
    WHERE i.school_id = p_school_id
      AND p.reference IS NOT NULL
      AND p.recorded_by IS NULL;
    
    RETURN COALESCE(unverified_count, 0);
END;
$$ LANGUAGE plpgsql;

-- Get students without invoices
CREATE OR REPLACE FUNCTION get_students_without_invoices(p_school_id UUID)
RETURNS TABLE(
    student_id UUID,
    student_name VARCHAR,
    admission_number VARCHAR,
    grade_name VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id,
        CONCAT(s.first_name, ' ', s.last_name)::VARCHAR,
        s.admission_number,
        g.name
    FROM students s
    JOIN grades g ON g.id = s.grade_id
    LEFT JOIN invoices i ON i.student_id = s.id
    WHERE s.school_id = p_school_id
      AND s.status = 'active'
      AND i.id IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Get compliance summary
CREATE OR REPLACE FUNCTION get_compliance_summary(p_school_id UUID)
RETURNS TABLE(
    total_students INTEGER,
    compliant_students INTEGER,
    compliance_rate DECIMAL
) AS $$
DECLARE
    total INTEGER;
    compliant INTEGER;
BEGIN
    SELECT COUNT(*) INTO total
    FROM students
    WHERE school_id = p_school_id AND status = 'active';
    
    SELECT COUNT(DISTINCT student_id) INTO compliant
    FROM student_documents
    WHERE student_id IN (
        SELECT id FROM students WHERE school_id = p_school_id AND status = 'active'
    )
    GROUP BY student_id
    HAVING COUNT(*) FILTER (WHERE uploaded = true) = 3;
    
    RETURN QUERY SELECT 
        total,
        COALESCE(compliant, 0),
        CASE WHEN total > 0 THEN ROUND((COALESCE(compliant, 0)::DECIMAL / total::DECIMAL) * 100, 2) ELSE 0 END;
END;
$$ LANGUAGE plpgsql;

-- Get fee collection trends
CREATE OR REPLACE FUNCTION get_fee_collection_trends(p_school_id UUID, p_months INTEGER DEFAULT 6)
RETURNS TABLE(
    month_year VARCHAR,
    collected DECIMAL,
    outstanding DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    WITH months AS (
        SELECT generate_series(
            date_trunc('month', CURRENT_DATE - (p_months || ' months')::INTERVAL),
            date_trunc('month', CURRENT_DATE),
            '1 month'::INTERVAL
        ) AS month
    )
    SELECT 
        TO_CHAR(m.month, 'Mon YYYY')::VARCHAR,
        COALESCE(SUM(p.amount), 0)::DECIMAL,
        COALESCE(SUM(i.amount - i.amount_paid), 0)::DECIMAL
    FROM months m
    LEFT JOIN payments p ON date_trunc('month', p.created_at) = m.month
    LEFT JOIN invoices i ON i.school_id = p_school_id AND date_trunc('month', i.created_at) = m.month
    GROUP BY m.month
    ORDER BY m.month;
END;
$$ LANGUAGE plpgsql;

-- Get at-risk students (multiple criteria)
CREATE OR REPLACE FUNCTION get_at_risk_students(p_school_id UUID)
RETURNS TABLE(
    student_id UUID,
    student_name VARCHAR,
    risk_factors TEXT[],
    risk_level VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id,
        CONCAT(s.first_name, ' ', s.last_name)::VARCHAR,
        ARRAY_AGG(DISTINCT risk_factor) AS risk_factors,
        CASE 
            WHEN COUNT(DISTINCT risk_factor) >= 3 THEN 'critical'
            WHEN COUNT(DISTINCT risk_factor) = 2 THEN 'high'
            ELSE 'medium'
        END::VARCHAR AS risk_level
    FROM students s
    CROSS JOIN LATERAL (
        SELECT 'Low Attendance' AS risk_factor
        WHERE (
            SELECT COUNT(*) FILTER (WHERE status = 'absent')::DECIMAL / NULLIF(COUNT(*), 0)
            FROM attendance_records
            WHERE student_id = s.id AND date >= CURRENT_DATE - INTERVAL '30 days'
        ) > 0.25
        
        UNION ALL
        
        SELECT 'Overdue Fees'
        WHERE EXISTS (
            SELECT 1 FROM invoices
            WHERE student_id = s.id 
              AND status != 'paid'
              AND due_date < CURRENT_DATE - INTERVAL '30 days'
        )
        
        UNION ALL
        
        SELECT 'Missing Documents'
        WHERE EXISTS (
            SELECT 1 FROM student_documents
            WHERE student_id = s.id AND uploaded = false
        )
        
        UNION ALL
        
        SELECT 'Low Academic Performance'
        WHERE (
            SELECT AVG(percentage)
            FROM assessment_scores acs
            JOIN assessments a ON a.id = acs.assessment_id
            WHERE acs.student_id = s.id
              AND a.created_at >= CURRENT_DATE - INTERVAL '90 days'
        ) < 50
    ) risks
    WHERE s.school_id = p_school_id AND s.status = 'active'
    GROUP BY s.id, s.first_name, s.last_name
    HAVING COUNT(DISTINCT risk_factor) > 0;
END;
$$ LANGUAGE plpgsql;

-- Get payment allocation candidates
CREATE OR REPLACE FUNCTION get_unallocated_payments(p_school_id UUID)
RETURNS TABLE(
    payment_id UUID,
    receipt_number VARCHAR,
    amount DECIMAL,
    payment_method VARCHAR,
    reference VARCHAR,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.receipt_number,
        p.amount,
        p.payment_method,
        p.reference,
        p.created_at
    FROM payments p
    WHERE p.invoice_id IS NULL
      AND EXISTS (
          SELECT 1 FROM invoices i
          WHERE i.school_id = p_school_id
      )
    ORDER BY p.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Auto-generate student admission number
CREATE OR REPLACE FUNCTION generate_admission_number(p_school_id UUID)
RETURNS VARCHAR AS $$
DECLARE
    next_number INTEGER;
    admission_num VARCHAR;
BEGIN
    SELECT COUNT(*) + 1 INTO next_number
    FROM students
    WHERE school_id = p_school_id;
    
    admission_num := 'STU-' || EXTRACT(YEAR FROM CURRENT_DATE) || '-' || LPAD(next_number::TEXT, 5, '0');
    
    RETURN admission_num;
END;
$$ LANGUAGE plpgsql;

-- Auto-generate invoice number
CREATE OR REPLACE FUNCTION generate_invoice_number(p_school_id UUID)
RETURNS VARCHAR AS $$
DECLARE
    next_number INTEGER;
    invoice_num VARCHAR;
BEGIN
    SELECT COUNT(*) + 1 INTO next_number
    FROM invoices
    WHERE school_id = p_school_id;
    
    invoice_num := 'INV-' || EXTRACT(YEAR FROM CURRENT_DATE) || '-' || LPAD(next_number::TEXT, 5, '0');
    
    RETURN invoice_num;
END;
$$ LANGUAGE plpgsql;
