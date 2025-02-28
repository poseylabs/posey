export interface InternetSearchResult {
  content: string;
  url: string;
  title?: string;
  snippet?: string;
  confidence?: number;
}

export interface SearchConfig {
  maxResults?: number;
  language?: string;
  region?: string;
  safeSearch?: boolean;
}

export interface VoiceSettings {
  stability?: number;
  similarity_boost?: number;
  useSpeakerBoost?: boolean;
}

export interface AbilityConfig {
  name: string;
  description: string;
  enabled: boolean;
}
