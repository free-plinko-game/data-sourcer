import type { PageServerLoad } from './$types';
import getSupabase from '$lib/server/db';
import { error } from '@sveltejs/kit';

export const load: PageServerLoad = async ({ params }) => {
	const supabase = getSupabase();

	const { data: casino, error: dbError } = await supabase
		.from('casinos')
		.select('*')
		.eq('id', params.id)
		.single();

	if (dbError || !casino) {
		throw error(404, 'Casino not found');
	}

	// Don't send the actual password to the client
	return {
		casino: {
			...casino,
			password: casino.password ? '******' : null
		}
	};
};
