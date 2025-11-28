<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	let filterCasino = $state('');
	let filterStatus = $state('');

	$effect(() => {
		// Reload data when filters change
		if (filterCasino !== '' || filterStatus !== '') {
			loadData();
		}
	});

	let scrapedData = $state(data.scrapedData);
	let loading = $state(false);

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

	{#if loading}
		<div class="card loading">Loading...</div>
	{:else if scrapedData.length === 0}
		<div class="card empty">
			<p>No scraped data found.</p>
			<a href="/scraper" class="btn btn-primary">Run Scraper</a>
		</div>
	{:else}
		<div class="card">
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
