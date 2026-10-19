from companies.adapters.workday import make_workday_company

EXCLUDED_ROLE_KEYWORDS = (
    "principal",
    "senior",
    "staff",
    "lead",
    "director",
    "manager",
    "architect",
    "pmts",
    "smts",
    "lmts",
    "sr.",
)

COMPANY = make_workday_company(
    slug="salesforce",
    display_name="Salesforce",
    host="salesforce.wd12.myworkdayjobs.com",
    tenant="salesforce",
    site="external_career_site",
    applied_facets={
        # United States
        "CF_-_REC_-_LRV_-_Job_Posting_Anchor_-_Country_from_Job_Posting_Location_Extended": [
            "bc33aa3152ec42d4995f4791a106ed09"
        ],
        "timeType": ["0e28126347c3100fe3b402cf26290000"],  # Full time
        "jobFamilyGroup": ["14fa3452ec7c1011f90d0002a2100000"],  # Software Engineering
        "workerSubType": ["3a910852b2c31010f48d2bbc8b020000"],  # Regular
    },
    # Salesforce's Workday throttles hard (429s even 5s apart). Results are newest first,
    # so regular runs fetch only the 20 newest; full scrapes page slowly with retries.
    default_max_pages=1,
    default_full_scrape_max_pages=10,
    request_delay_ms=5000,
    excluded_role_keywords=EXCLUDED_ROLE_KEYWORDS,
)
