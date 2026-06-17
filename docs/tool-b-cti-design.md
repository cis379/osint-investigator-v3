# Tool B — AI-Threat CTI: Design Notes

*Baseline 2026-06-12. Captures the user's framing and the storage/search architecture. Build order: after Tool A. A deep CTI-source investigation is the research task that precedes the build.*

## Mental model: a very, very enhanced news aggregator

Tool B's primary product is a **readable, searchable, tagged feed of threat reporting** — not a STIX firehose. The user explicitly does not want an endless stream of unusable structured data. So:

**Principle: documents-first, structured-data-on-promotion.**
- **Ingest** every item as a first-class **Document**: source, title, URL, published date, author, full text, and a hash-stamped raw capture (object store).
- **Classify**: the six AI-misuse buckets (cyber ops · influence ops · deepfakes/impersonation · fraud/scams · CSAM · prompt-injection abuse) + a relevance score + the "how adversaries use AI" theme filter.
- **Tag**: actors, techniques (DISARM/ATLAS where relevant), free-text topics.
- **Promote selectively**: structured extraction (IOCs, TTPs, STIX objects) runs **only when an item is relevant enough to promote** — not on every item.
- **STIX is an export, not the substrate.** Emit STIX/MISP only for items worth sharing downstream. This is what prevents the "endless unusable STIX stream."

The CLI agent is how you consume it: "what's new this month on AI-enabled influence ops?" → the agent searches the corpus and summarizes with citations.

## Storage + search (easy reference + searching)

Keep it all in Postgres for a lean stack:
- **Document corpus** in Postgres — every ingested item, deduped.
- **Full-text search** (`tsvector`) for keyword + filters (date / source / bucket / tag) — the news-aggregator baseline, no extra infra.
- **Semantic/vector search** (`pgvector`, embeddings in the *same* Postgres) for concept retrieval ("reporting *about* X") and to power agent RAG. Keeps us off a separate vector DB.
- **Raw captures** in object storage, content-hashed (SHA-256), always retrievable + citable.
- **Human verification gate** before anything promoted item becomes a "finished" intelligence product (LLMs still err on real-world threat research).

## Ingestion sources (to be finalized by the deep CTI-source investigation)
- **Feeds/RSS:** Risky Business / Risky Bulletin (`risky.biz/feeds/risky-business-news`), tl;dr sec, Detection Engineering Weekly, SANS ISC, Daniel Miessler.
- **Email-only newsletters:** dedicated IMAP inbox → parse (RSS where possible, else LLM-extract HTML body).
- **Vendor misuse reports (scrape — the richest raw material):** Anthropic, OpenAI, Google GTIG/Mandiant, Microsoft MSTIC, Recorded Future.
- **Free CTI feeds (selective, for promoted items):** abuse.ch, OTX, CISA KEV, Pulsedive — pulled on demand, not firehosed into the reader.
- **Knowledge anchors:** MITRE ATLAS (consume `atlas-data` / OpenCTI bundles), OWASP LLM Top 10, AI Incident DB.

## Shared with Tool D
The same Document corpus + ingestion substrate feeds **Tool D** (Capability/Ontology Curator). B extracts *intelligence about adversary AI use*; D extracts *new sources/tools/techniques to upgrade the system*. One ingestion layer, two extractors, two consumers.

## Optional heavier core
If structured-CTI volume ever justifies it, stand up **OpenCTI** as a system-of-record behind the promoted/structured layer (it ships ATLAS + ATT&CK bundles and a TAXII server). But the *reader* stays the primary surface; OpenCTI would sit behind the promotion step, not in front of the user.
