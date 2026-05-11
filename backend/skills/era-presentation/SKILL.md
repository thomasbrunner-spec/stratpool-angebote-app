---
name: era-presentation
description: >
  Use this skill whenever the user wants to create, update, or modify a PowerPoint presentation
  in the ERA Group corporate design. Trigger this skill whenever the user mentions "ERA Präsentation",
  "ERA Folie", "ERA Group", "Präsentation erstellen", "Folien erstellen", or asks to create any
  presentation that should follow the ERA Group CI/CD. Also trigger when the user wants to add slides,
  edit content in the ERA style, or build a deck from scratch using the ERA template. Always use this
  skill — do NOT try to create ERA-style presentations without it.
---

# ERA Group Präsentation – Skill

Dieser Skill stellt sicher, dass alle Präsentationen exakt dem ERA Group Corporate Design entsprechen.
Die Vorlage liegt unter `assets/ERA_Template.pptx` und wird als Basis für CI, Theme und Layouts verwendet.
**Die Template-Folien werden NICHT übernommen** – es wird eine frische Präsentation mit nur den gewünschten Folien erstellt.

---

## Pflichtregeln – Corporate Identity

### Farben
| Farbe | Hex | Verwendung |
|-------|-----|-----------|
| ERA Dunkelblau | `#003A70` | Primärfarbe, Hintergründe, Überschriften |
| ERA Orange | `#FF9C00` | Akzentfarbe, Highlights, CTAs |
| Weiß | `#FFFFFF` | Text auf dunklem Hintergrund |
| Hellgrau | `#97999B` | Sekundärtext, dezente Elemente |
| Hellblau | `#CCD7E2` | Panels, Trennelemente |

**NIEMALS andere Farben verwenden.**

### Schriftart
- **Trebuchet MS** – für alle Texte
- Größen: Titel 28–36pt, Untertitel 18–24pt, Fließtext 14–16pt, Beschriftungen 10–12pt

### Logo & Footer
- Footer auf jeder Folie: `© ERA Group` Mitte unten, Seitenzahl rechts unten, ERA-Logo links unten
- Diese Elemente kommen automatisch aus dem Slide Master – nicht manuell hinzufügen

---

## Workflow: Präsentation erstellen

### Schritt 1: Abhängigkeiten

```bash
pip install python-pptx --break-system-packages -q
```

### Schritt 2: Python-Skript (Pflichtvorlage)

```python
from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from datetime import date

# ── 1. KONFIGURATION ──────────────────────────────────────────────────────────
KUNDE         = "Kundenname GmbH"
BERATER_NAME  = "Max Mustermann"
BERATER_TITEL = "Senior Consultant DACH"
BERATER_TEL   = "+49 151 1234 5678"
BERATER_EMAIL = "mmustermann@eragroup.com"

_MONATE = {1:'Januar',2:'Februar',3:'März',4:'April',5:'Mai',6:'Juni',
           7:'Juli',8:'August',9:'September',10:'Oktober',11:'November',12:'Dezember'}
_heute = date.today()
DATUM = f"{_heute.day}. {_MONATE[_heute.month]} {_heute.year}"

# ── 2. TEMPLATE LADEN & ALLE FOLIEN ENTFERNEN ────────────────────────────────
prs = Presentation("assets/ERA_Template.pptx")
for i in range(len(prs.slides) - 1, -1, -1):
    rId = prs.slides._sldIdLst[i].get(qn("r:id"))
    prs.part.drop_rel(rId)
    del prs.slides._sldIdLst[i]

# ── 3. HILFSFUNKTIONEN ────────────────────────────────────────────────────────
def get_layout(name):
    return next(l for l in prs.slide_layouts if l.name == name)

def replace_layout_text(layout, shape_name, new_text, shape_id=None):
    """Ersetzt Text im ersten Run eines Layout-Shapes."""
    for shape in layout.shapes:
        if shape_id and shape.shape_id != shape_id:
            continue
        if shape.name == shape_name and shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    run.text = new_text
                    return True
    return False

def add_white_textbox(slide, left_in, top_in, width_in, height_in, text, font_size=24, bold=True):
    """Fügt eine weiße Textbox direkt auf der Folie hinzu."""
    txBox = slide.shapes.add_textbox(
        Inches(left_in), Inches(top_in), Inches(width_in), Inches(height_in)
    )
    tf = txBox.text_frame
    tf.word_wrap = False
    run = tf.paragraphs[0].add_run()
    run.text = text
    run.font.name = "Trebuchet MS"
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    return txBox

# ── 4. TITELFOLIE ─────────────────────────────────────────────────────────────
cover_layout = get_layout("Cover")

# Berater-Daten in Layout-Shapes eintragen (shape_id wichtig, da manche Namen doppelt vorkommen!)
replace_layout_text(cover_layout, "text1111", BERATER_NAME)            # Berater-Name
replace_layout_text(cover_layout, "text",     BERATER_TITEL, shape_id=19)  # Berater-Titel
replace_layout_text(cover_layout, "text51",   BERATER_TEL)             # Telefon
replace_layout_text(cover_layout, "text411",  BERATER_EMAIL)           # E-Mail
replace_layout_text(cover_layout, "date",     DATUM)                   # Datum

cover_slide = prs.slides.add_slide(cover_layout)

# Kundenname unter "Für:" – als direkte Textbox (Templafy-Feld ist hidden, daher Textbox).
# WICHTIG zur Ausrichtung mit "Für:":
#   1. Box-Position: left_in=0.787 — exakt die Box-Position des Layout-Labels "Für:"
#      (text111, shape_id=25 im Cover-Layout).
#   2. Margins NICHT manipulieren. Lass den text_frame mit Default-Werten — beide
#      Boxen erben dann margin_left=0.1in, und der Text-Anfang sitzt visuell exakt
#      unter dem "F" von "Für:" bei x≈0.887in.
#
# Häufige Falle: tf.margin_left=0 setzen schiebt das "T" des Kundennamens nach LINKS
# vor das "F" von "Für:" — das sieht aus wie ein Lay­out-Bug. NICHT machen.
add_white_textbox(cover_slide, left_in=0.787, top_in=4.95, width_in=4.5, height_in=0.55,
                  text=KUNDE, font_size=24, bold=True)
# Sanity-Check: NICHT die folgenden Zeilen einfügen, sie zerstören die Ausrichtung:
#   txBox.text_frame.margin_left = 0     ← FALSCH, Text rutscht zu weit links
#   txBox.text_frame.margin_top = 0      ← FALSCH, vertikaler Versatz

# ── 5. WEITERE FOLIEN ─────────────────────────────────────────────────────────
# Beispiel Agenda:
# agenda_slide = prs.slides.add_slide(get_layout("Agenda"))

# Beispiel Inhaltsfolie:
# content_slide = prs.slides.add_slide(get_layout("1 x Content"))
# for ph in content_slide.placeholders:
#     if ph.placeholder_format.idx == 0: ph.text = "Titel"
#     elif ph.placeholder_format.idx == 1: ph.text = "Inhalt..."
# WICHTIG: Body-Text in 1/2/3/4 x Content Layouts ist STANDARD/REGULAR — niemals fett.
# Fett-Setzungen nur für Hervorhebungen einzelner Wörter, nie für ganze Absätze.

# ── 6. SPEICHERN ──────────────────────────────────────────────────────────────
OUTPUT = "/home/claude/era_presentation.pptx"
prs.save(OUTPUT)
print(f"Gespeichert: {OUTPUT}")
```

---

## Verfügbare Layouts

| Layout-Name | Verwendung |
|-------------|-----------|
| `Cover` | Titelfolie (immer erste Folie) |
| `Abschnitts-\nüberschrift` | Abschnittstrenner |
| `Agenda` | Agenda mit nummerierten Punkten |
| `1 x Content` | Titel + 1 Textblock |
| `2 x Content` | Titel + 2 Spalten |
| `3 x Content` | Titel + 3 Spalten |
| `4 x Content` | Titel + 4 Spalten |
| `Content + Picture` | Text links, Bild rechts |
| `2 x Content + Picture` | 2 Textspalten + Bild |
| `1/2 Page Light Blue Horizontal Panel` | Hellblauer Querbalken |
| `1/2 Page Dark Blue Horizontal Panel` | Dunkelblauer Querbalken |
| `1 x Content Light Blue` | Hellblauer Hintergrund |
| `2 x Content Light Blue` | 2 Spalten, hellblau |
| `Bio x 1` | Kontaktfolie (1 Person) |
| `Bio x 3` | Teamfolie (3 Personen) |
| `Nur Titel` | Titel oben, freies Layout |
| `Leer` | Komplett freies Layout |

---

## Standard-Architektur eines ERA-Angebots-Decks (Pflichtreihenfolge)

ERA-Angebote sind **Verkaufspitches, keine Modul-Listings**. Sie folgen einer klaren Erzähl-Architektur. Wenn ein Angebot mit Discovery-Transkript + freigegebenem Inhalts-JSON gerendert wird, **diese Reihenfolge einhalten**:

| # | Slide-Typ | Kern-Layout | Inhalt | Quelle aus OfferContent |
|---|-----------|-------------|--------|-------------------------|
| 1 | **Cover** | `Cover` (Template-Layout) | Kunde, Berater(s), Datum | client_name, settings.berater_*, co_consultant |
| 2 | **Management Summary** | `Leer` + dark_bg + Hero-Prosa | Hero-Absatz in weiß auf blau, kein Bullet-Point | management_summary |
| 3 | **Hook-Quote** | `Leer` + dark_bg + vertikaler Balken | Großer zitierter Insight, Trebuchet 32pt italic weiß auf blau, schmaler orange Balken links | hook_quote |
| 4 | **Warum jetzt** | `Leer` + dark_bg + 2–5 Hellblau-Karten | Markt/Urgency, jeweils in eigener Karte | warum_jetzt_argumente |
| 5 | **Ausgangssituation** | `Leer` + dark_bg + zwei Hellblau-Karten | linke Karte „Was wir mitgenommen haben" + rechte Karte „Erste Hypothesen" | ausgangssituation + erkannte_anwendungsfaelle |
| 6 | **Zielsetzung** | `Leer` + dark_bg + Etappen-Karten | Identifizieren / Bewerten / Dokumentieren / Umsetzen als nummerierte Karten | zielsetzung_und_ergebnis |
| 7 | **Vorgehen-Übersicht** | `Leer` + dark_bg + horizontale Linie + Ovale + USP-Footer-Box | Alle Phasen mit nummerierten Ovalen auf Linie, USP-Highlight unten | phasen (Übersicht) |
| 8…N | **Phase-Detail-Slides** | `Leer` + dark_bg + Karten-Grid | EINE Slide pro Phase. 3–5 nummerierte Hellblau-Karten in einer Reihe (eine pro Aktivität/Setup-Aspekt) | phasen[i] (eine Slide pro Phase) |
| N+1 | **Technische Basis** | `Leer` + dark_bg + 2–4 Hellblau-Karten | Tech-Optionen pro Karte | technische_basis |
| N+2 | **Mehrwert auf 3 Ebenen** | `Leer` + dark_bg + 3 Hellblau-Karten | Strategisch / Organisatorisch / Menschlich, jeweils in eigener Karte mit Bullet-Liste | mehrwert_3_ebenen |
| N+3 | **Was im Angebot enthalten ist** | `Leer` + dark_bg + nummerierte Karten-Liste | Liste der Liefer-Items mit Mini-Beschreibungen, jede Zeile als kleine Karte | leistungsumfang_items |
| N+4 | **Investition** | `Leer` + dark_bg + große Preis-Karte links + Prosa rechts | Große Hellblau-Karte mit Preis-Hero links, Wert-Argument als weißer Text rechts | investition |
| N+5 | **Nächste Schritte / CTA** | `Leer` + dark_bg + 2–3 Karten oder Prosa | Konkrete Folgeschritte | naechste_schritte |
| Letzte | **Ihr Ansprechpartner** | `Bio x 1` oder `Bio x 3` | Hauptberater (+ ggf. Co-Berater) | settings.berater_* + co_consultant |

**Daraus ergibt sich ein Deck mit 12–16 Folien je nach Anzahl Phasen** — passt zur Saarpor-Referenz (17 Folien, 16 davon „Leer"-Layout).

## Layout-Wahl: Leer ist Default, mit Saarpor-Pattern

Standard-`1 x Content` / `2 x Content` / `3 x Content` Layouts sind **nicht** der Default. **Default ist `Leer` mit dem Saarpor-Pattern**:
```
add_era_dark_bg → add_era_header → Karten-Inhalt → add_era_footer
```

| Inhalt | Default-Layout | Wann doch ein Standard-Layout? |
|--------|----------------|--------------------------------|
| Cover | `Cover` | Immer |
| Hook-Statement, Quote, Hero-Slide | `Leer` + dark_bg + vertikaler orange Balken | Nie |
| Phasen-Übersicht | `Leer` + dark_bg + horizontale Linie mit Ovalen | Nie |
| Phase-Detail | `Leer` + dark_bg + Hellblau-Karten-Grid | Nie |
| Mehrwert-3-Ebenen | `Leer` + dark_bg + 3 Hellblau-Karten | Nie |
| Investition | `Leer` + dark_bg + große Preis-Hero-Karte | Nie |
| Ansprechpartner-Slide | `Bio x 1` / `Bio x 3` | Immer |

**Faustregel:** In einem ERA-Angebot nutzen alle Content-Folien das `Leer`-Layout mit `add_era_dark_bg` als Hintergrund. Standard-Content-Layouts werden NICHT mehr verwendet.

## Eigene Layouts – Fallback wenn kein Template-Layout passt

Wenn keines der 43 Template-Layouts den gewünschten Inhalt gut abbildet, darf Claude ein eigenes Layout auf Basis des `Leer`-Layouts bauen. Das CI muss dabei immer gewahrt bleiben.

### Entscheidungsbaum
1. **Gibt es ein passendes Template-Layout?** → Bevorzugen, aber bewusst variieren (s.o.)
2. **Passt kein Layout gut?** → Eigenes Layout auf `Leer`-Basis mit ERA-CI aufbauen
3. **Niemals** ohne ERA-Farben und -Schrift arbeiten

### Bausteine für eigene Layouts (Saarpor-Pattern – Pflicht)

**Das visuelle Grundprinzip aller Content-Slides:** Vollflächiger dunkelblauer Hintergrund mit weißer Header-Zeile oben und hellblauen Karten als Inhalts-Container. Keine weiße Slide-Fläche, keine schmale „Titelbar". Saarpor nutzt dieses Pattern auf 16 von 17 Folien.

```python
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

# ERA-Farben (zentrale Quelle, niemals abweichen)
ERA_DARK_BLUE  = RGBColor(0x00, 0x3A, 0x70)
ERA_ORANGE     = RGBColor(0xFF, 0x9C, 0x00)
ERA_LIGHT_BLUE = RGBColor(0xCC, 0xD7, 0xE2)  # Karten-Hintergrund
ERA_GREY       = RGBColor(0x97, 0x99, 0x9B)
ERA_WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
```

**`add_era_dark_bg(slide)` — Full-bleed dunkelblauer Hintergrund (Pflicht auf jeder Content-Slide außer Cover/Bio):**
```python
def add_era_dark_bg(slide):
    """Voller dunkelblauer Hintergrund über die ganze Slide."""
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0,
                                 prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = ERA_DARK_BLUE
    bg.line.fill.background()
    # Hintergrund nach hinten schieben, damit andere Shapes ihn nicht verdecken
    spTree = bg._element.getparent()
    spTree.remove(bg._element)
    spTree.insert(2, bg._element)
    return bg
```

**`add_era_header(slide, title, subtitle=None)` — Standard-Kopfzeile (Titel weiß + optional Eyebrow-Subtitle):**
```python
def add_era_header(slide, title, subtitle=None):
    """Saarpor-Standard-Header: Titel oben bei (0.60, 0.50), Subtitle bei (0.60, 1.25)."""
    title_box = slide.shapes.add_textbox(Inches(0.60), Inches(0.50),
                                          Inches(12.50), Inches(0.70))
    tf = title_box.text_frame
    tf.word_wrap = True
    run = tf.paragraphs[0].add_run()
    run.text = title
    run.font.name = "Trebuchet MS"
    run.font.size = Pt(26)
    run.font.bold = True
    run.font.color.rgb = ERA_WHITE
    if subtitle:
        sub_box = slide.shapes.add_textbox(Inches(0.60), Inches(1.25),
                                            Inches(12.50), Inches(0.40))
        sub_tf = sub_box.text_frame
        sub_tf.word_wrap = True
        sub_run = sub_tf.paragraphs[0].add_run()
        sub_run.text = subtitle
        sub_run.font.name = "Trebuchet MS"
        sub_run.font.size = Pt(14)
        sub_run.font.italic = True
        sub_run.font.color.rgb = ERA_WHITE
```

**`add_era_footer(slide, insight_text)` — Saarpor-Footer: dünne orange Linie + Insight-Zeile:**
```python
def add_era_footer(slide, insight_text):
    """Footer am unteren Slide-Rand: orange Linie + weißer Insight-Text."""
    # Orange Trennlinie bei y=6.95
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                   Inches(0.60), Inches(6.95),
                                   Inches(12.10), Inches(0.04))
    line.fill.solid()
    line.fill.fore_color.rgb = ERA_ORANGE
    line.line.fill.background()
    # Insight-Text bei y=7.05
    txt = slide.shapes.add_textbox(Inches(0.60), Inches(7.05),
                                    Inches(12.50), Inches(0.40))
    run = txt.text_frame.paragraphs[0].add_run()
    run.text = insight_text
    run.font.name = "Trebuchet MS"
    run.font.size = Pt(12)
    run.font.italic = True
    run.font.color.rgb = ERA_WHITE
```

**`add_era_card(slide, x, y, w, h, accent_w=0.85)` — Hellblaue Karte mit oranger Akzent-Linie oben:**
```python
def add_era_card(slide, x, y, w, h, accent_w=0.85):
    """Saarpor-Karten-Pattern:
    1. Orange Akzent-Rechteck (0.06" hoch) auf der Oberkante
    2. Hellblaues Karten-Rechteck direkt darunter
    accent_w in Zoll — Saarpor verwendet 0.85" für Phase-Detail-Karten."""
    # Orange Akzent oben
    acc = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                  Inches(x), Inches(y),
                                  Inches(accent_w), Inches(0.06))
    acc.fill.solid()
    acc.fill.fore_color.rgb = ERA_ORANGE
    acc.line.fill.background()
    # Hellblaue Karte
    card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                   Inches(x), Inches(y + 0.06),
                                   Inches(w), Inches(h - 0.06))
    card.fill.solid()
    card.fill.fore_color.rgb = ERA_LIGHT_BLUE
    card.line.fill.background()
    return card
```

**`add_era_numbered_oval(slide, x, y, number, size=0.55)` — Oranges Oval mit weißer Zahl:**
```python
def add_era_numbered_oval(slide, x, y, number, size=0.55):
    """Saarpor-Nummerierung: oranges Oval mit weißer fetter Zahl drin."""
    oval = slide.shapes.add_shape(MSO_SHAPE.OVAL,
                                   Inches(x), Inches(y),
                                   Inches(size), Inches(size))
    oval.fill.solid()
    oval.fill.fore_color.rgb = ERA_ORANGE
    oval.line.fill.background()
    # Zahl drauf
    tf = oval.text_frame
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = 2  # center
    run = p.add_run()
    run.text = str(number)
    run.font.name = "Trebuchet MS"
    run.font.size = Pt(20)
    run.font.bold = True
    run.font.color.rgb = ERA_WHITE
    return oval
```

**`add_era_textbox(slide, left, top, width, height, text, ...)` — Universeller Text-Helper:**
```python
def add_era_textbox(slide, left_in, top_in, width_in, height_in,
                    text, font_size=14, bold=False, italic=False,
                    color=None, on_dark_bg=True):
    """Textbox in ERA-Farbe.
    Default: weiß auf dunklem Hintergrund (für Content-Slides).
    Bei on_dark_bg=False: Dunkelblau auf hellem Karten-Hintergrund."""
    txBox = slide.shapes.add_textbox(
        Inches(left_in), Inches(top_in), Inches(width_in), Inches(height_in))
    tf = txBox.text_frame
    tf.word_wrap = True
    run = tf.paragraphs[0].add_run()
    run.text = text
    run.font.name = "Trebuchet MS"
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color
    else:
        run.font.color.rgb = ERA_WHITE if on_dark_bg else ERA_DARK_BLUE
    return txBox
```

**`add_era_accent(slide, left, top, width, height=0.04)` — Orange Trennlinie / Akzentbalken:**
```python
def add_era_accent(slide, left_in, top_in, width_in, height_in=0.04):
    """Orange Linie als Akzent/Trennelement."""
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
        Inches(left_in), Inches(top_in), Inches(width_in), Inches(height_in))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ERA_ORANGE
    bar.line.fill.background()
    return bar
```

**`add_era_logo(slide)` — ERA-Logo rechts oben (Pflicht auf jeder Content-Slide außer Cover):**
```python
def add_era_logo(slide):
    """Saarpor-Position für das ERA-Logo: (11.85", 0.10"), Größe 1.17" x 0.83".

    Das Logo liegt als PNG unter assets/era_logo.png. Wird auf jeder
    Content-Slide platziert — nicht auf der Cover-Slide (dort kommt es
    aus dem Layout-Master) und nicht auf Bio-Slides (kommt ebenfalls aus
    dem Master).
    """
    slide.shapes.add_picture(
        "assets/era_logo.png",
        Inches(11.85), Inches(0.10),
        width=Inches(1.17), height=Inches(0.83),
    )
```

**⚠️ Veraltet (NICHT MEHR VERWENDEN):**
`add_era_title_bar(slide, title)` — erzeugt eine schmale blaue Titelbar oben auf sonst weißem Hintergrund. Das ist NICHT Saarpor-konform. **Stattdessen IMMER:** `add_era_dark_bg(slide)` + `add_era_header(slide, title, subtitle)` + optional `add_era_footer(slide, insight)`.

### Wann eigene Layouts sinnvoll sind

| Situation | Eigenes Layout? | Ansatz |
|-----------|----------------|--------|
| Große Kennzahlen hervorheben (3–4 Zahlen) | ✅ | Leer-Basis, große Zahl in ERA-Blau + orangenes Label |
| Vorher/Nachher-Vergleich | ✅ | 2 Spalten, hellblauer Trennstrich |
| Horizontaler Zeitstrahl (5+ Schritte) | ✅ | Kreise in Orange mit Nummern, Verbindungslinie |
| Zitat mit Kundenlogo | ✅ | Kursivtext ERA-Blau, orangener Zitatstrich links |
| 2 Textspalten nebeneinander | ❌ | → `2 x Content` verwenden |
| Folie mit Bild rechts | ❌ | → `Content + Picture` verwenden |

### Verbote – auch bei eigenen Layouts

- ❌ Andere Farben als die ERA-Palette (`ERA_DARK_BLUE`, `ERA_ORANGE`, `ERA_LIGHT_BLUE`, `ERA_GREY`, `ERA_WHITE`)
- ❌ Andere Schrift als Trebuchet MS
- ❌ `add_era_title_bar()` oder eigene schmale Titelbar — IMMER `add_era_dark_bg` + `add_era_header`
- ❌ Content direkt auf dem dunkelblauen Hintergrund ohne Karten-Container (Ausnahmen: Header-Texte, Footer-Insight, Hook-Quote-Slide, Phasen-Übersicht-Spalten)
- ❌ Logo manuell hinzufügen (kommt automatisch vom Master)

---

## Titelfolie – Shape-Mapping (Referenz)

Getestete Shape-Namen und IDs im Cover-Layout:

| Shape-Name | shape_id | Inhalt |
|------------|----------|--------|
| `text1111` | 26 | Berater-Name (Position links unten, 12pt regular weiß) |
| `text` | 19 | Berater-Titel (12pt regular weiß) |
| `text51` | 12 | Telefon (12pt regular weiß) |
| `text411` | 18 | E-Mail (12pt regular weiß) |
| `date` | 3 | Datum (deutsch) |
| `TextBox 38` | 39 | „ERA Group" – **nicht ändern** |
| `text111` | 25 | „Für:" Label – **nicht ändern** (steht bei `left=0.85"`) |
| `text131` | 22 | Kundenname (versteckt → als Textbox auf Folie bei Position 0.85"/4.95") |

---

## Zwei Berater auf der Titelfolie

Wenn zwei Berater dargestellt werden sollen (z. B. ein Hauptberater und ein Co-Berater pro Mandat):

- **Linker Block (Layout):** Co-Berater. Die vier Layout-Shapes (`text1111`, `text` mit shape_id=19, `text51`, `text411`) werden mit den Daten des Co-Beraters überschrieben — siehe Workflow oben.
- **Rechter Block (Overlay):** Hauptberater. Vier eigene Textboxen werden auf das Cover gelegt, mit identischer Y-Höhe wie der Layout-Block, damit beide Berater visuell auf einer Linie sitzen.

Beide Blöcke nutzen **dieselbe Schrift** (Trebuchet MS, 12pt, regular, weiß) — also nicht fett, gleiche Größe wie der Layout-Block. Das ist kritisch für ein konsistentes Bild.

```python
# Rechter Block: Hauptberater als Overlay-Textboxen
# Y-Positionen 1:1 vom Layout-Block übernommen, damit beide Berater visuell
# auf einer Linie sitzen. WICHTIG: KEINE Margin-Manipulationen — Default
# margin_left=0.1in ist genau das, was der Layout-Block links auch hat.
RIGHT_X = 6.79
LINES = [
    (HAUPT_NAME,            6.02),  # gleiche Y wie Co-Berater "name"
    (HAUPT_TITEL,           6.25),  # gleiche Y wie Co-Berater "titel"
    (f"M: {HAUPT_TEL}",     6.47),  # gleiche Y wie Co-Berater "tel"
    (f"E: {HAUPT_EMAIL}",   6.70),  # gleiche Y wie Co-Berater "email"
]
for text, top in LINES:
    box = cover_slide.shapes.add_textbox(Inches(RIGHT_X), Inches(top), Inches(3.43), Inches(0.20))
    run = box.text_frame.paragraphs[0].add_run()
    run.text = text
    run.font.name = "Trebuchet MS"
    run.font.size = Pt(12)
    run.font.bold = False
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
```

**Generelle Regel** für jede Textbox auf dem Cover: keine `margin_left`/`margin_top`/`margin_right`/`margin_bottom` Werte setzen. Default-Margins sind genau das, was die Layout-Master verwenden, und sorgen für konsistente Ausrichtung.

Wenn nur **ein** Berater vorhanden ist, bleibt der Layout-Block unverändert (Default Thomas Löwer im Template) — hier ist die Berater-Datenquelle nicht ideal, dann besser den Layout-Block überschreiben **und** keinen Overlay setzen.

---

## Anti-Patterns – nicht akzeptabel

Diese Muster machen das Deck billig oder generisch — strikt vermeiden:

- **❌ KRITISCH: Schmale Titelbar + weißer Hintergrund.** Niemals `add_era_title_bar()` verwenden oder eine eigene 1.1"-blaue Titelbar auf weißem Slide bauen. Saarpor-Referenz nutzt **full-bleed Dunkelblau** auf 16/17 Slides. Pflichtschema für jede Content-Slide: `add_era_dark_bg(slide)` → `add_era_header(slide, title, subtitle)` → Inhalt mit `add_era_card(...)` → `add_era_footer(slide, insight)`.
- **❌ KRITISCH: Inhalts-Texte direkt auf dem dunkelblauen Hintergrund ohne Karten-Container.** Inhalte gehören in hellblaue Karten (`add_era_card`), nicht als nackter weißer Text auf Blau. Ausnahmen: Header, Footer-Insight, Hook-Quote-Slide (die ist explizit ohne Karte).
- **❌ KRITISCH: Andere Farben als die ERA-Palette** (`ERA_DARK_BLUE`, `ERA_ORANGE`, `ERA_LIGHT_BLUE`, `ERA_GREY`, `ERA_WHITE`). Niemals z.B. ein Grau improvisieren — immer `ERA_GREY` verwenden.
- **Bullet-Hellscape**: 6+ Bullet-Points hintereinander auf einer Folie. Wenn so viel Inhalt anfällt → in Karten / Spalten / mehrere Folien aufteilen.
- **Zwei-Punkt-Listen**: Bullet-Lists mit nur 2 Einträgen — wirken stiefmütterlich. Lösung: als Prosa schreiben oder einen dritten substanziellen Punkt einfügen, sonst weglassen.
- **„Modul A / Modul B / Modul C"**: anonyme Bezeichner. Phasen haben sprechende Namen („Vorbereitung", „Strategischer Workshop", „Vertiefung & Prototyp", „Umsetzung").
- **„Teil 1 / Teil 2"-Aufteilung** für eine Aufzählung, weil sie auf einer Folie nicht passt: die Aufzählung gehört auf eine Folie als Karten-Grid, oder als getrennte semantische Folien (z. B. eine Folie pro Phase).
- **Generische Bestandteile-Boxen** ohne klare Inhalts-Differenzierung: jede Bestandteil-/Phase-Folie hat einen eigenen erkennbaren Charakter (Setup-Tabelle, Ergebnis-Card, Aktivitäten-Liste).
- **Body-Text fett**: Body in Karten ist immer `regular`. Fett nur für Hervorhebungen einzelner Wörter oder Karten-Titel, nie für ganze Absätze.
- **Cover ohne Co-Berater wenn vorhanden**: wenn `co_consultant` gesetzt ist → Zwei-Berater-Layout (siehe oben). Sonst nur Hauptberater.
- **Wiederholte Adjektive**: „klar / klar / klar" in einer Folie wirkt billig. Variieren oder weglassen.
- **Letzte Slide leer / nur „Vielen Dank"**: die letzte Slide ist `Bio x 1` / `Bio x 3` (Ansprechpartner) oder ein konkreter CTA — nie ein Filler.

## Recipes für „Leer"-Slide-Kompositionen (Saarpor-Pattern)

Jede Content-Slide folgt diesem Skelett (Reihenfolge zwingend einhalten):
```python
slide = prs.slides.add_slide(get_layout("Leer"))
add_era_dark_bg(slide)                                    # 1. full-bleed Dunkelblau
add_era_logo(slide)                                       # 2. ERA-Logo rechts oben (Pflicht)
add_era_header(slide, "Slide-Titel", "Eyebrow-Subtitle")  # 3. weiße Kopfzeile
# … Slide-spezifische Komposition aus Karten, Ovalen, Texten …
add_era_footer(slide, "Insight-Satz unten")               # 4. orange Linie + weißer Footer-Text
```

**Logo-Regel:** Das ERA-Logo wird auf JEDER Content-Slide rechts oben platziert. Einzige Ausnahmen:
- Cover-Slide (Logo kommt aus dem Layout-Master)
- Bio-Slides `Bio x 1` / `Bio x 3` (Logo kommt ebenfalls aus dem Master)

Sobald `add_era_dark_bg(slide)` aufgerufen wurde, MUSS auch `add_era_logo(slide)` aufgerufen werden — die zwei sind ein untrennbares Paar.

**Text-Overflow-Regel:** Variabler Text aus dem OfferContent (Beschreibungen, Bullets, Prosa-Blöcke) kann unerwartet lang sein. Für JEDE Box mit variablem Text eine der zwei Strategien anwenden:
1. **Hard-cut vorher:** `text = text if len(text) <= MAX else text[:MAX-3].rstrip() + "…"`. Saubere Limits siehe pro Recipe.
2. **Auto-shrink:** nach dem `add_era_textbox` setzen: `box.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE` (Import: `from pptx.enum.text import MSO_AUTO_SIZE`).

Niemals einfach hoffen, dass Text passt — er passt im Zweifel nicht und läuft sichtbar aus der Karte raus. Das ist das hässlichste Resultat.

Alle Pixel-Positionen unten sind aus der echten Saarpor-PPTX extrahiert. Bei Iterationen die Positionen beibehalten, nur Texte und Anzahl der Elemente anpassen.

### Hook-Quote-Slide (Statement, Slide 3 in Saarpor)

```python
# Full-bleed Dunkelblau + schmaler vertikaler orange Balken links + großer Quote-Text rechts.
slide = prs.slides.add_slide(get_layout("Leer"))
add_era_dark_bg(slide)
add_era_logo(slide)
# Vertikaler orange Balken bei x=0.85, y=1.50 (Höhe 4.50")
acc = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                              Inches(0.85), Inches(1.50),
                              Inches(0.06), Inches(4.50))
acc.fill.solid()
acc.fill.fore_color.rgb = ERA_ORANGE
acc.line.fill.background()
# Quote-Text in weiß bei (1.15, 2.00), Breite 11.50", Höhe 4.00"
add_era_textbox(slide, 1.15, 2.00, 11.50, 4.00, HOOK_QUOTE,
                font_size=32, italic=True, on_dark_bg=True)
# Kein Footer auf der Hook-Slide — sie steht für sich.
```

### Phasen-Übersicht (Saarpor Slide 8: horizontale Linie + nummerierte Ovale + USP-Box)

```python
# 4 Phasen-Beispiel (auch 3 oder 5 möglich, Spaltenbreite entsprechend skalieren).
slide = prs.slides.add_slide(get_layout("Leer"))
add_era_dark_bg(slide)
add_era_logo(slide)
add_era_header(slide,
               f"Projektablauf in {len(PHASEN)} Phasen",
               "Vom Kontext zur Umsetzung – strukturiert, beteiligend, ergebnisorientiert.")

# Horizontale graue Linie bei y=2.55, durch die Mitte der Ovale
line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                               Inches(0.70), Inches(2.55),
                               Inches(11.90), Inches(0.03))
line.fill.solid()
line.fill.fore_color.rgb = ERA_GREY
line.line.fill.background()

# Pro Phase: Oval auf der Linie + Titel + Beschreibung. 4 Spalten:
# Saarpor verwendet bei 4 Phasen die Oval-Positionen x = 1.40, 4.55, 7.70, 10.85
col_x = {
    3: [1.90, 5.30, 8.70],
    4: [1.40, 4.55, 7.70, 10.85],
    5: [1.00, 3.55, 6.10, 8.65, 11.20],
}.get(len(PHASEN), None)
if col_x is None:
    # Fallback gleichmäßig
    step = 12.20 / (len(PHASEN) + 1)
    col_x = [0.60 + step * (i + 1) for i in range(len(PHASEN))]
title_x_offset = -1.40 + 0.55/2  # Phase-Titel etwas links vom Oval ausgerichtet
title_w = 2.80

for i, p in enumerate(PHASEN):
    ox = col_x[i]
    # Oval mit Zahl (auf der Linie zentriert, also y=2.30 für size=0.55)
    add_era_numbered_oval(slide, ox, 2.30, p.nummer, size=0.55)
    # Titel der Phase darunter
    tx = ox + title_x_offset
    if tx < 0:
        tx = 0.0
    add_era_textbox(slide, tx, 3.05, title_w, 0.55, p.titel,
                    font_size=16, bold=True, on_dark_bg=True)
    # Kurz-Beschreibung
    add_era_textbox(slide, tx, 4.00, title_w, 1.60,
                    short_summary(p.beschreibung, max_chars=180),
                    font_size=11, on_dark_bg=True)

# USP-Highlight-Box am Footer (orange, Höhe 1.20")
usp_bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                 Inches(0.60), Inches(5.60),
                                 Inches(12.20), Inches(1.20))
usp_bg.fill.solid()
usp_bg.fill.fore_color.rgb = ERA_ORANGE
usp_bg.line.fill.background()
add_era_textbox(slide, 0.95, 5.75, 12.00, 0.40,
                "Unser Alleinstellungsmerkmal",
                font_size=14, bold=True, color=ERA_WHITE)
add_era_textbox(slide, 0.95, 6.01, 12.00, 0.60,
                USP_TEXT,                # Kurze Prosa, max ~180 Zeichen
                font_size=12, color=ERA_WHITE)
# Schließende orange Linie unter der USP-Box (Saarpor-Detail)
add_era_accent(slide, 0.60, 7.14, 12.10, 0.04)
# Kein zusätzlicher Footer — die USP-Box ersetzt ihn.
```

### Phase-Detail-Slide (Saarpor Slide 9: nummerierte Karten-Reihe)

```python
# EINE Slide pro Phase. Jede Phase hat 3–5 Aktivitäten/Karten.
# Saarpor verwendet 4 Karten in einer Reihe mit Kartenbreite 2.95" und Abstand 0.30".
slide = prs.slides.add_slide(get_layout("Leer"))
add_era_dark_bg(slide)
add_era_logo(slide)
add_era_header(slide,
               f"Phase {p.nummer} – {p.titel}",
               p.untertitel or "")

# Karten-Grid. Anzahl Karten = Anzahl Aktivitäten (max 4, sonst aufteilen).
karten_inhalt = aktivitaeten_in_karten(p.aktivitaeten)  # [(label, body), ...]
n_cards = len(karten_inhalt)

card_h = 3.50
card_y = 2.56
# Saarpor: 4 Karten → Kartenbreite 2.95, Gap 0.30, Start-X 0.60
if n_cards == 4:
    card_w = 2.95
    gap = 0.30
    start_x = 0.60
elif n_cards == 3:
    card_w = 4.00
    gap = 0.30
    start_x = 0.60
else:
    # Anpassen, max 5 Karten
    margin = 0.60
    gap = 0.30
    card_w = (13.33 - 2 * margin - gap * (n_cards - 1)) / n_cards
    start_x = margin

for j, (label, body) in enumerate(karten_inhalt):
    x = start_x + j * (card_w + gap)
    # Karte zeichnen (Helper kümmert sich um Akzent-Strich oben)
    add_era_card(slide, x, 2.50, card_w, card_h, accent_w=0.85)
    # Oval mit Nummer in der Karte oben links
    add_era_numbered_oval(slide, x + 0.25, 2.80, j + 1, size=0.50)
    # Karten-Titel (DUNKELBLAU auf hellblauem Karten-Bg)
    add_era_textbox(slide, x + 0.25, 3.45, card_w - 0.50, 0.90,
                    label, font_size=14, bold=True, on_dark_bg=False)
    # Mini orange Trennstrich
    add_era_accent(slide, x + 0.25, 4.45, 0.60, 0.04)
    # Karten-Body (dunkelblau auf hellblau)
    add_era_textbox(slide, x + 0.25, 4.60, card_w - 0.50, 1.30,
                    body, font_size=11, on_dark_bg=False)

# Orange Trennlinie + Ergebnis-Text am Footer (Saarpor-Stil)
add_era_accent(slide, 0.60, 6.95, 12.10, 0.04)
add_era_textbox(slide, 0.60, 7.05, 12.50, 0.40,
                f"Ergebnis: {p.ergebnis}",
                font_size=12, italic=True, on_dark_bg=True)
```

### Mehrwert auf drei Ebenen (Saarpor Slide 14: 3 Hellblau-Karten nebeneinander)

```python
slide = prs.slides.add_slide(get_layout("Leer"))
add_era_dark_bg(slide)
add_era_logo(slide)
add_era_header(slide,
               "Ein klarer, messbarer Mehrwert auf drei Ebenen",
               f"Nutzen für {KUNDE} – strategisch, organisatorisch, menschlich.")

# Drei Karten. Saarpor: Kartenbreite 4.05", Gap 0.20", Höhe 4.40", Start (0.60, 2.30)
# Akzent-Strich-Breite 0.85
card_w = 4.05
card_h = 4.40
gap = 0.20
start_x = 0.60
card_y = 2.30

for i, ebene in enumerate(MEHRWERT_3_EBENEN):  # exakt 3
    x = start_x + i * (card_w + gap)
    add_era_card(slide, x, card_y, card_w, card_h, accent_w=0.85)
    # Ebenen-Titel (z.B. "Strategisch") in Dunkelblau auf hellblau
    add_era_textbox(slide, x + 0.30, card_y + 0.25, card_w - 0.50, 0.50,
                    ebene.ebene, font_size=18, bold=True, on_dark_bg=False)
    # Mini orange Trennstrich
    add_era_accent(slide, x + 0.30, card_y + 0.85, 0.70, 0.04)
    # Bullet-Liste der Punkte
    bullets_text = "\n".join(f"• {pt}" for pt in ebene.punkte)
    add_era_textbox(slide, x + 0.30, card_y + 1.10, card_w - 0.50, 2.26,
                    bullets_text, font_size=12, on_dark_bg=False)

# Footer mit Insight
add_era_footer(slide,
               "Drei Wirkungsebenen – ein gemeinsames Ergebnis: Klarheit, Geschwindigkeit, Akzeptanz.")
```

### Investition-Hero (Saarpor Slide 16: große Hellblau-Hero-Karte links + Inhalts-Bullets rechts)

**Wichtig — Text-Overflow-Schutz:** Diese Slide enthält viel variablen Text (Preis-Zahl, Inklusiv-Liste, Value-Prosa). Die Boxen müssen `MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE` haben ODER per Hand auf realistische Längen gekürzt werden. Konkret:
- **Preis-Zahl:** maximal 9 Zeichen (`"123.456 €"`) bei font_size=54. Wenn der Preis länger ist (z.B. mit Nachkomma + Währung), font_size auf 48 reduzieren.
- **Inklusiv-Bullets:** maximal 4 Stück, je maximal 80 Zeichen. Längere Items kürzen oder weglassen.
- **Value-Prosa rechts:** maximal 350 Zeichen. Längere Texte sind ein Schema-Signal, dass das `investition`-Feld zu lang ist — kürzen, nicht überfließen lassen.

```python
from pptx.enum.text import MSO_AUTO_SIZE

slide = prs.slides.add_slide(get_layout("Leer"))
add_era_dark_bg(slide)
add_era_logo(slide)
add_era_header(slide,
               "Ihre Investition",
               "Pauschalpreis – transparent, planbar, ohne Überraschungen.")

# Große Hellblau-Karte links: Breite 7.50", Höhe 4.60"
add_era_card(slide, 0.60, 2.20, 7.50, 4.60, accent_w=0.85)
add_era_textbox(slide, 0.85, 2.45, 7.00, 0.45, "Pauschalpreis",
                font_size=16, bold=True, on_dark_bg=False)

# Preis-Hero — Schrift-Größe adaptiv an Länge.
preis_str = PREIS_FORMATIERT  # z.B. "15.990 €"
preis_fs = 54 if len(preis_str) <= 9 else 44 if len(preis_str) <= 13 else 36
price_box = add_era_textbox(slide, 0.85, 2.95, 7.00, 1.50,
                             preis_str,
                             font_size=preis_fs, bold=True,
                             on_dark_bg=False, color=ERA_DARK_BLUE)
# Auto-shrink falls Text doch noch zu breit — pptx-Engine kümmert sich.
price_box.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE

# Sub-Info
add_era_textbox(slide, 0.85, 4.55, 7.00, 0.35,
                "zzgl. MwSt. – Spesen nach vorheriger Freigabe.",
                font_size=11, italic=True, on_dark_bg=False)

# Dunkelblauer Trennstrich
sep = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                              Inches(0.85), Inches(5.05),
                              Inches(7.00), Inches(0.03))
sep.fill.solid()
sep.fill.fore_color.rgb = ERA_DARK_BLUE
sep.line.fill.background()
add_era_textbox(slide, 0.85, 5.15, 7.00, 0.35, "Im Pauschalpreis enthalten:",
                font_size=12, bold=True, on_dark_bg=False)

# 2–4 kurze Inklusiv-Bullets — bei mehr Items abschneiden statt zu überlaufen
inklusiv_items = INVESTITION_INKLUSIV[:4]
y = 5.55
for inkl in inklusiv_items:
    # Lange Bullets kürzen, statt Overflow zu riskieren
    text = inkl if len(inkl) <= 80 else inkl[:77].rstrip() + "…"
    add_era_textbox(slide, 0.85, y, 7.00, 0.27, f"• {text}",
                    font_size=10, on_dark_bg=False)
    y += 0.27
    if y > 6.65:  # Karten-Boden bei 6.80 — Sicherheits-Margin
        break

# Rechte Spalte: Wert-Argument als Prosa in weiß auf dunkelblau (kein Karten-Bg)
value_text = INVESTITION_VALUE_TEXT
# Hart kürzen statt überlaufen lassen
if len(value_text) > 400:
    value_text = value_text[:397].rstrip() + "…"
value_box = add_era_textbox(slide, 8.40, 2.40, 4.50, 4.30,
                             value_text,
                             font_size=13, on_dark_bg=True)
value_box.text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE

add_era_footer(slide, "Investition in Klarheit, Geschwindigkeit, Umsetzungsfähigkeit.")
```

**Regel für ALLE Karten-Inhalte:** Wenn Text variabel ist (aus dem OfferContent kommt), entweder per `len()`-Check vorher kürzen oder `text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE` setzen. Niemals einfach hoffen, dass der Text passt — er passt im Zweifel nicht.

### Was im Angebot enthalten ist (nummerierte Liste, vertikal)

```python
slide = prs.slides.add_slide(get_layout("Leer"))
add_era_dark_bg(slide)
add_era_logo(slide)
add_era_header(slide,
               "Was im Angebot enthalten ist",
               "Leistungsumfang im Überblick.")

# Saarpor: Karten-Reihe mit nummerierten Ovalen. Bei 4–6 Items vertikal als Liste.
# Hier: vertikale Variante mit Hellblau-Karten als Zeilen.
items = LEISTUNGS_ITEMS
n = len(items)
# Verfügbarer Bereich: y=2.0 bis y=6.85
y_start = 2.0
y_end = 6.85
row_h = (y_end - y_start) / n - 0.10

y = y_start
for it in items:
    add_era_card(slide, 0.60, y, 12.10, row_h, accent_w=0.50)
    # Nummer-Oval links
    add_era_numbered_oval(slide, 0.85, y + (row_h - 0.50) / 2, it.nummer, size=0.50)
    # Titel + Beschreibung rechts vom Oval
    text_x = 1.65
    text_w = 10.80
    add_era_textbox(slide, text_x, y + 0.15, text_w, 0.35, it.titel,
                    font_size=13, bold=True, on_dark_bg=False)
    add_era_textbox(slide, text_x, y + 0.50, text_w, row_h - 0.55, it.beschreibung,
                    font_size=11, on_dark_bg=False)
    y += row_h + 0.10

add_era_footer(slide, "Klare Lieferobjekte, jederzeit nachvollziehbar.")
```

### Management Summary (Slide 2 in Saarpor: Prosa-Hero)

```python
slide = prs.slides.add_slide(get_layout("Leer"))
add_era_dark_bg(slide)
add_era_logo(slide)
add_era_header(slide,
               "Warum eine KI-Strategie – warum jetzt?",
               "Management Summary")
# Hero-Absatz mittig, max 12.10" breit, große Schrift
add_era_textbox(slide, 0.60, 2.20, 12.10, 4.50,
                MANAGEMENT_SUMMARY,
                font_size=16, on_dark_bg=True)
add_era_footer(slide, FOOTER_INSIGHT)
```

### Warum jetzt (Slide 4 in Saarpor: Karten + Kennzahlen)

```python
slide = prs.slides.add_slide(get_layout("Leer"))
add_era_dark_bg(slide)
add_era_logo(slide)
add_era_header(slide,
               "Warum jetzt der richtige Zeitpunkt ist",
               WARUM_JETZT_LEAD)  # z.B. „KI-Nutzung im deutschen Mittelstand hat sich in einem Jahr verdoppelt."

# Variante: 3 große Kennzahl-Karten + Begründung-Karten
# Für 2–5 Argumente: passende Karten-Anzahl wählen.
args = WARUM_JETZT_ARGUMENTE
n = len(args)
margin = 0.60
gap = 0.30
card_y = 2.20
card_h = 4.60
card_w = (13.33 - 2 * margin - gap * (n - 1)) / n
for i, arg in enumerate(args):
    x = margin + i * (card_w + gap)
    add_era_card(slide, x, card_y, card_w, card_h, accent_w=0.85)
    # Optional große Zahl wenn arg.kennzahl gesetzt; sonst nur Prosa.
    add_era_textbox(slide, x + 0.30, card_y + 0.40, card_w - 0.50, 1.20,
                    arg,
                    font_size=14, bold=True, on_dark_bg=False)
    # Restlicher Text falls länger
    # …

add_era_footer(slide, "Wer wartet, verliert nicht linear – sondern exponentiell.")
```

## Inhaltsquellen pro Render-Aufruf

Der Render-Aufruf liefert Claude:
1. **Discovery-Call-Transkript** – Roh-Material für Kontext-Tiefe.
2. **Freigegebenes OfferContent (JSON)** – die vom Berater finalisierte Inhaltsversion. **Diese ist führend** für die Inhalte der Slides 2–N+5. Das Transkript wird nur konsultiert, wenn das OfferContent nicht alle Details abdeckt (z. B. spezifische Personen-Namen, die im Discovery erwähnt wurden).

Wenn `OfferContent` komplett ist (was es bei v2 immer sein muss), keine Inhalte aus dem Transkript erfinden, die nicht im OfferContent stehen. Das OfferContent ist die Single Source of Truth.

## QA (Pflicht nach jeder Erstellung)

```bash
python -m markitdown /home/claude/era_presentation.pptx

python /mnt/skills/public/pptx/scripts/office/soffice.py --headless --convert-to pdf /home/claude/era_presentation.pptx
rm -f /home/claude/slide-*.jpg
pdftoppm -jpeg -r 150 /home/claude/era_presentation.pdf /home/claude/slide
ls -1 /home/claude/slide-*.jpg
```

Prüfpunkte:
1. Kundenname korrekt unter „Für:" ?
2. Berater-Daten vollständig?
3. Datum auf Deutsch?
4. Footer (© ERA Group + Seitenzahl) auf jeder Folie?
5. ERA-Logo sichtbar?
6. Kein Placeholder-Text übrig?

---

## Assets

- `assets/ERA_Template.pptx` – Offizielle ERA Group Vorlage mit CI, Theme, Master und allen Layouts. Immer als Basis verwenden, niemals von Null erstellen.
