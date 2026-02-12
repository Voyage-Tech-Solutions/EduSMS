-- ============================================================
-- PARENT DASHBOARD - DATABASE SCHEMA
-- ============================================================

-- Parent-Student Relationships (if not exists)
CREATE TABLE IF NOT EXISTS parent_student_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    relationship VARCHAR(50) NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(parent_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_parent_student_links_parent ON parent_student_links(parent_id);
CREATE INDEX IF NOT EXISTS idx_parent_student_links_student ON parent_student_links(student_id);

-- Absence Reports
CREATE TABLE IF NOT EXISTS absence_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    reported_by UUID NOT NULL REFERENCES user_profiles(id),
    absence_date DATE NOT NULL,
    reason TEXT NOT NULL,
    supporting_document_url TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_absence_reports_school ON absence_reports(school_id);
CREATE INDEX IF NOT EXISTS idx_absence_reports_student ON absence_reports(student_id);
CREATE INDEX IF NOT EXISTS idx_absence_reports_status ON absence_reports(status);

-- Assignments/Homework
CREATE TABLE IF NOT EXISTS assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    teacher_id UUID NOT NULL REFERENCES user_profiles(id),
    class_id UUID NOT NULL REFERENCES classes(id),
    subject_id UUID NOT NULL REFERENCES subjects(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    due_date DATE NOT NULL,
    total_marks DECIMAL(5,2),
    attachment_url TEXT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'closed', 'cancelled')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assignments_school ON assignments(school_id);
CREATE INDEX IF NOT EXISTS idx_assignments_class ON assignments(class_id);
CREATE INDEX IF NOT EXISTS idx_assignments_teacher ON assignments(teacher_id);
CREATE INDEX IF NOT EXISTS idx_assignments_due_date ON assignments(due_date);

-- Assignment Submissions
CREATE TABLE IF NOT EXISTS assignment_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assignment_id UUID NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    submission_url TEXT,
    submitted_at TIMESTAMPTZ,
    score DECIMAL(5,2),
    feedback TEXT,
    graded_by UUID REFERENCES user_profiles(id),
    graded_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'submitted', 'late', 'graded')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(assignment_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_assignment_submissions_assignment ON assignment_submissions(assignment_id);
CREATE INDEX IF NOT EXISTS idx_assignment_submissions_student ON assignment_submissions(student_id);
CREATE INDEX IF NOT EXISTS idx_assignment_submissions_status ON assignment_submissions(status);

-- School Notices
CREATE TABLE IF NOT EXISTS school_notices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    notice_type VARCHAR(50) NOT NULL CHECK (notice_type IN ('event', 'holiday', 'meeting', 'policy', 'general', 'urgent')),
    target_audience VARCHAR(50) DEFAULT 'all' CHECK (target_audience IN ('all', 'parents', 'teachers', 'students', 'grade_specific')),
    grade_id UUID REFERENCES grades(id),
    attachment_url TEXT,
    published_by UUID NOT NULL REFERENCES user_profiles(id),
    published_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_school_notices_school ON school_notices(school_id);
CREATE INDEX IF NOT EXISTS idx_school_notices_type ON school_notices(notice_type);
CREATE INDEX IF NOT EXISTS idx_school_notices_published_at ON school_notices(published_at);

-- Notice Acknowledgments
CREATE TABLE IF NOT EXISTS notice_acknowledgments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    notice_id UUID NOT NULL REFERENCES school_notices(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(id),
    acknowledged_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(notice_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_notice_acknowledgments_notice ON notice_acknowledgments(notice_id);
CREATE INDEX IF NOT EXISTS idx_notice_acknowledgments_user ON notice_acknowledgments(user_id);

-- Messages (Parent-Teacher Communication)
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES user_profiles(id),
    recipient_id UUID NOT NULL REFERENCES user_profiles(id),
    subject VARCHAR(200),
    message TEXT NOT NULL,
    attachment_url TEXT,
    thread_id UUID,
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_school ON messages(school_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_id);
CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(thread_id);

-- Parent Notifications
CREATE TABLE IF NOT EXISTS parent_notification_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    sms_enabled BOOLEAN DEFAULT true,
    email_enabled BOOLEAN DEFAULT true,
    app_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, notification_type)
);

CREATE INDEX IF NOT EXISTS idx_parent_notification_prefs_user ON parent_notification_preferences(user_id);

-- RLS Policies
DO $$ BEGIN
    ALTER TABLE parent_student_links ENABLE ROW LEVEL SECURITY;
    ALTER TABLE absence_reports ENABLE ROW LEVEL SECURITY;
    ALTER TABLE assignments ENABLE ROW LEVEL SECURITY;
    ALTER TABLE assignment_submissions ENABLE ROW LEVEL SECURITY;
    ALTER TABLE school_notices ENABLE ROW LEVEL SECURITY;
    ALTER TABLE notice_acknowledgments ENABLE ROW LEVEL SECURITY;
    ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
    ALTER TABLE parent_notification_preferences ENABLE ROW LEVEL SECURITY;
    
    CREATE POLICY parent_student_links_isolation ON parent_student_links FOR ALL USING (
        EXISTS (SELECT 1 FROM students s WHERE s.id = parent_student_links.student_id AND s.school_id = get_user_school_id())
    );
    
    CREATE POLICY absence_reports_isolation ON absence_reports FOR ALL USING (school_id = get_user_school_id());
    CREATE POLICY assignments_isolation ON assignments FOR ALL USING (school_id = get_user_school_id());
    CREATE POLICY assignment_submissions_isolation ON assignment_submissions FOR ALL USING (
        EXISTS (SELECT 1 FROM assignments a WHERE a.id = assignment_submissions.assignment_id AND a.school_id = get_user_school_id())
    );
    CREATE POLICY school_notices_isolation ON school_notices FOR ALL USING (school_id = get_user_school_id());
    CREATE POLICY notice_acknowledgments_isolation ON notice_acknowledgments FOR ALL USING (
        EXISTS (SELECT 1 FROM school_notices n WHERE n.id = notice_acknowledgments.notice_id AND n.school_id = get_user_school_id())
    );
    CREATE POLICY messages_isolation ON messages FOR ALL USING (school_id = get_user_school_id());
    CREATE POLICY parent_notification_prefs_isolation ON parent_notification_preferences FOR ALL USING (user_id = auth.uid());
    
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$ BEGIN
    CREATE TRIGGER update_assignments_updated_at BEFORE UPDATE ON assignments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    CREATE TRIGGER update_parent_notification_prefs_updated_at BEFORE UPDATE ON parent_notification_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
