"""
website_scraper_enhanced.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scrapes NBKR main website + department pages.
Strategy:
  1. requests + BeautifulSoup (no browser dependency)
  2. Crawls multiple NBKR pages (main, departments, notices, academics)
  3. Deduplicates and cleans text
  4. Retry with back-off on failures
  5. Saves structured CSV + JSON
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
import time
import re
from urllib.parse import urljoin, urlparse

SEED_URLS = [
    "https://www.nbkrist.org/",
    "https://www.nbkrist.org/departments.php",
    "https://www.nbkrist.org/academics.php",
    "https://www.nbkrist.org/admissions.php",
    "https://www.nbkrist.org/facilities.php",
    "https://www.nbkrist.org/placements.php",
    "https://www.nbkrist.org/about.php",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Tags worth extracting text from
CONTENT_TAGS = ["h1","h2","h3","h4","p","li","td","th","span","a","blockquote"]

# Minimum text length to keep
MIN_LEN = 10

# Noise patterns to skip
NOISE_PATTERNS = re.compile(
    r'^(home|about|contact|login|logout|register|search|menu|navigation|'
    r'copyright|all rights reserved|powered by|follow us|social media|'
    r'click here|read more|learn more|back to top|\d+)$',
    re.IGNORECASE
)


def _fetch(url: str, retries: int = 3, delay: float = 2.0):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            return resp
        except Exception as e:
            print(f"  ⚠ [{attempt+1}/{retries}] {url}: {e}")
            if attempt < retries - 1:
                time.sleep(delay * (2 ** attempt))
    return None


def _clean(text: str) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[^\x20-\x7E\u00A0-\uFFFF]', '', text)
    return text


def _extract_page(url: str, soup: BeautifulSoup) -> list:
    """Extract meaningful text entries from a parsed page."""
    entries = []
    seen = set()

    for tag in soup.find_all(CONTENT_TAGS):
        text = _clean(tag.get_text(separator=" ", strip=True))
        if len(text) < MIN_LEN:
            continue
        if text in seen:
            continue
        if NOISE_PATTERNS.match(text):
            continue
        seen.add(text)

        href = tag.get("href","") if tag.name == "a" else ""
        entries.append({
            "source": url,
            "tag":    tag.name,
            "text":   text,
            "href":   href,
        })

    return entries


def _discover_internal_links(base_url: str, soup: BeautifulSoup, limit: int = 10) -> list:
    """Find internal links on the page to crawl further."""
    base_domain = urlparse(base_url).netloc
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        if parsed.netloc == base_domain and parsed.scheme in ("http","https"):
            if full not in links and "#" not in full:
                links.append(full)
    return links[:limit]


def scrape_main_website() -> list:
    print("🔄 Scraping NBKR Website (requests + BeautifulSoup)…")
    os.makedirs("data/raw", exist_ok=True)

    all_data = []
    visited  = set()

    urls_to_visit = list(SEED_URLS)

    for url in urls_to_visit:
        if url in visited:
            continue
        visited.add(url)

        print(f"  Fetching: {url}")
        resp = _fetch(url)
        if resp is None:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove nav/footer/script noise
        for noise in soup.find_all(["nav","footer","script","style","noscript","header"]):
            noise.decompose()

        entries = _extract_page(url, soup)
        all_data.extend(entries)
        print(f"    → {len(entries)} entries")

        # Discover more pages from the main page only
        if url == SEED_URLS[0]:
            extra = _discover_internal_links(url, soup, limit=8)
            for link in extra:
                if link not in visited and link not in urls_to_visit:
                    urls_to_visit.append(link)

        time.sleep(0.5)  # polite crawl delay

    # Deduplicate by text
    seen_texts = set()
    deduped = []
    for entry in all_data:
        if entry["text"] not in seen_texts:
            seen_texts.add(entry["text"])
            deduped.append(entry)

    # Save
    df = pd.DataFrame(deduped)
    df.to_csv("data/raw/main_website.csv", index=False)
    with open("data/raw/main_website.json", "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2, ensure_ascii=False)

    print(f"✓ Website data saved: {len(deduped)} entries → data/raw/main_website.csv")
    return deduped


if __name__ == "__main__":
    data = scrape_main_website()
    print(f"\nSample entries:")
    for d in data[:5]:
        print(f"  [{d['tag']}] {d['text'][:80]}")
