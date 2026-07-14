"""Build osint-brief.pptx from the briefing content — a Google-Slides-importable deck.

Build-only (python-pptx is NOT a system dependency; not in requirements.txt).
Run:  python deck/build_deck.py   ->   deck/osint-brief.pptx
Then: upload the .pptx to Google Drive and open with Google Slides (auto-converts).
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
import os

# ---- palette (dark intelligence-briefing theme) ---------------------------
BG     = RGBColor(0x0D, 0x1B, 0x2A)   # deep navy
PANEL  = RGBColor(0x16, 0x32, 0x4F)   # panel blue
BLUE   = RGBColor(0x58, 0xA6, 0xFF)   # accent / seed
GREEN  = RGBColor(0x3F, 0xB9, 0x50)   # highly likely / good
AMBER  = RGBColor(0xD2, 0x99, 0x22)   # probable / caution
PURPLE = RGBColor(0xBC, 0x8C, 0xFF)   # findings / gates
TEXT   = RGBColor(0xE6, 0xED, 0xF3)   # body
MUTE   = RGBColor(0x9F, 0xB0, 0xC3)   # muted
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW, SH = prs.slide_width, prs.slide_height


def slide():
    s = prs.slides.add_slide(BLANK)
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SW, SH)
    r.fill.solid(); r.fill.fore_color.rgb = BG; r.line.fill.background()
    r.shadow.inherit = False
    s.shapes._spTree.remove(r._element); s.shapes._spTree.insert(2, r._element)
    return s


def _set(tf, size, color=TEXT, bold=False, align=PP_ALIGN.LEFT):
    for p in tf.paragraphs:
        p.alignment = align
        for run in p.runs:
            run.font.size = Pt(size); run.font.color.rgb = color
            run.font.bold = bold; run.font.name = "Calibri"


def box(s, x, y, w, h, fill=None, line=None, line_w=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    b = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        b.fill.background()
    else:
        b.fill.solid(); b.fill.fore_color.rgb = fill
    if line is None:
        b.line.fill.background()
    else:
        b.line.color.rgb = line; b.line.width = Pt(line_w)
    b.shadow.inherit = False
    return b


def text(s, x, y, w, h, runs, size=16, color=TEXT, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, space=4):
    """runs: str, or list of (text, size, color, bold) tuples, or list of paragraphs
    where a paragraph is a list of such tuples."""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    if isinstance(runs, str):
        runs = [[(runs, size, color, bold)]]
    elif runs and isinstance(runs[0], tuple):
        runs = [runs]
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.space_after = Pt(space)
        if isinstance(para, tuple):
            para = [para]
        for (t, sz, col, bd) in para:
            r = p.add_run(); r.text = t
            r.font.size = Pt(sz); r.font.color.rgb = col; r.font.bold = bd
            r.font.name = "Calibri"
    return tb


def bullets(s, x, y, w, h, items, size=17, color=TEXT, gap=7):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        if isinstance(it, str):
            it = [("•  " + it, size, color, False)]
        else:  # list of runs; caller supplies bullet
            pass
        for (t, sz, col, bd) in it:
            r = p.add_run(); r.text = t
            r.font.size = Pt(sz); r.font.color.rgb = col; r.font.bold = bd
            r.font.name = "Calibri"
    return tb


def header(s, kicker, title):
    box(s, 0, 0, 13.333, 0.12, fill=BLUE)
    text(s, 0.6, 0.35, 12, 0.4, kicker.upper(), size=13, color=BLUE, bold=True)
    text(s, 0.6, 0.72, 12.1, 1.0, title, size=30, color=WHITE, bold=True)


def footer(s, name):
    text(s, 0.6, 7.03, 8, 0.35, "OSINT Investigator  ·  external-OSINT only  ·  runs locally",
         size=10, color=MUTE)
    text(s, 9.0, 7.03, 3.7, 0.35, name, size=10, color=MUTE, align=PP_ALIGN.RIGHT)


def notes(s, txt):
    s.notes_slide.notes_text_frame.text = txt


def chip(s, x, y, w, label, color):
    b = box(s, x, y, w, 0.42, fill=PANEL, line=color, line_w=1.5)
    tf = b.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = label; r.font.size = Pt(12.5); r.font.bold = True
    r.font.color.rgb = TEXT; r.font.name = "Calibri"
    return b


def arrow(s, x, y, w=0.45):
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(0.28))
    a.fill.solid(); a.fill.fore_color.rgb = BLUE; a.line.fill.background(); a.shadow.inherit = False
    return a


# ============================================================ SLIDE 1 — TITLE
s = slide()
box(s, 0, 0, 13.333, 0.18, fill=BLUE)
box(s, 0, 7.32, 13.333, 0.18, fill=GREEN)
text(s, 0.9, 2.15, 11.5, 1.2, "OSINT Investigator", size=54, color=WHITE, bold=True)
text(s, 0.9, 3.25, 11.5, 0.8,
     "Automated external-OSINT investigation — from one seed to a cited intelligence graph",
     size=22, color=BLUE, bold=True)
text(s, 0.9, 4.4, 11.5, 1.6, [
    [("Give it a seed (domain, email, username, name, IP…) → it pivots through open sources, "
      "builds a confidence-tiered entity graph, and produces a cited CTI report.", 17, TEXT, False)],
    [("External OSINT only · Runs locally · Never fabricates a finding.", 16, GREEN, True)],
    [("Open source (MIT) · agent-vendor-agnostic (Claude Code or OpenAI Codex)", 14, MUTE, False)],
], space=8)
text(s, 0.9, 6.55, 11.5, 0.5, "Analyst briefing  ·  2026", size=13, color=MUTE)
notes(s, "This is a force-multiplier for an OSINT analyst. It does the tedious collection and "
         "first-pass link analysis at machine speed, and shows its work so you can trust or challenge "
         "every line. I'll finish with a real case where it mapped a ticket-fraud network from one URL.")

# ============================================================ SLIDE 2 — BLUF
s = slide(); header(s, "What it is", "One seed in → a cited intelligence graph out")
text(s, 0.6, 1.9, 6.0, 0.5, "THE PROBLEM", size=13, color=AMBER, bold=True)
text(s, 0.6, 2.25, 6.0, 2.0,
     "An analyst handed one selector faces hours of manual lookups across dozens of tools — then has "
     "to keep every link straight by hand.", size=17, color=TEXT)
text(s, 0.6, 3.5, 6.0, 0.5, "WHAT THIS DOES", size=13, color=GREEN, bold=True)
bullets(s, 0.6, 3.85, 6.2, 3.0, [
    "Runs the right tools automatically (ontology-driven, not hardcoded)",
    "Analyzes raw output and grades every finding by confidence",
    "Pivots on its own findings — loops until the leads run dry",
    "Red-teams itself before writing a report",
    "Ships a narrative report — every finding cited to tool output",
], size=15.5)
box(s, 7.05, 1.95, 5.7, 4.9, fill=PANEL, line=BLUE, line_w=1.5)
text(s, 7.35, 2.15, 5.1, 0.5, "THREE PROPERTIES THAT MAKE IT TRUSTWORTHY", size=13, color=BLUE, bold=True)
text(s, 7.35, 2.75, 5.1, 4.0, [
    [("1. No hallucination", 18, WHITE, True)],
    [("Every claim traces to a specific tool output or source URL.", 14.5, MUTE, False)],
    [(" ", 6, MUTE, False)],
    [("2. Full audit trail", 18, WHITE, True)],
    [("Every tool run logged raw; the graph is reproducible.", 14.5, MUTE, False)],
    [(" ", 6, MUTE, False)],
    [("3. Honest about limits", 18, WHITE, True)],
    [("Gaps are documented, never faked.", 14.5, MUTE, False)],
], space=5)
footer(s, "BLUF")
notes(s, "The headline for an analyst is the pivoting and confidence tiering. The headline for IT is "
         "the three properties on the right — local, auditable, external-only.")

# ============================================================ SLIDE 3 — OV-1
s = slide(); header(s, "Operational Concept (OV-1)", "One seed → cited graph + report, with two adversarial gates")
y0 = 2.15
# seed
chip(s, 0.6, y0+0.9, 1.5, "SEED\nselector", BLUE)
arrow(s, 2.15, y0+1.05)
# supervisor panel with 3 lines
box(s, 2.75, y0+0.15, 3.5, 3.0, fill=PANEL, line=BLUE, line_w=1.5)
text(s, 2.85, y0+0.25, 3.3, 0.5, "SUPERVISOR  (the only brain)", size=13, color=BLUE, bold=True)
text(s, 2.85, y0+0.62, 3.3, 0.4, "routes via the ONTOLOGY", size=11.5, color=MUTE)
chip(s, 2.95, y0+1.05, 3.1, "STRUCTURED line — 58 typed tools", GREEN)
chip(s, 2.95, y0+1.55, 3.1, "WEB-SEARCH line — searches + fetches", GREEN)
chip(s, 2.95, y0+2.05, 3.1, "ACTIVE line — tracker/analytics IDs", GREEN)
text(s, 2.85, y0+2.6, 3.3, 0.4, "collect raw · log · NEVER write the graph", size=11, color=AMBER, bold=True)
arrow(s, 6.3, y0+1.55)
# tier + commit + pivot loop
box(s, 6.9, y0+0.15, 2.7, 3.0, fill=PANEL, line=GREEN, line_w=1.5)
text(s, 7.0, y0+0.3, 2.5, 2.8, [
    [("ANALYZE + TIER", 14, WHITE, True)],
    [("highly likely /", 12.5, GREEN, True)],
    [("probable /", 12.5, AMBER, True)],
    [("possible", 12.5, MUTE, True)],
    [(" ", 8, MUTE, False)],
    [("COMMIT to graph", 13.5, WHITE, True)],
    [("→ PIVOT each new", 12.5, TEXT, False)],
    [("entity (loop)", 12.5, TEXT, False)],
], space=3)
arrow(s, 9.65, y0+1.55)
# gates + product
box(s, 10.25, y0+0.15, 2.5, 3.0, fill=PANEL, line=PURPLE, line_w=1.5)
text(s, 10.35, y0+0.3, 2.3, 2.8, [
    [("RED-TEAM GATE", 14, PURPLE, True)],
    [("challenges the", 12.5, MUTE, False)],
    [("analysis", 12.5, MUTE, False)],
    [(" ", 8, MUTE, False)],
    [("REPORT-WRITER", 13.5, WHITE, True)],
    [("+ grounding gate", 12.5, MUTE, False)],
    [(" ", 6, MUTE, False)],
    [("report.md / .html", 13, GREEN, True)],
], space=3)
text(s, 0.6, 6.15, 12.1, 0.8,
     "Separation of powers: collectors are dumb pipes · one supervisor analyzes & tiers "
     "(the raw/analysis split) · an independent red team tries to break the conclusions before they ship.",
     size=14, color=TEXT)
footer(s, "OV-1")
notes(s, "The key idea is separation of powers. Collectors are dumb pipes. One supervisor does all "
         "analysis. An independent red-team agent tries to break the conclusions before they reach you. "
         "That's what keeps a big auto-generated graph honest.")

# ============================================================ SLIDE 4 — ONTOLOGY
s = slide(); header(s, "The routing brain", "The ontology decides what runs — nothing is hardcoded")
rows = [("Selector types the ontology can reason about", "92", BLUE),
        ("Types with a dedicated structured tool", "20", GREEN),
        ("Runnable tools wired into the engine", "58", GREEN),
        ("Candidate-tool roadmap (what could be built)", "1,031", MUTE)]
yy = 2.05
for i, (lbl, num, col) in enumerate(rows):
    box(s, 0.6, yy, 6.7, 0.72, fill=PANEL if i % 2 == 0 else BG, line=None)
    text(s, 0.8, yy+0.13, 5.2, 0.5, lbl, size=15, color=TEXT)
    text(s, 6.0, yy+0.06, 1.2, 0.6, num, size=24, color=col, bold=True, align=PP_ALIGN.RIGHT)
    yy += 0.78
box(s, 7.6, 2.05, 5.15, 4.35, fill=PANEL, line=BLUE, line_w=1.5)
text(s, 7.85, 2.25, 4.7, 4.0, [
    [("ROUTING", 13, BLUE, True)],
    [("plan_collection(selector, type) → the exact tools to run + web-search availability + "
      "a fallback for bare handles.", 14, TEXT, False)],
    [(" ", 7, MUTE, False)],
    [("PIVOTING", 13, BLUE, True)],
    [("Each type declares what it yields (domain → IPs, certs, subdomains), so the system plans "
      "chains several hops ahead.", 14, TEXT, False)],
    [(" ", 7, MUTE, False)],
    [("HONESTY, ENFORCED", 13, GREEN, True)],
    [("A regression test asserts every runnable tool is accounted for — the ontology can't lie "
      "about what runs.", 14, TEXT, False)],
], space=5)
footer(s, "Ontology → Tools")
notes(s, "Adding coverage is cheap and safe: a new tool is a spec the ontology routes to, not bespoke "
         "plumbing. The honesty test means the system's self-description is always true — important when "
         "you brief findings up the chain.")

# ============================================================ SLIDE 5 — SOFTWARE LAYDOWN
s = slide(); header(s, "Software laydown", "Small, auditable, standard — pure-Python engine")
text(s, 0.6, 1.95, 6.0, 0.4, "CORE DEPENDENCIES (7, pinned)", size=13, color=GREEN, bold=True)
deps = [("requests", "HTTP client for all API tools"), ("networkx", "the investigation graph"),
        ("python-whois", "WHOIS lookups"), ("dnspython", "DNS records"),
        ("beautifulsoup4", "HTML parsing"), ("mmh3", "favicon hashing (ownership corroborator)"),
        ("phonenumbers", "phone parsing/validation")]
yy = 2.4
for i, (pk, ds) in enumerate(deps):
    box(s, 0.6, yy, 6.0, 0.5, fill=PANEL if i % 2 == 0 else BG)
    text(s, 0.75, yy+0.07, 2.2, 0.4, pk, size=14, color=BLUE, bold=True)
    text(s, 2.9, yy+0.08, 3.6, 0.4, ds, size=12.5, color=MUTE)
    yy += 0.54
box(s, 6.95, 1.95, 5.8, 4.9, fill=PANEL, line=GREEN, line_w=1.5)
text(s, 7.2, 2.1, 5.3, 0.4, "WHAT WE BUILT  (~48 Python modules under src/)", size=13, color=GREEN, bold=True)
text(s, 7.2, 2.6, 5.35, 4.2, [
    [("core/", 14.5, WHITE, True), ("  selector detection + investigation state", 13.5, MUTE, False)],
    [("ontology/", 14.5, WHITE, True), ("  the routing brain + honesty annotator", 13.5, MUTE, False)],
    [("tools/", 14.5, WHITE, True), ("  58 tools via declarative HttpTool/CliTool specs + registry", 13.5, MUTE, False)],
    [("graph/", 14.5, WHITE, True), ("  NetworkX graph + vis.js visualizer", 13.5, MUTE, False)],
    [("report/", 14.5, WHITE, True), ("  narrative CTI report (MD + HTML + Mermaid)", 13.5, MUTE, False)],
    [("logger/", 14.5, WHITE, True), ("  the raw audit trail", 13.5, MUTE, False)],
    [("scripts/health_check.py", 14.5, GREEN, True), ("  the safety gate (registry + floor + 3 suites)", 13.5, MUTE, False)],
    [(" ", 8, MUTE, False)],
    [("Optional external CLIs + keyed APIs (Shodan/DNSlytics/Flare) are opt-in and degrade "
      "gracefully — runs fully with zero keys.", 13, AMBER, False)],
], space=6)
footer(s, "Software laydown")
notes(s, "Seven mainstream open-source packages, everything pinned, one command to build and "
         "self-verify. No black box — an IT reviewer can read the whole dependency list on one slide.")

# ============================================================ SLIDE 6 — USE CASE 1
s = slide(); header(s, "Use case · ticket-fraud network", "One scam URL → a mapped network (auto-generated)")
box(s, 0.6, 1.9, 12.15, 0.95, fill=PANEL, line=BLUE, line_w=1.5)
text(s, 0.8, 2.02, 12, 0.9, [
    [("SEED:  ", 15, MUTE, True), ("colosseumdiroma-tickets.com", 16, BLUE, True),
     ("  — a fake Colosseum ticket-resale site", 15, TEXT, False)],
    [("AUTO-GENERATED RESULT:  ", 15, MUTE, True),
     ("a 119-node / 170-edge intelligence graph", 16, GREEN, True)],
], space=4)
text(s, 0.6, 3.1, 6.1, 0.4, "WHAT THE PIVOTS BUILT, AUTOMATICALLY", size=13, color=GREEN, bold=True)
bullets(s, 0.6, 3.5, 6.2, 3.2, [
    [("Registration", 15.5, WHITE, True), ("  — WHOIS/RDAP surfaced registrant org "
     "'The Walker Tours LLC' (survived privacy redaction); created 2024-01-16", 14, TEXT, False)],
    [("Hosting estate", 15.5, WHITE, True), ("  — domain → AWS IPs → co-hosted lookalike domains → "
     "loop. The engine that turns ONE site into the NETWORK", 14, TEXT, False)],
    [("Content identifiers", 15.5, WHITE, True), ("  — the active line extracted 15 tracker IDs "
     "(Google Ads AW-, GA4 G-, Universal Analytics UA-) tying sites to a common owner", 14, TEXT, False)],
], size=14, gap=9)
box(s, 7.0, 3.1, 5.75, 3.55, fill=PANEL, line=GREEN, line_w=1.5)
text(s, 7.25, 3.25, 5.3, 0.5, "THE GRAPH, TIERED HONESTLY", size=13, color=GREEN, bold=True)
text(s, 7.25, 3.8, 5.3, 2.8, [
    [("75 domains · 15 tracker IDs · 7 companies · 5 IPs · phones · emails", 14.5, TEXT, False)],
    [(" ", 6, MUTE, False)],
    [("96 highly likely", 17, GREEN, True), ("   ·   ", 15, MUTE, False),
     ("14 probable", 15, AMBER, True), ("   ·   ", 15, MUTE, False), ("9 possible", 15, MUTE, True)],
    [(" ", 6, MUTE, False)],
    [("Weak leads kept visible, not dropped. The count is NOT over-sold as a '75-site scam estate' "
      "— AWS nameservers, a CMS host, and the legit origin-brand domains are called out explicitly.",
      13.5, MUTE, False)],
], space=5)
footer(s, "Use case 1/2")
notes(s, "Start at one URL. The system expands the hosting neighborhood, fingerprints the sites, and "
         "clusters them by shared analytics IDs — the technique investigative journalists use by hand. "
         "Here it did it automatically and kept a running, tiered graph.")

# ============================================================ SLIDE 7 — USE CASE 2
s = slide(); header(s, "Use case · the trust story", "The system pressure-tests itself and refuses to over-claim")
steps = [
    ("1", "An early pass read the estate as TWO operators.", TEXT),
    ("2", "The RED-TEAM gate challenged the merge: 'shared hosting ≠ shared ownership — show an independent corroborator.'", TEXT),
    ("3", "A deeper pivot found the GOLD STANDARD: the seed itself ran a strong UA-131208121-1 analytics property in its 2024 Wayback snapshot — the same property as sevillafreetour.com.", GREEN),
    ("4", "On SIX independent corroborators, red-team round 3 REVISED the conclusion to ONE operator group: Grupo Feel The City S.L. (Seville), fronted by two US shells sharing federal EIN 37-2091569.", TEXT),
    ("5", "It distinguished the LEGITIMATE 2010 origin tour business from the 2024–26 scam build-out — and flagged the legit brand must NOT be labelled a scam.", AMBER),
]
yy = 1.95
for num, txt, col in steps:
    c = box(s, 0.6, yy, 0.5, 0.5, fill=PANEL, line=BLUE, line_w=1.5, shape=MSO_SHAPE.OVAL)
    tf = c.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = num; r.font.size = Pt(15); r.font.bold = True; r.font.color.rgb = BLUE
    text(s, 1.3, yy-0.02, 11.4, 0.9, txt, size=14, color=col, anchor=MSO_ANCHOR.MIDDLE)
    yy += 0.92
box(s, 0.6, 6.55, 12.15, 0.5, fill=PANEL, line=GREEN, line_w=1.5)
text(s, 0.8, 6.62, 12, 0.4,
     "Why it matters: it argued with itself on the record, changed its mind on evidence, and drew a "
     "clean line around the innocent business. Every step is in the audit log.",
     size=13.5, color=WHITE, bold=True)
footer(s, "Use case 2/2")
notes(s, "If a tool only ever confirms its first guess, you can't trust it. This one argued with "
         "itself on the record, upgraded its conclusion when the evidence justified it, and protected "
         "the innocent business. That discipline is what makes machine-assisted attribution safe to brief.")

# ============================================================ SLIDE 8 — IT 1 (egress)
s = slide(); header(s, "Why IT should approve · 1", "Where the data goes")
text(s, 0.6, 1.9, 12, 0.5, "CONCERN:  data egress / data handling", size=15, color=AMBER, bold=True)
bullets(s, 0.6, 2.5, 12.1, 4.2, [
    [("Runs entirely on the local machine.", 16, WHITE, True), ("  No server, no cloud service, no "
     "account required to operate.", 15, TEXT, False)],
    [("External OSINT only — by design and by scope.", 16, WHITE, True), ("  Never ingests internal/"
     "corporate data; internal-data analysis is explicitly out of scope.", 15, TEXT, False)],
    [("What leaves the machine is only the selector,", 16, WHITE, True), ("  sent to PUBLIC sources "
     "(WHOIS/DNS/CT logs, search engines, public APIs) — the same requests an analyst makes in a browser.",
     15, TEXT, False)],
    [("Results stay on disk.", 16, WHITE, True), ("  investigations/ and the .env key file are "
     "git-ignored — case data and keys are never committed or pushed.", 15, TEXT, False)],
    [("Passive-first OPSEC.", 16, WHITE, True), ("  The active line prefers archived (Wayback) copies "
     "before any live request; generic user-agent; no crawling; proxy seam for attribution control.",
     15, TEXT, False)],
], size=15, gap=11)
box(s, 0.6, 6.55, 12.15, 0.5, fill=PANEL, line=GREEN, line_w=1.5)
text(s, 0.8, 6.62, 12, 0.4, "Net: the tool's network behavior is a subset of normal analyst browsing, "
     "from the local machine, against public sources only.", size=13.5, color=WHITE, bold=True)
footer(s, "IT approval · data egress")
notes(s, "Nothing internal goes in. What goes out is the same public lookups an analyst runs manually. "
         "Results and keys never leave the box and are never committed to git.")

# ============================================================ SLIDE 9 — IT 2 (provenance)
s = slide(); header(s, "Why IT should approve · 2", "Dependency & tool provenance (supply chain)")
bullets(s, 0.6, 1.95, 12.1, 3.3, [
    [("Seven pinned, mainstream open-source packages.", 15.5, WHITE, True), ("  The entire core "
     "dependency list fits on one slide (requirements.txt). No obscure runtime.", 14.5, TEXT, False)],
    [("Declarative tool registry.", 15.5, WHITE, True), ("  Every one of the 58 tools is a small, "
     "readable spec (endpoint + parser) — auditable at a glance; no hidden collection.", 14.5, TEXT, False)],
    [("No bespoke scraping allowed.", 15.5, WHITE, True), ("  Collection goes only through registered, "
     "reviewed tools; the doctrine forbids ad-hoc scripts.", 14.5, TEXT, False)],
    [("Optional extras are opt-in and degrade gracefully.", 15.5, WHITE, True), ("  Fully functional "
     "with zero keys and zero extra installs.", 14.5, TEXT, False)],
    [("MIT-licensed", 15.5, WHITE, True), (" — open for review and download.", 14.5, TEXT, False)],
], size=14.5, gap=9)
box(s, 0.6, 5.35, 12.15, 1.35, fill=PANEL, line=BLUE, line_w=1.5)
text(s, 0.85, 5.5, 11.8, 0.4, "BUILT-IN SAFETY GOVERNANCE (bonus)", size=13, color=BLUE, bold=True)
text(s, 0.85, 5.9, 11.8, 0.8,
     "A health gate (health_check.py) + 3 regression suites gate every change · a capability-lock "
     "defines what must never regress · a separate System Manager role maintains it conservatively.",
     size=14, color=TEXT)
footer(s, "IT approval · provenance")
notes(s, "Everything a supply-chain reviewer wants: short pinned dependency list, every tool is a "
         "readable spec, no hidden network calls, opt-in extras, permissive license, and an automated "
         "gate that proves the system still works after any change.")

# ============================================================ SLIDE 10 — CLOSE
s = slide(); header(s, "Close", "Ready, open, and built to be trusted")
text(s, 0.6, 1.95, 12, 0.4, "WHAT THIS GIVES THE TEAM", size=13, color=GREEN, bold=True)
bullets(s, 0.6, 2.35, 12.1, 1.8, [
    "An analyst force-multiplier: seed → cited, confidence-tiered graph + report, automatically, with a full audit trail",
    "Proven on a real ticket-fraud network — mapped, attributed, and self-corrected without over-claiming",
    "Safe by construction: local · external-only · auditable · honest about limits",
], size=15.5, gap=8)
box(s, 0.6, 4.35, 12.15, 1.5, fill=PANEL, line=BLUE, line_w=1.5)
text(s, 0.85, 4.5, 11.8, 1.3, [
    [("AVAILABLE NOW", 13, BLUE, True)],
    [("Open-source (MIT):  github.com/cis379/osint-investigator-v3  (public)", 15, TEXT, False)],
    [("One command to stand up (./bootstrap.sh), health-gated, Mac / Linux / Windows · "
      "drive it with Claude Code or Codex", 14.5, TEXT, False)],
], space=5)
text(s, 0.6, 6.1, 12, 0.7, [
    [("THE ASK:  ", 18, AMBER, True),
     ("approval to run it locally, external-OSINT only, as an analyst tool.", 18, WHITE, True)],
])
footer(s, "Close")
notes(s, "It's ready, it's open, and it's built to be trusted. I'm asking for the green light to use "
         "it as a local analyst tool — and I'm happy to walk IT through the code and the audit trail.")

out = os.path.join(os.path.dirname(__file__), "osint-brief.pptx")
prs.save(out)
print("WROTE", out, "-", len(prs.slides._sldIdLst), "slides")
