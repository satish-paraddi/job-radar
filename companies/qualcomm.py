from companies.adapters.eightfold import make_eightfold_company

COMPANY = make_eightfold_company(
    slug="qualcomm",
    display_name="Qualcomm",
    host="careers.qualcomm.com",
    domain="qualcomm.com",
    params=[
        ("location", "United States"),
        ("filter_job_family", "software engineering"),
        ("filter_job_family", "software applications engineering"),
    ],
)
