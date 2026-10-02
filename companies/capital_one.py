from companies.adapters.workday import make_workday_company

COMPANY = make_workday_company(
    slug="capital-one",
    display_name="Capital One",
    host="capitalone.wd12.myworkdayjobs.com",
    tenant="capitalone",
    site="Capital_One",
    applied_facets={
        "jobFamilyGroup": ["23c40d87cd84100035bd7d9296540000"],  # Software-Engineering
    },
)
