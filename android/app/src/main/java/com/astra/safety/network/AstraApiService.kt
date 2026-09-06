package com.astra.safety.network

import com.astra.safety.network.models.RiskScoreResponse
import com.astra.safety.network.models.TelemetryInput
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface AstraApiService {
    @POST("api/v1/telemetry/score")
    suspend fun submitTelemetry(
        @Body telemetry: TelemetryInput
    ): Response<RiskScoreResponse>
}
