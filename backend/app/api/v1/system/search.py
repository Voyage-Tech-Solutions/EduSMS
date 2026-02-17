"""
EduCore Backend - Advanced Search API
Global search across all entities
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


class SearchResult(BaseModel):
    """Search result item"""
    id: str
    type: str  # student, teacher, class, etc.
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    score: float = 1.0
    metadata: Optional[dict] = None


# ============================================================
# GLOBAL SEARCH
# ============================================================

@router.get("")
async def global_search(
    q: str = Query(..., min_length=2, description="Search query"),
    types: Optional[str] = None,  # comma-separated: students,teachers,classes
    limit: int = Query(default=20, le=100),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Global search across all entities"""
    school_id = current_user.get("school_id")
    user_role = current_user.get("role")

    search_types = types.split(",") if types else ["students", "teachers", "classes", "users"]
    results = []

    # Search students
    if "students" in search_types:
        student_results = await _search_students(q, school_id, limit, supabase)
        results.extend(student_results)

    # Search teachers
    if "teachers" in search_types:
        teacher_results = await _search_teachers(q, school_id, limit, supabase)
        results.extend(teacher_results)

    # Search classes
    if "classes" in search_types:
        class_results = await _search_classes(q, school_id, limit, supabase)
        results.extend(class_results)

    # Search users (admin only)
    if "users" in search_types and user_role in ["system_admin", "principal", "office_admin"]:
        user_results = await _search_users(q, school_id, limit, supabase)
        results.extend(user_results)

    # Sort by relevance (simple scoring)
    results.sort(key=lambda x: x.get("score", 0), reverse=True)

    return {
        "query": q,
        "results": results[:limit],
        "total": len(results)
    }


async def _search_students(query: str, school_id: str, limit: int, supabase):
    """Search students"""
    results = []

    # Search by name, student number, email
    search_query = supabase.table("students").select(
        "id, student_number, first_name, last_name, email, status, grades(name), classes(name)"
    ).eq("school_id", school_id).or_(
        f"first_name.ilike.%{query}%,last_name.ilike.%{query}%,student_number.ilike.%{query}%,email.ilike.%{query}%"
    ).limit(limit)

    result = search_query.execute()

    for s in (result.data or []):
        name = f"{s['first_name']} {s['last_name']}"
        grade = s["grades"]["name"] if s.get("grades") else ""
        cls = s["classes"]["name"] if s.get("classes") else ""

        # Calculate relevance score
        score = _calculate_relevance(query.lower(), [
            name.lower(),
            s.get("student_number", "").lower(),
            s.get("email", "").lower()
        ])

        results.append({
            "id": s["id"],
            "type": "student",
            "title": name,
            "subtitle": f"#{s.get('student_number', '')} • {grade} • {cls}",
            "description": s.get("email"),
            "url": f"/students/{s['id']}",
            "score": score,
            "metadata": {"status": s.get("status")}
        })

    return results


async def _search_teachers(query: str, school_id: str, limit: int, supabase):
    """Search teachers"""
    results = []

    search_query = supabase.table("teachers").select(
        "id, employee_id, first_name, last_name, email, position, is_active"
    ).eq("school_id", school_id).or_(
        f"first_name.ilike.%{query}%,last_name.ilike.%{query}%,employee_id.ilike.%{query}%,email.ilike.%{query}%"
    ).limit(limit)

    result = search_query.execute()

    for t in (result.data or []):
        name = f"{t['first_name']} {t['last_name']}"

        score = _calculate_relevance(query.lower(), [
            name.lower(),
            t.get("employee_id", "").lower(),
            t.get("email", "").lower()
        ])

        results.append({
            "id": t["id"],
            "type": "teacher",
            "title": name,
            "subtitle": f"{t.get('position', 'Teacher')} • {t.get('employee_id', '')}",
            "description": t.get("email"),
            "url": f"/teachers/{t['id']}",
            "score": score,
            "metadata": {"is_active": t.get("is_active")}
        })

    return results


async def _search_classes(query: str, school_id: str, limit: int, supabase):
    """Search classes"""
    results = []

    search_query = supabase.table("classes").select(
        "id, name, section, grades(name), class_teacher:teacher_id(first_name, last_name)"
    ).eq("school_id", school_id).or_(
        f"name.ilike.%{query}%,section.ilike.%{query}%"
    ).limit(limit)

    result = search_query.execute()

    for c in (result.data or []):
        grade = c["grades"]["name"] if c.get("grades") else ""
        teacher = ""
        if c.get("class_teacher"):
            teacher = f"{c['class_teacher']['first_name']} {c['class_teacher']['last_name']}"

        score = _calculate_relevance(query.lower(), [
            c.get("name", "").lower(),
            c.get("section", "").lower()
        ])

        results.append({
            "id": c["id"],
            "type": "class",
            "title": f"{c['name']} {c.get('section', '')}",
            "subtitle": f"{grade} • Teacher: {teacher}" if teacher else grade,
            "url": f"/classes/{c['id']}",
            "score": score
        })

    return results


async def _search_users(query: str, school_id: str, limit: int, supabase):
    """Search users"""
    results = []

    search_query = supabase.table("user_profiles").select(
        "id, first_name, last_name, email, role"
    ).eq("school_id", school_id).or_(
        f"first_name.ilike.%{query}%,last_name.ilike.%{query}%,email.ilike.%{query}%"
    ).limit(limit)

    result = search_query.execute()

    for u in (result.data or []):
        name = f"{u['first_name']} {u['last_name']}"

        score = _calculate_relevance(query.lower(), [
            name.lower(),
            u.get("email", "").lower()
        ])

        results.append({
            "id": u["id"],
            "type": "user",
            "title": name,
            "subtitle": u.get("role", "").replace("_", " ").title(),
            "description": u.get("email"),
            "url": f"/users/{u['id']}",
            "score": score
        })

    return results


def _calculate_relevance(query: str, fields: List[str]) -> float:
    """Calculate simple relevance score"""
    score = 0.0

    for field in fields:
        if not field:
            continue
        if query == field:
            score += 10.0  # Exact match
        elif field.startswith(query):
            score += 5.0  # Starts with
        elif query in field:
            score += 2.0  # Contains

    return score


# ============================================================
# QUICK SEARCH
# ============================================================

@router.get("/quick")
async def quick_search(
    q: str = Query(..., min_length=2),
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Quick search returning minimal results for autocomplete"""
    school_id = current_user.get("school_id")

    results = []

    # Quick student search
    students = supabase.table("students").select(
        "id, first_name, last_name, student_number"
    ).eq("school_id", school_id).or_(
        f"first_name.ilike.%{q}%,last_name.ilike.%{q}%,student_number.ilike.%{q}%"
    ).limit(5).execute()

    for s in (students.data or []):
        results.append({
            "id": s["id"],
            "type": "student",
            "label": f"{s['first_name']} {s['last_name']} (#{s.get('student_number', '')})"
        })

    # Quick teacher search
    teachers = supabase.table("teachers").select(
        "id, first_name, last_name"
    ).eq("school_id", school_id).or_(
        f"first_name.ilike.%{q}%,last_name.ilike.%{q}%"
    ).limit(3).execute()

    for t in (teachers.data or []):
        results.append({
            "id": t["id"],
            "type": "teacher",
            "label": f"{t['first_name']} {t['last_name']}"
        })

    return {"results": results}


# ============================================================
# ENTITY-SPECIFIC SEARCH
# ============================================================

@router.get("/students")
async def search_students(
    q: str = Query(..., min_length=2),
    status: Optional[str] = None,
    grade_id: Optional[UUID] = None,
    class_id: Optional[UUID] = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Search students with filters"""
    school_id = current_user.get("school_id")

    query = supabase.table("students").select(
        "*, grades(name), classes(name)"
    ).eq("school_id", school_id).or_(
        f"first_name.ilike.%{q}%,last_name.ilike.%{q}%,student_number.ilike.%{q}%,email.ilike.%{q}%"
    )

    if status:
        query = query.eq("status", status)
    if grade_id:
        query = query.eq("grade_id", str(grade_id))
    if class_id:
        query = query.eq("class_id", str(class_id))

    query = query.order("last_name").range(offset, offset + limit - 1)

    result = query.execute()

    return {
        "results": result.data or [],
        "total": len(result.data) if result.data else 0
    }


@router.get("/teachers")
async def search_teachers(
    q: str = Query(..., min_length=2),
    is_active: Optional[bool] = None,
    subject_id: Optional[UUID] = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Search teachers with filters"""
    school_id = current_user.get("school_id")

    query = supabase.table("teachers").select("*").eq("school_id", school_id).or_(
        f"first_name.ilike.%{q}%,last_name.ilike.%{q}%,employee_id.ilike.%{q}%,email.ilike.%{q}%"
    )

    if is_active is not None:
        query = query.eq("is_active", is_active)

    query = query.order("last_name").range(offset, offset + limit - 1)

    result = query.execute()

    return {"results": result.data or []}


# ============================================================
# RECENT SEARCHES
# ============================================================

@router.get("/recent")
async def get_recent_searches(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get user's recent searches"""
    user_id = current_user.get("id")

    result = supabase.table("search_history").select(
        "query, result_count, searched_at"
    ).eq("user_id", user_id).order("searched_at", desc=True).limit(limit).execute()

    return {"recent_searches": result.data or []}


@router.post("/recent")
async def save_search(
    query: str,
    result_count: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Save a search to history"""
    user_id = current_user.get("id")

    supabase.table("search_history").insert({
        "user_id": user_id,
        "query": query,
        "result_count": result_count,
        "searched_at": datetime.utcnow().isoformat()
    }).execute()

    return {"success": True}


@router.delete("/recent")
async def clear_search_history(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Clear user's search history"""
    user_id = current_user.get("id")

    supabase.table("search_history").delete().eq("user_id", user_id).execute()

    return {"success": True}
