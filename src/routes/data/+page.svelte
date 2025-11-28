<script lang="ts">
	import type { PageData } from './$types';
	import { goto } from '$app/navigation';

	let { data }: { data: PageData } = $props();

	let filterCasino = $state('');
	let filterStatus = $state('');
	let selectedJob = $state(data.jobId || '');

	$effect(() => {
		// Reload data when filters change
		if (filterCasino !== '' || filterStatus !== '') {
			loadData();
		}
	});

	let scrapedData = $state(data.scrapedData);
	let loading = $state(false);
	let showRawJson = $state(false);

	async function loadData() {
		loading = true;
		const params = new URLSearchParams();
		if (filterCasino) params.set('casino_id', filterCasino);
		if (filterStatus) params.set('status', filterStatus);

		const response = await fetch(`/api/data?${params}`);
		const result = await response.json();
		scrapedData = result.data || [];
		loading = false;
	}

	async function deleteRecord(id: string) {
		if (!confirm('Delete this record?')) return;

		await fetch(`/api/data/${id}`, { method: 'DELETE' });
		scrapedData = scrapedData.filter((d) => d.id !== id);
	}

	function viewData(item: (typeof scrapedData)[0]) {
		const dataStr = JSON.stringify(item.extracted_data, null, 2);
		alert(dataStr);
	}

	function selectJob(jobId: string) {
		if (jobId) {
			goto(`/data?job=${jobId}`);
		} else {
			goto('/data');
		}
	}

	function copyToClipboard(text: string) {
		navigator.clipboard.writeText(text);
	}

	function downloadJson() {
		if (!data.job?.combined_data) return;
		const blob = new Blob([JSON.stringify(data.job.combined_data, null, 2)], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `combined-data-${data.job.id}.json`;
		a.click();
		URL.revokeObjectURL(url);
	}
</script>

<svelte:head>
	<title>Data | Data Sourcer</title>
</svelte:head>

<div class="data-page">
	<div class="page-header">
		<h1>Scraped Data</h1>
		<div class="export-buttons">
			<a href="/api/export/json" class="btn btn-secondary" download>Export JSON</a>
			<a href="/api/export/csv" class="btn btn-secondary" download>Export CSV</a>
		</div>
	</div>

	<!-- Job Selector -->
	{#if data.recentJobs && data.recentJobs.length > 0}
		<div class="card job-selector">
			<h3>Batch Jobs</h3>
			<div class="job-list">
				<button
					class="job-item"
					class:active={!selectedJob}
					onclick={() => selectJob('')}
				>
					<span class="job-name">All Data</span>
				</button>
				{#each data.recentJobs as job}
					<button
						class="job-item"
						class:active={selectedJob === job.id}
						onclick={() => selectJob(job.id)}
					>
						<span class="job-name">{job.name || 'Unnamed Job'}</span>
						<span class="job-meta">
							{job.completed_urls}/{job.total_urls} URLs
							<span class="badge badge-{job.status === 'completed' ? 'success' : job.status === 'failed' ? 'danger' : 'warning'}">
								{job.status}
							</span>
						</span>
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Combined Data View (when viewing a job) -->
	{#if data.job && data.job.combined_data}
		<div class="card combined-data-card">
			<div class="combined-header">
				<h2>Combined Data</h2>
				<div class="combined-actions">
					<button class="btn btn-secondary btn-sm" onclick={() => showRawJson = !showRawJson}>
						{showRawJson ? 'Show Table' : 'Show JSON'}
					</button>
					<button class="btn btn-secondary btn-sm" onclick={() => copyToClipboard(JSON.stringify(data.job?.combined_data, null, 2))}>
						Copy JSON
					</button>
					<button class="btn btn-primary btn-sm" onclick={downloadJson}>
						Download
					</button>
				</div>
			</div>
			<p class="combined-meta">
				Merged from {data.job.combined_data.sources_count || 0} sources
				{#if data.job.combined_data.merged_at}
					on {new Date(data.job.combined_data.merged_at).toLocaleString()}
				{/if}
			</p>

			{#if showRawJson}
				<pre class="json-view">{JSON.stringify(data.job.combined_data, null, 2)}</pre>
			{:else}
				<div class="data-grid">
					{#each Object.entries(data.job.combined_data) as [key, value]}
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

				{#if data.job.combined_data.source_urls}
					<div class="sources-section">
						<h4>Source URLs ({data.job.combined_data.source_urls.length})</h4>
						<ul class="source-urls">
							{#each data.job.combined_data.source_urls as url}
								<li><a href={url} target="_blank" rel="noopener">{url}</a></li>
							{/each}
						</ul>
					</div>
				{/if}
			{/if}
		</div>
	{/if}

	<!-- Filters (only when not viewing a specific job) -->
	{#if !data.jobId}
		<div class="card filters">
			<div class="filter-row">
				<div class="filter-group">
					<label class="label">Casino</label>
					<select class="input" bind:value={filterCasino} onchange={loadData}>
						<option value="">All Casinos</option>
						{#each data.casinos as casino}
							<option value={casino.id}>{casino.name}</option>
						{/each}
					</select>
				</div>
				<div class="filter-group">
					<label class="label">Status</label>
					<select class="input" bind:value={filterStatus} onchange={loadData}>
						<option value="">All Statuses</option>
						<option value="completed">Completed</option>
						<option value="failed">Failed</option>
						<option value="processing">Processing</option>
					</select>
				</div>
			</div>
		</div>
	{/if}

	<!-- Data Table -->
	{#if loading}
		<div class="card loading">Loading...</div>
	{:else if scrapedData.length === 0}
		<div class="card empty">
			<p>No scraped data found.</p>
			<a href="/scraper" class="btn btn-primary">Run Scraper</a>
		</div>
	{:else}
		<div class="card">
			<h3>Individual Scrape Records</h3>
			<table class="table">
				<thead>
					<tr>
						<th>Casino</th>
						<th>Source URL</th>
						<th>Status</th>
						<th>Scraped At</th>
						<th>Actions</th>
					</tr>
				</thead>
				<tbody>
					{#each scrapedData as item}
						<tr>
							<td>{item.casino?.name || 'Unknown'}</td>
							<td class="url-cell">
								<a href={item.source_url} target="_blank" rel="noopener">{item.source_url}</a>
							</td>
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
							<td class="actions-cell">
								{#if item.extracted_data}
									<button class="btn btn-secondary btn-sm" onclick={() => viewData(item)}>
										View
									</button>
								{/if}
								<button class="btn btn-danger btn-sm" onclick={() => deleteRecord(item.id)}>
									Delete
								</button>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>

<style>
	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	.page-header h1 {
		margin: 0;
	}

	.export-buttons {
		display: flex;
		gap: 0.5rem;
	}

	/* Job Selector */
	.job-selector {
		margin-bottom: 1.5rem;
	}

	.job-selector h3 {
		margin: 0 0 1rem 0;
		font-size: 0.875rem;
		color: var(--color-text-secondary);
	}

	.job-list {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.job-item {
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border);
		border-radius: 0.375rem;
		padding: 0.5rem 0.75rem;
		cursor: pointer;
		text-align: left;
		transition: all 0.2s;
	}

	.job-item:hover {
		border-color: var(--color-primary);
	}

	.job-item.active {
		background: var(--color-primary);
		border-color: var(--color-primary);
		color: white;
	}

	.job-name {
		display: block;
		font-weight: 500;
		font-size: 0.875rem;
	}

	.job-meta {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		font-size: 0.75rem;
		color: var(--color-text-secondary);
		margin-top: 0.25rem;
	}

	.job-item.active .job-meta {
		color: rgba(255, 255, 255, 0.8);
	}

	/* Combined Data Card */
	.combined-data-card {
		margin-bottom: 1.5rem;
		border: 2px solid var(--color-primary);
	}

	.combined-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.combined-header h2 {
		margin: 0;
		font-size: 1.125rem;
	}

	.combined-actions {
		display: flex;
		gap: 0.5rem;
	}

	.combined-meta {
		color: var(--color-text-secondary);
		font-size: 0.875rem;
		margin-bottom: 1rem;
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

	/* Filters */
	.filters {
		margin-bottom: 1.5rem;
	}

	.filter-row {
		display: flex;
		gap: 1rem;
	}

	.filter-group {
		flex: 1;
		max-width: 250px;
	}

	.empty {
		text-align: center;
		padding: 3rem;
	}

	.empty p {
		color: var(--color-text-secondary);
		margin-bottom: 1rem;
	}

	.loading {
		text-align: center;
		padding: 2rem;
		color: var(--color-text-secondary);
	}

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

	.actions-cell {
		display: flex;
		gap: 0.5rem;
	}

	.btn-sm {
		padding: 0.25rem 0.5rem;
		font-size: 0.75rem;
	}
</style>
