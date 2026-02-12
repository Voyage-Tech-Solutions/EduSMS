-- ============================================================
-- RPC FUNCTIONS FOR OFFICE DASHBOARD
-- ============================================================

-- Generate Invoice Number
CREATE OR REPLACE FUNCTION generate_invoice_number(p_school_id UUID)
RETURNS VARCHAR AS $$
DECLARE
    v_prefix VARCHAR;
    v_next_num INT;
    v_invoice_no VARCHAR;
BEGIN
    SELECT invoice_prefix, invoice_next_number 
    INTO v_prefix, v_next_num
    FROM billing_settings 
    WHERE school_id = p_school_id;
    
    v_invoice_no := v_prefix || '-' || LPAD(v_next_num::TEXT, 5, '0');
    
    UPDATE billing_settings 
    SET invoice_next_number = invoice_next_number + 1
    WHERE school_id = p_school_id;
    
    RETURN v_invoice_no;
END;
$$ LANGUAGE plpgsql;

-- Update Invoice Status
CREATE OR REPLACE FUNCTION update_invoice_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.balance = 0 THEN
        NEW.status := 'paid';
    ELSIF NEW.paid_amount > 0 THEN
        NEW.status := 'partial';
    ELSIF NEW.due_date < CURRENT_DATE AND NEW.balance > 0 THEN
        NEW.status := 'overdue';
    ELSE
        NEW.status := 'unpaid';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_invoice_status
BEFORE UPDATE ON invoices
FOR EACH ROW
EXECUTE FUNCTION update_invoice_status();

-- Get Fee Collection Summary
CREATE OR REPLACE FUNCTION get_fee_collection_summary(
    p_school_id UUID,
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
)
RETURNS TABLE(
    total_billed DECIMAL,
    total_collected DECIMAL,
    collection_rate DECIMAL,
    outstanding DECIMAL,
    overdue DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COALESCE(SUM(i.amount), 0) as total_billed,
        COALESCE(SUM(i.paid_amount), 0) as total_collected,
        CASE 
            WHEN SUM(i.amount) > 0 THEN (SUM(i.paid_amount) / SUM(i.amount) * 100)
            ELSE 0
        END as collection_rate,
        COALESCE(SUM(i.balance), 0) as outstanding,
        COALESCE(SUM(CASE WHEN i.due_date < CURRENT_DATE AND i.balance > 0 THEN i.balance ELSE 0 END), 0) as overdue
    FROM invoices i
    WHERE i.school_id = p_school_id
    AND (p_start_date IS NULL OR i.created_at::DATE >= p_start_date)
    AND (p_end_date IS NULL OR i.created_at::DATE <= p_end_date);
END;
$$ LANGUAGE plpgsql;

-- Get Document Compliance Summary
CREATE OR REPLACE FUNCTION get_document_compliance_summary(p_school_id UUID)
RETURNS TABLE(
    total_students BIGINT,
    fully_compliant BIGINT,
    missing_docs BIGINT,
    expired_docs BIGINT,
    pending_verification BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH student_compliance AS (
        SELECT 
            s.id,
            COUNT(dr.id) as required_count,
            COUNT(CASE WHEN d.status = 'verified' AND (d.expiry_date IS NULL OR d.expiry_date >= CURRENT_DATE) THEN 1 END) as verified_count
        FROM students s
        CROSS JOIN document_requirements dr
        LEFT JOIN documents d ON d.entity_id = s.id AND d.document_type = dr.document_type AND d.entity_type = 'student'
        WHERE s.school_id = p_school_id 
        AND dr.school_id = p_school_id
        AND dr.entity_type = 'student'
        AND dr.required = true
        AND dr.active = true
        GROUP BY s.id
    )
    SELECT
        COUNT(DISTINCT s.id)::BIGINT as total_students,
        COUNT(CASE WHEN sc.required_count = sc.verified_count THEN 1 END)::BIGINT as fully_compliant,
        COUNT(CASE WHEN d.status = 'missing' THEN 1 END)::BIGINT as missing_docs,
        COUNT(CASE WHEN d.status = 'expired' THEN 1 END)::BIGINT as expired_docs,
        COUNT(CASE WHEN d.status = 'uploaded' THEN 1 END)::BIGINT as pending_verification
    FROM students s
    LEFT JOIN student_compliance sc ON sc.id = s.id
    LEFT JOIN documents d ON d.entity_id = s.id AND d.entity_type = 'student'
    WHERE s.school_id = p_school_id;
END;
$$ LANGUAGE plpgsql;

-- Get Report Summary
CREATE OR REPLACE FUNCTION get_report_summary(
    p_school_id UUID,
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
)
RETURNS TABLE(
    total_enrollment BIGINT,
    avg_attendance DECIMAL,
    fee_collection DECIMAL,
    collection_rate DECIMAL,
    academic_avg DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM students WHERE school_id = p_school_id AND status = 'active')::BIGINT,
        (SELECT 
            CASE 
                WHEN COUNT(*) > 0 THEN 
                    (COUNT(CASE WHEN status = 'present' THEN 1 END)::DECIMAL / COUNT(*) * 100)
                ELSE 0
            END
         FROM attendance_records ar
         JOIN attendance_sessions ats ON ats.id = ar.session_id
         WHERE ats.school_id = p_school_id
         AND (p_start_date IS NULL OR ats.date >= p_start_date)
         AND (p_end_date IS NULL OR ats.date <= p_end_date)
        ),
        (SELECT COALESCE(SUM(paid_amount), 0) 
         FROM invoices 
         WHERE school_id = p_school_id
         AND (p_start_date IS NULL OR created_at::DATE >= p_start_date)
         AND (p_end_date IS NULL OR created_at::DATE <= p_end_date)
        ),
        (SELECT 
            CASE 
                WHEN SUM(amount) > 0 THEN (SUM(paid_amount) / SUM(amount) * 100)
                ELSE 0
            END
         FROM invoices 
         WHERE school_id = p_school_id
         AND (p_start_date IS NULL OR created_at::DATE >= p_start_date)
         AND (p_end_date IS NULL OR created_at::DATE <= p_end_date)
        ),
        0::DECIMAL; -- Academic average placeholder
END;
$$ LANGUAGE plpgsql;

-- Auto-generate Invoices for Grade
CREATE OR REPLACE FUNCTION auto_generate_invoices(
    p_school_id UUID,
    p_grade_id UUID,
    p_term_id UUID,
    p_fee_structure_id UUID,
    p_created_by UUID
)
RETURNS INT AS $$
DECLARE
    v_count INT := 0;
    v_student RECORD;
    v_fee_structure RECORD;
    v_invoice_no VARCHAR;
BEGIN
    SELECT * INTO v_fee_structure FROM fee_structures WHERE id = p_fee_structure_id;
    
    FOR v_student IN 
        SELECT id FROM students 
        WHERE school_id = p_school_id 
        AND grade_id = p_grade_id 
        AND status = 'active'
    LOOP
        -- Check if invoice already exists
        IF NOT EXISTS (
            SELECT 1 FROM invoices 
            WHERE student_id = v_student.id 
            AND term_id = p_term_id 
            AND description = v_fee_structure.name
        ) THEN
            v_invoice_no := generate_invoice_number(p_school_id);
            
            INSERT INTO invoices (
                school_id, invoice_no, student_id, description, 
                amount, balance, due_date, term_id, created_by
            ) VALUES (
                p_school_id, v_invoice_no, v_student.id, v_fee_structure.name,
                v_fee_structure.amount, v_fee_structure.amount,
                CURRENT_DATE + v_fee_structure.due_days_after_issue,
                p_term_id, p_created_by
            );
            
            v_count := v_count + 1;
        END IF;
    END LOOP;
    
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;
