import type { PageServerLoad } from './$types';
import getSupabase from '$lib/server/db';

export const load: PageServerLoad = async () => {
	const supabase = getSupabase();

	const [{ data: casinos }, { count: activeCasinos }] = await Promise.all([
		supabase.from('casinos').select('id, name').eq('is_active', true).order('name'),
		supabase.from('casinos').select('*', { count: 'exact', head: true }).eq('is_active', true)
	]);

	return {
		casinos: casinos || [],
		activeCasinos: activeCasinos || 0
	};
};
