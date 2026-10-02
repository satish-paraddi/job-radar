"""Eightfold career sites via the /api/pcsx/search JSON API (newest first)."""

import math
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

from companies.adapters.common import (
    DEFAULT_EXCLUDED_ROLE_KEYWORDS,
    DEFAULT_EXCLUDED_TITLE_PHRASES,
    format_locations,
    is_engineering_title,
    iso_date,
    load_json,
)
from companies.base import CompanyDefinition

PAGE_SIZE = 10  # Fixed by Eightfold.
REQUEST_DELAY_MS = 1000
MAX_ATTEMPTS = 3
RETRY_BACKOFF_MS = 5000


def make_eightfold_company(
    *,
    slug: str,
    display_name: str,
    host: str,
    domain: str,
    params: list[tuple[str, str]],
    search_query: str = "",
    engineering_titles_only: bool = False,
    default_max_pages: int = 5,
    default_full_scrape_max_pages: int = 40,
    excluded_role_keywords: tuple[str, ...] = DEFAULT_EXCLUDED_ROLE_KEYWORDS,
    excluded_title_phrases: tuple[str, ...] = DEFAULT_EXCLUDED_TITLE_PHRASES,
) -> CompanyDefinition:
    """`params` are search filters such as ("location", "United States") or
    ("filter_job_family", "software engineering"). When the site has no usable discipline
    filter, narrow with `search_query` and set `engineering_titles_only`."""
    base_url = f"https://{host}"
    careers_page_url = f"{base_url}/careers?domain={domain}"
    query = [("domain", domain), ("query", search_query), ("sort_by", "timestamp"), *params, ("start", "0")]
    search_url = f"{base_url}/api/pcsx/search?{urlencode(query, quote_via=quote)}"

    def build_search_url(url: str, page_num: int) -> str:
        parsed = urlsplit(url)
        items = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k != "start"]
        items.append(("start", str((page_num - 1) * PAGE_SIZE)))
        return urlunsplit(parsed._replace(query=urlencode(items, quote_via=quote)))

    async def fetch_page_html(page, runtime_config, url: str) -> str:
        # Eightfold may answer 429 to requests without the session cookies that the
        # careers page sets, so load it once per browser context first.
        if not page.url.startswith(base_url):
            print(f"[{runtime_config.slug}] Opening {careers_page_url} to establish a session")
            await page.goto(careers_page_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

        print(f"[{runtime_config.slug}] Loading Eightfold API: {url}")
        for attempt in range(1, MAX_ATTEMPTS + 1):
            response = await page.context.request.get(
                url,
                headers={"accept": "application/json", "referer": careers_page_url},
                timeout=30000,
            )
            if response.ok:
                await page.wait_for_timeout(REQUEST_DELAY_MS)
                return await response.text()
            if response.status == 429 and attempt < MAX_ATTEMPTS:
                print(f"[{runtime_config.slug}] Rate limited (429), retrying...")
                await page.wait_for_timeout(RETRY_BACKOFF_MS * attempt)
                continue
            raise RuntimeError(f"{display_name} Eightfold API request failed with status {response.status}")
        raise RuntimeError(f"{display_name} Eightfold API request failed")

    def _data(payload: str) -> dict:
        data = (load_json(payload) or {}).get("data")
        return data if isinstance(data, dict) else {}

    def parse_jobs(payload: str) -> list[dict]:
        jobs = []
        for raw in _data(payload).get("positions") or []:
            job_id = str(raw.get("displayJobId") or raw.get("atsJobId") or raw.get("id") or "").strip()
            title = str(raw.get("name") or "").strip()
            if not job_id or not title:
                continue
            if engineering_titles_only and not is_engineering_title(title):
                continue
            path = str(raw.get("positionUrl") or f"/careers/job/{raw.get('id')}")
            jobs.append(
                {
                    "key": job_id,
                    "job_id": job_id,
                    "title": title,
                    "team": str(raw.get("department") or "").strip(),
                    "location": format_locations(raw.get("standardizedLocations") or raw.get("locations")),
                    "posted": iso_date(raw.get("postedTs")),
                    "description": "",
                    "url": f"{base_url}{path}" if path.startswith("/") else path,
                }
            )
        return jobs

    def get_total_results(payload: str) -> int | None:
        count = _data(payload).get("count")
        return count if isinstance(count, int) else None

    def get_total_pages(payload: str) -> int | None:
        total = get_total_results(payload)
        return max(1, math.ceil(total / PAGE_SIZE)) if total is not None else None

    return CompanyDefinition(
        slug=slug,
        display_name=display_name,
        default_search_url=search_url,
        default_max_pages=default_max_pages,
        default_full_scrape_max_pages=default_full_scrape_max_pages,
        wait_selectors=(),
        build_search_url=build_search_url,
        parse_jobs=parse_jobs,
        get_total_pages=get_total_pages,
        get_total_results=get_total_results,
        fetch_page_html=fetch_page_html,
        excluded_role_keywords=excluded_role_keywords,
        excluded_title_phrases=excluded_title_phrases,
        # With engineering_titles_only a page can legitimately filter down to zero jobs.
        allow_empty_results=engineering_titles_only,
    )
