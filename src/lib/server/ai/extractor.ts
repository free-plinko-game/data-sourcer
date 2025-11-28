import OpenAI from 'openai';
import { env } from '$env/dynamic/private';

let openaiClient: OpenAI | null = null;

function getOpenAI(): OpenAI {
	if (!openaiClient) {
		openaiClient = new OpenAI({
			apiKey: env.OPENAI_API_KEY
		});
	}
	return openaiClient;
}

export interface CasinoInfo {
	brand: string | null;
	'Terms & Conditions': string | null;
	'Game Availability': string | null;
	'Casino Reputation': string | null;
	'Customer Support': string | null;
	'Mobile & App Availability': string | null;
	'Responsible Gambling Page/Tools': string | null;
	'Privacy Policy': string | null;
	'AML (Anti-Money Laundering)': string | null;
	'KYC (Know Your Customer) Details': string | null;
	Providers: string | null;
	'Year Established': string | null;
	'Payout – Speed/%': string | null;
	'Maximum/Minimum Deposit/Withdrawal': string | null;
	'Number of Games/Pokies': string | null;
	'Player Protection & Safety': string | null;
	'Number of Players': string | null;
	'Bonus Offers Breakdown': string | null;
	source_url: string;
}

const CASINO_INFO_PROMPT = `You are an expert data extraction agent. Extract high-level general information about the casino from this review content.

Note: Different websites may use varied terminology. You should recognize synonyms and alternate phrasings for all fields.

Examples:
- "brand" = site name, logo text, brand header, title tag (e.g. "Bet365", "LeoVegas")
- "Terms & Conditions" = Rules, User Agreement, General Terms, Terms of Use
- "Game Availability" = Available Games, Game Selection, Casino Library, Playable Games
- "Casino Reputation" = Trust Score, Industry Reputation, Reviews, Background
- "Customer Support" = Help, Support Center, Contact Us, Live Chat, FAQs
- "Mobile & App Availability" = Mobile App, iOS/Android App, Mobile Casino, App Download
- "Responsible Gambling Page/Tools" = Safe Play, Player Protection, Gambling Controls, Self-Exclusion Tools
- "Privacy Policy" = Data Use, Security Policy, Information Policy, Cookies & Privacy
- "AML (Anti-Money Laundering)" = Money Laundering Prevention, AML Policy, Anti-Fraud
- "KYC (Know Your Customer) Details" = Verification Process, Identity Check, Account Validation
- "Providers" = Game Developers, Software Providers, Studios, Game Vendors
- "Year Established" = Founded, Since, In Operation Since
- "Payout – Speed/%" = Withdrawal Times, RTP, Payout Rate, Cashout Duration
- "Maximum/Minimum Deposit/Withdrawal" = Payment Limits, Deposit Range, Withdrawal Range
- "Number of Games/Pokies" = Game Count, Slot Library, Pokie Total, Number of Titles
- "Player Protection & Safety" = Responsible Gaming, Security Features, Anti-Gambling Harm
- "Number of Players" = User Base, Player Count, Registered Users
- "Bonus Offers Breakdown" = Welcome Bonus, Offers Summary, Promotions, Bonus Types
- "source_url" = The page URL where this review content was extracted

If exact matches are not found, infer values based on context, phrasing, or implied meaning. If completely absent, return null.

Return a single JSON object using these exact keys. Use null only if absolutely no reasonable inference can be made.

Example format:
{
  "brand": "...",
  "Terms & Conditions": "...",
  "Game Availability": "...",
  "Casino Reputation": "...",
  "Customer Support": "...",
  "Mobile & App Availability": "...",
  "Responsible Gambling Page/Tools": "...",
  "Privacy Policy": "...",
  "AML (Anti-Money Laundering)": "...",
  "KYC (Know Your Customer) Details": "...",
  "Providers": "...",
  "Year Established": "...",
  "Payout – Speed/%": "...",
  "Maximum/Minimum Deposit/Withdrawal": "...",
  "Number of Games/Pokies": "...",
  "Player Protection & Safety": "...",
  "Number of Players": "...",
  "Bonus Offers Breakdown": "...",
  "source_url": "{{source_url}}"
}

Casino Review Content:
{{html}}

Do not explain or describe your response. Only return a valid JSON object.`;

export async function extractCasinoInfo(
	html: string,
	sourceUrl: string,
	customPrompt?: string
): Promise<CasinoInfo> {
	const openai = getOpenAI();

	// Use custom prompt if provided, otherwise use default
	let prompt = customPrompt || CASINO_INFO_PROMPT;
	prompt = prompt.replace('{{html}}', html).replace('{{source_url}}', sourceUrl);

	const response = await openai.chat.completions.create({
		model: 'gpt-4o',
		messages: [
			{
				role: 'user',
				content: prompt
			}
		],
		response_format: { type: 'json_object' },
		temperature: 0.1,
		max_tokens: 2000
	});

	const content = response.choices[0]?.message?.content;
	if (!content) {
		throw new Error('No response from OpenAI');
	}

	try {
		const parsed = JSON.parse(content) as CasinoInfo;
		// Ensure source_url is set
		parsed.source_url = sourceUrl;
		return parsed;
	} catch {
		throw new Error(`Failed to parse OpenAI response: ${content}`);
	}
}

export async function extractWithCustomPrompt(
	html: string,
	sourceUrl: string,
	prompt: string
): Promise<Record<string, unknown>> {
	const openai = getOpenAI();

	const fullPrompt = prompt.replace('{{html}}', html).replace('{{source_url}}', sourceUrl);

	const response = await openai.chat.completions.create({
		model: 'gpt-4o',
		messages: [
			{
				role: 'user',
				content: fullPrompt
			}
		],
		response_format: { type: 'json_object' },
		temperature: 0.1,
		max_tokens: 2000
	});

	const content = response.choices[0]?.message?.content;
	if (!content) {
		throw new Error('No response from OpenAI');
	}

	return JSON.parse(content);
}
