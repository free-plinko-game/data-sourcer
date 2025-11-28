import type { PageServerLoad } from './$types';
import getSupabase from '$lib/server/db';

export const load: PageServerLoad = async () => {
	const supabase = getSupabase();

	const [{ data: casinos }, { data: scrapedData }] = await Promise.all([
		supabase.from('casinos').select('id, name').order('name'),
		supabase
			.from('scraped_data')
			.select(
				`
				id,
				source_url,
				extracted_data,
				status,
				scraped_at,
				casino:casinos(id, name)
			`
			)
			.order('scraped_at', { ascending: false })
			.limit(100)
	]);

	return {
		casinos: casinos || [],
		scrapedData: scrapedData || []
	};
};
