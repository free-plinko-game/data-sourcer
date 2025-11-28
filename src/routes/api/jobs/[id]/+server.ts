import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import getSupabase from '$lib/server/db';

// GET /api/jobs/:id - Get a single job with its scraped data
export const GET: RequestHandler = async ({ params }) => {
	const supabase = getSupabase();

	const { data: job, error: jobError } = await supabase
		.from('scrape_jobs')
		.select('*, casinos(name)')
		.eq('id', params.id)
		.single();

	if (jobError) {
		return json({ error: jobError.message }, { status: jobError.code === 'PGRST116' ? 404 : 500 });
	}

	// Get all scraped data for this job
	const { data: scrapedData } = await supabase
		.from('scraped_data')
		.select('*')
		.eq('job_id', params.id)
		.order('scraped_at', { ascending: true });

	return json({ ...job, scraped_data: scrapedData || [] });
};

// PATCH /api/jobs/:id - Update a job (status, progress, combined data)
export const PATCH: RequestHandler = async ({ params, request }) => {
	const supabase = getSupabase();
	const body = await request.json();

	const { data, error } = await supabase
		.from('scrape_jobs')
		.update(body)
		.eq('id', params.id)
		.select()
		.single();

	if (error) {
		return json({ error: error.message }, { status: 500 });
	}

	return json(data);
};

// DELETE /api/jobs/:id - Delete a job and its associated scraped data
export const DELETE: RequestHandler = async ({ params }) => {
	const supabase = getSupabase();

	// First, delete associated scraped_data (or update to set job_id to null)
	await supabase
		.from('scraped_data')
		.update({ job_id: null })
		.eq('job_id', params.id);

	const { error } = await supabase
		.from('scrape_jobs')
		.delete()
		.eq('id', params.id);

	if (error) {
		return json({ error: error.message }, { status: 500 });
	}

	return json({ success: true });
};
