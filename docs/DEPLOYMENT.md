# Deployment auf Coolify

Schritt-für-Schritt-Anleitung, um eine Stratpool-App auf deinem Coolify-Server zu deployen.

## Voraussetzungen

- Coolify läuft auf `coolify.stratpool.pro`
- Supabase läuft auf `supabase.stratpool.pro`
- Repo der App ist auf GitHub und `thomasbrunner-spec` hat Zugriff
- DNS A-Record für `<app-name>.stratpool.pro` zeigt auf den VPS

## Schritt 1: GitHub Source in Coolify

Falls noch nicht passiert (einmalig pro GitHub-Account):

1. Coolify → **Sources** → **+ Add**
2. **GitHub App** auswählen
3. Wizard durchlaufen, Coolify-GitHub-App in deinem Repo installieren
4. Nur das App-Repo freigeben (nicht alle)

## Schritt 2: App in Coolify anlegen

1. **+ New Resource** → **Application**
2. **Source:** Dein GitHub-Account → Repo auswählen
3. **Build Pack:** **Docker Compose**
4. **Branch:** `main`
5. **Compose File:** `docker-compose.yml`
6. **Name:** `<app-name>`

## Schritt 3: Environment Variables

In Coolify → App → Tab **Environment Variables** alle Variablen aus
`.env.example` setzen:

| Variable | Quelle |
|---|---|
| `APP_NAME` | App-Name (z.B. `stratpool-angebote`) |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `ANTHROPIC_API_KEY` | Aus deinem Passwort-Manager |
| `VOYAGE_API_KEY` | Aus deinem Passwort-Manager |
| `SUPABASE_URL` | `https://supabase.stratpool.pro` |
| `SUPABASE_ANON_KEY` | Aus Supabase Studio → Project Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Aus Supabase Studio → Project Settings → API |
| `DATABASE_URL` | Supabase Postgres connection string |
| `JWT_SECRET` | Aus Supabase Studio → Project Settings → API → JWT Secret |
| `GITHUB_PACKAGES_TOKEN` | Dein Classic PAT mit `read:packages` |

## Schritt 4: Build Secret für npm-Token

Damit der Frontend-Container das `@thomasbrunner-spec/design-system`-Paket
beim Build installieren kann, brauchen wir den GitHub-Token als Build-Secret:

In Coolify → App → Tab **Build Secrets**:

- **Name:** `npm_token`
- **Value:** Dein `GITHUB_PACKAGES_TOKEN`

## Schritt 5: Domain konfigurieren

In Coolify → App → Tab **General**:

- **Domain:** `https://<app-name>.stratpool.pro`
- Coolify holt automatisch ein Let's-Encrypt-Zertifikat

## Schritt 6: Deploy

**Deploy** klicken. Beim ersten Deploy:

1. Coolify pullt das Repo
2. Baut Backend-Image (Python + uv + Dependencies)
3. Baut Frontend-Image (Node + pnpm + Dependencies)
4. Startet beide Container
5. Beantragt SSL-Zertifikat
6. Routet `<app-name>.stratpool.pro` auf den Frontend-Container

Geschätzte Zeit: 5-10 Min beim ersten Mal.

## Schritt 7: Verifikation

```bash
# Liveness-Check
curl https://<app-name>.stratpool.pro/

# Backend Health
curl https://<app-name>.stratpool.pro/api/v1/health/

# Volle Health (alle Integrationen)
curl https://<app-name>.stratpool.pro/api/v1/health/full
```

Im Browser:
- Landing Page erscheint mit Stratpool-Logo
- Login funktioniert
- Dashboard zeigt User-Info
- "Generate haiku" liefert ein Haiku → Pipeline funktioniert

## Auto-Deploy bei Push

Coolify watcht das Repo. Bei jedem Push auf `main`:
- Coolify pullt automatisch
- Baut neu
- Startet Container neu (Zero-Downtime, falls Health-Checks aktiv)

## Logs anschauen

In Coolify → App → Tab **Logs**:
- Frontend-Logs
- Backend-Logs
- Build-Logs (bei Problemen)

## Datenbank-Migrationen ausführen

Migrationen werden NICHT automatisch beim Deploy ausgeführt (Sicherheits-Default).
Nach einem Deploy mit neuen Migrationen:

**Variante A: Per Coolify-Terminal**

In Coolify → App → Tab **Terminal** (auf dem Backend-Container):

```bash
uv run alembic upgrade head
```

**Variante B: Per SSH auf den VPS**

```bash
ssh root@<vps-ip>
docker exec -it <app-name>-backend uv run alembic upgrade head
```

## Häufige Probleme

### "Failed to fetch package @thomasbrunner-spec/design-system"

→ `npm_token` Build-Secret fehlt oder ist falsch. Token im Passwort-Manager prüfen,
dann Secret in Coolify aktualisieren und neu deployen.

### "401 Unauthorized" beim API-Call

→ JWT_SECRET in Backend-Env stimmt nicht mit Supabase überein.
Studio → Settings → API → "JWT Secret" kopieren und in Coolify setzen.

### "Cannot connect to database"

→ `DATABASE_URL` falsch. Format:
`postgresql://postgres:PASSWORD@HOST:5432/postgres`
Bei Supabase auf demselben VPS: HOST ist `supabase-db` (interner Container-Name).

### Container restartet endlos

→ Logs anschauen. Häufig: Env-Variable fehlt oder ist falsch. Coolify zeigt
welche Variable beim Start nicht aufgelöst werden kann.
