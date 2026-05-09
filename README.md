# Stratpool App Template

> 🚀 GitHub Template Repository für neue Apps in der Stratpool-Plattform

Dieses Template enthält alles, was du brauchst, um eine neue App zu starten:
- ✅ FastAPI Backend (Python 3.12 + uv + Ruff)
- ✅ Next.js 15 Frontend (TypeScript + Tailwind + Design System)
- ✅ Supabase Auth (Login, geschützte Routes, Session-Handling)
- ✅ Anthropic SDK + Voyage AI integriert
- ✅ Docker Compose für Coolify-Deployment
- ✅ GitHub Actions: CI + Release Please

## 🎯 Schnellstart: Neue App aus Template erstellen

### 1. Template benutzen

Auf GitHub: Klick auf **"Use this template"** → **"Create a new repository"**

| Feld | Wert |
|---|---|
| Owner | `thomasbrunner-spec` |
| Repository name | `stratpool-<app-name>` (z.B. `stratpool-angebote`) |
| Visibility | Private |

### 2. Lokal klonen

```bash
cd ~/Desktop/Claude-Code
git clone git@github.com:thomasbrunner-spec/stratpool-<app-name>.git
cd stratpool-<app-name>
```

### 3. Environment-Dateien erstellen

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Werte aus deinem Passwort-Manager eintragen:
- `ANTHROPIC_API_KEY`
- `VOYAGE_API_KEY`
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `JWT_SECRET`
- `DATABASE_URL` (Supabase Postgres connection string)
- `GITHUB_PACKAGES_TOKEN` (für `@thomasbrunner-spec/design-system`)

### 4. Lokal starten

#### Option A: Docker Compose (empfohlen, identisch zur Produktion)

```bash
docker compose up --build
```

Frontend: http://localhost:3000
Backend: http://localhost:8000/docs

#### Option B: Native (für Entwicklung)

Backend:
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Frontend (anderes Terminal):
```bash
cd frontend
pnpm install
pnpm dev
```

### 5. Verifikation

- Öffne http://localhost:3000 → Landing Page mit Stratpool-Logo
- Klick "Sign in" → Login-Seite
- Login mit Supabase-Credentials → Dashboard
- Klick "Generate haiku" → wenn ein Haiku erscheint, läuft die ganze Pipeline:
  Frontend → Backend → Anthropic API → zurück

## 🛠 Entwicklungs-Workflow

### Conventional Commits + Release Please

```bash
git commit -m "feat: add offer generation endpoint"   # → Minor bump
git commit -m "fix: correct prompt template"           # → Patch bump
git commit -m "feat!: rename API endpoints"            # → Major bump
git commit -m "docs: update README"                    # → kein Bump
```

Push → Release Please erstellt PR → Merge → automatischer Tag + Release.

### Tests

```bash
# Backend
cd backend && uv run pytest

# Frontend
cd frontend && pnpm typecheck
```

### Lint + Format

```bash
# Backend
cd backend && uv run ruff check . && uv run ruff format .

# Frontend
cd frontend && pnpm lint && pnpm format
```

## 🚢 Deployment auf Coolify

Siehe `docs/DEPLOYMENT.md` für die vollständige Anleitung.

Kurzfassung:

1. In Coolify: New Resource → Application → Docker Compose
2. Git-Repo verbinden
3. Environment Variables setzen (alle aus `.env.example`)
4. Build Secret `npm_token` setzen (= `GITHUB_PACKAGES_TOKEN`)
5. Domain konfigurieren (z.B. `<app-name>.stratpool.pro`)
6. Deploy

## 📁 Projektstruktur

```
.
├── backend/                 # FastAPI app
│   ├── app/
│   │   ├── main.py          # Entry point
│   │   ├── config.py        # Pydantic Settings
│   │   ├── db.py            # Async SQLAlchemy
│   │   ├── routes/          # FastAPI routers
│   │   ├── services/        # Business logic
│   │   └── models/          # SQLAlchemy models
│   ├── tests/
│   ├── alembic/             # Database migrations
│   ├── pyproject.toml       # uv + dependencies
│   └── Dockerfile
├── frontend/                # Next.js 15 app
│   ├── app/                 # App Router pages
│   ├── components/          # React components
│   ├── lib/                 # Helpers (Supabase, API)
│   ├── middleware.ts        # Session refresh + route guards
│   ├── package.json
│   └── Dockerfile
├── .github/workflows/       # CI + Release
├── docker-compose.yml       # Local dev + Coolify
├── CLAUDE.md                # Anweisungen für Claude Code
└── README.md
```

## 🔧 Was du für jede neue App ändern musst

1. **In `package.json` (frontend) und `pyproject.toml` (backend):** `name`-Felder an deine App anpassen
2. **In `docker-compose.yml`:** `COMPOSE_PROJECT_NAME`-Default anpassen
3. **In `frontend/app/layout.tsx`:** Metadata (`title`, `description`)
4. **In `CLAUDE.md`:** Projektspezifischer Kontext (was diese App tut)
5. **In Coolify:** Subdomain, Env-Variablen
6. **In Supabase Studio:** Falls die App eigene Tabellen braucht, Migrationen über Alembic anlegen

## 📚 Weiterführende Doku

- `CLAUDE.md` – Anweisungen für Claude Code in diesem Repo
- `docs/DEPLOYMENT.md` – Coolify-Deployment im Detail
- `docs/ARCHITECTURE.md` – Tech-Stack-Entscheidungen, warum so

## 📦 Versionsstand

- Template Version: 0.1.0
- Last updated: 2026-05-07
