import { createClient } from '@supabase/supabase-js';
import { env } from '$env/dynamic/private';
import type { Database } from './types';

function getSupabaseClient() {
	const supabaseUrl = env.SUPABASE_URL;
	const supabaseKey = env.SUPABASE_SERVICE_ROLE_KEY;

	if (!supabaseUrl || !supabaseKey) {
		throw new Error('Missing Supabase environment variables');
	}

	return createClient<Database>(supabaseUrl, supabaseKey);
}

// Singleton pattern for server-side usage
let supabaseInstance: ReturnType<typeof createClient<Database>> | null = null;

export function getSupabase() {
	if (!supabaseInstance) {
		supabaseInstance = getSupabaseClient();
	}
	return supabaseInstance;
}

export default getSupabase;
