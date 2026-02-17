"""
EduCore Backend - Quiz Builder API
Create and manage quizzes/assessments with questions
"""
import logging
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class QuizQuestionAdd(BaseModel):
    """Add a question to quiz"""
    question_id: UUID
    order_index: int = 0
    points_override: Optional[float] = None


class QuizConfig(BaseModel):
    """Quiz configuration settings"""
    time_limit_minutes: Optional[int] = None
    shuffle_questions: bool = False
    shuffle_options: bool = False
    show_correct_answers: bool = False
    show_correct_answers_after: Optional[str] = None  # immediately, after_due_date, manual
    allow_retakes: int = 0
    retake_penalty_percent: float = 0
    release_scores_immediately: bool = True
    require_lockdown_browser: bool = False
    allow_calculator: bool = False
    show_one_question_at_a_time: bool = False
    prevent_going_back: bool = False
    password: Optional[str] = None


class QuizCreate(BaseModel):
    """Create a new quiz"""
    title: str
    description: Optional[str] = None
    class_id: UUID
    subject_id: UUID
    assessment_type: str = "quiz"  # quiz, test, exam, homework, practice
    category_id: Optional[UUID] = None  # grade category
    total_points: Optional[float] = None
    due_date: Optional[datetime] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    config: Optional[QuizConfig] = None
    question_ids: Optional[List[UUID]] = None  # Quick add existing questions


class QuizUpdate(BaseModel):
    """Update quiz details"""
    title: Optional[str] = None
    description: Optional[str] = None
    total_points: Optional[float] = None
    due_date: Optional[datetime] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    config: Optional[QuizConfig] = None
    is_published: Optional[bool] = None


class QuizResponse(BaseModel):
    """Quiz response with summary"""
    id: UUID
    title: str
    description: Optional[str] = None
    class_id: UUID
    subject_id: UUID
    assessment_type: str
    total_points: float
    question_count: int
    due_date: Optional[datetime] = None
    is_published: bool
    status: str  # draft, published, closed, graded


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_quizzes(
    class_id: Optional[UUID] = None,
    subject_id: Optional[UUID] = None,
    assessment_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List quizzes/assessments with filters"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # Build query
    query = supabase.table("assessments").select(
        "*, classes(name), subjects(name), quiz_configs(*)"
    ).eq("school_id", school_id).eq("created_by", user_id)

    if class_id:
        query = query.eq("class_id", str(class_id))
    if subject_id:
        query = query.eq("subject_id", str(subject_id))
    if assessment_type:
        query = query.eq("assessment_type", assessment_type)
    if status:
        if status == "draft":
            query = query.eq("is_published", False)
        elif status == "published":
            query = query.eq("is_published", True)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    # Get question counts
    quizzes = result.data or []
    for quiz in quizzes:
        count_result = supabase.table("assessment_questions").select(
            "id", count="exact"
        ).eq("assessment_id", quiz["id"]).execute()
        quiz["question_count"] = count_result.count or 0

    return {
        "quizzes": quizzes,
        "total": len(quizzes),
        "limit": limit,
        "offset": offset
    }


@router.get("/{quiz_id}")
async def get_quiz(
    quiz_id: UUID,
    include_questions: bool = True,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get quiz with full details and questions"""
    result = supabase.table("assessments").select(
        "*, classes(name), subjects(name), quiz_configs(*)"
    ).eq("id", str(quiz_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Quiz not found")

    quiz = result.data

    if include_questions:
        # Get questions with their details
        questions_result = supabase.table("assessment_questions").select(
            "*, question_bank(*)"
        ).eq("assessment_id", str(quiz_id)).order("order_index").execute()

        quiz["questions"] = questions_result.data or []

    # Get attempt statistics
    stats_result = supabase.table("quiz_attempts").select(
        "id, final_score"
    ).eq("assessment_id", str(quiz_id)).execute()

    attempts = stats_result.data or []
    quiz["stats"] = {
        "total_attempts": len(attempts),
        "average_score": sum(a["final_score"] or 0 for a in attempts) / len(attempts) if attempts else 0,
        "completed_count": len([a for a in attempts if a["final_score"] is not None])
    }

    return quiz


@router.post("")
async def create_quiz(
    quiz: QuizCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new quiz/assessment"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # Create the assessment
    assessment_data = {
        "school_id": school_id,
        "created_by": user_id,
        "class_id": str(quiz.class_id),
        "subject_id": str(quiz.subject_id),
        "title": quiz.title,
        "description": quiz.description,
        "assessment_type": quiz.assessment_type,
        "category_id": str(quiz.category_id) if quiz.category_id else None,
        "total_points": quiz.total_points or 0,
        "due_date": quiz.due_date.isoformat() if quiz.due_date else None,
        "available_from": quiz.available_from.isoformat() if quiz.available_from else None,
        "available_until": quiz.available_until.isoformat() if quiz.available_until else None,
        "is_published": False,
        "is_active": True
    }

    result = supabase.table("assessments").insert(assessment_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create quiz")

    assessment = result.data[0]
    assessment_id = assessment["id"]

    # Create quiz config if provided
    if quiz.config:
        config_data = {
            "assessment_id": assessment_id,
            "time_limit_minutes": quiz.config.time_limit_minutes,
            "shuffle_questions": quiz.config.shuffle_questions,
            "shuffle_options": quiz.config.shuffle_options,
            "show_correct_answers": quiz.config.show_correct_answers,
            "show_correct_answers_after": quiz.config.show_correct_answers_after,
            "allow_retakes": quiz.config.allow_retakes,
            "retake_penalty_percent": quiz.config.retake_penalty_percent,
            "release_scores_immediately": quiz.config.release_scores_immediately,
            "require_lockdown_browser": quiz.config.require_lockdown_browser,
            "allow_calculator": quiz.config.allow_calculator,
            "show_one_question_at_a_time": quiz.config.show_one_question_at_a_time,
            "prevent_going_back": quiz.config.prevent_going_back,
            "password": quiz.config.password
        }
        supabase.table("quiz_configs").insert(config_data).execute()

    # Add questions if provided
    if quiz.question_ids:
        questions_to_add = []
        for idx, qid in enumerate(quiz.question_ids):
            # Get question points
            q_result = supabase.table("question_bank").select("points").eq(
                "id", str(qid)
            ).single().execute()

            points = q_result.data["points"] if q_result.data else 1.0

            questions_to_add.append({
                "assessment_id": assessment_id,
                "question_id": str(qid),
                "order_index": idx,
                "points": points
            })

        if questions_to_add:
            supabase.table("assessment_questions").insert(questions_to_add).execute()

            # Update total points
            total = sum(q["points"] for q in questions_to_add)
            supabase.table("assessments").update({
                "total_points": total
            }).eq("id", assessment_id).execute()

    return assessment


@router.put("/{quiz_id}")
async def update_quiz(
    quiz_id: UUID,
    update: QuizUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update quiz details"""
    user_id = current_user["id"]

    # Check ownership
    existing = supabase.table("assessments").select(
        "created_by, is_published"
    ).eq("id", str(quiz_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if existing.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own quizzes")

    # Build update data
    update_data = {}
    if update.title is not None:
        update_data["title"] = update.title
    if update.description is not None:
        update_data["description"] = update.description
    if update.total_points is not None:
        update_data["total_points"] = update.total_points
    if update.due_date is not None:
        update_data["due_date"] = update.due_date.isoformat()
    if update.available_from is not None:
        update_data["available_from"] = update.available_from.isoformat()
    if update.available_until is not None:
        update_data["available_until"] = update.available_until.isoformat()
    if update.is_published is not None:
        update_data["is_published"] = update.is_published

    if update_data:
        supabase.table("assessments").update(update_data).eq("id", str(quiz_id)).execute()

    # Update config if provided
    if update.config:
        config_data = {
            "time_limit_minutes": update.config.time_limit_minutes,
            "shuffle_questions": update.config.shuffle_questions,
            "shuffle_options": update.config.shuffle_options,
            "show_correct_answers": update.config.show_correct_answers,
            "allow_retakes": update.config.allow_retakes,
            "release_scores_immediately": update.config.release_scores_immediately
        }

        # Check if config exists
        config_exists = supabase.table("quiz_configs").select("id").eq(
            "assessment_id", str(quiz_id)
        ).execute()

        if config_exists.data:
            supabase.table("quiz_configs").update(config_data).eq(
                "assessment_id", str(quiz_id)
            ).execute()
        else:
            config_data["assessment_id"] = str(quiz_id)
            supabase.table("quiz_configs").insert(config_data).execute()

    # Return updated quiz
    return await get_quiz(quiz_id, include_questions=False, current_user=current_user, supabase=supabase)


@router.delete("/{quiz_id}")
async def delete_quiz(
    quiz_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a quiz (soft delete)"""
    user_id = current_user["id"]

    # Check ownership
    existing = supabase.table("assessments").select(
        "created_by"
    ).eq("id", str(quiz_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if existing.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own quizzes")

    # Check for attempts
    attempts = supabase.table("quiz_attempts").select(
        "id", count="exact"
    ).eq("assessment_id", str(quiz_id)).execute()

    if attempts.count and attempts.count > 0:
        # Soft delete if there are attempts
        supabase.table("assessments").update({
            "is_active": False
        }).eq("id", str(quiz_id)).execute()
    else:
        # Hard delete if no attempts
        supabase.table("assessment_questions").delete().eq(
            "assessment_id", str(quiz_id)
        ).execute()
        supabase.table("quiz_configs").delete().eq(
            "assessment_id", str(quiz_id)
        ).execute()
        supabase.table("assessments").delete().eq("id", str(quiz_id)).execute()

    return {"success": True}


@router.post("/{quiz_id}/publish")
async def publish_quiz(
    quiz_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Publish a quiz to make it available to students"""
    user_id = current_user["id"]

    # Check ownership and get quiz
    existing = supabase.table("assessments").select(
        "created_by, is_published"
    ).eq("id", str(quiz_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if existing.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only publish your own quizzes")

    if existing.data["is_published"]:
        raise HTTPException(status_code=400, detail="Quiz is already published")

    # Check if quiz has questions
    questions = supabase.table("assessment_questions").select(
        "id", count="exact"
    ).eq("assessment_id", str(quiz_id)).execute()

    if not questions.count or questions.count == 0:
        raise HTTPException(status_code=400, detail="Quiz must have at least one question to publish")

    # Publish
    supabase.table("assessments").update({
        "is_published": True
    }).eq("id", str(quiz_id)).execute()

    return {"success": True, "message": "Quiz published successfully"}


@router.post("/{quiz_id}/unpublish")
async def unpublish_quiz(
    quiz_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Unpublish a quiz (only if no attempts exist)"""
    user_id = current_user["id"]

    # Check ownership
    existing = supabase.table("assessments").select(
        "created_by, is_published"
    ).eq("id", str(quiz_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if existing.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only unpublish your own quizzes")

    # Check for attempts
    attempts = supabase.table("quiz_attempts").select(
        "id", count="exact"
    ).eq("assessment_id", str(quiz_id)).execute()

    if attempts.count and attempts.count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot unpublish quiz with existing attempts. Consider closing it instead."
        )

    supabase.table("assessments").update({
        "is_published": False
    }).eq("id", str(quiz_id)).execute()

    return {"success": True, "message": "Quiz unpublished"}


# ============================================================
# QUESTION MANAGEMENT
# ============================================================

@router.post("/{quiz_id}/questions")
async def add_question_to_quiz(
    quiz_id: UUID,
    question: QuizQuestionAdd,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Add a question to the quiz"""
    user_id = current_user["id"]

    # Check ownership
    existing = supabase.table("assessments").select(
        "created_by"
    ).eq("id", str(quiz_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if existing.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own quizzes")

    # Get question details
    q_result = supabase.table("question_bank").select(
        "points"
    ).eq("id", str(question.question_id)).single().execute()

    if not q_result.data:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check if already added
    existing_q = supabase.table("assessment_questions").select("id").eq(
        "assessment_id", str(quiz_id)
    ).eq("question_id", str(question.question_id)).execute()

    if existing_q.data:
        raise HTTPException(status_code=400, detail="Question already in quiz")

    # Add question
    points = question.points_override or q_result.data["points"]

    question_data = {
        "assessment_id": str(quiz_id),
        "question_id": str(question.question_id),
        "order_index": question.order_index,
        "points": points
    }

    result = supabase.table("assessment_questions").insert(question_data).execute()

    # Update total points
    await _update_quiz_total_points(supabase, str(quiz_id))

    return result.data[0] if result.data else None


@router.delete("/{quiz_id}/questions/{question_id}")
async def remove_question_from_quiz(
    quiz_id: UUID,
    question_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Remove a question from the quiz"""
    user_id = current_user["id"]

    # Check ownership
    existing = supabase.table("assessments").select(
        "created_by"
    ).eq("id", str(quiz_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if existing.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own quizzes")

    # Remove question
    supabase.table("assessment_questions").delete().eq(
        "assessment_id", str(quiz_id)
    ).eq("question_id", str(question_id)).execute()

    # Update total points
    await _update_quiz_total_points(supabase, str(quiz_id))

    return {"success": True}


@router.put("/{quiz_id}/questions/reorder")
async def reorder_questions(
    quiz_id: UUID,
    question_order: List[UUID],
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Reorder questions in the quiz"""
    user_id = current_user["id"]

    # Check ownership
    existing = supabase.table("assessments").select(
        "created_by"
    ).eq("id", str(quiz_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if existing.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own quizzes")

    # Update order for each question
    for idx, qid in enumerate(question_order):
        supabase.table("assessment_questions").update({
            "order_index": idx
        }).eq("assessment_id", str(quiz_id)).eq("question_id", str(qid)).execute()

    return {"success": True}


@router.post("/{quiz_id}/duplicate")
async def duplicate_quiz(
    quiz_id: UUID,
    new_title: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a copy of an existing quiz"""
    user_id = current_user["id"]
    school_id = current_user.get("school_id")

    # Get original quiz
    original = supabase.table("assessments").select("*").eq(
        "id", str(quiz_id)
    ).single().execute()

    if not original.data:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Create copy
    new_quiz = {**original.data}
    del new_quiz["id"]
    del new_quiz["created_at"]
    del new_quiz["updated_at"]
    new_quiz["created_by"] = user_id
    new_quiz["school_id"] = school_id
    new_quiz["title"] = new_title or f"(Copy) {new_quiz['title']}"
    new_quiz["is_published"] = False

    result = supabase.table("assessments").insert(new_quiz).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to duplicate quiz")

    new_quiz_id = result.data[0]["id"]

    # Copy config
    config = supabase.table("quiz_configs").select("*").eq(
        "assessment_id", str(quiz_id)
    ).execute()

    if config.data:
        new_config = {**config.data[0]}
        del new_config["id"]
        new_config["assessment_id"] = new_quiz_id
        supabase.table("quiz_configs").insert(new_config).execute()

    # Copy questions
    questions = supabase.table("assessment_questions").select("*").eq(
        "assessment_id", str(quiz_id)
    ).execute()

    if questions.data:
        for q in questions.data:
            new_q = {**q}
            del new_q["id"]
            new_q["assessment_id"] = new_quiz_id
            supabase.table("assessment_questions").insert(new_q).execute()

    return result.data[0]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

async def _update_quiz_total_points(supabase, quiz_id: str):
    """Update total points for a quiz based on its questions"""
    questions = supabase.table("assessment_questions").select(
        "points"
    ).eq("assessment_id", quiz_id).execute()

    total = sum(q["points"] for q in (questions.data or []))

    supabase.table("assessments").update({
        "total_points": total
    }).eq("id", quiz_id).execute()
