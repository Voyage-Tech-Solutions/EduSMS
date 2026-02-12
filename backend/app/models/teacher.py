from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date, time
from uuid import UUID

# Teacher Dashboard
class NextClassCard(BaseModel):
    subject: str
    class_name: str
    time: str
    room: Optional[str]
    student_count: int
    last_attendance: Optional[float]
    pending_tasks: int

class GradingTasksCard(BaseModel):
    ungraded_count: int
    overdue_count: int
    avg_delay_days: float

class TeacherAlert(BaseModel):
    type: str
    message: str
    count: int
    link: str

# Teacher Gradebook
class CreateAssessmentRequest(BaseModel):
    title: str
    type: str
    subject_id: UUID
    class_id: UUID
    term_id: UUID
    total_marks: float
    pass_mark: Optional[float] = 50.0
    weighting: Optional[float] = None
    date_assigned: Optional[date] = None
    due_date: Optional[date] = None
    allow_late: bool = False
    notes: Optional[str] = None

class ImportMarksRequest(BaseModel):
    assessment_id: UUID
    scores: List[dict]

class LockGradebookRequest(BaseModel):
    class_id: UUID
    subject_id: UUID
    term_id: UUID
    reason: Optional[str] = None
    require_approval: bool = False

class AssessmentScore(BaseModel):
    student_id: UUID
    score: Optional[float]
    notes: Optional[str] = None

# Teacher Planning
class CreateLessonPlanRequest(BaseModel):
    date: date
    time_slot: Optional[str] = None
    class_id: UUID
    subject_id: UUID
    term_id: UUID
    topic: str
    objectives: str
    activities: Optional[str] = None
    homework: Optional[str] = None
    notes: Optional[str] = None

class CreateAssessmentPlanRequest(BaseModel):
    title: str
    type: str
    class_id: UUID
    subject_id: UUID
    term_id: UUID
    planned_date: Optional[date] = None
    total_marks: Optional[float] = None
    notes: Optional[str] = None

class UploadResourceRequest(BaseModel):
    title: str
    type: str
    url: str
    class_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    visibility: str = "private"

class CopyWeekRequest(BaseModel):
    from_week: str
    to_week: str
    copy_resources: bool = True
    copy_homework: bool = True
    shift_dates: bool = True

# Teacher Attendance
class AttendancePattern(BaseModel):
    student_id: UUID
    suggested_status: str
    reason: str
