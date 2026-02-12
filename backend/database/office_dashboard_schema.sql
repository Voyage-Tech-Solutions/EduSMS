-- ============================================================
-- OFFICE DASHBOARD ADDITIONAL TABLES
-- Required for PRD compliance
-- ============================================================

-- Student Documents Tracking
CREATE TABLE IF NOT EXISTS student_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN ('birth_certificate', 'parent_id', 'medical_form', 'other')),
    uploaded BOOLEAN DEFAULT false,
    verified BOOLEAN DEFAULT false,
    file_url TEXT,
    status VARCHAR(20) DEFAULT 'missing' CHECK (status IN ('missing', 'uploaded', 'verified', 'rejected')),
    notes TEXT,
    uploaded_at TIMESTAMPTZ,
    verified_at TIMESTAMPTZ,
    verified_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(student_id, document_type)
);

CREATE INDEX idx_student_documents_student ON student_documents(student_id);
CREATE INDEX idx_student_documents_status ON student_documents(status);

-- Payment Plans
CREATE TABLE IF NOT EXISTS payment_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    invoice_id UUID REFERENCES invoices(id) ON DELETE CASCADE,
    total_amount DECIMAL(12,2) NOT NULL,
    installment_amount DECIMAL(12,2) NOT NULL,
    frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('weekly', 'monthly', 'quarterly')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled', 'defaulted')),
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payment_plans_student ON payment_plans(student_id);
CREATE INDEX idx_payment_plans_status ON payment_plans(status);

-- Transfer Requests
CREATE TABLE IF NOT EXISTS transfer_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    transfer_type VARCHAR(20) NOT NULL CHECK (transfer_type IN ('incoming', 'outgoing')),
    destination_school VARCHAR(200),
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'completed')),
    requested_by UUID REFERENCES user_profiles(id),
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    processed_by UUID REFERENCES user_profiles(id),
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transfer_requests_student ON transfer_requests(student_id);
CREATE INDEX idx_transfer_requests_status ON transfer_requests(status);

-- Letter Requests
CREATE TABLE IF NOT EXISTS letter_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    letter_type VARCHAR(50) NOT NULL CHECK (letter_type IN ('recommendation', 'conduct', 'enrollment', 'transfer', 'other')),
    purpose TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'rejected')),
    requested_by UUID REFERENCES user_profiles(id),
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    generated_by UUID REFERENCES user_profiles(id),
    generated_at TIMESTAMPTZ,
    document_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_letter_requests_student ON letter_requests(student_id);
CREATE INDEX idx_letter_requests_status ON letter_requests(status);

-- Notifications Log
CREATE TABLE IF NOT EXISTS notifications_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    recipient_type VARCHAR(20) NOT NULL CHECK (recipient_type IN ('parent', 'student', 'teacher', 'staff')),
    recipient_id UUID REFERENCES user_profiles(id),
    delivery_method VARCHAR(20) NOT NULL CHECK (delivery_method IN ('sms', 'email', 'both')),
    message_type VARCHAR(50) NOT NULL,
    subject VARCHAR(255),
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'delivered')),
    sent_by UUID REFERENCES user_profiles(id),
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_log_recipient ON notifications_log(recipient_id);
CREATE INDEX idx_notifications_log_status ON notifications_log(status);
CREATE INDEX idx_notifications_log_sent_at ON notifications_log(sent_at);

-- Attendance Sessions (for bulk attendance entry)
CREATE TABLE IF NOT EXISTS attendance_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id),
    date DATE NOT NULL,
    teacher_id UUID REFERENCES user_profiles(id),
    notes TEXT,
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(class_id, date, subject_id)
);

CREATE INDEX idx_attendance_sessions_class ON attendance_sessions(class_id);
CREATE INDEX idx_attendance_sessions_date ON attendance_sessions(date);

-- Link attendance records to sessions (check if column exists first)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='attendance_records' AND column_name='session_id') THEN
        ALTER TABLE attendance_records ADD COLUMN session_id UUID REFERENCES attendance_sessions(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Parent-Student Links (for multi-child families)
CREATE TABLE IF NOT EXISTS parent_student_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    relationship VARCHAR(50) NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(parent_id, student_id)
);

CREATE INDEX idx_parent_student_links_parent ON parent_student_links(parent_id);
CREATE INDEX idx_parent_student_links_student ON parent_student_links(student_id);

-- Messages (for parent-teacher communication)
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    recipient_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMPTZ,
    parent_message_id UUID REFERENCES messages(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_recipient ON messages(recipient_id);
CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_is_read ON messages(is_read);

-- Assessments (for teacher gradebook)
CREATE TABLE IF NOT EXISTS assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    teacher_id UUID REFERENCES user_profiles(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    assessment_type VARCHAR(50) NOT NULL CHECK (assessment_type IN ('quiz', 'test', 'exam', 'assignment', 'project')),
    max_score DECIMAL(5,2) NOT NULL,
    weight DECIMAL(3,2) DEFAULT 1.0,
    due_date DATE,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'graded', 'archived')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_assessments_class ON assessments(class_id);
CREATE INDEX idx_assessments_teacher ON assessments(teacher_id);

-- Assessment Scores
CREATE TABLE IF NOT EXISTS assessment_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    score DECIMAL(5,2),
    percentage DECIMAL(5,2),
    feedback TEXT,
    graded_by UUID REFERENCES user_profiles(id),
    graded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(assessment_id, student_id)
);

CREATE INDEX idx_assessment_scores_student ON assessment_scores(student_id);
CREATE INDEX idx_assessment_scores_assessment ON assessment_scores(assessment_id);

-- Enable RLS on new tables
ALTER TABLE student_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE transfer_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE letter_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE parent_student_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_scores ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS student_documents_isolation ON student_documents;
DROP POLICY IF EXISTS payment_plans_isolation ON payment_plans;
DROP POLICY IF EXISTS transfer_requests_isolation ON transfer_requests;
DROP POLICY IF EXISTS letter_requests_isolation ON letter_requests;
DROP POLICY IF EXISTS notifications_log_isolation ON notifications_log;
DROP POLICY IF EXISTS attendance_sessions_isolation ON attendance_sessions;
DROP POLICY IF EXISTS parent_student_links_isolation ON parent_student_links;
DROP POLICY IF EXISTS messages_isolation ON messages;
DROP POLICY IF EXISTS assessments_isolation ON assessments;
DROP POLICY IF EXISTS assessment_scores_isolation ON assessment_scores;

-- RLS Policies
CREATE POLICY student_documents_isolation ON student_documents
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM students s 
            WHERE s.id = student_documents.student_id 
            AND s.school_id = get_user_school_id()
        )
    );

CREATE POLICY payment_plans_isolation ON payment_plans
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY transfer_requests_isolation ON transfer_requests
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY letter_requests_isolation ON letter_requests
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY notifications_log_isolation ON notifications_log
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY attendance_sessions_isolation ON attendance_sessions
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY parent_student_links_isolation ON parent_student_links
    FOR ALL USING (
        parent_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM students s 
            WHERE s.id = parent_student_links.student_id 
            AND s.school_id = get_user_school_id()
        )
    );

CREATE POLICY messages_isolation ON messages
    FOR ALL USING (
        school_id = get_user_school_id() OR
        sender_id = auth.uid() OR
        recipient_id = auth.uid()
    );

CREATE POLICY assessments_isolation ON assessments
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY assessment_scores_isolation ON assessment_scores
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM assessments a 
            WHERE a.id = assessment_scores.assessment_id 
            AND a.school_id = get_user_school_id()
        )
    );

-- Triggers for updated_at
CREATE TRIGGER update_student_documents_updated_at BEFORE UPDATE ON student_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_payment_plans_updated_at BEFORE UPDATE ON payment_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_transfer_requests_updated_at BEFORE UPDATE ON transfer_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_letter_requests_updated_at BEFORE UPDATE ON letter_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_attendance_sessions_updated_at BEFORE UPDATE ON attendance_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_assessments_updated_at BEFORE UPDATE ON assessments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_assessment_scores_updated_at BEFORE UPDATE ON assessment_scores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
