"""
EduCore Backend - FastAPI Application Entry Point
Multi-tenant School Management SaaS Platform
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.v1 import api_router
from app.db.supabase import init_supabase
from app.db.tenant import set_tenant, clear_tenant
from app.core.logging import setup_logging
from app.core.rate_limit import RateLimitMiddleware
from app.core.performance import PerformanceMiddleware


# Configure logging
logger = setup_logging("INFO" if not settings.DEBUG else "DEBUG")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_supabase()
    logger.info("Supabase clients initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-tenant School Management SaaS API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Rate Limiting Middleware
if not settings.DEBUG:
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

# Performance Monitoring
app.add_middleware(PerformanceMiddleware)


# Tenant Context Middleware
@app.middleware("http")
async def tenant_context_middleware(request: Request, call_next):
    """Extract and set tenant context from JWT for each request"""
    # Clear any existing tenant context
    clear_tenant()
    
    # Try to extract school_id from the authenticated user
    # This is handled by the security dependencies, but we can also
    # check for a custom header for service-to-service calls
    school_id = request.headers.get("X-School-ID")
    if school_id:
        set_tenant(school_id)
    
    response = await call_next(request)
    
    # Clear tenant context after request
    clear_tenant()
    
    return response


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True,
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else None,
        }
    )
    
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__},
        )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with logging"""
    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Include API routes
app.include_router(api_router)


# Explicit OPTIONS handler for CORS preflight
@app.options("/{full_path:path}")
async def options_handler():
    """Handle CORS preflight requests"""
    return {"status": "ok"}


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "Disabled in production",
    }
