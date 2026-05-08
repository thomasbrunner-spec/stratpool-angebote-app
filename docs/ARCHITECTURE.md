# Architecture

Tech-Stack-Entscheidungen für Apps in der StratPool-Plattform.

## Stack-Übersicht

| Schicht | Tool | Warum |
|---|---|---|
| Backend | FastAPI 0.115+ | Async, OpenAPI auto-gen, Pydantic-Validierung |
| Backend Build | uv | 10-100x schneller als pip, lockfiles, modern |
| Backend Lint | Ruff | Ersetzt black + flake8 + isort, ultraschnell |
| Backend ORM | SQLAlchemy 2.0 | Async-Support, Type-Hints |
| Backend Migrations | Alembic | Standard für SQLAlchemy |
| LLM | Anthropic SDK direkt | Kein LangChain-Overhead, volle Kontrolle |
| Embeddings | Voyage AI | Anthropic-empfohlen, generöser Free Tier |
| Frontend | Next.js 15 | App Router, React Server Components, Streaming |
| Frontend State | RSC + minimal Client State | Keine Redux-Komplexität |
| Auth | Supabase Auth | Integriert mit Supabase DB, Magic Links |
| DB | Postgres (via Supabase) | Volle SQL-Power, pgvector für Embeddings |
| Container | Docker | Standard, läuft überall |
| Orchestrierung | Docker Compose | Kein K8s nötig für Solo-Plattform |
| Deployment | Coolify | Self-Hosted Heroku-Alternative |
| Reverse Proxy | Traefik (über Coolify) | Auto-SSL, Auto-Routing |
| CI/CD | GitHub Actions | Standard, kostenlos für Private Repos |
| Versioning | Release Please | Auto-Versionierung aus Conventional Commits |

## Daten-Flow

```
User-Browser
    ↓ HTTPS
Traefik (Coolify)
    ↓
Frontend (Next.js, Port 3000)
    ↓ HTTP intern (Container-Netzwerk)
Backend (FastAPI, Port 8000)
    ↓
    ├── Supabase Postgres (Datenbank)
    ├── Anthropic API (LLM)
    └── Voyage AI (Embeddings)
```

## Auth-Flow

1. User → Login auf Frontend (Email + Passwort)
2. Frontend → Supabase Auth → JWT zurück
3. JWT wird in HTTP-Only Cookie gespeichert (via @supabase/ssr)
4. Bei jedem API-Call ans Backend:
   - Frontend-API-Helper (`lib/api.ts`) holt JWT aus Cookie
   - Hängt ihn als `Authorization: Bearer <jwt>` an Request
5. Backend (`services/auth.py`) verifiziert JWT mit `JWT_SECRET` (Supabase Secret)
6. Bei gültigem JWT: Request läuft, User-Info verfügbar via `CurrentUser`-Dependency

## Multi-App-Architektur

Mehrere Apps können auf derselben Supabase-Instanz laufen:
- Eigene Tabellen pro App (Schema-Trennung oder Prefix-Konvention)
- Geteilte `auth.users`-Tabelle (Single Sign-On über alle Apps)
- Geteilter Storage (mit Bucket-Trennung)

## Skalierung

Aktuell: Single-VPS-Setup für Solo-Plattform.

Später möglich (ohne Architekturänderung):
- Coolify auf größerem VPS (vertikal skalieren)
- Externer Postgres (Supabase Cloud, PgBouncer für Connection Pooling)
- CDN vor Frontend
- Background-Jobs in eigene Worker-Container (z.B. Arq)

## Was wir bewusst NICHT verwenden

- **Kubernetes**: Massiv Overkill für Solo-Plattform
- **Microservices**: Eine App = ein Backend + ein Frontend, kein Mesh
- **GraphQL**: REST mit FastAPI ist einfacher und für unsere Use Cases ausreichend
- **Server Actions** (für API-Calls): Wir nutzen FastAPI als Backend, nicht
  Next.js Server Actions, weil Backend-Logik in Python liegt (LLM, Embeddings)
- **LangChain/LlamaIndex**: Direkte Anthropic SDK + Voyage SDK reicht und ist robuster
