# api v1 module
from fastapi import APIRouter
from app.api.v1.telemetry import router as telemetry_router

api_router = APIRouter()
api_router.include_router(telemetry_router, prefix="/telemetry", tags=["Agent 1: Predictive Risk Engine"])

__all__ = ["api_router"]
