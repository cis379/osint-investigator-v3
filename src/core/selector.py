import re
from dataclasses import dataclass

SELECTOR_PATTERNS = {
    "email": re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'),
    "ip_v4": re.compile(r'^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$'),
    "ip_v6": re.compile(r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}$|^(?:[0-9a-fA-F]{1,4}:){1,7}:$'),
    "phone": re.compile(r'^\+?[1-9]\d{6,14}$'),
    "crypto_btc": re.compile(r'^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$'),
    "crypto_eth": re.compile(r'^0x[0-9a-fA-F]{40}$'),
    "hash_md5": re.compile(r'^[a-fA-F0-9]{32}$'),
    "hash_sha1": re.compile(r'^[a-fA-F0-9]{40}$'),
    "hash_sha256": re.compile(r'^[a-fA-F0-9]{64}$'),
    "url": re.compile(r'^https?://[^\s/$.?#].[^\s]*$'),
    "domain": re.compile(r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*\.[A-Za-z]{2,}$'),
    "telegram_handle": re.compile(r'^@?[a-zA-Z][a-zA-Z0-9_]{4,31}$'),
    "discord_id": re.compile(r'^\d{17,20}$'),
    "username": re.compile(r'^@?[a-zA-Z0-9._\-]{1,64}$'),
}

DETECTION_ORDER = [
    "email",
    "ip_v4",
    "ip_v6",
    "crypto_btc",
    "crypto_eth",
    "hash_sha256",
    "hash_sha1",
    "hash_md5",
    "url",
    "phone",
    "domain",
    "discord_id",
    # NOTE: telegram_handle is intentionally NOT auto-detected. A bare handle is
    # indistinguishable from a username on any other platform (the old pattern
    # greedily claimed every 5-32 char handle as telegram_handle with false "exact"
    # confidence, and telegram_handle has no structured tools -> silent 0-tool runs).
    # A bare handle resolves to the general "username" bucket (sherlock/maigret cover
    # all platforms, incl. Telegram/Instagram). Use telegram_handle only when the user
    # gives explicit platform context (e.g. a t.me/ URL).
    "username",
]


@dataclass
class Selector:
    value: str
    selector_type: str
    original_input: str
    confidence: str  # "exact" | "inferred"

    def to_dict(self):
        return {
            "value": self.value,
            "type": self.selector_type,
            "original_input": self.original_input,
            "confidence": self.confidence,
        }


def normalize_input(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("@") and not raw.startswith("@@"):
        pass  # keep @ for telegram detection, stripped later for username
    return raw


def detect_selector_type(raw_input: str) -> Selector:
    normalized = normalize_input(raw_input)

    for stype in DETECTION_ORDER:
        pattern = SELECTOR_PATTERNS[stype]
        test_value = normalized

        if stype == "phone":
            test_value = re.sub(r'[\s\-\(\)]', '', normalized)

        if stype == "telegram_handle" and normalized.startswith("@"):
            test_value = normalized
        elif stype == "username" and normalized.startswith("@"):
            test_value = normalized[1:]

        if pattern.match(test_value):
            final_value = test_value
            if stype == "telegram_handle" and final_value.startswith("@"):
                final_value = final_value[1:]
            if stype == "username" and normalized.startswith("@"):
                final_value = normalized[1:]
            if stype == "phone":
                final_value = re.sub(r'[\s\-\(\)]', '', normalized)

            # A bare handle matched as "username" is a GENERAL/ambiguous identifier
            # (platform unknown) -> mark inferred so the supervisor treats it generally
            # and leans on the broad enumerators + web search. Structured types
            # (email/ip/domain/...) remain "exact".
            return Selector(
                value=final_value,
                selector_type=stype,
                original_input=raw_input,
                confidence="inferred" if stype == "username" else "exact",
            )

    return Selector(
        value=normalized,
        selector_type="name",
        original_input=raw_input,
        confidence="inferred",
    )


def detect_multiple_types(raw_input: str) -> list[Selector]:
    normalized = normalize_input(raw_input)
    matches = []

    for stype in DETECTION_ORDER:
        pattern = SELECTOR_PATTERNS[stype]
        test_value = normalized
        if stype == "phone":
            test_value = re.sub(r'[\s\-\(\)]', '', normalized)

        if pattern.match(test_value):
            matches.append(Selector(
                value=test_value,
                selector_type=stype,
                original_input=raw_input,
                confidence="exact" if len(matches) == 0 else "possible",
            ))

    if not matches:
        matches.append(Selector(
            value=normalized,
            selector_type="name",
            original_input=raw_input,
            confidence="inferred",
        ))

    return matches


if __name__ == "__main__":
    test_cases = [
        "user@example.com",
        "192.168.1.1",
        "+15551234567",
        "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18",
        "d41d8cd98f00b204e9800998ecf8427e",
        "https://example.com/path",
        "example.com",
        "@telegram_user",
        "123456789012345678",
        "john_doe_123",
        "John Smith",
    ]

    for tc in test_cases:
        result = detect_selector_type(tc)
        print(f"{tc:50s} -> {result.selector_type:20s} ({result.value})")
