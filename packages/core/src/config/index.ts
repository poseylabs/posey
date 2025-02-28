import { LANG_CONFIG } from './languages';
import { LLM_CONFIG, getUpdatedLLMAdapters } from './models/llm';
import { IMAGE_CONFIG } from './models/image';
import { SYSTEM_CAPABILITIES } from './capabilities';
import Defaults from './defaults';
import { APP_CONFIG } from './app';
import { AgentConfig } from './agents';
import { AppConfig } from '../types/app';
import { UI_CONFIG } from './ui';

const ModelsConfig = {
  llm: LLM_CONFIG,
  image: IMAGE_CONFIG
}

export const config: AppConfig = {
  agent: AgentConfig,
  app: APP_CONFIG,
  capabilities: SYSTEM_CAPABILITIES,
  defaults: Defaults,
  lang: LANG_CONFIG,
  models: ModelsConfig,
  ui: UI_CONFIG
}

export {
  SYSTEM_CAPABILITIES,
  Defaults as DEFAULTS,
  getUpdatedLLMAdapters
}

export default config;
