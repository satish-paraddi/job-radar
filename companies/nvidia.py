from companies.adapters.common import DEFAULT_EXCLUDED_TITLE_PHRASES, HARDWARE_TITLE_PHRASES
from companies.adapters.workday import make_workday_company

COMPANY = make_workday_company(
    slug="nvidia",
    display_name="NVIDIA",
    host="nvidia.wd5.myworkdayjobs.com",
    tenant="nvidia",
    site="NVIDIAExternalCareerSite",
    applied_facets={
        "jobFamilyGroup": ["0c40f6bd1d8f10ae43ffaefd46dc7e78"],  # Engineering
        "locationHierarchy1": ["2fcb99c455831013ea52fb338f2932d8"],  # United States
    },
    # NVIDIA posts ~20 US engineering roles a day.
    default_max_pages=4,
    # The Engineering category also covers ASIC/PCB/hardware roles.
    excluded_title_phrases=DEFAULT_EXCLUDED_TITLE_PHRASES + HARDWARE_TITLE_PHRASES,
)
