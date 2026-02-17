"""
EduCore Backend - Backup & Restore API
Data backup and restore functionality
"""
import logging
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel

from app.api.deps import get_current_user, get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


class BackupType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    SELECTIVE = "selective"


class BackupStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class BackupRequest(BaseModel):
    """Request to create a backup"""
    backup_type: BackupType = BackupType.FULL
    description: Optional[str] = None
    include_files: bool = True
    tables: Optional[list] = None  # For selective backup


class ScheduledBackupCreate(BaseModel):
    """Create scheduled backup"""
    schedule: str  # daily, weekly, monthly
    time: str = "02:00"  # 24-hour format
    day_of_week: Optional[int] = None  # 0-6 for weekly
    day_of_month: Optional[int] = None  # 1-28 for monthly
    backup_type: BackupType = BackupType.FULL
    retention_days: int = 30


# ============================================================
# BACKUP OPERATIONS
# ============================================================

@router.post("/create")
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a new backup"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    user_role = current_user.get("role")

    if user_role not in ["system_admin", "school_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Create backup record
    backup_data = {
        "school_id": school_id,
        "created_by": user_id,
        "backup_type": request.backup_type.value,
        "description": request.description,
        "include_files": request.include_files,
        "tables": request.tables,
        "status": BackupStatus.PENDING.value,
        "started_at": datetime.utcnow().isoformat()
    }

    result = supabase.table("backups").insert(backup_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create backup")

    backup_id = result.data[0]["id"]

    # Start backup in background
    background_tasks.add_task(
        _perform_backup,
        backup_id,
        request,
        school_id,
        supabase
    )

    return {
        "backup_id": backup_id,
        "status": "pending",
        "message": "Backup started"
    }


async def _perform_backup(backup_id: str, request: BackupRequest, school_id: str, supabase):
    """Background task to perform backup"""
    try:
        # Update status
        supabase.table("backups").update({
            "status": BackupStatus.IN_PROGRESS.value
        }).eq("id", backup_id).execute()

        # Determine tables to backup
        if request.backup_type == BackupType.SELECTIVE and request.tables:
            tables = request.tables
        else:
            tables = [
                "students", "teachers", "classes", "grades", "attendance",
                "fee_records", "payments", "user_profiles", "announcements",
                "messages", "assignments", "submissions"
            ]

        # Collect data
        backup_data = {}
        record_count = 0

        for table in tables:
            try:
                result = supabase.table(table).select("*").eq("school_id", school_id).execute()
                backup_data[table] = result.data or []
                record_count += len(result.data or [])
            except Exception as e:
                logger.error(f"Error backing up table {table}: {e}")
                backup_data[table] = {"error": str(e)}

        # In production, would upload to S3/storage
        # For now, store metadata
        file_size = len(str(backup_data))  # Simplified

        supabase.table("backups").update({
            "status": BackupStatus.COMPLETED.value,
            "completed_at": datetime.utcnow().isoformat(),
            "record_count": record_count,
            "file_size_bytes": file_size,
            "file_url": f"/api/v1/system/backup/{backup_id}/download"
        }).eq("id", backup_id).execute()

    except Exception as e:
        logger.error(f"Backup failed: {e}")
        supabase.table("backups").update({
            "status": BackupStatus.FAILED.value,
            "error": str(e)
        }).eq("id", backup_id).execute()


@router.get("")
async def list_backups(
    status: Optional[BackupStatus] = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List backups"""
    school_id = current_user.get("school_id")
    user_role = current_user.get("role")

    if user_role not in ["system_admin", "school_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    query = supabase.table("backups").select(
        "*, creator:created_by(first_name, last_name)"
    ).eq("school_id", school_id)

    if status:
        query = query.eq("status", status.value)

    query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

    result = query.execute()

    return {"backups": result.data or []}


@router.get("/{backup_id}")
async def get_backup(
    backup_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get backup details"""
    result = supabase.table("backups").select("*").eq(
        "id", str(backup_id)
    ).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Backup not found")

    return result.data


@router.get("/{backup_id}/download")
async def download_backup(
    backup_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Download backup file"""
    user_role = current_user.get("role")

    if user_role not in ["system_admin", "school_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    backup = supabase.table("backups").select("status, file_url").eq(
        "id", str(backup_id)
    ).single().execute()

    if not backup.data:
        raise HTTPException(status_code=404, detail="Backup not found")

    if backup.data["status"] != BackupStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Backup not ready for download")

    # In production, return pre-signed S3 URL
    return {"download_url": backup.data.get("file_url"), "expires_in": 3600}


@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a backup"""
    user_role = current_user.get("role")

    if user_role not in ["system_admin"]:
        raise HTTPException(status_code=403, detail="System admin access required")

    supabase.table("backups").delete().eq("id", str(backup_id)).execute()

    return {"success": True}


# ============================================================
# RESTORE OPERATIONS
# ============================================================

@router.post("/{backup_id}/restore")
async def restore_backup(
    backup_id: UUID,
    tables: Optional[list] = None,
    overwrite: bool = False,
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Restore from a backup"""
    user_role = current_user.get("role")

    if user_role not in ["system_admin"]:
        raise HTTPException(status_code=403, detail="System admin access required")

    # Verify backup exists and is completed
    backup = supabase.table("backups").select("status").eq(
        "id", str(backup_id)
    ).single().execute()

    if not backup.data:
        raise HTTPException(status_code=404, detail="Backup not found")

    if backup.data["status"] != BackupStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Backup not in completed state")

    # Create restore job
    restore_data = {
        "backup_id": str(backup_id),
        "restored_by": current_user.get("id"),
        "tables": tables,
        "overwrite": overwrite,
        "status": "pending"
    }

    result = supabase.table("restore_jobs").insert(restore_data).execute()

    # In production, would queue background job
    return {
        "restore_id": result.data[0]["id"] if result.data else None,
        "status": "pending",
        "message": "Restore job queued. This may take several minutes."
    }


@router.get("/restore/{restore_id}/status")
async def get_restore_status(
    restore_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get restore job status"""
    result = supabase.table("restore_jobs").select("*").eq(
        "id", str(restore_id)
    ).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Restore job not found")

    return result.data


# ============================================================
# SCHEDULED BACKUPS
# ============================================================

@router.get("/scheduled")
async def list_scheduled_backups(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """List scheduled backups"""
    school_id = current_user.get("school_id")

    result = supabase.table("scheduled_backups").select("*").eq(
        "school_id", school_id
    ).eq("is_active", True).execute()

    return {"scheduled_backups": result.data or []}


@router.post("/scheduled")
async def create_scheduled_backup(
    schedule: ScheduledBackupCreate,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Create a scheduled backup"""
    school_id = current_user.get("school_id")
    user_id = current_user.get("id")
    user_role = current_user.get("role")

    if user_role not in ["system_admin", "school_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    schedule_data = {
        "school_id": school_id,
        "created_by": user_id,
        "schedule": schedule.schedule,
        "time": schedule.time,
        "day_of_week": schedule.day_of_week,
        "day_of_month": schedule.day_of_month,
        "backup_type": schedule.backup_type.value,
        "retention_days": schedule.retention_days,
        "is_active": True
    }

    result = supabase.table("scheduled_backups").insert(schedule_data).execute()

    return result.data[0] if result.data else None


@router.delete("/scheduled/{schedule_id}")
async def delete_scheduled_backup(
    schedule_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Delete a scheduled backup"""
    supabase.table("scheduled_backups").update({
        "is_active": False
    }).eq("id", str(schedule_id)).execute()

    return {"success": True}


# ============================================================
# BACKUP STATISTICS
# ============================================================

@router.get("/stats")
async def get_backup_stats(
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase)
):
    """Get backup statistics"""
    school_id = current_user.get("school_id")

    # Get all backups
    backups = supabase.table("backups").select(
        "status, file_size_bytes, created_at"
    ).eq("school_id", school_id).execute()

    all_backups = backups.data or []

    # Calculate stats
    total_backups = len(all_backups)
    successful = sum(1 for b in all_backups if b.get("status") == "completed")
    failed = sum(1 for b in all_backups if b.get("status") == "failed")
    total_size = sum(b.get("file_size_bytes", 0) for b in all_backups)

    # Last backup
    last_backup = None
    completed_backups = [b for b in all_backups if b.get("status") == "completed"]
    if completed_backups:
        last_backup = max(completed_backups, key=lambda x: x.get("created_at", ""))

    # Next scheduled
    scheduled = supabase.table("scheduled_backups").select(
        "schedule, time"
    ).eq("school_id", school_id).eq("is_active", True).limit(1).execute()

    return {
        "total_backups": total_backups,
        "successful": successful,
        "failed": failed,
        "total_storage_bytes": total_size,
        "total_storage_mb": round(total_size / (1024 * 1024), 2),
        "last_successful_backup": last_backup.get("created_at") if last_backup else None,
        "next_scheduled": scheduled.data[0] if scheduled.data else None
    }
