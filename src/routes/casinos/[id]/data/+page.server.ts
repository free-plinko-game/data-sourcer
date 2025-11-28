import type { PageServerLoad } from './$types';
import getSupabase from '$lib/server/db';
import { error } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ params }) => {
	const supabase = getSupabase();
	const { id } = params;

	// Get casino with combined data
	const { data: casino, error: casinoError } = await supabase
		.from('casinos')
		.select('id, name, base_url, combined_data, combined_data_updated_at')
		.eq('id', id)
		.single();

	if (casinoError || !casino) {
		throw error(404, 'Casino not found');
	}

	// Get individual scraped data records for this casino
	const { data: scrapedData } = await supabase
		.from('scraped_data')
		.select(`
			id,
			source_url,
			extracted_data,
			status,
			scraped_at,
			config:scrape_configs(name)
		`)
		.eq('casino_id', id)
		.order('scraped_at', { ascending: false })
		.limit(50);

	// Get scrape configs for this casino
	const { data: configs } = await supabase
		.from('scrape_configs')
		.select('id, name, page_url, is_active')
		.eq('casino_id', id)
		.order('name');

	return {
		casino,
		scrapedData: scrapedData || [],
		configs: configs || []
	};
};
