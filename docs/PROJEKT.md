# Projekt-Dossier: Stratpool Angebote-App

> Dieses Dokument ist die Lang-Version. Für die schnelle Übersicht reicht der README.
> Geschrieben am 2026-05-10, nach dem ersten erfolgreichen Coolify-Deploy.

---

## 1. Worum geht's?

Die **Angebote-App** generiert ERA-Group-Angebote aus drei Inputs:

1. **Discovery-Call-Transkript** (was der Kunde im Gespräch gesagt hat)
2. **Preis** (Honorar)
3. **Anmerkungen** (was der Berater dazupacken möchte)

Daraus baut die App in zwei parallelen Schritten:

- ein **strukturiertes JSON-Angebot** (für die Detail-UI im Frontend)
- ein **fertiges Word- und PowerPoint-Dokument** im **ERA-Corporate-Design**, das du an den Kunden schicken kannst

Im Hintergrund nutzt die App **frühere Angebote als Referenz** ("Few-Shot-Retrieval"), damit Stil und Inhaltsstruktur konsistent bleiben.

### Branding-Trennung (wichtig!)

Das ist Architektur, kein Detail:

- **Die App selbst** läuft im **Stratpool-Design** (Dark Mode, Plus Jakarta Sans, Signal Blue) — das ist die Marke deiner KI-Plattform.
- **Die generierten Dokumente** sind im **ERA-Group-Design** — weil die zum Kunden gehen und die ERA-Marke transportieren müssen.

Diese Trennung ist Absicht und sollte nie aufgeweicht werden.

---

## 2. Wie funktioniert sie?

Drei parallele Pipelines:

### A. Generate-Pipeline (Discovery → JSON)
```
Discovery-Transkript + Preis + Notes
        ↓
Voyage AI: Transkript wird in einen Vektor verwandelt ("Embedding")
        ↓
pgvector in Supabase: ähnliche frühere Angebote werden gefunden
        ↓
Anthropic Claude (Opus 4.7): erzeugt strukturiertes Angebots-JSON
        ↓
Speicherung in `offer_versions` (Versionshistorie eingebaut)
```

### B. Render-Pipeline (JSON → Word/PPT im ERA-CI)
```
Discovery-Transkript + Berater-Daten (du + Co-Berater)
        ↓
Anthropic Claude mit "code_execution" + Custom-Skills:
  - era-presentation (für PowerPoint, mit ERA-Template + Layout-Regeln)
  - era-word (für Word, mit ERA-CI-Style-Regeln)
        ↓
Claude komponiert das Deck/Dokument selbst (Folien-Anzahl, Layouts, Inhalt)
        ↓
Datei wird in der Anthropic Files-API gespeichert, wir laden sie runter
        ↓
Speicherung im Supabase-Storage-Bucket `offer-renders`
```

### C. Auth-Pipeline
- Login via **Supabase Auth** im Frontend
- Backend prüft JWT bei jedem geschützten Endpoint
- Im Frontend **nie direkt fetch** — immer `lib/api.ts` benutzen, der hängt das JWT automatisch dran

---

## 3. Tech-Stack (kompakt)

| Schicht | Technologie | Warum |
|---|---|---|
| Backend | FastAPI (Python 3.12), async überall | Performant, einfach, gut mit LLM-Calls |
| Frontend | Next.js 15 (App Router) + TypeScript strict | Moderner React-Stack, SSR, gute DX |
| Datenbank | Supabase (Postgres + pgvector + Auth + Storage) | Eine Plattform für alles, gehostet auf unserem VPS |
| LLM | Anthropic Claude (Opus 4.7) — direktes SDK, **kein LangChain** | Kontrolle, Caching, weniger Magie |
| Embeddings | Voyage AI (`voyage-3-large`) | Beste Qualität für Retrieval, EU-friendly |
| Container | Docker Compose | Standardweg, lokal+Coolify identisch |
| Hosting | Coolify auf Hostinger KVM4 | Self-hosted, GitHub-Webhook-Deployment |
| Render | Anthropic code_execution + Custom-Skills | Claude komponiert die Deck/Doc-Struktur selbst |

---

## 4. Was wurde gebaut (Block für Block)

Die Entwicklung lief in 7 Etappen ("Blöcke"). Alle abgeschlossen, Stand 2026-05-10:

| Block | Was | Wann |
|---|---|---|
| **1** | App-Identität säubern (Naming, Metadata, Branding) | 2026-05-08 |
| **2** | SQLAlchemy-Models für `offers`, `offer_versions`, `offer_embeddings` + Alembic-Baseline-Migration | 2026-05-08 |
| **3** | Voyage-Embeddings + Bestandsangebote-Seed-Skript | 2026-05-08 |
| **4** | Generate-Pipeline: `POST /api/v1/offers/generate` (Embed → Retrieve → Claude → Persist) | 2026-05-08 |
| **5a** | `/angebote/neu` Form + Vorschau-Cards | 2026-05-09 |
| **5b** | `/angebote` Liste + `/angebote/[id]` Detail + Status-Selector | 2026-05-09 |
| **5c** | Versions-History UI | **bewusst zurückgestellt**, Block 6 wichtiger |
| **6** | PPT-Render via Anthropic code_execution + Custom-Skill `era-presentation` | 2026-05-09 |
| **6c** | Word-Render via `era-word`-Skill (analog) | 2026-05-09 |
| **7** | DNS + Coolify-Deployment auf `https://angebote.stratpool.pro` | 2026-05-10 |

---

## 5. Coolify-Deploy-Survival-Kit (was am 10.05. wirklich passiert ist)

Block 7 sah am Vorabend nach "fast fertig" aus — Container `running:healthy`, Domain DNS-resolved, alle ENVs gesetzt. Trotzdem: **HTTP 503 "no available server"** auf der FQDN.

Heute haben wir drei separate Bugs übereinander entdeckt und gefixt. Sie sind alle **ins Template** geflossen, damit die nächste App nicht durch denselben Schmerz muss. Hier die Klartext-Erklärung:

### Bug 1: Healthcheck spricht IPv6, App spricht IPv4
- Healthcheck im Container ruft `http://localhost:3000` auf
- Alpine/BusyBox-Linux löst `localhost` zuerst zu **IPv6** auf (`[::1]`)
- Next.js (und FastAPI) hört aber nur auf **IPv4** (`0.0.0.0`)
- → "Connection refused" → Container wird `unhealthy`
- → Traefik (der Web-Router) **routet niemals zu unhealthy Containern** → 503

**Fix:** Im `docker-compose.yml` Healthcheck explizit `127.0.0.1` statt `localhost` schreiben.

### Bug 2: Traefik weiß nicht, welcher Service zu welchem Router gehört
- Coolify generiert für jede App **zwei** Traefik-Router (einen für HTTP, einen für HTTPS)
- Coolify generiert aber **keine** Service-Port-Bindings für Multi-Service-Setups
- Wenn man selbst zwei Service-Definitionen schreibt (eine pro Router), gibt Traefik den Fehler:
  *"Router cannot be linked automatically with multiple Services"*

**Fix:** **Eine** Service-Definition mit generischem Namen (`frontend`), beide Coolify-Router via `routers.X.service=frontend` explizit darauf zeigen lassen. Die UUID der App wird per ENV-Var (`COOLIFY_APP_UUID`) eingespielt.

### Bug 3: Backend kann die Datenbank nicht finden
- `DATABASE_URL` zeigt auf `supabase-db-<hash>` (Container-Name)
- Backend-Container ist aber **nicht im Supabase-Docker-Network** drin
- → asyncpg: `Temporary failure in name resolution` → API 500

**Fix:** Im `docker-compose.yml` ein externes Network `supabase` referenzieren (Name kommt aus ENV `SUPABASE_NETWORK`) und den Backend-Service da reinhängen.

### Weitere Fixes, die schon im April/Mai gefunden wurden und im Template fehlten:
- **Lockfiles** (`pnpm-lock.yaml`, `uv.lock`) — müssen committed werden, sonst `--frozen-lockfile` kaputt
- **NPM-Token** für GitHub Packages — direkt in projekt-`.npmrc` schreiben (pnpm liest die VOR `~/.npmrc`)
- **Compose-Secrets** unter Coolify unzuverlässig → ersetzt durch plain Build-Args
- **Next.js Public-Vars** als Build-Args übergeben (Next.js inlined `NEXT_PUBLIC_*` zur Build-Time, Runtime-Env reicht nicht)
- **`frontend/public/.gitkeep`** damit das Verzeichnis nach `git clone` existiert
- **TS-Strict-Mode** in Supabase-Helpers braucht explizite `CookieOptions[]`-Annotation

---

## 6. Wo liegt was (Repo- und Plattform-Übersicht)

### Repos auf GitHub (alle in der Org `thomasbrunner-spec`)

| Repo | Zweck |
|---|---|
| **stratpool-angebote-app** | Diese App (öffentlich) |
| **stratpool-app-template** | Template für neue Apps — enthält jetzt alle Coolify-Lessons (PR #1 reviewen + mergen) |
| **stratpool-design-system** | Design Tokens, Logos, UI-Komponenten — npm-Paket `@stratpool/design-system` |
| **stratpool-claude-config** | Globale Claude-Konfiguration, Skills, Decision-Log |

### Live-Systeme

| URL | Was |
|---|---|
| `https://angebote.stratpool.pro` | Diese App, live |
| `https://coolify.stratpool.pro` | Coolify-UI für Deployment + Logs + ENVs |
| `https://supabase.stratpool.pro` | Supabase-Studio (DB, Auth, Storage) |
| VPS: `72.61.157.171` | Hostinger KVM4 — alles drauf |

### Lokales Setup auf dem Mac

| Pfad | Was |
|---|---|
| `~/Desktop/Claude-Code/stratpool-angebote-app/` | Diese App |
| `~/Desktop/Claude-Code/stratpoo-app-template/` | Template-Repo (Tippfehler im Verzeichnis-Namen — Remote ist korrekt) |
| `~/.claude/CLAUDE.md` | **Globale** Anleitungen für Claude — Tech-Stack, Rolle, Don'ts |
| `./CLAUDE.md` (in jedem Repo) | **Projekt-spezifische** Anleitungen — ergänzen die globale |
| `~/.ssh/stratpool_vps` | SSH-Key für VPS (Alias `ssh stratpool-vps`) |

### Wichtige Code-Pfade in dieser App

```
backend/app/main.py              # FastAPI-Entry
backend/app/routes/              # API-Endpoints (offers, consultants, health)
backend/app/services/            # Business-Logic
  llm.py                           # Anthropic-Aufrufe
  embeddings.py                    # Voyage-Aufrufe
  retrieval.py                     # pgvector-Suche nach ähnlichen Angeboten
  offer_generator.py               # Generate-Pipeline (Block 4)
  render_via_skill.py              # Render-Pipeline (Block 6/6c)
  storage.py                       # Supabase Storage Upload
  auth.py                          # JWT-Verifikation
backend/app/models/              # SQLAlchemy-Models
backend/skills/era-presentation/ # Custom-Skill für PPT (geuploaded zu Anthropic)
backend/skills/era-word/         # Custom-Skill für Word
backend/seeds/                   # Bestandsangebote als YAML (PII-frei)
frontend/app/angebote/           # Liste, Detail, /neu Form
frontend/lib/api.ts              # Backend-API-Helper (hängt JWT an)
docker-compose.yml               # Coolify-Deployment
docs/PROJEKT.md                  # Diese Datei
```

---

## 7. Plattform-Guidelines: Was wurde wo dokumentiert?

Die Lessons aus diesem Projekt sind an drei Stellen verewigt:

### A. Im Template-Repo (`stratpool-app-template`) → für alle künftigen Apps
- **`docker-compose.yml`** enthält alle Coolify-Fixes. Mit ENV-Vars (`COOLIFY_APP_UUID`, `SUPABASE_NETWORK`) so generalisiert, dass jede neue App davon profitiert.
- **`frontend/Dockerfile`** mit gefixter NPM-Token-Injection.
- **`frontend/lib/supabase/{middleware,server}.ts`** mit den TS-Strict-Cookie-Annotations.
- **`docs/DEPLOY.md`** — Schritt-für-Schritt-First-Deploy-Anleitung mit Erklärung jeder Stolperstelle. **Das ist die wichtigste neue Doku.**
- **`CHANGELOG.md`** listet jeden Fix mit Begründung.
- **`pnpm-lock.yaml`** und **`uv.lock`** sind ab v0.2.0 ausgeliefert.
- **PR-Status:** https://github.com/thomasbrunner-spec/stratpool-app-template/pull/1 — noch zu reviewen + mergen.

### B. In `~/.claude/CLAUDE.md` (globale Claude-Anleitungen)
**Nicht angetastet in dieser Session.** Die globale Datei enthält Stack-Entscheidungen + Tonfall + Don'ts, die projektübergreifend gelten und sich nicht durch diese eine Erfahrung ändern. Wenn künftige Sessions zeigen, dass eine Coolify-spezifische Regel öfter gebraucht wird, kann ein Verweis dort ergänzt werden — aktuell aber nicht nötig, weil das Template das Wissen trägt.

### C. In dieser Projekt-`CLAUDE.md` → für Claude in DIESER App
- Die Roadmap-Sektion ist auf "alle Blöcke fertig" aktualisiert.
- Die Template-Bugs-Sektion ist umgeschrieben auf "im Upstream-PR gelöst".
- Die DB-Tunnel-Anleitung bleibt — die wirst du immer brauchen für Lokal-Dev.

### D. In Claude's Memory (für künftige Sessions in diesem Projekt)
- Pause-Stand mit dem heutigen Lerneffekt
- VPS-SSH-Setup
- User-Profil (du erwartest präzise Anleitungen)
- Stratpool-Schreibweise

Memory ist nicht im Repo — sie liegt in `~/.claude/projects/-Users-thomasbrunner-Desktop-Claude-Code-stratpool-angebote-app/memory/`.

---

## 8. Was offen ist (Stand 2026-05-10)

### Funktional
- **Browser-E2E zu Ende**: Generate-Pfad voll durchklicken (Login → /angebote/neu → Generate → Detail → PPT-Render → Word-Render). Liste-Verifikation ist durch.
- **Block 5c — Versions-History UI**: Bewusst pausiert. Nice-to-have.

### Cleanup (alles optional)
- `backend/assets/ERA_Template.pptx` und `backend/skills/era-presentation/assets/ERA_Template.pptx` sind Duplikate (12 MB). Können raus.
- `python-pptx` aus `pyproject.toml` Hauptdeps in Group `seed` verschieben.
- Test-Drafts in DB löschen: `DELETE FROM offers WHERE client_name = 'Mustermann Maschinenbau GmbH';`
- Hauptberater (du) aus `.env` in `consultants`-Tabelle ziehen mit `is_primary=true`.

### Plattform-Followups
- Template-PR #1 reviewen und mergen.
- Lokales Verzeichnis umbenennen: `mv ~/Desktop/Claude-Code/stratpoo-app-template ~/Desktop/Claude-Code/stratpool-app-template`.

---

## 9. Glossar (für nicht-Engineer-Leser)

| Begriff | Was es ist |
|---|---|
| **Container** | Eine isolierte Mini-Umgebung, in der ein Programm läuft. Man kann sich das wie eine virtuelle Mini-Festplatte vorstellen, die genau das enthält, was die App braucht. |
| **Docker Compose** | Eine Datei, die beschreibt: "Starte mir bitte folgende Container und verbinde sie so." |
| **Coolify** | Self-hosted Heroku-Klon. Schaut auf dein GitHub-Repo, baut bei jedem Push automatisch neue Container und schaltet sie live. |
| **Traefik** | Der Web-Router auf dem VPS. Entscheidet anhand des Domain-Namens, welcher Container die Anfrage bekommt. |
| **Healthcheck** | Coolify/Docker fragen alle paar Sekunden den Container "Lebst du noch?". Wenn nein → Neustart. |
| **Embedding** | Eine Zahlenreihe (Vektor), die einen Text "semantisch" beschreibt. Ähnliche Texte → ähnliche Vektoren. Damit kann man "ähnliche frühere Angebote" finden, ohne nach Wörtern zu suchen. |
| **pgvector** | Postgres-Erweiterung, die mit Embeddings rechnen kann. |
| **JWT** | "JSON Web Token" — der digitale Ausweis, den der Browser nach dem Login mit sich rumträgt. |
| **SSR** | "Server-Side Rendering" — das HTML wird auf dem Server gebaut (statt im Browser). Bei Next.js Standard. |
| **FQDN** | "Fully Qualified Domain Name" — der vollständige Domain-Name, z.B. `angebote.stratpool.pro`. |
| **Build-Arg** | Ein Wert, den man dem Container-Bau mitgibt (steht NICHT zur Laufzeit zur Verfügung). |
| **Runtime-Env** | Ein Wert, den der laufende Container sieht (NICHT beim Bauen verfügbar). |
| **Lockfile** | Datei, die exakt festlegt, welche Versionen aller Bibliotheken installiert werden — damit jeder Build identisch reproduzierbar ist. |

---

## 10. Wenn du diese Doku in 6 Monaten wieder liest

…und nichts mehr funktioniert, gehe in dieser Reihenfolge vor:

1. `https://angebote.stratpool.pro` öffnen — was siehst du?
2. Coolify-UI öffnen — Container-Status und Logs anschauen
3. `docs/DEPLOY.md` im Template lesen — die Stolperstellen-Checkliste durchgehen
4. Im VPS: `ssh stratpool-vps` und mit `docker logs <container>` reingucken
5. Wenn Healthcheck fehlt → siehe Bug 1 oben
6. Wenn 503 trotz healthy → siehe Bug 2 oben
7. Wenn API 500 mit DB-Fehler → siehe Bug 3 oben

Und wenn das alles nicht hilft: Claude eine neue Session öffnen, der Memory-Eintrag `project_angebote_app_pause.md` lädt automatisch und enthält den vollen Kontext.
