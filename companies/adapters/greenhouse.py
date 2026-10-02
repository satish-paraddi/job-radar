"""Greenhouse job boards via the public boards API (all jobs in a single response)."""

from companies.adapters.common import (
    DEFAULT_EXCLUDED_ROLE_KEYWORDS,
    DEFAULT_EXCLUDED_TITLE_PHRASES,
    is_engineering_title,
    is_us_location,
    iso_date,
    load_json,
)
from companies.base import CompanyDefinition


def _is_us_job(location: str, offices) -> bool:
    if is_us_location(location):
        return True
    return any(
        is_us_location(str(office.get("name") or "")) or is_us_location(str(office.get("location") or ""))
        for office in offices or []
        if isinstance(office, dict)
    )


def make_greenhouse_company(
    *,
    slug: str,
    display_name: str,
    board_token: str,
    excluded_role_keywords: tuple[str, ...] = DEFAULT_EXCLUDED_ROLE_KEYWORDS,
    excluded_title_phrases: tuple[str, ...] = DEFAULT_EXCLUDED_TITLE_PHRASES,
) -> CompanyDefinition:
    """Greenhouse has no reliable server-side filters, so jobs are filtered here to
    engineering titles in US locations."""
    # content=true adds each job's offices, which resolve vague location labels such as
    # "N/A" or "Remote" (e.g. office "US" vs "Canada Locations").
    api_url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"

    def build_search_url(search_url: str, page_num: int) -> str:
        return search_url

    async def fetch_page_html(page, runtime_config, url: str) -> str:
        print(f"[{runtime_config.slug}] Loading Greenhouse API: {url}")
        response = await page.context.request.get(url, headers={"accept": "application/json"}, timeout=60000)
        if not response.ok:
            raise RuntimeError(f"{display_name} Greenhouse API request failed with status {response.status}")
        return await response.text()

    def parse_jobs(payload: str) -> list[dict]:
        data = load_json(payload) or {}
        jobs = []
        for raw in data.get("jobs") or []:
            title = str(raw.get("title") or "").strip()
            location = str((raw.get("location") or {}).get("name") or "").strip()
            job_id = str(raw.get("id") or "").strip()
            if not job_id or not is_engineering_title(title) or not _is_us_job(location, raw.get("offices")):
                continue
            jobs.append(
                {
                    "key": job_id,
                    "job_id": job_id,
                    "title": title,
                    "team": "",
                    "location": location,
                    "posted": iso_date(raw.get("first_published") or raw.get("updated_at")),
                    "description": "",
                    "url": str(raw.get("absolute_url") or "").strip(),
                }
            )
        return jobs

    def get_total_results(payload: str) -> int | None:
        return len(parse_jobs(payload)) if load_json(payload) is not None else None

    def get_total_pages(payload: str) -> int | None:
        return 1

    return CompanyDefinition(
        slug=slug,
        display_name=display_name,
        default_search_url=api_url,
        default_max_pages=1,
        default_full_scrape_max_pages=1,
        wait_selectors=(),
        build_search_url=build_search_url,
        parse_jobs=parse_jobs,
        get_total_pages=get_total_pages,
        get_total_results=get_total_results,
        fetch_page_html=fetch_page_html,
        excluded_role_keywords=excluded_role_keywords,
        excluded_title_phrases=excluded_title_phrases,
        # A board with no current US engineering openings is legitimate, not a breakage.
        allow_empty_results=True,
    )
