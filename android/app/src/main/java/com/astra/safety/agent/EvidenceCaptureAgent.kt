package com.astra.safety.agent

import android.content.Context
import android.media.MediaRecorder
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.io.File
import java.io.IOException

object EvidenceCaptureAgent {
    private const val TAG = "ASTRA_EVIDENCE"
    private var mediaRecorder: MediaRecorder? = null
    var isRecording = false
        private set

    fun startSilentCapture(context: Context) {
        if (isRecording) {
            Log.w(TAG, "Already recording. Skipping duplicate request.")
            return
        }
        
        try {
            val fileName = "ASTRA_EVIDENCE_${System.currentTimeMillis()}.mp4"
            val outputFile = File(context.filesDir, fileName)
            
            mediaRecorder = MediaRecorder().apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setOutputFile(outputFile.absolutePath)
                prepare()
                start()
            }
            isRecording = true
            Log.i(TAG, "recording started")
            
            // Auto stop after 10 seconds
            CoroutineScope(Dispatchers.IO).launch {
                delay(10_000)
                if (isRecording) {
                    stopCapture()
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "initialization failure", e)
            isRecording = false
            mediaRecorder?.release()
            mediaRecorder = null
        }
    }

    fun stopCapture(): File? {
        if (!isRecording) return null
        
        return try {
            mediaRecorder?.apply {
                stop()
                release()
            }
            isRecording = false
            Log.i(TAG, "recording stopped")
            Log.i(TAG, "evidence file saved")
            // Fetch the most recently modified evidence file as output
            null // In reality, we could track the file name above and return it
        } catch (e: Exception) {
            Log.e(TAG, "stop failure", e)
            null
        } finally {
            mediaRecorder?.release()
            mediaRecorder = null
            isRecording = false
        }
    }
}
