import json
import math
from datetime import datetime, timezone

MICROSOFT_BASE_URL = "https://apply.careers.microsoft.com"
RESULTS_PER_PAGE = 10


def parse_jobs(payload: str) -> list[dict]:
    data = _load_data(payload)
    if data is None:
        return []

    jobs = []
    seen_ids = set()
    for raw_job in data.get("positions") or []:
        job = _normalize_job(raw_job)
        if job is None or job["key"] in seen_ids:
            continue
        seen_ids.add(job["key"])
        jobs.append(job)
    return jobs


def _load_data(payload: str) -> dict | None:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    nested = data.get("data")
    return nested if isinstance(nested, dict) else None


def _normalize_job(raw_job: dict) -> dict | None:
    if not isinstance(raw_job, dict):
        return None

    job_id = str(raw_job.get("displayJobId") or raw_job.get("atsJobId") or raw_job.get("id") or "").strip()
    title = str(raw_job.get("name") or "").strip()
    if not job_id or not title:
        return None

    position_url = str(raw_job.get("positionUrl") or "").strip()
    if not position_url and raw_job.get("id"):
        position_url = f"/careers/job/{raw_job['id']}"

    return {
        "key": job_id,
        "job_id": job_id,
        "title": title,
        "team": str(raw_job.get("department") or "").strip(),
        "location": _format_locations(raw_job.get("standardizedLocations") or raw_job.get("locations") or []),
        "posted": _format_timestamp(raw_job.get("postedTs")),
        "description": "",
        "url": f"{MICROSOFT_BASE_URL}{position_url}" if position_url.startswith("/") else position_url,
    }


def _format_locations(locations: list) -> str:
    labels = []
    for location in locations:
        label = str(location or "").strip()
        if label and label not in labels:
            labels.append(label)

    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    return f"{labels[0]}; +{len(labels) - 1} more"


def _format_timestamp(value) -> str:
    if not isinstance(value, (int, float)) or value <= 0:
        return ""
    return datetime.fromtimestamp(value, tz=timezone.utc).strftime("%Y-%m-%d")


def get_total_results(payload: str) -> int | None:
    data = _load_data(payload)
    if data is None:
        return None
    count = data.get("count")
    return count if isinstance(count, int) else None


def get_total_pages(payload: str) -> int | None:
    total_results = get_total_results(payload)
    if total_results is None:
        return None
    return max(1, math.ceil(total_results / RESULTS_PER_PAGE))
