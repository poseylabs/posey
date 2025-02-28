import { AppSettingsConfig } from 'src/types/app';
import pkg from '../../package.json';

export const APP_NAME = 'Posey';
export const APP_PORT = process.env.NEXT_PUBLIC_PORT_WWW;
export const APP_VERSION = pkg.version;
export const APP_DESCRIPTION = 'Posey is a AI assistant power by a network of helpful AI agents.';
export const APP_BASE_URL = process.env.NEXT_PUBLIC_APP_BASE_URL;
export const APP_AUTHOR_EMAIL = 'hello@posey.ai';

export const APP_CONFIG: AppSettingsConfig = {
  name: APP_NAME,
  port: APP_PORT ?? 8888,
  version: APP_VERSION,
  description: APP_DESCRIPTION,
  baseUrl: APP_BASE_URL ?? 'http://localhost:8888',
};
