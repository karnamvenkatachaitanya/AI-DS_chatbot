"""
faculty_scraper_enhanced.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scrapes AI & DS faculty from NBKR IRINS portal.
Strategy:
  1. requests + BeautifulSoup (fast, no browser needed)
  2. Multiple CSS selector patterns to handle site changes
  3. Retry with exponential back-off
  4. Falls back to the curated aids_faculty_data.json if scraping fails
  5. Saves structured JSON + CSV
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
import time
import re

URLS = [
    "https://nbkrist.irins.org/faculty/index/Department+of++AI+and+DS",
    "https://nbkrist.irins.org/faculty/index/Department+of+AI+and+DS",
    "https://nbkrist.irins.org/faculty/index/AI+and+DS",
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

# Designation normalisation map
DESIG_MAP = {
    "hod": "Head of the Department",
    "head": "Head of the Department",
    "professor": "Professor",
    "associate professor": "Associate Professor",
    "asst. professor": "Assistant Professor",
    "assistant professor": "Assistant Professor",
    "asst professor": "Assistant Professor",
    "lecturer": "Assistant Professor",
}

def _normalise_designation(raw: str) -> str:
    r = raw.lower().strip()
    for key, val in DESIG_MAP.items():
        if key in r:
            return val
    return raw.strip().title()


def _fetch_with_retry(url: str, retries: int = 3, delay: float = 2.0):
    """GET with retry + exponential back-off."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            return resp
        except Exception as e:
            print(f"  ⚠ Attempt {attempt+1}/{retries} failed for {url}: {e}")
            if attempt < retries - 1:
                time.sleep(delay * (2 ** attempt))
    return None


def _parse_irins_page(soup: BeautifulSoup) -> list:
    """
    Parse IRINS faculty listing page.
    Tries multiple selector strategies.
    """
    faculty = []

    # Strategy 1: profile cards with name + designation
    cards = soup.select(".profile-card, .faculty-card, .card, .faculty-item, .member-card")
    if cards:
        for card in cards:
            name_el  = card.select_one("h3, h4, .name, .faculty-name, strong")
            desig_el = card.select_one(".designation, .title, .position, p")
            spec_el  = card.select_one(".specialization, .research, .expertise")
            if name_el:
                entry = {
                    "name":           name_el.get_text(strip=True),
                    "designation":    _normalise_designation(desig_el.get_text(strip=True)) if desig_el else "",
                    "specialization": spec_el.get_text(strip=True) if spec_el else "",
                }
                if entry["name"]:
                    faculty.append(entry)
        if faculty:
            return faculty

    # Strategy 2: table rows
    rows = soup.select("table tr")
    for row in rows:
        cells = row.find_all(["td","th"])
        if len(cells) >= 2:
            name = cells[0].get_text(strip=True)
            desig = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            spec  = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            if name and len(name) > 3 and not name.lower().startswith(("s.no","sl","name","#")):
                faculty.append({
                    "name":           name,
                    "designation":    _normalise_designation(desig),
                    "specialization": spec,
                })
        if faculty:
            return faculty

    # Strategy 3: any div/li with a name-like heading
    for el in soup.select("div, li, article"):
        heading = el.find(["h2","h3","h4","strong","b"])
        if not heading:
            continue
        name = heading.get_text(strip=True)
        # Filter: must look like a person name (2+ words, no numbers)
        if len(name.split()) < 2 or re.search(r'\d', name):
            continue
        # Grab next sibling text as designation
        desig_text = ""
        for sib in heading.find_next_siblings(["p","span","div"], limit=2):
            t = sib.get_text(strip=True)
            if t and len(t) < 80:
                desig_text = t
                break
        faculty.append({
            "name":           name,
            "designation":    _normalise_designation(desig_text),
            "specialization": "",
        })

    return faculty


def scrape_faculty() -> list:
    print("🔄 Scraping Faculty Data (requests + BeautifulSoup)…")
    os.makedirs("data/raw", exist_ok=True)

    faculty_data = []

    for url in URLS:
        print(f"  Trying: {url}")
        resp = _fetch_with_retry(url)
        if resp is None:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        faculty_data = _parse_irins_page(soup)

        # Validate: entries must have real names (not just department headings)
        valid = [f for f in faculty_data
                 if f.get("name","") and
                 "department" not in f.get("name","").lower() and
                 len(f.get("name","").split()) >= 2]

        if valid:
            faculty_data = valid
            print(f"  ✓ Found {len(faculty_data)} valid faculty entries from {url}")
            break
        else:
            print(f"  ⚠ No valid faculty names found at {url} (JS-rendered page), trying next…")

    # ── Fallback: use curated JSON ────────────────────────────────────────
    if not faculty_data:
        print("  ⚠ Live scraping failed — loading curated aids_faculty_data.json")
        if os.path.exists("aids_faculty_data.json"):
            with open("aids_faculty_data.json", "r", encoding="utf-8") as f:
                faculty_data = json.load(f)
            print(f"  ✓ Loaded {len(faculty_data)} entries from curated data")
        else:
            print("  ✗ No fallback data available")
            return []

    # ── Save ──────────────────────────────────────────────────────────────
    df = pd.DataFrame(faculty_data)
    df.to_csv("data/raw/faculty_data.csv", index=False)
    with open("data/raw/faculty_data.json", "w", encoding="utf-8") as f:
        json.dump(faculty_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Faculty data saved: {len(faculty_data)} entries → data/raw/faculty_data.csv")
    return faculty_data


if __name__ == "__main__":
    data = scrape_faculty()
    print(f"\nSample entries:")
    for d in data[:3]:
        print(f"  {d}")
