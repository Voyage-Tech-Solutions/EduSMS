-- ============================================================
-- PRINCIPAL DASHBOARD TABLES
-- Risk management, interventions, staff tracking
-- ============================================================

-- Risk Cases
CREATE TABLE IF NOT EXISTS risk_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    risk_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    assigned_to UUID REFERENCES user_profiles(id),
    opened_by UUID REFERENCES user_profiles(id),
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Interventions
CREATE TABLE IF NOT EXISTS interventions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    risk_case_id UUID NOT NULL REFERENCES risk_cases(id) ON DELETE CASCADE,
    intervention_type VARCHAR(50) NOT NULL,
    assigned_to UUID REFERENCES user_profiles(id),
    due_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    notes TEXT,
    attachments JSONB,
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Report Submissions (Teacher Reports)
CREATE TABLE IF NOT EXISTS report_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    teacher_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    term_id UUID REFERENCES terms(id),
    grade_id UUID REFERENCES grades(id),
    report_type VARCHAR(50) NOT NULL,
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'submitted' CHECK (status IN ('pending', 'submitted', 'late', 'approved')),
    file_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Academic Targets
CREATE TABLE IF NOT EXISTS academic_targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    grade_id UUID REFERENCES grades(id),
    subject_id UUID REFERENCES subjects(id),
    target_type VARCHAR(50) NOT NULL,
    target_value DECIMAL(5,2) NOT NULL,
    applies_to VARCHAR(20) DEFAULT 'school' CHECK (applies_to IN ('school', 'grade', 'subject')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Invoice Adjustments (Write-offs)
CREATE TABLE IF NOT EXISTS invoice_adjustments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    adjustment_type VARCHAR(20) NOT NULL CHECK (adjustment_type IN ('writeoff', 'discount', 'correction')),
    amount DECIMAL(12,2) NOT NULL,
    reason TEXT NOT NULL,
    notes TEXT,
    approved_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Payment Plans
CREATE TABLE IF NOT EXISTS payment_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    invoice_id UUID NOT NULL REFERENCES invoices(id),
    total_amount DECIMAL(12,2) NOT NULL,
    installment_count INT NOT NULL,
    installment_amount DECIMAL(12,2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled', 'defaulted')),
    agreement_notes TEXT,
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Staff Assignments
CREATE TABLE IF NOT EXISTS teacher_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id),
    subject_id UUID REFERENCES subjects(id),
    effective_date DATE DEFAULT CURRENT_DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Notification Templates
CREATE TABLE IF NOT EXISTS notification_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    template_type VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    subject VARCHAR(255),
    message TEXT NOT NULL,
    variables JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_risk_cases_student ON risk_cases(student_id);
CREATE INDEX IF NOT EXISTS idx_risk_cases_status ON risk_cases(status);
CREATE INDEX IF NOT EXISTS idx_interventions_case ON interventions(risk_case_id);
CREATE INDEX IF NOT EXISTS idx_interventions_assigned ON interventions(assigned_to);
CREATE INDEX IF NOT EXISTS idx_report_submissions_teacher ON report_submissions(teacher_id);
CREATE INDEX IF NOT EXISTS idx_report_submissions_term ON report_submissions(term_id);
CREATE INDEX IF NOT EXISTS idx_teacher_assignments_teacher ON teacher_assignments(teacher_id);
CREATE INDEX IF NOT EXISTS idx_teacher_assignments_class ON teacher_assignments(class_id);
