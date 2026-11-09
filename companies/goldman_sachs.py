import json
from urllib.parse import parse_qsl, urlsplit

from companies.base import CompanyDefinition
from goldman_sachs_parser import PAGE_SIZE, get_total_pages, get_total_results, parse_jobs

# higher.gs.com is a client-rendered app backed by this public GraphQL API, which is
# queried directly because the rendered page is not reliably available to the scraper.
GOLDMAN_SACHS_API_URL = "https://api-higher.gs.com/gateway/api/v1/graphql"

GET_ROLES_QUERY = """
query GetRoles($searchQueryInput: RoleSearchQueryInput!) {
  roleSearch(searchQueryInput: $searchQueryInput) {
    totalCount
    items {
      roleId
      jobTitle
      division
      locations { primary city state country }
      externalSource { sourceId }
    }
  }
}
"""

SEARCH_FILTERS = [
    {"filterCategoryType": "JOB_FUNCTION", "filters": [{"filter": "Software Engineering", "subFilters": []}]},
    {
        "filterCategoryType": "EXPERIENCE_LEVEL",
        "filters": [{"filter": "Analyst", "subFilters": []}, {"filter": "Associate", "subFilters": []}],
    },
    {"filterCategoryType": "LOCATION", "filters": [{"filter": "United States", "subFilters": []}]},
]

EXCLUDED_ROLE_KEYWORDS = (
    "vice president",
    "executive director",
    "managing director",
    "partner",
)


def build_search_url(search_url: str, page_num: int) -> str:
    return f"{search_url.split('?', 1)[0]}?page={page_num}"


async def fetch_page_html(page, runtime_config, url: str) -> str:
    page_num = int(dict(parse_qsl(urlsplit(url).query)).get("page", "1"))
    print(f"[{runtime_config.slug}] Loading GraphQL API: {GOLDMAN_SACHS_API_URL} (page {page_num})")
    response = await page.context.request.post(
        GOLDMAN_SACHS_API_URL,
        headers={
            "content-type": "application/json",
            "origin": "https://higher.gs.com",
            "referer": "https://higher.gs.com/",
        },
        data=json.dumps(
            {
                "operationName": "GetRoles",
                "query": GET_ROLES_QUERY,
                "variables": {
                    "searchQueryInput": {
                        "page": {"pageSize": PAGE_SIZE, "pageNumber": page_num - 1},
                        "sort": {"sortStrategy": "POSTED_DATE", "sortOrder": "DESC"},
                        "filters": SEARCH_FILTERS,
                        "experiences": ["EARLY_CAREER", "PROFESSIONAL"],
                        "searchTerm": "",
                    }
                },
            }
        ),
        timeout=30000,
    )
    if not response.ok:
        raise RuntimeError(f"Goldman Sachs API request failed with status {response.status}")

    body = await response.text()
    errors = json.loads(body).get("errors")
    if errors:
        raise RuntimeError(f"Goldman Sachs API returned errors: {str(errors)[:300]}")
    return body


COMPANY = CompanyDefinition(
    slug="goldman-sachs",
    display_name="Goldman Sachs",
    default_search_url=f"{GOLDMAN_SACHS_API_URL}?page=1",
    default_max_pages=1,
    default_full_scrape_max_pages=5,
    wait_selectors=(),
    build_search_url=build_search_url,
    fetch_page_html=fetch_page_html,
    parse_jobs=parse_jobs,
    get_total_pages=get_total_pages,
    get_total_results=get_total_results,
    excluded_role_keywords=EXCLUDED_ROLE_KEYWORDS,
)
