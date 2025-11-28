import type { PageServerLoad } from './$types';
import getSupabase from '$lib/server/db';

export const load: PageServerLoad = async () => {
	const supabase = getSupabase();

	// Get stats in parallel
	const [
		{ count: totalCasinos },
		{ count: activeCasinos },
		{ count: totalScrapes },
		{ count: recentScrapes },
		{ data: recentData }
	] = await Promise.all([
		supabase.from('casinos').select('*', { count: 'exact', head: true }),
		supabase.from('casinos').select('*', { count: 'exact', head: true }).eq('is_active', true),
		supabase.from('scraped_data').select('*', { count: 'exact', head: true }),
		supabase
			.from('scraped_data')
			.select('*', { count: 'exact', head: true })
			.gte('scraped_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()),
		supabase
			.from('scraped_data')
			.select(`
				id,
				source_url,
				status,
				scraped_at,
				casino:casinos(name)
			`)
			.order('scraped_at', { ascending: false })
			.limit(10)
	]);

	return {
		stats: {
			totalCasinos: totalCasinos || 0,
			activeCasinos: activeCasinos || 0,
			totalScrapes: totalScrapes || 0,
			recentScrapes: recentScrapes || 0
		},
		recentData: recentData || []
	};
};
