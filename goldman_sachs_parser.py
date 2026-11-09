import json
import math

GOLDMAN_SACHS_BASE_URL = "https://higher.gs.com"
PAGE_SIZE = 100


def parse_jobs(payload: str) -> list[dict]:
    jobs = []
    seen_ids = set()
    for raw_job in _role_search(payload).get("items") or []:
        job = _normalize_job(raw_job)
        if job is None or job["key"] in seen_ids:
            continue
        seen_ids.add(job["key"])
        jobs.append(job)
    return jobs


def _role_search(payload: str) -> dict:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return {}
    role_search = ((data or {}).get("data") or {}).get("roleSearch")
    return role_search if isinstance(role_search, dict) else {}


def _normalize_job(raw_job: dict) -> dict | None:
    # /roles/<id> links use the source ID; roleId can be a UUID or "<id>_GS_MID_CAREER".
    job_id = str((raw_job.get("externalSource") or {}).get("sourceId") or raw_job.get("roleId") or "").strip()
    title = str(raw_job.get("jobTitle") or "").strip()
    if not job_id or not title:
        return None

    return {
        "key": job_id,
        "job_id": job_id,
        "title": title,
        "team": str(raw_job.get("division") or "").strip(),
        "location": _format_locations(raw_job.get("locations") or []),
        "posted": "",
        "description": "",
        "url": f"{GOLDMAN_SACHS_BASE_URL}/roles/{job_id}",
    }


def _format_locations(locations: list[dict]) -> str:
    # The search is US-only, so lead with a US office even when the primary one is abroad.
    ordered = sorted(locations, key=lambda loc: (loc.get("country") != "United States", not loc.get("primary")))
    labels = []
    for location in ordered:
        label = ", ".join(part for part in (location.get("city"), location.get("country")) if part)
        if label and label not in labels:
            labels.append(label)

    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    return f"{labels[0]}; +{len(labels) - 1} more"


def get_total_results(payload: str) -> int | None:
    total = _role_search(payload).get("totalCount")
    return total if isinstance(total, int) else None


def get_total_pages(payload: str) -> int | None:
    total_results = get_total_results(payload)
    if total_results is None:
        return None
    return max(1, math.ceil(total_results / PAGE_SIZE))
