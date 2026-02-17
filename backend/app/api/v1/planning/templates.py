"""
EduCore Backend - Lesson Templates API
Reusable lesson plan templates
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

class TemplateSection(BaseModel):
    """A section within a lesson template"""
    id: str
    name: str
    description: Optional[str] = None
    duration_minutes: int = 10
    type: str = "activity"  # opener, direct_instruction, activity, assessment, closure
    prompts: List[str] = []  # Guiding prompts for this section
    order_index: int = 0


class LessonTemplateCreate(BaseModel):
    """Create a lesson template"""
    name: str
    description: Optional[str] = None
    subject_id: Optional[UUID] = None
    grade_id: Optional[UUID] = None
    lesson_type: str = "standard"  # standard, workshop, inquiry, project, flipped
    duration_minutes: int = 45
    sections: List[TemplateSection] = []
    is_shared: bool = False


class LessonTemplateUpdate(BaseModel):
    """Update a lesson template"""
    name: Optional[str] = None
    description: Optional[str] = None
    lesson_type: Optional[str] = None
    duration_minutes: Optional[int] = None
    sections: Optional[List[TemplateSection]] = None
    is_shared: Optional[bool] = None
    is_active: Optional[bool] = None


# ============================================================
# BUILT-IN TEMPLATES
# ============================================================

BUILT_IN_TEMPLATES = {
    "gradual_release": {
        "name": "Gradual Release of Responsibility (I Do, We Do, You Do)",
        "description": "Classic instructional model for scaffolded learning",
        "lesson_type": "standard",
        "duration_minutes": 45,
        "sections": [
            {
                "id": "opener",
                "name": "Warm-Up / Opener",
                "description": "Activate prior knowledge and engage students",
                "duration_minutes": 5,
                "type": "opener",
                "prompts": [
                    "What will students do as they enter?",
                    "How does this connect to prior learning?"
                ],
                "order_index": 0
            },
            {
                "id": "objective",
                "name": "Learning Objective",
                "description": "State the learning target clearly",
                "duration_minutes": 2,
                "type": "direct_instruction",
                "prompts": [
                    "What will students be able to do by the end?",
                    "How will you communicate the objective?"
                ],
                "order_index": 1
            },
            {
                "id": "i_do",
                "name": "I Do (Direct Instruction)",
                "description": "Teacher models the skill or concept",
                "duration_minutes": 10,
                "type": "direct_instruction",
                "prompts": [
                    "How will you model the thinking process?",
                    "What examples will you use?",
                    "What common misconceptions should you address?"
                ],
                "order_index": 2
            },
            {
                "id": "we_do",
                "name": "We Do (Guided Practice)",
                "description": "Practice together with scaffolding",
                "duration_minutes": 10,
                "type": "activity",
                "prompts": [
                    "What problems/tasks will you work through together?",
                    "How will you check for understanding?",
                    "What scaffolds will you provide?"
                ],
                "order_index": 3
            },
            {
                "id": "you_do",
                "name": "You Do (Independent Practice)",
                "description": "Students practice independently",
                "duration_minutes": 12,
                "type": "activity",
                "prompts": [
                    "What tasks will students complete?",
                    "How will you support struggling learners?",
                    "What will early finishers do?"
                ],
                "order_index": 4
            },
            {
                "id": "closure",
                "name": "Closure / Exit Ticket",
                "description": "Summarize learning and assess understanding",
                "duration_minutes": 6,
                "type": "closure",
                "prompts": [
                    "How will students summarize their learning?",
                    "What exit ticket question will you use?",
                    "What's the preview for next lesson?"
                ],
                "order_index": 5
            }
        ]
    },
    "5e_model": {
        "name": "5E Inquiry Model",
        "description": "Engage, Explore, Explain, Elaborate, Evaluate",
        "lesson_type": "inquiry",
        "duration_minutes": 60,
        "sections": [
            {
                "id": "engage",
                "name": "Engage",
                "description": "Capture attention and activate prior knowledge",
                "duration_minutes": 8,
                "type": "opener",
                "prompts": [
                    "What hook or phenomenon will capture interest?",
                    "How will you surface prior knowledge?",
                    "What driving question will guide inquiry?"
                ],
                "order_index": 0
            },
            {
                "id": "explore",
                "name": "Explore",
                "description": "Hands-on investigation or discovery",
                "duration_minutes": 15,
                "type": "activity",
                "prompts": [
                    "What investigation will students conduct?",
                    "What materials are needed?",
                    "How will you guide without giving answers?"
                ],
                "order_index": 1
            },
            {
                "id": "explain",
                "name": "Explain",
                "description": "Students share findings, teacher clarifies concepts",
                "duration_minutes": 15,
                "type": "direct_instruction",
                "prompts": [
                    "How will students share their discoveries?",
                    "What key concepts need explicit instruction?",
                    "What vocabulary will you introduce?"
                ],
                "order_index": 2
            },
            {
                "id": "elaborate",
                "name": "Elaborate",
                "description": "Apply learning to new situations",
                "duration_minutes": 15,
                "type": "activity",
                "prompts": [
                    "What extension activity challenges students?",
                    "How will students apply their learning?",
                    "What real-world connections can be made?"
                ],
                "order_index": 3
            },
            {
                "id": "evaluate",
                "name": "Evaluate",
                "description": "Assess understanding and reflect",
                "duration_minutes": 7,
                "type": "assessment",
                "prompts": [
                    "What formative assessment will you use?",
                    "How will students self-assess?",
                    "What evidence of learning will you collect?"
                ],
                "order_index": 4
            }
        ]
    },
    "workshop_model": {
        "name": "Workshop Model",
        "description": "Mini-lesson, work time, share - ideal for reading/writing",
        "lesson_type": "workshop",
        "duration_minutes": 60,
        "sections": [
            {
                "id": "mini_lesson",
                "name": "Mini-Lesson",
                "description": "Focused instruction on one skill or strategy",
                "duration_minutes": 10,
                "type": "direct_instruction",
                "prompts": [
                    "What single skill/strategy will you teach?",
                    "What mentor text or example will you use?",
                    "How will you think aloud?"
                ],
                "order_index": 0
            },
            {
                "id": "work_time",
                "name": "Work Time",
                "description": "Independent reading/writing with conferring",
                "duration_minutes": 35,
                "type": "activity",
                "prompts": [
                    "What will students work on?",
                    "Which students will you confer with?",
                    "What small groups will you pull?"
                ],
                "order_index": 1
            },
            {
                "id": "mid_workshop",
                "name": "Mid-Workshop Teaching Point",
                "description": "Brief interruption for quick tip or reminder",
                "duration_minutes": 3,
                "type": "direct_instruction",
                "prompts": [
                    "What quick tip might students need?",
                    "What common issue should you address?"
                ],
                "order_index": 2
            },
            {
                "id": "share",
                "name": "Share",
                "description": "Students share work and learn from each other",
                "duration_minutes": 12,
                "type": "closure",
                "prompts": [
                    "How will students share their work?",
                    "What will you celebrate or reinforce?",
                    "How will you connect to tomorrow's lesson?"
                ],
                "order_index": 3
            }
        ]
    },
    "flipped_classroom": {
        "name": "Flipped Classroom",
        "description": "Content at home, application in class",
        "lesson_type": "flipped",
        "duration_minutes": 45,
        "sections": [
            {
                "id": "review",
                "name": "Quick Review / Q&A",
                "description": "Address questions from pre-class content",
                "duration_minutes": 8,
                "type": "direct_instruction",
                "prompts": [
                    "What pre-class content did students view?",
                    "What questions do students have?",
                    "What common confusions need addressing?"
                ],
                "order_index": 0
            },
            {
                "id": "application",
                "name": "Application Activity",
                "description": "Hands-on practice applying concepts",
                "duration_minutes": 25,
                "type": "activity",
                "prompts": [
                    "What application task will students do?",
                    "How is this more challenging than the video?",
                    "How will you differentiate?"
                ],
                "order_index": 1
            },
            {
                "id": "deepen",
                "name": "Deepen Understanding",
                "description": "Extension or discussion to build depth",
                "duration_minutes": 10,
                "type": "activity",
                "prompts": [
                    "How will students extend their thinking?",
                    "What discussion question promotes deeper understanding?",
                    "What connections can students make?"
                ],
                "order_index": 2
            },
            {
                "id": "preview",
                "name": "Preview Next Content",
                "description": "Introduce next pre-class assignment",
                "duration_minutes": 2,
                "type": "closure",
                "prompts": [
                    "What will students watch/read at home?",
                    "What questions should guide their viewing?",
                    "What's due when?"
                ],
                "order_index": 3
            }
        ]
    },
    "project_based": {
        "name": "Project Work Session",
        "description": "Structure for extended project work time",
        "lesson_type": "project",
        "duration_minutes": 60,
        "sections": [
            {
                "id": "check_in",
                "name": "Team Check-In",
                "description": "Review goals and address blockers",
                "duration_minutes": 5,
                "type": "opener",
                "prompts": [
                    "What should each team have accomplished?",
                    "What obstacles might teams face?",
                    "What quick wins can you celebrate?"
                ],
                "order_index": 0
            },
            {
                "id": "skill_spotlight",
                "name": "Skill Spotlight",
                "description": "Just-in-time instruction for needed skills",
                "duration_minutes": 8,
                "type": "direct_instruction",
                "prompts": [
                    "What skill do students need right now?",
                    "How can you teach it briefly and clearly?",
                    "What resources can you provide?"
                ],
                "order_index": 1
            },
            {
                "id": "work_time",
                "name": "Project Work Time",
                "description": "Focused time for teams to work",
                "duration_minutes": 35,
                "type": "activity",
                "prompts": [
                    "What milestones should teams reach today?",
                    "Which teams need your attention?",
                    "What formative check will you do?"
                ],
                "order_index": 2
            },
            {
                "id": "progress_share",
                "name": "Progress Share",
                "description": "Teams report progress and get feedback",
                "duration_minutes": 10,
                "type": "closure",
                "prompts": [
                    "How will teams share progress?",
                    "What feedback protocol will you use?",
                    "What's expected by next session?"
                ],
                "order_index": 3
            },
            {
                "id": "reflection",
                "name": "Individual Reflection",
                "description": "Personal reflection on contribution",
                "duration_minutes": 2,
                "type": "closure",
                "prompts": [
                    "What will students reflect on?",
                    "How will they document their contribution?",
                    "What self-assessment criteria will you use?"
                ],
                "order_index": 4
            }
        ]
    }
}


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_templates(
    lesson_type: Optional[str] = None,
    subject_id: Optional[UUID] = None,
    include_shared: bool = True,
    include_system: bool = True,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List lesson templates"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    query = supabase.table("lesson_templates").select(
        "*, subjects(name), grades(name)"
    ).eq("school_id", school_id).eq("is_active", True)

    # Filter ownership
    conditions = [f"created_by.eq.{user_id}"]
    if include_shared:
        conditions.append("is_shared.eq.true")
    if include_system:
        conditions.append("is_system_template.eq.true")

    query = query.or_(",".join(conditions))

    if lesson_type:
        query = query.eq("lesson_type", lesson_type)
    if subject_id:
        query = query.eq("subject_id", str(subject_id))
    if search:
        query = query.ilike("name", f"%{search}%")

    query = query.order("name").range(offset, offset + limit - 1)

    result = query.execute()

    return {
        "templates": result.data or [],
        "total": len(result.data) if result.data else 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/built-in")
async def get_built_in_templates(
    current_user: dict = Depends(get_current_user)
):
    """Get available built-in templates"""
    templates = []
    for key, template in BUILT_IN_TEMPLATES.items():
        templates.append({
            "id": key,
            "name": template["name"],
            "description": template["description"],
            "lesson_type": template["lesson_type"],
            "duration_minutes": template["duration_minutes"],
            "section_count": len(template["sections"])
        })
    return {"templates": templates}


@router.get("/built-in/{template_id}")
async def get_built_in_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific built-in template with full details"""
    if template_id not in BUILT_IN_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    return BUILT_IN_TEMPLATES[template_id]


@router.get("/{template_id}")
async def get_template(
    template_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific template"""
    result = supabase.table("lesson_templates").select(
        "*, subjects(name), grades(name)"
    ).eq("id", str(template_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Template not found")

    return result.data


@router.post("")
async def create_template(
    template: LessonTemplateCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new lesson template"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    template_data = {
        "school_id": school_id,
        "created_by": user_id,
        "name": template.name,
        "description": template.description,
        "subject_id": str(template.subject_id) if template.subject_id else None,
        "grade_id": str(template.grade_id) if template.grade_id else None,
        "lesson_type": template.lesson_type,
        "duration_minutes": template.duration_minutes,
        "structure": [s.dict() for s in template.sections],
        "is_shared": template.is_shared,
        "is_system_template": False,
        "is_active": True
    }

    result = supabase.table("lesson_templates").insert(template_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create template")

    return result.data[0]


@router.post("/from-built-in/{built_in_id}")
async def create_from_built_in(
    built_in_id: str,
    name: Optional[str] = None,
    subject_id: Optional[UUID] = None,
    grade_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a template from a built-in template"""
    if built_in_id not in BUILT_IN_TEMPLATES:
        raise HTTPException(status_code=404, detail="Built-in template not found")

    built_in = BUILT_IN_TEMPLATES[built_in_id]
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    template_data = {
        "school_id": school_id,
        "created_by": user_id,
        "name": name or built_in["name"],
        "description": built_in["description"],
        "subject_id": str(subject_id) if subject_id else None,
        "grade_id": str(grade_id) if grade_id else None,
        "lesson_type": built_in["lesson_type"],
        "duration_minutes": built_in["duration_minutes"],
        "structure": built_in["sections"],
        "is_shared": False,
        "is_system_template": False,
        "is_active": True
    }

    result = supabase.table("lesson_templates").insert(template_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create template")

    return result.data[0]


@router.put("/{template_id}")
async def update_template(
    template_id: UUID,
    update: LessonTemplateUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a lesson template"""
    user_id = current_user["id"]

    existing = supabase.table("lesson_templates").select(
        "created_by, is_system_template"
    ).eq("id", str(template_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Template not found")

    if existing.data.get("is_system_template"):
        raise HTTPException(status_code=403, detail="Cannot modify system templates")

    if existing.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own templates")

    update_data = {}
    if update.name is not None:
        update_data["name"] = update.name
    if update.description is not None:
        update_data["description"] = update.description
    if update.lesson_type is not None:
        update_data["lesson_type"] = update.lesson_type
    if update.duration_minutes is not None:
        update_data["duration_minutes"] = update.duration_minutes
    if update.sections is not None:
        update_data["structure"] = [s.dict() for s in update.sections]
    if update.is_shared is not None:
        update_data["is_shared"] = update.is_shared
    if update.is_active is not None:
        update_data["is_active"] = update.is_active

    result = supabase.table("lesson_templates").update(update_data).eq(
        "id", str(template_id)
    ).execute()

    return result.data[0] if result.data else None


@router.delete("/{template_id}")
async def delete_template(
    template_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a lesson template"""
    user_id = current_user["id"]

    existing = supabase.table("lesson_templates").select(
        "created_by, is_system_template"
    ).eq("id", str(template_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Template not found")

    if existing.data.get("is_system_template"):
        raise HTTPException(status_code=403, detail="Cannot delete system templates")

    if existing.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own templates")

    supabase.table("lesson_templates").update({
        "is_active": False
    }).eq("id", str(template_id)).execute()

    return {"success": True}


@router.post("/{template_id}/duplicate")
async def duplicate_template(
    template_id: UUID,
    new_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a copy of a template"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    original = supabase.table("lesson_templates").select("*").eq(
        "id", str(template_id)
    ).single().execute()

    if not original.data:
        raise HTTPException(status_code=404, detail="Template not found")

    new_template = {**original.data}
    del new_template["id"]
    del new_template["created_at"]
    del new_template["updated_at"]
    new_template["created_by"] = user_id
    new_template["school_id"] = school_id
    new_template["name"] = new_name or f"(Copy) {new_template['name']}"
    new_template["is_system_template"] = False
    new_template["is_shared"] = False

    result = supabase.table("lesson_templates").insert(new_template).execute()

    return result.data[0] if result.data else None
