# ReadyDay — Arquitectura MVP + Guía de Implementación

> Versión: 0.1.0 | Fecha: Abril 2026

---

## 1. Stack Tecnológico (100% Gratuito en MVP)

### Resumen

| Capa | Tecnología | Por qué | Coste |
|------|-----------|---------|-------|
| Reloj Garmin | Monkey C + Connect IQ SDK | Nativo, único camino | Gratis |
| App móvil | React Native + Expo | iOS + Android, SDK Garmin disponible | Gratis |
| Backend API | FastAPI (Python) | Rápido, tipado, OpenAPI auto | Gratis |
| Base de datos (dev) | SQLite | Sin servidor, zero config | Gratis |
| Base de datos (prod) | Supabase PostgreSQL | Free tier 500MB, auth incluida | Gratis |
| Auth | Supabase Auth | JWT, OAuth, magic link | Gratis |
| Hosting backend | Railway.app | 500h/mes gratis, deploy con `git push` | Gratis |
| Hosting landing | Vercel | Deploy automático desde GitHub | Gratis |
| AI explicaciones | Claude API (Anthropic) | $0.003/1k tokens, ~$0.001 por usuario/día | Pay-per-use |
| CI/CD | GitHub Actions | 2000 min/mes gratis | Gratis |
| Monitoreo | Better Uptime (free) o Sentry (free tier) | Alertas y errores | Gratis |

---

## 2. Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────┐
│                   GARMIN WATCH                       │
│  ┌─────────────────────────────────────────────┐    │
│  │         Connect IQ Widget/App                │    │
│  │  - Lee: Body Battery, HR, Stress, Sleep      │    │
│  │  - Calcula: score preliminar local           │    │
│  │  - Muestra: score + recomendación            │    │
│  │  - Comunica via: Communications module       │    │
│  └──────────────────┬──────────────────────────┘    │
└─────────────────────┼───────────────────────────────┘
                      │ Garmin Connect IQ Mobile SDK
                      │ (BLE / companion app channel)
┌─────────────────────▼───────────────────────────────┐
│                 MOBILE APP (React Native)             │
│  ┌─────────────────────────────────────────────┐    │
│  │  GarminBridgeService                         │    │
│  │  - Recibe snapshot del reloj                 │    │
│  │  - Cachea en SQLite local                    │    │
│  │  - Envía al backend                          │    │
│  └──────────────────┬──────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │  Screens                                     │    │
│  │  - Home (score + recomendación)              │    │
│  │  - Detail (breakdown de factores)            │    │
│  │  - Trends (7/30 días)                        │    │
│  │  - Settings (defaults, goal, idioma)         │    │
│  └──────────────────┬──────────────────────────┘    │
└─────────────────────┼───────────────────────────────┘
                      │ HTTPS REST API
┌─────────────────────▼───────────────────────────────┐
│              BACKEND (FastAPI + Python)               │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ Score Engine │  │Insights Svc  │  │ AI Layer  │ │
│  │ (algorithm)  │  │(correlaciones│  │(Claude API│ │
│  │              │  │ semanales)   │  │textos)    │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘ │
│         └─────────────────┼────────────────┘        │
│  ┌──────────────────────────────────────────────┐   │
│  │         PostgreSQL (Supabase)                 │   │
│  │  users | snapshots | scores | insights       │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 3. Flujo de Datos Diario

```
07:00 AM — Usuario despierta

1. Garmin reloj:
   └─ Lee Body Battery, HR nocturno, Stress overnight
   └─ Calcula score preliminar (offline)
   └─ Muestra en widget: "🟡 62 — Entrena suave"

2. Usuario abre app móvil:
   └─ GarminBridgeService recibe snapshot del reloj
   └─ Mezcla: snapshot + defaults usuario + override si existe
   └─ POST /device/snapshot → backend

3. Backend recibe snapshot:
   └─ ScoreEngine calcula score canónico
   └─ Si hay cambio de zona → genera explicación (Claude API)
   └─ Guarda en daily_scores
   └─ Retorna: { recovery, strain, zone, recommendation, explanation }

4. App móvil muestra:
   └─ Score final + recomendación + explicación natural
   └─ Sincroniza resumen al reloj

5. Usuario (opcional, 0 fricción):
   └─ Ajusta hábitos de hoy si son diferentes a defaults
   └─ App recalcula localmente sin llamar al backend
```

---

## 4. Estructura del Monorepo

```
readyday/
├── garmin-ciq/                    # Monkey C — Connect IQ
│   ├── source/
│   │   ├── ReadyDayApp.mc         # App principal
│   │   ├── ReadyDayGlance.mc      # Widget rápido
│   │   ├── views/
│   │   │   ├── MainView.mc        # Score principal
│   │   │   ├── WhyView.mc         # ¿Por qué?
│   │   │   └── HabitsView.mc      # Hábitos de hoy
│   │   ├── ScoreEngine.mc         # Algoritmo local
│   │   ├── Communications.mc      # Bridge móvil
│   │   └── Storage.mc             # Cache local
│   ├── resources/
│   │   ├── strings/strings.xml    # Español
│   │   └── strings/strings-en.xml # English
│   └── manifest.xml
│
├── mobile-app/                    # React Native + Expo
│   ├── app/
│   │   ├── (tabs)/
│   │   │   ├── index.tsx          # Today screen
│   │   │   ├── trends.tsx         # Trends screen
│   │   │   └── settings.tsx       # Settings screen
│   │   ├── detail.tsx             # Modal detail
│   │   └── onboarding/
│   │       ├── language.tsx
│   │       ├── goal.tsx
│   │       └── defaults.tsx
│   ├── services/
│   │   ├── garmin-bridge.ts       # Connect IQ Mobile SDK
│   │   ├── api.ts                 # Backend calls
│   │   └── local-cache.ts         # SQLite offline
│   ├── store/
│   │   └── useAppStore.ts         # Zustand state
│   └── utils/
│       ├── algorithm.ts           # Score calculation (mirror)
│       └── i18n.ts                # Translations
│
├── backend-api/                   # FastAPI + Python
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── device.py
│   │   │   ├── scores.py
│   │   │   ├── insights.py
│   │   │   └── overrides.py
│   │   ├── services/
│   │   │   ├── score_engine.py    # Core algorithm
│   │   │   ├── insights_service.py
│   │   │   └── ai_service.py      # Claude API
│   │   ├── models/
│   │   │   └── db.py              # SQLAlchemy models
│   │   └── schemas/
│   │       └── api.py             # Pydantic schemas
│   ├── alembic/                   # DB migrations
│   ├── tests/
│   └── requirements.txt
│
├── shared-types/                  # Contratos compartidos
│   └── types.ts
│
└── docs/
    ├── algorithm.md
    ├── garmin-api-notes.md
    └── data-contract.md
```

---

## 5. Modelo de Datos

### Tabla: users
```sql
CREATE TABLE users (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email       TEXT UNIQUE NOT NULL,
  language    TEXT DEFAULT 'es',
  goal        TEXT DEFAULT 'health',  -- health | performance | longevity
  timezone    TEXT DEFAULT 'America/Bogota',
  created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### Tabla: user_defaults
```sql
CREATE TABLE user_defaults (
  user_id           UUID REFERENCES users(id),
  caffeine_late     BOOLEAN DEFAULT FALSE,
  alcohol           BOOLEAN DEFAULT FALSE,
  late_dinner       BOOLEAN DEFAULT FALSE,
  updated_at        TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_id)
);
```

### Tabla: device_snapshots
```sql
CREATE TABLE device_snapshots (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             UUID REFERENCES users(id),
  captured_at         TIMESTAMPTZ NOT NULL,
  body_battery        INT,          -- 0-100
  body_battery_min    INT,          -- overnight min
  stress_avg          INT,          -- 0-100
  stress_night        INT,          -- overnight avg
  hr_resting          INT,          -- bpm
  hr_avg_8h           INT,          -- bpm
  sleep_score         INT,          -- 0-100
  sleep_hours         DECIMAL(3,1),
  activity_load       INT,          -- 0-100 proxy
  recovery_time_h     INT,          -- hours
  source_device       TEXT DEFAULT 'garmin_venu3'
);
```

### Tabla: daily_overrides
```sql
CREATE TABLE daily_overrides (
  user_id         UUID REFERENCES users(id),
  date            DATE NOT NULL,
  caffeine_late   BOOLEAN,
  alcohol         BOOLEAN,
  late_dinner     BOOLEAN,
  energy_override INT,  -- 0-4 (muy baja → muy alta)
  PRIMARY KEY (user_id, date)
);
```

### Tabla: daily_scores
```sql
CREATE TABLE daily_scores (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                 UUID REFERENCES users(id),
  date                    DATE NOT NULL,
  recovery_score          INT NOT NULL,      -- 0-100
  strain_score            INT NOT NULL,      -- 0-100
  balance_score           DECIMAL(5,1),
  readiness_zone          TEXT NOT NULL,     -- green | yellow | red
  recommendation_code     TEXT,              -- rec_green | rec_yellow | rec_red
  explanation_es          TEXT,
  explanation_en          TEXT,
  snapshot_id             UUID REFERENCES device_snapshots(id),
  UNIQUE(user_id, date)
);
```

### Tabla: insights
```sql
CREATE TABLE insights (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES users(id),
  generated_at    TIMESTAMPTZ DEFAULT NOW(),
  insight_type    TEXT,  -- alcohol_impact | caffeine_impact | sleep_pattern
  payload         JSONB,
  is_read         BOOLEAN DEFAULT FALSE
);
```

---

## 6. Algoritmo de Scoring

### Recovery Score (0–100)
```python
def calc_recovery_score(body_battery, stress_avg, hr_resting, sleep_score):
    # HR proxy: normalizar entre 40-80 bpm
    hr_score = max(0, min(100, 100 - ((hr_resting - 40) / 30) * 100))
    stress_score = 100 - stress_avg  # invertir
    sleep = sleep_score if sleep_score else 60  # fallback

    return round(clamp(
        0.35 * body_battery +
        0.25 * stress_score +
        0.20 * hr_score +
        0.20 * sleep
    , 0, 100))
```

### Strain Score (0–100)
```python
def calc_strain_score(activity_load, recovery_time_h, stress_avg, habits):
    rt_penalty = (
        85 if recovery_time_h >= 48 else
        65 if recovery_time_h >= 36 else
        45 if recovery_time_h >= 24 else
        25 if recovery_time_h >= 12 else 10
    )
    habit_penalty = (
        (22 if habits.caffeine_late else 0) +
        (28 if habits.alcohol else 0) +
        (15 if habits.late_dinner else 0)
    )
    return round(clamp(
        0.40 * activity_load +
        0.25 * rt_penalty +
        0.20 * stress_avg +
        0.15 * min(habit_penalty, 100)
    , 0, 100))
```

### Balance y Zona
```python
balance = recovery - (strain / 2)

zone = (
    "green"  if recovery >= 70 and balance >= 20 else
    "yellow" if recovery >= 45 else
    "red"
)
```

### Fallbacks si datos no disponibles
```python
# Sin sleep → redistribuir peso
if not sleep_score:
    recovery = round(
        0.50 * body_battery +
        0.30 * stress_score +
        0.20 * hr_score
    )

# Sin HRV directa → usar HR resting como proxy
# (ya incorporado en hr_score)

# Sin recovery time Garmin → estimar con:
#   activity_load + time_in_high_hr + stress_residual
def estimate_recovery_time(activity_load, hr_avg_post, stress_residual):
    base = activity_load * 0.6
    hr_factor = max(0, (hr_avg_post - 70) * 0.4)
    return round(base + hr_factor + stress_residual * 0.2)
```

---

## 7. API Endpoints (FastAPI)

```
POST   /auth/signup            → Registro
POST   /auth/login             → Login (Supabase JWT)
GET    /me                     → Perfil usuario
PATCH  /me/preferences         → Actualizar idioma/objetivo

GET    /defaults               → Hábitos por defecto
PATCH  /defaults               → Actualizar defaults

POST   /device/snapshot        → Enviar datos Garmin del día
GET    /device/latest          → Último snapshot

GET    /scores/today           → Score del día
GET    /scores/history?days=7  → Historial últimos N días

PUT    /overrides/today        → Override hábitos del día
GET    /overrides/today        → Override actual

GET    /insights/latest        → Últimos 5 insights
```

---

## 8. Configuración de Servicios Gratuitos

### Paso 1: Supabase (DB + Auth)
```bash
# 1. Ir a supabase.com → New project (gratis)
# 2. Copiar URL y anon key
# 3. Ejecutar las migraciones SQL del modelo de datos
# 4. En tu .env:
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGci...
DATABASE_URL=postgresql://postgres:pass@db.xxxxx.supabase.co:5432/postgres
```

### Paso 2: Railway (Backend hosting)
```bash
# 1. Ir a railway.app → New project → Deploy from GitHub
# 2. Seleccionar carpeta backend-api/
# 3. Agregar variables de entorno
# 4. Deploy automático en cada push a main
# URL: https://readyday-api.up.railway.app
```

### Paso 3: Garmin Connect IQ SDK
```bash
# 1. Descargar: developer.garmin.com/connect-iq/sdk
# 2. Instalar VSCode Extension: "Monkey C" de Garmin
# 3. Crear cuenta en developer.garmin.com
# 4. Configurar device simulators (Venu 3, Fenix 7, etc.)
# 5. Para publicar: Garmin Connect IQ Store (gratis)
```

### Paso 4: Expo (React Native)
```bash
npm install -g expo-cli
npx create-expo-app ReadyDay --template blank-typescript
cd ReadyDay
npx expo install expo-sqlite @react-navigation/native zustand

# Para Garmin Mobile SDK:
# iOS: CocoaPod ConnectIQ
# Android: ConnectIQ Android SDK (aar)
```

### Paso 5: Claude API (explicaciones)
```bash
# 1. console.anthropic.com → API Keys
# 2. En tu backend .env:
ANTHROPIC_API_KEY=sk-ant-...

# Ejemplo de uso (Python):
from anthropic import Anthropic
client = Anthropic()

def generate_explanation(zone, factors, lang='es'):
    prompt = f"""
    Genera una explicación en {lang} de máximo 2 frases para un usuario
    cuyo score de recuperación es {zone}.
    Factores: {factors}
    Tono: cercano, simple, sin jerga técnica.
    """
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",  # el más barato
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text
```

---

## 9. Garmin Connect IQ — Notas Clave

### APIs disponibles en Connect IQ (confirmadas)
```monkey-c
// Body Battery History
var bodyBatteryHistory = SensorHistory.getBodyBatteryHistory({
    :period => 60,  // minutos
    :order => SensorHistory.ORDER_NEWEST_FIRST
});

// Heart Rate History
var hrHistory = SensorHistory.getHeartRateHistory({
    :period => 480,  // 8 horas
    :order => SensorHistory.ORDER_NEWEST_FIRST
});

// Stress History
var stressHistory = SensorHistory.getStressHistory({
    :period => 480,
    :order => SensorHistory.ORDER_NEWEST_FIRST
});

// Sleep data (si disponible)
var sleepData = UserProfile.getSleepStatistics();

// Activity info
var activityInfo = Activity.getActivityInfo();
```

### Comunicación Reloj → Móvil
```monkey-c
// En el reloj (Monkey C)
Communications.transmit(snapshot, null, new TransmitCallback());

// En la app móvil (React Native)
ConnectIQ.addReceiveFileListener(deviceId, (data) => {
    garminBridgeService.processSnapshot(data);
});
```

### Diseño de pantallas (limitaciones Garmin)
- **Resolución Venu 3**: 454 x 454 px (redonda)
- **Colores**: hasta 64K colores (AMOLED)
- **Memoria**: ~128KB heap
- **Sin scroll nativo** → usar gestos (swipe up/down)
- **Máximo 3 pantallas por app** recomendado

---

## 10. Sprint Plan

### Sprint 1 (Semana 1–2): Foundation
- [ ] Repositorio GitHub + monorepo setup
- [ ] Backend FastAPI básico + modelo de datos
- [ ] Supabase setup (DB + auth)
- [ ] Mock data + score engine Python
- [ ] HTML MVP para validar UX (✅ DONE)

### Sprint 2 (Semana 3–4): Core
- [ ] Connect IQ app skeleton + views
- [ ] React Native app + Expo setup
- [ ] Integración Garmin Mobile SDK
- [ ] Endpoint /device/snapshot funcionando

### Sprint 3 (Semana 5–6): Polish
- [ ] Historial + tendencias
- [ ] Insights automáticos
- [ ] Claude API para explicaciones
- [ ] Bilingüe (ES/EN) en todas las capas

### Sprint 4 (Semana 7–8): Launch
- [ ] Testing en dispositivo real
- [ ] Publicar en Garmin Connect IQ Store
- [ ] Beta testing iOS + Android
- [ ] Landing page (Vercel)

---

## 11. Costes Estimados MVP (6 primeros meses)

| Concepto | Plan | Coste/mes |
|---------|------|----------|
| Supabase (DB + Auth) | Free | $0 |
| Railway (backend) | Free (500h) | $0 |
| Garmin Store | Developer account | $0 |
| Expo (React Native) | Free | $0 |
| GitHub | Free | $0 |
| Claude API (explicaciones) | ~1000 usuarios × $0.002 | ~$2 |
| Dominio | Si se quiere | ~$12/año |
| **TOTAL** | | **~$2/mes** |

### Cuando escalar (>1000 usuarios activos)
- Supabase Pro: $25/mes
- Railway Pro: $20/mes
- Cloudflare Workers (edge): $5/mes

---

## 12. Diferencial vs Competencia

| Feature | Garmin nativo | Whoop | ReadyDay |
|---------|--------------|-------|---------|
| Score diario | ✓ | ✓ | ✓ |
| Explicación humana | ✗ | Parcial | ✓ |
| Decisión clara (qué hacer) | ✗ | ✗ | ✓ |
| Hábitos correlacionados | ✗ | ✗ | ✓ |
| Sin dispositivo extra | N/A | ✗ | ✓ |
| En tu Garmin existente | ✓ | ✗ | ✓ |
| Precio | Gratis | $30/mes | Freemium |

---

*ReadyDay MVP — Construido con Claude Code*
*"Know your body. Decide your day."*
