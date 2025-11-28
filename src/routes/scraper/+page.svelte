<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	let selectedCasino = $state('');
	let scraping = $state(false);
	let scrapeResult = $state<{ success: boolean; message: string } | null>(null);

	async function scrapeOne() {
		if (!selectedCasino) return;

		scraping = true;
		scrapeResult = null;

		try {
			const response = await fetch('/api/scrape', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ casinoId: selectedCasino })
			});

			const result = await response.json();
			scrapeResult = {
				success: result.success,
				message: result.message || result.error || 'Unknown result'
			};
		} catch (err) {
			scrapeResult = {
				success: false,
				message: 'Network error'
			};
		} finally {
			scraping = false;
		}
	}

	async function scrapeAll() {
		scraping = true;
		scrapeResult = null;

		try {
			const response = await fetch('/api/scrape', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ all: true })
			});

			const result = await response.json();
			scrapeResult = {
				success: result.success,
				message: result.message || result.error || 'Unknown result'
			};
		} catch (err) {
			scrapeResult = {
				success: false,
				message: 'Network error'
			};
		} finally {
			scraping = false;
		}
	}
</script>

<svelte:head>
	<title>Scraper | Data Sourcer</title>
</svelte:head>

<div class="scraper-page">
	<h1>Scraper</h1>
	<p class="subtitle">Run scraping jobs to collect casino data</p>

	<div class="card">
		<h2>Run Scraper</h2>

		{#if scrapeResult}
			<div class="result-message {scrapeResult.success ? 'success' : 'error'}">
				{scrapeResult.message}
			</div>
		{/if}

		<div class="scrape-options">
			<div class="option-group">
				<h3>Scrape Single Casino</h3>
				<div class="form-row">
					<select class="input" bind:value={selectedCasino} disabled={scraping}>
						<option value="">Select a casino...</option>
						{#each data.casinos as casino}
							<option value={casino.id}>{casino.name}</option>
						{/each}
					</select>
					<button
						class="btn btn-primary"
						onclick={scrapeOne}
						disabled={scraping || !selectedCasino}
					>
						{scraping ? 'Scraping...' : 'Scrape'}
					</button>
				</div>
			</div>

			<div class="divider">OR</div>

			<div class="option-group">
				<h3>Scrape All Active Casinos</h3>
				<p class="hint">This will scrape all {data.activeCasinos} active casinos</p>
				<button class="btn btn-primary" onclick={scrapeAll} disabled={scraping}>
					{scraping ? 'Scraping...' : 'Scrape All'}
				</button>
			</div>
		</div>
	</div>

	<div class="card">
		<h2>How It Works</h2>
		<ol class="steps">
			<li>
				<strong>Fetch HTML</strong> - The scraper downloads the HTML content from the casino URL
			</li>
			<li>
				<strong>Clean Content</strong> - Scripts, styles, and non-content elements are removed
			</li>
			<li>
				<strong>AI Extraction</strong> - GPT-4 analyzes the content and extracts structured data
			</li>
			<li>
				<strong>Store Results</strong> - Extracted data is saved to the database
			</li>
		</ol>
	</div>
</div>

<style>
	.scraper-page h1 {
		margin: 0;
	}

	.subtitle {
		color: var(--color-text-secondary);
		margin: 0.5rem 0 2rem;
	}

	.card {
		margin-bottom: 1.5rem;
	}

	.card h2 {
		margin: 0 0 1rem 0;
		font-size: 1.125rem;
	}

	.scrape-options {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.option-group h3 {
		margin: 0 0 0.5rem 0;
		font-size: 0.875rem;
		color: var(--color-text-secondary);
	}

	.form-row {
		display: flex;
		gap: 0.75rem;
	}

	.form-row select {
		flex: 1;
	}

	.divider {
		text-align: center;
		color: var(--color-text-secondary);
		font-size: 0.875rem;
		position: relative;
	}

	.divider::before,
	.divider::after {
		content: '';
		position: absolute;
		top: 50%;
		width: 45%;
		height: 1px;
		background-color: var(--color-border);
	}

	.divider::before {
		left: 0;
	}

	.divider::after {
		right: 0;
	}

	.hint {
		font-size: 0.875rem;
		color: var(--color-text-secondary);
		margin: 0.25rem 0 0.75rem;
	}

	.result-message {
		padding: 0.75rem;
		border-radius: 0.375rem;
		margin-bottom: 1rem;
	}

	.result-message.success {
		background-color: rgba(34, 197, 94, 0.1);
		border: 1px solid var(--color-success);
		color: var(--color-success);
	}

	.result-message.error {
		background-color: rgba(239, 68, 68, 0.1);
		border: 1px solid var(--color-danger);
		color: var(--color-danger);
	}

	.steps {
		margin: 0;
		padding-left: 1.5rem;
	}

	.steps li {
		margin-bottom: 0.75rem;
		color: var(--color-text-secondary);
	}

	.steps li strong {
		color: var(--color-text);
	}
</style>
