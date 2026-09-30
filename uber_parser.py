import json
import math
import re

UBER_JOBS_BASE_URL = "https://jobs.uber.com"
UBER_JOB_URL_TEMPLATE = f"{UBER_JOBS_BASE_URL}/en/jobs/{{job_id}}/"
UBER_RESULTS_PER_PAGE = 10


def parse_jobs(payload: str) -> list[dict]:
    data = _load(payload)
    if data is None:
        return []

    jobs = []
    seen_ids = set()
    for raw_job in data.get("jobs") or []:
        job = _normalize_job(raw_job)
        if job is None or job["key"] in seen_ids:
            continue
        seen_ids.add(job["key"])
        jobs.append(job)
    return jobs


def _load(payload: str) -> dict | None:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _normalize_job(raw_job: dict) -> dict | None:
    if not isinstance(raw_job, dict):
        return None

    job_id = str(raw_job.get("Id") or raw_job.get("Reference") or "").strip()
    title = str(raw_job.get("Title") or "").strip()
    if not job_id or not title:
        return None

    return {
        "key": job_id,
        "job_id": job_id,
        "title": title,
        "team": ", ".join(team for team in raw_job.get("Teams") or [] if team),
        "location": _format_locations(raw_job.get("Locations") or []),
        "posted": str(raw_job.get("DisplayDate") or "").split("T", 1)[0],
        "description": _clean_description(str(raw_job.get("Description") or "")),
        "url": _job_url(raw_job, job_id),
    }


def _job_url(raw_job: dict, job_id: str) -> str:
    for entry in raw_job.get("Urls") or []:
        path = str((entry or {}).get("Url") or "")
        if path and (entry.get("IsDefault") or entry.get("Culture") == "en-us"):
            return f"{UBER_JOBS_BASE_URL}{path}" if path.startswith("/") else path
    return UBER_JOB_URL_TEMPLATE.format(job_id=job_id)


def _format_locations(locations: list) -> str:
    formatted_locations = []
    for location in locations:
        if not isinstance(location, dict):
            continue

        city = str(location.get("City") or "").strip()
        region = str(location.get("Region") or "").strip()
        country = str(location.get("Country") or "").strip()

        if city and region:
            label = f"{city}, {region}"
        elif city and country:
            label = f"{city}, {country}"
        else:
            label = str(location.get("Address") or "").strip() or region or country

        if label and label not in formatted_locations:
            formatted_locations.append(label)

    if not formatted_locations:
        return ""
    if len(formatted_locations) == 1:
        return formatted_locations[0]
    return f"{formatted_locations[0]}; +{len(formatted_locations) - 1} more"


def _clean_description(description: str) -> str:
    text = re.sub(r"<title>.*?</title>", " ", description, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = " ".join(text.split())
    return text[:280].strip()


def get_total_results(payload: str) -> int | None:
    data = _load(payload)
    if data is None:
        return None
    total = data.get("totalJobs")
    return total if isinstance(total, int) else None


def get_total_pages(payload: str) -> int | None:
    data = _load(payload)
    if data is None:
        return None
    total_pages = data.get("totalPages")
    if isinstance(total_pages, int) and total_pages > 0:
        return total_pages

    total_results = get_total_results(payload)
    if total_results is None:
        return None
    page_size = data.get("pageSize") if isinstance(data.get("pageSize"), int) else UBER_RESULTS_PER_PAGE
    return max(1, math.ceil(total_results / max(page_size, 1)))
