<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	async function deleteCasino(id: string, name: string) {
		if (!confirm(`Are you sure you want to delete "${name}"?`)) return;

		const response = await fetch(`/api/casinos/${id}`, { method: 'DELETE' });
		if (response.ok) {
			window.location.reload();
		} else {
			alert('Failed to delete casino');
		}
	}

	async function toggleActive(id: string, currentState: boolean) {
		const response = await fetch(`/api/casinos/${id}`, {
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ is_active: !currentState })
		});
		if (response.ok) {
			window.location.reload();
		}
	}
</script>

<svelte:head>
	<title>Casinos | Data Sourcer</title>
</svelte:head>

<div class="casinos-page">
	<div class="page-header">
		<h1>Casinos</h1>
		<a href="/casinos/new" class="btn btn-primary">Add Casino</a>
	</div>

	{#if data.casinos.length === 0}
		<div class="card empty-state">
			<p>No casinos added yet.</p>
			<a href="/casinos/new" class="btn btn-primary">Add Your First Casino</a>
		</div>
	{:else}
		<div class="card">
			<table class="table">
				<thead>
					<tr>
						<th>Name</th>
						<th>URL</th>
						<th>Status</th>
						<th>Scrapes</th>
						<th>Actions</th>
					</tr>
				</thead>
				<tbody>
					{#each data.casinos as casino}
						<tr>
							<td class="name-cell">
								<strong>{casino.name}</strong>
							</td>
							<td class="url-cell">
								<a href={casino.base_url} target="_blank" rel="noopener">{casino.base_url}</a>
							</td>
							<td>
								<button
									class="badge badge-{casino.is_active ? 'success' : 'neutral'}"
									onclick={() => toggleActive(casino.id, casino.is_active)}
								>
									{casino.is_active ? 'Active' : 'Inactive'}
								</button>
							</td>
							<td>
								{#if casino._count.scrapedData > 0}
									{casino._count.scrapedData} scrapes
								{:else}
									<span class="text-muted">None</span>
								{/if}
							</td>
							<td class="actions-cell">
								<a href="/casinos/{casino.id}" class="btn btn-secondary btn-sm">Edit</a>
								<button
									class="btn btn-danger btn-sm"
									onclick={() => deleteCasino(casino.id, casino.name)}
								>
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

	.empty-state {
		text-align: center;
		padding: 3rem;
	}

	.empty-state p {
		color: var(--color-text-secondary);
		margin-bottom: 1rem;
	}

	.url-cell {
		max-width: 250px;
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

	.text-muted {
		color: var(--color-text-secondary);
	}

	.badge {
		cursor: pointer;
		border: none;
	}
</style>
