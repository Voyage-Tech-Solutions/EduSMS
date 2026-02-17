-- ============================================================
-- EduSMS Rubric Grades Migration
-- Migration 007 - Rubric Grading Records
-- ============================================================

-- Rubric grades table (for storing grades given using rubrics)
CREATE TABLE IF NOT EXISTS rubric_grades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    rubric_id UUID NOT NULL REFERENCES rubrics(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    assessment_id UUID REFERENCES assessments(id) ON DELETE SET NULL,
    graded_by UUID NOT NULL REFERENCES user_profiles(id) ON DELETE SET NULL,
    criterion_scores JSONB NOT NULL DEFAULT '{}',
    weighted_total DECIMAL(10, 2) NOT NULL DEFAULT 0,
    max_weighted_total DECIMAL(10, 2) NOT NULL DEFAULT 0,
    percentage DECIMAL(5, 2) NOT NULL DEFAULT 0,
    overall_feedback TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for rubric_grades
CREATE INDEX IF NOT EXISTS idx_rubric_grades_school ON rubric_grades(school_id);
CREATE INDEX IF NOT EXISTS idx_rubric_grades_rubric ON rubric_grades(rubric_id);
CREATE INDEX IF NOT EXISTS idx_rubric_grades_student ON rubric_grades(student_id);
CREATE INDEX IF NOT EXISTS idx_rubric_grades_assessment ON rubric_grades(assessment_id);
CREATE INDEX IF NOT EXISTS idx_rubric_grades_graded_by ON rubric_grades(graded_by);
CREATE INDEX IF NOT EXISTS idx_rubric_grades_created ON rubric_grades(created_at);

-- RLS Policies
ALTER TABLE rubric_grades ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS rubric_grades_isolation ON rubric_grades;
CREATE POLICY rubric_grades_isolation ON rubric_grades
    FOR ALL USING (school_id = get_user_school_id());

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_rubric_grades_updated_at ON rubric_grades;
CREATE TRIGGER update_rubric_grades_updated_at
    BEFORE UPDATE ON rubric_grades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Comments
COMMENT ON TABLE rubric_grades IS 'Stores grades given to students using rubrics';
COMMENT ON COLUMN rubric_grades.criterion_scores IS 'JSON object with criterion_id -> {score, feedback, weight}';

-- Add graded_by and graded_at columns to quiz_attempts if not exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'quiz_attempts' AND column_name = 'graded_by'
    ) THEN
        ALTER TABLE quiz_attempts ADD COLUMN graded_by UUID REFERENCES user_profiles(id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'quiz_attempts' AND column_name = 'graded_at'
    ) THEN
        ALTER TABLE quiz_attempts ADD COLUMN graded_at TIMESTAMPTZ;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'quiz_attempts' AND column_name = 'status'
    ) THEN
        ALTER TABLE quiz_attempts ADD COLUMN status VARCHAR(50) DEFAULT 'in_progress';
    END IF;
END $$;

-- Create index for quiz_attempts status
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_status ON quiz_attempts(status);
