import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import getSupabase from '$lib/server/db';

// GET /api/configs - List all configs (optionally filtered by casino_id)
export const GET: RequestHandler = async ({ url }) => {
	const supabase = getSupabase();
	const casinoId = url.searchParams.get('casino_id');

	let query = supabase
		.from('scrape_configs')
		.select('*, casinos(name)')
		.order('created_at', { ascending: false });

	if (casinoId) {
		query = query.eq('casino_id', casinoId);
	}

	const { data, error } = await query;

	if (error) {
		return json({ error: error.message }, { status: 500 });
	}

	return json(data);
};

// POST /api/configs - Create a new scrape config
export const POST: RequestHandler = async ({ request }) => {
	const supabase = getSupabase();
	const body = await request.json();

	const { casino_id, name, page_url, requires_login, extraction_type, custom_prompt, is_active } = body;

	if (!casino_id || !name || !page_url) {
		return json({ error: 'casino_id, name, and page_url are required' }, { status: 400 });
	}

	const { data, error } = await supabase
		.from('scrape_configs')
		.insert({
			casino_id,
			name,
			page_url,
			requires_login: requires_login ?? false,
			extraction_type: extraction_type ?? 'casino_info',
			custom_prompt: custom_prompt ?? null,
			is_active: is_active ?? true
		})
		.select()
		.single();

	if (error) {
		return json({ error: error.message }, { status: 500 });
	}

	return json(data, { status: 201 });
};
