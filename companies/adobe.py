from companies.adapters.workday import make_workday_company

COMPANY = make_workday_company(
    slug="adobe",
    display_name="Adobe",
    host="adobe.wd5.myworkdayjobs.com",
    tenant="adobe",
    site="external_experienced",
    applied_facets={
        "jobFamilyGroup": ["591af8b812fa10737af39db3d96eed9f"],  # Engineering
        "locationCountry": ["bc33aa3152ec42d4995f4791a106ed09"],  # United States of America
    },
)
