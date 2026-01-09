# Casino.guru Australian Casino Review Scraper

A Python web scraper that extracts casino review data from casino.guru's Australian site and outputs structured JSON files.

## Features

- Scrapes 30 Australian casino review pages
- Extracts comprehensive data including:
  - Ratings (overall score, safety index)
  - Quick facts (established date, owner, licenses)
  - Bonus information (match %, max amounts, free spins, wagering requirements)
  - Pros and cons lists
  - Payment methods (deposit and withdrawal)
  - Game information (providers, game counts by category)
  - License details
  - Review content sections
  - JSON-LD structured data
- Outputs both detailed and summary JSON files
- Handles 404s gracefully with alternate URL patterns
- Polite scraping with 2-second delays between requests

## Installation

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the scraper:

```bash
python casino_scraper.py
```

The scraper will:
1. Iterate through all 30 target casinos
2. Display progress in the console
3. Generate output files when complete

## Output Files

### `casino_data.json`

Full detailed data for all casinos, including:
- Complete metadata
- All extracted ratings
- Quick facts and info
- Full bonus details
- Complete pros/cons lists
- Payment method information
- Game provider and count data
- License information
- Review content sections
- Raw JSON-LD data

### `casino_summary.json`

Condensed version with key fields only:
- Brand name
- Overall rating
- Safety index
- Established year
- Bonus headline
- Pros/cons counts
- Total games
- Provider count
- Licenses

## Target Casinos

The scraper targets these 30 Australian casinos:

1. Realz
2. 7Signs
3. Mafia Casino
4. Spinrise Casino
5. Lucky Circus
6. RollXO
7. Spinsy Casino
8. Ripper Casino
9. Rooli Casino
10. Lucky Wins Casino
11. JustCasino
12. OhMySpins Casino
13. Leon Bet
14. DundeeSlots
15. SkyCrown Casino
16. Neospin Casino
17. Rolling Slots Casino
18. Fair Go Casino
19. Stellar Spins Casino
20. Goodman Casino
21. Joe Fortune Casino
22. Uptown Pokies
23. PlayCroco
24. Queenspins Casino
25. Ignition Casino
26. Casino Chan
27. 21Bit Casino
28. 5Gringos Casino
29. Jackpot Jill
30. Ricky Casino

## Configuration

You can modify the following in `casino_scraper.py`:

- `TARGET_BRANDS` - List of casino brands to scrape
- `SLUG_OVERRIDES` - Manual URL slug mappings for edge cases
- `REQUEST_DELAY` - Delay between requests (default: 2 seconds)
- `HEADERS` - HTTP headers sent with requests

## Error Handling

- If a primary URL returns 404, the scraper tries alternate URL patterns
- Failed casinos are logged and listed in the final output
- Network errors are caught and reported without crashing

## Notes

- The scraper uses a browser-like User-Agent to avoid blocking
- HTML parsing uses BeautifulSoup with the lxml parser for speed
- All timestamps are in UTC
- Output files use UTF-8 encoding

## License

For educational and personal use only. Please respect casino.guru's terms of service and robots.txt.
