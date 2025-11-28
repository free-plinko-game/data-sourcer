<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
</script>

<svelte:head>
	<title>Dashboard | Data Sourcer</title>
</svelte:head>

<div class="dashboard">
	<h1>Dashboard</h1>
	<p class="subtitle">Casino data scraping and management</p>

	<div class="stats-grid">
		<div class="card stat-card">
			<div class="stat-value">{data.stats.totalCasinos}</div>
			<div class="stat-label">Total Casinos</div>
		</div>
		<div class="card stat-card">
			<div class="stat-value">{data.stats.activeCasinos}</div>
			<div class="stat-label">Active Casinos</div>
		</div>
		<div class="card stat-card">
			<div class="stat-value">{data.stats.totalScrapes}</div>
			<div class="stat-label">Total Scrapes</div>
		</div>
		<div class="card stat-card">
			<div class="stat-value">{data.stats.recentScrapes}</div>
			<div class="stat-label">Last 24h</div>
		</div>
	</div>

	<div class="actions-section">
		<h2>Quick Actions</h2>
		<div class="action-buttons">
			<a href="/casinos/new" class="btn btn-primary">Add Casino</a>
			<a href="/scraper" class="btn btn-secondary">Run Scraper</a>
			<a href="/data" class="btn btn-secondary">View Data</a>
		</div>
	</div>

	{#if data.recentData.length > 0}
		<div class="recent-section">
			<h2>Recent Scrapes</h2>
			<div class="card">
				<table class="table">
					<thead>
						<tr>
							<th>Casino</th>
							<th>URL</th>
							<th>Status</th>
							<th>Date</th>
						</tr>
					</thead>
					<tbody>
						{#each data.recentData as item}
							<tr>
								<td>{item.casino.name}</td>
								<td class="url-cell">{item.sourceUrl}</td>
								<td>
									<span class="badge badge-{item.status === 'completed' ? 'success' : item.status === 'failed' ? 'danger' : 'warning'}">
										{item.status}
									</span>
								</td>
								<td>{new Date(item.scrapedAt).toLocaleString()}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{/if}
</div>

<style>
	.dashboard h1 {
		margin: 0;
		font-size: 1.75rem;
	}

	.subtitle {
		color: var(--color-text-secondary);
		margin: 0.5rem 0 2rem;
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 1rem;
		margin-bottom: 2rem;
	}

	.stat-card {
		text-align: center;
	}

	.stat-value {
		font-size: 2.5rem;
		font-weight: 700;
		color: var(--color-primary);
	}

	.stat-label {
		color: var(--color-text-secondary);
		font-size: 0.875rem;
		margin-top: 0.25rem;
	}

	.actions-section {
		margin-bottom: 2rem;
	}

	.actions-section h2,
	.recent-section h2 {
		font-size: 1.25rem;
		margin-bottom: 1rem;
	}

	.action-buttons {
		display: flex;
		gap: 0.75rem;
	}

	.url-cell {
		max-width: 300px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		font-size: 0.875rem;
		color: var(--color-text-secondary);
	}
</style>
