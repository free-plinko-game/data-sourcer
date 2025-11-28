#!/usr/bin/env python3
"""
Casino Scraper using Selenium + BeautifulSoup + GPT
Run this separately from the web app to scrape casino sites.
"""

import os
import json
import time
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
        print(f"Fetching: {url}")
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
    print("Extracting data with GPT...")

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


def scrape_casino(casino_id: str, url: str) -> dict:
    """Scrape a single casino and save to Supabase."""

    # Create processing record
    result = supabase.table("scraped_data").insert({
        "casino_id": casino_id,
        "source_url": url,
        "status": "processing"
    }).execute()

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

        print(f"✓ Successfully scraped: {url}")
        return {"success": True, "data": extracted}

    except Exception as e:
        print(f"✗ Error scraping {url}: {e}")
        supabase.table("scraped_data").update({
            "status": "failed",
            "error_message": str(e)
        }).eq("id", record_id).execute()
        return {"success": False, "error": str(e)}


def scrape_all_active():
    """Scrape all active casinos."""
    result = supabase.table("casinos").select("id, name, base_url").eq("is_active", True).execute()

    casinos = result.data
    print(f"Found {len(casinos)} active casinos")

    for casino in casinos:
        print(f"\n--- Scraping: {casino['name']} ---")
        scrape_casino(casino["id"], casino["base_url"])


def scrape_single(casino_name: str):
    """Scrape a single casino by name."""
    result = supabase.table("casinos").select("id, name, base_url").ilike("name", f"%{casino_name}%").execute()

    if not result.data:
        print(f"Casino not found: {casino_name}")
        return

    casino = result.data[0]
    print(f"Scraping: {casino['name']}")
    scrape_casino(casino["id"], casino["base_url"])


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Scrape specific casino
        scrape_single(sys.argv[1])
    else:
        # Scrape all active casinos
        scrape_all_active()
