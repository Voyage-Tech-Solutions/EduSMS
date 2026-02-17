-- ============================================================
-- EduSMS Phase 2 Migration: Lesson Planning & Student Monitoring
-- Migration 005 - Curriculum Mapping, Lesson Plans, Interventions
-- ============================================================

-- ============================================================
-- CURRICULUM MAPS
-- Long-term curriculum planning by subject and grade
-- ============================================================

CREATE TABLE IF NOT EXISTS curriculum_maps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    grade_id UUID NOT NULL REFERENCES grades(id) ON DELETE CASCADE,
    academic_year_id UUID,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    -- Units breakdown
    units JSONB NOT NULL DEFAULT '[]',
    -- [{name, duration_weeks, start_date, end_date, standards: [], topics: [], resources: [], assessments: []}]
    pacing_notes TEXT,
    is_published BOOLEAN DEFAULT false,
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(school_id, subject_id, grade_id, academic_year_id)
);

CREATE INDEX IF NOT EXISTS idx_curriculum_maps_school ON curriculum_maps(school_id);
CREATE INDEX IF NOT EXISTS idx_curriculum_maps_subject ON curriculum_maps(subject_id);
CREATE INDEX IF NOT EXISTS idx_curriculum_maps_grade ON curriculum_maps(grade_id);

-- ============================================================
-- LESSON TEMPLATES
-- Reusable lesson plan structures
-- ============================================================

CREATE TABLE IF NOT EXISTS lesson_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    -- Template structure
    structure JSONB NOT NULL DEFAULT '[]',
    -- [{name: "Opening", duration_minutes: 10, type: "engagement", prompts: []}, ...]
    is_system_template BOOLEAN DEFAULT false,
    is_shared BOOLEAN DEFAULT true,
    subject_ids UUID[], -- Applicable subjects
    grade_ids UUID[], -- Applicable grades
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lesson_templates_school ON lesson_templates(school_id);

-- ============================================================
-- ENHANCED LESSON PLANS
-- Comprehensive lesson planning
-- ============================================================

CREATE TABLE IF NOT EXISTS lesson_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    teacher_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    -- Basic Info
    title VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    duration_minutes INTEGER,
    period INTEGER,
    -- Template reference
    template_id UUID REFERENCES lesson_templates(id),
    -- Content
    objectives TEXT[], -- Learning objectives
    essential_question TEXT,
    vocabulary TEXT[],
    -- Lesson Phases
    opening JSONB, -- {duration, activities, materials}
    instruction JSONB, -- Direct instruction
    guided_practice JSONB,
    independent_practice JSONB,
    closing JSONB,
    -- Standards & Differentiation
    standards_covered UUID[], -- References to learning_standards
    differentiation JSONB, -- {struggling: [], advanced: [], ell: [], iep: []}
    accommodations TEXT[],
    -- Resources
    materials TEXT[],
    resources JSONB, -- [{type, title, url}]
    technology_needed TEXT[],
    -- Assessment
    assessment_type VARCHAR(50),
    formative_assessment TEXT,
    summative_assessment_id UUID REFERENCES assessments(id),
    -- Reflection (Post-lesson)
    reflection TEXT,
    what_worked TEXT,
    improvements TEXT,
    student_engagement_rating INTEGER CHECK (student_engagement_rating >= 1 AND student_engagement_rating <= 5),
    objectives_met BOOLEAN,
    -- Status
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'planned', 'taught', 'reviewed')),
    is_substitute_ready BOOLEAN DEFAULT false,
    -- Collaboration
    shared_with UUID[], -- Other teachers
    copied_from UUID REFERENCES lesson_plans(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lesson_plans_teacher ON lesson_plans(teacher_id);
CREATE INDEX IF NOT EXISTS idx_lesson_plans_class ON lesson_plans(class_id);
CREATE INDEX IF NOT EXISTS idx_lesson_plans_date ON lesson_plans(date);
CREATE INDEX IF NOT EXISTS idx_lesson_plans_subject ON lesson_plans(subject_id);
CREATE INDEX IF NOT EXISTS idx_lesson_plans_status ON lesson_plans(status);

-- ============================================================
-- RESOURCE LIBRARY
-- Shared teaching resources
-- ============================================================

CREATE TABLE IF NOT EXISTS teaching_resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    uploaded_by UUID REFERENCES user_profiles(id),
    -- Resource Info
    title VARCHAR(255) NOT NULL,
    description TEXT,
    resource_type VARCHAR(50) NOT NULL CHECK (resource_type IN (
        'document', 'presentation', 'worksheet', 'video', 'link',
        'image', 'audio', 'interactive', 'other'
    )),
    file_url TEXT,
    external_url TEXT,
    thumbnail_url TEXT,
    -- Organization
    subject_ids UUID[],
    grade_ids UUID[],
    standard_ids UUID[],
    tags TEXT[],
    -- Sharing
    is_public BOOLEAN DEFAULT false, -- Visible to all teachers
    shared_with UUID[], -- Specific teachers
    -- Usage tracking
    download_count INTEGER DEFAULT 0,
    favorite_count INTEGER DEFAULT 0,
    rating DECIMAL(3,2),
    rating_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_teaching_resources_school ON teaching_resources(school_id);
CREATE INDEX IF NOT EXISTS idx_teaching_resources_type ON teaching_resources(resource_type);
CREATE INDEX IF NOT EXISTS idx_teaching_resources_tags ON teaching_resources USING GIN(tags);

-- ============================================================
-- STUDENT LEARNING PROFILES
-- Individual learning needs and accommodations
-- ============================================================

CREATE TABLE IF NOT EXISTS student_learning_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE UNIQUE,
    -- Learning Style
    learning_style VARCHAR(50), -- visual, auditory, kinesthetic, reading/writing
    learning_preferences JSONB,
    -- Strengths & Areas for Growth
    strengths TEXT[],
    areas_for_growth TEXT[],
    interests TEXT[],
    -- Special Education
    iep_status VARCHAR(50) CHECK (iep_status IN (
        'none', 'evaluation_pending', 'active', 'exited', 'declined'
    )) DEFAULT 'none',
    iep_start_date DATE,
    iep_end_date DATE,
    iep_goals JSONB, -- [{goal, benchmarks: [], progress: []}]
    iep_accommodations TEXT[],
    iep_modifications TEXT[],
    iep_services JSONB, -- [{service, frequency, provider}]
    -- 504 Plan
    section_504_status VARCHAR(50) CHECK (section_504_status IN (
        'none', 'evaluation_pending', 'active', 'exited'
    )) DEFAULT 'none',
    section_504_accommodations TEXT[],
    -- ELL/ESL
    ell_status VARCHAR(50),
    home_language VARCHAR(100),
    english_proficiency_level VARCHAR(50),
    ell_accommodations TEXT[],
    -- Behavioral
    behavior_plan BOOLEAN DEFAULT false,
    behavior_plan_details JSONB,
    -- Health
    health_concerns TEXT[],
    -- Notes
    teacher_notes TEXT,
    counselor_notes TEXT,
    parent_input TEXT,
    -- Tracking
    last_reviewed DATE,
    reviewed_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_student_learning_profiles_student ON student_learning_profiles(student_id);
CREATE INDEX IF NOT EXISTS idx_student_learning_profiles_iep ON student_learning_profiles(iep_status) WHERE iep_status != 'none';

-- ============================================================
-- STUDENT INTERVENTIONS (RTI/MTSS)
-- Response to Intervention tracking
-- ============================================================

CREATE TABLE IF NOT EXISTS student_interventions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    -- Intervention Details
    tier INTEGER NOT NULL CHECK (tier IN (1, 2, 3)), -- RTI Tiers
    intervention_type VARCHAR(100) NOT NULL, -- academic, behavioral, attendance
    focus_area VARCHAR(100), -- reading, math, writing, behavior
    intervention_name VARCHAR(255) NOT NULL,
    description TEXT,
    -- Schedule
    start_date DATE NOT NULL,
    end_date DATE,
    frequency VARCHAR(100), -- "3x weekly, 30 min"
    duration_minutes INTEGER,
    schedule_details JSONB,
    -- Team
    assigned_to UUID REFERENCES user_profiles(id),
    intervention_team UUID[],
    -- Goals & Progress
    goals JSONB NOT NULL, -- [{goal, target, baseline, current}]
    progress_monitoring_schedule VARCHAR(100), -- weekly, biweekly
    progress_notes JSONB DEFAULT '[]', -- [{date, note, data_points: {}}]
    -- Materials & Strategies
    materials TEXT[],
    strategies TEXT[],
    resources_used JSONB,
    -- Outcomes
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN (
        'planned', 'active', 'paused', 'completed', 'discontinued'
    )),
    outcome VARCHAR(100), -- goal_met, significant_progress, some_progress, minimal_progress, regressed
    outcome_notes TEXT,
    next_steps TEXT,
    -- Parent Communication
    parent_notified BOOLEAN DEFAULT false,
    parent_consent_required BOOLEAN DEFAULT false,
    parent_consent_received BOOLEAN,
    parent_consent_date DATE,
    created_by UUID REFERENCES user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_student_interventions_student ON student_interventions(student_id);
CREATE INDEX IF NOT EXISTS idx_student_interventions_tier ON student_interventions(tier);
CREATE INDEX IF NOT EXISTS idx_student_interventions_status ON student_interventions(status);
CREATE INDEX IF NOT EXISTS idx_student_interventions_assigned ON student_interventions(assigned_to);

-- ============================================================
-- PORTFOLIO ARTIFACTS
-- Student work portfolios
-- ============================================================

CREATE TABLE IF NOT EXISTS portfolio_artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    -- Artifact Info
    title VARCHAR(255) NOT NULL,
    description TEXT,
    artifact_type VARCHAR(50) NOT NULL CHECK (artifact_type IN (
        'work_sample', 'assessment', 'project', 'reflection',
        'presentation', 'artwork', 'writing', 'video', 'other'
    )),
    -- File
    file_url TEXT,
    thumbnail_url TEXT,
    file_type VARCHAR(100),
    -- Academic Context
    subject_id UUID REFERENCES subjects(id),
    class_id UUID REFERENCES classes(id),
    assignment_id UUID REFERENCES assessments(id),
    standard_ids UUID[],
    -- Scoring
    score DECIMAL(10,2),
    max_score DECIMAL(10,2),
    rubric_scores JSONB,
    -- Feedback
    student_reflection TEXT,
    teacher_feedback TEXT,
    peer_feedback TEXT,
    -- Display
    is_featured BOOLEAN DEFAULT false, -- Showcase piece
    is_public BOOLEAN DEFAULT false, -- Parent visible
    display_order INTEGER,
    -- Dates
    work_date DATE,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_portfolio_artifacts_student ON portfolio_artifacts(student_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_artifacts_subject ON portfolio_artifacts(subject_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_artifacts_featured ON portfolio_artifacts(student_id, is_featured) WHERE is_featured = true;

-- ============================================================
-- PROGRESS REPORTS
-- Periodic student progress reports
-- ============================================================

CREATE TABLE IF NOT EXISTS progress_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    academic_year_id UUID,
    term_id UUID,
    report_type VARCHAR(50) DEFAULT 'mid_term' CHECK (report_type IN (
        'weekly', 'mid_term', 'quarter', 'semester', 'annual', 'custom'
    )),
    report_date DATE NOT NULL,
    -- Content
    overall_status VARCHAR(50), -- on_track, needs_support, excelling
    academic_summary TEXT,
    behavior_summary TEXT,
    attendance_summary JSONB, -- {present, absent, tardy, percentage}
    -- By Subject
    subject_progress JSONB, -- [{subject_id, grade, trend, comments}]
    -- Goals
    current_goals JSONB,
    goals_progress JSONB,
    new_goals JSONB,
    -- Comments
    teacher_comments TEXT,
    counselor_comments TEXT,
    principal_comments TEXT,
    -- Status
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN (
        'draft', 'submitted', 'approved', 'sent'
    )),
    submitted_by UUID REFERENCES user_profiles(id),
    submitted_at TIMESTAMPTZ,
    approved_by UUID REFERENCES user_profiles(id),
    approved_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    parent_viewed_at TIMESTAMPTZ,
    parent_acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_progress_reports_student ON progress_reports(student_id);
CREATE INDEX IF NOT EXISTS idx_progress_reports_date ON progress_reports(report_date);
CREATE INDEX IF NOT EXISTS idx_progress_reports_status ON progress_reports(status);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE curriculum_maps ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE lesson_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE teaching_resources ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_learning_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_interventions ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE progress_reports ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS curriculum_maps_isolation ON curriculum_maps;
CREATE POLICY curriculum_maps_isolation ON curriculum_maps
    FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS lesson_templates_isolation ON lesson_templates;
CREATE POLICY lesson_templates_isolation ON lesson_templates
    FOR ALL USING (school_id IS NULL OR school_id = get_user_school_id());

DROP POLICY IF EXISTS lesson_plans_isolation ON lesson_plans;
CREATE POLICY lesson_plans_isolation ON lesson_plans
    FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS teaching_resources_isolation ON teaching_resources;
CREATE POLICY teaching_resources_isolation ON teaching_resources
    FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS student_learning_profiles_isolation ON student_learning_profiles;
CREATE POLICY student_learning_profiles_isolation ON student_learning_profiles
    FOR ALL USING (
        EXISTS (SELECT 1 FROM students s WHERE s.id = student_id AND s.school_id = get_user_school_id())
    );

DROP POLICY IF EXISTS student_interventions_isolation ON student_interventions;
CREATE POLICY student_interventions_isolation ON student_interventions
    FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS portfolio_artifacts_isolation ON portfolio_artifacts;
CREATE POLICY portfolio_artifacts_isolation ON portfolio_artifacts
    FOR ALL USING (school_id = get_user_school_id());

DROP POLICY IF EXISTS progress_reports_isolation ON progress_reports;
CREATE POLICY progress_reports_isolation ON progress_reports
    FOR ALL USING (school_id = get_user_school_id());

-- ============================================================
-- TRIGGERS
-- ============================================================

DROP TRIGGER IF EXISTS update_curriculum_maps_updated_at ON curriculum_maps;
CREATE TRIGGER update_curriculum_maps_updated_at BEFORE UPDATE ON curriculum_maps
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS update_lesson_templates_updated_at ON lesson_templates;
CREATE TRIGGER update_lesson_templates_updated_at BEFORE UPDATE ON lesson_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS update_lesson_plans_updated_at ON lesson_plans;
CREATE TRIGGER update_lesson_plans_updated_at BEFORE UPDATE ON lesson_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS update_teaching_resources_updated_at ON teaching_resources;
CREATE TRIGGER update_teaching_resources_updated_at BEFORE UPDATE ON teaching_resources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS update_student_learning_profiles_updated_at ON student_learning_profiles;
CREATE TRIGGER update_student_learning_profiles_updated_at BEFORE UPDATE ON student_learning_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS update_student_interventions_updated_at ON student_interventions;
CREATE TRIGGER update_student_interventions_updated_at BEFORE UPDATE ON student_interventions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS update_progress_reports_updated_at ON progress_reports;
CREATE TRIGGER update_progress_reports_updated_at BEFORE UPDATE ON progress_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- COMMENTS
-- ============================================================

COMMENT ON TABLE curriculum_maps IS 'Long-term curriculum planning and pacing guides';
COMMENT ON TABLE lesson_templates IS 'Reusable lesson plan structures and templates';
COMMENT ON TABLE lesson_plans IS 'Daily/weekly lesson plans with all instructional details';
COMMENT ON TABLE teaching_resources IS 'Shared library of teaching materials and resources';
COMMENT ON TABLE student_learning_profiles IS 'Individual student learning needs, IEP, 504, and accommodations';
COMMENT ON TABLE student_interventions IS 'RTI/MTSS intervention tracking and progress monitoring';
COMMENT ON TABLE portfolio_artifacts IS 'Student work portfolio pieces and artifacts';
COMMENT ON TABLE progress_reports IS 'Periodic student progress reports for parent communication';
