<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	let showRawJson = $state(false);
	let merging = $state(false);
	let mergeMessage = $state<{ success: boolean; message: string } | null>(null);

	function copyToClipboard(text: string) {
		navigator.clipboard.writeText(text);
	}

	function downloadJson() {
		if (!data.casino.combined_data) return;
		const blob = new Blob([JSON.stringify(data.casino.combined_data, null, 2)], {
			type: 'application/json'
		});
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `${data.casino.name.toLowerCase().replace(/\s+/g, '-')}-data.json`;
		a.click();
		URL.revokeObjectURL(url);
	}

	async function mergeData() {
		merging = true;
		mergeMessage = null;

		try {
			const response = await fetch(`/api/casinos/${data.casino.id}/merge`, {
				method: 'POST'
			});
			const result = await response.json();

			if (result.success) {
				mergeMessage = { success: true, message: 'Data merged successfully!' };
				// Reload to show updated data
				window.location.reload();
			} else {
				mergeMessage = { success: false, message: result.error || 'Merge failed' };
			}
		} catch (err) {
			mergeMessage = { success: false, message: 'Network error' };
		} finally {
			merging = false;
		}
	}

	function viewExtractedData(item: (typeof data.scrapedData)[0]) {
		const dataStr = JSON.stringify(item.extracted_data, null, 2);
		alert(dataStr);
	}
</script>

<svelte:head>
	<title>{data.casino.name} Data | Data Sourcer</title>
</svelte:head>

<div class="casino-data-page">
	<!-- Breadcrumb -->
	<nav class="breadcrumb">
		<a href="/casinos">All Casinos</a>
		<span class="separator">/</span>
		<a href="/casinos/{data.casino.id}">{data.casino.name}</a>
		<span class="separator">/</span>
		<span class="current">Data</span>
	</nav>

	<div class="page-header">
		<div class="header-info">
			<h1>{data.casino.name}</h1>
			<p class="subtitle">Combined scraped data from all sources</p>
		</div>
		<div class="header-actions">
			<a href="/casinos/{data.casino.id}" class="btn btn-secondary">Edit Casino</a>
			<a href="/scraper" class="btn btn-primary">Run Scraper</a>
		</div>
	</div>

	<!-- Merge Action -->
	{#if data.scrapedData.length > 0}
		<div class="card merge-card">
			<div class="merge-info">
				<h3>Merge Scraped Data</h3>
				<p>
					Combine all {data.scrapedData.filter((d) => d.status === 'completed').length} completed scrapes
					into a single combined dataset.
				</p>
			</div>
			<button class="btn btn-primary" onclick={mergeData} disabled={merging}>
				{merging ? 'Merging...' : 'Merge All Data'}
			</button>
		</div>

		{#if mergeMessage}
			<div class="merge-message {mergeMessage.success ? 'success' : 'error'}">
				{mergeMessage.message}
			</div>
		{/if}
	{/if}

	<!-- Combined Data View -->
	{#if data.casino.combined_data}
		<div class="card combined-data-card">
			<div class="combined-header">
				<div>
					<h2>Combined Data</h2>
					{#if data.casino.combined_data_updated_at}
						<p class="combined-meta">
							Last updated: {new Date(data.casino.combined_data_updated_at).toLocaleString()}
							{#if data.casino.combined_data.sources_count}
								| {data.casino.combined_data.sources_count} sources merged
							{/if}
						</p>
					{/if}
				</div>
				<div class="combined-actions">
					<button class="btn btn-secondary btn-sm" onclick={() => (showRawJson = !showRawJson)}>
						{showRawJson ? 'Show Table' : 'Show JSON'}
					</button>
					<button
						class="btn btn-secondary btn-sm"
						onclick={() => copyToClipboard(JSON.stringify(data.casino.combined_data, null, 2))}
					>
						Copy JSON
					</button>
					<button class="btn btn-primary btn-sm" onclick={downloadJson}> Download </button>
				</div>
			</div>

			{#if showRawJson}
				<pre class="json-view">{JSON.stringify(data.casino.combined_data, null, 2)}</pre>
			{:else}
				<div class="data-grid">
					{#each Object.entries(data.casino.combined_data) as [key, value]}
						{#if key !== 'source_urls' && key !== 'merged_at' && key !== 'sources_count'}
							<div class="data-row">
								<span class="data-key">{key}</span>
								<span class="data-value">
									{#if value === null}
										<em class="null-value">null</em>
									{:else if typeof value === 'object'}
										{JSON.stringify(value)}
									{:else}
										{value}
									{/if}
								</span>
							</div>
						{/if}
					{/each}
				</div>

				{#if data.casino.combined_data.source_urls}
					<div class="sources-section">
						<h4>Source URLs ({data.casino.combined_data.source_urls.length})</h4>
						<ul class="source-urls">
							{#each data.casino.combined_data.source_urls as url}
								<li><a href={url} target="_blank" rel="noopener">{url}</a></li>
							{/each}
						</ul>
					</div>
				{/if}
			{/if}
		</div>
	{:else}
		<div class="card empty-data">
			<p>No combined data yet.</p>
			<p class="hint">
				Run the scraper to collect data, then click "Merge All Data" to combine it.
			</p>
		</div>
	{/if}

	<!-- Individual Scrape Records -->
	{#if data.scrapedData.length > 0}
		<div class="card">
			<h3>Individual Scrape Records ({data.scrapedData.length})</h3>
			<table class="table">
				<thead>
					<tr>
						<th>Source URL</th>
						<th>Config</th>
						<th>Status</th>
						<th>Scraped At</th>
						<th>Actions</th>
					</tr>
				</thead>
				<tbody>
					{#each data.scrapedData as item}
						<tr class:failed-row={item.status === 'failed'}>
							<td class="url-cell">
								<a href={item.source_url} target="_blank" rel="noopener">{item.source_url}</a>
							</td>
							<td>{item.config?.name || '-'}</td>
							<td>
								<span
									class="badge badge-{item.status === 'completed'
										? 'success'
										: item.status === 'failed'
											? 'danger'
											: 'warning'}"
								>
									{item.status}
								</span>
							</td>
							<td>{new Date(item.scraped_at).toLocaleString()}</td>
							<td>
								{#if item.extracted_data}
									<button class="btn btn-secondary btn-sm" onclick={() => viewExtractedData(item)}>
										View
									</button>
								{/if}
							</td>
						</tr>
						{#if item.status === 'failed' && item.error_message}
							<tr class="error-row">
								<td colspan="5">
									<div class="error-detail">
										<strong>Error:</strong> {item.error_message}
									</div>
								</td>
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		</div>
	{:else}
		<div class="card empty-scrapes">
			<p>No scrape records found for this casino.</p>
			<a href="/scraper" class="btn btn-primary">Go to Scraper</a>
		</div>
	{/if}
</div>

<style>
	.breadcrumb {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 1.5rem;
		font-size: 0.875rem;
	}

	.breadcrumb a {
		color: var(--color-text-secondary);
		text-decoration: none;
	}

	.breadcrumb a:hover {
		color: var(--color-primary);
	}

	.breadcrumb .separator {
		color: var(--color-text-secondary);
	}

	.breadcrumb .current {
		color: var(--color-text);
		font-weight: 500;
	}

	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 1.5rem;
	}

	.page-header h1 {
		margin: 0;
	}

	.subtitle {
		color: var(--color-text-secondary);
		margin: 0.25rem 0 0 0;
	}

	.header-actions {
		display: flex;
		gap: 0.5rem;
	}

	/* Merge Card */
	.merge-card {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		background: var(--color-bg-secondary);
	}

	.merge-info h3 {
		margin: 0 0 0.25rem 0;
		font-size: 0.875rem;
	}

	.merge-info p {
		margin: 0;
		font-size: 0.75rem;
		color: var(--color-text-secondary);
	}

	.merge-message {
		padding: 0.75rem;
		border-radius: 0.375rem;
		margin-bottom: 1rem;
		font-size: 0.875rem;
	}

	.merge-message.success {
		background: rgba(34, 197, 94, 0.1);
		border: 1px solid var(--color-success);
		color: var(--color-success);
	}

	.merge-message.error {
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid var(--color-danger);
		color: var(--color-danger);
	}

	/* Combined Data Card */
	.combined-data-card {
		margin-bottom: 1.5rem;
		border: 2px solid var(--color-primary);
	}

	.combined-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 1rem;
	}

	.combined-header h2 {
		margin: 0;
		font-size: 1.125rem;
	}

	.combined-meta {
		color: var(--color-text-secondary);
		font-size: 0.75rem;
		margin: 0.25rem 0 0 0;
	}

	.combined-actions {
		display: flex;
		gap: 0.5rem;
	}

	.json-view {
		background: var(--color-bg-secondary);
		border-radius: 0.375rem;
		padding: 1rem;
		overflow-x: auto;
		font-size: 0.75rem;
		max-height: 500px;
		overflow-y: auto;
	}

	.data-grid {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.data-row {
		display: grid;
		grid-template-columns: 200px 1fr;
		gap: 1rem;
		padding: 0.5rem;
		background: var(--color-bg-secondary);
		border-radius: 0.25rem;
	}

	.data-key {
		font-weight: 500;
		color: var(--color-primary);
		font-size: 0.875rem;
	}

	.data-value {
		font-size: 0.875rem;
		word-break: break-word;
	}

	.null-value {
		color: var(--color-text-secondary);
	}

	.sources-section {
		margin-top: 1.5rem;
		padding-top: 1rem;
		border-top: 1px solid var(--color-border);
	}

	.sources-section h4 {
		margin: 0 0 0.75rem 0;
		font-size: 0.875rem;
		color: var(--color-text-secondary);
	}

	.source-urls {
		list-style: none;
		padding: 0;
		margin: 0;
		font-size: 0.75rem;
	}

	.source-urls li {
		padding: 0.25rem 0;
	}

	.source-urls a {
		color: var(--color-text-secondary);
		text-decoration: none;
	}

	.source-urls a:hover {
		color: var(--color-primary);
	}

	/* Empty states */
	.empty-data,
	.empty-scrapes {
		text-align: center;
		padding: 2rem;
	}

	.empty-data p,
	.empty-scrapes p {
		color: var(--color-text-secondary);
		margin: 0 0 0.5rem 0;
	}

	.hint {
		font-size: 0.875rem;
	}

	/* Table */
	.card h3 {
		margin: 0 0 1rem 0;
		font-size: 0.875rem;
		color: var(--color-text-secondary);
	}

	.url-cell {
		max-width: 300px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.url-cell a {
		color: var(--color-text-secondary);
		text-decoration: none;
	}

	.url-cell a:hover {
		color: var(--color-primary);
	}

	.btn-sm {
		padding: 0.25rem 0.5rem;
		font-size: 0.75rem;
	}

	.failed-row {
		opacity: 0.7;
	}

	.error-row td {
		padding: 0 !important;
		border-top: none !important;
	}

	.error-detail {
		background: rgba(239, 68, 68, 0.1);
		border-left: 3px solid var(--color-danger);
		padding: 0.5rem 0.75rem;
		font-size: 0.75rem;
		color: var(--color-danger);
		margin-bottom: 0.5rem;
	}
</style>
