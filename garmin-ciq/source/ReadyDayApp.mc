// ReadyDayApp.mc — Widget principal
// Lee sensores del reloj, calcula score local, envía al backend vía web request.

using Toybox.Application as App;
using Toybox.WatchUi as WatchUi;
using Toybox.SensorHistory as SensorHistory;
using Toybox.Communications as Comm;
using Toybox.System as Sys;
using Toybox.Application.Storage as Storage;

class ReadyDayApp extends App.AppBase {

    // API base — apunta a tu servidor
    const API_URL = "https://www.fergussononline.org/readyday/api";

    function initialize() {
        AppBase.initialize();
    }

    function onStart(state as Dictionary?) as Void {
    }

    function onStop(state as Dictionary?) as Void {
    }

    function getInitialView() as [WatchUi.Views] or [WatchUi.Views, WatchUi.InputDelegates] {
        var view = new ReadyDayView();
        return [view];
    }

    // ── Lee sensores del reloj ────────────────────────────────────────────────

    static function readSensors() as Dictionary {
        var data = {
            "source" => "garmin",
            "body_battery" => null,
            "sleep_score" => null,
            "sleep_hours" => null,
            "hr_resting" => null,
            "stress_avg" => null,
            "activity_load" => null,
            "recovery_time_h" => null,
        };

        // Body Battery — max del día
        try {
            var bbIter = SensorHistory.getBodyBatteryHistory({
                :period => 480,  // últimas 8 horas
                :order => SensorHistory.ORDER_NEWEST_FIRST
            });
            if (bbIter != null) {
                var maxBB = 0.0;
                var bbSample = bbIter.next();
                while (bbSample != null) {
                    var val = bbSample.data;
                    if (val != null && val > maxBB) { maxBB = val.toFloat(); }
                    bbSample = bbIter.next();
                }
                if (maxBB > 0.0) { data["body_battery"] = maxBB; }
            }
        } catch (e) { /* SensorHistory no disponible en este dispositivo */ }

        // HR en reposo — mínimo nocturno (últimas 8h)
        try {
            var hrIter = SensorHistory.getHeartRateHistory({
                :period => 480,
                :order => SensorHistory.ORDER_NEWEST_FIRST
            });
            if (hrIter != null) {
                var minHR = 999.0;
                var hrSample = hrIter.next();
                while (hrSample != null) {
                    var val = hrSample.data;
                    if (val != null && val > 0 && val < minHR) { minHR = val.toFloat(); }
                    hrSample = hrIter.next();
                }
                if (minHR < 999.0) { data["hr_resting"] = minHR; }
            }
        } catch (e) {}

        // Estrés promedio (últimas 8h)
        try {
            var stressIter = SensorHistory.getStressHistory({
                :period => 480,
                :order => SensorHistory.ORDER_NEWEST_FIRST
            });
            if (stressIter != null) {
                var sum = 0.0;
                var count = 0;
                var stressSample = stressIter.next();
                while (stressSample != null) {
                    var val = stressSample.data;
                    if (val != null && val >= 0) {
                        sum += val.toFloat();
                        count++;
                    }
                    stressSample = stressIter.next();
                }
                if (count > 0) { data["stress_avg"] = sum / count; }
            }
        } catch (e) {}

        // Sleep (CIQ 4.2+, disponible en Venu 3, Fenix 7 Pro, FR265+)
        try {
            var sleepStats = Toybox.UserProfile.getSleepStatistics();
            if (sleepStats != null) {
                var sleepSecs = sleepStats[:totalSleepSeconds];
                if (sleepSecs != null) {
                    data["sleep_hours"] = sleepSecs.toFloat() / 3600.0;
                }
                // Sleep score nativo (si el dispositivo lo provee)
                var nativeScore = sleepStats[:sleepScore];
                if (nativeScore != null) {
                    data["sleep_score"] = nativeScore.toFloat();
                } else if (sleepSecs != null) {
                    // Estimar score desde horas de sueño
                    var hours = sleepSecs.toFloat() / 3600.0;
                    var estimated = (hours >= 8.0) ? 90.0 :
                                    (hours >= 7.0) ? 75.0 :
                                    (hours >= 6.0) ? 55.0 :
                                    (hours >= 5.0) ? 35.0 : 20.0;
                    data["sleep_score"] = estimated;
                }
            }
        } catch (e) {}

        return data;
    }

    // ── Envía snapshot al backend ─────────────────────────────────────────────

    static function syncToBackend(sensorData as Dictionary) as Void {
        var token = Storage.getValue("api_token");
        if (token == null || token.length() == 0) {
            return;  // sin token no se puede sincronizar
        }

        // Timestamp ISO actual
        var now = Sys.getClockTime();
        var today = Sys.getLocalTime();
        var ts = Lang.format("$1$-$2$-$3$T$4$:$5$:$6$Z", [
            today.year.format("%04d"),
            today.month.format("%02d"),
            today.day.format("%02d"),
            now.hour.format("%02d"),
            now.min.format("%02d"),
            now.sec.format("%02d"),
        ]);

        var payload = {
            "source" => "garmin",
            "captured_at" => ts,
            "body_battery" => sensorData["body_battery"],
            "sleep_score" => sensorData["sleep_score"],
            "sleep_hours" => sensorData["sleep_hours"],
            "hr_resting" => sensorData["hr_resting"],
            "stress_avg" => sensorData["stress_avg"],
            "activity_load" => sensorData["activity_load"],
            "recovery_time_h" => sensorData["recovery_time_h"],
        };

        var headers = {
            "Content-Type" => "application/json",
            "Authorization" => "Bearer " + token,
        };

        Comm.makeWebRequest(
            API_URL + "/snapshots",
            payload,
            { :method => Comm.HTTP_REQUEST_METHOD_POST, :headers => headers },
            method(:onBackendResponse)
        );
    }

    function onBackendResponse(code as Number, data as Dictionary?) as Void {
        if (code == 201 && data != null) {
            // Guardar score recibido del servidor
            var score = data["score"];
            if (score != null) {
                Storage.setValue("last_server_recovery", score["recovery_score"]);
                Storage.setValue("last_server_zone", score["zone"]);
                Storage.setValue("last_server_rec", score["recommendation"]);
                // Forzar redraw de la vista
                WatchUi.requestUpdate();
            }
        }
    }
}
