from fastapi import APIRouter, Depends
from typing import List
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.db.supabase import get_supabase_admin

router = APIRouter()

# Models
class AttendanceRecord(BaseModel):
    student_id: str
    status: str

class SaveAttendanceRequest(BaseModel):
    class_id: str
    date: str
    records: List[AttendanceRecord]

# Dashboard
@router.get("/dashboard")
async def get_teacher_dashboard(supabase = Depends(get_supabase_admin)):
    """Teacher control center"""
    
    return {
        "next_class": {
            "time": "10:00 AM",
            "subject": "Mathematics",
            "class": "Grade 1A",
            "room": "R101",
            "class_id": "40404040-4040-4040-4040-404040404040"
        },
        "grading": {
            "submissions_waiting": 5,
            "overdue": 2,
            "unmarked": 3
        },
        "alerts": [],
        "schedule": [],
        "classes": []
    }

# Classes
@router.get("/classes")
async def get_teacher_classes(supabase = Depends(get_supabase_admin)):
    """Get teacher's assigned classes"""
    
    classes = supabase.table("classes").select("id, name, capacity").execute()
    return classes.data

@router.get("/classes/{class_id}/students")
async def get_class_students(class_id: str, supabase = Depends(get_supabase_admin)):
    """Get students in a class"""
    
    students = supabase.table("students").select("id, admission_number, first_name, last_name").eq("class_id", class_id).execute()
    return students.data

# Attendance
@router.post("/attendance/save")
async def save_attendance(request: SaveAttendanceRequest, supabase = Depends(get_supabase_admin)):
    """Save attendance records"""
    
    # Create session
    session = supabase.table("attendance_sessions").insert({
        "class_id": request.class_id,
        "date": request.date
    }).execute()
    
    session_id = session.data[0]["id"]
    
    # Create records
    records = [{
        "session_id": session_id,
        "student_id": record.student_id,
        "date": request.date,
        "status": record.status
    } for record in request.records]
    
    result = supabase.table("attendance_records").insert(records).execute()
    
    return {"message": "Attendance saved", "count": len(result.data)}

# Gradebook
@router.get("/gradebook")
async def get_gradebook(class_id: str, subject_id: str, supabase = Depends(get_supabase_admin)):
    """Get gradebook data"""
    
    assessments = supabase.table("assessments").select("*, assessment_scores(*)").eq("class_id", class_id).eq("subject_id", subject_id).execute()
    
    return assessments.data

# Assignments
@router.get("/assignments")
async def get_assignments(supabase = Depends(get_supabase_admin)):
    """Get teacher's assignments"""
    
    assignments = supabase.table("assignments").select("*, assignment_submissions(*)").execute()
    
    return assignments.data

@router.post("/assignments")
async def create_assignment(title: str, class_id: str, due_date: str, supabase = Depends(get_supabase_admin)):
    """Create new assignment"""
    
    result = supabase.table("assignments").insert({
        "title": title,
        "class_id": class_id,
        "due_date": due_date,
        "status": "active"
    }).execute()
    
    return {"message": "Assignment created", "data": result.data}
