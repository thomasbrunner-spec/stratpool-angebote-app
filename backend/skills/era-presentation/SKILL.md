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

## Layout-Variation – Folie für Folie überlegen

Ein gutes ERA-Angebot lebt von **visueller Abwechslung**. Nicht jede Folie soll `1 x Content` sein. Beim Komponieren des Decks pro Folie aktiv überlegen, welches Layout am besten passt:

| Inhalt | Bevorzugtes Layout |
|--------|--------------------|
| Vergleich zweier Aspekte | `2 x Content` |
| 3 Säulen / Phasen / Kategorien | `3 x Content` oder `4 x Content` |
| Text + visuelles Element | `Content + Picture` |
| Hervorgehobener Abschnitt | `1/2 Page Light Blue Horizontal Panel` oder `Dark Blue Panel` |
| Hellblauer Hintergrund (visuelle Pause) | `1 x Content Light Blue` |
| Übergang zwischen Kapiteln | `Abschnitts-\nüberschrift` |
| Großes Statement, freie Komposition | `Nur Titel` oder `Leer` |
| Investitions-Hero (große Zahl) | `Leer` mit eigenem Layout |
| Anwendungsfelder / Phasen mit nummerierten Schritten | `Leer` mit Kreisen + Verbindungen |

**Faustregel:** In einem 12-Folien-Deck sollten mindestens 4–5 verschiedene Layouts vorkommen. Wenn `1 x Content` mehr als 4× hintereinander auftaucht, bewusst variieren.

## Eigene Layouts – Fallback wenn kein Template-Layout passt

Wenn keines der 43 Template-Layouts den gewünschten Inhalt gut abbildet, darf Claude ein eigenes Layout auf Basis des `Leer`-Layouts bauen. Das CI muss dabei immer gewahrt bleiben.

### Entscheidungsbaum
1. **Gibt es ein passendes Template-Layout?** → Bevorzugen, aber bewusst variieren (s.o.)
2. **Passt kein Layout gut?** → Eigenes Layout auf `Leer`-Basis mit ERA-CI aufbauen
3. **Niemals** ohne ERA-Farben und -Schrift arbeiten

### Bausteine für eigene Layouts

**Dunkelblaue Titelleiste (ERA-Standard oben):**
```python
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def add_era_title_bar(slide, title_text):
    """ERA-typische dunkelblaue Titelleiste oben."""
    bg = slide.shapes.add_shape(1, Inches(0), Inches(0), prs.slide_width, Inches(1.1))
    bg.fill.solid()
    bg.fill.fore_color.rgb = RGBColor(0x00, 0x3A, 0x70)
    bg.line.fill.background()
    txBox = slide.shapes.add_textbox(Inches(0.4), Inches(0.15), Inches(12), Inches(0.8))
    run = txBox.text_frame.paragraphs[0].add_run()
    run.text = title_text
    run.font.name = "Trebuchet MS"
    run.font.size = Pt(28)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
```

**Textbox in ERA-Farbe:**
```python
def add_era_textbox(slide, left_in, top_in, width_in, height_in,
                    text, font_size=14, bold=False, dark_blue=True):
    txBox = slide.shapes.add_textbox(
        Inches(left_in), Inches(top_in), Inches(width_in), Inches(height_in))
    tf = txBox.text_frame
    tf.word_wrap = True
    run = tf.paragraphs[0].add_run()
    run.text = text
    run.font.name = "Trebuchet MS"
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(0x00, 0x3A, 0x70) if dark_blue else RGBColor(0xFF, 0xFF, 0xFF)
    return txBox
```

**Orangener Akzentbalken:**
```python
def add_era_accent(slide, left_in, top_in, width_in, height_in=0.05):
    bar = slide.shapes.add_shape(1,
        Inches(left_in), Inches(top_in), Inches(width_in), Inches(height_in))
    bar.fill.solid()
    bar.fill.fore_color.rgb = RGBColor(0xFF, 0x9C, 0x00)
    bar.line.fill.background()
    return bar
```

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

- ❌ Andere Farben als die ERA-Palette
- ❌ Andere Schrift als Trebuchet MS
- ❌ Folie ohne Titelleiste (außer Cover und Section Header)
- ❌ Footer/Logo manuell hinzufügen (kommt automatisch vom Master)

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
