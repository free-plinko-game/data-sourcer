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

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
