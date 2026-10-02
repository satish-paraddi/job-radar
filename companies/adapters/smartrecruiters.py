"""SmartRecruiters career sites via the public Posting API (newest first)."""

import math
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from companies.adapters.common import (
    DEFAULT_EXCLUDED_ROLE_KEYWORDS,
    DEFAULT_EXCLUDED_TITLE_PHRASES,
    iso_date,
    load_json,
)
from companies.base import CompanyDefinition

PAGE_SIZE = 100


def make_smartrecruiters_company(
    *,
    slug: str,
    display_name: str,
    company_id: str,
    filters: dict[str, str],
    default_max_pages: int = 1,
    default_full_scrape_max_pages: int = 10,
    excluded_role_keywords: tuple[str, ...] = DEFAULT_EXCLUDED_ROLE_KEYWORDS,
    excluded_title_phrases: tuple[str, ...] = DEFAULT_EXCLUDED_TITLE_PHRASES,
) -> CompanyDefinition:
    """`filters` are Posting API query params, e.g. {"country": "us", "department": "123"}."""
    api_url = f"https://api.smartrecruiters.com/v1/companies/{company_id}/postings"

    def build_search_url(search_url: str, page_num: int) -> str:
        parsed = urlsplit(search_url)
        params = [(k, v) for k, v in parse_qsl(parsed.query) if k not in {"offset", "limit"}]
        params += [("limit", str(PAGE_SIZE)), ("offset", str((page_num - 1) * PAGE_SIZE))]
        return urlunsplit(parsed._replace(query=urlencode(params)))

    async def fetch_page_html(page, runtime_config, url: str) -> str:
        print(f"[{runtime_config.slug}] Loading SmartRecruiters API: {url}")
        response = await page.context.request.get(url, headers={"accept": "application/json"}, timeout=30000)
        if not response.ok:
            raise RuntimeError(f"{display_name} SmartRecruiters API request failed with status {response.status}")
        return await response.text()

    def parse_jobs(payload: str) -> list[dict]:
        data = load_json(payload) or {}
        jobs = []
        for raw in data.get("content") or []:
            job_id = str(raw.get("id") or "").strip()
            title = str(raw.get("name") or "").strip()
            if not job_id or not title:
                continue
            location = raw.get("location") or {}
            jobs.append(
                {
                    "key": job_id,
                    "job_id": job_id,
                    "title": title,
                    "team": str((raw.get("department") or {}).get("label") or "").strip(),
                    "location": str(location.get("fullLocation") or location.get("city") or "").strip(),
                    "posted": iso_date(raw.get("releasedDate")),
                    "description": "",
                    "url": f"https://jobs.smartrecruiters.com/{company_id}/{job_id}",
                }
            )
        return jobs

    def get_total_results(payload: str) -> int | None:
        total = (load_json(payload) or {}).get("totalFound")
        return total if isinstance(total, int) else None

    def get_total_pages(payload: str) -> int | None:
        total = get_total_results(payload)
        return max(1, math.ceil(total / PAGE_SIZE)) if total is not None else None

    return CompanyDefinition(
        slug=slug,
        display_name=display_name,
        default_search_url=f"{api_url}?{urlencode(filters)}",
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
    )
