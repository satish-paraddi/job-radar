from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

from companies.base import CompanyDefinition
from microsoft_parser import RESULTS_PER_PAGE, get_total_pages, get_total_results, parse_jobs

# Microsoft careers runs on Eightfold (apply.careers.microsoft.com). The results page is
# backed by a public JSON API that takes the same filters with a "filter_" prefix.
MICROSOFT_CAREERS_BASE_URL = "https://apply.careers.microsoft.com"
MICROSOFT_CAREERS_PAGE_URL = f"{MICROSOFT_CAREERS_BASE_URL}/careers?domain=microsoft.com"
MICROSOFT_API_URL = f"{MICROSOFT_CAREERS_BASE_URL}/api/pcsx/search"
# No filter_seniority: ~20% of postings have no seniority tag and a seniority filter
# silently drops them. Senior roles are removed by EXCLUDED_ROLE_KEYWORDS instead.
MICROSOFT_SEARCH_URL = (
    f"{MICROSOFT_API_URL}"
    "?domain=microsoft.com"
    "&query="
    "&location=United%20States"
    "&sort_by=timestamp"
    "&filter_career_discipline=Software%20Engineering"
    "&start=0"
)

EXCLUDED_ROLE_KEYWORDS = (
    "principal",
    "senior",
    "staff",
    "director",
    "manager",
    "partner",
    "sr.",
    "sr ",
)


REQUEST_DELAY_MS = 1000
MAX_ATTEMPTS = 3
RETRY_BACKOFF_MS = 5000


def build_search_url(search_url: str, page_num: int) -> str:
    parsed = urlsplit(search_url)
    params = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k != "start"]
    params.append(("start", str((page_num - 1) * RESULTS_PER_PAGE)))
    return urlunsplit(parsed._replace(query=urlencode(params, quote_via=quote)))


async def _ensure_session(page, runtime_config) -> None:
    # The API answers 429 to requests without the session cookies that the careers
    # page sets, so load it once per browser context before calling the API.
    if page.url.startswith(MICROSOFT_CAREERS_BASE_URL):
        return
    print(f"[{runtime_config.slug}] Opening {MICROSOFT_CAREERS_PAGE_URL} to establish a session")
    await page.goto(MICROSOFT_CAREERS_PAGE_URL, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)


async def fetch_page_html(page, runtime_config, url: str) -> str:
    await _ensure_session(page, runtime_config)
    print(f"[{runtime_config.slug}] Loading API: {url}")

    for attempt in range(1, MAX_ATTEMPTS + 1):
        # context.request shares the browser context's cookies.
        response = await page.context.request.get(
            url,
            headers={"accept": "application/json", "referer": MICROSOFT_CAREERS_PAGE_URL},
            timeout=30000,
        )
        if response.ok:
            await page.wait_for_timeout(REQUEST_DELAY_MS)
            return await response.text()
        if response.status == 429 and attempt < MAX_ATTEMPTS:
            print(f"[{runtime_config.slug}] Rate limited (429), retrying in {RETRY_BACKOFF_MS * attempt // 1000}s...")
            await page.wait_for_timeout(RETRY_BACKOFF_MS * attempt)
            continue
        raise RuntimeError(f"Microsoft API request failed with status {response.status}")

    raise RuntimeError("Microsoft API request failed")


COMPANY = CompanyDefinition(
    slug="microsoft",
    display_name="Microsoft",
    default_search_url=MICROSOFT_SEARCH_URL,
    # Results are sorted newest first, so regular runs only need the first few pages.
    # Senior postings now share the result set, so check a few more pages per run.
    default_max_pages=5,
    default_full_scrape_max_pages=40,
    wait_selectors=(),
    build_search_url=build_search_url,
    parse_jobs=parse_jobs,
    get_total_pages=get_total_pages,
    get_total_results=get_total_results,
    fetch_page_html=fetch_page_html,
    excluded_role_keywords=EXCLUDED_ROLE_KEYWORDS,
)
