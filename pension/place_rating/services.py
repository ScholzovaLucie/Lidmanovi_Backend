import re
import urllib.request

from django.conf import settings


def fetch_place_rating():
    url = settings.GOOGLE_MAPS_PLACE_URL
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"},
    )
    with urllib.request.urlopen(req, timeout=8) as response:
        html = response.read().decode("utf-8")

    rating = _extract_rating(html)
    review_count = _extract_review_count(html)

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