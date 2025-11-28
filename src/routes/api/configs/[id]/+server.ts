import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import getSupabase from '$lib/server/db';

// GET /api/configs/:id - Get a single config
export const GET: RequestHandler = async ({ params }) => {
	const supabase = getSupabase();

	const { data, error } = await supabase
		.from('scrape_configs')
		.select('*, casinos(name)')
		.eq('id', params.id)
		.single();

	if (error) {
		return json({ error: error.message }, { status: error.code === 'PGRST116' ? 404 : 500 });
	}

	return json(data);
};

// PATCH /api/configs/:id - Update a config
export const PATCH: RequestHandler = async ({ params, request }) => {
	const supabase = getSupabase();
	const body = await request.json();

	const { data, error } = await supabase
		.from('scrape_configs')
		.update(body)
		.eq('id', params.id)
		.select()
		.single();

	if (error) {
		return json({ error: error.message }, { status: 500 });
	}

	return json(data);
};

// DELETE /api/configs/:id - Delete a config
export const DELETE: RequestHandler = async ({ params }) => {
	const supabase = getSupabase();

	const { error } = await supabase
		.from('scrape_configs')
		.delete()
		.eq('id', params.id);

	if (error) {
		return json({ error: error.message }, { status: 500 });
	}

	return json({ success: true });
};
