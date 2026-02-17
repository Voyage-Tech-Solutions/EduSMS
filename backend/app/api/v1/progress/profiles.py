"""
EduCore Backend - Student Learning Profiles API
Track learning styles, accommodations, and student-specific needs
"""
import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class LearningStyleAssessment(BaseModel):
    """Learning style assessment results"""
    visual: int = 0  # 0-100
    auditory: int = 0
    kinesthetic: int = 0
    reading_writing: int = 0


class Accommodation(BaseModel):
    """Student accommodation"""
    id: str
    type: str  # seating, timing, materials, assessment, behavior, technology
    description: str
    is_active: bool = True


class LearningGoal(BaseModel):
    """Student learning goal"""
    id: str
    goal: str
    target_date: Optional[str] = None
    status: str = "in_progress"  # in_progress, achieved, modified
    progress_notes: List[str] = []


class ProfileCreate(BaseModel):
    """Create a learning profile"""
    student_id: UUID
    learning_style: Optional[LearningStyleAssessment] = None
    strengths: List[str] = []
    areas_for_growth: List[str] = []
    interests: List[str] = []
    accommodations: List[Accommodation] = []
    learning_goals: List[LearningGoal] = []
    notes: Optional[str] = None
    iep_status: Optional[str] = None  # none, pending, active
    ell_status: Optional[str] = None  # none, level_1, level_2, level_3, level_4, level_5, exited
    gifted_status: Optional[str] = None  # none, identified, served


class ProfileUpdate(BaseModel):
    """Update a learning profile"""
    learning_style: Optional[LearningStyleAssessment] = None
    strengths: Optional[List[str]] = None
    areas_for_growth: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    accommodations: Optional[List[Accommodation]] = None
    learning_goals: Optional[List[LearningGoal]] = None
    notes: Optional[str] = None
    iep_status: Optional[str] = None
    ell_status: Optional[str] = None
    gifted_status: Optional[str] = None


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_profiles(
    class_id: Optional[UUID] = None,
    has_iep: Optional[bool] = None,
    has_ell: Optional[bool] = None,
    has_gifted: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List student learning profiles"""
    school_id = current_user.get("school_id")

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    query = supabase.table("student_learning_profiles").select(
        "*, students(first_name, last_name, student_number, class_id)"
    ).eq("school_id", school_id)

    if has_iep is not None:
        if has_iep:
            query = query.eq("iep_status", "active")
        else:
            query = query.neq("iep_status", "active")

    if has_ell is not None:
        if has_ell:
            query = query.neq("ell_status", "none")
        else:
            query = query.eq("ell_status", "none")

    if has_gifted is not None:
        if has_gifted:
            query = query.neq("gifted_status", "none")
        else:
            query = query.eq("gifted_status", "none")

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    profiles = result.data or []

    # Filter by class if needed
    if class_id:
        profiles = [
            p for p in profiles
            if p.get("students", {}).get("class_id") == str(class_id)
        ]

    # Filter by search
    if search:
        search_lower = search.lower()
        profiles = [
            p for p in profiles
            if search_lower in (p.get("students", {}).get("first_name", "") + " " +
                               p.get("students", {}).get("last_name", "")).lower()
        ]

    return {
        "profiles": profiles,
        "total": len(profiles),
        "limit": limit,
        "offset": offset
    }


@router.get("/student/{student_id}")
async def get_student_profile(
    student_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get learning profile for a specific student"""
    result = supabase.table("student_learning_profiles").select(
        "*, students(first_name, last_name, student_number, date_of_birth, class_id, classes(name))"
    ).eq("student_id", str(student_id)).single().execute()

    if not result.data:
        # Return empty profile structure if none exists
        return {
            "student_id": str(student_id),
            "exists": False,
            "learning_style": None,
            "strengths": [],
            "areas_for_growth": [],
            "interests": [],
            "accommodations": [],
            "learning_goals": [],
            "notes": None,
            "iep_status": "none",
            "ell_status": "none",
            "gifted_status": "none"
        }

    profile = result.data
    profile["exists"] = True

    return profile


@router.post("")
async def create_profile(
    profile: ProfileCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new learning profile"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # Check if profile already exists
    existing = supabase.table("student_learning_profiles").select("id").eq(
        "student_id", str(profile.student_id)
    ).execute()

    if existing.data:
        raise HTTPException(status_code=400, detail="Profile already exists for this student")

    profile_data = {
        "school_id": school_id,
        "student_id": str(profile.student_id),
        "created_by": user_id,
        "learning_style": profile.learning_style.dict() if profile.learning_style else None,
        "strengths": profile.strengths,
        "areas_for_growth": profile.areas_for_growth,
        "interests": profile.interests,
        "accommodations": [a.dict() for a in profile.accommodations],
        "learning_goals": [g.dict() for g in profile.learning_goals],
        "notes": profile.notes,
        "iep_status": profile.iep_status or "none",
        "ell_status": profile.ell_status or "none",
        "gifted_status": profile.gifted_status or "none"
    }

    result = supabase.table("student_learning_profiles").insert(profile_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create profile")

    return result.data[0]


@router.put("/student/{student_id}")
async def update_profile(
    student_id: UUID,
    update: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a student's learning profile"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    # Check if profile exists
    existing = supabase.table("student_learning_profiles").select("id").eq(
        "student_id", str(student_id)
    ).single().execute()

    if not existing.data:
        # Create new profile if it doesn't exist
        profile_data = {
            "school_id": school_id,
            "student_id": str(student_id),
            "created_by": user_id,
            "learning_style": update.learning_style.dict() if update.learning_style else None,
            "strengths": update.strengths or [],
            "areas_for_growth": update.areas_for_growth or [],
            "interests": update.interests or [],
            "accommodations": [a.dict() for a in (update.accommodations or [])],
            "learning_goals": [g.dict() for g in (update.learning_goals or [])],
            "notes": update.notes,
            "iep_status": update.iep_status or "none",
            "ell_status": update.ell_status or "none",
            "gifted_status": update.gifted_status or "none"
        }
        result = supabase.table("student_learning_profiles").insert(profile_data).execute()
        return result.data[0] if result.data else None

    # Update existing profile
    update_data = {"updated_by": user_id}

    if update.learning_style is not None:
        update_data["learning_style"] = update.learning_style.dict()
    if update.strengths is not None:
        update_data["strengths"] = update.strengths
    if update.areas_for_growth is not None:
        update_data["areas_for_growth"] = update.areas_for_growth
    if update.interests is not None:
        update_data["interests"] = update.interests
    if update.accommodations is not None:
        update_data["accommodations"] = [a.dict() for a in update.accommodations]
    if update.learning_goals is not None:
        update_data["learning_goals"] = [g.dict() for g in update.learning_goals]
    if update.notes is not None:
        update_data["notes"] = update.notes
    if update.iep_status is not None:
        update_data["iep_status"] = update.iep_status
    if update.ell_status is not None:
        update_data["ell_status"] = update.ell_status
    if update.gifted_status is not None:
        update_data["gifted_status"] = update.gifted_status

    result = supabase.table("student_learning_profiles").update(update_data).eq(
        "student_id", str(student_id)
    ).execute()

    return result.data[0] if result.data else None


@router.post("/student/{student_id}/goal")
async def add_learning_goal(
    student_id: UUID,
    goal: LearningGoal,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Add a learning goal to a student's profile"""
    profile = supabase.table("student_learning_profiles").select(
        "learning_goals"
    ).eq("student_id", str(student_id)).single().execute()

    if not profile.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    goals = profile.data.get("learning_goals") or []
    goals.append(goal.dict())

    supabase.table("student_learning_profiles").update({
        "learning_goals": goals
    }).eq("student_id", str(student_id)).execute()

    return {"success": True, "goal": goal.dict()}


@router.put("/student/{student_id}/goal/{goal_id}")
async def update_learning_goal(
    student_id: UUID,
    goal_id: str,
    status: str,
    progress_note: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a learning goal's status"""
    profile = supabase.table("student_learning_profiles").select(
        "learning_goals"
    ).eq("student_id", str(student_id)).single().execute()

    if not profile.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    goals = profile.data.get("learning_goals") or []
    updated = False

    for goal in goals:
        if goal.get("id") == goal_id:
            goal["status"] = status
            if progress_note:
                if "progress_notes" not in goal:
                    goal["progress_notes"] = []
                goal["progress_notes"].append(progress_note)
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail="Goal not found")

    supabase.table("student_learning_profiles").update({
        "learning_goals": goals
    }).eq("student_id", str(student_id)).execute()

    return {"success": True}


@router.get("/class/{class_id}/summary")
async def get_class_profile_summary(
    class_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get summary of learning profiles for a class"""
    school_id = current_user.get("school_id")

    # Get all students in class
    students = supabase.table("students").select(
        "id, first_name, last_name"
    ).eq("class_id", str(class_id)).execute()

    student_ids = [s["id"] for s in (students.data or [])]

    if not student_ids:
        return {
            "total_students": 0,
            "profiles_created": 0,
            "iep_count": 0,
            "ell_count": 0,
            "gifted_count": 0,
            "accommodation_summary": {}
        }

    # Get profiles
    profiles = supabase.table("student_learning_profiles").select(
        "student_id, iep_status, ell_status, gifted_status, accommodations, learning_style"
    ).in_("student_id", student_ids).execute()

    profile_data = profiles.data or []

    # Calculate summaries
    iep_count = len([p for p in profile_data if p.get("iep_status") == "active"])
    ell_count = len([p for p in profile_data if p.get("ell_status") not in ["none", None]])
    gifted_count = len([p for p in profile_data if p.get("gifted_status") not in ["none", None]])

    # Accommodation types summary
    accommodation_types = {}
    for p in profile_data:
        for acc in (p.get("accommodations") or []):
            acc_type = acc.get("type", "other")
            accommodation_types[acc_type] = accommodation_types.get(acc_type, 0) + 1

    # Learning style summary
    style_totals = {"visual": 0, "auditory": 0, "kinesthetic": 0, "reading_writing": 0}
    style_count = 0
    for p in profile_data:
        style = p.get("learning_style")
        if style:
            style_count += 1
            for key in style_totals:
                style_totals[key] += style.get(key, 0)

    learning_style_averages = {}
    if style_count > 0:
        for key, total in style_totals.items():
            learning_style_averages[key] = round(total / style_count, 1)

    return {
        "total_students": len(student_ids),
        "profiles_created": len(profile_data),
        "iep_count": iep_count,
        "ell_count": ell_count,
        "gifted_count": gifted_count,
        "accommodation_summary": accommodation_types,
        "learning_style_averages": learning_style_averages
    }
