from companies.adapters.smartrecruiters import make_smartrecruiters_company

COMPANY = make_smartrecruiters_company(
    slug="servicenow",
    display_name="ServiceNow",
    company_id="ServiceNow",
    filters={
        "country": "us",
        "department": "2294038",  # Engineering, Infrastructure and Operations
    },
)
