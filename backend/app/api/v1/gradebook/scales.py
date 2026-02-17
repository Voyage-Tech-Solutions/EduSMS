"""
EduCore Backend - Grading Scales API
Configure grading scales (percentage, letter grades, points, etc.)
"""
import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class GradeLevel(BaseModel):
    """A single grade level in a scale"""
    grade: str  # A, B, C, D, F or custom
    min_score: float
    max_score: float
    gpa_points: Optional[float] = None
    description: Optional[str] = None


class GradingScaleCreate(BaseModel):
    """Create a grading scale"""
    name: str
    type: str  # percentage, letter, points, standards, pass_fail
    scale_config: dict  # Grade level configuration
    is_default: bool = False


class GradingScaleUpdate(BaseModel):
    """Update a grading scale"""
    name: Optional[str] = None
    scale_config: Optional[dict] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class GradingScaleResponse(BaseModel):
    """Grading scale response"""
    id: UUID
    school_id: UUID
    name: str
    type: str
    scale_config: dict
    is_default: bool
    is_active: bool


# ============================================================
# DEFAULT SCALES
# ============================================================

DEFAULT_SCALES = {
    "standard_letter": {
        "name": "Standard Letter Grade (A-F)",
        "type": "letter",
        "scale_config": {
            "A+": {"min": 97, "max": 100, "gpa": 4.0},
            "A": {"min": 93, "max": 96.99, "gpa": 4.0},
            "A-": {"min": 90, "max": 92.99, "gpa": 3.7},
            "B+": {"min": 87, "max": 89.99, "gpa": 3.3},
            "B": {"min": 83, "max": 86.99, "gpa": 3.0},
            "B-": {"min": 80, "max": 82.99, "gpa": 2.7},
            "C+": {"min": 77, "max": 79.99, "gpa": 2.3},
            "C": {"min": 73, "max": 76.99, "gpa": 2.0},
            "C-": {"min": 70, "max": 72.99, "gpa": 1.7},
            "D+": {"min": 67, "max": 69.99, "gpa": 1.3},
            "D": {"min": 63, "max": 66.99, "gpa": 1.0},
            "D-": {"min": 60, "max": 62.99, "gpa": 0.7},
            "F": {"min": 0, "max": 59.99, "gpa": 0.0}
        }
    },
    "simple_letter": {
        "name": "Simple Letter Grade (A-F)",
        "type": "letter",
        "scale_config": {
            "A": {"min": 90, "max": 100, "gpa": 4.0},
            "B": {"min": 80, "max": 89.99, "gpa": 3.0},
            "C": {"min": 70, "max": 79.99, "gpa": 2.0},
            "D": {"min": 60, "max": 69.99, "gpa": 1.0},
            "F": {"min": 0, "max": 59.99, "gpa": 0.0}
        }
    },
    "pass_fail": {
        "name": "Pass/Fail",
        "type": "pass_fail",
        "scale_config": {
            "P": {"min": 60, "max": 100, "description": "Pass"},
            "F": {"min": 0, "max": 59.99, "description": "Fail"}
        }
    },
    "standards_based": {
        "name": "Standards-Based (1-4)",
        "type": "standards",
        "scale_config": {
            "4": {"min": 90, "max": 100, "description": "Advanced/Exceeding"},
            "3": {"min": 70, "max": 89.99, "description": "Proficient/Meeting"},
            "2": {"min": 50, "max": 69.99, "description": "Developing/Approaching"},
            "1": {"min": 0, "max": 49.99, "description": "Beginning/Not Yet"}
        }
    }
}


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_grading_scales(
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List all grading scales for the school"""
    school_id = current_user.get("school_id")
    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    query = supabase.table("grading_scales").select("*").eq("school_id", school_id)

    if not include_inactive:
        query = query.eq("is_active", True)

    result = query.order("name").execute()

    return {
        "scales": result.data or [],
        "default_templates": list(DEFAULT_SCALES.keys())
    }


@router.get("/templates")
async def get_scale_templates():
    """Get available grading scale templates"""
    return {
        "templates": DEFAULT_SCALES
    }


@router.get("/{scale_id}")
async def get_grading_scale(
    scale_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific grading scale"""
    result = supabase.table("grading_scales").select(
        "*"
    ).eq("id", str(scale_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Grading scale not found")

    return result.data


@router.post("", response_model=GradingScaleResponse)
async def create_grading_scale(
    scale: GradingScaleCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new grading scale"""
    school_id = current_user.get("school_id")
    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # If setting as default, unset other defaults
    if scale.is_default:
        supabase.table("grading_scales").update({
            "is_default": False
        }).eq("school_id", school_id).execute()

    scale_data = {
        "school_id": school_id,
        "name": scale.name,
        "type": scale.type,
        "scale_config": scale.scale_config,
        "is_default": scale.is_default,
        "is_active": True
    }

    result = supabase.table("grading_scales").insert(scale_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create grading scale")

    return GradingScaleResponse(**result.data[0])


@router.post("/from-template/{template_name}")
async def create_scale_from_template(
    template_name: str,
    make_default: bool = False,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a grading scale from a template"""
    if template_name not in DEFAULT_SCALES:
        raise HTTPException(status_code=404, detail="Template not found")

    template = DEFAULT_SCALES[template_name]
    school_id = current_user.get("school_id")

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # If setting as default, unset other defaults
    if make_default:
        supabase.table("grading_scales").update({
            "is_default": False
        }).eq("school_id", school_id).execute()

    scale_data = {
        "school_id": school_id,
        "name": template["name"],
        "type": template["type"],
        "scale_config": template["scale_config"],
        "is_default": make_default,
        "is_active": True
    }

    result = supabase.table("grading_scales").insert(scale_data).execute()

    return result.data[0] if result.data else None


@router.put("/{scale_id}", response_model=GradingScaleResponse)
async def update_grading_scale(
    scale_id: UUID,
    update: GradingScaleUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a grading scale"""
    school_id = current_user.get("school_id")

    update_data = {}
    if update.name is not None:
        update_data["name"] = update.name
    if update.scale_config is not None:
        update_data["scale_config"] = update.scale_config
    if update.is_active is not None:
        update_data["is_active"] = update.is_active
    if update.is_default is not None:
        update_data["is_default"] = update.is_default
        if update.is_default:
            # Unset other defaults
            supabase.table("grading_scales").update({
                "is_default": False
            }).eq("school_id", school_id).neq("id", str(scale_id)).execute()

    result = supabase.table("grading_scales").update(
        update_data
    ).eq("id", str(scale_id)).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Grading scale not found")

    return GradingScaleResponse(**result.data[0])


@router.delete("/{scale_id}")
async def delete_grading_scale(
    scale_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a grading scale (soft delete - sets inactive)"""
    result = supabase.table("grading_scales").update({
        "is_active": False
    }).eq("id", str(scale_id)).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Grading scale not found")

    return {"success": True}


@router.post("/{scale_id}/set-default")
async def set_default_scale(
    scale_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Set a grading scale as the default"""
    school_id = current_user.get("school_id")

    # Unset all defaults
    supabase.table("grading_scales").update({
        "is_default": False
    }).eq("school_id", school_id).execute()

    # Set new default
    result = supabase.table("grading_scales").update({
        "is_default": True
    }).eq("id", str(scale_id)).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Grading scale not found")

    return {"success": True, "scale": result.data[0]}


@router.get("/{scale_id}/convert/{percentage}")
async def convert_percentage_to_grade(
    scale_id: UUID,
    percentage: float,
    supabase = Depends(get_supabase)
):
    """Convert a percentage to a letter grade using a scale"""
    result = supabase.table("grading_scales").select(
        "scale_config, type"
    ).eq("id", str(scale_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Grading scale not found")

    scale_config = result.data["scale_config"]

    for grade, config in scale_config.items():
        min_score = config.get("min", 0)
        max_score = config.get("max", 100)

        if min_score <= percentage <= max_score:
            return {
                "percentage": percentage,
                "grade": grade,
                "gpa_points": config.get("gpa"),
                "description": config.get("description")
            }

    return {
        "percentage": percentage,
        "grade": None,
        "error": "Could not determine grade"
    }
