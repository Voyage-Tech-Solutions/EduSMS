from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta, time
from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client

router = APIRouter()

@router.get("/schedule/today")
async def get_today_schedule(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    # Mock schedule - would need timetable table
    return [
        {"time": "08:00-09:00", "subject": "Mathematics", "class": "Grade 8A", "room": "101", "status": "upcoming"},
        {"time": "09:15-10:15", "subject": "Mathematics", "class": "Grade 9B", "room": "101", "status": "upcoming"},
        {"time": "10:30-11:30", "subject": "Physics", "class": "Grade 10A", "room": "Lab 2", "status": "upcoming"},
        {"time": "11:45-12:45", "subject": "Mathematics", "class": "Grade 7C", "room": "101", "status": "upcoming"}
    ]

@router.get("/grading/queue")
async def get_grading_queue(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    supabase = get_supabase_client()
    teacher_id = current_user["id"]
    school_id = current_user["school_id"]
    
    # Get classes taught by this teacher
    classes = supabase.table("classes").select("id, name, grade_id").eq("teacher_id", teacher_id).execute()
    
    grading_tasks = []
    for cls in classes.data:
        # Count students in class
        students = supabase.table("students").select("id", count="exact").eq("class_id", cls["id"]).eq("status", "active").execute()
        
        # Count grade entries for this class
        entries = supabase.table("grade_entries").select("id", count="exact").eq("school_id", school_id).in_("student_id", [s["id"] for s in students.data] if students.data else []).gte("created_at", (datetime.now() - timedelta(days=7)).isoformat()).execute()
        
        pending = (students.count or 0) - (entries.count or 0)
        if pending > 0:
            grading_tasks.append({
                "type": "Assessment",
                "class": cls["name"],
                "task": "Recent submissions",
                "pending": pending
            })
    
    return grading_tasks

@router.get("/classes/snapshot")
async def get_classes_snapshot(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    supabase = get_supabase_client()
    teacher_id = current_user["id"]
    school_id = current_user["school_id"]
    
    classes = supabase.table("classes").select("id, name").eq("teacher_id", teacher_id).execute()
    
    class_data = []
    for cls in classes.data:
        # Student count
        students = supabase.table("students").select("id", count="exact").eq("class_id", cls["id"]).eq("status", "active").execute()
        student_count = students.count or 0
        
        # Attendance average (last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
        if students.data:
            attendance = supabase.table("attendance_records").select("status").in_("student_id", [s["id"] for s in students.data]).gte("date", thirty_days_ago).execute()
            present = sum(1 for r in attendance.data if r["status"] in ["present", "late"])
            attendance_avg = round((present / len(attendance.data) * 100), 1) if attendance.data else 0
        else:
            attendance_avg = 0
        
        # Class average (grades)
        if students.data:
            grades = supabase.table("grade_entries").select("score, max_score").in_("student_id", [s["id"] for s in students.data]).execute()
            if grades.data:
                avg_score = sum(float(g["score"]) / float(g["max_score"]) * 100 for g in grades.data) / len(grades.data)
                class_avg = round(avg_score, 1)
            else:
                class_avg = 0
        else:
            class_avg = 0
        
        class_data.append({
            "class": cls["name"],
            "students": student_count,
            "attendance_avg": attendance_avg,
            "class_avg": class_avg,
            "coverage": "On Track"  # Mock - would need syllabus tracking
        })
    
    return class_data

@router.get("/attention/items")
async def get_attention_items(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    supabase = get_supabase_client()
    teacher_id = current_user["id"]
    school_id = current_user["school_id"]
    
    items = []
    
    # Get teacher's classes
    classes = supabase.table("classes").select("id, name").eq("teacher_id", teacher_id).execute()
    
    for cls in classes.data:
        # Students in this class
        students = supabase.table("students").select("id, first_name, last_name").eq("class_id", cls["id"]).eq("status", "active").execute()
        
        if students.data:
            # Chronic absentees
            thirty_days_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
            for student in students.data:
                absences = supabase.table("attendance_records").select("id", count="exact").eq("student_id", student["id"]).eq("status", "absent").gte("date", thirty_days_ago).execute()
                if (absences.count or 0) >= 3:
                    items.append(f"{student['first_name']} {student['last_name']} absent 3+ days ({cls['name']})")
    
    # Mock additional items
    items.append("Mark submission deadline in 2 days")
    
    return items[:10]

@router.get("/planning/status")
async def get_planning_status(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Teacher access required")
    
    supabase = get_supabase_client()
    teacher_id = current_user["id"]
    
    classes = supabase.table("classes").select("id, name").eq("teacher_id", teacher_id).execute()
    
    # Mock planning data - would need lesson_plans table
    return [
        {"class": cls["name"], "term_plan": "Submitted", "coverage": "Week 6/10", "next_topic": "Topic " + str(idx+1)}
        for idx, cls in enumerate(classes.data)
    ]
