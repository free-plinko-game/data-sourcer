import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import getSupabase from '$lib/server/db';

/**
 * Merge multiple extracted data objects into one combined object.
 * Later values take precedence, but null values don't override existing values.
 */
function mergeExtractedData(dataArray: Record<string, unknown>[]): Record<string, unknown> {
	const combined: Record<string, unknown> = {};
	const sourceUrls: string[] = [];

	for (const data of dataArray) {
		if (!data) continue;

		// Track source URLs
		if (data.source_url) {
			sourceUrls.push(data.source_url as string);
		}

		// Merge each field
		for (const [key, value] of Object.entries(data)) {
			if (key === 'source_url') continue; // Handle separately

			// Only update if we have a non-null value, or if there's no existing value
			if (value !== null && value !== undefined && value !== '') {
				// If both are strings and we already have a value, concatenate unique info
				if (typeof value === 'string' && typeof combined[key] === 'string') {
					const existing = combined[key] as string;
					// Only append if the new value adds meaningful info
					if (!existing.toLowerCase().includes(value.toLowerCase().slice(0, 50))) {
						// Keep the longer/more detailed version
						if (value.length > existing.length) {
							combined[key] = value;
						}
					}
				} else if (Array.isArray(value) && Array.isArray(combined[key])) {
					// Merge arrays, removing duplicates
					const existingArray = combined[key] as unknown[];
					const mergedArray = [...new Set([...existingArray, ...value])];
					combined[key] = mergedArray;
				} else {
					// For other types, take the new value if we don't have one yet
					if (combined[key] === undefined || combined[key] === null) {
						combined[key] = value;
					} else if (value !== combined[key]) {
						// If values differ, keep the more detailed/longer one for strings
						if (typeof value === 'string' && typeof combined[key] === 'string') {
							if ((value as string).length > (combined[key] as string).length) {
								combined[key] = value;
							}
						}
					}
				}
			}
		}
	}

	// Add combined source URLs
	combined.source_urls = sourceUrls;
	combined.merged_at = new Date().toISOString();
	combined.sources_count = sourceUrls.length;

	return combined;
}

// POST /api/casinos/:id/merge - Merge all scraped data for a casino into combined_data
export const POST: RequestHandler = async ({ params }) => {
	const supabase = getSupabase();

	// Verify casino exists
	const { data: casino, error: casinoError } = await supabase
		.from('casinos')
		.select('id, name')
		.eq('id', params.id)
		.single();

	if (casinoError || !casino) {
		return json({ error: 'Casino not found' }, { status: 404 });
	}

	// Get all completed scraped data for this casino
	const { data: scrapedData, error: dataError } = await supabase
		.from('scraped_data')
		.select('extracted_data, source_url')
		.eq('casino_id', params.id)
		.eq('status', 'completed');

	if (dataError) {
		return json({ error: dataError.message }, { status: 500 });
	}

	if (!scrapedData || scrapedData.length === 0) {
		return json({ error: 'No completed scrape data found for this casino' }, { status: 404 });
	}

	// Extract the data objects and add source_url to each
	const dataObjects = scrapedData
		.map((d) => ({
			...(d.extracted_data as Record<string, unknown>),
			source_url: d.source_url
		}))
		.filter(Boolean);

	// Merge the data
	const combinedData = mergeExtractedData(dataObjects);

	// Update the casino with combined data
	const { data: updatedCasino, error: updateError } = await supabase
		.from('casinos')
		.update({
			combined_data: combinedData,
			combined_data_updated_at: new Date().toISOString()
		})
		.eq('id', params.id)
		.select()
		.single();

	if (updateError) {
		return json({ error: updateError.message }, { status: 500 });
	}

	return json({
		success: true,
		casino: updatedCasino,
		combined_data: combinedData,
		sources_merged: dataObjects.length
	});
};
