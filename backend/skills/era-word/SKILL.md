---
name: era-word
description: >
  Use this skill whenever the user wants to create, edit, or produce a Word document (.docx) in the ERA Group corporate design (CI/CD). Trigger when the user mentions "ERA Dokument", "ERA Word", "ERA Bericht", "ERA Gutachten", "ERA Konzept", "ERA Brief", or asks to create any document that should follow the ERA Group corporate identity. Also trigger when creating professional consulting reports, analysis documents, or proposals in the ERA style. Always use this skill — do NOT try to create ERA-style Word documents without it.
---

# ERA Group – Word Document Skill

Creates professional `.docx` files in the **ERA Group Corporate Identity**.

This skill **only** specifies the design rules. The runtime is `python-docx`,
provided by Anthropic's built-in `docx` skill. Combine both:
1. Read this skill for the ERA-CI rules below.
2. Use python-docx (built-in `docx` skill) for the actual document construction.
3. Save the result to `$OUTPUT_DIR/angebot.docx` (workspace output dir).

---

## ERA Corporate Identity — Complete Reference

### Colours
| Role | Hex | Usage |
|------|-----|-------|
| Dark Navy | `1B3A5C` | Heading 1, Heading 3, title text, header text bold |
| Medium Blue | `2E6B9E` | Heading 2, subtitle on title page |
| Body Text | `4A4A4A` | All body/normal text |
| ERA Orange | `E8941A` | Decorative lines: header bottom border, footer top border, title page separator line |

### Typography
- **Font**: Arial (all elements)
- **Body text**: 11pt, color `4A4A4A`
- **Language**: `de-DE`

### Heading Styles
| Style | Size | Bold | Color | Spacing before/after (pt) |
|-------|------|------|-------|---------------------------|
| Heading 1 | 16pt | Yes | `1B3A5C` | 18 / 12 |
| Heading 2 | 13pt | Yes | `2E6B9E` | 14 / 9 |
| Heading 3 | 11pt | Yes | `1B3A5C` | 10 / 6 |

### Page Layout
- **Paper**: A4
- **Margins**: 2.54 cm (= 1 inch) all sides
- **Header / Footer distance from edge**: 1.25 cm

### Header (every content page, NOT the title page)
- **Bottom border**: orange line (`E8941A`), 0.5pt single
- **Left**: "ERA Group" — bold, navy `1B3A5C`, 8pt
- **Right (tab-aligned)**: Document title — italic, 8pt, default color `4A4A4A`
- Spacing after the header paragraph: 10pt

### Footer (every content page, NOT the title page)
- **Top border**: orange line (`E8941A`), 0.25pt single
- **Left**: "Vertraulich" — italic, 7pt
- **Right (tab-aligned)**: `Seite [n] von [m]` — 7pt

### Title Page Structure (always page 1, no header/footer)
1. **ERA logo** — image from `assets/era_logo.png`, ~5.8 cm wide
2. Spacing below logo, then an **orange separator line** (paragraph bottom border, `E8941A`, ~1.5pt)
3. **Main title** — bold, `1B3A5C`, 22pt
4. **Subtitle** — `2E6B9E`, 16pt
5. **Client name** — 14pt
6. **Meta rows** (date, version, author) — 11pt regular, gray or dark

---

## Document Structure for an ERA Offer (`Angebot`)

A typical ERA offer has the following sections in order. Each Heading 1 starts a new content section (not a new page unless content demands it):

1. **Ausgangssituation** — description of the client's current state, derived from discovery
2. **Zielsetzung** — what the engagement should achieve
3. **Leistungsumfang** — top-level scope intro, then a numbered or bulleted list of `Bestandteile`. Each Bestandteil gets its own Heading 2 with a short description.
4. **Vorgehen / Projektablauf** — phases or methodology, sequenced
5. **Investition** — fee, payment terms, value framing. Headline figure can be set bold and slightly larger (14pt) for emphasis.
6. **Rahmenbedingungen** — payment terms, confidentiality, validity of the offer
7. **Kontakt** — consultant block (name, role, phone, email)

The body text is always **regular**, never bold by default. Bold is reserved for headings, section labels inside a paragraph, and the Investition headline figure.

---

## Title Page — Two Consultants

If the brief lists two consultants, render them as a meta block on the title page:

- **Hauptberater** (primary, the offer's owner): listed first
- **Co-Berater** (secondary, optional per offer): listed below

Each consultant block is 4 lines, 11pt regular, color `4A4A4A`:
```
{Name}
{Titel}
M: {Tel}
E: {Email}
```

If only one consultant is provided, render only the primary block.

---

## Implementation Workflow (python-docx)

### Step 1: Set up the document with ERA styles

Use python-docx (built-in `docx` skill provides it). Create the document, register the heading styles, set up section properties (A4 page, 1-inch margins, header/footer), and the title page section without header/footer.

### Step 2: Embed the logo

The ERA logo is in `assets/era_logo.png` of this skill. Copy it to a working location, then add it as the first paragraph of the title page section, ~5.8 cm wide.

### Step 3: Build the title page (section 1)

Title page has its own section without header/footer. Logo, orange separator line (paragraph bottom border), main title, subtitle, client name, and the meta block. Then a section break.

### Step 4: Build content pages (section 2 onwards)

Section 2 is the body. It has the orange-bordered header ("ERA Group" left, document title right) and footer ("Vertraulich" left, page number right). All Heading 1 paragraphs trigger the section structure described above.

### Step 5: Save and validate

Save to `$OUTPUT_DIR/angebot.docx` (so it lands in the workspace Files API). Validate using Anthropic's docx-validation tooling if available; at minimum, open the file with `Document(...)` again and inspect that the section count, header, footer, and title-page logo are present.

---

## Key ERA Rules

- **Never omit the ERA logo** on the title page — embed from `assets/era_logo.png`
- **Orange lines** (`E8941A`) mark the header bottom and footer top — these are the signature CI element
- **Navy blue** (`1B3A5C`) is the primary brand colour for headings and header text
- **Two sections**: title page (no header/footer) + content pages (with header/footer)
- **Vertraulich** always appears in the footer (unless the client explicitly says otherwise)
- **Font is always Arial** — never substitute
- **Body text colour** is `4A4A4A`, not pure black
- **Body text is regular by default** — bold is reserved for headings, occasional emphasis, and the Investition headline figure
- **A4 page format** with 2.54 cm margins
- The output **must** be saved as `$OUTPUT_DIR/angebot.docx` (workspace path,
  NOT `/home/claude/angebot.docx` alone — those bytes never reach the host)

---

## Assets

- `assets/era_logo.png` — official ERA logo for the title page
