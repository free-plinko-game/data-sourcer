#!/usr/bin/env python3
"""
Casino.guru Australian Casino Review Scraper

Extracts casino review data from casino.guru's Australian site
and outputs structured JSON files.
"""

import json
import re
import time
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

# Target brands to scrape
TARGET_BRANDS = [
    "Realz",
    "7Signs",
    "Mafia Casino",
    "Spinrise Casino",
    "Lucky Circus",
    "RollXO",
    "Spinsy Casino",
    "Ripper Casino",
    "Rooli Casino",
    "Lucky Wins Casino",
    "JustCasino",
    "OhMySpins Casino",
    "Leon Bet",
    "DundeeSlots",
    "SkyCrown Casino",
    "Neospin Casino",
    "Rolling Slots Casino",
    "Fair Go Casino",
    "Stellar Spins Casino",
    "Goodman Casino",
    "Joe Fortune Casino",
    "Uptown Pokies",
    "PlayCroco",
    "Queenspins Casino",
    "Ignition Casino",
    "Casino Chan",
    "21Bit Casino",
    "5Gringos Casino",
    "Jackpot Jill",
    "Ricky Casino",
]

# Manual slug overrides for edge cases
SLUG_OVERRIDES = {
    "7Signs": "7signs",
    "21Bit Casino": "21bit",
    "RollXO": "rollxo",
    "JustCasino": "justcasino",
    "DundeeSlots": "dundeeslots",
    "PlayCroco": "playcroco",
    "Casino Chan": "casinochan",
    "Jackpot Jill": "jackpot-jill",
    "Leon Bet": "leonbet",
    "OhMySpins Casino": "ohmyspins",
    "Uptown Pokies": "uptown-pokies",
    "5Gringos Casino": "5gringos",
}

BASE_URL = "https://casino.guru/au/"
REQUEST_DELAY = 2  # seconds between requests

# HTTP headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def generate_slug(brand_name: str) -> str:
    """Generate URL slug from brand name."""
    if brand_name in SLUG_OVERRIDES:
        return SLUG_OVERRIDES[brand_name]

    # Convert to lowercase and replace spaces with hyphens
    slug = brand_name.lower().replace(" ", "-")

    # Remove 'casino' suffix if present to avoid doubling
    if slug.endswith("-casino"):
        slug = slug[:-7]

    return slug


def get_review_url(brand_name: str) -> str:
    """Generate the review URL for a casino brand."""
    slug = generate_slug(brand_name)
    return f"{BASE_URL}{slug}-casino-review"


def get_alternate_urls(brand_name: str) -> list[str]:
    """Generate alternate URL patterns to try if primary fails."""
    slug = generate_slug(brand_name)
    base_slug = slug.replace("-casino", "").replace("casino-", "")

    alternates = [
        f"{BASE_URL}{slug}-review",
        f"{BASE_URL}{base_slug}-casino-review",
        f"{BASE_URL}{base_slug}-review",
        f"{BASE_URL}{slug}",
        f"{BASE_URL}{base_slug}",
    ]

    # Add version without hyphens
    no_hyphen = slug.replace("-", "")
    if no_hyphen != slug:
        alternates.append(f"{BASE_URL}{no_hyphen}-casino-review")

    return alternates


def fetch_page(url: str, session: requests.Session) -> tuple[str | None, str]:
    """Fetch a page and return its HTML content."""
    try:
        response = session.get(url, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            return response.text, url
        return None, url
    except requests.RequestException as e:
        print(f"  Error fetching {url}: {e}")
        return None, url


def extract_json_ld(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Extract JSON-LD structured data from the page."""
    json_ld_data = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                json_ld_data.extend(data)
            else:
                json_ld_data.append(data)
        except (json.JSONDecodeError, TypeError):
            continue
    return json_ld_data


def extract_metadata(soup: BeautifulSoup) -> dict[str, str | None]:
    """Extract page metadata."""
    metadata = {
        "title": None,
        "meta_description": None,
        "canonical_url": None,
    }

    # Page title
    title_tag = soup.find("title")
    if title_tag:
        metadata["title"] = title_tag.get_text(strip=True)

    # Meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and isinstance(meta_desc, Tag):
        metadata["meta_description"] = meta_desc.get("content")

    # Canonical URL
    canonical = soup.find("link", rel="canonical")
    if canonical and isinstance(canonical, Tag):
        metadata["canonical_url"] = canonical.get("href")

    return metadata


def extract_rating(soup: BeautifulSoup) -> dict[str, Any]:
    """Extract rating information from the page."""
    rating_data = {
        "overall_score": None,
        "safety_index": None,
        "reputation_rating": None,
        "user_rating": None,
    }

    # Look for rating elements with various selectors
    # Overall rating - often in a prominent widget
    rating_selectors = [
        ".rating-value",
        ".casino-rating",
        ".score-value",
        "[class*='rating']",
        "[class*='score']",
        ".reputation-badge",
    ]

    for selector in rating_selectors:
        elements = soup.select(selector)
        for elem in elements:
            text = elem.get_text(strip=True)
            # Look for numeric ratings
            match = re.search(r"(\d+\.?\d*)\s*(?:/\s*10|/\s*100)?", text)
            if match:
                score = float(match.group(1))
                if rating_data["overall_score"] is None:
                    rating_data["overall_score"] = score
                    break

    # Safety index - often has specific class or text
    safety_elements = soup.find_all(string=re.compile(r"safety\s*index", re.I))
    for elem in safety_elements:
        parent = elem.parent
        if parent:
            text = parent.get_text()
            match = re.search(r"(\w+)\s*safety\s*index", text, re.I)
            if match:
                rating_data["safety_index"] = match.group(1).strip()

    # Look for reputation rating
    rep_elements = soup.find_all(string=re.compile(r"reputation", re.I))
    for elem in rep_elements:
        parent = elem.parent
        if parent:
            # Look for rating nearby
            text = parent.get_text()
            match = re.search(r"(\w+)\s*reputation", text, re.I)
            if match:
                rating_data["reputation_rating"] = match.group(1).strip()

    return rating_data


def extract_quick_facts(soup: BeautifulSoup) -> dict[str, Any]:
    """Extract quick facts/info table data."""
    facts = {
        "established": None,
        "owner": None,
        "licenses": [],
        "withdrawal_limit": None,
        "min_deposit": None,
        "currencies": [],
        "languages": [],
        "website": None,
    }

    # Look for info tables or fact boxes
    info_selectors = [
        ".casino-info",
        ".quick-facts",
        ".info-table",
        ".casino-details",
        "table.info",
        "[class*='info-box']",
        "[class*='quick-info']",
    ]

    for selector in info_selectors:
        tables = soup.select(selector)
        for table in tables:
            rows = table.find_all("tr") or table.find_all("div", class_=re.compile(r"row|item"))
            for row in rows:
                text = row.get_text(separator=" ", strip=True).lower()

                # Established year
                if "established" in text or "founded" in text or "year" in text:
                    match = re.search(r"(\d{4})", row.get_text())
                    if match:
                        facts["established"] = int(match.group(1))

                # Owner/Operator
                if "owner" in text or "operator" in text or "operated by" in text:
                    cells = row.find_all(["td", "span", "div"])
                    if len(cells) >= 2:
                        facts["owner"] = cells[-1].get_text(strip=True)

                # License info
                if "license" in text or "licence" in text:
                    cells = row.find_all(["td", "span", "div", "a"])
                    for cell in cells:
                        license_text = cell.get_text(strip=True)
                        if license_text and "license" not in license_text.lower():
                            facts["licenses"].append(license_text)

                # Withdrawal limits
                if "withdrawal" in text and "limit" in text:
                    match = re.search(r"[\$€£]?\s*[\d,]+(?:\.\d{2})?", row.get_text())
                    if match:
                        facts["withdrawal_limit"] = match.group(0).strip()

                # Minimum deposit
                if "minimum" in text and "deposit" in text:
                    match = re.search(r"[\$€£]?\s*[\d,]+(?:\.\d{2})?", row.get_text())
                    if match:
                        facts["min_deposit"] = match.group(0).strip()

    # Clean up empty lists
    facts["licenses"] = list(set(facts["licenses"])) if facts["licenses"] else []

    return facts


def extract_bonuses(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Extract bonus information."""
    bonuses = []

    # Look for bonus sections
    bonus_selectors = [
        ".bonus-card",
        ".bonus-item",
        ".welcome-bonus",
        "[class*='bonus']",
        ".promotion",
        ".offer",
    ]

    for selector in bonus_selectors:
        bonus_elements = soup.select(selector)
        for elem in bonus_elements:
            bonus = {
                "title": None,
                "match_percentage": None,
                "max_amount": None,
                "free_spins": None,
                "wagering_requirement": None,
                "bonus_code": None,
                "description": None,
            }

            text = elem.get_text(separator=" ", strip=True)

            # Title
            title_elem = elem.find(["h2", "h3", "h4", ".bonus-title", ".title"])
            if title_elem:
                bonus["title"] = title_elem.get_text(strip=True)

            # Match percentage (e.g., "100%", "200% match")
            match_pct = re.search(r"(\d{2,3})%\s*(?:match|bonus)?", text, re.I)
            if match_pct:
                bonus["match_percentage"] = f"{match_pct.group(1)}%"

            # Max amount (e.g., "up to $1000", "max $500")
            max_amount = re.search(
                r"(?:up\s*to|max(?:imum)?)\s*[\$€£A-Z]*\s*([\d,]+)", text, re.I
            )
            if max_amount:
                bonus["max_amount"] = max_amount.group(1).replace(",", "")

            # Free spins
            free_spins = re.search(r"(\d+)\s*(?:free\s*)?spins", text, re.I)
            if free_spins:
                bonus["free_spins"] = int(free_spins.group(1))

            # Wagering requirement
            wagering = re.search(r"(\d+)[xX]\s*(?:wagering|playthrough|wager)", text, re.I)
            if not wagering:
                wagering = re.search(r"wagering[:\s]*(\d+)[xX]", text, re.I)
            if wagering:
                bonus["wagering_requirement"] = f"{wagering.group(1)}x"

            # Bonus code
            code = re.search(r"(?:code|promo)[:\s]*([A-Z0-9]+)", text, re.I)
            if code:
                bonus["bonus_code"] = code.group(1)

            # Description
            desc_elem = elem.find(["p", ".description", ".bonus-desc"])
            if desc_elem:
                bonus["description"] = desc_elem.get_text(strip=True)[:500]

            # Only add if we found meaningful data
            if any([bonus["title"], bonus["match_percentage"], bonus["free_spins"]]):
                bonuses.append(bonus)

    # Deduplicate based on title
    seen_titles = set()
    unique_bonuses = []
    for b in bonuses:
        title = b.get("title") or str(b)
        if title not in seen_titles:
            seen_titles.add(title)
            unique_bonuses.append(b)

    return unique_bonuses[:10]  # Limit to top 10 bonuses


def extract_pros_cons(soup: BeautifulSoup) -> dict[str, list[str]]:
    """Extract pros and cons lists."""
    result = {"pros": [], "cons": []}

    # Look for pros/cons sections
    pros_selectors = [
        ".pros",
        ".advantages",
        "[class*='pro']",
        ".positives",
        ".plus",
    ]
    cons_selectors = [
        ".cons",
        ".disadvantages",
        "[class*='con']",
        ".negatives",
        ".minus",
    ]

    # Extract pros
    for selector in pros_selectors:
        elements = soup.select(selector)
        for elem in elements:
            items = elem.find_all("li") or elem.find_all("div", class_=re.compile(r"item"))
            for item in items:
                text = item.get_text(strip=True)
                if text and len(text) > 5:
                    result["pros"].append(text)

    # Extract cons
    for selector in cons_selectors:
        elements = soup.select(selector)
        for elem in elements:
            items = elem.find_all("li") or elem.find_all("div", class_=re.compile(r"item"))
            for item in items:
                text = item.get_text(strip=True)
                if text and len(text) > 5:
                    result["cons"].append(text)

    # Also try to find by headers
    for header in soup.find_all(["h2", "h3", "h4"]):
        header_text = header.get_text(strip=True).lower()
        if "pro" in header_text or "advantage" in header_text or "positive" in header_text:
            next_elem = header.find_next_sibling()
            if next_elem:
                items = next_elem.find_all("li")
                for item in items:
                    text = item.get_text(strip=True)
                    if text and text not in result["pros"]:
                        result["pros"].append(text)
        elif "con" in header_text or "disadvantage" in header_text or "negative" in header_text:
            next_elem = header.find_next_sibling()
            if next_elem:
                items = next_elem.find_all("li")
                for item in items:
                    text = item.get_text(strip=True)
                    if text and text not in result["cons"]:
                        result["cons"].append(text)

    # Deduplicate
    result["pros"] = list(dict.fromkeys(result["pros"]))[:15]
    result["cons"] = list(dict.fromkeys(result["cons"]))[:15]

    return result


def extract_payment_methods(soup: BeautifulSoup) -> dict[str, list[str]]:
    """Extract payment method information."""
    payments = {"deposit_methods": [], "withdrawal_methods": [], "all_methods": []}

    # Look for payment sections
    payment_selectors = [
        ".payment-methods",
        ".payments",
        ".banking",
        "[class*='payment']",
        "[class*='deposit']",
        "[class*='withdrawal']",
    ]

    for selector in payment_selectors:
        elements = soup.select(selector)
        for elem in elements:
            # Check if it's deposit or withdrawal specific
            elem_text = elem.get_text(strip=True).lower()
            is_deposit = "deposit" in elem_text
            is_withdrawal = "withdrawal" in elem_text or "withdraw" in elem_text

            # Find payment method items
            items = elem.find_all(["li", "span", "div", "img"])
            for item in items:
                # Try to get method name from text or alt attribute
                if isinstance(item, Tag):
                    method = item.get("alt") or item.get("title") or item.get_text(strip=True)
                    if method and len(method) > 1 and len(method) < 50:
                        method = method.strip()
                        if is_deposit and method not in payments["deposit_methods"]:
                            payments["deposit_methods"].append(method)
                        elif is_withdrawal and method not in payments["withdrawal_methods"]:
                            payments["withdrawal_methods"].append(method)
                        elif method not in payments["all_methods"]:
                            payments["all_methods"].append(method)

    # Common payment method keywords to look for
    payment_keywords = [
        "visa",
        "mastercard",
        "paypal",
        "skrill",
        "neteller",
        "bitcoin",
        "ethereum",
        "paysafecard",
        "bank transfer",
        "apple pay",
        "google pay",
        "trustly",
        "interac",
        "ecopayz",
        "muchbetter",
        "astropay",
        "neosurf",
    ]

    # Search for payment keywords in page text
    page_text = soup.get_text().lower()
    for keyword in payment_keywords:
        if keyword in page_text and keyword.title() not in payments["all_methods"]:
            payments["all_methods"].append(keyword.title())

    return payments


def extract_games(soup: BeautifulSoup) -> dict[str, Any]:
    """Extract game information."""
    games = {
        "providers": [],
        "total_games": None,
        "game_categories": {},
    }

    # Look for provider sections
    provider_selectors = [
        ".providers",
        ".game-providers",
        ".software",
        "[class*='provider']",
        "[class*='software']",
    ]

    for selector in provider_selectors:
        elements = soup.select(selector)
        for elem in elements:
            items = elem.find_all(["li", "span", "a", "div", "img"])
            for item in items:
                if isinstance(item, Tag):
                    provider = item.get("alt") or item.get("title") or item.get_text(strip=True)
                    if provider and len(provider) > 1 and len(provider) < 50:
                        provider = provider.strip()
                        if provider not in games["providers"]:
                            games["providers"].append(provider)

    # Common providers to search for
    common_providers = [
        "NetEnt",
        "Microgaming",
        "Playtech",
        "Evolution",
        "Pragmatic Play",
        "Play'n GO",
        "Yggdrasil",
        "Red Tiger",
        "Quickspin",
        "Betsoft",
        "iSoftBet",
        "Hacksaw Gaming",
        "Nolimit City",
        "Push Gaming",
        "Relax Gaming",
        "Big Time Gaming",
        "ELK Studios",
        "Thunderkick",
    ]

    page_text = soup.get_text()
    for provider in common_providers:
        if provider.lower() in page_text.lower() and provider not in games["providers"]:
            games["providers"].append(provider)

    # Look for game counts
    game_count_patterns = [
        r"(\d{2,5})\+?\s*(?:games|slots|pokies)",
        r"(?:games|slots|pokies)[:\s]*(\d{2,5})",
        r"over\s*(\d{2,5})\s*(?:games|slots)",
    ]

    for pattern in game_count_patterns:
        match = re.search(pattern, page_text, re.I)
        if match:
            games["total_games"] = int(match.group(1))
            break

    # Game categories
    category_keywords = {
        "slots": r"(\d+)\s*slots",
        "pokies": r"(\d+)\s*pokies",
        "table_games": r"(\d+)\s*table\s*games",
        "live_casino": r"(\d+)\s*live\s*(?:casino|games)",
        "video_poker": r"(\d+)\s*video\s*poker",
        "jackpot_games": r"(\d+)\s*jackpot",
    }

    for category, pattern in category_keywords.items():
        match = re.search(pattern, page_text, re.I)
        if match:
            games["game_categories"][category] = int(match.group(1))

    return games


def extract_license_info(soup: BeautifulSoup) -> dict[str, Any]:
    """Extract licensing information."""
    license_info = {
        "licenses": [],
        "licensing_authority": None,
        "license_status": None,
    }

    # Common licensing authorities
    authorities = [
        ("Malta Gaming Authority", "MGA"),
        ("UK Gambling Commission", "UKGC"),
        ("Curacao", "Curaçao"),
        ("Gibraltar", None),
        ("Isle of Man", None),
        ("Kahnawake", None),
        ("Alderney", None),
        ("Sweden", "Swedish Gambling Authority"),
        ("Denmark", "Danish Gambling Authority"),
    ]

    page_text = soup.get_text()

    for auth, alt in authorities:
        if auth.lower() in page_text.lower():
            license_info["licenses"].append(auth)
        if alt and alt.lower() in page_text.lower():
            if auth not in license_info["licenses"]:
                license_info["licenses"].append(auth)

    if license_info["licenses"]:
        license_info["licensing_authority"] = license_info["licenses"][0]

    # Look for license status
    if re.search(r"licensed\s+and\s+regulated", page_text, re.I):
        license_info["license_status"] = "Licensed and Regulated"
    elif re.search(r"fully\s+licensed", page_text, re.I):
        license_info["license_status"] = "Fully Licensed"
    elif "unlicensed" in page_text.lower():
        license_info["license_status"] = "Unlicensed"

    return license_info


def extract_review_content(soup: BeautifulSoup) -> dict[str, str | None]:
    """Extract main review text sections."""
    content = {
        "introduction": None,
        "main_review": None,
        "conclusion": None,
        "expert_opinion": None,
    }

    # Look for main content sections
    content_selectors = [
        "article",
        ".review-content",
        ".main-content",
        ".casino-review",
        "[class*='review']",
    ]

    main_content = None
    for selector in content_selectors:
        elem = soup.select_one(selector)
        if elem:
            main_content = elem
            break

    if main_content:
        # Get all paragraphs
        paragraphs = main_content.find_all("p")
        if paragraphs:
            # First paragraph often is introduction
            content["introduction"] = paragraphs[0].get_text(strip=True)[:1000]

            # Combine middle paragraphs for main review
            if len(paragraphs) > 2:
                main_text = " ".join(p.get_text(strip=True) for p in paragraphs[1:-1])
                content["main_review"] = main_text[:3000]

            # Last paragraph often is conclusion
            if len(paragraphs) > 1:
                content["conclusion"] = paragraphs[-1].get_text(strip=True)[:1000]

    # Look for expert opinion
    expert_selectors = [".expert-opinion", ".verdict", ".summary", "[class*='verdict']"]
    for selector in expert_selectors:
        elem = soup.select_one(selector)
        if elem:
            content["expert_opinion"] = elem.get_text(strip=True)[:1000]
            break

    return content


def scrape_casino(
    brand_name: str, session: requests.Session
) -> tuple[dict[str, Any] | None, str]:
    """Scrape data for a single casino."""
    # Try primary URL first
    primary_url = get_review_url(brand_name)
    html, used_url = fetch_page(primary_url, session)

    # If primary fails, try alternates
    if html is None:
        print(f"  Primary URL failed, trying alternates...")
        for alt_url in get_alternate_urls(brand_name):
            if alt_url != primary_url:
                html, used_url = fetch_page(alt_url, session)
                if html:
                    print(f"  Found at: {used_url}")
                    break
                time.sleep(1)  # Small delay between alternate attempts

    if html is None:
        return None, primary_url

    soup = BeautifulSoup(html, "lxml")

    # Extract all data
    data = {
        "brand_name": brand_name,
        "source_url": used_url,
        "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "metadata": extract_metadata(soup),
        "ratings": extract_rating(soup),
        "quick_facts": extract_quick_facts(soup),
        "bonuses": extract_bonuses(soup),
        "pros_cons": extract_pros_cons(soup),
        "payment_methods": extract_payment_methods(soup),
        "games": extract_games(soup),
        "license_info": extract_license_info(soup),
        "review_content": extract_review_content(soup),
        "json_ld": extract_json_ld(soup),
    }

    return data, used_url


def create_summary(full_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create a condensed summary version of the data."""
    summaries = []

    for casino in full_data:
        if casino is None:
            continue

        # Get bonus headline
        bonus_headline = None
        if casino.get("bonuses") and len(casino["bonuses"]) > 0:
            first_bonus = casino["bonuses"][0]
            parts = []
            if first_bonus.get("match_percentage"):
                parts.append(first_bonus["match_percentage"])
            if first_bonus.get("max_amount"):
                parts.append(f"up to ${first_bonus['max_amount']}")
            if first_bonus.get("free_spins"):
                parts.append(f"{first_bonus['free_spins']} free spins")
            bonus_headline = " + ".join(parts) if parts else first_bonus.get("title")

        summary = {
            "brand_name": casino.get("brand_name"),
            "source_url": casino.get("source_url"),
            "overall_rating": casino.get("ratings", {}).get("overall_score"),
            "safety_index": casino.get("ratings", {}).get("safety_index"),
            "established": casino.get("quick_facts", {}).get("established"),
            "bonus_headline": bonus_headline,
            "pros_count": len(casino.get("pros_cons", {}).get("pros", [])),
            "cons_count": len(casino.get("pros_cons", {}).get("cons", [])),
            "total_games": casino.get("games", {}).get("total_games"),
            "provider_count": len(casino.get("games", {}).get("providers", [])),
            "licenses": casino.get("license_info", {}).get("licenses", []),
        }
        summaries.append(summary)

    return summaries


def main():
    """Main scraper function."""
    print("=" * 60)
    print("Casino.guru Australian Casino Review Scraper")
    print("=" * 60)
    print(f"\nTarget: {len(TARGET_BRANDS)} casinos")
    print(f"Delay: {REQUEST_DELAY}s between requests\n")

    all_data = []
    failed_casinos = []

    # Create session for connection pooling
    session = requests.Session()

    for i, brand in enumerate(TARGET_BRANDS, 1):
        print(f"[{i}/{len(TARGET_BRANDS)}] Scraping {brand}...")

        data, url = scrape_casino(brand, session)

        if data:
            all_data.append(data)
            rating = data.get("ratings", {}).get("overall_score", "N/A")
            bonuses = len(data.get("bonuses", []))
            print(f"  ✓ Success - Rating: {rating}, Bonuses: {bonuses}")
        else:
            failed_casinos.append({"brand": brand, "url": url})
            print(f"  ✗ Failed to scrape")

        # Delay between requests (except for the last one)
        if i < len(TARGET_BRANDS):
            time.sleep(REQUEST_DELAY)

    # Save full data
    print("\n" + "=" * 60)
    print("Saving results...")

    with open("casino_data.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "total_casinos": len(all_data),
                "failed_casinos": failed_casinos,
                "casinos": all_data,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"  ✓ Saved casino_data.json ({len(all_data)} casinos)")

    # Save summary
    summaries = create_summary(all_data)
    with open("casino_summary.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "total_casinos": len(summaries),
                "casinos": summaries,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"  ✓ Saved casino_summary.json ({len(summaries)} casinos)")

    # Print summary
    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)
    print(f"Successfully scraped: {len(all_data)}/{len(TARGET_BRANDS)} casinos")

    if failed_casinos:
        print(f"\nFailed casinos ({len(failed_casinos)}):")
        for fc in failed_casinos:
            print(f"  - {fc['brand']}: {fc['url']}")

    print("\nOutput files:")
    print("  - casino_data.json (full detailed data)")
    print("  - casino_summary.json (condensed summary)")


if __name__ == "__main__":
    main()
