export interface SuperTokensConfig {
  connectionURI: string;
  apiKey?: string;
}

export interface DashboardConfig {
  apiKey: string;
  admins?: string[];
}

export interface Config {
  port: number;
  allowedOrigins: string[];
  apiDomain: string;
  websiteDomain: string;
  supertokens: SuperTokensConfig;
  dashboard: DashboardConfig;
  oauth: {
    google: {
      clientId: string;
      clientSecret: string;
    };
  };
}

const allowedOrigins: string[] = [
  'http://localhost:5555',
  'http://localhost:8888',
]

export const config: Config = {
  port: Number(process.env.AUTH_PORT) || 9999,
  allowedOrigins: allowedOrigins,
  apiDomain: process.env.AUTH_API_DOMAIN || 'http://localhost:9999',
  websiteDomain: process.env.UI_BASE_URL || 'http://localhost:8888',
  supertokens: {
    connectionURI: process.env.SUPERTOKENS_CONNECTION_URI || 'http://posey-supertokens:3567',
    apiKey: process.env.SUPERTOKENS_API_KEY,
  },
  dashboard: {
    apiKey: process.env.DASHBOARD_API_KEY || 'your-dashboard-api-key',
    admins: process.env.DASHBOARD_ADMINS ? process.env.DASHBOARD_ADMINS.split(',') : [],
  },
  oauth: {
    google: {
      clientId: process.env.GOOGLE_CLIENT_ID || 'ERROR',
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || 'ERROR',
    },
  },
};

console.log('AUTH CONFIG:', config);
