<script lang="ts">
	import { goto } from '$app/navigation';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	// Casino fields
	let name = $state(data.casino.name);
	let baseUrl = $state(data.casino.base_url);
	let loginUrl = $state(data.casino.login_url || '');
	let username = $state(data.casino.username || '');
	let password = $state('');
	let notes = $state(data.casino.notes || '');
	let isActive = $state(data.casino.is_active);
	let saving = $state(false);
	let error = $state('');
	let success = $state('');

	// Scrape URLs
	let scrapeUrls = $state(data.scrapeUrls || []);
	let newUrlName = $state('');
	let newUrlPage = $state('');
	let addingUrl = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		saving = true;
		error = '';
		success = '';

		try {
			const payload: Record<string, unknown> = {
				name,
				base_url: baseUrl,
				login_url: loginUrl || null,
				username: username || null,
				notes: notes || null,
				is_active: isActive
			};

			// Only include password if changed
			if (password) {
				payload.password = password;
			}

			const response = await fetch(`/api/casinos/${data.casino.id}`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(payload)
			});

			if (response.ok) {
				success = 'Casino updated successfully';
				password = '';
			} else {
				const result = await response.json();
				error = result.error || 'Failed to update casino';
			}
		} catch (err) {
			error = 'Network error. Please try again.';
		} finally {
			saving = false;
		}
	}

	async function handleDelete() {
		if (!confirm(`Are you sure you want to delete "${name}"? This will also delete all scraped data.`)) return;

		const response = await fetch(`/api/casinos/${data.casino.id}`, { method: 'DELETE' });
		if (response.ok) {
			goto('/casinos');
		} else {
			error = 'Failed to delete casino';
		}
	}

	async function addScrapeUrl() {
		if (!newUrlName || !newUrlPage) {
			error = 'Please enter both name and URL';
			return;
		}

		addingUrl = true;
		error = '';

		try {
			const response = await fetch('/api/configs', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					casino_id: data.casino.id,
					name: newUrlName,
					page_url: newUrlPage,
					is_active: true
				})
			});

			if (response.ok) {
				const newConfig = await response.json();
				scrapeUrls = [...scrapeUrls, newConfig];
				newUrlName = '';
				newUrlPage = '';
			} else {
				const result = await response.json();
				error = result.error || 'Failed to add URL';
			}
		} catch (err) {
			error = 'Network error. Please try again.';
		} finally {
			addingUrl = false;
		}
	}

	async function toggleUrlActive(configId: string, currentState: boolean) {
		try {
			const response = await fetch(`/api/configs/${configId}`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ is_active: !currentState })
			});

			if (response.ok) {
				scrapeUrls = scrapeUrls.map(u =>
					u.id === configId ? { ...u, is_active: !currentState } : u
				);
			}
		} catch (err) {
			console.error('Failed to toggle URL:', err);
		}
	}

	async function deleteScrapeUrl(configId: string) {
		if (!confirm('Delete this scrape URL?')) return;

		try {
			const response = await fetch(`/api/configs/${configId}`, { method: 'DELETE' });
			if (response.ok) {
				scrapeUrls = scrapeUrls.filter(u => u.id !== configId);
			}
		} catch (err) {
			console.error('Failed to delete URL:', err);
		}
	}
</script>

<svelte:head>
	<title>Edit {data.casino.name} | Data Sourcer</title>
</svelte:head>

<div class="edit-casino-page">
	<div class="page-header">
		<h1>Edit Casino</h1>
	</div>

	<div class="content-grid">
		<!-- Casino Details Form -->
		<form onsubmit={handleSubmit} class="card form-card">
			<h2>Casino Details</h2>

			{#if error}
				<div class="error-message">{error}</div>
			{/if}
			{#if success}
				<div class="success-message">{success}</div>
			{/if}

			<div class="form-group">
				<label for="name" class="label">Casino Name *</label>
				<input type="text" id="name" class="input" bind:value={name} required />
			</div>

			<div class="form-group">
				<label for="baseUrl" class="label">Base URL *</label>
				<input type="url" id="baseUrl" class="input" bind:value={baseUrl} required />
			</div>

			<div class="form-group">
				<label class="checkbox-label">
					<input type="checkbox" bind:checked={isActive} />
					<span>Active (include in scraping)</span>
				</label>
			</div>

			<div class="form-divider">
				<span>Login Credentials (for future use)</span>
			</div>

			<div class="form-group">
				<label for="loginUrl" class="label">Login Page URL</label>
				<input type="url" id="loginUrl" class="input" bind:value={loginUrl} />
			</div>

			<div class="form-row">
				<div class="form-group">
					<label for="username" class="label">Username</label>
					<input type="text" id="username" class="input" bind:value={username} />
				</div>

				<div class="form-group">
					<label for="password" class="label">Password</label>
					<input
						type="password"
						id="password"
						class="input"
						bind:value={password}
						placeholder={data.casino.password ? '••••••••' : 'Enter password'}
					/>
					{#if data.casino.password}
						<small class="hint">Leave blank to keep current password</small>
					{/if}
				</div>
			</div>

			<div class="form-group">
				<label for="notes" class="label">Notes</label>
				<textarea id="notes" class="input textarea" bind:value={notes} rows="3"></textarea>
			</div>

			<div class="form-actions">
				<button type="button" class="btn btn-danger" onclick={handleDelete}>Delete</button>
				<div class="right-actions">
					<a href="/casinos" class="btn btn-secondary">Cancel</a>
					<button type="submit" class="btn btn-primary" disabled={saving}>
						{saving ? 'Saving...' : 'Save Changes'}
					</button>
				</div>
			</div>
		</form>

		<!-- Scrape URLs Section -->
		<div class="card urls-card">
			<h2>Scrape URLs</h2>
			<p class="subtitle">Add multiple URLs to scrape for this casino</p>

			<!-- Add New URL Form -->
			<div class="add-url-form">
				<div class="form-group">
					<label for="newUrlName" class="label">Page Name</label>
					<input
						type="text"
						id="newUrlName"
						class="input"
						bind:value={newUrlName}
						placeholder="e.g., Home Page, Terms, Games"
					/>
				</div>
				<div class="form-group">
					<label for="newUrlPage" class="label">Page URL</label>
					<input
						type="url"
						id="newUrlPage"
						class="input"
						bind:value={newUrlPage}
						placeholder="https://..."
					/>
				</div>
				<button
					type="button"
					class="btn btn-primary add-url-btn"
					onclick={addScrapeUrl}
					disabled={addingUrl}
				>
					{addingUrl ? 'Adding...' : '+ Add URL'}
				</button>
			</div>

			<!-- URL List -->
			{#if scrapeUrls.length > 0}
				<div class="url-list">
					{#each scrapeUrls as urlConfig (urlConfig.id)}
						<div class="url-item" class:inactive={!urlConfig.is_active}>
							<div class="url-info">
								<span class="url-name">{urlConfig.name}</span>
								<span class="url-page">{urlConfig.page_url}</span>
							</div>
							<div class="url-actions">
								<button
									type="button"
									class="btn btn-sm"
									class:btn-secondary={urlConfig.is_active}
									class:btn-outline={!urlConfig.is_active}
									onclick={() => toggleUrlActive(urlConfig.id, urlConfig.is_active)}
								>
									{urlConfig.is_active ? 'Active' : 'Inactive'}
								</button>
								<button
									type="button"
									class="btn btn-sm btn-danger-outline"
									onclick={() => deleteScrapeUrl(urlConfig.id)}
								>
									Delete
								</button>
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<div class="empty-state">
					<p>No scrape URLs configured yet.</p>
					<p class="hint">Add URLs above to start scraping multiple pages.</p>
				</div>
			{/if}
		</div>
	</div>
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

	.content-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}

	@media (max-width: 1024px) {
		.content-grid {
			grid-template-columns: 1fr;
		}
	}

	.form-card h2,
	.urls-card h2 {
		margin-top: 0;
		margin-bottom: 0.5rem;
	}

	.subtitle {
		color: var(--color-text-secondary);
		font-size: 0.875rem;
		margin-bottom: 1.5rem;
	}

	.form-group {
		margin-bottom: 1rem;
	}

	.form-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.form-divider {
		margin: 1.5rem 0;
		text-align: center;
		position: relative;
		color: var(--color-text-secondary);
		font-size: 0.875rem;
	}

	.form-divider::before,
	.form-divider::after {
		content: '';
		position: absolute;
		top: 50%;
		width: 40%;
		height: 1px;
		background-color: var(--color-border);
	}

	.form-divider::before {
		left: 0;
	}

	.form-divider::after {
		right: 0;
	}

	.textarea {
		resize: vertical;
		min-height: 80px;
	}

	.checkbox-label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
	}

	.checkbox-label input {
		width: 1rem;
		height: 1rem;
	}

	.hint {
		color: var(--color-text-secondary);
		font-size: 0.75rem;
		margin-top: 0.25rem;
		display: block;
	}

	.form-actions {
		display: flex;
		justify-content: space-between;
		margin-top: 1.5rem;
	}

	.right-actions {
		display: flex;
		gap: 0.75rem;
	}

	.error-message {
		background-color: rgba(239, 68, 68, 0.1);
		border: 1px solid var(--color-danger);
		color: var(--color-danger);
		padding: 0.75rem;
		border-radius: 0.375rem;
		margin-bottom: 1rem;
	}

	.success-message {
		background-color: rgba(34, 197, 94, 0.1);
		border: 1px solid var(--color-success);
		color: var(--color-success);
		padding: 0.75rem;
		border-radius: 0.375rem;
		margin-bottom: 1rem;
	}

	/* URL Management Styles */
	.add-url-form {
		background: var(--color-bg-secondary);
		padding: 1rem;
		border-radius: 0.5rem;
		margin-bottom: 1.5rem;
	}

	.add-url-btn {
		width: 100%;
		margin-top: 0.5rem;
	}

	.url-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.url-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem;
		background: var(--color-bg-secondary);
		border-radius: 0.375rem;
		gap: 1rem;
	}

	.url-item.inactive {
		opacity: 0.6;
	}

	.url-info {
		flex: 1;
		min-width: 0;
	}

	.url-name {
		display: block;
		font-weight: 500;
		margin-bottom: 0.25rem;
	}

	.url-page {
		display: block;
		font-size: 0.75rem;
		color: var(--color-text-secondary);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.url-actions {
		display: flex;
		gap: 0.5rem;
		flex-shrink: 0;
	}

	.btn-sm {
		padding: 0.25rem 0.5rem;
		font-size: 0.75rem;
	}

	.btn-outline {
		background: transparent;
		border: 1px solid var(--color-border);
		color: var(--color-text-secondary);
	}

	.btn-danger-outline {
		background: transparent;
		border: 1px solid var(--color-danger);
		color: var(--color-danger);
	}

	.btn-danger-outline:hover {
		background: var(--color-danger);
		color: white;
	}

	.empty-state {
		text-align: center;
		padding: 2rem;
		color: var(--color-text-secondary);
	}

	.empty-state p {
		margin: 0.25rem 0;
	}
</style>
