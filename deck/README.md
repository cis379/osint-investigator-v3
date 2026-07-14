# Briefing deck

Leadership/IT briefing for OSINT Investigator. Built from the live system + a real completed case
(INV-20260626-001), so every figure is grounded.

## Files
- **`osint-brief.pptx`** — the **13-slide** deck (dark "intelligence-briefing" theme), with **speaker
  notes on every slide**, and **real graph pictures** from the scam case embedded. Import this into Google Slides.
- **`img/`** — the rendered graph PNGs from the real case (overview, attribution cluster, tracker hub).
- **`osint-brief.md`** — the narrative slide content + speaker notes in plain text (easy to copy-edit).
- **`render_graphs.py`** — regenerates the graph PNGs from the real `investigations/INV-20260626-001/
  graph.json` (`python deck/render_graphs.py`). Build-only deps: `matplotlib` + `networkx`.
- **`build_deck.py`** — regenerates the `.pptx` (`python deck/build_deck.py`; run `render_graphs.py`
  first). Build-only dep: `python-pptx` (`pip install python-pptx` — NOT a system dependency).

To rebuild everything: `python deck/render_graphs.py && python deck/build_deck.py`.

## Get it into Google Slides (2 minutes)
1. Go to **drive.google.com** → **New → File upload** → choose `deck/osint-brief.pptx`.
2. In Drive, **right-click the file → Open with → Google Slides**. It auto-converts to a native
   Google Slides deck (speaker notes come across).
3. **File → Save as Google Slides** (if you want a permanent Slides copy), then edit/brand freely.

*(Alternative: in an existing Google Slides deck, **File → Import slides → Upload** the `.pptx`.)*

## Slide order (13)
1. Title · 2. What it is (BLUF) · 3. **OV-1** — the 3 distinct collector agents + which SKILL runs each,
red team as its own stage, paid-CTI placeholder on the structured collector · 4. Ontology — high-level
CATEGORIES · 5. The tools — a real sample of the 58, grouped by selector · 6. Software laydown ·
7. **Use case 1/3** — scam URL → mapped network (real 119-node graph picture) · 8. **Use case 2/3** —
who runs it (attribution cluster picture) + how we know (shared-tracker picture) · 9. Use case 3/3 —
the trust story (red-team self-correction) · 10. IT approval — data egress · 11. IT approval —
provenance · 12. Close / the ask · 13. **Appendix** — exact requirements / installations.

`osint-brief.md` holds the narrative copy + notes (the built `.pptx` extends it with the graph images
and the install appendix).

## Presenting tips
- The **speaker notes** carry the narration — open **View → Presenter view** in Google Slides.
- The **OV-1 (slide 3)** and the **two use-case slides (6–7)** are the ones to slow down on.
- If you want to show the live product, open a real case's `graph.html` / `report.html` from an
  `investigations/INV-*/` folder alongside the deck.
