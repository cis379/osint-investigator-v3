"""
Merge extracted tool research files and rebuild the ontology.
Run after all extraction agents complete.
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(r"C:\Users\cis37\osint-investigator-v3")
DOCS_DIR = BASE_DIR / "docs"
ONTOLOGY_DIR = BASE_DIR / "src" / "ontology"

# Standard selector types (existing + new)
SELECTOR_TYPE_DEFINITIONS = {
    # Original types
    "username": {"description": "Social media or platform username/handle", "category": "identity"},
    "email": {"description": "Email address", "category": "identity"},
    "domain": {"description": "Domain name", "category": "infrastructure"},
    "ip_v4": {"description": "IPv4 address", "category": "infrastructure"},
    "ip_v6": {"description": "IPv6 address", "category": "infrastructure"},
    "phone": {"description": "Phone number", "category": "identity"},
    "crypto_btc": {"description": "Bitcoin wallet address", "category": "financial"},
    "crypto_eth": {"description": "Ethereum wallet address", "category": "financial"},
    "url": {"description": "Full URL", "category": "infrastructure"},
    "hash_md5": {"description": "MD5 file hash", "category": "malware"},
    "hash_sha1": {"description": "SHA1 file hash", "category": "malware"},
    "hash_sha256": {"description": "SHA256 file hash", "category": "malware"},
    "telegram_handle": {"description": "Telegram username", "category": "identity"},
    "discord_id": {"description": "Discord user/server ID", "category": "identity"},
    "name": {"description": "Real name or alias", "category": "identity"},
    "asn": {"description": "Autonomous System Number", "category": "infrastructure"},
    "company": {"description": "Company or organization name", "category": "identity"},
    # New types from research
    "image": {"description": "Image file or URL for reverse search", "category": "media"},
    "keyword": {"description": "Search keyword or phrase", "category": "search"},
    "hashtag": {"description": "Social media hashtag", "category": "social"},
    "geolocation": {"description": "GPS coordinates or location", "category": "geospatial"},
    "coordinates": {"description": "Lat/lon coordinate pair", "category": "geospatial"},
    "twitter_id": {"description": "Twitter/X numeric user ID", "category": "identity"},
    "facebook_id": {"description": "Facebook numeric user ID", "category": "identity"},
    "youtube_channel_id": {"description": "YouTube channel ID", "category": "identity"},
    "youtube_video_id": {"description": "YouTube video ID", "category": "media"},
    "reddit_username": {"description": "Reddit username", "category": "identity"},
    "instagram_handle": {"description": "Instagram handle", "category": "identity"},
    "github_username": {"description": "GitHub username", "category": "identity"},
    "linkedin_url": {"description": "LinkedIn profile URL", "category": "identity"},
    "tiktok_handle": {"description": "TikTok username", "category": "identity"},
    "snapchat_handle": {"description": "Snapchat username", "category": "identity"},
    "whatsapp_number": {"description": "WhatsApp phone number", "category": "identity"},
    "skype_id": {"description": "Skype username", "category": "identity"},
    "steam_id": {"description": "Steam profile ID or vanity URL", "category": "identity"},
    "xbox_gamertag": {"description": "Xbox gamertag", "category": "identity"},
    "minecraft_username": {"description": "Minecraft username", "category": "identity"},
    "twitch_handle": {"description": "Twitch username", "category": "identity"},
    "mastodon_handle": {"description": "Mastodon handle (user@instance)", "category": "identity"},
    "spotify_user": {"description": "Spotify username", "category": "identity"},
    "onlyfans_handle": {"description": "OnlyFans username", "category": "identity"},
    "vk_id": {"description": "VK (VKontakte) user ID", "category": "identity"},
    "license_plate": {"description": "Vehicle license/number plate", "category": "transport"},
    "vin": {"description": "Vehicle Identification Number", "category": "transport"},
    "imei": {"description": "Mobile device IMEI number", "category": "device"},
    "mac_address": {"description": "Network MAC address", "category": "infrastructure"},
    "ssid": {"description": "WiFi network SSID name", "category": "infrastructure"},
    "bssid": {"description": "WiFi access point MAC (BSSID)", "category": "infrastructure"},
    "flight_number": {"description": "Flight number (e.g., AA123)", "category": "transport"},
    "vessel_mmsi": {"description": "Ship MMSI or IMO number", "category": "transport"},
    "vessel_name": {"description": "Ship/vessel name", "category": "transport"},
    "certificate": {"description": "SSL/TLS certificate hash or serial", "category": "infrastructure"},
    "favicon_hash": {"description": "Website favicon hash", "category": "infrastructure"},
    "crypto_wallet": {"description": "Generic cryptocurrency wallet address", "category": "financial"},
    "crypto_tx": {"description": "Cryptocurrency transaction hash", "category": "financial"},
    "nft_token": {"description": "NFT token ID or collection", "category": "financial"},
    "pgp_key": {"description": "PGP/GPG key fingerprint or ID", "category": "identity"},
    "property_address": {"description": "Physical/real estate address", "category": "geospatial"},
    "document": {"description": "Document file for analysis", "category": "media"},
    "audio_file": {"description": "Audio file for analysis", "category": "media"},
    "video_file": {"description": "Video file for analysis", "category": "media"},
    "password": {"description": "Password or password hash for breach search", "category": "security"},
    "cve_id": {"description": "CVE vulnerability identifier", "category": "security"},
    "subreddit": {"description": "Reddit subreddit name", "category": "social"},
    "slack_workspace": {"description": "Slack workspace URL or name", "category": "identity"},
}


def load_extracted_tools():
    all_tools = []
    for pattern in ["extracted_tools_section*.json", "tools_research_part*.json"]:
        for f in DOCS_DIR.glob(pattern):
            try:
                data = json.load(open(f, "r", encoding="utf-8"))
                if isinstance(data, list):
                    all_tools.extend(data)
                    print(f"  Loaded {len(data)} tools from {f.name}")
            except (json.JSONDecodeError, Exception) as e:
                print(f"  Error loading {f.name}: {e}")
    return all_tools


def deduplicate_tools(tools):
    seen = {}
    for t in tools:
        key = t.get("url", "") or t.get("name", "")
        if key and key not in seen:
            seen[key] = t
        elif key in seen:
            existing = seen[key]
            existing_inputs = set(existing.get("input_types", []))
            existing_outputs = set(existing.get("output_types", []))
            existing_inputs.update(t.get("input_types", []))
            existing_outputs.update(t.get("output_types", []))
            existing["input_types"] = list(existing_inputs)
            existing["output_types"] = list(existing_outputs)
    return list(seen.values())


def build_tools_registry(tools):
    registry = []
    for i, t in enumerate(tools):
        entry = {
            "id": f"ext_{i:04d}_{t.get('name', 'unknown').lower().replace(' ', '_').replace('/', '_')[:30]}",
            "name": t.get("name", "Unknown"),
            "category": t.get("category", "uncategorized"),
            "description": t.get("description", ""),
            "input_types": t.get("input_types", []),
            "output_types": t.get("output_types", []),
            "method": t.get("method", "website"),
            "url": t.get("url", ""),
            "free": t.get("free", True),
            "reliability": "medium",
            "automated": t.get("method", "website") in ("api", "cli"),
        }
        registry.append(entry)
    return registry


def build_pivot_map(registry):
    pivot_map = defaultdict(lambda: {"tools": [], "yields": set(), "description": ""})

    for tool in registry:
        for input_type in tool.get("input_types", []):
            entry = pivot_map[input_type]
            entry["tools"].append(tool["id"])
            for output_type in tool.get("output_types", []):
                entry["yields"].add(output_type)

    result = {}
    for selector_type, data in pivot_map.items():
        result[selector_type] = {
            "tools": data["tools"],
            "yields": sorted(list(data["yields"])),
            "tool_count": len(data["tools"]),
            "description": SELECTOR_TYPE_DEFINITIONS.get(selector_type, {}).get("description", f"Selector type: {selector_type}"),
        }

    return result


def build_selector_types(pivot_map):
    types = {}
    for stype in set(list(SELECTOR_TYPE_DEFINITIONS.keys()) + list(pivot_map.keys())):
        definition = SELECTOR_TYPE_DEFINITIONS.get(stype, {})
        pm_entry = pivot_map.get(stype, {})
        types[stype] = {
            "description": definition.get("description", f"Auto-discovered: {stype}"),
            "category": definition.get("category", "unknown"),
            "tool_count": pm_entry.get("tool_count", 0),
            "yields_to": pm_entry.get("yields", []),
        }
    return types


def main():
    print("=== Building Expanded Ontology ===\n")

    # Load existing tools registry
    existing_registry = []
    existing_file = ONTOLOGY_DIR / "tools_registry.json"
    if existing_file.exists():
        existing_data = json.load(open(existing_file, "r", encoding="utf-8"))
        existing_registry = existing_data.get("tools", [])
        print(f"Existing registry: {len(existing_registry)} tools")

    # Load extracted tools
    print("\nLoading extracted tools...")
    extracted = load_extracted_tools()
    print(f"Total extracted: {len(extracted)}")

    # Deduplicate
    deduped = deduplicate_tools(extracted)
    print(f"After deduplication: {len(deduped)}")

    # Build new registry (merge existing + new)
    new_registry = build_tools_registry(deduped)

    # Merge: keep existing tools (they have wrappers), add new ones
    existing_ids = {t["id"] for t in existing_registry}
    merged_registry = list(existing_registry)
    for tool in new_registry:
        if tool["id"] not in existing_ids:
            merged_registry.append(tool)

    print(f"Merged registry: {len(merged_registry)} tools ({len(existing_registry)} existing + {len(merged_registry) - len(existing_registry)} new)")

    # Build pivot map
    pivot_map = build_pivot_map(merged_registry)
    print(f"\nPivot map: {len(pivot_map)} selector types")
    for stype, data in sorted(pivot_map.items(), key=lambda x: -x[1]["tool_count"])[:20]:
        print(f"  {stype:25s} -> {data['tool_count']:3d} tools -> yields {len(data['yields']):2d} types")

    # Build selector types
    selector_types = build_selector_types(pivot_map)

    # Save
    print("\nSaving...")
    with open(ONTOLOGY_DIR / "tools_registry_expanded.json", "w", encoding="utf-8") as f:
        json.dump({"tools": merged_registry, "total": len(merged_registry)}, f, indent=2, ensure_ascii=False)
    print(f"  tools_registry_expanded.json: {len(merged_registry)} tools")

    with open(ONTOLOGY_DIR / "pivot_map_expanded.json", "w", encoding="utf-8") as f:
        json.dump({"pivot_map": pivot_map}, f, indent=2, ensure_ascii=False)
    print(f"  pivot_map_expanded.json: {len(pivot_map)} types")

    with open(ONTOLOGY_DIR / "selector_types_expanded.json", "w", encoding="utf-8") as f:
        json.dump({"selector_types": selector_types}, f, indent=2, ensure_ascii=False)
    print(f"  selector_types_expanded.json: {len(selector_types)} types")

    # Stats
    all_inputs = set()
    all_outputs = set()
    automatable = 0
    for t in merged_registry:
        all_inputs.update(t.get("input_types", []))
        all_outputs.update(t.get("output_types", []))
        if t.get("automated"):
            automatable += 1

    print(f"\n=== ONTOLOGY STATS ===")
    print(f"Total tools: {len(merged_registry)}")
    print(f"Automatable (API/CLI): {automatable}")
    print(f"Unique input types: {len(all_inputs)}")
    print(f"Unique output types: {len(all_outputs)}")
    print(f"Total selector types: {len(selector_types)}")
    print(f"\nAll input types: {sorted(all_inputs)}")
    print(f"\nAll output types: {sorted(all_outputs)}")


if __name__ == "__main__":
    main()
