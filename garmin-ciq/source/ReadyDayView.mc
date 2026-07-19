// ReadyDayView.mc — Vista principal del widget
// Muestra: score grande + zona + recomendación corta + métricas clave

using Toybox.WatchUi as WatchUi;
using Toybox.Graphics as Gfx;
using Toybox.Application.Storage as Storage;
using Toybox.System as Sys;

class ReadyDayView extends WatchUi.View {

    var _sensorData as Dictionary;
    var _recovery   as Number;
    var _strain     as Number;
    var _zone       as Number;
    var _synced     as Boolean;

    function initialize() {
        View.initialize();
        _sensorData = {};
        _recovery = -1;
        _strain   = 0;
        _zone     = 1;
        _synced   = false;
    }

    function onShow() as Void {
        // Lee sensores y calcula score local al mostrar el widget
        _sensorData = ReadyDayApp.readSensors();
        _computeLocalScore();

        // Intenta sincronizar con el backend en segundo plano
        ReadyDayApp.syncToBackend(_sensorData);
    }

    function _computeLocalScore() as Void {
        var bb    = (_sensorData["body_battery"] != null) ? _sensorData["body_battery"].toFloat()    : 50.0;
        var stress = (_sensorData["stress_avg"]  != null) ? _sensorData["stress_avg"].toFloat()      : 50.0;
        var hr    = (_sensorData["hr_resting"]   != null) ? _sensorData["hr_resting"].toFloat()      : 65.0;
        var sleep = (_sensorData["sleep_score"]  != null) ? _sensorData["sleep_score"].toFloat()     : 50.0;
        var act   = (_sensorData["activity_load"] != null) ? _sensorData["activity_load"].toFloat()  : 0.0;
        var rt    = (_sensorData["recovery_time_h"] != null) ? _sensorData["recovery_time_h"].toFloat() : 0.0;

        _recovery = ScoreEngine.calcRecovery(bb, stress, hr, sleep);
        _strain   = ScoreEngine.calcStrain(act, rt, stress);
        var balance = ScoreEngine.calcBalance(_recovery, _strain);
        _zone = ScoreEngine.getZone(_recovery, balance);

        // Si el servidor ya respondió, usar su score
        var serverRec = Storage.getValue("last_server_recovery");
        if (serverRec != null) {
            _recovery = serverRec;
            var serverZoneStr = Storage.getValue("last_server_zone");
            if (serverZoneStr != null) {
                if (serverZoneStr.equals("green"))  { _zone = 0; }
                else if (serverZoneStr.equals("yellow")) { _zone = 1; }
                else { _zone = 2; }
            }
            _synced = true;
        }
    }

    function onUpdate(dc as Gfx.Dc) as Void {
        var width  = dc.getWidth();
        var height = dc.getHeight();
        var cx     = width / 2;
        var cy     = height / 2;

        // Fondo negro
        dc.setColor(Gfx.COLOR_TRANSPARENT, 0x07070F);
        dc.clear();

        if (_recovery < 0) {
            // Estado sin datos
            dc.setColor(0x6B6B8A, Gfx.COLOR_TRANSPARENT);
            dc.drawText(cx, cy - 20, Gfx.FONT_MEDIUM, "ReadyDay", Gfx.TEXT_JUSTIFY_CENTER);
            dc.drawText(cx, cy + 10, Gfx.FONT_TINY, "Sincronizando...", Gfx.TEXT_JUSTIFY_CENTER);
            return;
        }

        var zoneColor = ScoreEngine.zoneColor(_zone);

        // ── Anillo de zona ────────────────────────────────
        var ringR  = (width < height ? width : height) / 2 - 8;
        var ringW  = 8;
        dc.setPenWidth(ringW);
        dc.setColor(zoneColor, Gfx.COLOR_TRANSPARENT);
        // Arco completo (360° = zona completa)
        dc.drawArc(cx, cy, ringR, Gfx.ARC_CLOCKWISE, 0, 360);

        // ── Score principal ───────────────────────────────
        dc.setColor(zoneColor, Gfx.COLOR_TRANSPARENT);
        dc.drawText(cx, cy - 52, Gfx.FONT_NUMBER_THAI_HOT, _recovery.toString(), Gfx.TEXT_JUSTIFY_CENTER);

        // Label "RECOVERY"
        dc.setColor(0x6B6B8A, Gfx.COLOR_TRANSPARENT);
        dc.drawText(cx, cy - 14, Gfx.FONT_XTINY, "RECOVERY", Gfx.TEXT_JUSTIFY_CENTER);

        // ── Zona label ────────────────────────────────────
        var zLabel = (_zone == 0) ? "VERDE" : (_zone == 1) ? "AMARILLO" : "ROJO";
        dc.setColor(zoneColor, Gfx.COLOR_TRANSPARENT);
        dc.drawText(cx, cy + 6, Gfx.FONT_TINY, zLabel, Gfx.TEXT_JUSTIFY_CENTER);

        // ── Métricas pequeñas (fila inferior) ─────────────
        var metricsY = cy + 32;
        dc.setColor(0xAAAAAA, Gfx.COLOR_TRANSPARENT);

        var bbStr    = (_sensorData["body_battery"] != null) ? (_sensorData["body_battery"].toNumber().toString() + "%") : "--";
        var hrStr    = (_sensorData["hr_resting"]   != null) ? (_sensorData["hr_resting"].toNumber().toString() + "bpm") : "--";
        var sleepStr = (_sensorData["sleep_hours"]  != null) ? (_sensorData["sleep_hours"].format("%.1f") + "h") : "--";

        var col1 = cx - width / 3;
        var col2 = cx;
        var col3 = cx + width / 3;

        dc.drawText(col1, metricsY, Gfx.FONT_XTINY, "BB", Gfx.TEXT_JUSTIFY_CENTER);
        dc.drawText(col2, metricsY, Gfx.FONT_XTINY, "FC", Gfx.TEXT_JUSTIFY_CENTER);
        dc.drawText(col3, metricsY, Gfx.FONT_XTINY, "Sueño", Gfx.TEXT_JUSTIFY_CENTER);

        dc.setColor(0xE8E8F0, Gfx.COLOR_TRANSPARENT);
        dc.drawText(col1, metricsY + 16, Gfx.FONT_TINY, bbStr, Gfx.TEXT_JUSTIFY_CENTER);
        dc.drawText(col2, metricsY + 16, Gfx.FONT_TINY, hrStr, Gfx.TEXT_JUSTIFY_CENTER);
        dc.drawText(col3, metricsY + 16, Gfx.FONT_TINY, sleepStr, Gfx.TEXT_JUSTIFY_CENTER);

        // Indicator de sync con servidor
        if (_synced) {
            dc.setColor(0x00D4AA, Gfx.COLOR_TRANSPARENT);
            dc.drawText(cx, cy - 72, Gfx.FONT_XTINY, "✓ sync", Gfx.TEXT_JUSTIFY_CENTER);
        }
    }

    function onHide() as Void {
    }
}


class ReadyDayDelegate extends WatchUi.BehaviorDelegate {
    function initialize() {
        BehaviorDelegate.initialize();
    }

    function onMenu() as Boolean {
        WatchUi.pushView(new ReadyDaySettingsView(), new ReadyDaySettingsDelegate(), WatchUi.SLIDE_UP);
        return true;
    }

    function onSelect() as Boolean {
        // Tap/press = refrescar datos
        WatchUi.requestUpdate();
        return true;
    }
}


// ── Pantalla de ajustes (token de API) ────────────────────────────────────────
class ReadyDaySettingsView extends WatchUi.View {
    function initialize() { View.initialize(); }

    function onUpdate(dc as Gfx.Dc) as Void {
        var cx = dc.getWidth() / 2;
        var cy = dc.getHeight() / 2;
        dc.setColor(Gfx.COLOR_TRANSPARENT, 0x07070F);
        dc.clear();

        dc.setColor(0xE8E8F0, Gfx.COLOR_TRANSPARENT);
        dc.drawText(cx, cy - 40, Gfx.FONT_SMALL, "Ajustes", Gfx.TEXT_JUSTIFY_CENTER);

        var token = Storage.getValue("api_token");
        var tokenStatus = (token != null && token.length() > 0) ? "Token: OK ✓" : "Token: no configurado";

        dc.setColor(token != null ? 0x00D4AA : 0xFF4D6D, Gfx.COLOR_TRANSPARENT);
        dc.drawText(cx, cy - 10, Gfx.FONT_TINY, tokenStatus, Gfx.TEXT_JUSTIFY_CENTER);

        dc.setColor(0x6B6B8A, Gfx.COLOR_TRANSPARENT);
        dc.drawText(cx, cy + 20, Gfx.FONT_XTINY, "Entra en readyday.co", Gfx.TEXT_JUSTIFY_CENTER);
        dc.drawText(cx, cy + 36, Gfx.FONT_XTINY, "y copia tu token", Gfx.TEXT_JUSTIFY_CENTER);
    }
}

class ReadyDaySettingsDelegate extends WatchUi.BehaviorDelegate {
    function initialize() { BehaviorDelegate.initialize(); }
    function onBack() as Boolean {
        WatchUi.popView(WatchUi.SLIDE_DOWN);
        return true;
    }
}
