"""
scraper.py — Core scraping logic for product review extraction.
Supports multiple sites with anti-detection headers and graceful fallback.
"""

import re
import time
import random
import logging
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger("scraper")

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Review:
    author: str = "Unknown"
    rating: Optional[float] = None
    date: str = ""
    title: str = ""
    text: str = ""
    verified: bool = False
    url: str = ""

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
    })
    return s


def fetch_page(url: str, retries: int = 3, backoff: float = 2.0) -> Optional[BeautifulSoup]:
    """Fetch a URL with retries and exponential back-off."""
    session = _session()
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Fetching (attempt {attempt}): {url}")
            resp = session.get(url, timeout=15)
            resp.encoding = resp.apparent_encoding or "utf-8"
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, "html.parser")
            elif resp.status_code in (429, 503):
                wait = backoff ** attempt + random.uniform(0, 1)
                logger.warning(f"Rate-limited ({resp.status_code}). Waiting {wait:.1f}s …")
                time.sleep(wait)
            else:
                logger.error(f"HTTP {resp.status_code} for {url}")
                return None
        except requests.RequestException as e:
            logger.error(f"Network error on attempt {attempt}: {e}")
            time.sleep(backoff * attempt)
    return None

# ---------------------------------------------------------------------------
# Site-specific parsers
# ---------------------------------------------------------------------------

def _detect_site(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "amazon" in host:
        return "amazon"
    if "bestbuy" in host:
        return "bestbuy"
    if "books.toscrape" in host:
        return "books_toscrape"
    return "generic"


def _books_http_fallback(url: str) -> str:
    parsed = urlparse(url)
    if "books.toscrape" in parsed.netloc.lower() and parsed.scheme == "https":
        return parsed._replace(scheme="http").geturl()
    return url


def _parse_amazon(soup: BeautifulSoup, url: str) -> list[Review]:
    reviews = []
    for block in soup.select("div[data-hook='review']"):
        r = Review(url=url)
        name_el = block.select_one("span.a-profile-name")
        r.author = name_el.get_text(strip=True) if name_el else "Unknown"

        rating_el = block.select_one("i[data-hook='review-star-rating'] span, "
                                     "i[data-hook='cmps-review-star-rating'] span")
        if rating_el:
            m = re.search(r"([\d.]+)", rating_el.get_text())
            r.rating = float(m.group(1)) if m else None

        date_el = block.select_one("span[data-hook='review-date']")
        r.date = date_el.get_text(strip=True) if date_el else ""

        title_el = block.select_one("a[data-hook='review-title'] span:not(.a-letter-space), "
                                    "span[data-hook='review-title']")
        r.title = title_el.get_text(strip=True) if title_el else ""

        body_el = block.select_one("span[data-hook='review-body'] span")
        r.text = body_el.get_text(strip=True) if body_el else ""

        verified_el = block.select_one("span[data-hook='avp-badge']")
        r.verified = bool(verified_el)

        if r.text:
            reviews.append(r)
    return reviews


def _parse_bestbuy(soup: BeautifulSoup, url: str) -> list[Review]:
    reviews = []
    for block in soup.select("li.review-item, div.ugc-review"):
        r = Review(url=url)
        name_el = block.select_one(".ugc-author, .reviewer-name")
        r.author = name_el.get_text(strip=True) if name_el else "Unknown"

        rating_el = block.select_one(".c-review-average, .rating-score")
        if rating_el:
            m = re.search(r"([\d.]+)", rating_el.get_text())
            r.rating = float(m.group(1)) if m else None

        date_el = block.select_one(".submission-date, time")
        r.date = date_el.get_text(strip=True) if date_el else ""

        title_el = block.select_one(".review-title h4, .ugc-review-title")
        r.title = title_el.get_text(strip=True) if title_el else ""

        body_el = block.select_one(".review-content p, .ugc-review-body")
        r.text = body_el.get_text(strip=True) if body_el else ""

        if r.text:
            reviews.append(r)
    return reviews


def _parse_books_toscrape(soup: BeautifulSoup, url: str) -> list[Review]:
    """
    books.toscrape.com doesn't have reviews per se, but we parse
    'articles' as pseudo-reviews for demo purposes.
    """
    reviews = []
    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    for article in soup.select("article.product_pod"):
        r = Review(url=url)
        title_el = article.select_one("h3 a")
        r.title = title_el["title"] if title_el and title_el.has_attr("title") else ""
        r.author = "Catalogue Entry"

        rating_el = article.select_one("p.star-rating")
        if rating_el:
            cls = [c for c in rating_el["class"] if c != "star-rating"]
            r.rating = float(rating_map.get(cls[0], 0)) if cls else None

        price_el = article.select_one("p.price_color")
        price = price_el.get_text(strip=True) if price_el else "N/A"
        avail_el = article.select_one("p.availability")
        avail = avail_el.get_text(strip=True) if avail_el else ""
        r.text = f"Price: {price}. Availability: {avail}. Book title: {r.title}."
        r.date = "2024"
        reviews.append(r)
    return reviews


def _parse_generic(soup: BeautifulSoup, url: str) -> list[Review]:
    reviews = []
    candidates = soup.find_all(
        lambda tag: tag.name in ("div", "li", "article")
        and any(kw in " ".join(tag.get("class", [])).lower()
                for kw in ("review", "comment", "testimonial", "feedback"))
    )
    for block in candidates[:20]:
        text = block.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        if len(text) > 40:
            reviews.append(Review(text=text[:1500], url=url))
    return reviews


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scrape_reviews(url: str) -> list[Review]:
    """Scrape reviews from a product URL. Returns list of Review objects."""
    original_url = url
    soup = fetch_page(url)
    if soup is None:
        logger.error("Could not fetch page.")
        return []

    site = _detect_site(url)
    logger.info(f"Detected site type: {site}")

    parsers = {
        "amazon": _parse_amazon,
        "bestbuy": _parse_bestbuy,
        "books_toscrape": _parse_books_toscrape,
        "generic": _parse_generic,
    }
    reviews = parsers[site](soup, url)

    if not reviews and site == "books_toscrape":
        fallback_url = _books_http_fallback(original_url)
        if fallback_url != original_url:
            logger.warning(
                "No catalogue entries found over HTTPS. Retrying books.toscrape with HTTP."
            )
            soup = fetch_page(fallback_url)
            if soup is not None:
                reviews = _parse_books_toscrape(soup, fallback_url)
                url = fallback_url

    logger.info(f"Total reviews scraped: {len(reviews)}")

    if not reviews and site == "amazon":
        logger.warning("Amazon likely blocked the request. Use --mock for demo data.")

    return reviews
