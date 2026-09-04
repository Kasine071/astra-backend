"""
Project ASTRA - AI-Powered Multi-Agent Women's Travel Safety Assistant
Phase-1 Review 1 (50% Implementation Milestone)
CHRIST (Deemed to be University), Department of CSE

Team:
- Kasine RS (GitHub: https://github.com/Kasine071 - Backend/ML Lead)
- Darshan R (GitHub: https://github.com/Drzxn - Android/Client Lead)

Core Microservice: Agent 1 (Predictive Risk Scoring) & Agent 4 (Evidence Trigger Pipeline)
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1 import api_router
from app.services.risk_engine import risk_engine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("astra.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown handler."""
    logger.info("Initializing Project ASTRA Backend microservice...")
    loaded = risk_engine.load_model()
    if loaded:
        logger.info("ML Risk Model (Agent 1) loaded and warmed up successfully.")
    else:
        logger.warning("ML Risk Model could not be loaded. Operating on safety heuristic fallback rules.")
    yield
    logger.info("Shutting down Project ASTRA Backend microservice.")


app = FastAPI(
    title="Project ASTRA - Travel Safety Intelligence API",
    description="""
    ## Project ASTRA: AI-Powered Multi-Agent Women's Travel Safety Assistant
    **Academic Stage:** Phase-1 Review 1 (50% Implementation Milestone)  
    **Institution:** CHRIST (Deemed to be University), Department of CSE  
    **Team:** Kasine RS (Backend/ML Lead) & Darshan R (Android/Client Lead)  

    ---
    ### Implemented Architecture Components:
    * **Agent 1 (Predictive Risk Scoring):** Real-time multi-class classification (`Safe`, `Moderate`, `Critical`) based on GPS deviation, dwell time, velocity, and temporal features.
    * **Agent 4 (Evidence Trigger Pipeline):** Automated threshold trigger activating multimedia evidence capture on Android when Critical risk (`risk_code == 2`) is detected.
    * **Android Telemetry Stream Interface:** Seamless integration contract for Darshan's Android ForegroundService.
    """,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for all origins (permits Android Emulator 10.0.2.2 & Physical Device Wi-Fi IPs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Diagnostic"], summary="Root Information Endpoint")
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "acronym": settings.PROJECT_ACRONYM,
        "institution": settings.INSTITUTION,
        "stage": settings.STAGE,
        "team": {
            "backend_ml_lead": "Kasine RS (https://github.com/Kasine071)",
            "android_client_lead": "Darshan R (https://github.com/Drzxn)"
        },
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "telemetry_risk_scoring": f"{settings.API_V1_STR}/telemetry/score"
        },
        "status": "online"
    }


@app.get("/health", tags=["Diagnostic"], summary="System Health Check")
async def health_check():
    model_active = risk_engine.model is not None
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "astra-backend",
            "agent_1_risk_engine": "active" if model_active else "fallback_mode",
            "agent_4_trigger_pipeline": "enabled",
            "model_path": str(settings.MODEL_PATH),
            "model_loaded": model_active
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
