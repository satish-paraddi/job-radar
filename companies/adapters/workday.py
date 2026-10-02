"""Workday career sites via their public JSON API (POST /wday/cxs/<tenant>/<site>/jobs)."""

import json
import math
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from companies.adapters.common import (
    DEFAULT_EXCLUDED_ROLE_KEYWORDS,
    DEFAULT_EXCLUDED_TITLE_PHRASES,
    load_json,
    relative_posted_date,
)
from companies.base import CompanyDefinition

PAGE_SIZE = 20  # Workday rejects larger page sizes with HTTP 400.
_JOB_ID_RE = re.compile(r"_([A-Z]*R?\d[\w-]*)$")


def make_workday_company(
    *,
    slug: str,
    display_name: str,
    host: str,
    tenant: str,
    site: str,
    applied_facets: dict[str, list[str]],
    default_max_pages: int = 3,
    default_full_scrape_max_pages: int = 50,
    excluded_role_keywords: tuple[str, ...] = DEFAULT_EXCLUDED_ROLE_KEYWORDS,
    excluded_title_phrases: tuple[str, ...] = DEFAULT_EXCLUDED_TITLE_PHRASES,
) -> CompanyDefinition:
    """`host` is e.g. "nvidia.wd5.myworkdayjobs.com". Results come back newest first."""
    api_url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
    public_base = f"https://{host}/en-US/{site}"

    def build_search_url(search_url: str, page_num: int) -> str:
        parsed = urlsplit(search_url)
        params = [(k, v) for k, v in parse_qsl(parsed.query) if k != "offset"]
        params.append(("offset", str((page_num - 1) * PAGE_SIZE)))
        return urlunsplit(parsed._replace(query=urlencode(params)))

    async def fetch_page_html(page, runtime_config, url: str) -> str:
        offset = int(dict(parse_qsl(urlsplit(url).query)).get("offset", "0"))
        print(f"[{runtime_config.slug}] Loading Workday API: {api_url} (offset {offset})")
        response = await page.context.request.post(
            api_url,
            headers={"accept": "application/json", "content-type": "application/json"},
            data=json.dumps(
                {"appliedFacets": applied_facets, "limit": PAGE_SIZE, "offset": offset, "searchText": ""}
            ),
            timeout=30000,
        )
        if not response.ok:
            raise RuntimeError(f"{display_name} Workday API request failed with status {response.status}")
        return await response.text()

    def parse_jobs(payload: str) -> list[dict]:
        data = load_json(payload) or {}
        jobs = []
        for raw in data.get("jobPostings") or []:
            title = str(raw.get("title") or "").strip()
            path = str(raw.get("externalPath") or "").strip()
            bullets = raw.get("bulletFields") or []
            match = _JOB_ID_RE.search(path)
            job_id = str(bullets[0]).strip() if bullets else (match.group(1) if match else path)
            if not title or not job_id:
                continue
            jobs.append(
                {
                    "key": job_id,
                    "job_id": job_id,
                    "title": title,
                    "team": "",
                    "location": str(raw.get("locationsText") or "").strip(),
                    "posted": relative_posted_date(raw.get("postedOn", "")),
                    "description": "",
                    "url": f"{public_base}{path}",
                }
            )
        return jobs

    def get_total_results(payload: str) -> int | None:
        # Workday only reports the real total on the first page; later pages say 0.
        total = (load_json(payload) or {}).get("total")
        return total if isinstance(total, int) and total > 0 else None

    def get_total_pages(payload: str) -> int | None:
        total = get_total_results(payload)
        return max(1, math.ceil(total / PAGE_SIZE)) if total else None

    return CompanyDefinition(
        slug=slug,
        display_name=display_name,
        default_search_url=f"{api_url}?offset=0",
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
