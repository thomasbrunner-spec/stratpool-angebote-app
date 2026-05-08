# Setup-Guide: `stratpool-app-template`

> Anleitung zum Einrichten des Template-Repos.
> Voraussetzungen: Sub-Outputs A und B sind durch.

---

## Übersicht

Du erstellst ein **GitHub Template Repository**. "Template" heißt: Bei jeder neuen App
klickst du nur auf "Use this template" und bekommst eine Kopie. Das Template selbst ist
nie eine laufende App, sondern Boilerplate für künftige Apps.

Geschätzte Zeit: **10 Min** Setup.

---

## Schritt 1 – ZIP entpacken

```bash
cd ~/Desktop/Claude-Code

# ZIP entpacken (Pfad ggf. anpassen)
unzip ~/Downloads/stratpool-app-template.zip

cd stratpool-app-template

# Verifikation
ls -la
```

Erwartet: `backend/`, `frontend/`, `docker-compose.yml`, `.github/`, `README.md`, `CLAUDE.md`,
`docs/`, etc.

---

## Schritt 2 – Lokal sanity-checken (optional)

Dieser Schritt ist optional aber empfohlen, damit du sicher bist, dass alles passt
**bevor** du es als Template hochlädst.

### Backend-Check

```bash
cd backend
uv sync --no-install-project
uv run ruff check .
cd ..
```

Erwartet: keine Lint-Fehler.

### Frontend-Check

```bash
cd frontend
# Token in temporärer Variable setzen, NICHT in .npmrc dauerhaft schreiben
export GITHUB_PACKAGES_TOKEN="ghp_..."  # aus Passwort-Manager
echo "//npm.pkg.github.com/:_authToken=${GITHUB_PACKAGES_TOKEN}" >> .npmrc.local
NPM_CONFIG_USERCONFIG=$(pwd)/.npmrc.local pnpm install
pnpm typecheck
rm .npmrc.local
cd ..
```

Erwartet: TypeScript-Check ohne Fehler.

> **Hinweis:** Das `pnpm install` kann nur funktionieren, wenn das `@thomasbrunner-spec/design-system`-Paket
> auf GitHub Packages bereits publiziert ist. Du hast das in Sub-Output B gemacht — also sollte es klappen.

---

## Schritt 3 – GitHub-Repo anlegen und pushen

```bash
cd ~/Desktop/Claude-Code/stratpool-app-template

git init
git branch -M main
git add .
git commit -m "feat: initial app template v0.1.0"

gh repo create thomasbrunner-spec/stratpool-app-template \
  --private \
  --description "GitHub Template für neue Apps in der StratPool-Plattform" \
  --source=. \
  --push
```

---

## Schritt 4 – Als Template markieren

GitHub muss wissen, dass dieses Repo ein Template ist:

1. Öffne https://github.com/thomasbrunner-spec/stratpool-app-template/settings
2. Im Abschnitt **General** scrolle zu **"Template repository"**
3. ☑️ **"Template repository"** ankreuzen

Ab jetzt erscheint bei jedem Aufruf des Repos der grüne **"Use this template"**-Button.

---

## Schritt 5 – GitHub Actions Permissions setzen

Wie bei Sub-Output B:

1. Öffne https://github.com/thomasbrunner-spec/stratpool-app-template/settings/actions
2. Bei **"Workflow permissions"**:
   - ✅ **"Read and write permissions"**
   - ✅ **"Allow GitHub Actions to create and approve pull requests"**
3. **Save**

> **Wichtig:** Das Template selbst hat **keinen** `NPM_PUBLISH_TOKEN`-Bedarf, weil
> es nichts publishen soll. Aber jede App, die du daraus ableitest, braucht den
> Token für den Frontend-Build (siehe `docs/DEPLOYMENT.md`).

---

## Schritt 6 – Erster Test: App aus Template ableiten

Lass uns testen, dass das Template funktioniert:

1. Im Browser: https://github.com/thomasbrunner-spec/stratpool-app-template
2. Grüner Button **"Use this template"** → **"Create a new repository"**
3. Felder:
   - **Owner:** `thomasbrunner-spec`
   - **Repository name:** `stratpool-test-app` (zum Testen)
   - **Visibility:** Private
4. **Create repository**

GitHub erstellt eine Kopie. Falls alles funktioniert: Test-Repo gleich wieder löschen,
oder behalten und damit experimentieren.

---

## Schritt 7 – Optional: Smoke-Test des Templates

Falls du wirklich sehen willst, dass die generierte App auch lokal läuft:

```bash
cd ~/Desktop/Claude-Code
git clone git@github.com:thomasbrunner-spec/stratpool-test-app.git
cd stratpool-test-app

cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Werte aus Passwort-Manager eintragen

docker compose up --build
```

Wenn alles funktioniert:
- http://localhost:3000 zeigt die Landing Page
- http://localhost:8000/docs zeigt die FastAPI-Docs
- Login mit Supabase-Credentials funktioniert
- "Generate haiku" liefert tatsächlich ein Haiku

---

## Was du jetzt hast

| Asset | Status |
|---|---|
| Repo `thomasbrunner-spec/stratpool-app-template` | ✅ |
| Als GitHub Template markiert | ✅ |
| Bereit für "Use this template" | ✅ |

---

## Was als nächstes ansteht

Etappe 2: **Erste konkrete App — der Angebots-Generator.**

Dafür leiten wir vom Template das Repo `stratpool-angebote-app` ab und füllen es mit:
- Datenbank-Schema (offers, offer_versions, offer_embeddings)
- Frontend für neue Angebote, Vorschau, Versionsgeschichte
- Backend-Pipeline: Embed Transkript → Few-Shot-Retrieval → Claude → Word/PPT-Render
- Integration der ERA-Skills für die Dokumenten-Generierung
- Bestandsangebote als Lerngrundlage einbauen

---

## Troubleshooting

### `pnpm install` schlägt mit 401 fehl

→ Globale `~/.npmrc` hat den Token nicht. Siehe Sub-Output A Schritt 7.

### `pnpm install` schlägt mit "package not found" fehl

→ Das `@thomasbrunner-spec/design-system`-Paket ist noch nicht publiziert. Sub-Output B
fertigstellen.

### `docker compose up` schlägt mit "secret not found" fehl

→ `GITHUB_PACKAGES_TOKEN`-Env nicht gesetzt. In `.env` eintragen.

### Frontend-Build schlägt mit Tailwind-Fehler fehl

→ `@thomasbrunner-spec/design-system/tailwind` wird nicht gefunden. Check:
- ist `transpilePackages: ["@thomasbrunner-spec/design-system"]` in `next.config.ts`?
- ist das Paket aktuell installiert?
