# Projekt: stratpool-angebote-app

> Diese Datei ergänzt die globale `~/.claude/CLAUDE.md`.

## Über dieses Projekt

**Name:** Angebote-App
**Zweck:** AI-gestützter Generator für ERA-Group-Angebote — Discovery-Call-Transkript + Preis + Anmerkungen → Few-Shot-Retrieval aus Bestandsangeboten → Anthropic Claude → strukturiertes Angebots-JSON → Word/PowerPoint-Render im ERA-CI.
**Repo:** `thomasbrunner-spec/stratpool-angebote-app`
**Subdomain:** `angebote.stratpool.pro`
**Status:** In Entwicklung (Etappe 2 der StratPool-Plattform)

## Architektur

Standard-Monorepo aus dem `stratpool-app-template`. Backend in `backend/` (FastAPI), Frontend in `frontend/` (Next.js 15). Beide laufen lokal via Docker Compose, deployt via Coolify.

**App-Branding:** StratPool (Dark Mode, Plus Jakarta Sans, Signal Blue).
**Output-Branding:** ERA Group (Word/PowerPoint im ERA-CI über die `era-word`- und `era-presentation`-Skills).
Diese Trennung ist Architektur, nicht Detail.

## Datenmodell (Supabase)

Schon in Supabase angelegt (mit RLS), Code-Modelle folgen in Etappe 2 Block 2:

- `offers` — Angebot-Stammdaten (Kunde, Datum, Status: Entwurf | Versendet | Gewonnen | Verloren, Preis, Themen)
- `offer_versions` — Versionsverlauf eines Angebots (Inhalt, Erstellungs-Metadaten)
- `offer_embeddings` — pgvector-Embeddings je Version, für Few-Shot-Retrieval bei Neugenerierungen

## Was bei diesem Projekt anders ist

- **DB-Verbindung lokal via SSH-Tunnel** (siehe Abschnitt unten) — Supabase-Postgres ist auf dem VPS nicht öffentlich erreichbar
- **Output-Skills:** `era-word` und `era-presentation` sind die einzigen erlaubten Wege, Word/PPT zu generieren — niemals python-docx daneben
- **Lernschicht:** Gewonnene Angebote bekommen im Retrieval höheres Gewicht als Verlorene (kommt in Etappe 4)

## Lokale DB-Verbindung (SSH-Tunnel)

Supabase-Postgres ist nicht öffentlich exposed. Lokal arbeiten wir mit:

1. **Bridge-Container auf dem VPS** (einmalig, persistent, nur an `127.0.0.1` des VPS gebunden):
   ```
   docker run -d --restart unless-stopped --name pg-tunnel-bridge \
     --network cv9l7oliqkgmiu4hr8oufncd \
     -p 127.0.0.1:5432:5432 \
     alpine/socat tcp-listen:5432,fork,reuseaddr \
     tcp-connect:supabase-db-cv9l7oliqkgmiu4hr8oufncd:5432
   ```

2. **SSH-Tunnel auf dem Mac** (in eigenem Terminal-Tab, läuft solange du arbeitest):
   ```
   ssh -N -L 5432:127.0.0.1:5432 root@72.61.157.171
   ```

3. **`DATABASE_URL`** im `.env` zeigt auf `host.docker.internal:5432` (Mac-Host aus Sicht des Backend-Containers).

## Wichtige Pfade

```
backend/app/main.py             # FastAPI-Entry
backend/app/services/           # Business-Logic (LLM, Embeddings, Auth)
backend/app/routes/             # API-Endpoints (health bereits da, offers folgt)
backend/app/models/             # SQLAlchemy-Models (offers/versions/embeddings — Etappe 2 B2)
backend/app/prompts/            # Anthropic-Prompts für Angebots-Generierung
frontend/app/                   # Next.js Pages
frontend/components/            # React-Komponenten
frontend/lib/api.ts             # Backend-API-Helper mit Auth
docker-compose.yml              # Coolify-Deployment
```

## Häufige Aufgaben

### Lokale Entwicklung
```bash
# Tunnel im eigenen Tab offen lassen:
ssh -N -L 5432:127.0.0.1:5432 root@72.61.157.171

# Container:
docker compose up -d --build
docker compose logs -f
docker compose down

# Health (vom Container aus):
docker compose exec backend python -c "import urllib.request, json; \
  print(json.dumps(json.loads(urllib.request.urlopen('http://localhost:8000/api/v1/health/full').read()), indent=2))"
```

### Tests
```bash
cd backend && uv run pytest
cd frontend && pnpm typecheck
```

### Datenbank-Migration
```bash
cd backend && uv run alembic revision -m "describe change"
# Datei in alembic/versions/ anpassen, dann:
uv run alembic upgrade head
```

### Release
- Push auf `main` mit Conventional Commit → Release Please erstellt PR
- Merge des PRs → automatischer Tag + Release
- Coolify watcht das Repo und deployt automatisch

## Anmerkungen für Claude Code

- **Backend nutzt async überall** (FastAPI + SQLAlchemy 2.0 async)
- **Anthropic-Aufrufe** über `app.services.llm.simple_completion()` oder direkt mit `get_anthropic_client()` für komplexere Calls
- **Embeddings** über `app.services.embeddings.embed_text()` (Voyage)
- **Auth** über die `CurrentUser`-Dependency in jedem Route, der Auth braucht:
  ```python
  from app.services.auth import CurrentUser

  @router.get("/protected")
  async def protected(user: CurrentUser):
      return {"user_id": user.id}
  ```
- **Frontend → Backend**: Immer `lib/api.ts` benutzen (hängt automatisch JWT an)
- **Niemals** `private: true` in `package.json` setzen
- **Niemals** `pnpm version` doppelt definieren

## Template-Bugs, die hier gefixt wurden (für Upstream-PR ans Template)

1. **Lockfiles nicht ausgeliefert** — `pnpm-lock.yaml` und `uv.lock` müssen ins Template
2. **`secrets.environment` in `docker-compose.yml`** ist unzuverlässig — auf `secrets.file` umstellen
3. **Token-Injection im Frontend-Dockerfile** — `npm config set` schreibt in `~/.npmrc`, pnpm liest aber projekt-`.npmrc` zuerst → Token muss direkt in projekt-`.npmrc` injiziert werden
4. **TS-Strict-Mode-Fehler** in `frontend/lib/supabase/{middleware,server}.ts` — `cookiesToSet` braucht explizite `CookieOptions`-Annotation

## Roadmap

- [x] Block 1 — App-Identität säubern (CLAUDE.md, package.json, pyproject.toml, layout-Metadata)
- [ ] Block 2 — SQLAlchemy-Models für offers/versions/embeddings + Alembic-Baseline
- [ ] Block 3 — Bestandsangebote (4 anonymisierte) einseeden
- [ ] Block 4 — Generierungs-Pipeline (POST /api/v1/offers/generate)
- [ ] Block 5 — Frontend (Eingabe-Form, Vorschau, Versions-History, Status-Tagging)
- [ ] Block 6 — Word/PPT-Render via era-word / era-presentation Skills
- [ ] Block 7 — DNS-A-Record + Coolify-Deployment
