"""
Project ASTRA - Core Configuration
Phase-1 Review 1 (50% Implementation Milestone)
CHRIST (Deemed to be University), Department of CSE
"""

import os
from pathlib import Path
from typing import List
from pydantic import BaseModel


class Settings(BaseModel):
    # Service Metadata
    PROJECT_NAME: str = "Project ASTRA - Women's Travel Safety Assistant"
    PROJECT_ACRONYM: str = "ASTRA"
    STAGE: str = "Phase-1 Review 1 (50% Implementation Milestone)"
    INSTITUTION: str = "CHRIST (Deemed to be University), Department of CSE"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # CORS Configuration (Permissive for Android Emulators & Physical Devices)
    CORS_ORIGINS: List[str] = ["*"]

    # Model Configuration
    # Finds ml/risk_model.pkl relative to project root
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    MODEL_PATH: Path = BASE_DIR / "ml" / "risk_model.pkl"

    # Risk Engine Thresholds
    CRITICAL_RISK_CODE: int = 2
    MODERATE_RISK_CODE: int = 1
    SAFE_RISK_CODE: int = 0


settings = Settings()
