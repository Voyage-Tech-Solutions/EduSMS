"""
EduCore Backend - Pydantic Models for Core Entities
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# ============== ENUMS ==============

class UserRole(str, Enum):
    SYSTEM_ADMIN = "system_admin"
    PRINCIPAL = "principal"
    OFFICE_ADMIN = "office_admin"
    TEACHER = "teacher"
    PARENT = "parent"
    STUDENT = "student"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class StudentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRANSFERRED = "transferred"
    GRADUATED = "graduated"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


# ============== BASE MODELS ==============

class TimestampMixin(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============== AUTH MODELS ==============

class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: UserRole
    school_id: Optional[str] = None


class UserResponse(UserBase, TimestampMixin):
    id: str
    role: UserRole
    school_id: Optional[str] = None
    is_active: bool = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============== SCHOOL MODELS ==============

class SchoolBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    logo_url: Optional[str] = None


class SchoolCreate(SchoolBase):
    pass


class SchoolResponse(SchoolBase, TimestampMixin):
    id: str
    is_active: bool = True


# ============== STUDENT MODELS ==============

class StudentBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: Gender
    admission_number: Optional[str] = None
    grade_id: Optional[str] = None
    class_id: Optional[str] = None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    grade_id: Optional[str] = None
    class_id: Optional[str] = None
    status: Optional[StudentStatus] = None


class StudentResponse(StudentBase, TimestampMixin):
    id: str
    school_id: str
    status: StudentStatus = StudentStatus.ACTIVE
    admission_number: str


# ============== GUARDIAN MODELS ==============

class GuardianBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    relationship: str = Field(..., max_length=50)  # father, mother, guardian
    phone: str
    email: Optional[EmailStr] = None
    is_primary: bool = False


class GuardianCreate(GuardianBase):
    student_id: str


class GuardianResponse(GuardianBase, TimestampMixin):
    id: str
    student_id: str


# ============== GRADE & CLASS MODELS ==============

class GradeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)  # e.g., "Grade 1", "Form 1"
    order: int = Field(..., ge=1)  # For sorting


class GradeCreate(GradeBase):
    pass


class GradeResponse(GradeBase, TimestampMixin):
    id: str
    school_id: str


class ClassBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)  # e.g., "A", "B"
    grade_id: str
    teacher_id: Optional[str] = None  # Class teacher


class ClassCreate(ClassBase):
    pass


class ClassResponse(ClassBase, TimestampMixin):
    id: str
    school_id: str


# ============== FEE MODELS ==============

class FeeStructureBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., ge=0)
    grade_id: Optional[str] = None  # If null, applies to all grades
    term: Optional[str] = None
    year: int


class FeeStructureCreate(FeeStructureBase):
    pass


class FeeStructureResponse(FeeStructureBase, TimestampMixin):
    id: str
    school_id: str


class InvoiceBase(BaseModel):
    student_id: str
    amount: float
    due_date: date
    description: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    fee_structure_id: Optional[str] = None


class InvoiceResponse(InvoiceBase, TimestampMixin):
    id: str
    school_id: str
    invoice_number: str
    status: PaymentStatus = PaymentStatus.PENDING
    amount_paid: float = 0


class PaymentBase(BaseModel):
    invoice_id: str
    amount: float = Field(..., gt=0)
    payment_method: str  # cash, card, bank_transfer
    reference: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentResponse(PaymentBase, TimestampMixin):
    id: str
    receipt_number: str


# ============== ATTENDANCE MODELS ==============

class AttendanceBase(BaseModel):
    student_id: str
    date: date
    status: AttendanceStatus
    notes: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceBulkCreate(BaseModel):
    date: date
    class_id: str
    records: List[dict]  # [{student_id, status, notes}]


class AttendanceResponse(AttendanceBase, TimestampMixin):
    id: str
    school_id: str
    recorded_by: str


# ============== ACADEMIC MODELS ==============

class SubjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = None


class SubjectCreate(SubjectBase):
    pass


class SubjectResponse(SubjectBase, TimestampMixin):
    id: str
    school_id: str


class GradeEntryBase(BaseModel):
    student_id: str
    subject_id: str
    term: str
    year: int
    score: float = Field(..., ge=0, le=100)
    max_score: float = Field(default=100, ge=0)
    weight: float = Field(default=1.0, ge=0)
    assessment_type: str  # exam, test, assignment


class GradeEntryCreate(GradeEntryBase):
    pass


class GradeEntryResponse(GradeEntryBase, TimestampMixin):
    id: str
    school_id: str
    entered_by: str


# ============== TIMETABLE MODELS ==============

class TimetableSlotBase(BaseModel):
    class_id: str
    subject_id: str
    teacher_id: Optional[str] = None
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday
    start_time: str  # HH:MM
    end_time: str
    room: Optional[str] = None


class TimetableSlotCreate(TimetableSlotBase):
    pass


class TimetableSlotResponse(TimetableSlotBase, TimestampMixin):
    id: str
    school_id: str


# ============== ASSIGNMENT MODELS ==============

class AssignmentStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    DRAFT = "draft"


class SubmissionStatus(str, Enum):
    SUBMITTED = "submitted"
    GRADED = "graded"
    LATE = "late"
    MISSING = "missing"


class AssignmentBase(BaseModel):
    class_id: str
    subject_id: str
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: date
    max_score: Optional[float] = None


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentResponse(AssignmentBase, TimestampMixin):
    id: str
    school_id: str
    teacher_id: Optional[str] = None
    status: AssignmentStatus = AssignmentStatus.ACTIVE


class SubmissionCreate(BaseModel):
    assignment_id: str
    student_id: str


class SubmissionResponse(BaseModel):
    id: str
    assignment_id: str
    student_id: str
    submitted_at: Optional[datetime] = None
    score: Optional[float] = None
    graded_at: Optional[datetime] = None
    status: SubmissionStatus = SubmissionStatus.SUBMITTED


# ============== ANNOUNCEMENT MODELS ==============

class AnnouncementAudience(str, Enum):
    ALL = "all"
    PARENTS = "parents"
    STUDENTS = "students"
    TEACHERS = "teachers"
    STAFF = "staff"


class AnnouncementPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class AnnouncementBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str
    audience: AnnouncementAudience = AnnouncementAudience.ALL
    priority: AnnouncementPriority = AnnouncementPriority.NORMAL


class AnnouncementCreate(AnnouncementBase):
    expires_at: Optional[datetime] = None


class AnnouncementResponse(AnnouncementBase, TimestampMixin):
    id: str
    school_id: str
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_by: Optional[str] = None


# ============== AUDIT LOG MODEL ==============

class AuditLogResponse(BaseModel):
    id: str
    school_id: Optional[str]
    user_id: str
    action: str
    entity_type: str
    entity_id: str
    before_data: Optional[dict] = None
    after_data: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime
