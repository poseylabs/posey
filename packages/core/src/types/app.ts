import { LANG_CONFIG } from '../config/languages';
import { UI_CONFIG } from '../config/ui';
import Defaults from '../config/defaults';
import { AgentConfig } from '../config/agents';
import { Capability } from './capabilities';
import { ModelsConfig } from './model';

export interface AppSettingsConfig {
  name: string;
  port: number | string;
  version: string;
  description: string;
  baseUrl: string;
}

export interface AppConfig {
  app: AppSettingsConfig;
  defaults: typeof Defaults;
  capabilities: Capability[];
  lang: typeof LANG_CONFIG;
  models: ModelsConfig
  agent: typeof AgentConfig;
  ui: typeof UI_CONFIG
}
