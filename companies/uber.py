from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

from companies.base import CompanyDefinition
from uber_parser import get_total_pages, get_total_results, parse_jobs

# Uber moved careers from uber.com/careers to jobs.uber.com (Next.js + Cloudflare).
# The results page is backed by GET /api/jobs/search/ which accepts the same query
# params as the page URL (team, subTeam, countries, locations, page, pagesize).
UBER_JOBS_BASE_URL = "https://jobs.uber.com"
UBER_SEARCH_URL = (
    f"{UBER_JOBS_BASE_URL}/en/jobs/"
    "?team=Engineer"
    "&countries=United%20States"
)
UBER_API_PATH = "/api/jobs/search/"
PAGE_SIZE = 100

EXCLUDED_ROLE_KEYWORDS = (
    "principal",
    "senior",
    "staff",
    "lead",
    "director",
    "manager",
    "sr.",
    "sr ",
)

# Cloudflare rate-limits the API aggressively, so space requests out and back off on 429.
REQUEST_DELAY_MS = 1500
MAX_ATTEMPTS = 3
RETRY_BACKOFF_MS = 10000

# The API rejects plain HTTP clients (Cloudflare challenge), so it's called with fetch()
# from inside a loaded jobs.uber.com page, which carries the Cloudflare cookies.
_FETCH_JS = """
async (path) => {
    const response = await fetch(path, { headers: { accept: "application/json" } });
    return [response.status, await response.text()];
}
"""


def build_search_url(search_url: str, page_num: int) -> str:
    parsed = urlsplit(search_url)
    params = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k not in {"page", "pagesize"}]
    params += [("page", str(page_num)), ("pagesize", str(PAGE_SIZE))]
    return urlunsplit(parsed._replace(query=urlencode(params, quote_via=quote)))


def _build_api_path(url: str) -> str:
    query = urlsplit(url).query
    return f"{UBER_API_PATH}?{query}" if query else UBER_API_PATH


async def _ensure_on_jobs_site(page, runtime_config) -> None:
    if page.url.startswith(UBER_JOBS_BASE_URL):
        return
    print(f"[{runtime_config.slug}] Opening {UBER_JOBS_BASE_URL} to establish a browser session")
    await page.goto(f"{UBER_JOBS_BASE_URL}/en/jobs/", wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)


async def fetch_page_html(page, runtime_config, url: str) -> str:
    await _ensure_on_jobs_site(page, runtime_config)
    api_path = _build_api_path(url)
    print(f"[{runtime_config.slug}] Loading API: {UBER_JOBS_BASE_URL}{api_path}")

    for attempt in range(1, MAX_ATTEMPTS + 1):
        status, body = await page.evaluate(_FETCH_JS, api_path)
        if status == 200:
            await page.wait_for_timeout(REQUEST_DELAY_MS)
            return body
        if status == 429 and attempt < MAX_ATTEMPTS:
            print(f"[{runtime_config.slug}] Rate limited (429), retrying in {RETRY_BACKOFF_MS // 1000}s...")
            await page.wait_for_timeout(RETRY_BACKOFF_MS * attempt)
            continue
        raise RuntimeError(f"Uber API request failed with status {status}")

    raise RuntimeError("Uber API request failed")


COMPANY = CompanyDefinition(
    slug="uber",
    display_name="Uber",
    default_search_url=UBER_SEARCH_URL,
    # Results aren't sorted by recency, so regular runs cover the full filtered result set.
    default_max_pages=10,
    default_full_scrape_max_pages=10,
    wait_selectors=(),
    build_search_url=build_search_url,
    parse_jobs=parse_jobs,
    get_total_pages=get_total_pages,
    get_total_results=get_total_results,
    fetch_page_html=fetch_page_html,
    excluded_role_keywords=EXCLUDED_ROLE_KEYWORDS,
    allow_empty_results=True,
)
