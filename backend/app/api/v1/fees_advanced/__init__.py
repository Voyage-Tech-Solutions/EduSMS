"""
EduCore Backend - Advanced Fee Management Module
Payment plans, scholarships, refunds, and financial reports
"""
from fastapi import APIRouter

from app.api.v1.fees_advanced.payment_plans import router as payment_plans_router
from app.api.v1.fees_advanced.scholarships import router as scholarships_router
from app.api.v1.fees_advanced.refunds import router as refunds_router
from app.api.v1.fees_advanced.financial_reports import router as reports_router

router = APIRouter()

router.include_router(payment_plans_router, prefix="/payment-plans", tags=["payment_plans"])
router.include_router(scholarships_router, prefix="/scholarships", tags=["scholarships"])
router.include_router(refunds_router, prefix="/refunds", tags=["refunds"])
router.include_router(reports_router, prefix="/financial-reports", tags=["financial_reports"])
