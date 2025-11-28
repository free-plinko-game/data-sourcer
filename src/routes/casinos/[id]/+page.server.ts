import type { PageServerLoad } from './$types';
import getSupabase from '$lib/server/db';
import { error } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ params }) => {
	const supabase = getSupabase();

	const { data: casino, error: casinoError } = await supabase
		.from('casinos')
		.select('*')
		.eq('id', params.id)
		.single();

	if (casinoError || !casino) {
		throw error(404, 'Casino not found');
	}

	// Load scrape configs (URLs) for this casino
	const { data: scrapeUrls, error: urlsError } = await supabase
		.from('scrape_configs')
		.select('*')
		.eq('casino_id', params.id)
		.order('created_at', { ascending: true });

	if (urlsError) {
		console.error('Error loading scrape configs:', urlsError);
	}

	// Don't send the actual password to the client
	return {
		casino: {
			...casino,
			password: casino.password ? '******' : null
		},
		scrapeUrls: scrapeUrls ?? []
	};
};
