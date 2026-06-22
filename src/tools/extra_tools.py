"""Library/custom tools that don't fit the HTTP or CLI declarative runners.

- phonenumbers: offline phone validation/region/carrier (Google libphonenumber).
- email_header_analyzer: parse raw email headers / .eml -> originating IPs, relays, addresses.
"""
import re

from .base import BaseTool, EntityFound

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_IPV4_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b")
_IPV6_RE = re.compile(r"\b(?:[0-9A-Fa-f]{1,4}:){2,7}[0-9A-Fa-f]{0,4}\b")
_PRIVATE_IP = re.compile(r"^(?:10\.|127\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.|0\.)")


class PhoneNumbersTool(BaseTool):
    name = "phonenumbers"
    description = "Phone validation, region, carrier, and line-type (offline, libphonenumber)"
    input_types = ["phone"]
    output_types = ["location", "company"]
    method = "library"

    def check_installed(self) -> bool:
        try:
            import phonenumbers  # noqa: F401
            return True
        except ImportError:
            return False

    def query(self, selector, selector_type):
        if selector_type != "phone":
            return self.make_result(selector, selector_type, "", [], False, "phonenumbers only accepts phone")
        try:
            import phonenumbers
            from phonenumbers import geocoder, carrier, timezone, number_type, PhoneNumberType
        except ImportError:
            return self.make_result(selector, selector_type, "", [], False,
                                    "phonenumbers not installed. Install: pip install phonenumbers")

        raw_in = selector if selector.strip().startswith("+") else "+" + selector.strip()
        try:
            num = phonenumbers.parse(raw_in, None)
        except phonenumbers.NumberParseException as e:
            return self.make_result(selector, selector_type, f"parse error: {e}", [], False, str(e))

        valid = phonenumbers.is_valid_number(num)
        region = geocoder.description_for_number(num, "en")
        carr = carrier.name_for_number(num, "en")
        tzs = list(timezone.time_zones_for_number(num))
        type_names = {v: k for k, v in vars(PhoneNumberType).items() if isinstance(v, int)}
        ntype = type_names.get(number_type(num), "UNKNOWN")
        e164 = phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)

        entities = []
        if region:
            entities.append(EntityFound(value=region, entity_type="location", confidence="probable",
                                        source_citation="phonenumbers geocoder",
                                        metadata={"country_code": num.country_code}))
        if carr:
            entities.append(EntityFound(value=carr, entity_type="company", confidence="probable",
                                        source_citation="phonenumbers carrier (numbering-plan guess)"))
        raw = (f"input={selector} e164={e164} valid={valid} region={region or '-'} "
               f"carrier={carr or '-'} line_type={ntype} timezones={tzs}")
        return self.make_result(selector, selector_type, raw, entities, success=valid,
                                error="" if valid else "not a valid phone number")


class EmailHeaderTool(BaseTool):
    name = "email_header_analyzer"
    description = "Parse raw email headers / .eml: originating IPs, relay chain, sender/recipient addresses"
    input_types = ["email_header", "eml_file"]
    output_types = ["ip_v4", "ip_v6", "email", "domain"]
    method = "library"

    def query(self, selector, selector_type):
        if selector_type not in self.input_types:
            return self.make_result(selector, selector_type, "", [], False,
                                    f"email_header_analyzer doesn't accept {selector_type}")
        import email
        from email import policy

        if selector_type == "eml_file":
            try:
                raw = open(selector, encoding="utf-8", errors="replace").read()
            except OSError as e:
                return self.make_result(selector, selector_type, "", [], False, f"cannot read file: {e}")
        else:
            raw = selector

        try:
            msg = email.message_from_string(raw, policy=policy.default)
        except Exception as e:
            return self.make_result(selector, selector_type, raw[:2000], [], False, f"parse error: {e}")

        entities, seen = [], set()

        def add(value, etype, conf, cite):
            key = (etype, value.lower())
            if value and key not in seen:
                seen.add(key)
                entities.append(EntityFound(value=value, entity_type=etype, confidence=conf,
                                            source_citation=cite))

        # Addresses from envelope headers
        for hdr in ("from", "to", "return-path", "reply-to", "sender", "cc"):
            v = msg.get(hdr)
            if v:
                for em in _EMAIL_RE.findall(str(v)):
                    add(em, "email", "confirmed", f"email header: {hdr}")

        # Received chain -> originating public IPs (skip private/internal)
        received = msg.get_all("Received") or []
        for line in received:
            for ip in _IPV4_RE.findall(str(line)):
                if not _PRIVATE_IP.match(ip):
                    add(ip, "ip_v4", "probable", "email Received header")
            for ip in _IPV6_RE.findall(str(line)):
                if ip.lower() not in ("::1",):
                    add(ip, "ip_v6", "probable", "email Received header")

        # Sender domains from key headers
        for hdr in ("from", "return-path", "message-id"):
            v = msg.get(hdr)
            if v:
                for em in _EMAIL_RE.findall(str(v)):
                    dom = em.split("@", 1)[1]
                    add(dom, "domain", "probable", f"email header domain ({hdr})")

        summary = (f"From={msg.get('from','-')} | Subject={msg.get('subject','-')} | "
                   f"Date={msg.get('date','-')} | Received-hops={len(received)}")
        return self.make_result(selector, selector_type, summary + "\n\n" + raw[:3000],
                                entities, success=bool(entities))


TOOLS = [PhoneNumbersTool(), EmailHeaderTool()]
