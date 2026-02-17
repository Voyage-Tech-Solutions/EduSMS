-- ============================================================
-- EduSMS Phase 2 Migration: Gradebook & Assessment System
-- Migration 004 - Enhanced Gradebook, Quiz Builder, Question Bank
-- ============================================================

-- ============================================================
-- GRADING SCALES
-- Support for different grading systems (percentage, letter, points)
-- ============================================================

CREATE TABLE IF NOT EXISTS grading_scales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('percentage', 'letter', 'points', 'standards', 'pass_fail')),
    scale_config JSONB NOT NULL, -- {A: {min: 90, max: 100, gpa: 4.0}, B: {min: 80, max: 89, gpa: 3.0}}
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(school_id, name)
);

CREATE INDEX IF NOT EXISTS idx_grading_scales_school ON grading_scales(school_id);

-- ============================================================
-- GRADE CATEGORIES (Weighted Categories)
-- For weighted grading: Homework 20%, Tests 40%, Projects 40%
-- ============================================================

CREATE TABLE IF NOT EXISTS grade_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    academic_year_id UUID,
    term_id UUID,
    name VARCHAR(100) NOT NULL, -- Homework, Tests, Projects, Participation
    weight DECIMAL(5,2) NOT NULL CHECK (weight >= 0 AND weight <= 100), -- Percentage weight
    drop_lowest INTEGER DEFAULT 0, -- Number of lowest scores to drop
    is_extra_credit BOOLEAN DEFAULT false,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_grade_categories_class ON grade_categories(class_id);
CREATE INDEX IF NOT EXISTS idx_grade_categories_subject ON grade_categories(subject_id);

-- ============================================================
-- LEARNING STANDARDS
-- Standards-based grading support (e.g., Common Core, NGSS)
-- ============================================================

CREATE TABLE IF NOT EXISTS learning_standards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL, -- CCSS.MATH.3.OA.1
    short_code VARCHAR(20), -- 3.OA.1
    description TEXT NOT NULL,
    grade_level VARCHAR(50), -- Grade 3, K-2, High School
    subject VARCHAR(100),
    strand VARCHAR(100), -- Operations and Algebraic Thinking
    parent_id UUID REFERENCES learning_standards(id) ON DELETE SET NULL,
    source VARCHAR(100), -- Common Core, State Standards, Custom
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(school_id, code)
);

CREATE INDEX IF NOT EXISTS idx_learning_standards_school ON learning_standards(school_id);
CREATE INDEX IF NOT EXISTS idx_learning_standards_subject ON learning_standards(subject);
CREATE INDEX IF NOT EXISTS idx_learning_standards_grade ON learning_standards(grade_level);
CREATE INDEX IF NOT EXISTS idx_learning_standards_parent ON learning_standards(parent_id);

-- ============================================================
-- STANDARD SCORES
-- Track student proficiency on standards
-- ============================================================

CREATE TABLE IF NOT EXISTS standard_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    standard_id UUID NOT NULL REFERENCES learning_standards(id) ON DELETE CASCADE,
    assessment_id UUID REFERENCES assessments(id) ON DELETE SET NULL,
    proficiency_level INTEGER NOT NULL CHECK (proficiency_level >= 1 AND proficiency_level <= 4),
    -- 1=Beginning, 2=Developing, 3=Proficient, 4=Advanced
    notes TEXT,
    assessed_by UUID REFERENCES user_profiles(id),
    assessed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(student_id, standard_id, assessment_id)
);

CREATE INDEX IF NOT EXISTS idx_standard_scores_student ON standard_scores(student_id);
CREATE INDEX IF NOT EXISTS idx_standard_scores_standard ON standard_scores(standard_id);

-- ============================================================
-- RUBRICS
-- Detailed scoring rubrics for assessments
-- ============================================================

CREATE TABLE IF NOT EXISTS rubrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    teacher_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    criteria JSONB NOT NULL,
    -- [{name: "Content", weight: 40, levels: [{score: 4, label: "Excellent", description: "..."}, ...]}]
    max_score DECIMAL(10,2),
    is_template BOOLEAN DEFAULT false,
    is_shared BOOLEAN DEFAULT false, -- Shared with other teachers
    subject_id UUID REFERENCES subjects(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rubrics_school ON rubrics(school_id);
CREATE INDEX IF NOT EXISTS idx_rubrics_teacher ON rubrics(teacher_id);

-- ============================================================
-- QUESTION BANK
-- Reusable questions for assessments
-- ============================================================

CREATE TABLE IF NOT EXISTS question_bank (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    teacher_id UUID REFERENCES user_profiles(id) ON DELETE SET NULL,
    subject_id UUID REFERENCES subjects(id),
    grade_id UUID REFERENCES grades(id),
    question_type VARCHAR(50) NOT NULL CHECK (question_type IN (
        'multiple_choice', 'true_false', 'short_answer', 'essay',
        'matching', 'fill_blank', 'numeric', 'ordering'
    )),
    question_text TEXT NOT NULL,
    question_html TEXT, -- Rich text version
    question_media JSONB, -- [{type: 'image', url: '...'}]
    options JSONB, -- For MCQ: [{id, text, is_correct, feedback}]
    correct_answer TEXT, -- For non-MCQ
    answer_key JSONB, -- Detailed answer with explanation
    points DECIMAL(10,2) DEFAULT 1,
    difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard')),
    bloom_level VARCHAR(50), -- Remember, Understand, Apply, Analyze, Evaluate, Create
    tags TEXT[],
    standard_ids UUID[], -- Linked standards
    times_used INTEGER DEFAULT 0,
    avg_score DECIMAL(5,2),
    discrimination_index DECIMAL(5,4), -- Item analysis
    is_active BOOLEAN DEFAULT true,
    is_shared BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_question_bank_school ON question_bank(school_id);
CREATE INDEX IF NOT EXISTS idx_question_bank_teacher ON question_bank(teacher_id);
CREATE INDEX IF NOT EXISTS idx_question_bank_subject ON question_bank(subject_id);
CREATE INDEX IF NOT EXISTS idx_question_bank_type ON question_bank(question_type);
CREATE INDEX IF NOT EXISTS idx_question_bank_difficulty ON question_bank(difficulty);
CREATE INDEX IF NOT EXISTS idx_question_bank_tags ON question_bank USING GIN(tags);

-- ============================================================
-- ENHANCED ASSESSMENTS
-- Add additional fields to existing assessments table
-- ============================================================

ALTER TABLE assessments ADD COLUMN IF NOT EXISTS assessment_type VARCHAR(50) DEFAULT 'standard';
-- standard, quiz, test, exam, project, homework, formative, summative

ALTER TABLE assessments ADD COLUMN IF NOT EXISTS grading_scale_id UUID REFERENCES grading_scales(id);
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS category_id UUID REFERENCES grade_categories(id);
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS rubric_id UUID REFERENCES rubrics(id);
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS instructions TEXT;
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS time_limit_minutes INTEGER;
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS attempts_allowed INTEGER DEFAULT 1;
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS shuffle_questions BOOLEAN DEFAULT false;
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS shuffle_options BOOLEAN DEFAULT false;
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS show_correct_answers BOOLEAN DEFAULT false;
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS show_correct_after VARCHAR(50) DEFAULT 'submission';
-- submission, due_date, manual, never
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS release_scores_at TIMESTAMPTZ;
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS late_submission_policy VARCHAR(50) DEFAULT 'accept';
-- accept, penalize, reject
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS late_penalty_percent DECIMAL(5,2) DEFAULT 0;
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS standards_ids UUID[];
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS weight DECIMAL(5,2) DEFAULT 1;
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS is_published BOOLEAN DEFAULT false;
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ;

-- ============================================================
-- ASSESSMENT QUESTIONS
-- Link questions to assessments
-- ============================================================

CREATE TABLE IF NOT EXISTS assessment_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    question_id UUID REFERENCES question_bank(id) ON DELETE SET NULL,
    -- If question_id is null, question is inline (not from bank)
    question_order INTEGER NOT NULL,
    points DECIMAL(10,2) NOT NULL,
    -- Inline question data (when not from bank)
    question_type VARCHAR(50),
    question_text TEXT,
    options JSONB,
    correct_answer TEXT,
    is_required BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assessment_questions_assessment ON assessment_questions(assessment_id);
CREATE INDEX IF NOT EXISTS idx_assessment_questions_question ON assessment_questions(question_id);

-- ============================================================
-- QUIZ ATTEMPTS / SUBMISSIONS
-- Track student quiz attempts
-- ============================================================

CREATE TABLE IF NOT EXISTS quiz_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    attempt_number INTEGER DEFAULT 1,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submitted_at TIMESTAMPTZ,
    time_spent_seconds INTEGER,
    -- Scores
    auto_score DECIMAL(10,2), -- Automatically graded
    manual_score DECIMAL(10,2), -- Teacher-graded portions
    final_score DECIMAL(10,2),
    percentage DECIMAL(5,2),
    letter_grade VARCHAR(10),
    -- Answers
    answers JSONB NOT NULL DEFAULT '{}', -- {question_id: {answer, auto_score, manual_score, feedback}}
    -- Status
    status VARCHAR(50) DEFAULT 'in_progress' CHECK (status IN (
        'in_progress', 'submitted', 'graded', 'returned'
    )),
    graded_by UUID REFERENCES user_profiles(id),
    graded_at TIMESTAMPTZ,
    feedback TEXT,
    is_late BOOLEAN DEFAULT false,
    late_penalty_applied DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quiz_attempts_assessment ON quiz_attempts(assessment_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_student ON quiz_attempts(student_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_status ON quiz_attempts(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_quiz_attempts_unique ON quiz_attempts(assessment_id, student_id, attempt_number);

-- ============================================================
-- GRADEBOOK ENTRIES
-- Consolidated gradebook for all student grades
-- ============================================================

CREATE TABLE IF NOT EXISTS gradebook_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    academic_year_id UUID,
    term_id UUID,
    -- Source reference
    assessment_id UUID REFERENCES assessments(id) ON DELETE SET NULL,
    quiz_attempt_id UUID REFERENCES quiz_attempts(id) ON DELETE SET NULL,
    category_id UUID REFERENCES grade_categories(id),
    -- Grade data
    score DECIMAL(10,2),
    max_score DECIMAL(10,2),
    percentage DECIMAL(5,2),
    letter_grade VARCHAR(10),
    points DECIMAL(10,2),
    weight DECIMAL(5,2) DEFAULT 1,
    is_extra_credit BOOLEAN DEFAULT false,
    is_missing BOOLEAN DEFAULT false,
    is_excused BOOLEAN DEFAULT false,
    -- Metadata
    notes TEXT,
    entered_by UUID REFERENCES user_profiles(id),
    entered_at TIMESTAMPTZ DEFAULT NOW(),
    modified_by UUID REFERENCES user_profiles(id),
    modified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gradebook_school ON gradebook_entries(school_id);
CREATE INDEX IF NOT EXISTS idx_gradebook_student ON gradebook_entries(student_id);
CREATE INDEX IF NOT EXISTS idx_gradebook_class ON gradebook_entries(class_id);
CREATE INDEX IF NOT EXISTS idx_gradebook_subject ON gradebook_entries(subject_id);
CREATE INDEX IF NOT EXISTS idx_gradebook_assessment ON gradebook_entries(assessment_id);
CREATE INDEX IF NOT EXISTS idx_gradebook_category ON gradebook_entries(category_id);

-- ============================================================
-- GRADE OVERRIDES
-- Track manual grade adjustments
-- ============================================================

CREATE TABLE IF NOT EXISTS grade_overrides (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    gradebook_entry_id UUID NOT NULL REFERENCES gradebook_entries(id) ON DELETE CASCADE,
    original_score DECIMAL(10,2),
    override_score DECIMAL(10,2) NOT NULL,
    reason TEXT NOT NULL,
    override_by UUID NOT NULL REFERENCES user_profiles(id),
    override_at TIMESTAMPTZ DEFAULT NOW(),
    approved_by UUID REFERENCES user_profiles(id),
    approved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_grade_overrides_entry ON grade_overrides(gradebook_entry_id);

-- ============================================================
-- TERM GRADES
-- Calculated term/semester grades
-- ============================================================

CREATE TABLE IF NOT EXISTS term_grades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    academic_year_id UUID,
    term_id UUID,
    -- Calculated grades
    raw_average DECIMAL(5,2),
    weighted_average DECIMAL(5,2),
    final_percentage DECIMAL(5,2),
    final_letter_grade VARCHAR(10),
    gpa_points DECIMAL(4,2),
    -- Status
    status VARCHAR(50) DEFAULT 'in_progress' CHECK (status IN (
        'in_progress', 'calculated', 'finalized', 'published'
    )),
    finalized_by UUID REFERENCES user_profiles(id),
    finalized_at TIMESTAMPTZ,
    -- Comments
    teacher_comment TEXT,
    conduct_grade VARCHAR(20),
    effort_grade VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(student_id, class_id, subject_id, term_id)
);

CREATE INDEX IF NOT EXISTS idx_term_grades_student ON term_grades(student_id);
CREATE INDEX IF NOT EXISTS idx_term_grades_class ON term_grades(class_id);
CREATE INDEX IF NOT EXISTS idx_term_grades_term ON term_grades(term_id);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE grading_scales ENABLE ROW LEVEL SECURITY;
ALTER TABLE grade_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_standards ENABLE ROW LEVEL SECURITY;
ALTER TABLE standard_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE rubrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_bank ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE gradebook_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE grade_overrides ENABLE ROW LEVEL SECURITY;
ALTER TABLE term_grades ENABLE ROW LEVEL SECURITY;

-- School isolation policies
CREATE POLICY grading_scales_isolation ON grading_scales
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY grade_categories_isolation ON grade_categories
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY learning_standards_isolation ON learning_standards
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY standard_scores_isolation ON standard_scores
    FOR ALL USING (
        EXISTS (SELECT 1 FROM students s WHERE s.id = student_id AND s.school_id = get_user_school_id())
    );

CREATE POLICY rubrics_isolation ON rubrics
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY question_bank_isolation ON question_bank
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY assessment_questions_isolation ON assessment_questions
    FOR ALL USING (
        EXISTS (SELECT 1 FROM assessments a WHERE a.id = assessment_id AND a.school_id = get_user_school_id())
    );

CREATE POLICY quiz_attempts_isolation ON quiz_attempts
    FOR ALL USING (
        EXISTS (SELECT 1 FROM assessments a WHERE a.id = assessment_id AND a.school_id = get_user_school_id())
    );

CREATE POLICY gradebook_entries_isolation ON gradebook_entries
    FOR ALL USING (school_id = get_user_school_id());

CREATE POLICY grade_overrides_isolation ON grade_overrides
    FOR ALL USING (
        EXISTS (SELECT 1 FROM gradebook_entries g WHERE g.id = gradebook_entry_id AND g.school_id = get_user_school_id())
    );

CREATE POLICY term_grades_isolation ON term_grades
    FOR ALL USING (school_id = get_user_school_id());

-- ============================================================
-- TRIGGERS
-- ============================================================

CREATE TRIGGER update_grading_scales_updated_at BEFORE UPDATE ON grading_scales
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_grade_categories_updated_at BEFORE UPDATE ON grade_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_rubrics_updated_at BEFORE UPDATE ON rubrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_question_bank_updated_at BEFORE UPDATE ON question_bank
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_quiz_attempts_updated_at BEFORE UPDATE ON quiz_attempts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_gradebook_entries_updated_at BEFORE UPDATE ON gradebook_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_term_grades_updated_at BEFORE UPDATE ON term_grades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- HELPER FUNCTIONS
-- ============================================================

-- Calculate weighted average for a student in a class/subject
CREATE OR REPLACE FUNCTION calculate_weighted_average(
    p_student_id UUID,
    p_class_id UUID,
    p_subject_id UUID,
    p_term_id UUID DEFAULT NULL
)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    weighted_sum DECIMAL(20,4) := 0;
    total_weight DECIMAL(10,4) := 0;
    category RECORD;
    category_avg DECIMAL(10,4);
    category_count INTEGER;
BEGIN
    -- Get each category and calculate weighted contribution
    FOR category IN
        SELECT gc.id, gc.weight, gc.drop_lowest
        FROM grade_categories gc
        WHERE gc.class_id = p_class_id
        AND gc.subject_id = p_subject_id
        AND (p_term_id IS NULL OR gc.term_id = p_term_id)
    LOOP
        -- Calculate average for this category
        SELECT AVG(percentage), COUNT(*)
        INTO category_avg, category_count
        FROM (
            SELECT percentage
            FROM gradebook_entries
            WHERE student_id = p_student_id
            AND class_id = p_class_id
            AND subject_id = p_subject_id
            AND category_id = category.id
            AND is_excused = false
            ORDER BY percentage ASC
            OFFSET category.drop_lowest
        ) sub;

        IF category_avg IS NOT NULL THEN
            weighted_sum := weighted_sum + (category_avg * category.weight / 100);
            total_weight := total_weight + category.weight;
        END IF;
    END LOOP;

    IF total_weight = 0 THEN
        RETURN NULL;
    END IF;

    RETURN ROUND((weighted_sum / total_weight * 100)::DECIMAL, 2);
END;
$$ LANGUAGE plpgsql;

-- Get letter grade from percentage
CREATE OR REPLACE FUNCTION get_letter_grade(
    p_percentage DECIMAL(5,2),
    p_grading_scale_id UUID
)
RETURNS VARCHAR(10) AS $$
DECLARE
    scale_config JSONB;
    grade_key TEXT;
    grade_value JSONB;
    result VARCHAR(10) := NULL;
BEGIN
    SELECT scale_config INTO scale_config
    FROM grading_scales
    WHERE id = p_grading_scale_id;

    IF scale_config IS NULL THEN
        -- Default grading scale
        IF p_percentage >= 90 THEN RETURN 'A';
        ELSIF p_percentage >= 80 THEN RETURN 'B';
        ELSIF p_percentage >= 70 THEN RETURN 'C';
        ELSIF p_percentage >= 60 THEN RETURN 'D';
        ELSE RETURN 'F';
        END IF;
    END IF;

    FOR grade_key, grade_value IN SELECT * FROM jsonb_each(scale_config)
    LOOP
        IF p_percentage >= (grade_value->>'min')::DECIMAL
        AND p_percentage <= (grade_value->>'max')::DECIMAL THEN
            RETURN grade_key;
        END IF;
    END LOOP;

    RETURN 'F';
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- COMMENTS
-- ============================================================

COMMENT ON TABLE grading_scales IS 'Configurable grading scales for different assessment types';
COMMENT ON TABLE grade_categories IS 'Weighted grade categories (Homework, Tests, Projects, etc.)';
COMMENT ON TABLE learning_standards IS 'Academic standards for standards-based grading';
COMMENT ON TABLE standard_scores IS 'Student proficiency scores on learning standards';
COMMENT ON TABLE rubrics IS 'Detailed scoring rubrics for assessments';
COMMENT ON TABLE question_bank IS 'Reusable question library for assessments';
COMMENT ON TABLE assessment_questions IS 'Questions linked to specific assessments';
COMMENT ON TABLE quiz_attempts IS 'Student quiz/test attempt tracking';
COMMENT ON TABLE gradebook_entries IS 'Consolidated gradebook with all student scores';
COMMENT ON TABLE term_grades IS 'Calculated term/semester grades';
