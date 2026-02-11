"""
EduCore Backend - Supabase Client
"""
from supabase import create_client, Client
from app.core.config import settings


def get_supabase_client() -> Client:
    """Get Supabase client with anon key (for user-context operations)"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


def get_supabase_admin() -> Client:
    """Get Supabase client with service role key (for admin operations)"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


# Singleton instances
supabase: Client = None
supabase_admin: Client = None


def init_supabase():
    """Initialize Supabase clients"""
    global supabase, supabase_admin
    if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
        supabase = get_supabase_client()
    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
        supabase_admin = get_supabase_admin()
