import logging
import re
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

LOGGER = logging.getLogger(__name__)


def fetch_place_rating():
    """
    Returns {"rating": None, "review_count": None} instead of raising if Google Maps is
    unreachable or its markup changed - this backs a public, unauthenticated endpoint and a
    scraping failure shouldn't turn into a 500 for site visitors.
    """
    url = urllib.parse.quote(settings.GOOGLE_MAPS_PLACE_URL, safe=":/?=&@#%+")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"},
    )

    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            html = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        LOGGER.warning("Failed to fetch place rating from Google Maps: %s", exc)
        return {"rating": None, "review_count": None}

    try:
        rating = _extract_rating(html)
        review_count = _extract_review_count(html)
    except (ValueError, AttributeError) as exc:
        LOGGER.warning("Failed to parse place rating from Google Maps response: %s", exc)
        return {"rating": None, "review_count": None}

    return {"rating": rating, "review_count": review_count}


def _extract_rating(html):
    match = re.search(r'"(\d+[.,]\d+)"[^}]*?"[^"]*?recenz', html)
    if match:
        return float(match.group(1).replace(",", "."))
    match = re.search(r'ratingValue["\s:]+(\d+[.,]\d+)', html)
    if match:
        return float(match.group(1).replace(",", "."))
    return None


def _extract_review_count(html):
    match = re.search(r'(\d[\d\s]*)\s*recenz', html)
    if match:
        return int(match.group(1).replace("\xa0", "").replace(" ", ""))
    match = re.search(r'reviewCount["\s:]+(\d+)', html)
    if match:
        return int(match.group(1))
    return None