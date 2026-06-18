# Baseline Test — Golden Results & Comparison Log

**Directive:** Every time we run the three standing baseline cases, compare V3's
output against the **V1 golden results** below. V1 is the bar. A V3 run that finds
materially less than V1 is a regression in *capability* (even if the pipeline is
"green"). Record each run's delta here.

The three standing cases (run each iteration):

| Case | Seed | Type | V1 golden case |
|------|------|------|----------------|
| domain | `example.com` | domain | (control / plumbing) |
| name | `Robin Grieff` | name | `~/osint-investigator/investigations/INV-20260519-003` |
| username | `allthespills` | username (Instagram) | `~/osint-investigator/investigations/INV-20260519-002` |

---

## V1 GOLDEN RESULTS (the bar to match)

### Robin Grieff (V1 INV-20260519-003) — 44 entities, 42 relationships
Resolved the **real person**: NY-admitted attorney (2020, Reg #5764840), Director of
D.C. Career Services at **ASU Sandra Day O'Connor College of Law**; **Cornell Law JD**
(2019), Binghamton BA (2013). Found 2 emails (rgrieff@asu.edu, rgrieff@gmail.com),
3 phones, home address (462 Claybourne Rd, Rochester NY), DOB (1991-03-28), family
network (Marvin D. Grieff MD, Brianna Grieff), 13+ platform accounts, full geographic
progression. **The "law connection" and nearly all identity detail came from
`Web Search` + public records (Clustrmaps, Spokeo, LocatePeople, FindLaw, OpenGovNY,
LinkedIn).** Tools list explicitly includes "Web Search (multiple queries)."

### allthespills (V1 INV-20260519-002) — 10 entities, 8 relationships
Resolved to **Charles "Charley" Smith** — US Army 2nd Ranger Battalion, US Cyber
Command, former Twitter 1.0 Trust & Safety, probable JHU Applied Physics Lab.
Confirmed Bluesky / Threads / Instagram accounts. **The entire identity came from
`WebSearch` + `WebFetch` of the profile pages + Bluesky API** — sherlock/maigret only
ever produced the namespace hits.

---

## V3 RUN LOG

### 2026-06-18 — first live agent runs (commit de6fd0b era)
Pipeline: PASS end-to-end both cases (raw/analysis split held; supervisor re-tiered
the tool wrappers' blanket "confirmed"). **Intelligence yield: FAR below V1.**

| Case | V3 result | vs V1 |
|------|-----------|-------|
| Robin Grieff (INV-20260618-003) | 17 entities, 1 confirmed (seed only), 0 attribution. Wikipedia hits = false positives; pivot to username `robing` = generic, no attribution. | **MISSED the entire law connection** — no ASU, no Cornell, no attorney record, no family, no emails/phones/address. |
| allthespills (INV-20260618-002) | 58 entities, 1 confirmed (seed only), Instagram **unverifiable**. 57 namespace hits re-tiered to 12 probable / 45 possible. | **MISSED the Charles Smith identity entirely** — no name, no military/Cyber Command/Twitter T&S, no Instagram confirmation. |

**Root cause (decisive): V3 has no wired web-search or profile-fetch tool.** V1's
richness was the agent browsing the open web ad hoc and reading profile/record pages —
never a repeatable, logged tool. V3 (a copy of V1's *code*) only has
`google_dork_generator`, which emits dork **strings** and executes/fetches/logs
**nothing**. sherlock/maigret are username-existence enumerators, not search.

**Conclusion that drives the roadmap:** web search + URL/profile content fetch must be
wired as first-class, logged collectors at the ontology level. This is the #1 gap
between V3 and V1's actual output, proven by direct comparison — not a theory.

---

## How to compare (each future run)
1. Run `python tests/replay_baseline.py` (plumbing must stay green).
2. Run the live supervisor agents on the 3 seeds.
3. For name + username, diff the live result against the V1 golden summary above:
   did we recover the law connection (Robin) / the Charles Smith identity (allthespills)?
4. Append a dated row to the V3 RUN LOG with the entity counts and the V1 delta.
