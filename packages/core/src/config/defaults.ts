import { uuid } from 'src/utils/crypto';
import { POSEY_AGENT_PROMPT } from 'src/prompts/agents';
import { SYSTEM_PROMPT } from 'src/prompts/system';
import { SYSTEM_CAPABILITIES } from 'src/config/capabilities';

import { ImageDefaults, User, UserPreferences, UserProfile, UserRole, VoiceSettings } from 'src/types';
import { Agent } from 'src/types/agent';

import { ANTHROPIC_MODELS, ANTHROPIC_NAMESPACE } from 'src/config/models/llm/anthropic';
import { GOOGLE_MODELS, GOOGLE_NAMESPACE } from 'src/config/models/llm/google';
import { OPENAI_MODELS } from 'src/config/models/llm/openai';

import {
  MAX_TOKENS_XS,
  MAX_TOKENS_SMALL,
  MAX_TOKENS_MEDIUM,
  MAX_TOKENS_LARGE,
  MAX_TOKENS_XL,
  DEFAULT_MODEL_MAX_TOKENS,
  DEFAULT_MODEL_CONTEXT_WINDOW,
  DEFAULT_MODEL_TEMP
} from './models/llm/model-defaults';

export const llmDefaults = {
  provider: ANTHROPIC_NAMESPACE,
  anthropic: ANTHROPIC_MODELS[0],
  google: GOOGLE_MODELS[0],
  openai: OPENAI_MODELS[0],
  ollama: null,
  tokens: {
    max: DEFAULT_MODEL_MAX_TOKENS,
    xs: MAX_TOKENS_XS,
    small: MAX_TOKENS_SMALL,
    medium: MAX_TOKENS_MEDIUM,
    large: MAX_TOKENS_LARGE,
    xl: MAX_TOKENS_XL
  },
  contextWindow: DEFAULT_MODEL_CONTEXT_WINDOW,
  maxTokens: DEFAULT_MODEL_MAX_TOKENS,
  temperature: DEFAULT_MODEL_TEMP
}

// LLM
export const DEFAULT_LLM_ADAPTER = llmDefaults.provider;
export const DEFAULT_LLM_MODEL = llmDefaults.anthropic;
export const DEFAULT_ANTHROPIC_MODEL = llmDefaults.anthropic;
export const DEFAULT_OPENAI_MODEL = llmDefaults.openai;
export const DEFAULT_GOOGLE_MODEL = llmDefaults.google;
export const DEFAULT_OLLAMA_MODEL = llmDefaults.ollama;

// Image
export const DEFAULT_IMG_ADAPTER = 'flux';
export const DEFAULT_IMG_MODEL_FLUX = 'flux-dev';
export const DEFAULT_IMG_MODEL_DALLE = 'dall-e-3';
export const DEFAULT_IMG_MODEL_STABLE_DIFFUSION = 'ultra';

export const DEFAULT_TIMEZONE = 'UTC';
export const DEFAULT_LANGUAGE = 'en';
export const DEFAULT_THEME = 'dark';

export const DEFAULT_AVATAR = 'https://img.daisyui.com/images/stock/photo-1534528741775-53994a69daeb.webp';

// VOICE
export const DEFAULT_TTS_ENABLED = false;
export const DEFAULT_VOICE_STABILITY = 0;
export const DEFAULT_VOICE_SIMILARITY_BOOST = 0.75;
export const DEFAULT_VOICE_USE_SPEAKER_BOOST = true;

// INTERNET
export const DEFAULT_INTERNET_ENABLED = false;

export const DEFAULT_AGENT: Agent = {
  id: 'c079d8a2-9b06-5c2c-97be-0af43c36ef03',
  name: 'Posey',
  description: 'Posey is a helpful assistant that can help you with your questions.',
  adapter: DEFAULT_LLM_ADAPTER,
  model: DEFAULT_LLM_MODEL,
  prompts: [SYSTEM_PROMPT, POSEY_AGENT_PROMPT],
  capabilities: SYSTEM_CAPABILITIES,
  avatar: DEFAULT_AVATAR,
}

export const DEFAULT_VOICE_SETTINGS: VoiceSettings = {
  stability: DEFAULT_VOICE_STABILITY,
  similarity_boost: DEFAULT_VOICE_SIMILARITY_BOOST,
  useSpeakerBoost: DEFAULT_VOICE_USE_SPEAKER_BOOST
};

interface UserMetadata {
  name?: string;
  email?: string;
  username?: string;
}

export const DEFAULT_USER_METADATA: UserMetadata = {
  name: '',
  email: '',
  username: '',
}

export const DEFAULT_USER_PROFILE: UserProfile = {
  avatar: DEFAULT_AVATAR,
  name: '',
  occupation: null,
  location: null,
  interests: [],
  role: UserRole.ANON,
  birthDate: null,
  gender: null,
}

export const DEFAULT_USER_PREFERENCES: UserPreferences = {
  theme: DEFAULT_THEME,
  language: DEFAULT_LANGUAGE,
  notification_preferences: {
    enabled: true,
    email: true,
    sms: true,
    push: true
  },
  timezone: DEFAULT_TIMEZONE,
  preferred_image_adapter: DEFAULT_IMG_ADAPTER,
  preferred_image_models: {
    flux: DEFAULT_IMG_MODEL_FLUX,
    dalle: 'dall-e-3',
    stable_diffusion: 'core'
  },
  preferred_model: DEFAULT_LLM_MODEL.id,
  preferred_provider: DEFAULT_LLM_ADAPTER,
  preferred_voices: {},
  tts_enabled: DEFAULT_TTS_ENABLED,
  internet_enabled: DEFAULT_INTERNET_ENABLED,
  voice_settings: DEFAULT_VOICE_SETTINGS
}

export const DEFAULT_USER: User = {
  id: '',
  email: '',
  username: '',
  role: UserRole.GUEST,
  lastLogin: new Date(),
  createdAt: new Date(),
  metadata: {
    preferences: DEFAULT_USER_PREFERENCES,
    profile: DEFAULT_USER_PROFILE
  }
}

export const POSEY_IMAGE_DEFAULTS: ImageDefaults = {
  adapter: 'flux',
  model: 'flux-pro',
  defaultOptions: {
    width: 1024,
    height: 576,
    steps: 30,
    cfgScale: 7,
    samples: 1,
    seed: -1,
    quality: "standard",
    style: "vivid",
  }
}

export const APP_DEFAULTS = {
  voiceSettings: DEFAULT_VOICE_SETTINGS,
  user: DEFAULT_USER,
  agent: DEFAULT_AGENT,
}

export default APP_DEFAULTS;
