if (process.env.NODE_DEBUG !== 'true' || process.env.NEXT_PUBLIC_LOGGING === 'true') {
  process.env.NODE_DEBUG = 'true';
}

export const DEFAULT_LOGGER_NAME = 'Posey';
export const ENABLE_LOGGING = process.env.NODE_DEBUG === 'true' || process.env.NEXT_PUBLIC_LOGGING === 'true';

export class Logger {
  private readonly debugMode: boolean = false;
  enabled: boolean = ENABLE_LOGGING;
  name: string;
  logger: any;

  constructor({ debug = false, name = '' }: { debug?: boolean, name?: string }) {
    this.debugMode = process.env.NEXT_PUBLIC_DEBUG === 'true' || debug;
    this.name =name || DEFAULT_LOGGER_NAME;
    this.logger = console;
  }

  disable() {
    this.enabled = false;
  }

  enable() {
    this.enabled = true;
  }

  debug(...args: any[]) {
    if (this.debugMode) {
      this.logger.log(`${this.name}:`, ...args);
    }
  }

  log(...args: any[]) {
    if (this.enabled) {
      this.logger.log(`${this.name}:`, ...args);
    }
  }

  error(...args: any[]) {
    if (this.enabled) {
      this.logger.error(`${this.name}:`, ...args);
    }
  }

  warn(...args: any[]) {
    if (this.enabled) {
      this.logger.warn(`${this.name}:`, ...args);
    }
  }

  info(...args: any[]) {
    if (this.enabled) {
      this.logger.info(`${this.name}:`, ...args);
    }
  }
}
