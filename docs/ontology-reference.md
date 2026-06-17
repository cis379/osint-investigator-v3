# OSINT Investigation Ontology Reference

This document describes the selector-tool ontology that powers the OSINT Investigator system. The ontology defines **what data types exist** (selectors), **what tools can process them**, and **what new selectors each tool produces** -- enabling automated pivot chains through investigation graphs.

---

## Table of Contents

1. [Overview](#overview)
2. [Selector Types](#selector-types)
3. [Automated Tools](#automated-tools)
4. [Pivot Chains](#pivot-chains)
5. [Ontology Statistics](#ontology-statistics)
6. [Extending the Ontology](#extending-the-ontology)

---

## Overview

The ontology is a directed graph that maps **selectors** (data types like email addresses, domains, usernames) through **tools** (OSINT data sources) to produce **new selectors**. This creates a traversable investigation space where each finding opens new avenues of inquiry.

### Core Concepts

| Concept | Definition |
|---------|-----------|
| **Selector** | A typed piece of investigative data (e.g., an email address, IP, username) |
| **Selector Type** | The classification of a selector (e.g., `email`, `ip_v4`, `domain`) |
| **Tool** | An OSINT data source that accepts one or more selector types as input |
| **Yield** | A new selector type produced by a tool's output |
| **Pivot** | The act of taking a tool's output and feeding it into another tool |
| **Pivot Chain** | A sequence of selector-to-tool-to-selector transitions forming an investigation path |

### How It Works

```
Selector (email) --> Tool (holehe) --> New Selectors (domains where registered)
                                            |
                                            v
                                  Tool (whois_lookup) --> New Selectors (registrant name, IP)
                                                                |
                                                                v
                                                      Tool (sherlock) --> Profile URLs
```

The system:
1. Detects the type of a seed selector (e.g., `john.doe@gmail.com` is type `email`)
2. Looks up all tools that accept `email` in the pivot map
3. Runs applicable automated tools, collecting structured results
4. Extracts new selectors from the output (domains, usernames, IPs, etc.)
5. Repeats the process for each new selector, building an investigation graph

### Data Files

| File | Purpose |
|------|---------|
| `src/ontology/selector_types.json` | Defines all 114 selector types with categories and yield mappings |
| `src/ontology/tools_registry.json` | Catalog of all 1,031 OSINT tools with metadata |
| `src/ontology/pivot_map.json` | Maps each selector type to its applicable tools and expected yields |

---

## Selector Types

The system recognizes 114 distinct selector types organized into categories. Each type defines what tools can consume it and what new types those tools produce.

### Identity Selectors

These represent people, accounts, and digital identities.

| Selector Type | Description | Tools | Key Yields |
|--------------|-------------|-------|------------|
| `username` | Social media or platform username | 189 | url, email, name, profiles, social_accounts, posts, connections |
| `email` | Email address | 58 | breaches, name, phone, social_accounts, domain, profiles, username |
| `name` | Real name or alias | 58 | email, phone, social_accounts, username, domain, company, profiles |
| `phone` | Phone number | 44 | name, email, carrier, location, social_accounts, telegram_handle |
| `company` | Company or organization name | 31 | domain, email, employees, phone, profiles, shipping_data |
| `telegram_handle` | Telegram username | 12 | phone, name, channels, messages, groups, profiles |
| `facebook_id` | Facebook numeric user ID | 2 | name, friends, social_accounts, username |
| `discord_id` | Discord user/server ID | 2 | messages, profiles, servers, chat_data |
| `youtube_channel_id` | YouTube channel ID | 3 | analytics, videos, comments, playlists, transcript |
| `pgp_key` | PGP/GPG key fingerprint or ID | 0 | -- |
| `linkedin_url` | LinkedIn profile URL | 0 | -- |
| `instagram_handle` | Instagram handle | 0 | -- |
| `twitter_id` | Twitter/X numeric user ID | 0 | -- |
| `reddit_username` | Reddit username | 0 | -- |
| `github_username` | GitHub username | 0 | -- |
| `mastodon_handle` | Mastodon handle (user@instance) | 0 | -- |
| `slack_workspace` | Slack workspace URL or name | 0 | -- |
| `skype_id` | Skype username | 0 | -- |
| `steam_id` | Steam profile ID or vanity URL | 0 | -- |
| `spotify_user` | Spotify username | 0 | -- |
| `twitch_handle` | Twitch username | 0 | -- |
| `tiktok_handle` | TikTok username | 0 | -- |
| `snapchat_handle` | Snapchat username | 0 | -- |
| `xbox_gamertag` | Xbox gamertag | 0 | -- |
| `vk_id` | VK (VKontakte) user ID | 0 | -- |
| `onlyfans_handle` | OnlyFans username | 0 | -- |
| `whatsapp_number` | WhatsApp phone number | 0 | -- |
| `minecraft_username` | Minecraft username | 0 | -- |

> Selector types with 0 tools are recognized by the type detector but rely on the generic `username` tools (Sherlock, Maigret) or manual investigation. They serve as output types yielded by other tools.

### Infrastructure Selectors

These represent network and web infrastructure.

| Selector Type | Description | Tools | Key Yields |
|--------------|-------------|-------|------------|
| `url` | Full URL | 145 | domain, email, ip_v4, metadata, images, profiles, username |
| `domain` | Domain name | 70 | ip_v4, dns, whois, subdomains, certificates, email, technologies |
| `ip_v4` | IPv4 address | 29 | domain, geolocation, asn, ports, services, whois, vulnerabilities |
| `ip_v6` | IPv6 address | 7 | asn, domain, geolocation, services, threat_report |
| `bssid` | WiFi access point MAC (BSSID) | 3 | coordinates, email, location, name, phone |
| `certificate` | SSL/TLS certificate hash or serial | 1 | domain, ip_v4, port |
| `ssid` | WiFi network SSID name | 1 | coordinates |
| `mac_address` | Network MAC address | 1 | company |
| `asn` | Autonomous System Number | 1 | carrier, geolocation |
| `favicon_hash` | Website favicon hash | 0 | -- |

### Financial Selectors

These represent cryptocurrency and financial identifiers.

| Selector Type | Description | Tools | Key Yields |
|--------------|-------------|-------|------------|
| `crypto_btc` | Bitcoin wallet address | 13 | transactions, addresses, balances, connections, visualizations |
| `crypto_eth` | Ethereum wallet address | 7 | transactions, tokens, contracts, connections, balances |
| `nft_token` | NFT token ID or collection | 3 | nft_data |
| `crypto_wallet` | Generic cryptocurrency wallet | 0 | -- |
| `crypto_tx` | Cryptocurrency transaction hash | 0 | -- |

### Malware & Threat Selectors

These represent file hashes and threat indicators.

| Selector Type | Description | Tools | Key Yields |
|--------------|-------------|-------|------------|
| `hash_md5` | MD5 file hash | 8 | malware_analysis, domain, ip_v4, password |
| `hash_sha256` | SHA256 file hash | 6 | malware_analysis, domain, ip_v4, password |
| `hash_sha1` | SHA1 file hash | 4 | malware_analysis, domain, ip_v4, password |

### Security Selectors

| Selector Type | Description | Tools | Key Yields |
|--------------|-------------|-------|------------|
| `password` | Password or hash for breach search | 2 | breaches, domain, email, username |
| `cve_id` | CVE vulnerability identifier | 0 | -- |

### Media Selectors

These represent files and media content for analysis.

| Selector Type | Description | Tools | Key Yields |
|--------------|-------------|-------|------------|
| `image` | Image file or URL for reverse search | 25 | geolocation, exif, profiles, similar_images, social_accounts |
| `youtube_video_id` | YouTube video ID | 5 | transcript, comments, metadata, geolocation |
| `document` | Document file for analysis | 3 | text, url |
| `audio_file` | Audio file for analysis | 2 | transcript |
| `video_file` | Video file for analysis | 0 | -- |

### Social Selectors

| Selector Type | Description | Tools | Key Yields |
|--------------|-------------|-------|------------|
| `hashtag` | Social media hashtag | 15 | posts, trends, sentiment, profiles, analytics |
| `subreddit` | Reddit subreddit name | 7 | posts, comments, trends, analytics |

### Geospatial Selectors

| Selector Type | Description | Tools | Key Yields |
|--------------|-------------|-------|------------|
| `coordinates` | Lat/lon coordinate pair | 151 | map_data, social_media_posts, tweet_data, vessel_data, flight_data |
| `geolocation` | GPS coordinates or location | 15 | profiles, social_media_posts, trends, username, visualizations |
| `property_address` | Physical/real estate address | 4 | name, email, phone, location, map_data |

### Transport Selectors

| Selector Type | Description | Tools | Key Yields |
|--------------|-------------|-------|------------|
| `flight_number` | Flight number (e.g., AA123) | 7 | flight_data, map_data, incident_report |
| `vessel_name` | Ship/vessel name | 3 | vessel_data, shipping_data, map_data |
| `license_plate` | Vehicle license/number plate | 3 | vehicle_data, name, email, phone |
| `vessel_mmsi` | Ship MMSI or IMO number | 1 | vessel_data |
| `vin` | Vehicle Identification Number | 1 | name, email, phone |

### Device Selectors

| Selector Type | Description | Tools | Key Yields |
|--------------|-------------|-------|------------|
| `imei` | Mobile device IMEI number | 7 | device_data, location, manufacturer, warranty |

### Search Selectors

| Selector Type | Description | Tools | Key Yields |
|--------------|-------------|-------|------------|
| `keyword` | Search keyword or phrase | 326 | url, domain, profiles, posts, email, images, social_accounts |

### Other / Auto-Discovered Selectors

These types were auto-discovered from tool definitions and assigned to the `unknown` category. They typically serve as intermediate or specialized data types.

| Selector Type | Description | Tools | Key Yields |
|--------------|-------------|-------|------------|
| `location` | Location string | 8 | ip_data, url, email, name, phone |
| `code` | Source code snippet | 10 | code, text |
| `text` | Text content | 6 | audio, image, text, url, video |
| `date` | Date/time value | 5 | history, trends, url, repositories |
| `file` | Generic file | 3 | exif, metadata, malware_analysis |
| `email_header` | Email header data | 3 | email, ip_v4, metadata, routing |
| `serial_number` | Device serial number | 3 | device_data, product, warranty |
| `container_number` | Shipping container number | 3 | shipping_data |
| `device_model` | Device model identifier | 3 | ip_v4, password, username |
| `warc_file` | Web archive file | 3 | file, metadata, url |
| `cell_tower_id` | Cell tower identifier | 2 | coordinates, map_data |
| `lei` / `lei_number` | Legal Entity Identifier | 2 | company |
| `whatsapp_export` | WhatsApp chat export | 2 | chat_data |
| `gpx_file` | GPS exchange file | 2 | map_data |
| `doi` | Digital Object Identifier | 2 | document, url |
| `app_id` | Application identifier | 2 | metadata, url |
| `api_key` | API key or token | 2 | credentials, url |
| `artist_name` | Music artist name | 2 | streaming_stats, analytics |
| `video` | Video content | 2 | video |
| `credential` | Login credential | 1 | breach_data |
| `telegram_export` | Telegram chat export | 1 | chat_data |
| `google_dork` | Google dork query | 1 | url |
| `eml_file` | Email .eml file | 1 | email, metadata, threat_report |
| `twitter_archive` | Twitter data archive | 1 | tweets, media |
| `mbox_file` | Mailbox file | 1 | email, url |
| `har_file` | HTTP archive file | 1 | warc_file |
| `slack_token` | Slack API token | 1 | chat_data, credentials, messages |
| `iban` | International Bank Account Number | 1 | company |
| `bin` / `bin_number` | Bank Identification Number | 1 | company |
| `credit_card_number` | Credit card number | 1 | company |
| `bank_identifier` | Bank identifier | 1 | company |
| `fdic_cert` | FDIC certificate number | 1 | company |
| `barcode` | Product barcode | 1 | company, product |
| `hs_code` | Harmonized System code | 1 | company, shipping_data |
| `fcc_id` | FCC device identifier | 1 | company, device_data |
| `asin` | Amazon Standard Identification Number | 1 | keyword |
| `document_id` | Document identifier | 1 | name, location |
| `national_id` | National ID number | 1 | name, location |
| `ssn` | Social Security Number | 1 | name, location |
| `group_id` | Group identifier | 1 | profiles, username |
| `node_id` | Network node ID | 1 | profiles, sysop_info |
| `token_id` | Token identifier | 1 | nft_data |
| `snapchat_id` / `snapchat_bitmoji_id` | Snapchat identifiers | 1 | avatars, images |
| `http_status_code` | HTTP status code | 1 | image |
| `regex` | Regular expression | 1 | transcript, subtitles |
| `voyage_number` | Shipping voyage number | 1 | shipping_data |

---

## Automated Tools

Of the 1,031 tools in the registry, approximately 24 have working Python automation with structured output parsing. These are the tools the system can execute directly without human intervention.

### Domain Tools (`src/tools/domain_tools.py`)

| Tool | Description | Input | Output | Method | Free |
|------|------------|-------|--------|--------|------|
| **whois_lookup** | WHOIS registration data -- registrant name, email, org, registrar, nameservers, dates | `domain` | `name`, `email`, `phone`, `company`, `domain` | Library (`python-whois`) | Yes |
| **dns_lookup** | DNS record enumeration -- A, AAAA, MX, TXT, NS, CNAME, SOA records | `domain` | `ip_v4`, `ip_v6`, `domain` | Library (`dnspython`) | Yes |
| **crtsh** | Certificate Transparency log search via crt.sh -- discovers subdomains and cert metadata | `domain` | `domain`, `email` | API (`crt.sh`) | Yes |
| **wayback** | Wayback Machine historical snapshots -- finds archived versions of pages | `domain`, `url` | `url` | API (`web.archive.org`) | Yes |
| **http_headers** | HTTP header analysis -- server software, security headers, resolved IP | `domain`, `url` | `ip_v4` | Library (`requests`) | Yes |

### IP Tools (`src/tools/ip_tools.py`)

| Tool | Description | Input | Output | Method | Free |
|------|------------|-------|--------|--------|------|
| **ip_geolocation** | Geolocate IP -- city, country, ISP, ASN, coordinates | `ip_v4`, `ip_v6` | `asn`, `company` | API (`ip-api.com`) | Yes |
| **reverse_dns** | Reverse DNS (PTR) lookup for IP addresses | `ip_v4`, `ip_v6` | `domain` | Library (`dnspython`) | Yes |
| **shodan_internetdb** | Shodan InternetDB -- open ports, hostnames, vulns, CPEs (no API key needed) | `ip_v4` | `domain` | API (`internetdb.shodan.io`) | Yes |
| **ipinfo** | IPinfo.io -- geolocation, ASN, company, hostname | `ip_v4`, `ip_v6` | `domain`, `asn`, `company` | API (`ipinfo.io`) | Yes |

### Email Tools (`src/tools/email_tools.py`)

| Tool | Description | Input | Output | Method | Free |
|------|------------|-------|--------|--------|------|
| **holehe** | Check if email is registered on various platforms (site enumeration) | `email` | `url`, `username` | CLI (`holehe`) | Yes |
| **emailrep** | Email reputation score -- suspicious flags, references count, breach history | `email` | (metadata) | API (`emailrep.io`) | Yes |

### Username Tools (`src/tools/username_tools.py`)

| Tool | Description | Input | Output | Method | Free |
|------|------------|-------|--------|--------|------|
| **sherlock** | Hunt usernames across 400+ social networks | `username` | `url` | CLI (`sherlock-project`) | Yes |
| **maigret** | Collect info from 2,500+ sites -- extracts profile URLs, emails, names | `username` | `url`, `email`, `name` | CLI (`maigret`) | Yes |

### Name Tools (`src/tools/name_tools.py`)

| Tool | Description | Input | Output | Method | Free |
|------|------------|-------|--------|--------|------|
| **wikipedia_search** | Search Wikipedia for biographical/organizational information | `name`, `company` | `name`, `url`, `company` | API (`wikipedia.org`) | Yes |
| **wikidata_search** | Search Wikidata for structured data -- occupations, employers, birth dates, citizenship | `name`, `company` | `name`, `url`, `company` | API (`wikidata.org`) | Yes |
| **gravatar_check** | Check Gravatar profiles for email candidates derived from a name | `name`, `email` | `email`, `url`, `username` | API (`gravatar.com`) | Yes |
| **hibp_name_search** | Generate email permutations from a name for breach checking | `name`, `email` | `email`, `url` | API + Generator | Yes |
| **name_to_username** | Generate likely usernames from a real name and check GitHub/GitLab | `name` | `username`, `url` | Library + API | Yes |

### Crypto Tools (`src/tools/crypto_tools.py`)

| Tool | Description | Input | Output | Method | Free |
|------|------------|-------|--------|--------|------|
| **blockchain_btc** | Bitcoin address lookup -- balance, transaction count, connected addresses | `crypto_btc` | `crypto_btc` | API (`blockchain.info`) | Yes |
| **etherscan** | Ethereum address transactions -- counterparty addresses, values | `crypto_eth` | `crypto_eth` | API (`etherscan.io`) | Yes |

### Social / Threat Tools (`src/tools/social_tools.py`)

| Tool | Description | Input | Output | Method | Free |
|------|------------|-------|--------|--------|------|
| **urlscan** | Search urlscan.io for previously scanned pages -- domains, IPs, technologies | `domain`, `url`, `ip_v4` | `url`, `domain`, `ip_v4` | API (`urlscan.io`) | Yes |
| **threatfox** | ThreatFox IOC search -- malware families, threat types, confidence scores | `ip_v4`, `domain`, `hash_md5`, `hash_sha256`, `url` | `ip_v4`, `domain`, `hash_md5`, `hash_sha256` | API (`abuse.ch`) | Yes |
| **google_dork_generator** | Generate Google dork queries tailored to a selector type | `username`, `email`, `domain`, `name`, `phone`, `company`, `telegram_handle` | (dork queries) | Generator | Yes |

---

## Pivot Chains

Pivot chains are the investigation paths the system follows. Each chain starts with a seed selector and branches through tools into new selectors. Below are the most common and productive chains.

### Chain 1: Username Investigation

```
username
  |
  +---> sherlock ---------> profile URLs (400+ sites)
  |                              |
  |                              +---> extract domains ---> whois_lookup ---> registrant name, email
  |                              |                     +--> dns_lookup -----> IPs
  |                              |                     +--> crtsh ----------> subdomains
  |                              |
  |                              +---> extract usernames on new platforms ---> repeat
  |
  +---> maigret ----------> profile URLs (2,500+ sites), emails, names
  |                              |
  |                              +---> holehe (if email found) ---> more platforms
  |                              +---> name_to_username (if name found) ---> GitHub/GitLab profiles
  |
  +---> google_dork_generator --> search queries for manual follow-up
```

**Example:** Starting with username `jdoe42`:
- Sherlock finds profiles on GitHub, Reddit, Twitter, Instagram
- Maigret finds additional profiles and extracts email `jdoe42@gmail.com`
- Holehe confirms the email is registered on Spotify, Adobe, Pinterest
- Name extraction yields "John Doe" which feeds into Wikipedia/Wikidata searches

### Chain 2: Email Investigation

```
email
  |
  +---> holehe ------------> platforms where email is registered (domains)
  |                              |
  |                              +---> extract local part as username
  |                              |        |
  |                              |        +---> sherlock ---> more profile URLs
  |                              |
  |                              +---> domain tools on registration platforms
  |
  +---> emailrep -----------> reputation data, breach indicators
  |
  +---> gravatar_check -----> Gravatar profile, linked accounts, display name
  |                              |
  |                              +---> username extraction ---> sherlock/maigret
  |
  +---> google_dork_generator --> targeted search queries
```

**Example:** Starting with `jane.smith@protonmail.com`:
- Holehe confirms registration on GitHub, Spotify, Twitter
- EmailRep shows low reputation score with 3 breach references
- Gravatar reveals display name "JaneS" and linked GitHub account
- Sherlock runs on "janesmith" and "JaneS" usernames
- Google dorks find the email mentioned in a Pastebin post

### Chain 3: Domain Investigation

```
domain
  |
  +---> whois_lookup -------> registrant name, email, org, registrar, nameservers
  |                              |
  |                              +---> registrant email ---> holehe, emailrep
  |                              +---> registrant name ----> wikipedia, wikidata, name_to_username
  |                              +---> nameservers ---------> shared hosting analysis
  |
  +---> dns_lookup ----------> A records (IPv4), AAAA (IPv6), MX, NS, CNAME
  |                              |
  |                              +---> IP addresses ---------> ip_geolocation, shodan_internetdb
  |                              +---> MX hosts --------------> mail infrastructure analysis
  |
  +---> crtsh ---------------> subdomains from Certificate Transparency
  |                              |
  |                              +---> each subdomain -------> recursive domain investigation
  |
  +---> wayback -------------> historical snapshots (content changes over time)
  |
  +---> http_headers --------> server software, resolved IP, security headers
  |
  +---> urlscan -------------> scan results, associated IPs, technologies
  |
  +---> threatfox -----------> IOC matches if domain is flagged as malicious
```

**Example:** Starting with `suspicious-site.com`:
- WHOIS reveals registrant `Privacy Service` (redacted) but nameservers point to Cloudflare
- DNS returns IP `104.21.x.x` -- geolocation shows Cloudflare CDN
- crt.sh discovers `api.suspicious-site.com`, `admin.suspicious-site.com`, `staging.suspicious-site.com`
- Shodan InternetDB shows port 22 (SSH) and port 8080 open on the origin IP
- ThreatFox flags the domain as associated with a phishing campaign

### Chain 4: Name Investigation

```
name
  |
  +---> wikipedia_search ----> biographical articles, Wikipedia URLs
  |
  +---> wikidata_search -----> structured data: occupations, employers, DOB, citizenship
  |                              |
  |                              +---> employer names ----> company investigation
  |
  +---> gravatar_check ------> Gravatar profiles for generated email permutations
  |                              |
  |                              +---> confirmed emails ---> email investigation chain
  |                              +---> linked accounts ----> username investigation chain
  |
  +---> hibp_name_search ----> generated email candidates for breach checking
  |
  +---> name_to_username ----> generated usernames checked against GitHub/GitLab
  |                              |
  |                              +---> confirmed profiles --> URL extraction, bio analysis
  |                              +---> confirmed usernames -> sherlock/maigret
  |
  +---> google_dork_generator --> LinkedIn, social media, resume/CV searches
```

**Example:** Starting with name `Alex Morgan`:
- Wikipedia finds multiple results (soccer player, actor, etc.) -- supervisor disambiguates
- Wikidata returns structured data with Wikidata QID, occupation, employer
- `name_to_username` generates `alexmorgan`, `alex.morgan`, `amorgan`, etc.
- GitHub API confirms `alexmorgan` exists with matching display name
- Gravatar finds a profile for `alex.morgan@gmail.com` with linked Twitter account

### Chain 5: IP Address Investigation

```
ip_v4
  |
  +---> ip_geolocation ------> country, city, ISP, ASN, coordinates
  |
  +---> reverse_dns ----------> hostname(s) --> domain investigation chain
  |
  +---> shodan_internetdb ----> open ports, hostnames, CVEs, CPEs
  |                              |
  |                              +---> hostnames -----------> domain investigation
  |                              +---> CVEs ----------------> vulnerability research
  |
  +---> ipinfo ---------------> geolocation, ASN name, org, hostname
  |
  +---> urlscan --------------> pages previously scanned from this IP
  |
  +---> threatfox ------------> IOC matches if IP is flagged as malicious
```

### Chain 6: Cryptocurrency Investigation

```
crypto_btc
  |
  +---> blockchain_btc ------> balance, tx count, connected addresses
                                    |
                                    +---> input addresses (who sent funds)
                                    |        |
                                    |        +---> recursive BTC investigation
                                    |
                                    +---> output addresses (who received funds)
                                             |
                                             +---> recursive BTC investigation
```

```
crypto_eth
  |
  +---> etherscan -----------> transaction list, counterparty addresses
                                    |
                                    +---> from/to addresses ---> recursive ETH investigation
```

---

## Ontology Statistics

| Metric | Count |
|--------|-------|
| **Total tools in registry** | 1,031 |
| **Automated tools (with Python wrappers)** | 24 |
| **Selector types defined** | 114 |
| **Selector categories** | 12 (identity, infrastructure, financial, malware, security, media, social, geospatial, transport, device, search, unknown) |

### Selector Types by Category

| Category | Count | Examples |
|----------|-------|---------|
| Identity | 28 | username, email, name, phone, company, telegram_handle |
| Infrastructure | 10 | url, domain, ip_v4, ip_v6, bssid, certificate, ssid, mac_address, asn, favicon_hash |
| Financial | 5 | crypto_btc, crypto_eth, nft_token, crypto_wallet, crypto_tx |
| Malware | 3 | hash_md5, hash_sha256, hash_sha1 |
| Security | 2 | password, cve_id |
| Media | 4 | image, youtube_video_id, audio_file, document, video_file |
| Social | 2 | hashtag, subreddit |
| Geospatial | 3 | coordinates, geolocation, property_address |
| Transport | 5 | flight_number, vessel_name, license_plate, vessel_mmsi, vin |
| Device | 1 | imei |
| Search | 1 | keyword |
| Unknown (auto-discovered) | 50+ | location, code, text, date, file, email_header, etc. |

### Top Selector Types by Tool Coverage

| Rank | Selector Type | Tools Available |
|------|--------------|----------------|
| 1 | `keyword` | 326 |
| 2 | `username` | 189 |
| 3 | `coordinates` | 151 |
| 4 | `url` | 145 |
| 5 | `domain` | 70 |
| 6 | `email` | 58 |
| 7 | `name` | 58 |
| 8 | `phone` | 44 |
| 9 | `company` | 31 |
| 10 | `ip_v4` | 29 |

### Automated Tools by Selector Type

| Selector Type | Automated Tools |
|--------------|----------------|
| `domain` | whois_lookup, dns_lookup, crtsh, wayback, http_headers, urlscan, threatfox, google_dork_generator |
| `ip_v4` | ip_geolocation, reverse_dns, shodan_internetdb, ipinfo, urlscan, threatfox |
| `ip_v6` | ip_geolocation, reverse_dns, ipinfo |
| `email` | holehe, emailrep, gravatar_check, hibp_name_search, google_dork_generator |
| `username` | sherlock, maigret, google_dork_generator |
| `name` | wikipedia_search, wikidata_search, gravatar_check, hibp_name_search, name_to_username, google_dork_generator |
| `company` | wikipedia_search, wikidata_search, google_dork_generator |
| `url` | wayback, http_headers, urlscan, threatfox |
| `crypto_btc` | blockchain_btc |
| `crypto_eth` | etherscan |
| `hash_md5` | threatfox |
| `hash_sha256` | threatfox |
| `phone` | google_dork_generator |
| `telegram_handle` | google_dork_generator |

---

## Extending the Ontology

### Adding a New Automated Tool

1. **Create the wrapper** in the appropriate file under `src/tools/` (or create a new file):

```python
from .base import BaseTool, ToolResult, EntityFound

class MyNewTool(BaseTool):
    name = "my_new_tool"                    # Unique tool ID
    description = "What this tool does"
    input_types = ["domain", "ip_v4"]       # What selector types it accepts
    output_types = ["email", "name"]        # What selector types it produces
    method = "api"                          # "api", "cli", "library", or "generator"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        # Run the tool and collect results
        entities = []
        
        # For each finding, create an EntityFound:
        entities.append(EntityFound(
            value="found@email.com",
            entity_type="email",
            confidence="confirmed",       # "confirmed", "probable", or "possible"
            source_citation="Tool output line that proves this",
            metadata={"extra": "data"},   # Optional structured metadata
        ))
        
        return self.make_result(
            selector, selector_type,
            raw_output="Full tool output text",
            entities=entities,
            success=True,
        )

# Register the tool
TOOLS = [MyNewTool()]
```

2. **Add to `pivot_map.json`** under each input selector type:

```json
{
  "pivot_map": {
    "domain": {
      "tools": ["...", "my_new_tool"],
      "yields": ["...", "email", "name"]
    }
  }
}
```

3. **Add to `tools_registry.json`** for the catalog:

```json
{
  "id": "my_new_tool",
  "name": "My New Tool",
  "category": "domain_osint",
  "description": "What this tool does",
  "input_types": ["domain", "ip_v4"],
  "output_types": ["email", "name"],
  "method": "api",
  "reliability": "high",
  "free": true
}
```

4. **Update `selector_types.json`** if the tool introduces new selector types or changes yield mappings.

### Adding a New Selector Type

1. Add the type definition to `selector_types.json`:

```json
{
  "my_new_type": {
    "description": "What this type represents",
    "category": "infrastructure",
    "tool_count": 0,
    "yields_to": []
  }
}
```

2. Add detection logic to `src/core/selector.py` so the system can auto-detect the type from raw input.

3. Add a pivot map entry in `pivot_map.json` once tools exist for the type.

### Design Principles for New Tools

- **Structured output**: Every tool must return `ToolResult` with typed `EntityFound` objects
- **Confidence levels**: Use `confirmed` for direct evidence, `probable` for strong inference, `possible` for speculation
- **Source citations**: Every entity must cite the exact tool output that proves it exists
- **Error handling**: Return `success=False` with an error message rather than raising exceptions
- **Rate limiting**: Respect API rate limits; add delays if needed
- **Free preference**: Prefer free tools and APIs; clearly document when a tool requires payment
- **Raw output**: Always capture the raw tool output for the investigation audit log
