package co.readyday.app.plugins

import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.records.*
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import com.getcapacitor.JSObject
import com.getcapacitor.Plugin
import com.getcapacitor.PluginCall
import com.getcapacitor.PluginMethod
import com.getcapacitor.annotation.CapacitorPlugin
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.ZonedDateTime
import kotlin.math.min

/**
 * HealthPlugin — lee métricas de Health Connect (sincronizadas desde Garmin Connect)
 * y las retorna como snapshot normalizado listo para POST /api/snapshots.
 *
 * Métricas leídas:
 *   - HeartRateRecord → hr_resting (mínimo overnight)
 *   - SleepSessionRecord → sleep_hours + sleep_score estimado
 *   - StepsRecord → activity_load proxy
 *   - ExerciseSessionRecord → activity_load refinado
 *
 * NOTA: Body Battery es propietario de Garmin y NO está en Health Connect.
 * Para Body Battery necesitas el CIQ widget (lee directo del reloj).
 */
@CapacitorPlugin(name = "HealthPlugin")
class HealthPlugin : Plugin() {

    private val scope = CoroutineScope(Dispatchers.IO)

    @PluginMethod
    fun checkAvailability(call: PluginCall) {
        val status = HealthConnectClient.getSdkStatus(context)
        val ret = JSObject()
        ret.put("available", status == HealthConnectClient.SDK_AVAILABLE)
        ret.put("status", status)
        call.resolve(ret)
    }

    @PluginMethod
    fun requestPermissions(call: PluginCall) {
        // Las permisos se piden via Activity en Android — el usuario debe grantearlos
        // en Health Connect Settings. Este método lanza la pantalla de ajustes.
        val intent = HealthConnectClient.getOrCreate(context).let {
            android.content.Intent(HealthConnectClient.ACTION_HEALTH_CONNECT_SETTINGS)
        }
        activity.startActivity(intent)
        call.resolve(JSObject().put("launched", true))
    }

    @PluginMethod
    fun readTodaySnapshot(call: PluginCall) {
        scope.launch {
            try {
                val client = HealthConnectClient.getOrCreate(context)
                val snapshot = readSnapshot(client)
                activity.runOnUiThread { call.resolve(snapshot) }
            } catch (e: Exception) {
                activity.runOnUiThread {
                    call.reject("Health Connect error: ${e.message}", e)
                }
            }
        }
    }

    private suspend fun readSnapshot(client: HealthConnectClient): JSObject {
        val now = Instant.now()
        val startOfDay = LocalDate.now()
            .atStartOfDay(ZoneId.systemDefault())
            .toInstant()
        val last24h = now.minusSeconds(86400)

        val result = JSObject()
        result.put("source", "apple_watch")  // En Android = Health Connect

        // ── HR en reposo (mínimo de las últimas 8h) ─────────────────────────
        try {
            val hrRecords = client.readRecords(
                ReadRecordsRequest(
                    recordType = HeartRateRecord::class,
                    timeRangeFilter = TimeRangeFilter.between(
                        now.minusSeconds(28800),  // 8 horas
                        now
                    )
                )
            ).records
            val minHR = hrRecords
                .flatMap { it.samples }
                .minOfOrNull { it.beatsPerMinute }
            if (minHR != null) result.put("hr_resting", minHR.toDouble())
        } catch (e: Exception) { /* permiso no concedido */ }

        // ── Sueño ────────────────────────────────────────────────────────────
        try {
            val sleepRecords = client.readRecords(
                ReadRecordsRequest(
                    recordType = SleepSessionRecord::class,
                    timeRangeFilter = TimeRangeFilter.between(last24h, now)
                )
            ).records
            val latestSleep = sleepRecords.maxByOrNull { it.endTime }
            if (latestSleep != null) {
                val hours = (latestSleep.endTime.epochSecond - latestSleep.startTime.epochSecond)
                    .toDouble() / 3600.0
                result.put("sleep_hours", hours)

                // Estimar sleep score desde horas
                val score = when {
                    hours >= 8.0 -> 90.0
                    hours >= 7.0 -> 75.0
                    hours >= 6.0 -> 55.0
                    hours >= 5.0 -> 35.0
                    else -> 20.0
                }
                result.put("sleep_score", score)
            }
        } catch (e: Exception) {}

        // ── Pasos → activity_load proxy ──────────────────────────────────────
        try {
            val stepsRecords = client.readRecords(
                ReadRecordsRequest(
                    recordType = StepsRecord::class,
                    timeRangeFilter = TimeRangeFilter.between(startOfDay, now)
                )
            ).records
            val totalSteps = stepsRecords.sumOf { it.count }
            // 10.000 pasos ≈ 50 de activity_load; 20.000+ ≈ 100
            val actLoad = min(100.0, totalSteps.toDouble() / 200.0)
            result.put("activity_load", actLoad)
        } catch (e: Exception) {}

        return result
    }
}
