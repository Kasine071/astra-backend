"""
Project ASTRA - Telemetry & Risk Scoring API
Phase-1 Review 1 (50% Implementation Milestone)
CHRIST (Deemed to be University), Department of CSE
"""

import logging
from fastapi import APIRouter, HTTPException, status
from app.schemas.telemetry import TelemetryInput, RiskScoreResponse
from app.services.risk_engine import risk_engine

logger = logging.getLogger("astra.api.telemetry")

router = APIRouter()


@router.post(
    "/score",
    response_model=RiskScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute Predictive Risk Score for Live Telemetry",
    description="""
    Inference endpoint for **Agent 1 (Predictive Risk Scoring)**.
    
    Streams telemetry from Darshan's Android ForegroundService (`user_id`, `latitude`, `longitude`, `deviation_meters`, `stop_duration_seconds`, `speed_kmh`, `hour_of_day`).
    Returns classified `risk_level` ('Safe' | 'Moderate' | 'Critical'), `risk_code` (0 | 1 | 2), and confidence.
    
    When `risk_code == 2` (Critical), `trigger_evidence_capture` is flagged `True` to activate **Agent 4 (Evidence Capture Pipeline)** on Android.
    """
)
async def score_telemetry(payload: TelemetryInput) -> RiskScoreResponse:
    try:
        response = risk_engine.score_telemetry(payload)
        logger.info(
            f"User {payload.user_id} | Risk: {response.risk_level} (Code: {response.risk_code}, Conf: {response.confidence}) | Trigger: {response.trigger_evidence_capture}"
        )
        return response
    except Exception as e:
        logger.error(f"Error processing telemetry for user {payload.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute risk score: {str(e)}"
        )
