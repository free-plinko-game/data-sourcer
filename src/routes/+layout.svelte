<script lang="ts">
	import '../app.css';

	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();
</script>

<div class="app">
	<nav class="sidebar">
		<div class="logo">
			<h1>Data Sourcer</h1>
		</div>
		<ul class="nav-links">
			<li><a href="/">Dashboard</a></li>
			<li><a href="/casinos">Casinos</a></li>
			<li><a href="/scraper">Scraper</a></li>
			<li><a href="/data">Data</a></li>
			<li><a href="/api-docs">API</a></li>
		</ul>
	</nav>
	<main class="content">
		{@render children?.()}
	</main>
</div>

<style>
	.app {
		display: flex;
		min-height: 100vh;
	}

	.sidebar {
		width: 220px;
		background-color: var(--color-bg-secondary);
		border-right: 1px solid var(--color-border);
		padding: 1.5rem;
		flex-shrink: 0;
	}

	.logo h1 {
		font-size: 1.25rem;
		font-weight: 700;
		color: var(--color-primary);
		margin: 0 0 2rem 0;
	}

	.nav-links {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.nav-links li {
		margin-bottom: 0.5rem;
	}

	.nav-links a {
		display: block;
		padding: 0.75rem 1rem;
		border-radius: 0.375rem;
		color: var(--color-text-secondary);
		text-decoration: none;
		transition: all 0.2s;
	}

	.nav-links a:hover {
		background-color: var(--color-bg-tertiary);
		color: var(--color-text);
	}

	.content {
		flex: 1;
		padding: 2rem;
		overflow-y: auto;
	}
</style>
