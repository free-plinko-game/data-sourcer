import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import getSupabase from '$lib/server/db';

export const GET: RequestHandler = async ({ params }) => {
	const supabase = getSupabase();

	const { data, error } = await supabase
		.from('scraped_data')
		.select(
			`
			*,
			casino:casinos(id, name, base_url)
		`
		)
		.eq('id', params.id)
		.single();

	if (error || !data) {
		return json({ error: 'Data not found' }, { status: 404 });
	}

	return json(data);
};

export const DELETE: RequestHandler = async ({ params }) => {
	const supabase = getSupabase();

	const { error } = await supabase.from('scraped_data').delete().eq('id', params.id);

	if (error) {
		return json({ error: 'Failed to delete data' }, { status: 500 });
	}

	return json({ success: true });
};
