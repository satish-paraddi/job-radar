import json
import re
from datetime import date, datetime, timedelta, timezone

DEFAULT_EXCLUDED_ROLE_KEYWORDS = (
    "principal",
    "senior",
    "staff",
    "lead",
    "director",
    "manager",
    "distinguished",
    "sr.",
    "sr ",
)

# Titles that contain "engineer" but aren't software engineering roles.
DEFAULT_EXCLUDED_TITLE_PHRASES = (
    "sales engineer",
    "solutions engineer",
    "solution engineer",
    "support engineer",
    "solutions architect",
    "field engineer",
)

# For companies whose engineering category mixes in hardware roles (NVIDIA, DoorDash).
HARDWARE_TITLE_PHRASES = (
    "asic",
    "pcb",
    "hardware",
    "mixed signal",
    "electrical engineer",
    "layout engineer",
    "verification engineer",
    "co-design",
    "soc ip",
    "low-power",
    "bring-up",
    "cpu design",
    "package design",
    "package test",
    "system design engineer",
    "power test",
    "radio frequency",
    "flight test",
    "reliability test",
    "manufacturing",
    "technician",
    "technical sourcer",
)

ENGINEERING_TITLE_RE =re.compile(r"\b(software|engineer|engineering|developer|swe)\b", re.I)

_US_STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA",
    "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT",
    "VA", "WA", "WV", "WI", "WY", "DC",
}
_US_STATE_CODE_RE = re.compile(r",\s*([A-Z]{2})\b")
_US_MARKER_RE = re.compile(r"\b(united states|usa|u\.s\.)\b", re.I)
_US_TOKEN_RE = re.compile(r"\bUS\b")
_US_CITIES_RE = re.compile(
    r"\b(san francisco|seattle|new york|nyc|chicago|sunnyvale|oakland|austin|boston|"
    r"los angeles|atlanta|denver|miami|bay area|mountain view|palo alto|san jose|"
    r"menlo park|redmond|bellevue|portland|dallas|philadelphia|pittsburgh|ann arbor|"
    r"washington,? d\.?c\.?|san diego|santa clara|cambridge, ma)\b",
    re.I,
)
_US_STATE_NAMES_RE = re.compile(
    r"\b(alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|florida|"
    r"hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|"
    r"massachusetts|michigan|minnesota|mississippi|missouri|montana|nebraska|nevada|"
    r"new hampshire|new jersey|new mexico|north carolina|north dakota|ohio|oklahoma|oregon|"
    r"pennsylvania|rhode island|south carolina|south dakota|tennessee|texas|utah|vermont|"
    r"virginia|washington|west virginia|wisconsin|wyoming)\b",
    re.I,
)


def load_json(payload: str):
    try:
        return json.loads(payload)
    except (json.JSONDecodeError, TypeError):
        return None


def is_us_location(text: str) -> bool:
    if not text:
        return False
    if any(regex.search(text) for regex in (_US_MARKER_RE, _US_TOKEN_RE, _US_CITIES_RE, _US_STATE_NAMES_RE)):
        return True
    return any(code in _US_STATE_CODES for code in _US_STATE_CODE_RE.findall(text))


def is_engineering_title(title: str) -> bool:
    return bool(ENGINEERING_TITLE_RE.search(title or ""))


def format_locations(labels) -> str:
    unique = []
    for label in labels or []:
        label = str(label or "").strip()
        if label and label not in unique:
            unique.append(label)
    if not unique:
        return ""
    if len(unique) == 1:
        return unique[0]
    return f"{unique[0]}; +{len(unique) - 1} more"


def iso_date(value) -> str:
    """'2026-10-02T13:37:47.218Z' or a unix timestamp -> '2026-10-02'."""
    if isinstance(value, (int, float)) and value > 0:
        return datetime.fromtimestamp(value, tz=timezone.utc).strftime("%Y-%m-%d")
    return str(value or "").strip()[:10]


_RELATIVE_DAYS_RE = re.compile(r"(\d+)\+?\s+days?\s+ago", re.I)


def relative_posted_date(text: str, today: date | None = None) -> str:
    """Workday-style 'Posted Today' / 'Posted Yesterday' / 'Posted 3 Days Ago' -> ISO date."""
    text = (text or "").strip()
    today = today or date.today()
    lowered = text.lower()
    if "today" in lowered:
        return today.isoformat()
    if "yesterday" in lowered:
        return (today - timedelta(days=1)).isoformat()
    match = _RELATIVE_DAYS_RE.search(text)
    if match:
        if "+" in text:
            return ""
        return (today - timedelta(days=int(match.group(1)))).isoformat()
    return ""
