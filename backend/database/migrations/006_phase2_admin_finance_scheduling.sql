-- ============================================================
-- EduSMS Phase 2 Migration: Admin, Finance & Scheduling
-- Migration 006 - Fee Management, Scheduling, Admissions, Parent Portal
-- ============================================================

-- ============================================================
-- SCHOLARSHIPS & FINANCIAL AID
-- ============================================================

CREATE TABLE IF NOT EXISTS scholarships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL CHECK (type IN (
        'merit', 'need_based', 'athletic', 'sibling', 'staff',
        'community', 'academic', 'full', 'partial', 'other'
    )),
    -- Discount configuration
    discount_type VARCHAR(20) NOT NULL CHECK (discount_type IN ('percentage', 'fixed')),
    discount_value DECIMAL(10,2) NOT NULL,
    applies_to VARCHAR(50) DEFAULT 'tuition' CHECK (applies_to IN (
        'tuition', 'fees', 'all', 'specific_fees'
    )),
    specific_fee_ids UUID[], -- If applies_to = 'specific_fees'
    -- Eligibility
    criteria JSONB, -- {min_gpa, income_bracket, grade_ids, etc.}
    grade_ids UUID[], -- Applicable grades
    -- Limits
    max_recipients INTEGER,
    current_recipients INTEGER DEFAULT 0,
    budget_amount DECIMAL(12,2),
    used_amount DECIMAL(12,2) DEFAULT 0,
    -- Period
    academic_year_id UUID,
    is_renewable BOOLEAN DEFAULT true,
    renewal_criteria JSONB,
    -- Status
    is_active BOOLEAN DEFAULT true,
    application_required BOOLEAN DEFAULT false,
    application_deadline DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scholarships_school ON scholarships(school_id);
CREATE INDEX IF NOT EXISTS idx_scholarships_type ON scholarships(type);

-- ============================================================
-- STUDENT SCHOLARSHIPS
-- ============================================================

CREATE TABLE IF NOT EXISTS student_scholarships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    scholarship_id UUID NOT NULL REFERENCES scholarships(id) ON DELETE CASCADE,
    academic_year_id UUID,
    -- Award details
    awarded_amount DECIMAL(10,2) NOT NULL,
    award_percentage DECIMAL(5,2),
    -- Status
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN (
        'pending', 'approved', 'active', 'suspended', 'revoked', 'expired'
    )),
    applied_at TIMESTAMPTZ,
    approved_by UUID REFERENCES user_profiles(id),
    approved_at TIMESTAMPTZ,
    -- Reason/Notes
    application_notes TEXT,
    approval_notes TEXT,
    revocation_reason TEXT,
    -- Dates
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(student_id, scholarship_id, academic_year_id)
);

-- Ensure columns exist if table was created by another migration
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'student_scholarships' AND column_name = 'student_id') THEN
        ALTER TABLE student_scholarships ADD COLUMN student_id UUID REFERENCES students(id) ON DELETE CASCADE;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_student_scholarships_student ON student_scholarships(student_id);
CREATE INDEX IF NOT EXISTS idx_student_scholarships_scholarship ON student_scholarships(scholarship_id);
CREATE INDEX IF NOT EXISTS idx_student_scholarships_status ON student_scholarships(status);

-- ============================================================
-- PAYMENT PLANS
-- Enhanced payment plan tracking
-- ============================================================

CREATE TABLE IF NOT EXISTS payment_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    -- Plan details
    name VARCHAR(255) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    down_payment DECIMAL(12,2) DEFAULT 0,
    remaining_amount DECIMAL(12,2) NOT NULL,
    -- Schedule
    frequency VARCHAR(20) NOT NULL CHECK (frequency IN (
        'weekly', 'biweekly', 'monthly', 'quarterly', 'custom'
    )),
    installment_amount DECIMAL(12,2) NOT NULL,
    num_installments INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    next_due_date DATE,
    -- Automatic payments
    auto_charge BOOLEAN DEFAULT false,
    payment_method_id TEXT, -- Stored payment method reference
    -- Status tracking
    installments_paid INTEGER DEFAULT 0,
    amount_paid DECIMAL(12,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN (
        'pending', 'active', 'completed', 'defaulted', 'cancelled'
    )),
    -- Late fees
    late_fee_amount DECIMAL(10,2) DEFAULT 0,
    grace_period_days INTEGER DEFAULT 5,
    total_late_fees DECIMAL(10,2) DEFAULT 0,
    -- Notes
    notes TEXT,
    approved_by UUID REFERENCES user_profiles(id),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure columns exist if table was created by another migration
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'payment_plans' AND column_name = 'student_id') THEN
        ALTER TABLE payment_plans ADD COLUMN student_id UUID REFERENCES students(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'payment_plans' AND column_name = 'next_due_date') THEN
        ALTER TABLE payment_plans ADD COLUMN next_due_date DATE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'payment_plans' AND column_name = 'status') THEN
        ALTER TABLE payment_plans ADD COLUMN status VARCHAR(50) DEFAULT 'active';
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_payment_plans_student ON payment_plans(student_id);
CREATE INDEX IF NOT EXISTS idx_payment_plans_status ON payment_plans(status);
CREATE INDEX IF NOT EXISTS idx_payment_plans_next_due ON payment_plans(next_due_date);

-- ============================================================
-- PAYMENT PLAN INSTALLMENTS
-- ============================================================

CREATE TABLE IF NOT EXISTS payment_plan_installments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payment_plan_id UUID NOT NULL REFERENCES payment_plans(id) ON DELETE CASCADE,
    installment_number INTEGER NOT NULL,
    due_date DATE NOT NULL,
    amount_due DECIMAL(12,2) NOT NULL,
    amount_paid DECIMAL(12,2) DEFAULT 0,
    late_fee DECIMAL(10,2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN (
        'pending', 'paid', 'partial', 'overdue', 'waived'
    )),
    paid_at TIMESTAMPTZ,
    payment_id UUID REFERENCES payments(id),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_installments_plan ON payment_plan_installments(payment_plan_id);
CREATE INDEX IF NOT EXISTS idx_installments_due ON payment_plan_installments(due_date);
CREATE INDEX IF NOT EXISTS idx_installments_status ON payment_plan_installments(status);

-- ============================================================
-- REFUNDS
-- ============================================================

CREATE TABLE IF NOT EXISTS refunds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    refund_number VARCHAR(50) UNIQUE,
    amount DECIMAL(12,2) NOT NULL,
    reason TEXT NOT NULL,
    refund_method VARCHAR(50), -- original_method, check, bank_transfer
    -- Status
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN (
        'pending', 'approved', 'processing', 'completed', 'rejected'
    )),
    -- Approval flow
    requested_by UUID REFERENCES user_profiles(id),
    requested_at TIMESTAMPTZ DEFAULT NOW(),
    approved_by UUID REFERENCES user_profiles(id),
    approved_at TIMESTAMPTZ,
    processed_by UUID REFERENCES user_profiles(id),
    processed_at TIMESTAMPTZ,
    -- Transaction details
    transaction_reference TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_refunds_payment ON refunds(payment_id);
CREATE INDEX IF NOT EXISTS idx_refunds_status ON refunds(status);

-- ============================================================
-- ROOMS
-- Physical space management
-- ============================================================

CREATE TABLE IF NOT EXISTS rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20),
    building VARCHAR(100),
    floor VARCHAR(20),
    capacity INTEGER,
    room_type VARCHAR(50) NOT NULL CHECK (room_type IN (
        'classroom', 'lab', 'computer_lab', 'library', 'gym',
        'auditorium', 'cafeteria', 'office', 'conference', 'other'
    )),
    -- Features
    equipment TEXT[],
    features TEXT[], -- AC, projector, whiteboard, etc.
    -- Scheduling
    is_bookable BOOLEAN DEFAULT true,
    default_class_id UUID REFERENCES classes(id),
    -- Status
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(school_id, code)
);

CREATE INDEX IF NOT EXISTS idx_rooms_school ON rooms(school_id);
CREATE INDEX IF NOT EXISTS idx_rooms_type ON rooms(room_type);

-- ============================================================
-- BELL SCHEDULES
-- Different schedules for different day types
-- ============================================================

CREATE TABLE IF NOT EXISTS bell_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, -- Regular, Early Release, Assembly, Exam
    description TEXT,
    -- Periods configuration
    periods JSONB NOT NULL,
    -- [{number: 1, name: "Period 1", start_time: "08:00", end_time: "08:50", type: "class"},
    --  {number: 0, name: "Homeroom", start_time: "07:45", end_time: "08:00", type: "homeroom"},
    --  {number: null, name: "Lunch", start_time: "12:00", end_time: "12:30", type: "break"}]
    total_periods INTEGER,
    school_start_time TIME,
    school_end_time TIME,
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(school_id, name)
);

CREATE INDEX IF NOT EXISTS idx_bell_schedules_school ON bell_schedules(school_id);

-- ============================================================
-- ENHANCED TIMETABLE
-- ============================================================

-- Create timetable_slots if it doesn't exist
CREATE TABLE IF NOT EXISTS timetable_slots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id),
    subject_id UUID REFERENCES subjects(id),
    teacher_id UUID REFERENCES user_profiles(id),
    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    academic_year_id UUID,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add enhanced columns if table exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'timetable_slots') THEN
        -- Add room_id if not exists
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'timetable_slots' AND column_name = 'room_id') THEN
            ALTER TABLE timetable_slots ADD COLUMN room_id UUID REFERENCES rooms(id);
        END IF;
        -- Add bell_schedule_id if not exists
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'timetable_slots' AND column_name = 'bell_schedule_id') THEN
            ALTER TABLE timetable_slots ADD COLUMN bell_schedule_id UUID REFERENCES bell_schedules(id);
        END IF;
        -- Add period_number if not exists
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'timetable_slots' AND column_name = 'period_number') THEN
            ALTER TABLE timetable_slots ADD COLUMN period_number INTEGER;
        END IF;
        -- Add is_recurring if not exists
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'timetable_slots' AND column_name = 'is_recurring') THEN
            ALTER TABLE timetable_slots ADD COLUMN is_recurring BOOLEAN DEFAULT true;
        END IF;
        -- Add specific_date if not exists
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'timetable_slots' AND column_name = 'specific_date') THEN
            ALTER TABLE timetable_slots ADD COLUMN specific_date DATE;
        END IF;
        -- Add notes if not exists
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'timetable_slots' AND column_name = 'notes') THEN
            ALTER TABLE timetable_slots ADD COLUMN notes TEXT;
        END IF;
    END IF;
END $$;

-- ============================================================
-- SCHEDULING CONSTRAINTS
-- Rules for auto-scheduling
-- ============================================================

CREATE TABLE IF NOT EXISTS scheduling_constraints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    constraint_type VARCHAR(50) NOT NULL CHECK (constraint_type IN (
        'teacher_unavailable', 'room_unavailable', 'subject_preference',
        'max_consecutive', 'min_gap', 'avoid_period', 'must_have_period'
    )),
    -- What this constraint applies to
    entity_type VARCHAR(50) NOT NULL, -- teacher, room, class, subject
    entity_id UUID NOT NULL,
    -- Time constraints
    day_of_week INTEGER, -- 0=Monday, null=all days
    time_slots JSONB, -- [{day: 0, period: 1}, ...]
    -- Parameters
    parameters JSONB, -- Type-specific parameters
    priority INTEGER DEFAULT 5, -- 1=must enforce, 10=nice to have
    is_active BOOLEAN DEFAULT true,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scheduling_constraints_school ON scheduling_constraints(school_id);
CREATE INDEX IF NOT EXISTS idx_scheduling_constraints_entity ON scheduling_constraints(entity_type, entity_id);

-- ============================================================
-- SUBSTITUTIONS
-- Substitute teacher assignments
-- ============================================================

CREATE TABLE IF NOT EXISTS substitutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    -- Original assignment
    original_teacher_id UUID NOT NULL REFERENCES user_profiles(id),
    class_id UUID NOT NULL REFERENCES classes(id),
    subject_id UUID REFERENCES subjects(id),
    -- Substitute
    substitute_teacher_id UUID REFERENCES user_profiles(id),
    substitute_type VARCHAR(50) CHECK (substitute_type IN (
        'internal', 'external', 'split', 'cancelled'
    )),
    -- Schedule
    date DATE NOT NULL,
    periods INTEGER[], -- Which periods
    start_time TIME,
    end_time TIME,
    -- Reason
    absence_reason VARCHAR(100),
    absence_type VARCHAR(50) CHECK (absence_type IN (
        'sick', 'personal', 'professional_development', 'emergency', 'other'
    )),
    -- Status
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN (
        'pending', 'assigned', 'confirmed', 'completed', 'cancelled'
    )),
    -- Notes
    lesson_plan_url TEXT,
    special_instructions TEXT,
    notes TEXT,
    -- Tracking
    created_by UUID REFERENCES user_profiles(id),
    confirmed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_substitutions_date ON substitutions(date);
CREATE INDEX IF NOT EXISTS idx_substitutions_original ON substitutions(original_teacher_id);
CREATE INDEX IF NOT EXISTS idx_substitutions_substitute ON substitutions(substitute_teacher_id);
CREATE INDEX IF NOT EXISTS idx_substitutions_status ON substitutions(status);

-- ============================================================
-- ENHANCED APPLICATION FORMS
-- Dynamic application form configuration
-- ============================================================

CREATE TABLE IF NOT EXISTS application_forms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    -- Grades accepting applications
    grade_ids UUID[],
    -- Form configuration
    form_config JSONB NOT NULL DEFAULT '[]',
    -- [{section: "Student Info", fields: [{name, type, required, options}]}]
    required_documents TEXT[], -- birth_certificate, transcript, photo, etc.
    -- Fees
    application_fee DECIMAL(10,2) DEFAULT 0,
    fee_waiver_available BOOLEAN DEFAULT false,
    -- Dates
    open_date DATE,
    deadline DATE,
    late_deadline DATE,
    late_fee DECIMAL(10,2) DEFAULT 0,
    -- Capacity
    available_spots JSONB, -- {grade_id: spots}
    waitlist_enabled BOOLEAN DEFAULT true,
    lottery_enabled BOOLEAN DEFAULT false,
    lottery_date DATE,
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_published BOOLEAN DEFAULT false,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_application_forms_school ON application_forms(school_id);
CREATE INDEX IF NOT EXISTS idx_application_forms_active ON application_forms(is_active, is_published);

-- ============================================================
-- CONFERENCE SLOTS
-- Parent-teacher conference scheduling
-- ============================================================

CREATE TABLE IF NOT EXISTS conference_slots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    teacher_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    -- Schedule
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_minutes INTEGER DEFAULT 15,
    -- Location
    location VARCHAR(255),
    room_id UUID REFERENCES rooms(id),
    is_virtual BOOLEAN DEFAULT false,
    meeting_link TEXT,
    -- Availability
    is_available BOOLEAN DEFAULT true,
    max_bookings INTEGER DEFAULT 1,
    current_bookings INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conference_slots_teacher ON conference_slots(teacher_id);
CREATE INDEX IF NOT EXISTS idx_conference_slots_date ON conference_slots(date);
CREATE INDEX IF NOT EXISTS idx_conference_slots_available ON conference_slots(is_available);

-- ============================================================
-- CONFERENCE BOOKINGS
-- ============================================================

CREATE TABLE IF NOT EXISTS conference_bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slot_id UUID NOT NULL REFERENCES conference_slots(id) ON DELETE CASCADE,
    parent_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    -- Status
    status VARCHAR(50) DEFAULT 'confirmed' CHECK (status IN (
        'pending', 'confirmed', 'cancelled', 'completed', 'no_show'
    )),
    -- Notes
    parent_notes TEXT, -- What parent wants to discuss
    teacher_notes TEXT, -- Post-conference notes
    -- Cancellation
    cancelled_at TIMESTAMPTZ,
    cancelled_by UUID REFERENCES user_profiles(id),
    cancellation_reason TEXT,
    -- Reminders
    reminder_sent BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure columns exist if table was created by another migration
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'conference_bookings' AND column_name = 'student_id') THEN
        ALTER TABLE conference_bookings ADD COLUMN student_id UUID REFERENCES students(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'conference_bookings' AND column_name = 'parent_id') THEN
        ALTER TABLE conference_bookings ADD COLUMN parent_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_conference_bookings_slot ON conference_bookings(slot_id);
CREATE INDEX IF NOT EXISTS idx_conference_bookings_parent ON conference_bookings(parent_id);
CREATE INDEX IF NOT EXISTS idx_conference_bookings_student ON conference_bookings(student_id);

-- ============================================================
-- PARENT NOTIFICATION PREFERENCES
-- ============================================================

CREATE TABLE IF NOT EXISTS parent_notification_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE UNIQUE,
    -- Channels
    email_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT true,
    push_enabled BOOLEAN DEFAULT true,
    whatsapp_enabled BOOLEAN DEFAULT false,
    -- Notification types
    grade_notifications BOOLEAN DEFAULT true,
    attendance_notifications BOOLEAN DEFAULT true,
    fee_notifications BOOLEAN DEFAULT true,
    announcement_notifications BOOLEAN DEFAULT true,
    assignment_notifications BOOLEAN DEFAULT true,
    behavior_notifications BOOLEAN DEFAULT true,
    event_notifications BOOLEAN DEFAULT true,
    report_notifications BOOLEAN DEFAULT true,
    -- Timing
    digest_frequency VARCHAR(20) DEFAULT 'immediate' CHECK (digest_frequency IN (
        'immediate', 'daily', 'weekly'
    )),
    quiet_hours_enabled BOOLEAN DEFAULT false,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    -- Preferences
    language_preference VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_parent_notifications_parent ON parent_notification_preferences(parent_id);

-- ============================================================
-- STAFF EVALUATIONS
-- Teacher performance evaluation
-- ============================================================

CREATE TABLE IF NOT EXISTS staff_evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    staff_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    evaluator_id UUID NOT NULL REFERENCES user_profiles(id),
    -- Period
    evaluation_period VARCHAR(50) NOT NULL, -- 2024-Q1, 2024-Annual
    evaluation_type VARCHAR(50) DEFAULT 'annual' CHECK (evaluation_type IN (
        'probation', 'annual', 'mid_year', 'observation', 'improvement_plan'
    )),
    -- Scores
    scores JSONB NOT NULL, -- {category: {score, max, weight, comments}}
    overall_rating DECIMAL(3,2),
    rating_scale VARCHAR(50), -- 1-5, 1-4, letter
    -- Narrative
    strengths TEXT[],
    areas_for_improvement TEXT[],
    accomplishments TEXT[],
    goals JSONB, -- [{goal, timeline, measures}]
    professional_development_plan TEXT,
    -- Observation details (if applicable)
    observation_date DATE,
    observation_class_id UUID REFERENCES classes(id),
    observation_notes TEXT,
    -- Status
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN (
        'draft', 'submitted', 'in_review', 'finalized', 'acknowledged'
    )),
    submitted_at TIMESTAMPTZ,
    finalized_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,
    acknowledgement_comments TEXT,
    -- Follow-up
    follow_up_required BOOLEAN DEFAULT false,
    follow_up_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_staff_evaluations_staff ON staff_evaluations(staff_id);
CREATE INDEX IF NOT EXISTS idx_staff_evaluations_evaluator ON staff_evaluations(evaluator_id);
CREATE INDEX IF NOT EXISTS idx_staff_evaluations_period ON staff_evaluations(evaluation_period);
CREATE INDEX IF NOT EXISTS idx_staff_evaluations_status ON staff_evaluations(status);

-- ============================================================
-- PROFESSIONAL DEVELOPMENT
-- ============================================================

CREATE TABLE IF NOT EXISTS professional_development (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    staff_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    -- Activity details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    provider VARCHAR(255),
    activity_type VARCHAR(50) CHECK (activity_type IN (
        'workshop', 'conference', 'course', 'certification', 'webinar',
        'coaching', 'peer_observation', 'self_study', 'other'
    )),
    -- Hours
    hours DECIMAL(5,2),
    credit_hours DECIMAL(5,2),
    -- Dates
    start_date DATE,
    end_date DATE,
    completion_date DATE,
    -- Documentation
    certificate_url TEXT,
    reflection TEXT,
    -- Verification
    verified BOOLEAN DEFAULT false,
    verified_by UUID REFERENCES user_profiles(id),
    -- Categories
    category VARCHAR(100), -- content_area, technology, leadership, etc.
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_professional_development_staff ON professional_development(staff_id);
CREATE INDEX IF NOT EXISTS idx_professional_development_type ON professional_development(activity_type);

-- ============================================================
-- SCHOOL GOALS
-- Strategic goal tracking
-- ============================================================

CREATE TABLE IF NOT EXISTS school_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    academic_year_id UUID,
    -- Goal details
    category VARCHAR(100) NOT NULL, -- academic, attendance, financial, enrollment, etc.
    title VARCHAR(255) NOT NULL,
    description TEXT,
    metric VARCHAR(255) NOT NULL, -- What we're measuring
    -- Values
    baseline_value DECIMAL(10,2),
    target_value DECIMAL(10,2) NOT NULL,
    current_value DECIMAL(10,2),
    unit VARCHAR(50), -- percent, count, currency, etc.
    -- Tracking
    milestones JSONB, -- [{date, target, actual}]
    status VARCHAR(50) DEFAULT 'in_progress' CHECK (status IN (
        'not_started', 'in_progress', 'on_track', 'at_risk', 'achieved', 'not_achieved'
    )),
    -- Ownership
    owner_id UUID REFERENCES user_profiles(id),
    -- Dates
    start_date DATE,
    target_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_school_goals_school ON school_goals(school_id);
CREATE INDEX IF NOT EXISTS idx_school_goals_category ON school_goals(category);
CREATE INDEX IF NOT EXISTS idx_school_goals_status ON school_goals(status);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE scholarships ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_scholarships ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_plan_installments ENABLE ROW LEVEL SECURITY;
ALTER TABLE refunds ENABLE ROW LEVEL SECURITY;
ALTER TABLE rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE bell_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduling_constraints ENABLE ROW LEVEL SECURITY;
ALTER TABLE substitutions ENABLE ROW LEVEL SECURITY;
ALTER TABLE application_forms ENABLE ROW LEVEL SECURITY;
ALTER TABLE conference_slots ENABLE ROW LEVEL SECURITY;
ALTER TABLE conference_bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE parent_notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_evaluations ENABLE ROW LEVEL SECURITY;
ALTER TABLE professional_development ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_goals ENABLE ROW LEVEL SECURITY;

-- Create isolation policies for all tables
-- Create isolation policies for all tables
DROP POLICY IF EXISTS scholarships_isolation ON scholarships;
CREATE POLICY scholarships_isolation ON scholarships FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS student_scholarships_isolation ON student_scholarships;
CREATE POLICY student_scholarships_isolation ON student_scholarships FOR ALL USING (
    EXISTS (SELECT 1 FROM students s WHERE s.id = student_id AND s.school_id = get_user_school_id())
);

DROP POLICY IF EXISTS payment_plans_isolation ON payment_plans;
CREATE POLICY payment_plans_isolation ON payment_plans FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS payment_plan_installments_isolation ON payment_plan_installments;
CREATE POLICY payment_plan_installments_isolation ON payment_plan_installments FOR ALL USING (
    EXISTS (SELECT 1 FROM payment_plans pp WHERE pp.id = payment_plan_id AND pp.school_id = get_user_school_id())
);

DROP POLICY IF EXISTS refunds_isolation ON refunds;
CREATE POLICY refunds_isolation ON refunds FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS rooms_isolation ON rooms;
CREATE POLICY rooms_isolation ON rooms FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS bell_schedules_isolation ON bell_schedules;
CREATE POLICY bell_schedules_isolation ON bell_schedules FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS scheduling_constraints_isolation ON scheduling_constraints;
CREATE POLICY scheduling_constraints_isolation ON scheduling_constraints FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS substitutions_isolation ON substitutions;
CREATE POLICY substitutions_isolation ON substitutions FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS application_forms_isolation ON application_forms;
CREATE POLICY application_forms_isolation ON application_forms FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS conference_slots_isolation ON conference_slots;
CREATE POLICY conference_slots_isolation ON conference_slots FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS conference_bookings_isolation ON conference_bookings;
CREATE POLICY conference_bookings_isolation ON conference_bookings FOR ALL USING (
    EXISTS (SELECT 1 FROM conference_slots cs WHERE cs.id = slot_id AND cs.school_id = get_user_school_id())
);

DROP POLICY IF EXISTS parent_notification_preferences_own ON parent_notification_preferences;
CREATE POLICY parent_notification_preferences_own ON parent_notification_preferences FOR ALL USING (parent_id = auth.uid());

DROP POLICY IF EXISTS staff_evaluations_isolation ON staff_evaluations;
CREATE POLICY staff_evaluations_isolation ON staff_evaluations FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS professional_development_isolation ON professional_development;
CREATE POLICY professional_development_isolation ON professional_development FOR ALL USING (
    school_id IS NULL OR school_id = get_user_school_id()
);

DROP POLICY IF EXISTS school_goals_isolation ON school_goals;
CREATE POLICY school_goals_isolation ON school_goals FOR ALL USING (school_id = get_user_school_id());

-- ============================================================
-- COMMENTS
-- ============================================================

COMMENT ON TABLE scholarships IS 'Scholarship and financial aid programs';
COMMENT ON TABLE student_scholarships IS 'Student scholarship awards and status';
COMMENT ON TABLE payment_plans IS 'Installment payment plans for fees';
COMMENT ON TABLE refunds IS 'Payment refund requests and processing';
COMMENT ON TABLE rooms IS 'Physical rooms and spaces in the school';
COMMENT ON TABLE bell_schedules IS 'Different schedule configurations (regular, early release, etc.)';
COMMENT ON TABLE scheduling_constraints IS 'Rules for automatic schedule generation';
COMMENT ON TABLE substitutions IS 'Substitute teacher assignments';
COMMENT ON TABLE application_forms IS 'Dynamic admission application form configurations';
COMMENT ON TABLE conference_slots IS 'Available parent-teacher conference time slots';
COMMENT ON TABLE conference_bookings IS 'Parent-teacher conference appointments';
COMMENT ON TABLE staff_evaluations IS 'Teacher and staff performance evaluations';
COMMENT ON TABLE professional_development IS 'Staff professional development activities';
COMMENT ON TABLE school_goals IS 'School-wide strategic goals and targets';
