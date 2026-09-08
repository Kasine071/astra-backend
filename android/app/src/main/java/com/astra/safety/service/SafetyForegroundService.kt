package com.astra.safety.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import com.astra.safety.agent.EvidenceCaptureAgent
import com.astra.safety.network.AstraApiService
import com.astra.safety.network.models.RiskScoreResponse
import com.astra.safety.network.models.TelemetryInput
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class SafetyForegroundService : Service() {
    private val TAG = "ASTRA_SERVICE"
    private val CHANNEL_ID = "astra_safety_channel"
    private val NOTIFICATION_ID = 1

    private var serviceJob: Job? = null
    private val serviceScope = CoroutineScope(Dispatchers.IO)

    // Using 10.0.2.2 for emulator
    private val BACKEND_HOST = "10.0.2.2"
    private val BASE_URL = "http://$BACKEND_HOST:8000/"

    private lateinit var apiService: AstraApiService

    companion object {
        val serviceActive = MutableStateFlow(false)
        val backendConnected = MutableStateFlow(false)
        val riskLevel = MutableStateFlow("SAFE")
        val riskCode = MutableStateFlow(0)
        val confidence = MutableStateFlow(0.0)
        val evidenceState = MutableStateFlow("IDLE")
        val lastUpdate = MutableStateFlow(0L)
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        
        val logging = HttpLoggingInterceptor { Log.d("ASTRA_NETWORK", it) }
        logging.level = HttpLoggingInterceptor.Level.BODY

        val client = OkHttpClient.Builder()
            .addInterceptor(logging)
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .client(client)
            .build()
            
        apiService = retrofit.create(AstraApiService::class.java)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = buildNotification("Monitoring active", "ASTRA Safety is protecting you.")
        startForeground(NOTIFICATION_ID, notification)
        
        serviceActive.value = true
        Log.i(TAG, "service started")
        
        startTelemetryLoop()
        
        return START_STICKY
    }

    private fun startTelemetryLoop() {
        serviceJob?.cancel()
        serviceJob = serviceScope.launch {
            while (isActive) {
                // Dummy telemetry logic for polling
                val dummyTelemetry = TelemetryInput(
                    userId = "DARSHAN_DEMO_USER",
                    latitude = 12.9344,
                    longitude = 77.6060,
                    deviationMeters = 10.0,
                    stopDurationSeconds = 0.0,
                    speedKmh = 45.0,
                    hourOfDay = 14
                )
                
                try {
                    val response = apiService.submitTelemetry(dummyTelemetry)
                    Log.i(TAG, "telemetry sent")
                    
                    if (response.isSuccessful) {
                        backendConnected.value = true
                        Log.i(TAG, "HTTP result: SUCCESS")
                        val riskData = response.body()
                        if (riskData != null) {
                            handleRiskResponse(riskData)
                        }
                    } else {
                        backendConnected.value = false
                        Log.e(TAG, "network errors: ${response.code()}")
                    }
                } catch (e: Exception) {
                    backendConnected.value = false
                    Log.e(TAG, "network errors: ${e.message}")
                }
                
                delay(8000)
            }
        }
    }
    
    private fun handleRiskResponse(riskData: RiskScoreResponse) {
        riskLevel.value = riskData.riskLevel
        riskCode.value = riskData.riskCode
        confidence.value = riskData.confidence
        lastUpdate.value = System.currentTimeMillis()
        
        Log.i(TAG, "risk result: ${riskData.riskLevel}")
        Log.i(TAG, "confidence: ${riskData.confidence}")

        if (riskData.triggerEvidenceCapture && !EvidenceCaptureAgent.isRecording) {
            Log.i(TAG, "evidence trigger: TRUE")
            evidenceState.value = "RECORDING"
            EvidenceCaptureAgent.startSilentCapture(this)
            
            val notification = buildNotification("CRITICAL ALERT", "Evidence capture started.")
            val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.notify(NOTIFICATION_ID, notification)
            
            // Background reset of evidence state after 10 sec recording
            CoroutineScope(Dispatchers.IO).launch {
                delay(10_500) // little extra time to ensure recording stopped
                if (!EvidenceCaptureAgent.isRecording) {
                    evidenceState.value = "SAVED"
                }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        serviceJob?.cancel()
        serviceActive.value = false
        EvidenceCaptureAgent.stopCapture()
        evidenceState.value = "IDLE"
        Log.i(TAG, "service stopped")
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val name = "ASTRA Safety Service"
            val descriptionText = "Persistent Android foreground monitoring service."
            val importance = NotificationManager.IMPORTANCE_LOW
            val channel = NotificationChannel(CHANNEL_ID, name, importance).apply {
                description = descriptionText
            }
            val notificationManager: NotificationManager =
                getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }

    private fun buildNotification(title: String, text: String): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }
}
