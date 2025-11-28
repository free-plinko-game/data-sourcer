import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import getSupabase from '$lib/server/db';

export const GET: RequestHandler = async ({ params }) => {
	const supabase = getSupabase();

	const { data: casino, error } = await supabase
		.from('casinos')
		.select('*')
		.eq('id', params.id)
		.single();

	if (error || !casino) {
		return json({ error: 'Casino not found' }, { status: 404 });
	}

	// Don't expose the actual password
	return json({
		...casino,
		password: casino.password ? '******' : null
	});
};

export const PATCH: RequestHandler = async ({ params, request }) => {
	const supabase = getSupabase();

	try {
		const body = await request.json();
		const updateData: Record<string, unknown> = {};

		// Only include fields that were provided
		if (body.name !== undefined) updateData.name = body.name;
		if (body.base_url !== undefined) updateData.base_url = body.base_url;
		if (body.login_url !== undefined) updateData.login_url = body.login_url;
		if (body.username !== undefined) updateData.username = body.username;
		if (body.notes !== undefined) updateData.notes = body.notes;
		if (body.is_active !== undefined) updateData.is_active = body.is_active;

		// Only update password if a new one is provided
		if (body.password && body.password !== '******') {
			updateData.password = body.password;
		}

		const { data: casino, error } = await supabase
			.from('casinos')
			.update(updateData)
			.eq('id', params.id)
			.select()
			.single();

		if (error) {
			return json({ error: 'Failed to update casino' }, { status: 500 });
		}

		return json({
			...casino,
			password: casino.password ? '******' : null
		});
	} catch {
		return json({ error: 'Invalid request body' }, { status: 400 });
	}
};

export const DELETE: RequestHandler = async ({ params }) => {
	const supabase = getSupabase();

	const { error } = await supabase.from('casinos').delete().eq('id', params.id);

	if (error) {
		return json({ error: 'Failed to delete casino' }, { status: 500 });
	}

	return json({ success: true });
};
