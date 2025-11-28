<script lang="ts">
	const baseUrl = typeof window !== 'undefined' ? window.location.origin : '';
</script>

<svelte:head>
	<title>API Documentation | Data Sourcer</title>
</svelte:head>

<div class="api-docs">
	<h1>API Documentation</h1>
	<p class="subtitle">REST API endpoints for accessing casino data</p>

	<div class="card endpoint">
		<h2>GET /api/casinos</h2>
		<p>List all casinos</p>
		<div class="params">
			<h4>Query Parameters</h4>
			<ul>
				<li><code>active=true</code> - Only return active casinos</li>
			</ul>
		</div>
		<div class="example">
			<code>{baseUrl}/api/casinos?active=true</code>
		</div>
	</div>

	<div class="card endpoint">
		<h2>GET /api/casinos/:id</h2>
		<p>Get a single casino by ID</p>
	</div>

	<div class="card endpoint">
		<h2>POST /api/casinos</h2>
		<p>Create a new casino</p>
		<div class="params">
			<h4>Request Body</h4>
			<pre>{`{
  "name": "Casino Name",
  "base_url": "https://example-casino.com.au",
  "login_url": "https://example-casino.com.au/login",
  "username": "user@email.com",
  "password": "password123",
  "notes": "Optional notes"
}`}</pre>
		</div>
	</div>

	<div class="card endpoint">
		<h2>GET /api/data</h2>
		<p>Get scraped data with pagination</p>
		<div class="params">
			<h4>Query Parameters</h4>
			<ul>
				<li><code>casino_id</code> - Filter by casino ID</li>
				<li><code>status</code> - Filter by status (completed, failed, processing)</li>
				<li><code>limit</code> - Number of results (default: 100)</li>
				<li><code>offset</code> - Pagination offset (default: 0)</li>
			</ul>
		</div>
		<div class="example">
			<code>{baseUrl}/api/data?status=completed&limit=50</code>
		</div>
	</div>

	<div class="card endpoint">
		<h2>POST /api/scrape</h2>
		<p>Trigger a scrape job</p>
		<div class="params">
			<h4>Request Body</h4>
			<pre>{`// Scrape single casino
{
  "casinoId": "uuid-here"
}

// Scrape all active casinos
{
  "all": true
}`}</pre>
		</div>
	</div>

	<div class="card endpoint">
		<h2>GET /api/export/json</h2>
		<p>Export all completed scrapes as JSON file</p>
		<div class="params">
			<h4>Query Parameters</h4>
			<ul>
				<li><code>casino_id</code> - Filter by casino ID</li>
				<li><code>status</code> - Filter by status (default: completed)</li>
			</ul>
		</div>
		<div class="example">
			<a href="/api/export/json" class="btn btn-secondary" download>Download JSON</a>
		</div>
	</div>

	<div class="card endpoint">
		<h2>GET /api/export/csv</h2>
		<p>Export all completed scrapes as CSV file</p>
		<div class="params">
			<h4>Query Parameters</h4>
			<ul>
				<li><code>casino_id</code> - Filter by casino ID</li>
				<li><code>status</code> - Filter by status (default: completed)</li>
			</ul>
		</div>
		<div class="example">
			<a href="/api/export/csv" class="btn btn-secondary" download>Download CSV</a>
		</div>
	</div>

	<div class="card">
		<h2>Extracted Data Schema</h2>
		<p>When scraping casino pages, the following fields are extracted:</p>
		<pre>{`{
  "brand": "Casino brand name",
  "Terms & Conditions": "T&C details",
  "Game Availability": "Available games info",
  "Casino Reputation": "Trust score/reputation",
  "Customer Support": "Support options",
  "Mobile & App Availability": "Mobile app info",
  "Responsible Gambling Page/Tools": "Safe play tools",
  "Privacy Policy": "Privacy details",
  "AML (Anti-Money Laundering)": "AML policy",
  "KYC (Know Your Customer) Details": "Verification info",
  "Providers": "Game developers/studios",
  "Year Established": "Founded year",
  "Payout – Speed/%": "Withdrawal times/RTP",
  "Maximum/Minimum Deposit/Withdrawal": "Payment limits",
  "Number of Games/Pokies": "Game count",
  "Player Protection & Safety": "Safety features",
  "Number of Players": "User base",
  "Bonus Offers Breakdown": "Promotions",
  "source_url": "Page URL scraped"
}`}</pre>
	</div>
</div>

<style>
	.api-docs h1 {
		margin: 0;
	}

	.subtitle {
		color: var(--color-text-secondary);
		margin: 0.5rem 0 2rem;
	}

	.endpoint {
		margin-bottom: 1.5rem;
	}

	.endpoint h2 {
		margin: 0 0 0.5rem 0;
		font-size: 1rem;
		font-family: monospace;
		color: var(--color-primary);
	}

	.endpoint > p {
		margin: 0 0 1rem 0;
		color: var(--color-text-secondary);
	}

	.params {
		margin-bottom: 1rem;
	}

	.params h4 {
		margin: 0 0 0.5rem 0;
		font-size: 0.875rem;
		color: var(--color-text-secondary);
	}

	.params ul {
		margin: 0;
		padding-left: 1.5rem;
	}

	.params li {
		margin-bottom: 0.25rem;
	}

	.params code {
		background-color: var(--color-bg-tertiary);
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
		font-size: 0.875rem;
	}

	.params pre {
		background-color: var(--color-bg-tertiary);
		padding: 1rem;
		border-radius: 0.375rem;
		overflow-x: auto;
		font-size: 0.8125rem;
		margin: 0;
	}

	.example {
		background-color: var(--color-bg-tertiary);
		padding: 0.75rem;
		border-radius: 0.375rem;
	}

	.example code {
		font-size: 0.875rem;
		word-break: break-all;
	}

	.card pre {
		background-color: var(--color-bg-tertiary);
		padding: 1rem;
		border-radius: 0.375rem;
		overflow-x: auto;
		font-size: 0.8125rem;
		margin: 0;
	}
</style>
