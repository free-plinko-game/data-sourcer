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

Field definitions and expected formats:
- "brand" = Site name, logo text, brand header, title tag (e.g. "Bet365", "LeoVegas")
- "Terms & Conditions" = Summarize KEY terms: wagering requirements (e.g. "35x bonus"), withdrawal limits, bonus expiry periods, restricted games, notable restrictions. NOT just "terms and conditions"
- "Game Availability" = List game categories available (e.g. "Slots, Live Casino, Table Games, Poker, Sports Betting")
- "Casino Reputation" = Trust indicators: licenses held, industry awards, years in operation, parent company
- "Customer Support" = Support channels and hours (e.g. "24/7 Live Chat, Email, Phone support in English/German")
- "Mobile & App Availability" = Specific app availability (e.g. "iOS and Android apps available", "Mobile browser only", "No app")
- "Responsible Gambling Page/Tools" = List specific tools: deposit limits, loss limits, session limits, self-exclusion, reality checks, cool-off periods
- "Privacy Policy" = Key privacy points: data encryption, third-party sharing policy, GDPR compliance
- "AML (Anti-Money Laundering)" = AML policy details, transaction monitoring, reporting requirements
- "KYC (Know Your Customer) Details" = Verification requirements: documents needed (ID, proof of address, payment method), verification timeframes
- "Providers" = List game providers/developers (e.g. "NetEnt, Microgaming, Evolution Gaming, Pragmatic Play")
- "Year Established" = Founding year as a number (e.g. "2017", "2005")
- "Payout – Speed/%" = Extract ACTUAL withdrawal timeframes (e.g. "24-48 hours", "1-3 business days", "instant for e-wallets") and RTP percentages if mentioned. NOT vague terms like "fast"
- "Maximum/Minimum Deposit/Withdrawal" = Specific limits with currency (e.g. "Min deposit: £10, Max withdrawal: £5,000/day, £20,000/month")
- "Number of Games/Pokies" = Extract ACTUAL numbers (e.g. "500+ slots", "1,200 total games", "800 pokies"). If no exact number stated, return null
- "Player Protection & Safety" = Security features: SSL encryption, responsible gambling certifications, player fund protection
- "Number of Players" = Actual user count if mentioned (e.g. "1 million+ registered users"). If not stated, return null
- "Bonus Offers Breakdown" = Specific bonus details: welcome bonus amount/percentage, wagering requirements, free spins, ongoing promotions
- "source_url" = The page URL where this content was extracted

IMPORTANT:
- Extract SPECIFIC data, not vague descriptions
- Use actual numbers, timeframes, and percentages where possible
- If data is genuinely not present on the page, return null rather than guessing
- Do not return generic phrases like "fast", "many games", "good support" - extract specifics or return null

Return a single JSON object using these exact keys.

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
