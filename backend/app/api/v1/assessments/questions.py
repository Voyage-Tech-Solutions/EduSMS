"""
EduCore Backend - Question Bank API
Reusable question library for assessments
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

class QuestionOption(BaseModel):
    """Multiple choice option"""
    id: str
    text: str
    is_correct: bool = False
    feedback: Optional[str] = None


class QuestionCreate(BaseModel):
    """Create a question"""
    subject_id: Optional[UUID] = None
    grade_id: Optional[UUID] = None
    question_type: str  # multiple_choice, true_false, short_answer, essay, matching, fill_blank, numeric
    question_text: str
    question_html: Optional[str] = None
    question_media: Optional[List[dict]] = None
    options: Optional[List[QuestionOption]] = None  # For MCQ
    correct_answer: Optional[str] = None  # For non-MCQ
    answer_key: Optional[dict] = None
    points: float = 1.0
    difficulty: Optional[str] = None  # easy, medium, hard
    bloom_level: Optional[str] = None
    tags: Optional[List[str]] = None
    standard_ids: Optional[List[UUID]] = None
    is_shared: bool = False


class QuestionUpdate(BaseModel):
    """Update a question"""
    question_text: Optional[str] = None
    question_html: Optional[str] = None
    options: Optional[List[QuestionOption]] = None
    correct_answer: Optional[str] = None
    answer_key: Optional[dict] = None
    points: Optional[float] = None
    difficulty: Optional[str] = None
    bloom_level: Optional[str] = None
    tags: Optional[List[str]] = None
    standard_ids: Optional[List[UUID]] = None
    is_shared: Optional[bool] = None
    is_active: Optional[bool] = None


class QuestionResponse(BaseModel):
    """Question response"""
    id: UUID
    school_id: UUID
    teacher_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    question_type: str
    question_text: str
    options: Optional[List[dict]] = None
    points: float
    difficulty: Optional[str] = None
    tags: Optional[List[str]] = None
    times_used: int
    avg_score: Optional[float] = None


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("")
async def list_questions(
    subject_id: Optional[UUID] = None,
    grade_id: Optional[UUID] = None,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    include_shared: bool = True,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List questions from the question bank with filters"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # Build query - get own questions and shared questions
    query = supabase.table("question_bank").select(
        "*, subjects(name), grades(name)"
    ).eq("school_id", school_id).eq("is_active", True)

    if not include_shared:
        query = query.eq("teacher_id", user_id)

    if subject_id:
        query = query.eq("subject_id", str(subject_id))
    if grade_id:
        query = query.eq("grade_id", str(grade_id))
    if question_type:
        query = query.eq("question_type", question_type)
    if difficulty:
        query = query.eq("difficulty", difficulty)
    if tag:
        query = query.contains("tags", [tag])
    if search:
        query = query.ilike("question_text", f"%{search}%")

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    return {
        "questions": result.data or [],
        "total": len(result.data) if result.data else 0,
        "limit": limit,
        "offset": offset
    }


@router.get("/{question_id}")
async def get_question(
    question_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get a specific question with full details"""
    result = supabase.table("question_bank").select(
        "*, subjects(name), grades(name)"
    ).eq("id", str(question_id)).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Question not found")

    return result.data


@router.post("", response_model=QuestionResponse)
async def create_question(
    question: QuestionCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new question in the question bank"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    # Validate question type specific requirements
    if question.question_type == "multiple_choice" and not question.options:
        raise HTTPException(status_code=400, detail="Multiple choice questions require options")

    if question.question_type == "true_false":
        # Auto-create true/false options
        question.options = [
            QuestionOption(id="true", text="True", is_correct=question.correct_answer == "true"),
            QuestionOption(id="false", text="False", is_correct=question.correct_answer == "false")
        ]

    question_data = {
        "school_id": school_id,
        "teacher_id": user_id,
        "subject_id": str(question.subject_id) if question.subject_id else None,
        "grade_id": str(question.grade_id) if question.grade_id else None,
        "question_type": question.question_type,
        "question_text": question.question_text,
        "question_html": question.question_html,
        "question_media": question.question_media,
        "options": [opt.dict() for opt in question.options] if question.options else None,
        "correct_answer": question.correct_answer,
        "answer_key": question.answer_key,
        "points": question.points,
        "difficulty": question.difficulty,
        "bloom_level": question.bloom_level,
        "tags": question.tags,
        "standard_ids": [str(s) for s in question.standard_ids] if question.standard_ids else None,
        "is_shared": question.is_shared,
        "is_active": True,
        "times_used": 0
    }

    result = supabase.table("question_bank").insert(question_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create question")

    return QuestionResponse(**result.data[0])


@router.put("/{question_id}")
async def update_question(
    question_id: UUID,
    update: QuestionUpdate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Update a question"""
    user_id = current_user["id"]

    # Check ownership
    existing = supabase.table("question_bank").select(
        "teacher_id"
    ).eq("id", str(question_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Question not found")

    if existing.data["teacher_id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own questions")

    update_data = {}
    if update.question_text is not None:
        update_data["question_text"] = update.question_text
    if update.question_html is not None:
        update_data["question_html"] = update.question_html
    if update.options is not None:
        update_data["options"] = [opt.dict() for opt in update.options]
    if update.correct_answer is not None:
        update_data["correct_answer"] = update.correct_answer
    if update.answer_key is not None:
        update_data["answer_key"] = update.answer_key
    if update.points is not None:
        update_data["points"] = update.points
    if update.difficulty is not None:
        update_data["difficulty"] = update.difficulty
    if update.bloom_level is not None:
        update_data["bloom_level"] = update.bloom_level
    if update.tags is not None:
        update_data["tags"] = update.tags
    if update.standard_ids is not None:
        update_data["standard_ids"] = [str(s) for s in update.standard_ids]
    if update.is_shared is not None:
        update_data["is_shared"] = update.is_shared
    if update.is_active is not None:
        update_data["is_active"] = update.is_active

    result = supabase.table("question_bank").update(
        update_data
    ).eq("id", str(question_id)).execute()

    return result.data[0] if result.data else None


@router.delete("/{question_id}")
async def delete_question(
    question_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Soft delete a question (set inactive)"""
    user_id = current_user["id"]

    # Check ownership
    existing = supabase.table("question_bank").select(
        "teacher_id"
    ).eq("id", str(question_id)).single().execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="Question not found")

    if existing.data["teacher_id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own questions")

    supabase.table("question_bank").update({
        "is_active": False
    }).eq("id", str(question_id)).execute()

    return {"success": True}


@router.post("/{question_id}/duplicate")
async def duplicate_question(
    question_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a copy of an existing question"""
    user_id = current_user["id"]
    school_id = current_user.get("school_id")

    # Get original question
    original = supabase.table("question_bank").select("*").eq(
        "id", str(question_id)
    ).single().execute()

    if not original.data:
        raise HTTPException(status_code=404, detail="Question not found")

    # Create copy
    new_question = {**original.data}
    del new_question["id"]
    del new_question["created_at"]
    del new_question["updated_at"]
    new_question["teacher_id"] = user_id
    new_question["school_id"] = school_id
    new_question["times_used"] = 0
    new_question["avg_score"] = None
    new_question["question_text"] = f"(Copy) {new_question['question_text']}"

    result = supabase.table("question_bank").insert(new_question).execute()

    return result.data[0] if result.data else None


@router.get("/stats/by-subject")
async def get_question_stats_by_subject(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get question bank statistics by subject"""
    school_id = current_user.get("school_id")

    # This would be better with a SQL function, but using client-side aggregation
    result = supabase.table("question_bank").select(
        "subject_id, question_type, difficulty"
    ).eq("school_id", school_id).eq("is_active", True).execute()

    questions = result.data or []

    # Aggregate stats
    stats = {}
    for q in questions:
        subject_id = q["subject_id"] or "uncategorized"
        if subject_id not in stats:
            stats[subject_id] = {
                "total": 0,
                "by_type": {},
                "by_difficulty": {}
            }

        stats[subject_id]["total"] += 1

        q_type = q["question_type"]
        stats[subject_id]["by_type"][q_type] = stats[subject_id]["by_type"].get(q_type, 0) + 1

        difficulty = q["difficulty"] or "unspecified"
        stats[subject_id]["by_difficulty"][difficulty] = stats[subject_id]["by_difficulty"].get(difficulty, 0) + 1

    return stats


@router.post("/import")
async def import_questions(
    questions: List[QuestionCreate],
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Bulk import questions"""
    school_id = current_user.get("school_id")
    user_id = current_user["id"]

    if not school_id:
        raise HTTPException(status_code=400, detail="School context required")

    questions_to_insert = []
    for q in questions:
        questions_to_insert.append({
            "school_id": school_id,
            "teacher_id": user_id,
            "subject_id": str(q.subject_id) if q.subject_id else None,
            "grade_id": str(q.grade_id) if q.grade_id else None,
            "question_type": q.question_type,
            "question_text": q.question_text,
            "options": [opt.dict() for opt in q.options] if q.options else None,
            "correct_answer": q.correct_answer,
            "points": q.points,
            "difficulty": q.difficulty,
            "tags": q.tags,
            "is_active": True,
            "times_used": 0
        })

    result = supabase.table("question_bank").insert(questions_to_insert).execute()

    return {
        "success": True,
        "imported": len(result.data) if result.data else 0
    }
