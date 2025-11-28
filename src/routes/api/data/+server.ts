import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import getSupabase from '$lib/server/db';

export const GET: RequestHandler = async ({ url }) => {
	const supabase = getSupabase();

	const casinoId = url.searchParams.get('casino_id');
	const status = url.searchParams.get('status');
	const limit = parseInt(url.searchParams.get('limit') || '100');
	const offset = parseInt(url.searchParams.get('offset') || '0');

	let query = supabase
		.from('scraped_data')
		.select(
			`
			id,
			casino_id,
			source_url,
			extracted_data,
			status,
			error_message,
			scraped_at,
			processed_at,
			casino:casinos(id, name, base_url)
		`
		)
		.order('scraped_at', { ascending: false })
		.range(offset, offset + limit - 1);

	if (casinoId) {
		query = query.eq('casino_id', casinoId);
	}

	if (status) {
		query = query.eq('status', status);
	}

	const { data, error, count } = await query;

	if (error) {
		return json({ error: 'Failed to fetch data' }, { status: 500 });
	}

	// Get total count
	let countQuery = supabase.from('scraped_data').select('*', { count: 'exact', head: true });

	if (casinoId) {
		countQuery = countQuery.eq('casino_id', casinoId);
	}
	if (status) {
		countQuery = countQuery.eq('status', status);
	}

	const { count: totalCount } = await countQuery;

	return json({
		data,
		pagination: {
			total: totalCount || 0,
			limit,
			offset
		}
	});
};
