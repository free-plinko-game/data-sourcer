<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	let selectedCasino = $state('');
	let scraping = $state(false);
	let scrapeResult = $state<{ success: boolean; message: string } | null>(null);

	// Batch scraping state
	let batchProgress = $state<{
		running: boolean;
		total: number;
		completed: number;
		current: string;
		results: Array<{ url: string; success: boolean; message: string }>;
	} | null>(null);

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

	async function runBatchScrape() {
		if (data.scrapeConfigs.length === 0) {
			scrapeResult = {
				success: false,
				message: 'No scrape URLs configured. Add URLs in the casino edit page.'
			};
			return;
		}

		batchProgress = {
			running: true,
			total: data.scrapeConfigs.length,
			completed: 0,
			current: '',
			results: []
		};

		for (const config of data.scrapeConfigs) {
			batchProgress = {
				...batchProgress!,
				current: config.page_url
			};

			try {
				const response = await fetch('/api/scrape', {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						casinoId: config.casino_id,
						configId: config.id,
						url: config.page_url
					})
				});

				const result = await response.json();
				batchProgress = {
					...batchProgress!,
					completed: batchProgress!.completed + 1,
					results: [
						...batchProgress!.results,
						{
							url: config.page_url,
							success: result.success,
							message: result.message || result.error || 'Done'
						}
					]
				};
			} catch (err) {
				batchProgress = {
					...batchProgress!,
					completed: batchProgress!.completed + 1,
					results: [
						...batchProgress!.results,
						{
							url: config.page_url,
							success: false,
							message: 'Network error'
						}
					]
				};
			}
		}

		batchProgress = {
			...batchProgress!,
			running: false,
			current: ''
		};
	}

	function clearBatchResults() {
		batchProgress = null;
	}
</script>

<svelte:head>
	<title>Scraper | Data Sourcer</title>
</svelte:head>

<div class="scraper-page">
	<h1>Scraper</h1>
	<p class="subtitle">Run scraping jobs to collect casino data</p>

	<!-- Batch Scraper Section -->
	<div class="card batch-card">
		<h2>Batch Scraper</h2>
		<p class="description">
			Scrape all configured URLs across all casinos. Configure URLs in each casino's edit page.
		</p>

		<div class="stats">
			<div class="stat">
				<span class="stat-value">{data.activeConfigs}</span>
				<span class="stat-label">Active URLs</span>
			</div>
			<div class="stat">
				<span class="stat-value">{data.activeCasinos}</span>
				<span class="stat-label">Active Casinos</span>
			</div>
		</div>

		{#if batchProgress}
			<div class="batch-progress">
				<div class="progress-header">
					<span>
						{batchProgress.running ? 'Scraping...' : 'Completed'}
						({batchProgress.completed}/{batchProgress.total})
					</span>
					{#if !batchProgress.running}
						<button class="btn btn-sm btn-secondary" onclick={clearBatchResults}>
							Clear
						</button>
					{/if}
				</div>

				<div class="progress-bar">
					<div
						class="progress-fill"
						style="width: {(batchProgress.completed / batchProgress.total) * 100}%"
					></div>
				</div>

				{#if batchProgress.current}
					<div class="current-url">
						Currently scraping: <code>{batchProgress.current}</code>
					</div>
				{/if}

				{#if batchProgress.results.length > 0}
					<div class="batch-results">
						{#each batchProgress.results as result}
							<div class="batch-result" class:success={result.success} class:error={!result.success}>
								<span class="result-icon">{result.success ? '✓' : '✗'}</span>
								<span class="result-url">{result.url}</span>
								<span class="result-message">{result.message}</span>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{:else}
			<button
				class="btn btn-primary btn-large"
				onclick={runBatchScrape}
				disabled={data.activeConfigs === 0}
			>
				Run Batch Scrape ({data.activeConfigs} URLs)
			</button>

			{#if data.activeConfigs === 0}
				<p class="hint">No scrape URLs configured. Add URLs in each casino's edit page.</p>
			{/if}
		{/if}
	</div>

	<!-- Configured URLs Preview -->
	{#if data.scrapeConfigs.length > 0}
		<div class="card">
			<h2>Configured URLs ({data.scrapeConfigs.length})</h2>
			<div class="url-preview-list">
				{#each data.scrapeConfigs as config}
					<div class="url-preview">
						<span class="casino-name">{config.casinos?.name || 'Unknown'}</span>
						<span class="config-name">{config.name}</span>
						<span class="page-url">{config.page_url}</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Single Casino Scraper -->
	<div class="card">
		<h2>Single Casino Scraper</h2>

		{#if scrapeResult}
			<div class="result-message {scrapeResult.success ? 'success' : 'error'}">
				{scrapeResult.message}
			</div>
		{/if}

		<div class="scrape-options">
			<div class="option-group">
				<h3>Scrape Base URL</h3>
				<p class="hint">Scrape the base URL of a single casino</p>
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
		</div>
	</div>

	<div class="card">
		<h2>How It Works</h2>
		<ol class="steps">
			<li>
				<strong>Fetch HTML</strong> - Selenium downloads the HTML content (bypasses bot protection)
			</li>
			<li>
				<strong>Clean Content</strong> - BeautifulSoup removes scripts, styles, and non-content elements
			</li>
			<li>
				<strong>AI Extraction</strong> - GPT-4 analyzes the content and extracts structured data
			</li>
			<li>
				<strong>Store Results</strong> - Extracted data is saved to Supabase
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
		margin: 0 0 0.5rem 0;
		font-size: 1.125rem;
	}

	.description {
		color: var(--color-text-secondary);
		font-size: 0.875rem;
		margin-bottom: 1.5rem;
	}

	.batch-card {
		border: 2px solid var(--color-primary);
	}

	.stats {
		display: flex;
		gap: 2rem;
		margin-bottom: 1.5rem;
	}

	.stat {
		display: flex;
		flex-direction: column;
	}

	.stat-value {
		font-size: 2rem;
		font-weight: 700;
		color: var(--color-primary);
	}

	.stat-label {
		font-size: 0.75rem;
		color: var(--color-text-secondary);
		text-transform: uppercase;
	}

	.btn-large {
		padding: 0.75rem 1.5rem;
		font-size: 1rem;
	}

	.batch-progress {
		margin-top: 1rem;
	}

	.progress-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
		font-size: 0.875rem;
	}

	.progress-bar {
		height: 8px;
		background: var(--color-bg-secondary);
		border-radius: 4px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: var(--color-primary);
		transition: width 0.3s ease;
	}

	.current-url {
		margin-top: 0.75rem;
		font-size: 0.75rem;
		color: var(--color-text-secondary);
	}

	.current-url code {
		color: var(--color-primary);
	}

	.batch-results {
		margin-top: 1rem;
		max-height: 300px;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.batch-result {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem;
		border-radius: 0.25rem;
		font-size: 0.75rem;
	}

	.batch-result.success {
		background: rgba(34, 197, 94, 0.1);
	}

	.batch-result.error {
		background: rgba(239, 68, 68, 0.1);
	}

	.result-icon {
		flex-shrink: 0;
		width: 1rem;
	}

	.batch-result.success .result-icon {
		color: var(--color-success);
	}

	.batch-result.error .result-icon {
		color: var(--color-danger);
	}

	.result-url {
		flex: 1;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.result-message {
		color: var(--color-text-secondary);
		flex-shrink: 0;
	}

	.url-preview-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		max-height: 300px;
		overflow-y: auto;
	}

	.url-preview {
		display: grid;
		grid-template-columns: 150px 120px 1fr;
		gap: 1rem;
		padding: 0.5rem;
		background: var(--color-bg-secondary);
		border-radius: 0.25rem;
		font-size: 0.75rem;
	}

	.casino-name {
		font-weight: 500;
	}

	.config-name {
		color: var(--color-text-secondary);
	}

	.page-url {
		color: var(--color-primary);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.scrape-options {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.option-group h3 {
		margin: 0 0 0.25rem 0;
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

	.btn-sm {
		padding: 0.25rem 0.5rem;
		font-size: 0.75rem;
	}
</style>
