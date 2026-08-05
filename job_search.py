import requests
from urllib.parse import quote

# The Apify actor (scraper) we use to get LinkedIn jobs
# Docs: https://apify.com/cheap_scraper/linkedin-job-scraper
ACTOR_ID = "cheap_scraper~linkedin-job-scraper"

# This endpoint runs the scraper and waits for the results in one call
API_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"

# LinkedIn time filter codes (how recently the job was posted)
TIME_FILTERS = {
    "Past hour": "r3600",
    "Past 24 hours": "r86400",
    "Past week": "r604800",
}


# Fetch recent LinkedIn jobs for the given keywords + location
def fetch_linkedin_jobs(apify_token, keywords, location, time_label, max_items=150):
    # Build one LinkedIn search URL per keyword.
    # We use URLs (not the actor's keyword field) because URLs support
    # the "past hour" filter (f_TPR=r3600), which the actor's own
    # publishedAt option does not.
    time_code = TIME_FILTERS[time_label]
    start_urls = []
    for kw in keywords:
        url = (
            "https://www.linkedin.com/jobs/search/"
            f"?keywords={quote(kw)}"
            f"&location={quote(location)}"
            f"&f_TPR={time_code}"
        )
        start_urls.append({"url": url})

    run_input = {
        "startUrls": start_urls,
        "maxItems": max_items,
        "saveOnlyUniqueItems": True,
        "enrichCompanyData": False,  # faster + cheaper
    }

    response = requests.post(
        API_URL,
        params={"token": apify_token},
        json=run_input,
        timeout=300,
    )
    response.raise_for_status()
    return [normalize_job(item) for item in response.json()]


# Different scrapers name their fields differently, so this helper
# tries a few common names and returns a clean, consistent job dict
def first_value(item, keys, default=""):
    for key in keys:
        value = item.get(key)
        if value:
            return value
    return default


def normalize_job(item):
    return {
        "title": first_value(item, ["title", "jobTitle", "position"], "Unknown title"),
        "company": first_value(item, ["companyName", "company", "companyTitle"], "Unknown company"),
        "location": first_value(item, ["location", "jobLocation", "place"]),
        "posted": first_value(item, ["postedTime", "publishedAt", "postedDate", "listedAt"]),
        "url": first_value(item, ["jobUrl", "link", "url"]),
        "description": first_value(item, ["descriptionText", "description", "jobDescription", "descriptionHtml"]),
    }
