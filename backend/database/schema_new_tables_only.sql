-- ============================================================
-- NEW TABLES ONLY - Run this if base tables already exist
-- ============================================================

-- Attendance Sessions
CREATE TABLE IF NOT EXISTS attendance_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    recorded_by UUID REFERENCES user_profiles(id),
    override_mode BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(class_id, date)
);

CREATE INDEX IF NOT EXISTS idx_attendance_sessions_school ON attendance_sessions(school_id);
CREATE INDEX IF NOT EXISTS idx_attendance_sessions_class_date ON attendance_sessions(class_id, date);

DO $$ BEGIN
    ALTER TABLE attendance_sessions ENABLE ROW LEVEL SECURITY;
    CREATE POLICY attendance_sessions_isolation ON attendance_sessions FOR ALL USING (school_id = get_user_school_id());
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Fee Structures
CREATE TABLE IF NOT EXISTS fee_structures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    grade_id UUID REFERENCES grades(id),
    term_id UUID REFERENCES terms(id),
    name VARCHAR(200) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    due_days_after_issue INTEGER DEFAULT 30,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fee_structures_school ON fee_structures(school_id);
CREATE INDEX IF NOT EXISTS idx_fee_structures_grade ON fee_structures(grade_id);

CREATE TABLE IF NOT EXISTS payment_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    total_amount DECIMAL(10,2) NOT NULL,
    installment_count INTEGER NOT NULL,
    installment_amount DECIMAL(10,2) NOT NULL,
    start_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payment_plans_invoice ON payment_plans(invoice_id);

CREATE TABLE IF NOT EXISTS invoice_adjustments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    adjustment_type VARCHAR(50) NOT NULL CHECK (adjustment_type IN ('writeoff', 'discount', 'penalty', 'refund')),
    amount DECIMAL(10,2) NOT NULL,
    reason TEXT NOT NULL,
    approved_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invoice_adjustments_invoice ON invoice_adjustments(invoice_id);

DO $$ BEGIN
    ALTER TABLE fee_structures ENABLE ROW LEVEL SECURITY;
    ALTER TABLE payment_plans ENABLE ROW LEVEL SECURITY;
    ALTER TABLE invoice_adjustments ENABLE ROW LEVEL SECURITY;
    
    CREATE POLICY fee_structures_isolation ON fee_structures FOR ALL USING (school_id = get_user_school_id());
    CREATE POLICY payment_plans_isolation ON payment_plans FOR ALL USING (EXISTS (SELECT 1 FROM invoices i WHERE i.id = payment_plans.invoice_id AND i.school_id = get_user_school_id()));
    CREATE POLICY invoice_adjustments_isolation ON invoice_adjustments FOR ALL USING (EXISTS (SELECT 1 FROM invoices i WHERE i.id = invoice_adjustments.invoice_id AND i.school_id = get_user_school_id()));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Risk Cases
CREATE TABLE IF NOT EXISTS risk_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    risk_type VARCHAR(50) NOT NULL CHECK (risk_type IN ('attendance', 'academic', 'financial', 'behavior', 'manual')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    opened_by UUID REFERENCES user_profiles(id),
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_cases_school ON risk_cases(school_id);
CREATE INDEX IF NOT EXISTS idx_risk_cases_student ON risk_cases(student_id);
CREATE INDEX IF NOT EXISTS idx_risk_cases_status ON risk_cases(status);

CREATE TABLE IF NOT EXISTS interventions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    risk_case_id UUID NOT NULL REFERENCES risk_cases(id) ON DELETE CASCADE,
    intervention_type VARCHAR(100) NOT NULL,
    assigned_to UUID REFERENCES user_profiles(id),
    due_date DATE,
    notes TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_interventions_case ON interventions(risk_case_id);
CREATE INDEX IF NOT EXISTS idx_interventions_assigned ON interventions(assigned_to);

CREATE TABLE IF NOT EXISTS report_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    teacher_id UUID NOT NULL REFERENCES user_profiles(id),
    term_id UUID REFERENCES terms(id),
    report_type VARCHAR(50) NOT NULL,
    submitted_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'submitted', 'late', 'approved')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_report_submissions_school ON report_submissions(school_id);
CREATE INDEX IF NOT EXISTS idx_report_submissions_teacher ON report_submissions(teacher_id);

DO $$ BEGIN
    ALTER TABLE risk_cases ENABLE ROW LEVEL SECURITY;
    ALTER TABLE interventions ENABLE ROW LEVEL SECURITY;
    ALTER TABLE report_submissions ENABLE ROW LEVEL SECURITY;
    
    CREATE POLICY risk_cases_isolation ON risk_cases FOR ALL USING (school_id = get_user_school_id());
    CREATE POLICY interventions_isolation ON interventions FOR ALL USING (EXISTS (SELECT 1 FROM risk_cases rc WHERE rc.id = interventions.risk_case_id AND rc.school_id = get_user_school_id()));
    CREATE POLICY report_submissions_isolation ON report_submissions FOR ALL USING (school_id = get_user_school_id());
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Assessments
CREATE TABLE IF NOT EXISTS assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    term_id UUID REFERENCES terms(id),
    grade_id UUID REFERENCES grades(id),
    class_id UUID REFERENCES classes(id),
    subject_id UUID REFERENCES subjects(id),
    teacher_id UUID REFERENCES user_profiles(id),
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    total_marks DECIMAL(5,2) NOT NULL,
    date_assigned DATE,
    due_date DATE,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'closed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assessments_school ON assessments(school_id);
CREATE INDEX IF NOT EXISTS idx_assessments_class ON assessments(class_id);
CREATE INDEX IF NOT EXISTS idx_assessments_teacher ON assessments(teacher_id);

CREATE TABLE IF NOT EXISTS assessment_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    score DECIMAL(5,2),
    percentage DECIMAL(5,2),
    submitted_at TIMESTAMPTZ,
    marked_by UUID REFERENCES user_profiles(id),
    marked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(assessment_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_assessment_scores_assessment ON assessment_scores(assessment_id);
CREATE INDEX IF NOT EXISTS idx_assessment_scores_student ON assessment_scores(student_id);

CREATE TABLE IF NOT EXISTS grade_targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    grade_id UUID REFERENCES grades(id),
    subject_id UUID REFERENCES subjects(id),
    pass_mark DECIMAL(5,2) DEFAULT 50.00,
    target_pass_rate DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_grade_targets_school ON grade_targets(school_id);

DO $$ BEGIN
    ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;
    ALTER TABLE assessment_scores ENABLE ROW LEVEL SECURITY;
    ALTER TABLE grade_targets ENABLE ROW LEVEL SECURITY;
    
    CREATE POLICY assessments_isolation ON assessments FOR ALL USING (school_id = get_user_school_id());
    CREATE POLICY assessment_scores_isolation ON assessment_scores FOR ALL USING (EXISTS (SELECT 1 FROM assessments a WHERE a.id = assessment_scores.assessment_id AND a.school_id = get_user_school_id()));
    CREATE POLICY grade_targets_isolation ON grade_targets FOR ALL USING (school_id = get_user_school_id());
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
