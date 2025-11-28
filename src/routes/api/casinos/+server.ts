import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import getSupabase from '$lib/server/db';

export const GET: RequestHandler = async ({ url }) => {
	const supabase = getSupabase();
	const activeOnly = url.searchParams.get('active') === 'true';

	let query = supabase
		.from('casinos')
		.select('id, name, base_url, login_url, is_active, created_at, updated_at')
		.order('name');

	if (activeOnly) {
		query = query.eq('is_active', true);
	}

	const { data: casinos, error } = await query;

	if (error) {
		return json({ error: 'Failed to fetch casinos' }, { status: 500 });
	}

	return json(casinos);
};

export const POST: RequestHandler = async ({ request }) => {
	const supabase = getSupabase();

	try {
		const body = await request.json();
		const { name, base_url, login_url, username, password, notes } = body;

		if (!name || !base_url) {
			return json({ error: 'Name and base_url are required' }, { status: 400 });
		}

		const { data: casino, error } = await supabase
			.from('casinos')
			.insert({
				name,
				base_url,
				login_url: login_url || null,
				username: username || null,
				password: password || null,
				notes: notes || null
			})
			.select()
			.single();

		if (error) {
			return json({ error: 'Failed to create casino' }, { status: 500 });
		}

		return json(casino, { status: 201 });
	} catch {
		return json({ error: 'Invalid request body' }, { status: 400 });
	}
};
