# Data Isolation, API Budget & Deployment Posture

*Baseline 2026-06-12. Answers three operational questions: (1) what "separate, 100%-controlled platform_analyst" means concretely, (2) the API-budget posture, (3) GitHub storage + pull-down-and-run portability. Companion to [tool-a-architecture.md](tool-a-architecture.md).*

---

## 1. The three-tool split and why C is isolated

| Tool | Data it touches | Sensitivity | Isolation |
|---|---|---|---|
| **A — OSINT investigator** | Public / external OSINT | Low–moderate | Standard |
| **B — AI-threat CTI** | Public feeds, vendor reports, newsletters | Low | Standard |
| **C — platform_analyst** | **Internal platform data**: user PII, prompts/generations, account records, IPs, sessions, devices | **High / regulated** | **Fully isolated, 100% your control** |

`platform_analyst` was a *skill inside Tool A*; it's now **Tool C, a separate system.** Internal platform data is the most sensitive and legally-governed data you'll touch, so it must never share a runtime, store, or egress path with the external tools.

### What "100% control for data privacy" means — concretely

1. **Separate everything.** Tool C has its **own private repo, its own Postgres instance, its own object store, its own runtime host, and its own credentials.** It never shares a database, schema, or storage bucket with Tools A/B. Internal data lives only in Tool C's store, on infrastructure you control.

2. **No external egress of internal data — ever.** Tool C's collectors do **not** call public OSINT APIs or any third-party service with internal data. **This includes the LLM:** the analyst model that reads internal prompts must run against an **approved zero-/no-retention endpoint** (your foundational AI access — an enterprise/Bedrock/Vertex/zero-retention Anthropic endpoint), **never a consumer API that retains data.** This is the single easiest rule to violate and the most important to get right.

3. **Interoperability via a one-way, minimized, human-gated export boundary — not a shared DB.** When an internal finding needs external enrichment (you surfaced a suspicious email/IP and want OSINT on it), Tool C exports **only the minimal selector(s)** — never raw internal records — as a STIX/FtM bundle that **you review before it crosses into Tool A.** Direction matters: internal→external is minimized + gated; external enrichment attaches to the case in Tool A, and only a deliberate, reviewed summary flows back to C. The seam is effectively an air-gap with a human checkpoint, realized through the shared interchange format. This is how you get "interoperable **and** separate."

4. **Data minimization, pseudonymization, retention.** Tokenize/hash internal IDs where feasible; store only what the investigation needs; enforce retention/deletion windows per employer policy; purpose-limit.

5. **Access control + full audit.** RBAC (only you / authorized analysts); append-only, Postgres-backed audit of every internal query (who, what, when, why) — queryable for compliance.

6. **Governance alignment.** Tool C is designed to sit inside your employer's data-handling policy (GDPR/CCPA, internal privacy/legal rules, lawful basis, purpose limitation). The `platform_analyst.md` "assumed schema" stays an **illustrative design stand-in** until you have real access — we design the *interfaces*, not against real data.

7. **Repo privacy.** Tool C's repo is **private** and must never contain real internal schemas, sensitive table/column names, data samples, or credentials — only the illustrative assumed schema, with `.env` + secrets manager + `.gitignore`. (Tools A/B may be public if you choose; **C is private, always.**)

**What it does *not* mean:** C isn't crippled in isolation — it runs the coordination/cluster-hunting SQL internally (shared-IP/payment/device/session pivots, the `platform_analyst` playbook) and produces leads. It simply hands *minimized* selectors outward under your control.

---

## 2. API budget posture

Wide latitude, but controlled — you'll *see* spend, not be throttled by stinginess. Foundational AI access means LLM calls are generous; still bounded for safety.

### Source tiers (provisioning guidance)
- **Tier 1 — free, always-on** (no budget concern): crt.sh, CertSpotter, DoH DNS, RDAP, Wayback, HackerTarget, abuse.ch (ThreatFox/URLhaus/MalwareBazaar), AlienVault OTX, GreyNoise community, IPinfo/ip-api, Maigret/Sherlock/WhatsMyName/Naminter/Linkook, OpenSanctions, Wikidata, Nominatim/Overpass, blockchain explorers.
- **Tier 2 — provisioned paid, budget OK** (provision freely): Shodan, Censys, SecurityTrails, Netlas, Criminal IP, VirusTotal, HIBP, OSINT Industries (flagship pivot API), Epieos, **Spur.us** (proxy/VPN attribution — essential), Arkham, Breadcrumbs, GeoSpy, urlscan Pro, Sentinel Hub, Twilio Lookup.
- **Tier 3 — premium, per-need with explicit opt-in** (confirm before each costly run): Intelligence X, Pipl, PimEyes, Crystal, FOFA/ZoomEye/Quake, Predicta/UserSearch.

### Controls (cost-awareness, not rationing)
- **Response caching keyed on `(selector, source)`** — never re-query the same thing; the biggest single cost saver (estorides does this — port it).
- **Per-source rate limiting + monthly-credit tracking** so you don't blow a plan's quota unawares.
- **Per-investigation cost telemetry + a soft ceiling with one-click override** — you see spend accrue; the system warns, it doesn't block.
- **Tier-3 sources require explicit per-use confirmation.**
- **Key isolation; keys from env/secrets manager; never logged, never in evidence `request_params`.**
- **LLM:** prompt-caching + bounded context + a per-case token budget shown in telemetry. For **Tool C**, the endpoint MUST be the compliant zero-retention one (§1.2).

---

## 3. GitHub storage + pull-down-and-run deployment

You keep code on GitHub and deploy by pulling down onto a VM. Design for that from the start.

### What lives in git vs not
- **In git:** code, config *templates* (`.env.example`), the declarative source-definition YAMLs, DB migrations, `docker-compose.yml`, docs.
- **Never in git** (`.gitignore`): `.env` / secrets, the artifact vault, `investigations/` case data, any internal data (Tool C), API keys. Content-addressed artifacts live in object storage, not the repo.
- **Repo visibility:** A & B may be public; **C private, always.**

### Easy pull-down-and-run on a VM (the requirement)
Target a **Linux VM** (you build on Windows now; deploy to a server later). Make startup one command via containers:

- **`docker-compose.yml`** brings up **Postgres + MinIO + the app** together. Migrations auto-run on boot.
- **`.env.example`** lists every required/optional API key with a link to where each is obtained; copy to `.env`, fill, go.
- **One-command bootstrap** (`make up` or `./install.sh`): clone → `cp .env.example .env` → `docker compose up`. Done.
- **Pinned dependencies** (lockfile / pinned `requirements.txt`) so a fresh VM reproduces the build.
- **Storage is config, not code:** `DATABASE_URL` + S3 endpoint are env vars. Local = MinIO; server = managed Postgres + S3 — the same compose file, no code change. This is exactly what makes "local now, server later" free.
- **Health checks + a smoke test** (`_validate.py`-style) so a fresh deploy self-verifies.

estorides already models this ergonomics well (`install.sh`, `.env.example`, `pyproject.toml`, `_validate.py`) — port the deployment pattern along with the code patterns. Each of the three tools ships its own compose stack so they deploy independently (and C deploys to its own isolated host).
