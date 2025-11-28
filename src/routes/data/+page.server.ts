import type { PageServerLoad } from './$types';
import getSupabase from '$lib/server/db';

export const load: PageServerLoad = async ({ url }) => {
	const supabase = getSupabase();
	const jobId = url.searchParams.get('job');

	// If viewing a specific job, load job data with combined results
	let job = null;
	if (jobId) {
		const { data: jobData } = await supabase
			.from('scrape_jobs')
			.select('*, casinos(name)')
			.eq('id', jobId)
			.single();
		job = jobData;
	}

	// Load recent jobs for the job selector
	const { data: recentJobs } = await supabase
		.from('scrape_jobs')
		.select('id, name, status, started_at, completed_urls, total_urls, casinos(name)')
		.order('started_at', { ascending: false })
		.limit(20);

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
				job_id,
				casino:casinos(id, name)
			`
			)
			.order('scraped_at', { ascending: false })
			.limit(100)
	]);

	return {
		casinos: casinos || [],
		scrapedData: scrapedData || [],
		recentJobs: recentJobs || [],
		job,
		jobId
	};
};
