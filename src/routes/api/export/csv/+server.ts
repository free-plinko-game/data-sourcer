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
		return new Response('Failed to export data', { status: 500 });
	}

	if (!data || data.length === 0) {
		return new Response('No data to export', { status: 404 });
	}

	// Collect all possible columns from extracted_data
	const extractedKeys = new Set<string>();
	data.forEach((item) => {
		if (item.extracted_data && typeof item.extracted_data === 'object') {
			Object.keys(item.extracted_data as Record<string, unknown>).forEach((key) => extractedKeys.add(key));
		}
	});

	// Build CSV headers
	const baseHeaders = ['id', 'casino_name', 'casino_url', 'source_url', 'scraped_at', 'processed_at'];
	const allHeaders = [...baseHeaders, ...Array.from(extractedKeys)];

	// Escape CSV value
	const escapeCSV = (value: unknown): string => {
		if (value === null || value === undefined) return '';
		const str = String(value);
		if (str.includes(',') || str.includes('"') || str.includes('\n')) {
			return `"${str.replace(/"/g, '""')}"`;
		}
		return str;
	};

	// Build CSV rows
	const rows = data.map((item) => {
		const extractedData = (item.extracted_data || {}) as Record<string, unknown>;
		const row = [
			item.id,
			item.casino?.name || '',
			item.casino?.base_url || '',
			item.source_url,
			item.scraped_at,
			item.processed_at || ''
		];

		// Add extracted data columns
		extractedKeys.forEach((key) => {
			row.push(extractedData[key] ?? '');
		});

		return row.map(escapeCSV).join(',');
	});

	const csv = [allHeaders.join(','), ...rows].join('\n');

	return new Response(csv, {
		headers: {
			'Content-Type': 'text/csv',
			'Content-Disposition': `attachment; filename="casino-data-${new Date().toISOString().split('T')[0]}.csv"`
		}
	});
};
