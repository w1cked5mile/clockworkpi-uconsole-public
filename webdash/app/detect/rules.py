"""The owner's detection rules: load, validate, match. Pure stdlib, no I/O beyond reading the file.

The rules file lives on the device, outside the repo: WEBDASH_DATA_DIR/detect-rules.json. It ships
empty (see configs/webdash/detect-rules.example.json for the format); the owner fills it from
sources they have checked. Each rule says which device class a match means, which radio and which
field it reads, how to match, and how sure a match is:

  {"rules": [
    {"id": "own-test-ap", "class": "other", "radio": "wifi", "field": "ssid",
     "match": "exact", "pattern": "fancy-detect-test", "confidence": "low",
     "note": "my own phone hotspot, to prove the log works"}
  ]}

A rule that fails validation is skipped and reported (load() returns the errors), so one typo
can't take the whole watch down.
"""
import json
import os
import re
from pathlib import Path

DATA_DIR = Path(os.environ.get("WEBDASH_DATA_DIR", "/data"))
RULES_PATH = DATA_DIR / "detect-rules.json"

# Device classes the UI has a glyph and plain label for (js/detect.js CLASSES). "other" catches
# anything the owner doesn't want to classify; Kismet alerts land in deauth_flood or other.
CLASSES = ("flipper", "pwnagotchi", "marauder", "bruce", "pineapple", "deauther", "implant",
           "deauth_flood", "beacon_flood", "ble_spam", "other")
RADIOS = ("wifi", "ble")
# Fields a rule may read, per radio. Wi-Fi fields are the reduced Kismet record (survey/snapshot.py);
# BLE fields are reserved for the passive BLE listener (not built yet), so BLE rules load but can't
# fire until it exists.
FIELDS = {"wifi": ("ssid", "name", "mac", "manuf"), "ble": ("name", "mac")}
MATCHES = ("exact", "prefix", "contains", "regex")
CONFIDENCES = ("high", "medium", "low")
CONF_RANK = {"low": 1, "medium": 2, "high": 3}

MAX_RULES = 200
MAX_PATTERN = 200
ID_RE = re.compile(r"^[A-Za-z0-9_.-]{1,48}$")


def _validate(i: int, r) -> tuple[dict | None, str | None]:
    if not isinstance(r, dict):
        return None, f"rule {i}: not an object"
    rid = r.get("id")
    if not isinstance(rid, str) or not ID_RE.match(rid):
        return None, f"rule {i}: id must be 1-48 of A-Z a-z 0-9 _ . -"
    cls, radio, field = r.get("class"), r.get("radio"), r.get("field")
    match, pattern, conf = r.get("match", "exact"), r.get("pattern"), r.get("confidence")
    if cls not in CLASSES:
        return None, f"{rid}: class must be one of {', '.join(CLASSES)}"
    if radio not in RADIOS:
        return None, f"{rid}: radio must be wifi or ble"
    if field not in FIELDS[radio]:
        return None, f"{rid}: field for {radio} must be one of {', '.join(FIELDS[radio])}"
    if match not in MATCHES:
        return None, f"{rid}: match must be one of {', '.join(MATCHES)}"
    if not isinstance(pattern, str) or not pattern or len(pattern) > MAX_PATTERN:
        return None, f"{rid}: pattern must be a non-empty string of at most {MAX_PATTERN} characters"
    if conf not in CONFIDENCES:
        return None, f"{rid}: confidence must be high, medium or low"
    case = bool(r.get("case_sensitive", False))
    compiled = None
    if match == "regex":
        try:
            compiled = re.compile(pattern, 0 if case else re.IGNORECASE)
        except re.error as exc:
            return None, f"{rid}: bad regex ({exc})"
    note = r.get("note", "")
    return {
        "id": rid, "class": cls, "radio": radio, "field": field, "match": match,
        "pattern": pattern, "confidence": conf, "case_sensitive": case,
        "note": note[:300] if isinstance(note, str) else "", "_re": compiled,
    }, None


def parse(obj) -> tuple[list[dict], list[str]]:
    """Validate a decoded rules document → (rules, errors)."""
    if not isinstance(obj, dict) or not isinstance(obj.get("rules"), list):
        return [], ['rules file must be {"rules": [...]}']
    rules, errors, seen = [], [], set()
    for i, r in enumerate(obj["rules"][:MAX_RULES]):
        rule, err = _validate(i, r)
        if err:
            errors.append(err)
        elif rule["id"] in seen:
            errors.append(f"{rule['id']}: duplicate id")
        else:
            seen.add(rule["id"])
            rules.append(rule)
    if len(obj["rules"]) > MAX_RULES:
        errors.append(f"only the first {MAX_RULES} rules are used")
    return rules, errors


def load(path: Path | None = None) -> tuple[list[dict], list[str]]:
    """Read and validate the rules file. A missing file is the normal shipped state: no rules,
    no error."""
    p = path or RULES_PATH
    try:
        text = p.read_text()
    except FileNotFoundError:
        return [], []
    except OSError as exc:
        return [], [f"can't read {p.name}: {exc}"]
    try:
        obj = json.loads(text)
    except ValueError as exc:
        return [], [f"{p.name} is not valid JSON: {exc}"]
    return parse(obj)


def public(rule: dict) -> dict:
    """A rule without its compiled regex, for the API."""
    return {k: v for k, v in rule.items() if not k.startswith("_")}


def _hit(rule: dict, value) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if rule["match"] == "regex":
        return bool(rule["_re"].search(value))
    v, p = (value, rule["pattern"]) if rule["case_sensitive"] else (value.lower(), rule["pattern"].lower())
    if rule["field"] == "mac":  # MACs compare without separators, so AA:BB and aabb both work
        v, p = v.replace(":", "").replace("-", ""), p.replace(":", "").replace("-", "")
    if rule["match"] == "exact":
        return v == p
    if rule["match"] == "prefix":
        return v.startswith(p)
    return p in v


def match(record: dict, rules: list[dict], radio: str) -> dict | None:
    """The strongest rule that matches one observed record on `radio`, or None. Ties go to the
    first rule in the file."""
    best = None
    for rule in rules:
        if rule["radio"] != radio or not _hit(rule, record.get(rule["field"])):
            continue
        if best is None or CONF_RANK[rule["confidence"]] > CONF_RANK[best["confidence"]]:
            best = rule
    return best


def describe(rule: dict) -> str:
    """Plain-English statement of a rule, for the log's details pane."""
    how = {"exact": "is", "prefix": "starts with", "contains": "contains", "regex": "matches"}[rule["match"]]
    radio = "BLE" if rule["radio"] == "ble" else "Wi-Fi"
    return f"{radio} {rule['field']} {how} “{rule['pattern']}”"
