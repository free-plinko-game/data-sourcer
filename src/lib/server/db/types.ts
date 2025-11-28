export interface Database {
	public: {
		Tables: {
			casinos: {
				Row: {
					id: string;
					name: string;
					base_url: string;
					login_url: string | null;
					username: string | null;
					password: string | null;
					notes: string | null;
					is_active: boolean;
					created_at: string;
					updated_at: string;
				};
				Insert: {
					id?: string;
					name: string;
					base_url: string;
					login_url?: string | null;
					username?: string | null;
					password?: string | null;
					notes?: string | null;
					is_active?: boolean;
					created_at?: string;
					updated_at?: string;
				};
				Update: {
					id?: string;
					name?: string;
					base_url?: string;
					login_url?: string | null;
					username?: string | null;
					password?: string | null;
					notes?: string | null;
					is_active?: boolean;
					updated_at?: string;
				};
			};
			scrape_configs: {
				Row: {
					id: string;
					casino_id: string;
					name: string;
					page_url: string;
					requires_login: boolean;
					extraction_type: string;
					custom_prompt: string | null;
					is_active: boolean;
					created_at: string;
					updated_at: string;
				};
				Insert: {
					id?: string;
					casino_id: string;
					name: string;
					page_url: string;
					requires_login?: boolean;
					extraction_type?: string;
					custom_prompt?: string | null;
					is_active?: boolean;
					created_at?: string;
					updated_at?: string;
				};
				Update: {
					id?: string;
					casino_id?: string;
					name?: string;
					page_url?: string;
					requires_login?: boolean;
					extraction_type?: string;
					custom_prompt?: string | null;
					is_active?: boolean;
					updated_at?: string;
				};
			};
			scraped_data: {
				Row: {
					id: string;
					casino_id: string;
					config_id: string | null;
					source_url: string;
					raw_html: string | null;
					extracted_data: Record<string, unknown> | null;
					status: string;
					error_message: string | null;
					scraped_at: string;
					processed_at: string | null;
				};
				Insert: {
					id?: string;
					casino_id: string;
					config_id?: string | null;
					source_url: string;
					raw_html?: string | null;
					extracted_data?: Record<string, unknown> | null;
					status?: string;
					error_message?: string | null;
					scraped_at?: string;
					processed_at?: string | null;
				};
				Update: {
					id?: string;
					casino_id?: string;
					config_id?: string | null;
					source_url?: string;
					raw_html?: string | null;
					extracted_data?: Record<string, unknown> | null;
					status?: string;
					error_message?: string | null;
					processed_at?: string | null;
				};
			};
		};
	};
}

export type Casino = Database['public']['Tables']['casinos']['Row'];
export type CasinoInsert = Database['public']['Tables']['casinos']['Insert'];
export type CasinoUpdate = Database['public']['Tables']['casinos']['Update'];

export type ScrapeConfig = Database['public']['Tables']['scrape_configs']['Row'];
export type ScrapeConfigInsert = Database['public']['Tables']['scrape_configs']['Insert'];
export type ScrapeConfigUpdate = Database['public']['Tables']['scrape_configs']['Update'];

export type ScrapedData = Database['public']['Tables']['scraped_data']['Row'];
export type ScrapedDataInsert = Database['public']['Tables']['scraped_data']['Insert'];
export type ScrapedDataUpdate = Database['public']['Tables']['scraped_data']['Update'];
