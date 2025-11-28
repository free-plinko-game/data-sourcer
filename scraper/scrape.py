#!/usr/bin/env python3
"""
Casino Scraper using Selenium + BeautifulSoup + GPT
Run this separately from the web app to scrape casino sites.

Usage:
    python scrape.py                  # Scrape all configured URLs
    python scrape.py --all            # Scrape all configured URLs
    python scrape.py --casino "Bet365" # Scrape a specific casino by name
    python scrape.py --url "https://..." --casino-id "uuid" # Scrape a specific URL
"""

import os
import sys
import json
import time
import argparse
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from openai import OpenAI
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize clients
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# GPT extraction prompt
EXTRACTION_PROMPT = """You are an expert data extraction agent. Extract high-level general information about the casino from this review content.

Note: Different websites may use varied terminology. You should recognize synonyms and alternate phrasings for all fields.

Examples:
- "brand" = site name, logo text, brand header, title tag (e.g. "Bet365", "LeoVegas")
- "Terms & Conditions" = Rules, User Agreement, General Terms, Terms of Use
- "Game Availability" = Available Games, Game Selection, Casino Library, Playable Games
- "Casino Reputation" = Trust Score, Industry Reputation, Reviews, Background
- "Customer Support" = Help, Support Center, Contact Us, Live Chat, FAQs
- "Mobile & App Availability" = Mobile App, iOS/Android App, Mobile Casino, App Download
- "Responsible Gambling Page/Tools" = Safe Play, Player Protection, Gambling Controls, Self-Exclusion Tools
- "Privacy Policy" = Data Use, Security Policy, Information Policy, Cookies & Privacy
- "AML (Anti-Money Laundering)" = Money Laundering Prevention, AML Policy, Anti-Fraud
- "KYC (Know Your Customer) Details" = Verification Process, Identity Check, Account Validation
- "Providers" = Game Developers, Software Providers, Studios, Game Vendors
- "Year Established" = Founded, Since, In Operation Since
- "Payout – Speed/%" = Withdrawal Times, RTP, Payout Rate, Cashout Duration
- "Maximum/Minimum Deposit/Withdrawal" = Payment Limits, Deposit Range, Withdrawal Range
- "Number of Games/Pokies" = Game Count, Slot Library, Pokie Total, Number of Titles
- "Player Protection & Safety" = Responsible Gaming, Security Features, Anti-Gambling Harm
- "Number of Players" = User Base, Player Count, Registered Users
- "Bonus Offers Breakdown" = Welcome Bonus, Offers Summary, Promotions, Bonus Types
- "source_url" = The page URL where this review content was extracted

If exact matches are not found, infer values based on context, phrasing, or implied meaning. If completely absent, return null.

Return a single JSON object using these exact keys. Use null only if absolutely no reasonable inference can be made.

Casino Review Content:
{html}

Do not explain or describe your response. Only return a valid JSON object."""


def get_driver():
    """Create a Selenium WebDriver with stealth settings."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Additional stealth
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver


def fetch_page(url: str) -> str:
    """Fetch a page using Selenium and return the HTML."""
    driver = get_driver()
    try:
        print(f"  Fetching: {url}")
        driver.get(url)
        time.sleep(3)  # Wait for dynamic content
        html = driver.page_source
        return html
    finally:
        driver.quit()


def clean_html(html: str) -> str:
    """Clean HTML using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted elements
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "link", "meta"]):
        tag.decompose()

    # Remove common non-content elements
    for selector in ["[class*='cookie']", "[class*='popup']", "[class*='modal']",
                     "[class*='advertisement']", "[class*='ad-']", "[id*='cookie']"]:
        for el in soup.select(selector):
            el.decompose()

    # Get text
    text = soup.get_text(separator=" ", strip=True)

    # Clean whitespace
    text = " ".join(text.split())

    # Limit length for GPT
    return text[:50000]


def extract_with_gpt(text: str, source_url: str) -> dict:
    """Extract structured data using GPT."""
    print("  Extracting data with GPT...")

    prompt = EXTRACTION_PROMPT.format(html=text)

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=2000
    )

    content = response.choices[0].message.content
    data = json.loads(content)
    data["source_url"] = source_url
    return data


def scrape_url(casino_id: str, url: str, config_id: str = None) -> dict:
    """Scrape a single URL and save to Supabase."""

    # Create processing record
    insert_data = {
        "casino_id": casino_id,
        "source_url": url,
        "status": "processing"
    }
    if config_id:
        insert_data["config_id"] = config_id

    result = supabase.table("scraped_data").insert(insert_data).execute()
    record_id = result.data[0]["id"]

    try:
        # Fetch page
        html = fetch_page(url)

        # Clean HTML
        cleaned = clean_html(html)

        # Extract with GPT
        extracted = extract_with_gpt(cleaned, url)

        # Update record
        supabase.table("scraped_data").update({
            "raw_html": html,
            "extracted_data": extracted,
            "status": "completed",
            "processed_at": "now()"
        }).eq("id", record_id).execute()

        print(f"  ✓ Success: {url}")
        return {"success": True, "data": extracted}

    except Exception as e:
        print(f"  ✗ Error: {e}")
        supabase.table("scraped_data").update({
            "status": "failed",
            "error_message": str(e)
        }).eq("id", record_id).execute()
        return {"success": False, "error": str(e)}


def scrape_all_configs():
    """Scrape all active URLs from scrape_configs table."""
    print("\n=== Batch Scraper ===\n")

    # Get all active scrape configs with casino info
    result = supabase.table("scrape_configs")\
        .select("id, casino_id, name, page_url, casinos(name)")\
        .eq("is_active", True)\
        .execute()

    configs = result.data
    total = len(configs)

    if total == 0:
        print("No active scrape URLs configured.")
        print("Add URLs in the web app: Casinos > Edit > Scrape URLs")
        return

    print(f"Found {total} active URLs to scrape\n")

    success = 0
    failed = 0

    for i, config in enumerate(configs, 1):
        casino_name = config.get("casinos", {}).get("name", "Unknown")
        print(f"[{i}/{total}] {casino_name} - {config['name']}")

        result = scrape_url(
            casino_id=config["casino_id"],
            url=config["page_url"],
            config_id=config["id"]
        )

        if result["success"]:
            success += 1
        else:
            failed += 1

        print()

    print(f"\n=== Batch Complete ===")
    print(f"Success: {success}/{total}")
    print(f"Failed: {failed}/{total}")


def scrape_casino_base_urls():
    """Scrape all active casino base URLs."""
    print("\n=== Scraping Casino Base URLs ===\n")

    result = supabase.table("casinos")\
        .select("id, name, base_url")\
        .eq("is_active", True)\
        .execute()

    casinos = result.data
    total = len(casinos)
    print(f"Found {total} active casinos\n")

    success = 0
    failed = 0

    for i, casino in enumerate(casinos, 1):
        print(f"[{i}/{total}] {casino['name']}")

        result = scrape_url(
            casino_id=casino["id"],
            url=casino["base_url"]
        )

        if result["success"]:
            success += 1
        else:
            failed += 1

        print()

    print(f"\n=== Complete ===")
    print(f"Success: {success}/{total}")
    print(f"Failed: {failed}/{total}")


def scrape_single_casino(casino_name: str):
    """Scrape all URLs for a specific casino by name."""
    # Find casino
    result = supabase.table("casinos")\
        .select("id, name, base_url")\
        .ilike("name", f"%{casino_name}%")\
        .execute()

    if not result.data:
        print(f"Casino not found: {casino_name}")
        return

    casino = result.data[0]
    print(f"\n=== Scraping: {casino['name']} ===\n")

    # Get scrape configs for this casino
    configs_result = supabase.table("scrape_configs")\
        .select("id, name, page_url")\
        .eq("casino_id", casino["id"])\
        .eq("is_active", True)\
        .execute()

    configs = configs_result.data

    if not configs:
        # No configs, scrape base URL
        print("No scrape URLs configured, using base URL")
        scrape_url(casino["id"], casino["base_url"])
    else:
        print(f"Found {len(configs)} configured URLs\n")
        for config in configs:
            print(f"- {config['name']}")
            scrape_url(casino["id"], config["page_url"], config["id"])
            print()


def main():
    parser = argparse.ArgumentParser(description="Casino Scraper")
    parser.add_argument("--all", action="store_true", help="Scrape all configured URLs")
    parser.add_argument("--base", action="store_true", help="Scrape all casino base URLs only")
    parser.add_argument("--casino", type=str, help="Scrape a specific casino by name")
    parser.add_argument("--url", type=str, help="Scrape a specific URL")
    parser.add_argument("--casino-id", type=str, help="Casino ID (required with --url)")

    args = parser.parse_args()

    if args.url:
        if not args.casino_id:
            print("Error: --casino-id is required when using --url")
            sys.exit(1)
        print(f"\n=== Scraping URL ===\n")
        scrape_url(args.casino_id, args.url)

    elif args.casino:
        scrape_single_casino(args.casino)

    elif args.base:
        scrape_casino_base_urls()

    else:
        # Default: scrape all configured URLs
        scrape_all_configs()


if __name__ == "__main__":
    main()
