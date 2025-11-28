import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { scrapeCasino, scrapeAllCasinos } from '$lib/server/scraper';

export const POST: RequestHandler = async ({ request }) => {
	try {
		const body = await request.json();
		const { casinoId, configId, all } = body;

		if (all) {
			// Scrape all active casinos
			const result = await scrapeAllCasinos();
			return json({
				success: true,
				message: `Scraped ${result.success}/${result.total} casinos successfully`,
				...result
			});
		}

		if (!casinoId) {
			return json({ error: 'casinoId is required' }, { status: 400 });
		}

		const result = await scrapeCasino({
			casinoId,
			configId,
			saveRawHtml: true
		});

		if (result.success) {
			return json({
				success: true,
				dataId: result.dataId,
				message: 'Scrape completed successfully'
			});
		} else {
			return json(
				{
					success: false,
					error: result.error
				},
				{ status: 500 }
			);
		}
	} catch (err) {
		console.error('Scrape error:', err);
		return json(
			{
				error: err instanceof Error ? err.message : 'Scrape failed'
			},
			{ status: 500 }
		);
	}
};
