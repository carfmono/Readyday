# ReadyDay — Mapa transferible (llms.md)
> Para que cualquier agente o dev pueda intervenir sin romper la app.
> Actualizado: 2026-07-19

---

## Qué hace

App de **readiness diario** multi-wearable (Garmin, Apple Watch futuro, manual).
Calcula un score diario (Recovery / Strain / Balance / Zona) y da una recomendación concreta.
Entrega push notification a las 7am con el score del día.

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI + Python 3.11+ |
| DB | SQLite (volumen Docker `/app/data/`) |
| Auth | JWT (python-jose) + bcrypt |
| IA | Claude Haiku (Anthropic API) — explicaciones en texto natural |
| Push | FCM (Firebase Cloud Messaging) — Android |
| Garmin pull | garminconnect Python lib (fallback; el camino principal es Connect IQ) |
| Encriptación | Fernet (cryptography) — credenciales Garmin por usuario |
| Deploy | Docker + Caddy en VPS. Ruta: `www.fergussononline.org/readyday` |

---

## Árbol de archivos y responsabilidades

```
backend/
├── main.py                    # FastAPI app, lifespan, routers, static files
├── config.py                  # Settings (pydantic-settings, .env)
├── database.py                # SQLAlchemy engine + SessionLocal + init_db()
├── models.py                  # ORM: User, DeviceSnapshot, DailyScore, UserDevice, PushToken
├── schemas.py                 # Pydantic I/O: RegisterRequest, SnapshotIn, ScoreOut, ...
├── auth.py                    # hash_password, verify_password, create_access_token, get_current_user
├── scheduler.py               # APScheduler: job mañanero 7am (sync + push)
├── requirements.txt
├── Dockerfile
├── routers/
│   ├── auth.py                # POST /api/auth/register|login  GET /api/auth/me
│   ├── snapshots.py           # POST /api/snapshots  (entrada multi-wearable)
│   ├── scores.py              # GET /api/scores/today|history
│   ├── devices.py             # POST /api/devices/connect  GET /api/devices
│   └── notifications.py      # POST /api/notifications/register
└── services/
    ├── score_engine.py        # Cálculo puro: compute_daily_readiness() — SIN efectos secundarios
    ├── explanation_engine.py  # generate_explanation() — Claude o plantillas
    ├── notification_service.py # send_score_notification() — FCM
    └── garmin_service.py      # fetch_snapshot() — pull desde Garmin Connect cloud

frontend/
├── landing.html               # Landing page marketing (sirve en /)
└── index.html                 # Dashboard web — sirve en /app/ y /app/{path}

garmin-ciq/                    # Monkey C — app Connect IQ para el reloj
└── source/
    ├── ReadyDayApp.mc         # App principal
    ├── ReadyDayView.mc        # Vista del score en reloj
    ├── ScoreEngine.mc         # Cálculo local (offline)
    └── Communications.mc      # Bridge reloj → companion app Android

mobile/                        # React Native + Expo (Android primero)
└── app/
    ├── (tabs)/index.tsx       # Pantalla Today
    └── auth/login.tsx         # Login / Register

docker-compose.yml
.env.example
```

---

## Costuras de intervención

### Agregar un nuevo wearable (Fitbit, Samsung, etc.)

1. **`schemas.py`** — agregar literal a `WearableSource`: `"fitbit"`
2. **`models.py`** — `WearableSource` enum: agregar valor
3. **`routers/snapshots.py`** — `POST /api/snapshots` ya acepta cualquier source normalizado; si el nuevo wearable necesita transformación, agregar un `_normalize_<source>()` helper ahí
4. **Invariante**: el snapshot llega SIEMPRE en el schema normalizado (`body_battery`, `sleep_score`, etc.) — el score engine no sabe qué dispositivo generó los datos
5. **Blast radius**: solo `snapshots.py` + `schemas.py` + `models.py` — el score engine no se toca

### Cambiar la fórmula del score

- **Archivo**: `services/score_engine.py`
- **Invariante**: todas las funciones son PURAS (sin DB, sin I/O). Input: dict de snapshot + hábitos. Output: dict con scores.
- **Blast radius**: solo el archivo. Verificar: `pytest tests/test_score_engine.py`

### Cambiar el modelo de Claude (explicaciones)

- **Archivo**: `services/explanation_engine.py` — línea `model="claude-haiku-4-5-20251001"`
- **Blast radius**: solo el archivo. Si la API falla, hay fallback a plantillas.

### Cambiar el horario de la notificación push

- **Config**: `.env` → `NOTIFICATION_HOUR=7` (UTC-5 → ajustar según timezone del servidor)
- **Código**: `scheduler.py` — job `morning_sync`
- **Blast radius**: solo `scheduler.py`

### Cambiar la landing page o el routing de rutas web

- **Landing** (`/`): `frontend/landing.html` — página de marketing. Editar este archivo para cambiar copy/branding.
- **App dashboard** (`/app/*`): `frontend/index.html` — dashboard auth completo.
- **Routing en backend**: `main.py` función `serve_landing()` para `/`; `serve_app()` para `/app*`; `serve_static_fallback()` para archivos con extensión.
- **Blast radius**: solo `main.py` + los dos HTML. No afecta API.
- **Center** (`/data/proyectos/caddy/site/center/index.html`): acceso directo al servicio en el panel central del servidor — array `SERVICES`.

### Agregar autenticación OAuth (en lugar de email/password)

- **Punto de extensión**: `routers/auth.py` — agregar endpoint `/api/auth/oauth/<provider>`
- **Invariante**: el JWT que se emite debe tener el mismo shape (`sub=user_id, email, exp`)
- **Blast radius**: `routers/auth.py` + nuevo servicio OAuth. `get_current_user` en `auth.py` no cambia.

---

## Invariantes del sistema (no romper)

1. **Score engine es puro** — `compute_daily_readiness()` no toca DB ni I/O
2. **Snapshot normalizado** — cualquier wearable convierte sus datos al schema antes de llegar al score engine
3. **Claude es opcional** — si `ANTHROPIC_API_KEY` está vacío, la app funciona con plantillas
4. **FCM es opcional** — si `FCM_SERVER_KEY` está vacío, los push se omiten silenciosamente
5. **Credenciales Garmin encriptadas** — nunca se guardan en texto plano; usar `encrypt_credentials()` de `garmin_service.py`
6. **SQLite con volumen** — el archivo DB está en `/app/data/readyday.db` (volumen Docker). Si cambias la ruta, actualizar `config.py` + `docker-compose.yml`

---

## Cómo verificar después de intervenir

```bash
# Levantar el stack
cd /data/proyectos/readyday && docker compose up -d

# Ver logs
docker logs readyday-api -f

# Smoke test rápido
curl http://localhost:8001/health

# Crear usuario de prueba
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"testpass123","name":"Test"}'

# Subir snapshot manual
TOKEN="<token del step anterior>"
curl -X POST http://localhost:8001/api/snapshots \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"manual","captured_at":"2026-07-19T07:00:00Z","body_battery":75,"sleep_score":80,"hr_resting":58,"stress_avg":30}'
```

---

## Variables de entorno requeridas

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `SECRET_KEY` | ✅ | JWT signing key (32+ chars random) |
| `ANTHROPIC_API_KEY` | ⚠️ Opcional | Claude API (si vacío → plantillas) |
| `FCM_SERVER_KEY` | ⚠️ Opcional | Firebase push (si vacío → sin push) |
| `ENCRYPTION_KEY` | ⚠️ Opcional | Fernet key para credenciales Garmin |
| `NOTIFICATION_HOUR` | default: 7 | Hora del push mañanero (servidor local) |

---

## Garmin Connect IQ — notas de integración

El watch app (Monkey C en `garmin-ciq/`) **pushea** datos al companion Android.
La app Android reenvía al backend via `POST /api/snapshots` con `source: "garmin"`.
El backend NUNCA llama directamente al reloj — el flujo es siempre: reloj → teléfono → API.

El `garmin_service.py` (pull desde nube) es el fallback para usuarios que sincronizan el reloj
pero no tienen la app abierta. Se activa desde el scheduler nocturno.
