package com.astra.safety

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.astra.safety.agent.EvidenceCaptureAgent
import com.astra.safety.network.AstraApiService
import com.astra.safety.network.models.TelemetryInput
import com.astra.safety.service.SafetyForegroundService
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MainActivity : AppCompatActivity() {

    private val TAG = "ASTRA_UI"
    private val PERMISSION_REQUEST_CODE = 100

    private lateinit var tvServiceState: TextView
    private lateinit var tvBackendState: TextView
    private lateinit var tvRiskState: TextView
    private lateinit var tvRiskCode: TextView
    private lateinit var tvConfidence: TextView
    private lateinit var tvEvidenceState: TextView
    private lateinit var tvLastUpdate: TextView

    private lateinit var btnStartProtection: Button
    private lateinit var btnStopProtection: Button
    private lateinit var btnSimulateDaytime: Button
    private lateinit var btnSimulateCritical: Button
    private lateinit var btnViewEvidence: Button

    private lateinit var apiService: AstraApiService
    private val BACKEND_HOST = "10.0.2.2"
    private val BASE_URL = "http://$BACKEND_HOST:8000/"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        initViews()
        initNetwork()
        setupListeners()
        observeServiceState()
    }

    private fun initViews() {
        tvServiceState = findViewById(R.id.tvServiceState)
        tvBackendState = findViewById(R.id.tvBackendState)
        tvRiskState = findViewById(R.id.tvRiskState)
        tvRiskCode = findViewById(R.id.tvRiskCode)
        tvConfidence = findViewById(R.id.tvConfidence)
        tvEvidenceState = findViewById(R.id.tvEvidenceState)
        tvLastUpdate = findViewById(R.id.tvLastUpdate)

        btnStartProtection = findViewById(R.id.btnStartProtection)
        btnStopProtection = findViewById(R.id.btnStopProtection)
        btnSimulateDaytime = findViewById(R.id.btnSimulateDaytime)
        btnSimulateCritical = findViewById(R.id.btnSimulateCritical)
        btnViewEvidence = findViewById(R.id.btnViewEvidence)
    }

    private fun initNetwork() {
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

    private fun setupListeners() {
        btnStartProtection.setOnClickListener {
            if (checkPermissions()) {
                startSafetyService()
            } else {
                requestPermissions()
            }
        }

        btnStopProtection.setOnClickListener {
            stopSafetyService()
        }

        btnSimulateDaytime.setOnClickListener {
            simulateScenario(
                TelemetryInput(
                    userId = "DARSHAN_DEMO_USER",
                    latitude = 12.9344,
                    longitude = 77.6060,
                    deviationMeters = 10.0,
                    stopDurationSeconds = 0.0,
                    speedKmh = 45.0,
                    hourOfDay = 14
                )
            )
        }

        btnSimulateCritical.setOnClickListener {
            simulateScenario(
                TelemetryInput(
                    userId = "DARSHAN_DEMO_USER",
                    latitude = 12.9344, // Using same base location for simplicity
                    longitude = 77.6060,
                    deviationMeters = 550.0,
                    stopDurationSeconds = 400.0,
                    speedKmh = 0.0,
                    hourOfDay = 23
                )
            )
        }

        btnViewEvidence.setOnClickListener {
            viewCapturedEvidence()
        }
    }

    private fun observeServiceState() {
        lifecycleScope.launch {
            SafetyForegroundService.serviceActive.collect { isActive ->
                tvServiceState.text = if (isActive) "ACTIVE" else "INACTIVE"
                btnStartProtection.isEnabled = !isActive
                btnStopProtection.isEnabled = isActive
            }
        }
        
        lifecycleScope.launch {
            SafetyForegroundService.backendConnected.collect { isConnected ->
                tvBackendState.text = if (isConnected) "CONNECTED" else "DISCONNECTED"
            }
        }
        
        lifecycleScope.launch {
            SafetyForegroundService.riskLevel.collect { risk ->
                tvRiskState.text = risk
            }
        }
        
        lifecycleScope.launch {
            SafetyForegroundService.riskCode.collect { code ->
                tvRiskCode.text = code.toString()
            }
        }
        
        lifecycleScope.launch {
            SafetyForegroundService.confidence.collect { conf ->
                tvConfidence.text = "%.2f%%".format(conf * 100)
            }
        }
        
        lifecycleScope.launch {
            SafetyForegroundService.evidenceState.collect { state ->
                tvEvidenceState.text = state
            }
        }
        
        lifecycleScope.launch {
            SafetyForegroundService.lastUpdate.collect { timestamp ->
                if (timestamp > 0) {
                    val sdf = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
                    tvLastUpdate.text = "Last update: ${sdf.format(Date(timestamp))}"
                }
            }
        }
    }

    private fun checkPermissions(): Boolean {
        val audioPermission = ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED
        val locationPermission = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
        return audioPermission && locationPermission
    }

    private fun requestPermissions() {
        val permissions = mutableListOf(
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.ACCESS_COARSE_LOCATION
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            permissions.add(Manifest.permission.FOREGROUND_SERVICE)
        }
        ActivityCompat.requestPermissions(this, permissions.toTypedArray(), PERMISSION_REQUEST_CODE)
    }

    private fun startSafetyService() {
        val serviceIntent = Intent(this, SafetyForegroundService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent)
        } else {
            startService(serviceIntent)
        }
    }

    private fun stopSafetyService() {
        val serviceIntent = Intent(this, SafetyForegroundService::class.java)
        stopService(serviceIntent)
    }

    private fun simulateScenario(telemetry: TelemetryInput) {
        lifecycleScope.launch(Dispatchers.IO) {
            try {
                val response = apiService.submitTelemetry(telemetry)
                if (response.isSuccessful) {
                    SafetyForegroundService.backendConnected.value = true
                    val data = response.body()
                    if (data != null) {
                        withContext(Dispatchers.Main) {
                            SafetyForegroundService.riskLevel.value = data.riskLevel
                            SafetyForegroundService.riskCode.value = data.riskCode
                            SafetyForegroundService.confidence.value = data.confidence
                            SafetyForegroundService.lastUpdate.value = System.currentTimeMillis()
                            
                            if (data.triggerEvidenceCapture && !EvidenceCaptureAgent.isRecording) {
                                SafetyForegroundService.evidenceState.value = "RECORDING"
                                EvidenceCaptureAgent.startSilentCapture(this@MainActivity)
                                
                                // Reset evidence state after 10 sec recording
                                launch {
                                    delay(10_500)
                                    if (!EvidenceCaptureAgent.isRecording) {
                                        SafetyForegroundService.evidenceState.value = "SAVED"
                                    }
                                }
                            }
                        }
                    }
                } else {
                    SafetyForegroundService.backendConnected.value = false
                    withContext(Dispatchers.Main) {
                        Toast.makeText(this@MainActivity, "Network Error: ${response.code()}", Toast.LENGTH_SHORT).show()
                    }
                }
            } catch (e: Exception) {
                SafetyForegroundService.backendConnected.value = false
                withContext(Dispatchers.Main) {
                    Toast.makeText(this@MainActivity, "Error: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    private fun viewCapturedEvidence() {
        val files = filesDir.listFiles { _, name -> name.startsWith("ASTRA_EVIDENCE_") && name.endsWith(".mp4") }
        if (files.isNullOrEmpty()) {
            Toast.makeText(this, "No evidence files found", Toast.LENGTH_SHORT).show()
            return
        }

        val message = StringBuilder("Captured Evidence:\n\n")
        val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
        
        files.sortedByDescending { it.lastModified() }.forEach { file ->
            val sizeKb = file.length() / 1024
            message.append("Name: ${file.name}\n")
            message.append("Size: $sizeKb KB\n")
            message.append("Time: ${sdf.format(Date(file.lastModified()))}\n\n")
        }

        androidx.appcompat.app.AlertDialog.Builder(this)
            .setTitle("Evidence Viewer")
            .setMessage(message.toString())
            .setPositiveButton("OK", null)
            .show()
    }
}
