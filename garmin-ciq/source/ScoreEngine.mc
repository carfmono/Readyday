// ScoreEngine.mc — Cálculo de score local (offline)
// Misma fórmula que el backend Python para coherencia perfecta.
// IMPORTANTE: Funciones puras, sin efectos secundarios.

class ScoreEngine {

    // ── HR score (FC reposo → score 0-100) ───────────────
    static function hrScore(hr as Float) as Float {
        if (hr <= 50.0) { return 100.0; }
        if (hr <= 55.0) { return 90.0; }
        if (hr <= 60.0) { return 75.0; }
        if (hr <= 65.0) { return 55.0; }
        if (hr <= 70.0) { return 35.0; }
        return 20.0;
    }

    // ── Clamp ─────────────────────────────────────────────
    static function clamp(v as Float, a as Float, b as Float) as Float {
        if (v < a) { return a; }
        if (v > b) { return b; }
        return v;
    }

    // ── Recovery Score 0-100 ──────────────────────────────
    // Fórmula: 0.35×BB + 0.25×(100-Stress) + 0.20×HRscore + 0.20×Sleep
    static function calcRecovery(
        bodyBattery as Float,
        stressAvg   as Float,
        hrResting   as Float,
        sleepScore  as Float
    ) as Number {
        var score = (0.35 * bodyBattery)
                  + (0.25 * (100.0 - stressAvg))
                  + (0.20 * hrScore(hrResting))
                  + (0.20 * sleepScore);
        return clamp(score, 0.0, 100.0).toNumber();
    }

    // ── Strain Score 0-100 ────────────────────────────────
    static function calcStrain(
        activityLoad   as Float,
        recoveryTimeH  as Float,
        stressAvg      as Float
    ) as Number {
        var rtPenalty;
        if (recoveryTimeH >= 48.0)      { rtPenalty = 85.0; }
        else if (recoveryTimeH >= 36.0) { rtPenalty = 65.0; }
        else if (recoveryTimeH >= 24.0) { rtPenalty = 45.0; }
        else if (recoveryTimeH >= 12.0) { rtPenalty = 25.0; }
        else                            { rtPenalty = 10.0; }

        var score = (0.40 * activityLoad)
                  + (0.25 * rtPenalty)
                  + (0.20 * stressAvg)
                  + (0.15 * 0.0);  // hábitos: 0 en el reloj (se ajusta en el server)
        return clamp(score, 0.0, 100.0).toNumber();
    }

    // ── Balance ───────────────────────────────────────────
    static function calcBalance(recovery as Number, strain as Number) as Float {
        return recovery.toFloat() - (strain.toFloat() / 2.0);
    }

    // ── Zona ─────────────────────────────────────────────
    // Retorna: 0=green, 1=yellow, 2=red
    static function getZone(recovery as Number, balance as Float) as Number {
        if (recovery >= 70 && balance >= 20.0) { return 0; }  // green
        if (recovery >= 45)                    { return 1; }  // yellow
        return 2;                                             // red
    }

    // ── Colores por zona ──────────────────────────────────
    static function zoneColor(zone as Number) as Number {
        if (zone == 0) { return 0x00D4AA; }  // verde
        if (zone == 1) { return 0xF5C842; }  // amarillo
        return 0xFF4D6D;                      // rojo
    }

    // ── Emoji/label por zona ──────────────────────────────
    static function zoneLabel(zone as Number) as String {
        if (zone == 0) { return "VERDE — Entrena fuerte"; }
        if (zone == 1) { return "AMARILLO — Moderado"; }
        return "ROJO — Descansa";
    }
}
