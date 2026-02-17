"""
EduCore Backend - Message Templates API
Reusable message and notification templates
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import re

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class TemplateCreate(BaseModel):
    """Create a message template"""
    name: str
    category: str  # announcement, message, notification, email, sms
    subject: Optional[str] = None
    body: str
    variables: List[str] = []  # e.g., ["student_name", "date", "amount"]
    is_system: bool = False
    tags: List[str] = []


class TemplateUpdate(BaseModel):
    """Update a template"""
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    variables: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class RenderTemplateRequest(BaseModel):
    """Request to render a template with variables"""
    template_id: Optional[UUID] = None
    template_body: Optional[str] = None
    variables: dict = {}


# ============================================================
# BUILT-IN TEMPLATES
# ============================================================

SYSTEM_TEMPLATES = [
    {
        "id": "welcome_parent",
        "name": "Welcome Parent",
        "category": "email",
        "subject": "Welcome to {{school_name}}",
        "body": """Dear {{parent_name}},

Welcome to {{school_name}}! We are excited to have {{student_name}} join our school community.

Your login credentials have been sent to your email. Please log in to our parent portal to:
- View your child's academic progress
- Check attendance records
- Pay fees online
- Communicate with teachers

If you have any questions, please don't hesitate to contact us.

Best regards,
{{school_name}} Administration""",
        "variables": ["parent_name", "student_name", "school_name"],
        "is_system": True
    },
    {
        "id": "fee_reminder",
        "name": "Fee Payment Reminder",
        "category": "notification",
        "subject": "Fee Payment Reminder",
        "body": "Dear {{parent_name}}, this is a reminder that a fee payment of {{currency}}{{amount}} for {{fee_type}} is due on {{due_date}}. Please make the payment through our parent portal.",
        "variables": ["parent_name", "amount", "currency", "fee_type", "due_date"],
        "is_system": True
    },
    {
        "id": "fee_overdue",
        "name": "Overdue Fee Notice",
        "category": "notification",
        "subject": "Overdue Fee Notice",
        "body": "Dear {{parent_name}}, the fee payment of {{currency}}{{amount}} for {{fee_type}} was due on {{due_date}} and is now overdue. Please make the payment immediately to avoid late fees.",
        "variables": ["parent_name", "amount", "currency", "fee_type", "due_date"],
        "is_system": True
    },
    {
        "id": "attendance_absent",
        "name": "Absence Notification",
        "category": "sms",
        "subject": None,
        "body": "{{school_name}}: {{student_name}} was marked absent today ({{date}}). If this is incorrect, please contact the school.",
        "variables": ["school_name", "student_name", "date"],
        "is_system": True
    },
    {
        "id": "attendance_late",
        "name": "Late Arrival Notification",
        "category": "notification",
        "subject": "Late Arrival Notice",
        "body": "{{student_name}} arrived late to school today at {{arrival_time}}. Please ensure timely arrival for optimal learning.",
        "variables": ["student_name", "arrival_time"],
        "is_system": True
    },
    {
        "id": "grade_posted",
        "name": "Grade Posted Notification",
        "category": "notification",
        "subject": "New Grade Posted",
        "body": "{{student_name}} received a grade of {{score}} ({{grade_letter}}) in {{subject}} for {{assessment_name}}.",
        "variables": ["student_name", "score", "grade_letter", "subject", "assessment_name"],
        "is_system": True
    },
    {
        "id": "low_grade_alert",
        "name": "Low Grade Alert",
        "category": "notification",
        "subject": "Academic Alert",
        "body": "Dear {{parent_name}}, {{student_name}}'s grade in {{subject}} has dropped to {{score}}. Please schedule a meeting with the teacher to discuss support strategies.",
        "variables": ["parent_name", "student_name", "subject", "score"],
        "is_system": True
    },
    {
        "id": "event_reminder",
        "name": "Event Reminder",
        "category": "notification",
        "subject": "Upcoming Event: {{event_name}}",
        "body": "Reminder: {{event_name}} is scheduled for {{event_date}} at {{event_time}}. Location: {{location}}. We look forward to seeing you there!",
        "variables": ["event_name", "event_date", "event_time", "location"],
        "is_system": True
    },
    {
        "id": "conference_reminder",
        "name": "Conference Reminder",
        "category": "sms",
        "subject": None,
        "body": "Reminder: Your parent-teacher conference with {{teacher_name}} is scheduled for {{date}} at {{time}}. Please arrive 5 minutes early.",
        "variables": ["teacher_name", "date", "time"],
        "is_system": True
    },
    {
        "id": "report_card_ready",
        "name": "Report Card Ready",
        "category": "email",
        "subject": "Report Card Available for {{student_name}}",
        "body": """Dear {{parent_name}},

The report card for {{student_name}} for {{term_name}} is now available.

You can view and download the report card by logging into the parent portal.

Overall GPA: {{gpa}}
Attendance: {{attendance_rate}}%

If you have any questions about your child's progress, please contact the class teacher.

Best regards,
{{school_name}}""",
        "variables": ["parent_name", "student_name", "term_name", "gpa", "attendance_rate", "school_name"],
        "is_system": True
    },
    {
        "id": "password_reset",
        "name": "Password Reset",
        "category": "email",
        "subject": "Password Reset Request",
        "body": """Hello {{user_name}},

We received a request to reset your password for your {{school_name}} account.

Click the link below to reset your password:
{{reset_link}}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
{{school_name}}""",
        "variables": ["user_name", "school_name", "reset_link"],
        "is_system": True
    }
]


# ============================================================
# TEMPLATE CRUD
# ============================================================

@router.get("")
async def list_templates(
    category: Optional[str] = None,
    include_system: bool = True,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List message templates"""
    school_id = current_user.get("school_id")

    templates = []

    # Add system templates
    if include_system:
        for t in SYSTEM_TEMPLATES:
            if not category or t["category"] == category:
                if not search or search.lower() in t["name"].lower():
                    templates.append({**t, "source": "system"})

    # Get custom templates
    query = supabase.table("message_templates").select("*").eq("school_id", school_id)

    if category:
        query = query.eq("category", category)

    result = query.order("name").execute()

    for t in (result.data or []):
        if not search or search.lower() in t["name"].lower():
            templates.append({**t, "source": "custom"})

    return {"templates": templates}


@router.get("/system")
async def get_system_templates():
    """Get all system templates"""
    return {"templates": SYSTEM_TEMPLATES}


@router.get("/categories")
async def get_template_categories():
    """Get available template categories"""
    return {
        "categories": [
            {"id": "announcement", "name": "Announcement", "description": "School-wide announcements"},
            {"id": "message", "name": "Message", "description": "Direct messages between users"},
            {"id": "notification", "name": "Notification", "description": "Push/in-app notifications"},
            {"id": "email", "name": "Email", "description": "Email communications"},
            {"id": "sms", "name": "SMS", "description": "Text message notifications"}
        ]
    }


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get template by ID"""
    # Check system templates first
    for t in SYSTEM_TEMPLATES:
        if t["id"] == template_id:
            return {**t, "source": "system"}

    # Check custom templates
    result = supabase.table("message_templates").select("*").eq(
        "id", template_id
    ).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Template not found")

    return {**result.data, "source": "custom"}


@router.post("")
async def create_template(
    template: TemplateCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a custom template"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")

    # Extract variables from body
    variables = template.variables or _extract_variables(template.body)
    if template.subject:
        variables.extend(_extract_variables(template.subject))
    variables = list(set(variables))

    template_data = {
        "school_id": school_id,
        "created_by": user_id,
        "name": template.name,
        "category": template.category,
        "subject": template.subject,
        "body": template.body,
        "variables": variables,
        "is_system": False,
        "tags": template.tags
    }

    result = supabase.table("message_templates").insert(template_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create template")

    return result.data[0]


@router.put("/{template_id}")
async def update_template(
    template_id: UUID,
    update: TemplateUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a custom template"""
    existing = supabase.table("message_templates").select("is_system").eq(
        "id", str(template_id)
    ).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Template not found")

    if existing.data.get("is_system"):
        raise HTTPException(status_code=400, detail="Cannot modify system templates")

    update_data = {k: v for k, v in update.dict().items() if v is not None}

    # Re-extract variables if body changed
    if update.body:
        variables = _extract_variables(update.body)
        if update.variables:
            variables.extend(update.variables)
        update_data["variables"] = list(set(variables))

    result = supabase.table("message_templates").update(update_data).eq(
        "id", str(template_id)
    ).execute()

    return result.data[0] if result.data else None


@router.delete("/{template_id}")
async def delete_template(
    template_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a custom template"""
    existing = supabase.table("message_templates").select("is_system").eq(
        "id", str(template_id)
    ).single().execute()

    if existing.data and existing.data.get("is_system"):
        raise HTTPException(status_code=400, detail="Cannot delete system templates")

    supabase.table("message_templates").delete().eq("id", str(template_id)).execute()
    return {"success": True}


# ============================================================
# TEMPLATE RENDERING
# ============================================================

@router.post("/render")
async def render_template(
    request: RenderTemplateRequest,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Render a template with provided variables"""
    template_body = request.template_body

    if request.template_id:
        # Get template
        template = await get_template(str(request.template_id), current_user, supabase)
        template_body = template.get("body", "")
        subject = template.get("subject")
    else:
        subject = None

    if not template_body:
        raise HTTPException(status_code=400, detail="No template body provided")

    # Render body
    rendered_body = _render_string(template_body, request.variables)
    rendered_subject = _render_string(subject, request.variables) if subject else None

    # Check for missing variables
    missing = _find_missing_variables(rendered_body)

    return {
        "subject": rendered_subject,
        "body": rendered_body,
        "missing_variables": missing
    }


@router.post("/preview")
async def preview_template(
    template_id: str,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Preview a template with sample data"""
    template = await get_template(template_id, current_user, supabase)

    # Generate sample data
    sample_data = {}
    for var in template.get("variables", []):
        sample_data[var] = _get_sample_value(var)

    rendered_body = _render_string(template.get("body", ""), sample_data)
    rendered_subject = _render_string(template.get("subject"), sample_data) if template.get("subject") else None

    return {
        "subject": rendered_subject,
        "body": rendered_body,
        "sample_data": sample_data
    }


def _extract_variables(text: str) -> List[str]:
    """Extract variable names from template text"""
    if not text:
        return []
    pattern = r'\{\{(\w+)\}\}'
    return list(set(re.findall(pattern, text)))


def _render_string(text: str, variables: dict) -> str:
    """Render template string with variables"""
    if not text:
        return ""
    for key, value in variables.items():
        text = text.replace(f"{{{{{key}}}}}", str(value))
    return text


def _find_missing_variables(text: str) -> List[str]:
    """Find unreplaced variables in rendered text"""
    pattern = r'\{\{(\w+)\}\}'
    return list(set(re.findall(pattern, text)))


def _get_sample_value(variable: str) -> str:
    """Get sample value for a variable"""
    samples = {
        "student_name": "John Smith",
        "parent_name": "Jane Smith",
        "teacher_name": "Mr. Johnson",
        "school_name": "Springfield Elementary",
        "date": "January 15, 2026",
        "time": "9:00 AM",
        "amount": "500.00",
        "currency": "$",
        "score": "85",
        "grade_letter": "B",
        "subject": "Mathematics",
        "term_name": "Fall 2025",
        "gpa": "3.5",
        "attendance_rate": "95",
        "event_name": "Annual Science Fair",
        "event_date": "February 1, 2026",
        "event_time": "2:00 PM",
        "location": "Main Auditorium",
        "fee_type": "Tuition",
        "due_date": "January 31, 2026",
        "arrival_time": "8:45 AM",
        "assessment_name": "Chapter 5 Quiz",
        "user_name": "John Doe",
        "reset_link": "https://example.com/reset/abc123"
    }
    return samples.get(variable, f"[{variable}]")


# ============================================================
# TEMPLATE VARIABLES
# ============================================================

@router.get("/variables")
async def get_available_variables():
    """Get all available template variables with descriptions"""
    return {
        "variables": [
            {"name": "student_name", "description": "Student's full name", "category": "student"},
            {"name": "student_first_name", "description": "Student's first name", "category": "student"},
            {"name": "student_number", "description": "Student ID number", "category": "student"},
            {"name": "parent_name", "description": "Parent's full name", "category": "parent"},
            {"name": "parent_first_name", "description": "Parent's first name", "category": "parent"},
            {"name": "teacher_name", "description": "Teacher's full name", "category": "staff"},
            {"name": "school_name", "description": "School name", "category": "school"},
            {"name": "date", "description": "Formatted date", "category": "general"},
            {"name": "time", "description": "Formatted time", "category": "general"},
            {"name": "amount", "description": "Monetary amount", "category": "financial"},
            {"name": "currency", "description": "Currency symbol", "category": "financial"},
            {"name": "score", "description": "Numeric score/grade", "category": "academic"},
            {"name": "grade_letter", "description": "Letter grade", "category": "academic"},
            {"name": "subject", "description": "Subject name", "category": "academic"},
            {"name": "term_name", "description": "Term/semester name", "category": "academic"},
            {"name": "gpa", "description": "Grade point average", "category": "academic"},
            {"name": "attendance_rate", "description": "Attendance percentage", "category": "attendance"},
            {"name": "event_name", "description": "Event name", "category": "event"},
            {"name": "event_date", "description": "Event date", "category": "event"},
            {"name": "event_time", "description": "Event time", "category": "event"},
            {"name": "location", "description": "Location/venue", "category": "event"},
            {"name": "fee_type", "description": "Type of fee", "category": "financial"},
            {"name": "due_date", "description": "Payment due date", "category": "financial"}
        ]
    }
