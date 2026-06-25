# Manual guide — reverse-lookup a tracker / analytics ID

**When to use:** the investigation extracted a tracker ID (e.g. `UA-12345678-1`, a GA4 `G-…`,
AdSense `ca-pub-…`, a Meta Pixel, a Salesforce org ID) from a site's source, and you want to find
**other domains that embed the SAME id** — because a shared tracker ID is an *independent
corroborator of common ownership* (it links sites that merely sharing a host cannot). Use this when
the automated `tracker_reverse` tool reports it was blocked, rate-limited, or has no API key.

## What you're proving
- **Shared GA property (`UA-…` / GA4 `G-…`), AdSense `ca-pub-…`, Yandex counter, or Matomo idsite+host
  = STRONG** common-owner signal (these tie to one account / one payee).
- **GTM container, Meta Pixel, Hotjar, Clarity, TikTok = MEDIUM** (can be shared by an agency or a
  reused template — a lead, not proof).
- **reCAPTCHA site key = WEAK** (copied/leaked freely — don't merge on it).
Always feed the result back: *if* the same strong ID appears on another site, tell the supervisor —
that's the corroborator that can upgrade a `co_hosted_with` link to `same_operator_as`.

## Free / low-cost sources (try these first)
1. **PublicWWW** — https://publicwww.com/ — source-code search; works for ANY id kind.
   Search the raw id in quotes: `"UA-12345678"` or `"ca-pub-1234567890123456"`. Free results are
   limited to top-ranked sites; full coverage + API are paid. Best general-purpose reverser.
2. **SpyOnWeb** — https://spyonweb.com/ — reverses GA (UA), AdSense, IP, DNS. Free API key gives a
   modest monthly quota (set `SPYONWEB_API_KEY` to let `tracker_reverse` use it automatically). The
   site is intermittently down — retry later if it fails.
3. **DNSlytics Reverse Analytics** — https://dnslytics.com/reverse-analytics/ — GA (UA + Google tag)
   and AdSense reverse; limited free web lookups, API is paid.
4. **HackerTarget** — https://hackertarget.com/reverse-analytics-search/ — reverse GA (UA); low free
   quota then keyed.
5. **osint.sh / "Reverse Google Analytics"** — free web, GA only, manual.

## Paid / deeper (operator judgment)
- **BuiltWith "Relationships"** report — https://builtwith.com/relationships/ — explicitly an
  ownership-relationship view across GA/AdSense/Pixel; the good data is paid.
- **NerdyData** — https://www.nerdydata.com/ — source-code search like PublicWWW; paid.

## Favicon pivot (separate path)
If the investigation produced a **favicon hash**, it pivots in **Shodan** (`http.favicon.hash:<hash>`)
or **FOFA** (`icon_hash="<hash>"`) to find hosts serving the same icon (same template/operator). Both
need an account; Shodan's free tier is small.

## How to read results
- A handful of unrelated domains sharing a *medium/weak* id → probably an agency/template; note it,
  don't merge.
- Two or more lookalike/suspect domains sharing a *strong* id (GA property / AdSense payee) → a real
  common-owner corroborator. Bring the exact id + the list of domains back to the supervisor.
