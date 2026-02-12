from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID

# Parent Dashboard
class ChildSelector(BaseModel):
    student_id: UUID
    name: str
    grade: str
    class_name: Optional[str]

class DailyStatus(BaseModel):
    attendance_status: str
    next_class: Optional[str]
    alerts_count: int

class AcademicSnapshot(BaseModel):
    current_average: float
    status: str  # good, at_risk, failing
    latest_score: Optional[float]
    missing_assignments: int

class FinancialSummary(BaseModel):
    outstanding_balance: float
    overdue: bool
    next_due_date: Optional[date]

# Attendance
class ReportAbsenceRequest(BaseModel):
    student_id: UUID
    absence_date: date
    reason: str
    supporting_document_url: Optional[str] = None

# Assignments
class AssignmentItem(BaseModel):
    id: UUID
    title: str
    subject: str
    due_date: date
    status: str
    score: Optional[float]

class SubmitAssignmentRequest(BaseModel):
    assignment_id: UUID
    student_id: UUID
    submission_url: str
    notes: Optional[str] = None

# Payments
class PaymentRequest(BaseModel):
    invoice_id: UUID
    amount: float
    payment_method: str
    transaction_reference: Optional[str] = None

# Documents
class UploadDocumentRequest(BaseModel):
    student_id: UUID
    document_type: str
    file_url: str
    expiry_date: Optional[date] = None

# Messages
class SendMessageRequest(BaseModel):
    recipient_id: UUID
    subject: str
    message: str
    attachment_url: Optional[str] = None
    thread_id: Optional[UUID] = None

# Notices
class AcknowledgeNoticeRequest(BaseModel):
    notice_id: UUID
