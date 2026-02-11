"""Supabase client module - re-exports from supabase for backward compatibility"""
from app.db.supabase import (
    get_supabase_client,
    get_supabase_admin,
    supabase,
    supabase_admin,
    init_supabase,
)
