package com.astra.safety.network.models

import com.google.gson.annotations.SerializedName

data class TelemetryInput(
    @SerializedName("user_id") val userId: String,
    @SerializedName("latitude") val latitude: Double,
    @SerializedName("longitude") val longitude: Double,
    @SerializedName("deviation_meters") val deviationMeters: Double,
    @SerializedName("stop_duration_seconds") val stopDurationSeconds: Double,
    @SerializedName("speed_kmh") val speedKmh: Double,
    @SerializedName("hour_of_day") val hourOfDay: Int
)

data class RiskScoreResponse(
    @SerializedName("status") val status: String,
    @SerializedName("user_id") val userId: String,
    @SerializedName("risk_level") val riskLevel: String,
    @SerializedName("risk_code") val riskCode: Int,
    @SerializedName("confidence") val confidence: Double,
    @SerializedName("trigger_evidence_capture") val triggerEvidenceCapture: Boolean
)
