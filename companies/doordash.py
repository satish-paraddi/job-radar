from companies.adapters.common import DEFAULT_EXCLUDED_TITLE_PHRASES, HARDWARE_TITLE_PHRASES
from companies.adapters.greenhouse import make_greenhouse_company

COMPANY = make_greenhouse_company(
    slug="doordash",
    display_name="DoorDash",
    board_token="doordashusa",
    # DoorDash Labs/Air/Dot post electrical, PCB and other hardware roles.
    excluded_title_phrases=DEFAULT_EXCLUDED_TITLE_PHRASES + HARDWARE_TITLE_PHRASES,
)
