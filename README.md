# Project ASTRA 🛡️
### AI-Powered Multi-Agent Women's Travel Safety Assistant
**Review Stage:** Phase-1 Review 1 (50% Implementation Milestone)  
**Institution:** CHRIST (Deemed to be University), Bangalore — Department of Computer Science and Engineering  

---

## 👥 Project Team & Responsibilities
* **Kasine RS** ([GitHub: @Kasine071](https://github.com/Kasine071)) — **Backend & Machine Learning Lead**
  * *Architecture Lead for Agent 1 (Predictive Risk Scoring Engine) and Agent 4 Trigger Pipeline.*
* **Darshan R** ([GitHub: @Drzxn](https://github.com/Drzxn)) — **Android & Client Systems Lead**
  * *Architecture Lead for Android ForegroundService Telemetry Stream & Agent 4 (Evidence Capture Agent).*

---

## 🧭 Milestone Overview (50% Implementation Scope)
Project ASTRA introduces a multi-agent safety framework that autonomously detects anomalies during transit and captures protective evidence before critical danger occurs.

```
+-------------------------------------------------------------------------------+
|                       Android Client (Darshan R)                              |
|                                                                               |
|  +---------------------------+        +-----------------------------------+   |
|  | Android ForegroundService |        |   Agent 4 (Evidence Capture)      |   |
|  | (GPS & Dwell Telemetry)   |        |   [Camera / Mic / Sensor Sync]    |   |
|  +-------------+-------------+        +-----------------+-----------------+   |
+----------------|----------------------------------------^---------------------+
                 | HTTP POST                               |
                 | Live Telemetry                          | trigger_evidence_capture = true
                 v                                         |
+----------------------------------------------------------|--------------------+
|                       ASTRA Backend Microservice (Kasine RS)                  |
|                                                                               |
|  +---------------------------+        +------------------+-----------------+  |
|  | POST /api/v1/telemetry/   | =====> |       Agent 1 Risk Engine          |  |
|  | score                     |        |  (RandomForest Multi-Class Model)  |  |
|  +---------------------------+        +------------------------------------+  |
+-------------------------------------------------------------------------------+
```

1. **Agent 1 (Predictive Risk Scoring):**
   - Ingests real-time transit telemetry (`route_deviation_meters`, `stop_duration_seconds`, `speed_kmh`, `hour_of_day`).
   - Classifies risk into **Safe (0)**, **Moderate (1)**, or **Critical (2)** using a trained `RandomForestClassifier`.
2. **Agent 4 (Evidence Trigger Pipeline):**
   - Automatically determines when critical escalation is warranted.
   - Sets `trigger_evidence_capture = true` upon detecting `risk_code == 2`, signalling the Android ForegroundService to begin silent evidence logging.

---

## 🚀 Quickstart & Server Setup

### 1. Prerequisites & Environment Setup
```bash
# Navigate to repository
cd astra-backend

# Install dependencies
pip install -r requirements.txt
```

### 2. Train or Retrain the Risk ML Model (Agent 1)
```bash
python ml/train_risk_model.py
```
*Evaluates the model on synthetic travel distributions and exports the serialized model artifact to `ml/risk_model.pkl`.*

### 3. Start the FastAPI Microservice
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
* The API will be active at: `http://localhost:8000`
* Interactive OpenAPI Documentation (Swagger UI): `http://localhost:8000/docs`
* Redoc Documentation: `http://localhost:8000/redoc`

---

## 📱 Android Client Integration Guide (For Darshan R)

### Network Configuration
When connecting the Android app to the backend:
* **Android Emulator:** Point OkHttp / Retrofit baseUrl to `http://10.0.2.2:8000/`
* **Physical Android Device (Wi-Fi):** Point baseUrl to your laptop's local LAN IP: `http://192.168.x.x:8000/`

> [!NOTE]
> Make sure `android:usesCleartextTraffic="true"` is enabled in your AndroidManifest.xml for local HTTP testing, or use HTTPS in production.

---

### API Contract & Kotlin Data Classes

#### 1. Telemetry Ingest Request (`POST /api/v1/telemetry/score`)
**Endpoint:** `http://<HOST>:8000/api/v1/telemetry/score`  
**Method:** `POST`  
**Content-Type:** `application/json`

**Kotlin Model:**
```kotlin
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
```

**Request JSON Example:**
```json
{
  "user_id": "darshan_device_01",
  "latitude": 12.934533,
  "longitude": 77.606041,
  "deviation_meters": 10.0,
  "stop_duration_seconds": 0.0,
  "speed_kmh": 45.0,
  "hour_of_day": 14
}
```

---

#### 2. Risk Score Response
**Kotlin Model:**
```kotlin
package com.astra.safety.network.models

import com.google.gson.annotations.SerializedName

data class RiskScoreResponse(
    @SerializedName("status") val status: String,
    @SerializedName("user_id") val userId: String,
    @SerializedName("risk_level") val riskLevel: String, // "Safe", "Moderate", "Critical"
    @SerializedName("risk_code") val riskCode: Int,      // 0, 1, 2
    @SerializedName("confidence") val confidence: Double,
    @SerializedName("trigger_evidence_capture") val triggerEvidenceCapture: Boolean
)
```

**Response JSON Example (Critical Anomaly):**
```json
{
  "status": "success",
  "user_id": "darshan_device_01",
  "risk_level": "Critical",
  "risk_code": 2,
  "confidence": 0.9850,
  "trigger_evidence_capture": true
}
```

---

### Retrofit Service Definition
```kotlin
package com.astra.safety.network

import com.astra.safety.network.models.TelemetryInput
import com.astra.safety.network.models.RiskScoreResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface AstraApiService {
    @POST("api/v1/telemetry/score")
    suspend fun submitTelemetry(
        @Body telemetry: TelemetryInput
    ): Response<RiskScoreResponse>
}
```

### Agent 4 Handling Logic in Android ForegroundService
```kotlin
// In Android ForegroundService telemetry dispatch loop:
val response = astraApiService.submitTelemetry(currentTelemetry)
if (response.isSuccessful) {
    val riskData = response.body()
    if (riskData?.triggerEvidenceCapture == true) {
        // Activate Agent 4: Evidence Capture Pipeline (Camera/Audio recording)
        EvidenceCaptureAgent.startSilentCapture(context)
    }
}
```

---

## 🧪 Testing & Verification

### 1. Automated Pytest Suite
Run the unit and integration tests:
```bash
pytest -v tests/test_api.py
```

### 2. Mock Android Client Simulation
To test the full inference pipeline without an Android device attached:
```bash
# Terminal 1: Run server
uvicorn app.main:app --port 8000

# Terminal 2: Run simulator
python tests/mock_android_client.py
```

**Scenarios Simulated:**
1. **Scenario 1 (Daytime Commute):** 10m deviation, 45 km/h, 2:00 PM $\rightarrow$ **Safe (0)**, Trigger: `False`.
2. **Scenario 2 (Traffic Signal Pause):** 20m deviation, 90s dwell, 6:00 PM $\rightarrow$ **Safe (0)**, Trigger: `False`.
3. **Scenario 3 (Critical Midnight Halt):** 550m deviation, 400s dwell, 11:30 PM $\rightarrow$ **Critical (2)**, Trigger: `True` 🚨.

---

## 📁 Repository Structure
```
astra-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── telemetry.py       # POST /api/v1/telemetry/score router
│   ├── core/
│   │   └── config.py              # Application settings & thresholds
│   ├── schemas/
│   │   └── telemetry.py           # Pydantic schemas for Android telemetry & responses
│   ├── services/
│   │   └── risk_engine.py         # Agent 1 inference service & Agent 4 trigger logic
│   └── main.py                    # FastAPI entrypoint & CORS setup
├── ml/
│   ├── train_risk_model.py        # ML training pipeline for Agent 1
│   └── risk_model.pkl             # Trained RandomForest model artifact
├── tests/
│   ├── mock_android_client.py     # Live mock client simulating Android telemetry
│   └── test_api.py                # Automated Pytest suite
├── requirements.txt               # Dependencies
├── .gitignore                     # Git ignore rules
└── README.md                      # Documentation & integration contracts
```

---

## 📱 Android Client — Darshan R

### Project Location
The Android client implementation is located in the `android/` directory at the root of the repository.

### Getting Started

1. **Open in Android Studio:**
   Launch Android Studio, click **Open**, and select the `astra-backend/android/` directory (not the `astra-backend` root). Let Gradle sync and build the project.

2. **Network Configuration (`BACKEND_HOST`):**
   - By default, the app targets the Android Emulator loopback `10.0.2.2`. 
   - **For Physical Devices:** Modify the `BACKEND_HOST` constant in `MainActivity.kt` and `SafetyForegroundService.kt` to match your local network IP (e.g., `192.168.1.42`) where the FastAPI server is running.
   - Note: The app uses `android:usesCleartextTraffic="true"` for local HTTP testing. Use HTTPS for production.

3. **Backend Startup (Kasine):**
   ```bash
   cd astra-backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Review 1 Demonstration Procedure

1. **Deploy:** Install the app on an Android device or emulator.
2. **Permissions:** Tap **Start ASTRA Protection**. You will be prompted for Location and Microphone permissions. Grant them.
3. **Start Protection:** Tap **Start ASTRA Protection** again. A persistent foreground notification will appear, and the service will begin sending dummy telemetry every 8 seconds.
4. **Daytime Commute Simulation:** 
   - Tap **Simulate Daytime Commute**.
   - The UI will display **SAFE** (Risk Code 0) with a high confidence. Evidence remains **IDLE**.
5. **Critical Midnight Halt Simulation:**
   - Tap **Simulate Critical Midnight Halt**.
   - The UI will display **CRITICAL** (Risk Code 2) and `trigger_evidence_capture = true`.
   - The Evidence status will change to **RECORDING**.
   - Wait 10 seconds; the status will update to **SAVED**.
6. **Verify Evidence:**
   - Tap **View Captured Evidence** to see a list of saved `.mp4` recordings.
   - You can also verify the file via Android Studio's **Device File Explorer** under `data/data/com.astra.safety/files/`.

### Troubleshooting
- **Network Errors / DISCONNECTED:** Check if the FastAPI server is running. Ensure the `BACKEND_HOST` IP is reachable from the Android device. Check Logcat under the `ASTRA_NETWORK` tag for HTTP details.
- **Recording Fails:** Ensure Microphone permission is granted in Android Settings. Check Logcat under the `ASTRA_EVIDENCE` tag.
