"""
portal_scraper.py
━━━━━━━━━━━━━━━━━
Scrapes NBKR Student Portal public pages.
Strategy:
  1. requests + BeautifulSoup (no Playwright needed)
  2. Extracts public-facing info (login page labels, announcements, notices)
  3. Falls back to curated portal knowledge if site is unreachable
  4. Saves structured CSV + JSON
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
import time
import re

PORTAL_URLS = [
    "https://portal.nbkrsac.in/",
    "https://nbkrist.org/",
    "https://www.nbkrist.org/",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Curated fallback knowledge about the portal
PORTAL_FALLBACK = [
    {"tag": "info", "content": "NBKR Student Portal provides online attendance tracking for students and faculty."},
    {"tag": "info", "content": "Students can check their attendance percentage through the NBKR intranet portal."},
    {"tag": "info", "content": "Faculty can enter attendance through the Online Attendance System on the portal."},
    {"tag": "info", "content": "The NBKR portal offers E-Journal publishing and reading for academic research."},
    {"tag": "info", "content": "Online assessments and internal marks are available through the NBKR intranet."},
    {"tag": "info", "content": "Timetables for all departments are accessible via the NBKR portal."},
    {"tag": "info", "content": "Exam duty schedules for faculty are managed through the NBKR intranet system."},
    {"tag": "info", "content": "Students can access their results and grade cards through the student portal."},
    {"tag": "info", "content": "The NBKR portal URL is portal.nbkrsac.in — login with your student/faculty credentials."},
    {"tag": "info", "content": "Fee payment and fee structure details are available on the NBKR student portal."},
    {"tag": "info", "content": "Library resources and e-books can be accessed through the NBKR intranet portal."},
    {"tag": "info", "content": "Hostel allotment and hostel fee details are managed through the NBKR portal."},
    {"tag": "info", "content": "NBKR Institute provides Wi-Fi campus connectivity for students and faculty."},
    {"tag": "info", "content": "Academic calendar and important dates are published on the NBKR portal."},
    {"tag": "info", "content": "Placement cell information and job notifications are posted on the NBKR portal."},
]


def _fetch(url: str, retries: int = 3, delay: float = 2.0):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=12)
            resp.raise_for_status()
            return resp
        except Exception as e:
            print(f"  ⚠ [{attempt+1}/{retries}] {url}: {e}")
            if attempt < retries - 1:
                time.sleep(delay * (2 ** attempt))
    return None


def _extract(url: str, soup: BeautifulSoup) -> list:
    entries = []
    seen = set()
    for tag in soup.find_all(["h1","h2","h3","p","li","td","label","button","a","span"]):
        text = re.sub(r'\s+', ' ', tag.get_text(separator=" ", strip=True))
        if len(text) < 8 or text in seen:
            continue
        seen.add(text)
        entries.append({"tag": tag.name, "content": text, "source": url})
    return entries


def scrape_portal() -> list:
    print("🔄 Scraping Student Portal (requests + BeautifulSoup)…")
    os.makedirs("data/raw", exist_ok=True)

    all_data = []
    any_success = False

    for url in PORTAL_URLS:
        print(f"  Fetching: {url}")
        resp = _fetch(url)
        if resp is None:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        for noise in soup.find_all(["script","style","noscript"]):
            noise.decompose()

        entries = _extract(url, soup)
        if entries:
            all_data.extend(entries)
            any_success = True
            print(f"    → {len(entries)} entries")
        time.sleep(0.5)

    # Fallback if nothing scraped
    if not any_success or len(all_data) < 5:
        print("  ⚠ Live portal scraping failed — using curated portal knowledge")
        all_data = PORTAL_FALLBACK.copy()

    # Deduplicate
    seen_texts = set()
    deduped = []
    for entry in all_data:
        text = entry.get("content","")
        if text not in seen_texts:
            seen_texts.add(text)
            deduped.append(entry)

    # Save
    df = pd.DataFrame(deduped)
    df.to_csv("data/raw/portal_data.csv", index=False)
    with open("data/raw/portal_data.json", "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2, ensure_ascii=False)

    print(f"✓ Portal data saved: {len(deduped)} entries → data/raw/portal_data.csv")
    return deduped


if __name__ == "__main__":
    data = scrape_portal()
    print(f"\nSample entries:")
    for d in data[:5]:
        print(f"  [{d['tag']}] {d['content'][:80]}")
