"""
Project ASTRA - Telemetry & Risk Schemas
Phase-1 Review 1 (50% Implementation Milestone)
"""

from typing import Literal
from pydantic import BaseModel, Field


class TelemetryInput(BaseModel):
    """
    Incoming real-time streaming telemetry payload from Android ForegroundService.
    Lead: Darshan R (Android Client Lead)
    """
    user_id: str = Field(
        ...,
        description="Unique identifier for the user session (e.g., 'user_astra_101')",
        examples=["user_astra_101"]
    )
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Current GPS latitude coordinate",
        examples=[12.934533]
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Current GPS longitude coordinate",
        examples=[77.606041]
    )
    deviation_meters: float = Field(
        ...,
        ge=0.0,
        description="Cross-track distance in meters from assigned safe route polyline",
        examples=[10.5]
    )
    stop_duration_seconds: float = Field(
        ...,
        ge=0.0,
        description="Unscheduled dwell time in seconds at current location",
        examples=[0.0]
    )
    speed_kmh: float = Field(
        ...,
        ge=0.0,
        description="Current speed of the vehicle in km/h",
        examples=[45.0]
    )
    hour_of_day: int = Field(
        ...,
        ge=0,
        le=23,
        description="24-hour format hour of the day (0-23)",
        examples=[14]
    )


class RiskScoreResponse(BaseModel):
    """
    Risk evaluation response returned by Agent 1 inference microservice.
    If risk_code == 2 (Critical), trigger_evidence_capture is set to True to activate Agent 4.
    """
    status: str = Field(
        default="success",
        description="Execution status of the inference pipeline",
        examples=["success"]
    )
    user_id: str = Field(
        ...,
        description="Echoed unique user identifier",
        examples=["user_astra_101"]
    )
    risk_level: Literal["Safe", "Moderate", "Critical"] = Field(
        ...,
        description="Human-readable categorized risk level",
        examples=["Safe"]
    )
    risk_code: Literal[0, 1, 2] = Field(
        ...,
        description="Numeric risk level: 0 (Safe), 1 (Moderate), 2 (Critical)",
        examples=[0]
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model prediction confidence score [0.0 - 1.0]",
        examples=[0.98]
    )
    trigger_evidence_capture: bool = Field(
        ...,
        description="Flag alerting Android client to activate Agent 4 (Evidence Capture Agent)",
        examples=[False]
    )
