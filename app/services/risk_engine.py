"""
Project ASTRA - Risk Scoring Engine (Agent 1 & Agent 4 Trigger Pipeline)
Phase-1 Review 1 (50% Implementation Milestone)
CHRIST (Deemed to be University), Department of CSE
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
import joblib
import numpy as np
import pandas as pd

from app.core.config import settings
from app.schemas.telemetry import TelemetryInput, RiskScoreResponse

logger = logging.getLogger("astra.risk_engine")


class RiskScoringEngine:
    """
    Inference service for Agent 1 (Predictive Risk Scoring).
    Wraps the trained RandomForest model, produces class probabilities,
    and controls the trigger for Agent 4 (Evidence Capture).
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or settings.MODEL_PATH
        self.model: Optional[Any] = None
        self.feature_names = [
            "route_deviation_meters",
            "stop_duration_seconds",
            "speed_kmh",
            "hour_of_day"
        ]
        self.label_map = {
            0: "Safe",
            1: "Moderate",
            2: "Critical"
        }
        self.load_model()

    def load_model(self) -> bool:
        """Loads the serialized model artifact into memory."""
        try:
            if self.model_path.exists():
                artifact = joblib.load(self.model_path)
                if isinstance(artifact, dict) and "model" in artifact:
                    self.model = artifact["model"]
                    self.feature_names = artifact.get("feature_names", self.feature_names)
                    self.label_map = artifact.get("class_labels", self.label_map)
                else:
                    self.model = artifact
                logger.info(f"Successfully loaded risk model artifact from {self.model_path}")
                return True
            else:
                logger.warning(f"Model file not found at {self.model_path}. Fallback heuristic rules will be active.")
                return False
        except Exception as e:
            logger.error(f"Error loading model from {self.model_path}: {e}. Falling back to heuristic rules.")
            self.model = None
            return False

    def _fallback_heuristic_score(self, telemetry: TelemetryInput) -> Dict[str, Any]:
        """
        Rule-based safety fallback used if the ML model is unavailable
        or for safety verification.
        """
        # Critical conditions: High deviation + long stop or midnight deviation
        is_night = telemetry.hour_of_day >= 22 or telemetry.hour_of_day <= 5
        
        if (telemetry.deviation_meters > 180 and telemetry.stop_duration_seconds > 240) or \
           (is_night and telemetry.deviation_meters > 200 and telemetry.speed_kmh < 10) or \
           (telemetry.deviation_meters > 400):
            risk_code = 2
            confidence = 0.95
        elif (telemetry.deviation_meters > 40 or telemetry.stop_duration_seconds > 120 or (is_night and telemetry.deviation_meters > 25)):
            risk_code = 1
            confidence = 0.85
        else:
            risk_code = 0
            confidence = 0.90

        return {
            "risk_code": risk_code,
            "risk_level": self.label_map[risk_code],
            "confidence": confidence
        }

    def score_telemetry(self, telemetry: TelemetryInput) -> RiskScoreResponse:
        """
        Takes raw telemetry input from Android client, executes inference,
        and returns structured risk classification.
        """
        if self.model is not None:
            try:
                # Prepare DataFrame with explicit feature column names to avoid sklearn warnings
                input_df = pd.DataFrame([{
                    "route_deviation_meters": telemetry.deviation_meters,
                    "stop_duration_seconds": telemetry.stop_duration_seconds,
                    "speed_kmh": telemetry.speed_kmh,
                    "hour_of_day": telemetry.hour_of_day
                }])[self.feature_names]

                # Run prediction
                pred_code = int(self.model.predict(input_df)[0])
                probabilities = self.model.predict_proba(input_df)[0]
                confidence = float(probabilities[pred_code])

                risk_level = self.label_map.get(pred_code, "Safe")
                risk_code = pred_code
            except Exception as e:
                logger.error(f"Inference error with ML model: {e}. Utilizing heuristic fallback.")
                fallback = self._fallback_heuristic_score(telemetry)
                risk_code = fallback["risk_code"]
                risk_level = fallback["risk_level"]
                confidence = fallback["confidence"]
        else:
            fallback = self._fallback_heuristic_score(telemetry)
            risk_code = fallback["risk_code"]
            risk_level = fallback["risk_level"]
            confidence = fallback["confidence"]

        # Agent 4 Pipeline Trigger Rule:
        # If risk_code == 2 (Critical), activate evidence capture trigger for Android
        trigger_evidence = (risk_code == settings.CRITICAL_RISK_CODE)

        return RiskScoreResponse(
            status="success",
            user_id=telemetry.user_id,
            risk_level=risk_level,
            risk_code=risk_code,
            confidence=round(confidence, 4),
            trigger_evidence_capture=trigger_evidence
        )


# Singleton instance for application lifespan
risk_engine = RiskScoringEngine()
