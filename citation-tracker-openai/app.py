"""
LLM Citation Tracker - Competitive Intelligence Tool
Tracks how competitors appear in LLM search citations
Modified to use OpenAI API
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from urllib.parse import urlparse
from collections import Counter

app = Flask(__name__)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment!")
print(f"Initializing OpenAI client with key: {api_key[:20]}...")

client = OpenAI(api_key=api_key)

DATABASE = 'citations.db'

# ============ DATABASE SETUP ============

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS competitors (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                domain TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY,
                query_text TEXT,
                run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS citations (
                id INTEGER PRIMARY KEY,
                query_id INTEGER,
                domain TEXT,
                title TEXT,
                context TEXT,
                competitor_id INTEGER,
                found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (query_id) REFERENCES queries(id),
                FOREIGN KEY (competitor_id) REFERENCES competitors(id)
            );

            CREATE TABLE IF NOT EXISTS page_analyses (
                id INTEGER PRIMARY KEY,
                url TEXT,
                analysis TEXT,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS pattern_tests (
                id INTEGER PRIMARY KEY,
                topic TEXT,
                test_results TEXT,
                tested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

# ============ CORE ANALYSIS FUNCTIONS ============

def analyze_citations_for_competitors(query_text, competitors=None):
    """Run query and identify which competitors appear in citations."""

    # Build competitor context for the prompt
    competitor_list = ""
    if competitors:
        competitor_list = "\n\nSpecifically track if any of these competitors appear: " + ", ".join(competitors)

    response = client.responses.create(
        model="gpt-4o",
        tools=[{"type": "web_search_preview"}],
        input=f"""Search the web for: {query_text}

After searching, provide:
1. A comprehensive answer to the query
2. At the end, list ALL sources/domains that were cited in your response in this exact JSON format:

```json
{{
    "cited_sources": [
        {{"domain": "example.com", "title": "Page Title", "relevance": "brief note on why cited"}}
    ]
}}
```
{competitor_list}"""
    )

    # Extract the response text
    response_text = ""
    for item in response.output:
        if item.type == "message":
            for content in item.content:
                if content.type == "output_text":
                    response_text += content.text

    # Try to extract JSON from response
    cited_sources = []
    try:
        json_start = response_text.rfind("```json")
        json_end = response_text.rfind("```", json_start + 7)
        if json_start != -1 and json_end != -1:
            json_str = response_text[json_start + 7:json_end].strip()
            data = json.loads(json_str)
            cited_sources = data.get("cited_sources", [])
    except (json.JSONDecodeError, ValueError):
        pass

    return {
        "query": query_text,
        "response": response_text,
        "cited_sources": cited_sources
    }

def check_competitor_visibility(competitor_domain, test_queries):
    """Check how often a competitor appears across multiple queries."""

    results = []
    appearances = 0

    for query in test_queries:
        result = analyze_citations_for_competitors(query)

        # Check if competitor domain appears in citations
        found = False
        for source in result.get("cited_sources", []):
            if competitor_domain.lower() in source.get("domain", "").lower():
                found = True
                break

        results.append({
            "query": query,
            "competitor_found": found,
            "all_citations": result.get("cited_sources", [])
        })

        if found:
            appearances += 1

    return {
        "competitor": competitor_domain,
        "total_queries": len(test_queries),
        "appearances": appearances,
        "visibility_rate": (appearances / len(test_queries) * 100) if test_queries else 0,
        "detailed_results": results
    }

def analyze_page_for_citation_factors(url):
    """Analyze a page to understand what makes it citation-worthy."""

    response = client.responses.create(
        model="gpt-4o",
        tools=[{"type": "web_search_preview"}],
        input=f"""Please fetch and analyze this page: {url}

Analyze it for factors that would make an LLM likely to cite it as a source.

Provide your analysis in this JSON format:
```json
{{
    "url": "{url}",
    "content_type": "blog/documentation/product page/research/etc",
    "citation_factors": {{
        "authority_signals": ["list of authority indicators"],
        "content_structure": "description of how content is organized",
        "data_richness": "does it contain statistics, research, original data?",
        "freshness": "how recent/updated is the content",
        "expertise_markers": "credentials, author info, etc",
        "unique_value": "what unique information does this provide"
    }},
    "strengths": ["list of citation-worthy strengths"],
    "weaknesses": ["areas that might reduce citation likelihood"],
    "recommendations": ["suggestions to improve citation likelihood"],
    "overall_citation_score": 1-10
}}
```"""
    )

    # Extract the response text
    response_text = ""
    for item in response.output:
        if item.type == "message":
            for content in item.content:
                if content.type == "output_text":
                    response_text += content.text

    # Extract JSON
    analysis = {}
    try:
        json_start = response_text.rfind("```json")
        json_end = response_text.rfind("```", json_start + 7)
        if json_start != -1 and json_end != -1:
            json_str = response_text[json_start + 7:json_end].strip()
            analysis = json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        analysis = {"raw_analysis": response_text}

    return analysis


def generate_query_variations(topic, include_brands=None):
    """Generate different query variations for pattern testing."""

    brands_context = ""
    if include_brands:
        brands_context = f"\nInclude these brands in branded queries: {', '.join(include_brands)}"

    response = client.responses.create(
        model="gpt-4o",
        input=f"""Generate search query variations for the topic: "{topic}"
{brands_context}

Create exactly 12 query variations across these categories:

1. INFORMATIONAL (3 queries) - Questions seeking to understand/learn
   - "what is...", "how does... work", "...explained", "guide to..."

2. TRANSACTIONAL (3 queries) - Intent to take action/purchase
   - "best...", "top... 2024", "...pricing", "buy...", "...alternatives"

3. BRANDED (3 queries) - Include specific brand/company names
   - "[brand] vs [brand]", "[brand] review", "is [brand] good for..."

4. LONG-TAIL (3 queries) - Specific, detailed queries (6+ words)
   - Very specific use cases or scenarios

Return ONLY a JSON object in this exact format:
```json
{{
    "topic": "{topic}",
    "variations": {{
        "informational": ["query1", "query2", "query3"],
        "transactional": ["query1", "query2", "query3"],
        "branded": ["query1", "query2", "query3"],
        "long_tail": ["query1", "query2", "query3"]
    }}
}}
```"""
    )

    # Extract the response text
    response_text = ""
    for item in response.output:
        if item.type == "message":
            for content in item.content:
                if content.type == "output_text":
                    response_text += content.text

    # Parse JSON
    try:
        json_start = response_text.rfind("```json")
        json_end = response_text.rfind("```", json_start + 7)
        if json_start != -1 and json_end != -1:
            json_str = response_text[json_start + 7:json_end].strip()
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        pass

    return {"topic": topic, "variations": {}, "error": "Failed to generate variations"}


def run_pattern_analysis(topic, variations, track_domains=None):
    """Run all query variations and analyze citation patterns."""

    results = {
        "topic": topic,
        "track_domains": track_domains or [],
        "by_category": {},
        "domain_frequency": {},
        "domain_by_category": {},
        "insights": []
    }

    all_domains = []

    for category, queries in variations.items():
        category_results = []
        category_domains = []

        for query in queries:
            # Run the query
            query_result = analyze_citations_for_competitors(query, track_domains)

            cited_domains = [s.get("domain", "unknown") for s in query_result.get("cited_sources", [])]
            category_domains.extend(cited_domains)
            all_domains.extend(cited_domains)

            # Check if tracked domains appeared
            tracked_found = []
            if track_domains:
                for domain in track_domains:
                    for cited in cited_domains:
                        if domain.lower() in cited.lower():
                            tracked_found.append(domain)
                            break

            category_results.append({
                "query": query,
                "cited_domains": cited_domains,
                "tracked_found": tracked_found,
                "citation_count": len(cited_domains)
            })

        # Category summary
        results["by_category"][category] = {
            "queries": category_results,
            "total_citations": len(category_domains),
            "unique_domains": list(set(category_domains)),
            "domain_counts": dict(Counter(category_domains))
        }

        # Track domain frequency by category
        results["domain_by_category"][category] = dict(Counter(category_domains))

    # Overall domain frequency
    results["domain_frequency"] = dict(Counter(all_domains).most_common(20))

    # Generate insights
    results["insights"] = generate_pattern_insights(results, track_domains)

    return results


def generate_pattern_insights(results, track_domains):
    """Generate actionable insights from pattern analysis."""

    insights = []

    # Find which category has most citations
    category_totals = {cat: data["total_citations"] for cat, data in results["by_category"].items()}
    if category_totals:
        top_category = max(category_totals, key=category_totals.get)
        insights.append(f"'{top_category}' queries generate the most citations ({category_totals[top_category]} total)")

    # Find domains that appear across all categories
    all_category_domains = [set(data["unique_domains"]) for data in results["by_category"].values()]
    if all_category_domains:
        consistent_domains = set.intersection(*all_category_domains) if len(all_category_domains) > 1 else all_category_domains[0]
        if consistent_domains:
            insights.append(f"Domains cited across ALL query types: {', '.join(list(consistent_domains)[:5])}")

    # Check tracked domain performance by category
    if track_domains:
        for domain in track_domains:
            domain_categories = []
            for cat, data in results["by_category"].items():
                for q in data["queries"]:
                    if domain in q.get("tracked_found", []):
                        domain_categories.append(cat)
                        break
            if domain_categories:
                insights.append(f"'{domain}' appears in: {', '.join(domain_categories)}")
            else:
                insights.append(f"'{domain}' was NOT cited in any query type")

    # Find category-specific domains
    for cat, data in results["by_category"].items():
        top_domains = sorted(data["domain_counts"].items(), key=lambda x: x[1], reverse=True)[:3]
        if top_domains:
            domain_list = ", ".join([f"{d[0]} ({d[1]}x)" for d in top_domains])
            insights.append(f"Top domains for {cat}: {domain_list}")

    return insights


# ============ FLASK ROUTES ============

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def api_query():
    """Run a query and extract competitor citations."""
    data = request.json
    query_text = data.get('query', '')
    competitors = data.get('competitors', [])

    if not query_text:
        return jsonify({"error": "Query is required"}), 400

    try:
        result = analyze_citations_for_competitors(query_text, competitors)

        # Store in database
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO queries (query_text) VALUES (?)",
                (query_text,)
            )
            query_id = cursor.lastrowid

            for source in result.get("cited_sources", []):
                # Check if it matches a competitor
                competitor_id = None
                if competitors:
                    for comp in competitors:
                        if comp.lower() in source.get("domain", "").lower():
                            row = conn.execute(
                                "SELECT id FROM competitors WHERE domain LIKE ?",
                                (f"%{comp}%",)
                            ).fetchone()
                            if row:
                                competitor_id = row['id']
                            break

                conn.execute(
                    "INSERT INTO citations (query_id, domain, title, context, competitor_id) VALUES (?, ?, ?, ?, ?)",
                    (query_id, source.get("domain"), source.get("title"), source.get("relevance"), competitor_id)
                )

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/competitor-check', methods=['POST'])
def api_competitor_check():
    """Check competitor visibility across multiple queries."""
    data = request.json
    competitor = data.get('competitor', '')
    queries = data.get('queries', [])

    if not competitor or not queries:
        return jsonify({"error": "Competitor and queries are required"}), 400

    try:
        result = check_competitor_visibility(competitor, queries)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze-page', methods=['POST'])
def api_analyze_page():
    """Analyze a page for citation factors."""
    data = request.json
    url = data.get('url', '')

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        result = analyze_page_for_citation_factors(url)

        # Store in database
        with get_db() as conn:
            conn.execute(
                "INSERT INTO page_analyses (url, analysis) VALUES (?, ?)",
                (url, json.dumps(result))
            )

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/competitors', methods=['GET', 'POST', 'DELETE'])
def api_competitors():
    """Manage competitor list."""
    if request.method == 'GET':
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM competitors ORDER BY name").fetchall()
            return jsonify([dict(row) for row in rows])

    elif request.method == 'POST':
        data = request.json
        name = data.get('name', '')
        domain = data.get('domain', '')

        if not name or not domain:
            return jsonify({"error": "Name and domain required"}), 400

        with get_db() as conn:
            try:
                conn.execute(
                    "INSERT INTO competitors (name, domain) VALUES (?, ?)",
                    (name, domain)
                )
                return jsonify({"success": True})
            except sqlite3.IntegrityError:
                return jsonify({"error": "Competitor already exists"}), 400

    elif request.method == 'DELETE':
        data = request.json
        competitor_id = data.get('id')

        with get_db() as conn:
            conn.execute("DELETE FROM competitors WHERE id = ?", (competitor_id,))
            return jsonify({"success": True})

@app.route('/api/history')
def api_history():
    """Get query history with citations."""
    with get_db() as conn:
        queries = conn.execute("""
            SELECT q.*, COUNT(c.id) as citation_count
            FROM queries q
            LEFT JOIN citations c ON q.id = c.query_id
            GROUP BY q.id
            ORDER BY q.run_at DESC
            LIMIT 50
        """).fetchall()

        return jsonify([dict(row) for row in queries])

@app.route('/api/stats')
def api_stats():
    """Get overall statistics."""
    with get_db() as conn:
        # Most cited domains
        top_domains = conn.execute("""
            SELECT domain, COUNT(*) as count
            FROM citations
            GROUP BY domain
            ORDER BY count DESC
            LIMIT 10
        """).fetchall()

        # Competitor citation counts
        competitor_citations = conn.execute("""
            SELECT comp.name, comp.domain, COUNT(c.id) as citations
            FROM competitors comp
            LEFT JOIN citations c ON comp.id = c.competitor_id
            GROUP BY comp.id
            ORDER BY citations DESC
        """).fetchall()

        total_queries = conn.execute("SELECT COUNT(*) FROM queries").fetchone()[0]
        total_citations = conn.execute("SELECT COUNT(*) FROM citations").fetchone()[0]

        return jsonify({
            "total_queries": total_queries,
            "total_citations": total_citations,
            "top_domains": [dict(row) for row in top_domains],
            "competitor_citations": [dict(row) for row in competitor_citations]
        })


@app.route('/api/pattern-test/generate', methods=['POST'])
def api_generate_variations():
    """Generate query variations for a topic."""
    data = request.json
    topic = data.get('topic', '')
    brands = data.get('brands', [])

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    try:
        result = generate_query_variations(topic, brands if brands else None)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/pattern-test/run', methods=['POST'])
def api_run_pattern_test():
    """Run full pattern analysis with query variations."""
    data = request.json
    topic = data.get('topic', '')
    variations = data.get('variations', {})
    track_domains = data.get('track_domains', [])

    if not topic or not variations:
        return jsonify({"error": "Topic and variations are required"}), 400

    try:
        result = run_pattern_analysis(topic, variations, track_domains if track_domains else None)

        # Store in database
        with get_db() as conn:
            conn.execute(
                "INSERT INTO pattern_tests (topic, test_results) VALUES (?, ?)",
                (topic, json.dumps(result))
            )

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/pattern-test/history')
def api_pattern_history():
    """Get pattern test history."""
    with get_db() as conn:
        tests = conn.execute("""
            SELECT id, topic, tested_at
            FROM pattern_tests
            ORDER BY tested_at DESC
            LIMIT 20
        """).fetchall()

        return jsonify([dict(row) for row in tests])


@app.route('/api/pattern-test/<int:test_id>')
def api_pattern_test_detail(test_id):
    """Get detailed results for a specific pattern test."""
    with get_db() as conn:
        test = conn.execute(
            "SELECT * FROM pattern_tests WHERE id = ?",
            (test_id,)
        ).fetchone()

        if not test:
            return jsonify({"error": "Test not found"}), 404

        result = dict(test)
        result['test_results'] = json.loads(result['test_results'])
        return jsonify(result)


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
