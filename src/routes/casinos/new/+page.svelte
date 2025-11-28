<script lang="ts">
	import { goto } from '$app/navigation';

	let name = $state('');
	let baseUrl = $state('');
	let loginUrl = $state('');
	let username = $state('');
	let password = $state('');
	let notes = $state('');
	let saving = $state(false);
	let error = $state('');

	async function handleSubmit(e: Event) {
		e.preventDefault();
		saving = true;
		error = '';

		try {
			const response = await fetch('/api/casinos', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					name,
					base_url: baseUrl,
					login_url: loginUrl || null,
					username: username || null,
					password: password || null,
					notes: notes || null
				})
			});

			if (response.ok) {
				const data = await response.json();
				goto(`/casinos/${data.id}`);
			} else {
				const data = await response.json();
				error = data.error || 'Failed to create casino';
			}
		} catch (err) {
			error = 'Network error. Please try again.';
		} finally {
			saving = false;
		}
	}
</script>

<svelte:head>
	<title>Add Casino | Data Sourcer</title>
</svelte:head>

<div class="add-casino-page">
	<h1>Add Casino</h1>

	<form onsubmit={handleSubmit} class="card form-card">
		{#if error}
			<div class="error-message">{error}</div>
		{/if}

		<div class="form-group">
			<label for="name" class="label">Casino Name *</label>
			<input
				type="text"
				id="name"
				class="input"
				bind:value={name}
				required
				placeholder="e.g., Bet365"
			/>
		</div>

		<div class="form-group">
			<label for="baseUrl" class="label">Base URL *</label>
			<input
				type="url"
				id="baseUrl"
				class="input"
				bind:value={baseUrl}
				required
				placeholder="https://example-casino.com.au"
			/>
		</div>

		<div class="form-divider">
			<span>Login Credentials (Optional)</span>
		</div>

		<div class="form-group">
			<label for="loginUrl" class="label">Login Page URL</label>
			<input
				type="url"
				id="loginUrl"
				class="input"
				bind:value={loginUrl}
				placeholder="https://example-casino.com.au/login"
			/>
		</div>

		<div class="form-row">
			<div class="form-group">
				<label for="username" class="label">Username</label>
				<input
					type="text"
					id="username"
					class="input"
					bind:value={username}
					placeholder="username or email"
				/>
			</div>

			<div class="form-group">
				<label for="password" class="label">Password</label>
				<input
					type="password"
					id="password"
					class="input"
					bind:value={password}
					placeholder="••••••••"
				/>
			</div>
		</div>

		<div class="form-group">
			<label for="notes" class="label">Notes</label>
			<textarea
				id="notes"
				class="input textarea"
				bind:value={notes}
				rows="3"
				placeholder="Any additional notes about this casino..."
			></textarea>
		</div>

		<div class="form-actions">
			<a href="/casinos" class="btn btn-secondary">Cancel</a>
			<button type="submit" class="btn btn-primary" disabled={saving}>
				{saving ? 'Saving...' : 'Add Casino'}
			</button>
		</div>
	</form>
</div>

<style>
	.add-casino-page h1 {
		margin-bottom: 1.5rem;
	}

	.form-card {
		max-width: 600px;
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

	.form-actions {
		display: flex;
		gap: 0.75rem;
		justify-content: flex-end;
		margin-top: 1.5rem;
	}

	.error-message {
		background-color: rgba(239, 68, 68, 0.1);
		border: 1px solid var(--color-danger);
		color: var(--color-danger);
		padding: 0.75rem;
		border-radius: 0.375rem;
		margin-bottom: 1rem;
	}
</style>
