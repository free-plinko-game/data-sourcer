import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import getSupabase from '$lib/server/db';

export const GET: RequestHandler = async ({ url }) => {
	const supabase = getSupabase();

	const casinoId = url.searchParams.get('casino_id');
	const status = url.searchParams.get('status') || 'completed';

	let query = supabase
		.from('scraped_data')
		.select(
			`
			id,
			source_url,
			extracted_data,
			scraped_at,
			processed_at,
			casino:casinos(id, name, base_url)
		`
		)
		.eq('status', status)
		.order('scraped_at', { ascending: false });

	if (casinoId) {
		query = query.eq('casino_id', casinoId);
	}

	const { data, error } = await query;

	if (error) {
		return json({ error: 'Failed to export data' }, { status: 500 });
	}

	// Format for export - flatten the data
	const exportData = (data || []).map((item) => ({
		id: item.id,
		casino_name: item.casino?.name,
		casino_url: item.casino?.base_url,
		source_url: item.source_url,
		scraped_at: item.scraped_at,
		processed_at: item.processed_at,
		...item.extracted_data
	}));

	return new Response(JSON.stringify(exportData, null, 2), {
		headers: {
			'Content-Type': 'application/json',
			'Content-Disposition': `attachment; filename="casino-data-${new Date().toISOString().split('T')[0]}.json"`
		}
	});
};
