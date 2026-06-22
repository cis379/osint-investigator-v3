
import sys, re
import ignorant.core as _c
_c.check_update = lambda: None
raw = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    import phonenumbers
    e164 = raw if raw.strip().startswith("+") else "+" + re.sub(r"[^0-9]", "", raw)
    p = phonenumbers.parse(e164, None)
    cc, num = str(p.country_code), str(p.national_number)
except Exception:
    s = re.sub(r"[^0-9]", "", raw)
    cc, num = s[:1], s[1:]
sys.argv = ["ignorant", "--no-color", "--no-clear", "-T", "12", cc, num]
_c.main()
