"""
main_scraper.py
━━━━━━━━━━━━━━━
Complete NBKR data scraping pipeline.
Uses requests + BeautifulSoup (no Playwright required).
Run this once to populate data/raw/ before starting the chatbot.
"""

import os
import sys


def main():
    print("=" * 70)
    print("🚀 NBKR Institute — Data Scraping Pipeline v2.0")
    print("   (requests + BeautifulSoup — no browser required)")
    print("=" * 70)

    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/cleaned", exist_ok=True)

    results = {}

    # ── STEP 1: Faculty ──────────────────────────────────────────────────────
    print("\n📚 STEP 1: Faculty Data")
    print("-" * 70)
    try:
        from faculty_scraper_enhanced import scrape_faculty
        results["faculty"] = scrape_faculty()
    except Exception as e:
        print(f"  ✗ Faculty scraping failed: {e}")
        results["faculty"] = []

    # ── STEP 2: Main Website ─────────────────────────────────────────────────
    print("\n🌐 STEP 2: Main Website")
    print("-" * 70)
    try:
        from website_scraper_enhanced import scrape_main_website
        results["website"] = scrape_main_website()
    except Exception as e:
        print(f"  ✗ Website scraping failed: {e}")
        results["website"] = []

    # ── STEP 3: PDF Documents ────────────────────────────────────────────────
    print("\n📄 STEP 3: PDF Documents")
    print("-" * 70)
    try:
        from pdf_scraper import scrape_pdf
        results["pdf"] = scrape_pdf()
    except Exception as e:
        print(f"  ✗ PDF scraping failed: {e}")
        results["pdf"] = []

    # ── STEP 4: Student Portal ───────────────────────────────────────────────
    print("\n🔐 STEP 4: Student Portal")
    print("-" * 70)
    try:
        from portal_scraper import scrape_portal
        results["portal"] = scrape_portal()
    except Exception as e:
        print(f"  ✗ Portal scraping failed: {e}")
        results["portal"] = []

    # ── STEP 5: Preprocess ───────────────────────────────────────────────────
    print("\n🧹 STEP 5: Preprocessing")
    print("-" * 70)
    try:
        from preprocess import preprocess_all_data
        results["cleaned"] = preprocess_all_data()
    except Exception as e:
        print(f"  ✗ Preprocessing failed: {e}")
        results["cleaned"] = []

    # ── STEP 6: Embeddings ───────────────────────────────────────────────────
    print("\n🧠 STEP 6: Embeddings + ChromaDB")
    print("-" * 70)
    try:
        from embeddings import create_embeddings
        create_embeddings()
    except Exception as e:
        print(f"  ✗ Embedding creation failed: {e}")

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("✅ Scraping Pipeline Complete!")
    print("=" * 70)
    print(f"\n📊 Results:")
    print(f"   Faculty entries   : {len(results.get('faculty', []))}")
    print(f"   Website entries   : {len(results.get('website', []))}")
    print(f"   PDF pages         : {len(results.get('pdf', []))}")
    print(f"   Portal entries    : {len(results.get('portal', []))}")
    print(f"   Cleaned documents : {len(results.get('cleaned', []))}")
    print(f"\n📁 Output:")
    print(f"   Raw data    → data/raw/")
    print(f"   Cleaned     → data/cleaned/")
    print(f"   Vector DB   → ./chroma_db/")
    print(f"\n💡 Next: python rag_chatbot.py")
    print()


if __name__ == "__main__":
    main()
