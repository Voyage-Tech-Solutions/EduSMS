"""
EduCore Backend - Grade Categories API
Weighted grade categories (Homework, Tests, Projects, etc.)
"""
import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, validator

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class GradeCategoryCreate(BaseModel):
    """Create a grade category"""
    class_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    name: str
    weight: float  # Percentage weight (e.g., 20 for 20%)
    drop_lowest: int = 0
    is_extra_credit: bool = False
    display_order: int = 0

    @validator('weight')
    def weight_must_be_valid(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Weight must be between 0 and 100')
        return v


class GradeCategoryUpdate(BaseModel):
    """Update a grade category"""
    name: Optional[str] = None
    weight: Optional[float] = None
    drop_lowest: Optional[int] = None
    is_extra_credit: Optional[bool] = None
    display_order: Optional[int] = None


class GradeCategoryResponse(BaseModel):
    """Grade category response"""
    id: UUID
    school_id: UUID
    class_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    name: str
    weight: float
    drop_lowest: int
    is_extra_credit: bool
    display_order: int


class CategoryWeightValidation(BaseModel):
    """Response for weight validation"""
    is_valid: bool
    total_weight: float
    message: str
    categories: List[dict]


# ============================================================
# DEFAULT CATEGORY TEMPLATES
# ============================================================

DEFAULT_CATEGORY_TEMPLATES = {
    "standard": [
        {"name": "Tests/Quizzes", "weight": 40, "drop_lowest": 0},
        {"name": "Homework", "weight": 20, "drop_lowest": 1},
        {"name": "Projects", "weight": 25, "drop_lowest": 0},
        {"name": "Participation", "weight": 15, "drop_lowest": 0}
    ],
    "test_heavy": [
        {"name": "Tests", "weight": 50, "drop_lowest": 0},
        {"name": "Quizzes", "weight": 25, "drop_lowest": 1},
        {"name": "Homework", "weight": 15, "drop_lowest": 2},
        {"name": "Participation", "weight": 10, "drop_lowest": 0}
    ],
    "project_based": [
        {"name": "Projects", "weight": 45, "drop_lowest": 0},
        {"name": "Presentations", "weight": 20, "drop_lowest": 0},
        {"name": "Assignments", "weight": 20, "drop_lowest": 1},
        {"name": "Participation", "weight": 15, "drop_lowest": 0}
    ],
    "balanced": [
        {"name": "Assessments", "weight": 33.33, "drop_lowest": 0},
        {"name": "Classwork", "weight": 33.33, "drop_lowest": 1},
        {"name": "Homework", "weight": 33.34, "drop_lowest": 2}
    ],
    "simple": [
        {"name": "Formative", "weight": 40, "drop_lowest": 1},
        {"name": "Summative", "weight": 60, "drop_lowest": 0}
    ]
}


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_grade_categories(
    class_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List grade categories, optionally filtered by class/subject"""
    school_id = current_user.get("school_id")
    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    query = supabase.table("grade_categories").select("*").eq("school_id", school_id)

    if class_id:
        query = query.eq("class_id", str(class_id))
    if subject_id:
        query = query.eq("subject_id", str(subject_id))

    result = query.order("display_order").execute()

    # Calculate total weight
    categories = result.data or []
    total_weight = sum(c["weight"] for c in categories if not c.get("is_extra_credit"))

    return {
        "categories": categories,
        "total_weight": round(total_weight, 2),
        "is_valid": abs(total_weight - 100) < 0.01 or total_weight == 0
    }


@router.get("/templates")
async def get_category_templates():
    """Get available category templates"""
    return {
        "templates": DEFAULT_CATEGORY_TEMPLATES
    }


@router.get("/{category_id}")
async def get_grade_category(
    category_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific grade category"""
    result = supabase.table("grade_categories").select(
        "*"
    ).eq("id", str(category_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Category not found")

    return result.data


@router.post("", response_model=GradeCategoryResponse)
async def create_grade_category(
    category: GradeCategoryCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new grade category"""
    school_id = current_user.get("school_id")
    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    category_data = {
        "school_id": school_id,
        "class_id": str(category.class_id) if category.class_id else None,
        "subject_id": str(category.subject_id) if category.subject_id else None,
        "name": category.name,
        "weight": category.weight,
        "drop_lowest": category.drop_lowest,
        "is_extra_credit": category.is_extra_credit,
        "display_order": category.display_order
    }

    result = supabase.table("grade_categories").insert(category_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create category")

    return GradeCategoryResponse(**result.data[0])


@router.post("/from-template/{template_name}")
async def create_categories_from_template(
    template_name: str,
    class_id: UUID,
    subject_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create grade categories from a template"""
    if template_name not in DEFAULT_CATEGORY_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    template = DEFAULT_CATEGORY_TEMPLATES[template_name]
    school_id = current_user.get("school_id")

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # Delete existing categories for this class/subject
    supabase.table("grade_categories").delete().eq(
        "class_id", str(class_id)
    ).eq("subject_id", str(subject_id)).execute()

    # Create new categories
    categories_to_insert = []
    for i, cat in enumerate(template):
        categories_to_insert.append({
            "school_id": school_id,
            "class_id": str(class_id),
            "subject_id": str(subject_id),
            "name": cat["name"],
            "weight": cat["weight"],
            "drop_lowest": cat.get("drop_lowest", 0),
            "is_extra_credit": cat.get("is_extra_credit", False),
            "display_order": i
        })

    result = supabase.table("grade_categories").insert(categories_to_insert).execute()

    return {
        "success": True,
        "categories_created": len(result.data) if result.data else 0,
        "categories": result.data
    }


@router.put("/{category_id}", response_model=GradeCategoryResponse)
async def update_grade_category(
    category_id: UUID,
    update: GradeCategoryUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a grade category"""
    update_data = {}
    if update.name is not None:
        update_data["name"] = update.name
    if update.weight is not None:
        update_data["weight"] = update.weight
    if update.drop_lowest is not None:
        update_data["drop_lowest"] = update.drop_lowest
    if update.is_extra_credit is not None:
        update_data["is_extra_credit"] = update.is_extra_credit
    if update.display_order is not None:
        update_data["display_order"] = update.display_order

    result = supabase.table("grade_categories").update(
        update_data
    ).eq("id", str(category_id)).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Category not found")

    return GradeCategoryResponse(**result.data[0])


@router.delete("/{category_id}")
async def delete_grade_category(
    category_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a grade category"""
    # Check if category has entries
    entries = supabase.table("gradebook_entries").select(
        "id"
    ).eq("category_id", str(category_id)).limit(1).execute()

    if entries.data:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete category with existing gradebook entries"
        )

    supabase.table("grade_categories").delete().eq("id", str(category_id)).execute()

    return {"success": True}


@router.post("/validate-weights")
async def validate_category_weights(
    class_id: UUID,
    subject_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
) -> CategoryWeightValidation:
    """Validate that category weights sum to 100%"""
    result = supabase.table("grade_categories").select(
        "id, name, weight, is_extra_credit"
    ).eq("class_id", str(class_id)).eq("subject_id", str(subject_id)).execute()

    categories = result.data or []

    # Only count non-extra-credit categories
    regular_categories = [c for c in categories if not c.get("is_extra_credit")]
    total_weight = sum(c["weight"] for c in regular_categories)

    is_valid = abs(total_weight - 100) < 0.01

    if is_valid:
        message = "Category weights are valid (sum to 100%)"
    elif total_weight < 100:
        message = f"Category weights sum to {total_weight:.1f}%. Missing {100 - total_weight:.1f}%"
    else:
        message = f"Category weights sum to {total_weight:.1f}%. Exceeds 100% by {total_weight - 100:.1f}%"

    return CategoryWeightValidation(
        is_valid=is_valid,
        total_weight=round(total_weight, 2),
        message=message,
        categories=[{
            "id": c["id"],
            "name": c["name"],
            "weight": c["weight"],
            "is_extra_credit": c.get("is_extra_credit", False)
        } for c in categories]
    )


@router.post("/reorder")
async def reorder_categories(
    category_orders: List[dict],  # [{id, display_order}]
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Reorder categories"""
    for order in category_orders:
        supabase.table("grade_categories").update({
            "display_order": order["display_order"]
        }).eq("id", order["id"]).execute()

    return {"success": True}
