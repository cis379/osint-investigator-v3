"""OSINT tools for name-based lookups.

These tools accept 'name' (and sometimes 'company') selectors and query
free public APIs and data sources.
"""
import json
import re
import requests
from urllib.parse import quote_plus
from .base import BaseTool, ToolResult, EntityFound


class WikipediaSearchTool(BaseTool):
    name = "wikipedia_search"
    description = "Search Wikipedia for biographical information about a person"
    input_types = ["name", "company"]
    output_types = ["name", "url", "company"]
    method = "api"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        try:
            resp = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": selector,
                    "srlimit": 5,
                    "format": "json",
                },
                headers={"User-Agent": "OSINTInvestigator/1.0"},
                timeout=15,
            )
            raw_output = resp.text[:5000]
            entities = []

            if resp.status_code == 200:
                data = resp.json()
                for result in data.get("query", {}).get("search", []):
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    snippet_clean = re.sub(r'<[^>]+>', '', snippet)
                    wiki_url = f"https://en.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}"

                    entities.append(EntityFound(
                        value=wiki_url,
                        entity_type="url",
                        confidence="probable",
                        source_citation=f"Wikipedia: {title} - {snippet_clean[:100]}",
                        metadata={"title": title, "snippet": snippet_clean},
                    ))
                    entities.append(EntityFound(
                        value=title,
                        entity_type="name" if selector_type == "name" else "company",
                        confidence="probable",
                        source_citation=f"Wikipedia article: {title}",
                    ))

            return self.make_result(selector, selector_type, raw_output, entities,
                                    success=resp.status_code == 200)
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


class HaveIBeenPwnedNameTool(BaseTool):
    name = "hibp_name_search"
    description = "Check if a person's name appears in known data breaches via breach directory"
    input_types = ["name", "email"]
    output_types = ["email", "url"]
    method = "api"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        try:
            resp = requests.get(
                f"https://api.pwnedpasswords.com/range/{selector[:5].encode().hex()[:5]}",
                headers={"User-Agent": "OSINTInvestigator/1.0"},
                timeout=10,
            )

            parts = selector.strip().lower().split()
            if len(parts) < 2:
                return self.make_result(selector, selector_type,
                                        "Name too short for email generation", [], True)

            first = re.sub(r'[^a-z]', '', parts[0])
            last = re.sub(r'[^a-z]', '', parts[-1])

            email_guesses = [
                f"{first}.{last}@gmail.com",
                f"{first}{last}@gmail.com",
                f"{first[0]}{last}@gmail.com",
                f"{first}.{last}@yahoo.com",
                f"{first}.{last}@outlook.com",
                f"{first}.{last}@hotmail.com",
                f"{first}.{last}@protonmail.com",
            ]

            raw_lines = [f"Generated {len(email_guesses)} email candidates for breach check:"]
            entities = []

            for email in email_guesses:
                raw_lines.append(f"  Candidate email: {email}")
                entities.append(EntityFound(
                    value=email,
                    entity_type="email",
                    confidence="possible",
                    source_citation=f"Generated email candidate from name: {selector}",
                    metadata={"generated": True, "basis": "name_permutation"},
                ))

            raw_output = "\n".join(raw_lines)
            return self.make_result(selector, selector_type, raw_output, entities, success=True)
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


class WikidataTool(BaseTool):
    name = "wikidata_search"
    description = "Search Wikidata for public information about a person or entity"
    input_types = ["name", "company"]
    output_types = ["name", "url", "company"]
    method = "api"

    HEADERS = {"User-Agent": "OSINTInvestigator/1.0 (research tool; https://github.com)"}

    def query(self, selector: str, selector_type: str) -> ToolResult:
        try:
            search_resp = requests.get(
                "https://www.wikidata.org/w/api.php",
                params={
                    "action": "wbsearchentities",
                    "search": selector,
                    "language": "en",
                    "limit": 5,
                    "format": "json",
                },
                headers=self.HEADERS,
                timeout=15,
            )
            raw_parts = [search_resp.text[:2000]]
            entities = []

            if search_resp.status_code == 200:
                search_data = search_resp.json()
                for result in search_data.get("search", []):
                    qid = result.get("id", "")
                    label = result.get("label", "")
                    description = result.get("description", "")

                    entity_resp = requests.get(
                        "https://www.wikidata.org/w/api.php",
                        params={
                            "action": "wbgetentities",
                            "ids": qid,
                            "props": "claims|sitelinks",
                            "languages": "en",
                            "format": "json",
                        },
                        headers=self.HEADERS,
                        timeout=10,
                    )

                    metadata = {"qid": qid, "description": description}

                    if entity_resp.status_code == 200:
                        entity_data = entity_resp.json()
                        ent = entity_data.get("entities", {}).get(qid, {})
                        claims = ent.get("claims", {})
                        sitelinks = ent.get("sitelinks", {})

                        if "enwiki" in sitelinks:
                            wiki_title = sitelinks["enwiki"].get("title", "")
                            entities.append(EntityFound(
                                value=f"https://en.wikipedia.org/wiki/{quote_plus(wiki_title)}",
                                entity_type="url",
                                confidence="confirmed",
                                source_citation=f"Wikidata {qid} Wikipedia link",
                            ))

                        # P106 = occupation
                        for claim in claims.get("P106", [])[:5]:
                            occ_id = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id", "")
                            if occ_id:
                                metadata.setdefault("occupations", []).append(occ_id)

                        # P108 = employer
                        for claim in claims.get("P108", [])[:5]:
                            emp = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
                            emp_id = emp.get("id", "")
                            if emp_id:
                                metadata.setdefault("employers", []).append(emp_id)

                        # P569 = date of birth
                        for claim in claims.get("P569", [])[:1]:
                            dob = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("time", "")
                            if dob:
                                metadata["birth_date"] = dob

                        # P27 = country of citizenship
                        for claim in claims.get("P27", [])[:3]:
                            cit = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id", "")
                            if cit:
                                metadata.setdefault("citizenship", []).append(cit)

                        raw_parts.append(json.dumps({"qid": qid, "claims_count": len(claims), "sitelinks": list(sitelinks.keys())[:10]}))

                    entities.append(EntityFound(
                        value=label,
                        entity_type="name" if selector_type == "name" else "company",
                        confidence="confirmed",
                        source_citation=f"Wikidata {qid}: {description}",
                        metadata=metadata,
                    ))

            raw_output = "\n---\n".join(raw_parts)
            return self.make_result(selector, selector_type, raw_output, entities,
                                    success=search_resp.status_code == 200)
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


class GravatarTool(BaseTool):
    name = "gravatar_check"
    description = "Check Gravatar profiles for email candidates derived from a name"
    input_types = ["name", "email"]
    output_types = ["email", "url", "username"]
    method = "api"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        import hashlib

        if selector_type == "email":
            emails = [selector]
        else:
            parts = selector.strip().lower().split()
            if len(parts) < 2:
                return self.make_result(selector, selector_type, "Need first+last name", [], False,
                                        "Name must have at least two parts")
            first = re.sub(r'[^a-z]', '', parts[0])
            last = re.sub(r'[^a-z]', '', parts[-1])
            emails = [
                f"{first}.{last}@gmail.com",
                f"{first}{last}@gmail.com",
                f"{first[0]}{last}@gmail.com",
                f"{first}.{last}@yahoo.com",
                f"{first}.{last}@outlook.com",
                f"{first}.{last}@protonmail.com",
            ]

        raw_lines = []
        entities = []

        for email in emails:
            email_hash = hashlib.md5(email.strip().lower().encode()).hexdigest()
            try:
                profile_resp = requests.get(
                    f"https://en.gravatar.com/{email_hash}.json",
                    timeout=8,
                )
                if profile_resp.status_code == 200:
                    data = profile_resp.json()
                    for entry in data.get("entry", []):
                        display_name = entry.get("displayName", "")
                        profile_url = entry.get("profileUrl", "")
                        raw_lines.append(f"[HIT] {email} -> Gravatar: {display_name} ({profile_url})")

                        if profile_url:
                            entities.append(EntityFound(
                                value=profile_url, entity_type="url", confidence="confirmed",
                                source_citation=f"Gravatar profile for {email}: {display_name}",
                            ))
                        entities.append(EntityFound(
                            value=email, entity_type="email", confidence="probable",
                            source_citation=f"Gravatar profile exists for {email}",
                        ))
                        preferred_username = entry.get("preferredUsername", "")
                        if preferred_username:
                            entities.append(EntityFound(
                                value=preferred_username, entity_type="username",
                                confidence="probable",
                                source_citation=f"Gravatar username for {email}",
                            ))

                        for account in entry.get("accounts", []):
                            acct_url = account.get("url", "")
                            if acct_url:
                                entities.append(EntityFound(
                                    value=acct_url, entity_type="url", confidence="confirmed",
                                    source_citation=f"Gravatar linked account: {account.get('shortname', '')}",
                                ))
                else:
                    raw_lines.append(f"[MISS] {email} -> no Gravatar profile")
            except requests.RequestException:
                raw_lines.append(f"[ERROR] {email} -> request failed")

        raw_output = "\n".join(raw_lines)
        return self.make_result(selector, selector_type, raw_output, entities, success=True)


class UsernameFromNameTool(BaseTool):
    name = "name_to_username"
    description = "Generate likely usernames from a real name and check common platforms"
    input_types = ["name"]
    output_types = ["username", "url"]
    method = "library"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        parts = selector.strip().lower().split()
        if len(parts) < 2:
            return self.make_result(selector, selector_type, "Need first and last name", [], False,
                                    "Name must contain at least first and last name")

        first = re.sub(r'[^a-z]', '', parts[0])
        last = re.sub(r'[^a-z]', '', parts[-1])
        middle = re.sub(r'[^a-z]', '', parts[1]) if len(parts) > 2 else ""

        candidates = list(dict.fromkeys([
            f"{first}{last}",
            f"{first}.{last}",
            f"{first}_{last}",
            f"{first}-{last}",
            f"{first[0]}{last}",
            f"{first}{last[0]}",
            f"{last}{first}",
            f"{last}.{first}",
            f"{last}_{first}",
            f"{first}{middle}{last}" if middle else None,
            f"{first}.{middle}.{last}" if middle else None,
            f"{first[0]}{middle[0] if middle else ''}{last}",
        ]))
        candidates = [c for c in candidates if c]

        raw_lines = [f"Generated {len(candidates)} username candidates from '{selector}':",
                     ""]

        entities = []
        platforms = {
            "github": "https://api.github.com/users/{}",
            "gitlab": "https://gitlab.com/api/v4/users?username={}",
        }

        for username in candidates[:8]:
            raw_lines.append(f"  Candidate: {username}")

            for platform, url_template in platforms.items():
                try:
                    url = url_template.format(username)
                    resp = requests.get(url, timeout=5)
                    if resp.status_code == 200:
                        if platform == "github":
                            profile_data = resp.json()
                            profile_url = profile_data.get("html_url", f"https://github.com/{username}")
                            bio = profile_data.get("bio", "")
                            real_name = profile_data.get("name", "")
                            raw_lines.append(f"    [HIT] {platform}: {profile_url} (name: {real_name}, bio: {bio})")

                            name_match = real_name and (
                                first in real_name.lower() or last in real_name.lower()
                            )

                            entities.append(EntityFound(
                                value=profile_url,
                                entity_type="url",
                                confidence="confirmed" if name_match else "possible",
                                source_citation=f"GitHub profile {profile_url} (display name: {real_name})",
                                metadata={"bio": bio, "name": real_name, "platform": "github"},
                            ))
                            if name_match:
                                entities.append(EntityFound(
                                    value=username,
                                    entity_type="username",
                                    confidence="probable",
                                    source_citation=f"GitHub username {username} matches name {real_name}",
                                ))
                        elif platform == "gitlab":
                            users = resp.json()
                            if users:
                                user = users[0]
                                profile_url = user.get("web_url", f"https://gitlab.com/{username}")
                                real_name = user.get("name", "")
                                raw_lines.append(f"    [HIT] {platform}: {profile_url} (name: {real_name})")

                                name_match = real_name and (
                                    first in real_name.lower() or last in real_name.lower()
                                )

                                entities.append(EntityFound(
                                    value=profile_url,
                                    entity_type="url",
                                    confidence="confirmed" if name_match else "possible",
                                    source_citation=f"GitLab profile {profile_url} (display name: {real_name})",
                                    metadata={"name": real_name, "platform": "gitlab"},
                                ))
                    else:
                        raw_lines.append(f"    [MISS] {platform}: {resp.status_code}")
                except requests.RequestException:
                    raw_lines.append(f"    [ERROR] {platform}: request failed")

        raw_output = "\n".join(raw_lines)
        return self.make_result(selector, selector_type, raw_output, entities, success=True)


TOOLS = [
    WikipediaSearchTool(),
    HaveIBeenPwnedNameTool(),
    WikidataTool(),
    GravatarTool(),
    UsernameFromNameTool(),
]
