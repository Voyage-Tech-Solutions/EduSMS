"""
EduCore Backend - Quiz Attempts API
Track and manage student quiz attempts and submissions
"""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import random

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# MODELS
# ============================================================

class StartAttemptRequest(BaseModel):
    """Start a quiz attempt"""
    assessment_id: UUID


class AnswerSubmission(BaseModel):
    """Submit answer for a question"""
    question_id: UUID
    answer: Any  # Can be string, list, dict depending on question type
    time_spent_seconds: int = 0


class AttemptSubmission(BaseModel):
    """Submit entire attempt"""
    answers: Dict[str, Any]  # question_id -> answer
    time_spent_seconds: int


class ManualGradeRequest(BaseModel):
    """Grade a manual-review question"""
    question_id: UUID
    score: float
    feedback: Optional[str] = None


class AttemptResponse(BaseModel):
    """Quiz attempt response"""
    id: UUID
    assessment_id: UUID
    student_id: UUID
    attempt_number: int
    started_at: datetime
    submitted_at: Optional[datetime] = None
    auto_score: Optional[float] = None
    final_score: Optional[float] = None
    status: str  # in_progress, submitted, graded


# ============================================================
# STUDENT ENDPOINTS
# ============================================================

@router.post("/start")
async def start_attempt(
    request: StartAttemptRequest,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Start a new quiz attempt"""
    user_id = current_user["id"]

    # Get student record
    student = supabase.table("students").select("id").eq(
        "user_id", user_id
    ).single().execute()

    if not student.data:
        raise HTTPException(status_code=403, detail="Only students can take quizzes")

    student_id = student.data["id"]

    # Get quiz details
    quiz = supabase.table("assessments").select(
        "*, quiz_configs(*)"
    ).eq("id", str(request.assessment_id)).single().execute()

    if not quiz.data:
        raise HTTPException(status_code=404, detail="Quiz not found")

    quiz_data = quiz.data

    # Check if published
    if not quiz_data.get("is_published"):
        raise HTTPException(status_code=400, detail="Quiz is not available")

    # Check availability dates
    now = datetime.utcnow()
    if quiz_data.get("available_from"):
        available_from = datetime.fromisoformat(quiz_data["available_from"].replace("Z", ""))
        if now < available_from:
            raise HTTPException(status_code=400, detail="Quiz is not yet available")

    if quiz_data.get("available_until"):
        available_until = datetime.fromisoformat(quiz_data["available_until"].replace("Z", ""))
        if now > available_until:
            raise HTTPException(status_code=400, detail="Quiz is no longer available")

    # Check existing attempts
    existing_attempts = supabase.table("quiz_attempts").select(
        "id, attempt_number, submitted_at"
    ).eq("assessment_id", str(request.assessment_id)).eq(
        "student_id", student_id
    ).order("attempt_number", desc=True).execute()

    attempts = existing_attempts.data or []

    # Check for in-progress attempt
    for attempt in attempts:
        if not attempt.get("submitted_at"):
            # Resume existing attempt
            return {
                "attempt_id": attempt["id"],
                "resumed": True,
                "questions": await _get_attempt_questions(
                    supabase, str(request.assessment_id), quiz_data.get("quiz_configs")
                )
            }

    # Check retake limits
    config = quiz_data.get("quiz_configs") or {}
    max_attempts = config.get("allow_retakes", 0) + 1

    if len(attempts) >= max_attempts:
        raise HTTPException(status_code=400, detail="Maximum attempts reached")

    # Create new attempt
    attempt_number = len(attempts) + 1

    attempt_data = {
        "assessment_id": str(request.assessment_id),
        "student_id": student_id,
        "attempt_number": attempt_number,
        "started_at": datetime.utcnow().isoformat(),
        "answers": {},
        "status": "in_progress"
    }

    result = supabase.table("quiz_attempts").insert(attempt_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to start attempt")

    # Get questions
    questions = await _get_attempt_questions(
        supabase, str(request.assessment_id), config
    )

    return {
        "attempt_id": result.data[0]["id"],
        "attempt_number": attempt_number,
        "time_limit_minutes": config.get("time_limit_minutes"),
        "questions": questions,
        "total_points": quiz_data.get("total_points", 0)
    }


@router.post("/{attempt_id}/answer")
async def save_answer(
    attempt_id: UUID,
    answer: AnswerSubmission,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Save answer for a question (auto-save)"""
    user_id = current_user["id"]

    # Get student
    student = supabase.table("students").select("id").eq(
        "user_id", user_id
    ).single().execute()

    if not student.data:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get attempt
    attempt = supabase.table("quiz_attempts").select(
        "student_id, answers, submitted_at"
    ).eq("id", str(attempt_id)).single().execute()

    if not attempt.data:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.data["student_id"] != student.data["id"]:
        raise HTTPException(status_code=403, detail="Not your attempt")

    if attempt.data.get("submitted_at"):
        raise HTTPException(status_code=400, detail="Attempt already submitted")

    # Update answer
    answers = attempt.data.get("answers") or {}
    answers[str(answer.question_id)] = {
        "answer": answer.answer,
        "time_spent": answer.time_spent_seconds,
        "saved_at": datetime.utcnow().isoformat()
    }

    supabase.table("quiz_attempts").update({
        "answers": answers
    }).eq("id", str(attempt_id)).execute()

    return {"success": True}


@router.post("/{attempt_id}/submit")
async def submit_attempt(
    attempt_id: UUID,
    submission: AttemptSubmission,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Submit quiz attempt for grading"""
    user_id = current_user["id"]

    # Get student
    student = supabase.table("students").select("id").eq(
        "user_id", user_id
    ).single().execute()

    if not student.data:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get attempt
    attempt = supabase.table("quiz_attempts").select(
        "*, assessments(total_points, quiz_configs(*))"
    ).eq("id", str(attempt_id)).single().execute()

    if not attempt.data:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.data["student_id"] != student.data["id"]:
        raise HTTPException(status_code=403, detail="Not your attempt")

    if attempt.data.get("submitted_at"):
        raise HTTPException(status_code=400, detail="Attempt already submitted")

    # Merge answers
    current_answers = attempt.data.get("answers") or {}
    for qid, answer in submission.answers.items():
        current_answers[qid] = {
            "answer": answer,
            "saved_at": datetime.utcnow().isoformat()
        }

    # Calculate auto-score
    auto_score, needs_manual = await _calculate_auto_score(
        supabase, attempt.data["assessment_id"], current_answers
    )

    # Calculate final score (apply retake penalty if applicable)
    config = attempt.data.get("assessments", {}).get("quiz_configs") or {}
    penalty = config.get("retake_penalty_percent", 0)
    attempt_number = attempt.data.get("attempt_number", 1)

    final_score = auto_score
    if attempt_number > 1 and penalty > 0:
        penalty_multiplier = 1 - (penalty * (attempt_number - 1) / 100)
        final_score = auto_score * max(0, penalty_multiplier)

    # Update attempt
    update_data = {
        "answers": current_answers,
        "submitted_at": datetime.utcnow().isoformat(),
        "time_spent_seconds": submission.time_spent_seconds,
        "auto_score": auto_score,
        "status": "needs_grading" if needs_manual else "graded"
    }

    if not needs_manual:
        update_data["final_score"] = final_score
        update_data["manual_score"] = auto_score

    supabase.table("quiz_attempts").update(update_data).eq("id", str(attempt_id)).execute()

    # Get release settings
    show_results = config.get("release_scores_immediately", True)

    response = {
        "success": True,
        "submitted_at": update_data["submitted_at"],
        "status": update_data["status"]
    }

    if show_results and not needs_manual:
        response["score"] = final_score
        response["total_points"] = attempt.data.get("assessments", {}).get("total_points", 0)
        response["percentage"] = (final_score / response["total_points"] * 100) if response["total_points"] > 0 else 0

    if needs_manual:
        response["message"] = "Some questions require manual grading"

    return response


@router.get("/{attempt_id}")
async def get_attempt(
    attempt_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get attempt details"""
    user_id = current_user["id"]
    role = current_user.get("role")

    # Get attempt
    attempt = supabase.table("quiz_attempts").select(
        "*, students(first_name, last_name), assessments(title, total_points, created_by, quiz_configs(*))"
    ).eq("id", str(attempt_id)).single().execute()

    if not attempt.data:
        raise HTTPException(status_code=404, detail="Attempt not found")

    # Check access
    if role == "student":
        student = supabase.table("students").select("id").eq(
            "user_id", user_id
        ).single().execute()

        if not student.data or attempt.data["student_id"] != student.data["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
    elif role == "teacher":
        if attempt.data.get("assessments", {}).get("created_by") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

    return attempt.data


@router.get("/{attempt_id}/review")
async def get_attempt_review(
    attempt_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get detailed attempt review with answers and correct answers"""
    user_id = current_user["id"]
    role = current_user.get("role")

    # Get attempt
    attempt = supabase.table("quiz_attempts").select(
        "*, assessments(*, quiz_configs(*))"
    ).eq("id", str(attempt_id)).single().execute()

    if not attempt.data:
        raise HTTPException(status_code=404, detail="Attempt not found")

    # Check if review is allowed
    config = attempt.data.get("assessments", {}).get("quiz_configs") or {}
    show_answers = config.get("show_correct_answers", False)
    show_after = config.get("show_correct_answers_after", "immediately")

    is_teacher = role == "teacher" and attempt.data.get("assessments", {}).get("created_by") == user_id

    if not is_teacher:
        # Check student access
        student = supabase.table("students").select("id").eq(
            "user_id", user_id
        ).single().execute()

        if not student.data or attempt.data["student_id"] != student.data["id"]:
            raise HTTPException(status_code=403, detail="Access denied")

        if not show_answers:
            raise HTTPException(status_code=403, detail="Review not available")

        if show_after == "after_due_date":
            due_date = attempt.data.get("assessments", {}).get("due_date")
            if due_date:
                due = datetime.fromisoformat(due_date.replace("Z", ""))
                if datetime.utcnow() < due:
                    raise HTTPException(status_code=403, detail="Review available after due date")

    # Get questions with correct answers
    questions = supabase.table("assessment_questions").select(
        "*, question_bank(question_text, question_type, options, correct_answer, answer_key)"
    ).eq("assessment_id", attempt.data["assessment_id"]).order("order_index").execute()

    student_answers = attempt.data.get("answers") or {}

    review_data = []
    for q in (questions.data or []):
        question = q.get("question_bank", {})
        qid = q.get("question_id")

        student_answer = student_answers.get(qid, {}).get("answer")

        item = {
            "question_id": qid,
            "question_text": question.get("question_text"),
            "question_type": question.get("question_type"),
            "points": q.get("points", 1),
            "student_answer": student_answer,
            "options": question.get("options") if is_teacher or show_answers else None
        }

        if is_teacher or show_answers:
            item["correct_answer"] = question.get("correct_answer")
            item["is_correct"] = _check_answer(
                question.get("question_type"),
                student_answer,
                question.get("correct_answer"),
                question.get("options"),
                question.get("answer_key")
            )

        review_data.append(item)

    return {
        "attempt": {
            "id": attempt.data["id"],
            "submitted_at": attempt.data.get("submitted_at"),
            "auto_score": attempt.data.get("auto_score"),
            "final_score": attempt.data.get("final_score"),
            "total_points": attempt.data.get("assessments", {}).get("total_points")
        },
        "questions": review_data
    }


# ============================================================
# TEACHER ENDPOINTS
# ============================================================

@router.get("/quiz/{assessment_id}/all")
async def get_all_attempts(
    assessment_id: UUID,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get all attempts for a quiz (teacher only)"""
    user_id = current_user["id"]

    # Check ownership
    quiz = supabase.table("assessments").select(
        "created_by"
    ).eq("id", str(assessment_id)).single().execute()

    if not quiz.data:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if quiz.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get attempts
    query = supabase.table("quiz_attempts").select(
        "*, students(first_name, last_name, student_number)"
    ).eq("assessment_id", str(assessment_id))

    if status:
        query = query.eq("status", status)

    result = query.order("submitted_at", desc=True).execute()

    return {
        "attempts": result.data or [],
        "total": len(result.data) if result.data else 0
    }


@router.post("/{attempt_id}/grade")
async def grade_attempt(
    attempt_id: UUID,
    grades: List[ManualGradeRequest],
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Manually grade questions in an attempt"""
    user_id = current_user["id"]

    # Get attempt
    attempt = supabase.table("quiz_attempts").select(
        "*, assessments(created_by, total_points)"
    ).eq("id", str(attempt_id)).single().execute()

    if not attempt.data:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.data.get("assessments", {}).get("created_by") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get current answers
    answers = attempt.data.get("answers") or {}

    # Apply grades
    manual_total = 0
    for grade in grades:
        qid = str(grade.question_id)
        if qid in answers:
            answers[qid]["manual_score"] = grade.score
            answers[qid]["feedback"] = grade.feedback
        else:
            answers[qid] = {
                "manual_score": grade.score,
                "feedback": grade.feedback
            }
        manual_total += grade.score

    # Recalculate total score
    auto_score = attempt.data.get("auto_score") or 0

    # Get auto-graded questions total
    questions = supabase.table("assessment_questions").select(
        "question_id, points, question_bank(question_type)"
    ).eq("assessment_id", attempt.data["assessment_id"]).execute()

    auto_graded_points = 0
    for q in (questions.data or []):
        qtype = q.get("question_bank", {}).get("question_type")
        if qtype in ["multiple_choice", "true_false", "numeric"]:
            auto_graded_points += q.get("points", 0)

    # Final score = auto_score + manual grades
    final_score = auto_score + manual_total

    # Update attempt
    supabase.table("quiz_attempts").update({
        "answers": answers,
        "manual_score": manual_total,
        "final_score": final_score,
        "status": "graded",
        "graded_at": datetime.utcnow().isoformat(),
        "graded_by": user_id
    }).eq("id", str(attempt_id)).execute()

    return {
        "success": True,
        "final_score": final_score,
        "total_points": attempt.data.get("assessments", {}).get("total_points", 0)
    }


@router.get("/quiz/{assessment_id}/stats")
async def get_quiz_statistics(
    assessment_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get detailed statistics for a quiz"""
    user_id = current_user["id"]

    # Check ownership
    quiz = supabase.table("assessments").select(
        "created_by, total_points"
    ).eq("id", str(assessment_id)).single().execute()

    if not quiz.data:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if quiz.data["created_by"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    total_points = quiz.data.get("total_points", 100)

    # Get all attempts
    attempts = supabase.table("quiz_attempts").select(
        "final_score, submitted_at, answers"
    ).eq("assessment_id", str(assessment_id)).not_.is_("submitted_at", "null").execute()

    if not attempts.data:
        return {
            "total_attempts": 0,
            "average_score": 0,
            "median_score": 0,
            "highest_score": 0,
            "lowest_score": 0,
            "pass_rate": 0,
            "grade_distribution": {},
            "question_analysis": []
        }

    scores = [a["final_score"] for a in attempts.data if a.get("final_score") is not None]

    if not scores:
        return {
            "total_attempts": len(attempts.data),
            "graded_attempts": 0,
            "pending_grading": len(attempts.data)
        }

    # Calculate statistics
    avg_score = sum(scores) / len(scores)
    sorted_scores = sorted(scores)
    median_score = sorted_scores[len(sorted_scores) // 2]

    # Grade distribution
    distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for score in scores:
        pct = (score / total_points) * 100 if total_points > 0 else 0
        if pct >= 90:
            distribution["A"] += 1
        elif pct >= 80:
            distribution["B"] += 1
        elif pct >= 70:
            distribution["C"] += 1
        elif pct >= 60:
            distribution["D"] += 1
        else:
            distribution["F"] += 1

    # Question-level analysis
    questions = supabase.table("assessment_questions").select(
        "question_id, points, question_bank(question_text, question_type)"
    ).eq("assessment_id", str(assessment_id)).execute()

    question_stats = []
    for q in (questions.data or []):
        qid = q["question_id"]
        correct_count = 0
        total_responses = 0

        for attempt in attempts.data:
            answers = attempt.get("answers") or {}
            if qid in answers:
                total_responses += 1
                # Check if correct (simplified)
                answer_data = answers[qid]
                if isinstance(answer_data, dict) and answer_data.get("manual_score"):
                    if answer_data["manual_score"] > 0:
                        correct_count += 1

        question_stats.append({
            "question_id": qid,
            "question_text": q.get("question_bank", {}).get("question_text", "")[:100],
            "question_type": q.get("question_bank", {}).get("question_type"),
            "total_responses": total_responses,
            "correct_rate": (correct_count / total_responses * 100) if total_responses > 0 else 0
        })

    return {
        "total_attempts": len(attempts.data),
        "graded_attempts": len(scores),
        "average_score": round(avg_score, 2),
        "average_percentage": round((avg_score / total_points) * 100, 1) if total_points > 0 else 0,
        "median_score": median_score,
        "highest_score": max(scores),
        "lowest_score": min(scores),
        "pass_rate": round(len([s for s in scores if (s / total_points) >= 0.6]) / len(scores) * 100, 1) if scores else 0,
        "grade_distribution": distribution,
        "question_analysis": question_stats
    }


# ============================================================
# HELPER FUNCTIONS
# ============================================================

async def _get_attempt_questions(supabase, assessment_id: str, config: dict = None):
    """Get questions for an attempt, applying shuffling if configured"""
    questions = supabase.table("assessment_questions").select(
        "question_id, order_index, points, question_bank(question_text, question_type, options, question_html, question_media)"
    ).eq("assessment_id", assessment_id).order("order_index").execute()

    question_list = []
    for q in (questions.data or []):
        question = q.get("question_bank", {})
        item = {
            "question_id": q["question_id"],
            "question_text": question.get("question_text"),
            "question_html": question.get("question_html"),
            "question_type": question.get("question_type"),
            "points": q.get("points", 1),
            "options": question.get("options"),
            "media": question.get("question_media")
        }

        # Shuffle options if configured
        if config and config.get("shuffle_options") and item["options"]:
            options = item["options"].copy()
            random.shuffle(options)
            item["options"] = options

        # Remove correct answer indicators from options for students
        if item["options"]:
            item["options"] = [
                {"id": opt.get("id"), "text": opt.get("text")}
                for opt in item["options"]
            ]

        question_list.append(item)

    # Shuffle questions if configured
    if config and config.get("shuffle_questions"):
        random.shuffle(question_list)

    return question_list


async def _calculate_auto_score(supabase, assessment_id: str, answers: dict):
    """Calculate auto-score for auto-gradable questions"""
    questions = supabase.table("assessment_questions").select(
        "question_id, points, question_bank(question_type, correct_answer, options, answer_key)"
    ).eq("assessment_id", assessment_id).execute()

    total_score = 0
    needs_manual = False

    for q in (questions.data or []):
        qid = q["question_id"]
        question = q.get("question_bank", {})
        qtype = question.get("question_type")
        points = q.get("points", 1)

        student_answer = answers.get(qid, {})
        if isinstance(student_answer, dict):
            student_answer = student_answer.get("answer")

        if qtype in ["essay", "short_answer"]:
            needs_manual = True
            continue

        is_correct = _check_answer(
            qtype,
            student_answer,
            question.get("correct_answer"),
            question.get("options"),
            question.get("answer_key")
        )

        if is_correct:
            total_score += points

    return total_score, needs_manual


def _check_answer(question_type: str, student_answer, correct_answer, options=None, answer_key=None) -> bool:
    """Check if student answer is correct"""
    if student_answer is None:
        return False

    if question_type == "multiple_choice":
        # For MCQ, correct answer might be in options
        if options:
            for opt in options:
                if opt.get("is_correct") and opt.get("id") == student_answer:
                    return True
            return False
        return str(student_answer).lower() == str(correct_answer).lower()

    elif question_type == "true_false":
        return str(student_answer).lower() == str(correct_answer).lower()

    elif question_type == "numeric":
        try:
            student_val = float(student_answer)
            correct_val = float(correct_answer)
            # Allow small tolerance
            return abs(student_val - correct_val) < 0.001
        except (ValueError, TypeError):
            return False

    elif question_type == "matching":
        if isinstance(answer_key, dict) and isinstance(student_answer, dict):
            return answer_key == student_answer
        return False

    elif question_type == "fill_blank":
        if isinstance(correct_answer, list):
            return str(student_answer).lower().strip() in [str(a).lower().strip() for a in correct_answer]
        return str(student_answer).lower().strip() == str(correct_answer).lower().strip()

    return False
