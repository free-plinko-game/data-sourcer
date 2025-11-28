import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import getSupabase from '$lib/server/db';

// GET /api/jobs - List all scrape jobs
export const GET: RequestHandler = async ({ url }) => {
	const supabase = getSupabase();
	const casinoId = url.searchParams.get('casino_id');

	let query = supabase
		.from('scrape_jobs')
		.select('*, casinos(name)')
		.order('started_at', { ascending: false });

	if (casinoId) {
		query = query.eq('casino_id', casinoId);
	}

	const { data, error } = await query;

	if (error) {
		return json({ error: error.message }, { status: 500 });
	}

	return json(data);
};

// POST /api/jobs - Create a new scrape job
export const POST: RequestHandler = async ({ request }) => {
	const supabase = getSupabase();
	const body = await request.json();

	const { casino_id, name, total_urls } = body;

	const { data, error } = await supabase
		.from('scrape_jobs')
		.insert({
			casino_id: casino_id || null,
			name: name || `Batch Scrape ${new Date().toLocaleString()}`,
			status: 'running',
			total_urls: total_urls || 0
		})
		.select()
		.single();

	if (error) {
		return json({ error: error.message }, { status: 500 });
	}

	return json(data, { status: 201 });
};
