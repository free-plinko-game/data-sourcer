import type { PageServerLoad } from './$types';
import getSupabase from '$lib/server/db';

export const load: PageServerLoad = async () => {
	const supabase = getSupabase();

	// Get casinos with scrape counts
	const { data: casinos } = await supabase
		.from('casinos')
		.select(`
			id,
			name,
			base_url,
			is_active,
			created_at,
			updated_at
		`)
		.order('name');

	// Get scrape counts for each casino
	const casinosWithCounts = await Promise.all(
		(casinos || []).map(async (casino) => {
			const { count } = await supabase
				.from('scraped_data')
				.select('*', { count: 'exact', head: true })
				.eq('casino_id', casino.id);

			return {
				...casino,
				_count: { scrapedData: count || 0 }
			};
		})
	);

	return { casinos: casinosWithCounts };
};
