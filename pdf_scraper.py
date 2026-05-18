"""
pdf_scraper.py
━━━━━━━━━━━━━━
Downloads and extracts text from NBKR PDF documents.
Strategy:
  1. requests to download PDFs (no Playwright)
  2. pdfplumber for text extraction
  3. Discovers PDF links from website HTML (no browser)
  4. Falls back to curated academic calendar data if PDFs unavailable
  5. Saves structured CSV + JSON
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
import time
import re

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

# Known PDF URLs to try
KNOWN_PDFS = [
    {
        "url": "https://nbkrist.org/Acdemic_calendar/II,III&IVB.Tech.ISem.2025.pdf",
        "label": "Academic Calendar 2025 (II, III & IV B.Tech I Sem)",
        "filename": "academic_calendar_2025.pdf",
    },
    {
        "url": "https://nbkrist.org/Acdemic_calendar/IBTech.ISem.2025.pdf",
        "label": "Academic Calendar 2025 (I B.Tech I Sem)",
        "filename": "academic_calendar_iyr_2025.pdf",
    },
]

# Curated fallback academic calendar data
CALENDAR_FALLBACK = [
    {"page": 1, "content": "NBKR Institute of Science & Technology Academic Calendar 2024-25.", "source": "curated"},
    {"page": 1, "content": "First semester begins in July. Second semester begins in January.", "source": "curated"},
    {"page": 1, "content": "Mid-term examinations are conducted in September and February.", "source": "curated"},
    {"page": 1, "content": "End semester examinations are conducted in November-December and April-May.", "source": "curated"},
    {"page": 1, "content": "Supplementary examinations are held in June-July.", "source": "curated"},
    {"page": 1, "content": "Fresher's day is celebrated in August for first year students.", "source": "curated"},
    {"page": 1, "content": "Annual day and cultural events are held in February-March.", "source": "curated"},
    {"page": 1, "content": "Sports day is conducted in January.", "source": "curated"},
    {"page": 1, "content": "Industrial visits are scheduled in October and March.", "source": "curated"},
    {"page": 1, "content": "Project work and seminars are conducted in the final semester.", "source": "curated"},
    {"page": 1, "content": "NBKR follows JNTU Ananthapur academic regulations and examination pattern.", "source": "curated"},
    {"page": 1, "content": "Attendance requirement is minimum 75% for appearing in end semester examinations.", "source": "curated"},
    {"page": 1, "content": "Internal marks consist of two mid-term exams and assignments.", "source": "curated"},
    {"page": 1, "content": "NBKR Institute offers B.Tech programs in CSE, ECE, EEE, ME, CE, AI&DS, and other branches.", "source": "curated"},
]


def _fetch(url: str, retries: int = 3, delay: float = 2.0, stream: bool = False):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20, stream=stream)
            resp.raise_for_status()
            return resp
        except Exception as e:
            print(f"  ⚠ [{attempt+1}/{retries}] {url}: {e}")
            if attempt < retries - 1:
                time.sleep(delay * (2 ** attempt))
    return None


def _discover_pdf_links(base_url: str = "https://www.nbkrist.org/") -> list:
    """Find PDF links from the website HTML without a browser."""
    print(f"  Discovering PDF links from {base_url}…")
    resp = _fetch(base_url)
    if resp is None:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if ".pdf" in href.lower():
            if not href.startswith("http"):
                href = f"https://www.nbkrist.org/{href.lstrip('/')}"
            label = a.get_text(strip=True) or href.split("/")[-1]
            links.append({"url": href, "label": label})

    print(f"  Found {len(links)} PDF links")
    return links[:8]  # limit to 8 discovered PDFs


def _download_and_extract(url: str, filename: str, label: str = "") -> list:
    """Download a PDF and extract text using pdfplumber."""
    os.makedirs("data/raw", exist_ok=True)
    filepath = os.path.join("data/raw", filename)

    print(f"  Downloading: {url}")
    resp = _fetch(url, stream=True)
    if resp is None:
        return []

    with open(filepath, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"  Saved: {filepath} ({os.path.getsize(filepath)//1024} KB)")

    extracted = []
    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    # Clean up extracted text
                    clean = re.sub(r'\s+', ' ', text.strip())
                    extracted.append({
                        "page":    i + 1,
                        "content": clean,
                        "source":  label or filename,
                    })
        print(f"  Extracted {len(extracted)} pages")
    except ImportError:
        print("  ⚠ pdfplumber not installed — run: pip install pdfplumber")
    except Exception as e:
        print(f"  ⚠ PDF extraction failed: {e}")

    return extracted


def scrape_pdf() -> list:
    print("🔄 Scraping PDF Documents (requests + pdfplumber)…")
    os.makedirs("data/raw", exist_ok=True)

    all_extracted = []

    # 1. Known PDFs
    for pdf_info in KNOWN_PDFS:
        data = _download_and_extract(pdf_info["url"], pdf_info["filename"], pdf_info["label"])
        all_extracted.extend(data)
        time.sleep(0.5)

    # 2. Discovered PDFs from website
    try:
        discovered = _discover_pdf_links()
        for i, link in enumerate(discovered):
            fname = f"discovered_{i+1}.pdf"
            data  = _download_and_extract(link["url"], fname, link["label"])
            all_extracted.extend(data)
            time.sleep(0.5)
    except Exception as e:
        print(f"  ⚠ PDF discovery failed: {e}")

    # Fallback
    if not all_extracted:
        print("  ⚠ No PDFs extracted — using curated academic calendar data")
        all_extracted = CALENDAR_FALLBACK.copy()

    # Save
    df = pd.DataFrame(all_extracted)
    df.to_csv("data/raw/academic_calendar.csv", index=False)
    with open("data/raw/academic_calendar.json", "w", encoding="utf-8") as f:
        json.dump(all_extracted, f, indent=2, ensure_ascii=False)

    print(f"✓ PDF data saved: {len(all_extracted)} pages → data/raw/academic_calendar.csv")
    return all_extracted


if __name__ == "__main__":
    data = scrape_pdf()
    print(f"\nSample entries:")
    for d in data[:3]:
        print(f"  [Page {d.get('page','-')}] {str(d.get('content',''))[:80]}")
