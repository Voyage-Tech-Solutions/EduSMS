from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID

# Principal Students
class StudentOversightFilter(BaseModel):
    search: Optional[str] = None
    grade_id: Optional[UUID] = None
    status: Optional[str] = None
    risk_level: Optional[str] = None
    attendance_below: Optional[float] = None
    academic_below: Optional[float] = None
    overdue_fees: Optional[bool] = None

class StudentOversightRow(BaseModel):
    id: UUID
    admission_number: str
    name: str
    grade: str
    class_name: Optional[str]
    gender: str
    status: str
    attendance_percentage: float
    academic_average: float
    outstanding_fees: float
    risk_level: Optional[str]

class FlagInterventionRequest(BaseModel):
    student_id: UUID
    risk_type: str
    severity: str
    assigned_to: Optional[UUID] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None

class SendNotificationRequest(BaseModel):
    student_id: UUID
    template: str
    channel: str
    include_performance: bool = False

class ChangeStatusRequest(BaseModel):
    student_id: UUID
    new_status: str
    reason: str
    effective_date: date

# Principal Approvals
class ApprovalRequest(BaseModel):
    type: str
    entity_id: UUID
    entity_type: str
    description: str
    priority: str = "normal"
    metadata: Optional[dict] = None

class ApprovalDecision(BaseModel):
    decision: str
    notes: Optional[str] = None
    notify_requester: bool = True
    notify_affected: bool = False

class ApprovalRow(BaseModel):
    id: UUID
    request_id: str
    type: str
    entity_name: str
    description: str
    priority: str
    submitted_by: str
    submitted_at: datetime
    status: str

# Principal Reports
class ReportFilter(BaseModel):
    date_range: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class GenerateReportRequest(BaseModel):
    report_type: str
    filters: dict
    format: str = "pdf"
