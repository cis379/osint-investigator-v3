# Briefing deck

Leadership/IT briefing for OSINT Investigator. Built from the live system + a real completed case
(INV-20260626-001), so every figure is grounded.

## Files
- **`osint-brief.pptx`** — the 10-slide deck (dark "intelligence-briefing" theme), with **speaker
  notes on every slide**. This is what you import into Google Slides.
- **`osint-brief.md`** — the full slide content + speaker notes in plain text (source of truth / easy
  to copy-edit).
- **`build_deck.py`** — regenerates the `.pptx` from scratch (`python deck/build_deck.py`). Requires
  `python-pptx` (build-only: `pip install python-pptx` — NOT a system dependency).

## Get it into Google Slides (2 minutes)
1. Go to **drive.google.com** → **New → File upload** → choose `deck/osint-brief.pptx`.
2. In Drive, **right-click the file → Open with → Google Slides**. It auto-converts to a native
   Google Slides deck (speaker notes come across).
3. **File → Save as Google Slides** (if you want a permanent Slides copy), then edit/brand freely.

*(Alternative: in an existing Google Slides deck, **File → Import slides → Upload** the `.pptx`.)*

## Slide order
1. Title · 2. What it is (BLUF) · 3. OV-1 (operational concept) · 4. Ontology → tools ·
5. Software laydown · 6. Use case 1/2 (scam URL → mapped network) · 7. Use case 2/2 (the trust story) ·
8. Why IT should approve — data egress · 9. Why IT should approve — provenance · 10. Close / the ask.

Back-up/appendix talking points are at the bottom of `osint-brief.md`.

## Presenting tips
- The **speaker notes** carry the narration — open **View → Presenter view** in Google Slides.
- The **OV-1 (slide 3)** and the **two use-case slides (6–7)** are the ones to slow down on.
- If you want to show the live product, open a real case's `graph.html` / `report.html` from an
  `investigations/INV-*/` folder alongside the deck.
