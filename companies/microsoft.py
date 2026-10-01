from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

from companies.base import CompanyDefinition
from microsoft_parser import RESULTS_PER_PAGE, get_total_pages, get_total_results, parse_jobs

# Microsoft careers runs on Eightfold (apply.careers.microsoft.com). The results page is
# backed by a public JSON API that takes the same filters with a "filter_" prefix.
MICROSOFT_API_URL = "https://apply.careers.microsoft.com/api/pcsx/search"
MICROSOFT_SEARCH_URL = (
    f"{MICROSOFT_API_URL}"
    "?domain=microsoft.com"
    "&query="
    "&location=United%20States"
    "&sort_by=timestamp"
    "&filter_career_discipline=Software%20Engineering"
    "&filter_seniority=Entry"
    "&filter_seniority=Mid-Level"
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


def build_search_url(search_url: str, page_num: int) -> str:
    parsed = urlsplit(search_url)
    params = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k != "start"]
    params.append(("start", str((page_num - 1) * RESULTS_PER_PAGE)))
    return urlunsplit(parsed._replace(query=urlencode(params, quote_via=quote)))


async def fetch_page_html(page, runtime_config, url: str) -> str:
    print(f"[{runtime_config.slug}] Loading API: {url}")
    response = await page.context.request.get(
        url,
        headers={"accept": "application/json", "user-agent": "Mozilla/5.0"},
        timeout=30000,
    )
    if not response.ok:
        raise RuntimeError(f"Microsoft API request failed with status {response.status}")
    return await response.text()


COMPANY = CompanyDefinition(
    slug="microsoft",
    display_name="Microsoft",
    default_search_url=MICROSOFT_SEARCH_URL,
    # Results are sorted newest first, so regular runs only need the first few pages.
    default_max_pages=3,
    default_full_scrape_max_pages=30,
    wait_selectors=(),
    build_search_url=build_search_url,
    parse_jobs=parse_jobs,
    get_total_pages=get_total_pages,
    get_total_results=get_total_results,
    fetch_page_html=fetch_page_html,
    excluded_role_keywords=EXCLUDED_ROLE_KEYWORDS,
)
