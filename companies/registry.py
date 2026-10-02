from companies.adobe import COMPANY as ADOBE
from companies.amazon import COMPANY as AMAZON
from companies.apple import COMPANY as APPLE
from companies.base import CompanyDefinition
from companies.capital_one import COMPANY as CAPITAL_ONE
from companies.cvs import COMPANY as CVS
from companies.cvs_wd import COMPANY as CVS_WD
from companies.doordash import COMPANY as DOORDASH
from companies.goldman_sachs import COMPANY as GOLDMAN_SACHS
from companies.google import COMPANY as GOOGLE
from companies.lyft import COMPANY as LYFT
from companies.meta import COMPANY as META
from companies.microsoft import COMPANY as MICROSOFT
from companies.nvidia import COMPANY as NVIDIA
from companies.paypal import COMPANY as PAYPAL
from companies.qualcomm import COMPANY as QUALCOMM
from companies.salesforce import COMPANY as SALESFORCE
from companies.servicenow import COMPANY as SERVICENOW
from companies.stripe import COMPANY as STRIPE
from companies.uber import COMPANY as UBER

COMPANIES: dict[str, CompanyDefinition] = {
    ADOBE.slug: ADOBE,
    AMAZON.slug: AMAZON,
    APPLE.slug: APPLE,
    CAPITAL_ONE.slug: CAPITAL_ONE,
    CVS.slug: CVS,
    CVS_WD.slug: CVS_WD,
    DOORDASH.slug: DOORDASH,
    GOLDMAN_SACHS.slug: GOLDMAN_SACHS,
    GOOGLE.slug: GOOGLE,
    LYFT.slug: LYFT,
    META.slug: META,
    MICROSOFT.slug: MICROSOFT,
    NVIDIA.slug: NVIDIA,
    PAYPAL.slug: PAYPAL,
    QUALCOMM.slug: QUALCOMM,
    SALESFORCE.slug: SALESFORCE,
    SERVICENOW.slug: SERVICENOW,
    STRIPE.slug: STRIPE,
    UBER.slug: UBER,
}


def get_company(slug: str) -> CompanyDefinition:
    normalized_slug = slug.strip().lower()
    try:
        return COMPANIES[normalized_slug]
    except KeyError as exc:
        supported = ", ".join(sorted(COMPANIES))
        raise ValueError(f"Unsupported company '{slug}'. Supported companies: {supported}") from exc


def list_companies() -> list[str]:
    return sorted(COMPANIES)