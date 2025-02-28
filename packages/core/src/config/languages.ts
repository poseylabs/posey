export interface LanguageConfig {
  code: string;
  accents: string[];
  name: string;
  defaultVoiceId: string;
  enabled: boolean;
}

export const SUPPORTED_LANGUAGES: LanguageConfig[] = [
  {
    code: 'en',
    accents: ['american', 'british', "southern"],
    name: 'English',
    defaultVoiceId: 'gcgATH9maP3HG8oRh9Pn',
    enabled: true
  },
  {
    code: 'vi',
    accents: ['vietnamese'],
    name: 'Vietnamese',
    defaultVoiceId: 'HAAKLJlaJeGl18MKHYeg',
    enabled: true
  }
];

export const DEFAULT_LANGUAGE = SUPPORTED_LANGUAGES[0];

export const getDefaultVoiceForLanguage = (languageCode: string): string => {
  const language = SUPPORTED_LANGUAGES.find(lang => lang.code === languageCode);
  return language?.defaultVoiceId || SUPPORTED_LANGUAGES[0].defaultVoiceId;
};

export const LANG_CONFIG = {
  languages: SUPPORTED_LANGUAGES,
  default: DEFAULT_LANGUAGE,
  getDefaultVoiceForLanguage: getDefaultVoiceForLanguage
}
