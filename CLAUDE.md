# CLAUDE.md - AI Assistant Guidelines for data-sourcer

## Project Overview

**Repository:** data-sourcer
**Organization:** free-plinko-game
**Purpose:** Casino data scraping and management system for Australian casinos

A SvelteKit-based web application that:
- Manages a database of Australian casinos (name, URLs, credentials)
- Scrapes casino websites and extracts structured data using GPT
- Provides REST API endpoints for data access
- Exports data in JSON and CSV formats

## Tech Stack

- **Frontend:** SvelteKit 2 with Svelte 5, TypeScript
- **Styling:** Tailwind CSS 4
- **Database:** Supabase (PostgreSQL)
- **AI Extraction:** OpenAI GPT-4 API
- **Scraping:** Simple HTTP fetch + Cheerio for HTML parsing

## Repository Structure

```
data-sourcer/
├── CLAUDE.md                    # AI assistant guidelines
├── package.json                 # Dependencies and scripts
├── svelte.config.js             # SvelteKit configuration
├── vite.config.ts               # Vite configuration
├── tsconfig.json                # TypeScript configuration
├── supabase/
│   └── schema.sql               # Database schema (run in Supabase SQL Editor)
├── src/
│   ├── app.html                 # HTML template
│   ├── app.css                  # Global styles
│   ├── app.d.ts                 # App type declarations
│   ├── lib/
│   │   └── server/
│   │       ├── db/              # Supabase client and types
│   │       │   ├── index.ts     # Supabase client singleton
│   │       │   └── types.ts     # Database type definitions
│   │       ├── ai/
│   │       │   └── extractor.ts # GPT-based data extraction
│   │       └── scraper/
│   │           └── index.ts     # HTTP scraping logic
│   └── routes/
│       ├── +layout.svelte       # App layout with navigation
│       ├── +page.svelte         # Dashboard
│       ├── casinos/             # Casino management pages
│       │   ├── +page.svelte     # List casinos
│       │   ├── new/             # Add casino
│       │   └── [id]/            # Edit casino
│       ├── scraper/             # Scraper UI
│       ├── data/                # View scraped data
│       ├── api-docs/            # API documentation
│       └── api/                 # REST API endpoints
│           ├── casinos/         # Casino CRUD
│           ├── scrape/          # Trigger scraping
│           ├── data/            # Access scraped data
│           └── export/          # JSON/CSV export
```

## Development Commands

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type check
npm run check
```

## Environment Setup

Create a `.env` file based on `.env.example`:

```bash
# OpenAI API Key
OPENAI_API_KEY=sk-your-api-key-here

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### Database Setup

1. Create a Supabase project at https://supabase.com
2. Run the SQL in `supabase/schema.sql` in the SQL Editor
3. Copy your project URL and keys to `.env`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/casinos` | List all casinos |
| POST | `/api/casinos` | Create a casino |
| GET | `/api/casinos/:id` | Get casino by ID |
| PATCH | `/api/casinos/:id` | Update casino |
| DELETE | `/api/casinos/:id` | Delete casino |
| POST | `/api/scrape` | Trigger scrape job |
| GET | `/api/data` | Get scraped data |
| GET | `/api/export/json` | Export as JSON |
| GET | `/api/export/csv` | Export as CSV |

## Scraping Flow

1. **Fetch HTML** - Download page using HTTP fetch with browser User-Agent
2. **Clean HTML** - Remove scripts, styles, ads using Cheerio
3. **AI Extraction** - Send cleaned text to GPT-4 with extraction prompt
4. **Store Results** - Save extracted JSON to Supabase

## Extracted Data Schema

The AI extracts these fields from casino pages:

- `brand` - Casino name
- `Terms & Conditions` - T&C details
- `Game Availability` - Available games
- `Casino Reputation` - Trust score
- `Customer Support` - Support options
- `Mobile & App Availability` - App info
- `Responsible Gambling Page/Tools` - Safe play tools
- `Privacy Policy` - Privacy details
- `AML (Anti-Money Laundering)` - AML policy
- `KYC (Know Your Customer) Details` - Verification info
- `Providers` - Game developers
- `Year Established` - Founded year
- `Payout – Speed/%` - RTP/withdrawal times
- `Maximum/Minimum Deposit/Withdrawal` - Payment limits
- `Number of Games/Pokies` - Game count
- `Player Protection & Safety` - Safety features
- `Number of Players` - User base
- `Bonus Offers Breakdown` - Promotions
- `source_url` - Scraped URL

## Code Conventions

- **TypeScript** with strict mode
- **Svelte 5** runes ($state, $props, $effect)
- **snake_case** for database columns (Supabase/PostgreSQL)
- **camelCase** for TypeScript variables
- **Async/await** for all async operations

## AI Assistant Guidelines

### When Working on This Codebase

1. Use Supabase client from `$lib/server/db` for database operations
2. Server-side code goes in `src/lib/server/` directory
3. API routes use SvelteKit's `+server.ts` convention
4. Pages use `+page.svelte` with `+page.server.ts` for data loading

### Key Files to Know

- `src/lib/server/db/index.ts` - Supabase client
- `src/lib/server/ai/extractor.ts` - GPT extraction logic
- `src/lib/server/scraper/index.ts` - Scraping logic
- `supabase/schema.sql` - Database schema

---

*Last updated: 2025-11-28*
