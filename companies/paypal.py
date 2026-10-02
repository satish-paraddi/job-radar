from companies.adapters.eightfold import make_eightfold_company

COMPANY = make_eightfold_company(
    slug="paypal",
    display_name="PayPal",
    host="paypal.eightfold.ai",
    domain="paypal.com",
    params=[("location", "United States")],
    # PayPal's site has no discipline filter, so search "engineer" and keep engineering titles.
    search_query="engineer",
    engineering_titles_only=True,
)
