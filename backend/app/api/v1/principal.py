from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client

router = APIRouter()

@router.get("/dashboard/metrics")
async def get_dashboard_metrics(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")
    
    supabase = get_supabase_client()
    school_id = current_user["school_id"]
    
    # Total students
    students = supabase.table("students").select("id, status", count="exact").eq("school_id", school_id).eq("status", "active").execute()
    total_students = students.count
    
    # Attendance rate (last 30 days)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
    attendance = supabase.table("attendance_records").select("status").eq("school_id", school_id).gte("date", thirty_days_ago).execute()
    present_count = sum(1 for r in attendance.data if r["status"] in ["present", "late"])
    attendance_rate = round((present_count / len(attendance.data) * 100), 1) if attendance.data else 0
    
    # Students at risk (chronic absentees + discipline issues)
    chronic_absentees = supabase.rpc("get_chronic_absentees", {"p_school_id": school_id, "p_start_date": thirty_days_ago, "p_threshold": 5}).execute()
    discipline_students = supabase.table("discipline_incidents").select("student_id").eq("school_id", school_id).gte("incident_date", thirty_days_ago).execute()
    at_risk_count = len(set([r["student_id"] for r in chronic_absentees.data] + [r["student_id"] for r in discipline_students.data]))
    
    # Fee collection
    invoices = supabase.table("invoices").select("amount, amount_paid").eq("school_id", school_id).execute()
    total_expected = sum(float(i["amount"]) for i in invoices.data)
    total_collected = sum(float(i["amount_paid"]) for i in invoices.data)
    collection_rate = round((total_collected / total_expected * 100), 1) if total_expected > 0 else 0
    outstanding = total_expected - total_collected
    
    return {
        "total_students": total_students,
        "attendance_rate": attendance_rate,
        "at_risk_count": at_risk_count,
        "collection_rate": collection_rate,
        "outstanding_balance": round(outstanding, 2)
    }

@router.get("/alerts")
async def get_school_alerts(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")
    
    supabase = get_supabase_client()
    school_id = current_user["school_id"]
    alerts = []
    
    # Low attendance by grade
    grades = supabase.table("grades").select("id, name").eq("school_id", school_id).execute()
    for grade in grades.data:
        students_in_grade = supabase.table("students").select("id").eq("grade_id", grade["id"]).eq("status", "active").execute()
        if not students_in_grade.data:
            continue
        
        thirty_days_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
        attendance = supabase.table("attendance_records").select("status").in_("student_id", [s["id"] for s in students_in_grade.data]).gte("date", thirty_days_ago).execute()
        present = sum(1 for r in attendance.data if r["status"] in ["present", "late"])
        rate = (present / len(attendance.data) * 100) if attendance.data else 0
        
        if rate < 90:
            alerts.append({"severity": "high", "message": f"Attendance below threshold in {grade['name']} ({rate:.1f}%)"})
    
    # At-risk students
    chronic_absentees = supabase.rpc("get_chronic_absentees", {"p_school_id": school_id, "p_start_date": (datetime.now() - timedelta(days=30)).date().isoformat(), "p_threshold": 5}).execute()
    if len(chronic_absentees.data) > 0:
        alerts.append({"severity": "high", "message": f"{len(chronic_absentees.data)} students flagged 'At Risk'"})
    
    # Fee collection
    invoices = supabase.table("invoices").select("amount, amount_paid").eq("school_id", school_id).execute()
    total_expected = sum(float(i["amount"]) for i in invoices.data)
    total_collected = sum(float(i["amount_paid"]) for i in invoices.data)
    rate = (total_collected / total_expected * 100) if total_expected > 0 else 100
    if rate < 85:
        alerts.append({"severity": "medium", "message": f"Fee collection below target ({rate:.1f}%)"})
    
    # Teachers not submitting marks
    teachers = supabase.table("user_profiles").select("id, first_name, last_name").eq("school_id", school_id).eq("role", "teacher").execute()
    teachers_with_entries = supabase.table("grade_entries").select("entered_by").eq("school_id", school_id).gte("created_at", (datetime.now() - timedelta(days=30)).isoformat()).execute()
    submitted_teachers = set(e["entered_by"] for e in teachers_with_entries.data if e["entered_by"])
    not_submitted = len([t for t in teachers.data if t["id"] not in submitted_teachers])
    if not_submitted > 0:
        alerts.append({"severity": "low", "message": f"{not_submitted} teachers haven't submitted marks"})
    
    return alerts[:10]

@router.get("/approvals")
async def get_pending_approvals(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")
    
    # Mock approval data - would need approval tables in real implementation
    return [
        {"type": "Fee Discounts", "count": 6, "priority": "high"},
        {"type": "Late Mark Changes", "count": 4, "priority": "medium"},
        {"type": "Student Transfers", "count": 2, "priority": "high"},
        {"type": "Disciplinary Cases", "count": 3, "priority": "high"}
    ]

@router.get("/academic/performance")
async def get_academic_performance(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")
    
    supabase = get_supabase_client()
    school_id = current_user["school_id"]
    
    # Pass rate calculation
    grade_entries = supabase.table("grade_entries").select("score, max_score").eq("school_id", school_id).execute()
    passing_grades = sum(1 for e in grade_entries.data if (float(e["score"]) / float(e["max_score"]) * 100) >= 50)
    pass_rate = round((passing_grades / len(grade_entries.data) * 100), 1) if grade_entries.data else 0
    
    # Assessment completion
    students = supabase.table("students").select("id").eq("school_id", school_id).eq("status", "active").execute()
    subjects = supabase.table("subjects").select("id").eq("school_id", school_id).execute()
    expected_entries = len(students.data) * len(subjects.data)
    actual_entries = len(grade_entries.data)
    completion_rate = round((actual_entries / expected_entries * 100), 1) if expected_entries > 0 else 0
    
    # Reports submitted
    teachers = supabase.table("user_profiles").select("id").eq("school_id", school_id).eq("role", "teacher").execute()
    teachers_with_entries = supabase.table("grade_entries").select("entered_by").eq("school_id", school_id).gte("created_at", (datetime.now() - timedelta(days=30)).isoformat()).execute()
    submitted = len(set(e["entered_by"] for e in teachers_with_entries.data if e["entered_by"]))
    
    return {
        "pass_rate": pass_rate,
        "completion_rate": completion_rate,
        "reports_submitted": submitted,
        "total_teachers": len(teachers.data)
    }

@router.get("/finance/overview")
async def get_finance_overview(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")
    
    supabase = get_supabase_client()
    school_id = current_user["school_id"]
    
    invoices = supabase.table("invoices").select("amount, amount_paid, due_date").eq("school_id", school_id).execute()
    
    total_expected = sum(float(i["amount"]) for i in invoices.data)
    total_collected = sum(float(i["amount_paid"]) for i in invoices.data)
    collection_rate = round((total_collected / total_expected * 100), 1) if total_expected > 0 else 0
    outstanding = total_expected - total_collected
    
    # Overdue calculation
    today = datetime.now().date()
    overdue = sum(float(i["amount"]) - float(i["amount_paid"]) for i in invoices.data if datetime.fromisoformat(i["due_date"].replace('Z', '+00:00')).date() < today and float(i["amount_paid"]) < float(i["amount"]))
    
    return {
        "collection_rate": collection_rate,
        "outstanding_balance": round(outstanding, 2),
        "overdue_amount": round(overdue, 2),
        "total_collected": round(total_collected, 2)
    }

@router.get("/staff/insight")
async def get_staff_insight(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")
    
    supabase = get_supabase_client()
    school_id = current_user["school_id"]
    
    teachers = supabase.table("user_profiles").select("id").eq("school_id", school_id).eq("role", "teacher").eq("is_active", True).execute()
    
    # Marking completion
    teachers_with_entries = supabase.table("grade_entries").select("entered_by").eq("school_id", school_id).gte("created_at", (datetime.now() - timedelta(days=30)).isoformat()).execute()
    submitted = len(set(e["entered_by"] for e in teachers_with_entries.data if e["entered_by"]))
    marking_complete = round((submitted / len(teachers.data) * 100), 1) if teachers.data else 0
    
    # Late submissions (teachers who haven't submitted in 30 days)
    late_submissions = len(teachers.data) - submitted
    
    return {
        "active_teachers": len(teachers.data),
        "marking_complete": marking_complete,
        "staff_absent": 0,  # Would need attendance tracking for staff
        "late_submissions": late_submissions
    }

@router.get("/activity/recent")
async def get_recent_activity(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")
    
    supabase = get_supabase_client()
    school_id = current_user["school_id"]
    
    # Get recent audit logs
    logs = supabase.table("audit_logs").select("action, entity_type, created_at").eq("school_id", school_id).order("created_at", desc=True).limit(20).execute()
    
    activities = []
    for log in logs.data:
        if "payment" in log["action"].lower() and "large" in log["action"].lower():
            activities.append({"action": log["action"], "time": log["created_at"]})
        elif "report" in log["action"].lower():
            activities.append({"action": log["action"], "time": log["created_at"]})
        elif "discipline" in log["entity_type"].lower():
            activities.append({"action": f"Disciplinary case {log['action']}", "time": log["created_at"]})
    
    return activities[:10]


@router.get("/academic/full-report")
async def get_academic_full_report(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")

    supabase = get_supabase_client()
    school_id = current_user["school_id"]

    # Fetch all grade entries for this school
    grade_entries = supabase.table("grade_entries").select(
        "id, student_id, subject_id, score, max_score, entered_by, assessment_type, created_at"
    ).eq("school_id", school_id).execute()

    # Fetch students with grade info
    students = supabase.table("students").select(
        "id, first_name, last_name, grade_id, class_id"
    ).eq("school_id", school_id).eq("status", "active").execute()
    student_map = {s["id"]: s for s in students.data}

    # Fetch grades (grade levels)
    grades = supabase.table("grades").select("id, name, order").eq("school_id", school_id).order("order").execute()
    grade_map = {g["id"]: g["name"] for g in grades.data}

    # Fetch subjects
    subjects = supabase.table("subjects").select("id, name").eq("school_id", school_id).execute()
    subject_map = {s["id"]: s["name"] for s in subjects.data}

    # Fetch teachers
    teachers = supabase.table("user_profiles").select(
        "id, first_name, last_name"
    ).eq("school_id", school_id).eq("role", "teacher").execute()
    teacher_map = {t["id"]: f"{t['first_name']} {t['last_name']}" for t in teachers.data}

    # --- School-wide pass rate ---
    total_entries = len(grade_entries.data)
    passing = sum(1 for e in grade_entries.data if float(e["score"]) / float(e["max_score"]) * 100 >= 50)
    school_pass_rate = round((passing / total_entries * 100), 1) if total_entries > 0 else 0

    # --- Per-grade performance ---
    grade_stats = {}
    for entry in grade_entries.data:
        student = student_map.get(entry["student_id"])
        if not student:
            continue
        gid = student.get("grade_id")
        if not gid:
            continue
        if gid not in grade_stats:
            grade_stats[gid] = {"scores": [], "student_ids": set()}
        pct = float(entry["score"]) / float(entry["max_score"]) * 100
        grade_stats[gid]["scores"].append(pct)
        grade_stats[gid]["student_ids"].add(entry["student_id"])

    grade_performance = []
    for gid in [g["id"] for g in grades.data]:
        stats = grade_stats.get(gid)
        if not stats:
            grade_performance.append({
                "grade": grade_map.get(gid, "Unknown"),
                "grade_id": gid,
                "pass_rate": 0,
                "average_score": 0,
                "student_count": 0,
                "entries_count": 0,
            })
            continue
        scores = stats["scores"]
        pass_count = sum(1 for s in scores if s >= 50)
        grade_performance.append({
            "grade": grade_map.get(gid, "Unknown"),
            "grade_id": gid,
            "pass_rate": round((pass_count / len(scores) * 100), 1),
            "average_score": round(sum(scores) / len(scores), 1),
            "student_count": len(stats["student_ids"]),
            "entries_count": len(scores),
        })

    # --- Per-subject performance (ranked by avg score) ---
    subject_stats = {}
    for entry in grade_entries.data:
        sid = entry["subject_id"]
        if sid not in subject_stats:
            subject_stats[sid] = []
        pct = float(entry["score"]) / float(entry["max_score"]) * 100
        subject_stats[sid].append(pct)

    subject_performance = []
    for sid, scores in subject_stats.items():
        pass_count = sum(1 for s in scores if s >= 50)
        subject_performance.append({
            "subject": subject_map.get(sid, "Unknown"),
            "subject_id": sid,
            "average_score": round(sum(scores) / len(scores), 1),
            "pass_rate": round((pass_count / len(scores) * 100), 1),
            "entries_count": len(scores),
        })
    subject_performance.sort(key=lambda x: x["average_score"], reverse=True)

    # --- Per-teacher performance ---
    teacher_stats = {}
    for entry in grade_entries.data:
        tid = entry.get("entered_by")
        if not tid:
            continue
        if tid not in teacher_stats:
            teacher_stats[tid] = {"scores": [], "subject_ids": set()}
        pct = float(entry["score"]) / float(entry["max_score"]) * 100
        teacher_stats[tid]["scores"].append(pct)
        teacher_stats[tid]["subject_ids"].add(entry["subject_id"])

    teacher_performance = []
    for tid, stats in teacher_stats.items():
        scores = stats["scores"]
        subjects_taught = [subject_map.get(sid, "Unknown") for sid in stats["subject_ids"]]
        teacher_performance.append({
            "teacher": teacher_map.get(tid, "Unknown"),
            "teacher_id": tid,
            "average_student_score": round(sum(scores) / len(scores), 1),
            "entries_graded": len(scores),
            "subjects": subjects_taught,
        })
    teacher_performance.sort(key=lambda x: x["average_student_score"], reverse=True)

    # --- Assessment completion by teacher ---
    thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
    recent_entries = supabase.table("grade_entries").select("entered_by").eq("school_id", school_id).gte("created_at", thirty_days_ago).execute()
    submitted_teacher_ids = set(e["entered_by"] for e in recent_entries.data if e.get("entered_by"))

    teacher_completion = []
    for t in teachers.data:
        has_submitted = t["id"] in submitted_teacher_ids
        teacher_completion.append({
            "teacher": f"{t['first_name']} {t['last_name']}",
            "teacher_id": t["id"],
            "has_submitted": has_submitted,
        })
    teacher_completion.sort(key=lambda x: (not x["has_submitted"], x["teacher"]))

    return {
        "school_pass_rate": school_pass_rate,
        "total_entries": total_entries,
        "total_students": len(students.data),
        "total_subjects": len(subjects.data),
        "total_teachers": len(teachers.data),
        "grade_performance": grade_performance,
        "subject_performance": subject_performance,
        "teacher_performance": teacher_performance,
        "teacher_completion": teacher_completion,
    }


@router.get("/finance/arrears")
async def get_finance_arrears(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")

    supabase = get_supabase_client()
    school_id = current_user["school_id"]

    # Fetch all invoices with outstanding balances
    invoices = supabase.table("invoices").select(
        "id, student_id, amount, amount_paid, due_date, description, status"
    ).eq("school_id", school_id).execute()

    # Fetch students
    students = supabase.table("students").select(
        "id, first_name, last_name, grade_id, class_id"
    ).eq("school_id", school_id).eq("status", "active").execute()
    student_map = {s["id"]: s for s in students.data}

    # Fetch grades and classes
    grades = supabase.table("grades").select("id, name").eq("school_id", school_id).execute()
    grade_map = {g["id"]: g["name"] for g in grades.data}

    classes = supabase.table("classes").select("id, name").eq("school_id", school_id).execute()
    class_map = {c["id"]: c["name"] for c in classes.data}

    today = datetime.now().date()

    # Collection summary
    total_expected = sum(float(i["amount"]) for i in invoices.data)
    total_collected = sum(float(i["amount_paid"]) for i in invoices.data)
    total_outstanding = total_expected - total_collected
    collection_rate = round((total_collected / total_expected * 100), 1) if total_expected > 0 else 0

    # Build student arrears list and aging buckets
    student_arrears = []
    grade_arrears = {}
    aging_30 = 0
    aging_60 = 0
    aging_90 = 0
    total_overdue = 0

    for inv in invoices.data:
        outstanding = float(inv["amount"]) - float(inv["amount_paid"])
        if outstanding <= 0:
            continue

        student = student_map.get(inv["student_id"])
        if not student:
            continue

        # Parse due date
        due_str = inv["due_date"]
        try:
            if 'T' in str(due_str):
                due_date = datetime.fromisoformat(due_str.replace('Z', '+00:00')).date()
            else:
                due_date = datetime.strptime(str(due_str), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue

        days_overdue = (today - due_date).days
        is_overdue = days_overdue > 0

        if is_overdue:
            total_overdue += outstanding
            if days_overdue >= 90:
                aging_90 += outstanding
            elif days_overdue >= 60:
                aging_60 += outstanding
            elif days_overdue >= 30:
                aging_30 += outstanding

        grade_name = grade_map.get(student.get("grade_id"), "Unassigned")
        class_name = class_map.get(student.get("class_id"), "Unassigned")

        student_arrears.append({
            "student_name": f"{student['first_name']} {student['last_name']}",
            "student_id": inv["student_id"],
            "grade": grade_name,
            "class": class_name,
            "description": inv.get("description", "Fee"),
            "amount_owed": round(outstanding, 2),
            "due_date": inv["due_date"],
            "days_overdue": max(days_overdue, 0),
            "status": inv["status"],
        })

        # Aggregate by grade
        if grade_name not in grade_arrears:
            grade_arrears[grade_name] = {"outstanding": 0, "student_count": set()}
        grade_arrears[grade_name]["outstanding"] += outstanding
        grade_arrears[grade_name]["student_count"].add(inv["student_id"])

    # Sort by days overdue descending
    student_arrears.sort(key=lambda x: x["days_overdue"], reverse=True)

    # Format grade arrears
    grade_arrears_list = []
    for grade_name, data in sorted(grade_arrears.items()):
        grade_arrears_list.append({
            "grade": grade_name,
            "outstanding": round(data["outstanding"], 2),
            "student_count": len(data["student_count"]),
        })

    return {
        "summary": {
            "total_expected": round(total_expected, 2),
            "total_collected": round(total_collected, 2),
            "total_outstanding": round(total_outstanding, 2),
            "total_overdue": round(total_overdue, 2),
            "collection_rate": collection_rate,
        },
        "aging": {
            "days_30": round(aging_30, 2),
            "days_60": round(aging_60, 2),
            "days_90_plus": round(aging_90, 2),
        },
        "grade_arrears": grade_arrears_list,
        "student_arrears": student_arrears,
    }


# ==================== STAFF MANAGEMENT ====================

@router.get("/staff")
async def get_staff_list(role: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ("principal", "system_admin"):
        raise HTTPException(status_code=403, detail="Principal access required")

    supabase = get_supabase_client()
    school_id = current_user["school_id"]

    query = supabase.table("user_profiles").select(
        "id, email, first_name, last_name, phone, role, is_active, created_at"
    ).eq("school_id", school_id).in_("role", ["principal", "teacher", "office_admin"])

    if role and role != "all":
        query = query.eq("role", role)

    result = query.order("created_at", desc=True).execute()

    staff = []
    for s in result.data:
        staff.append({
            "id": s["id"],
            "email": s.get("email", ""),
            "first_name": s.get("first_name", ""),
            "last_name": s.get("last_name", ""),
            "full_name": f"{s.get('first_name', '')} {s.get('last_name', '')}".strip(),
            "phone": s.get("phone", ""),
            "role": s["role"],
            "is_active": s.get("is_active", True),
            "created_at": s.get("created_at"),
        })

    return staff


@router.post("/staff")
async def create_staff(staff_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ("principal", "system_admin"):
        raise HTTPException(status_code=403, detail="Principal access required")

    supabase = get_supabase_client()
    school_id = current_user["school_id"]

    email = staff_data.get("email")
    password = staff_data.get("password", "Welcome123!")
    role = staff_data.get("role", "teacher")
    first_name = staff_data.get("first_name", "")
    last_name = staff_data.get("last_name", "")
    phone = staff_data.get("phone", "")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    if role not in ("teacher", "office_admin", "principal"):
        raise HTTPException(status_code=400, detail="Invalid staff role")

    # Create auth user via Supabase admin
    from app.db.supabase_client import get_supabase_admin
    admin = get_supabase_admin()

    try:
        auth_result = admin.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
        })
        user_id = auth_result.user.id
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create user account: {str(e)}")

    # Create user profile
    try:
        profile = supabase.table("user_profiles").insert({
            "id": user_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "role": role,
            "school_id": school_id,
            "is_active": True,
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create profile: {str(e)}")

    return {
        "id": user_id,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
        "role": role,
        "is_active": True,
    }


@router.patch("/staff/{user_id}")
async def update_staff(user_id: str, staff_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ("principal", "system_admin"):
        raise HTTPException(status_code=403, detail="Principal access required")

    supabase = get_supabase_client()
    school_id = current_user["school_id"]

    # Verify staff belongs to this school
    existing = supabase.table("user_profiles").select("id").eq("id", user_id).eq("school_id", school_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Staff member not found")

    update_fields = {}
    for field in ["first_name", "last_name", "phone", "role"]:
        if field in staff_data:
            update_fields[field] = staff_data[field]

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = supabase.table("user_profiles").update(update_fields).eq("id", user_id).execute()
    return {"status": "updated", "id": user_id}


@router.post("/staff/{user_id}/deactivate")
async def deactivate_staff(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ("principal", "system_admin"):
        raise HTTPException(status_code=403, detail="Principal access required")

    supabase = get_supabase_client()
    school_id = current_user["school_id"]

    existing = supabase.table("user_profiles").select("id, is_active").eq("id", user_id).eq("school_id", school_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Staff member not found")

    new_status = not existing.data[0].get("is_active", True)
    supabase.table("user_profiles").update({"is_active": new_status}).eq("id", user_id).execute()
    return {"status": "active" if new_status else "deactivated", "is_active": new_status}


# ==================== REPORTS OVERVIEW ====================

@router.get("/reports/overview")
async def get_reports_overview(period: str = "month", current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ("principal", "system_admin"):
        raise HTTPException(status_code=403, detail="Principal access required")

    supabase = get_supabase_client()
    school_id = current_user["school_id"]

    # Calculate date range
    now = datetime.now()
    if period == "week":
        start_date = (now - timedelta(days=7)).date().isoformat()
    elif period == "term":
        start_date = (now - timedelta(days=90)).date().isoformat()
    elif period == "year":
        start_date = (now - timedelta(days=365)).date().isoformat()
    else:
        start_date = (now - timedelta(days=30)).date().isoformat()

    # Total students
    students = supabase.table("students").select("id", count="exact").eq("school_id", school_id).eq("status", "active").execute()
    total_students = students.count

    # Avg attendance
    attendance = supabase.table("attendance_records").select("status").eq("school_id", school_id).gte("date", start_date).execute()
    present_count = sum(1 for r in attendance.data if r["status"] in ["present", "late"])
    avg_attendance = round((present_count / len(attendance.data) * 100), 1) if attendance.data else 0

    # Fee collection
    invoices = supabase.table("invoices").select("amount, amount_paid").eq("school_id", school_id).execute()
    total_expected = sum(float(i["amount"]) for i in invoices.data)
    total_collected = sum(float(i["amount_paid"]) for i in invoices.data)
    collection_rate = round((total_collected / total_expected * 100), 1) if total_expected > 0 else 0

    # Academic avg
    grade_entries = supabase.table("grade_entries").select("score, max_score").eq("school_id", school_id).gte("created_at", start_date).execute()
    if grade_entries.data:
        academic_avg = round(sum(float(e["score"]) / float(e["max_score"]) * 100 for e in grade_entries.data) / len(grade_entries.data), 1)
    else:
        academic_avg = 0

    return {
        "total_students": total_students,
        "avg_attendance": avg_attendance,
        "total_collected": round(total_collected, 2),
        "collection_rate": collection_rate,
        "academic_avg": academic_avg,
    }


# ==================== APPROVALS (DYNAMIC) ====================

@router.get("/approvals/dynamic")
async def get_dynamic_approvals(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "principal":
        raise HTTPException(status_code=403, detail="Principal access required")

    supabase = get_supabase_client()
    school_id = current_user["school_id"]

    approvals = []

    # Overdue invoices that may need discount approval
    overdue_invoices = supabase.table("invoices").select("id").eq("school_id", school_id).eq("status", "overdue").execute()
    if overdue_invoices.data:
        approvals.append({"type": "Fee Adjustments", "count": len(overdue_invoices.data), "priority": "high"})

    # Students pending transfer
    transfer_students = supabase.table("students").select("id").eq("school_id", school_id).eq("status", "transferred").execute()
    if transfer_students.data:
        approvals.append({"type": "Student Transfers", "count": len(transfer_students.data), "priority": "high"})

    # Teachers without grade submissions in 30 days
    thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
    teachers = supabase.table("user_profiles").select("id").eq("school_id", school_id).eq("role", "teacher").eq("is_active", True).execute()
    entries = supabase.table("grade_entries").select("entered_by").eq("school_id", school_id).gte("created_at", thirty_days_ago).execute()
    submitted = set(e["entered_by"] for e in entries.data if e.get("entered_by"))
    late_count = len([t for t in teachers.data if t["id"] not in submitted])
    if late_count > 0:
        approvals.append({"type": "Late Mark Submissions", "count": late_count, "priority": "medium"})

    # Inactive students that may need review
    inactive = supabase.table("students").select("id").eq("school_id", school_id).eq("status", "inactive").execute()
    if inactive.data:
        approvals.append({"type": "Inactive Student Reviews", "count": len(inactive.data), "priority": "low"})

    return approvals
