import { User, UserPreferences } from './user';

export interface AuthResponse {
  user: User | null;
  session: {
    accessToken?: string;  // Optional since we're using HTTP-only cookies
    refreshToken?: string; // Optional since we're using HTTP-only cookies
    sessionHandle?: string;
  } | null;
}

export interface SuperTokensResponse {
  status: string;
  user: {
    id: string;
    email: string;
    timeJoined: number;
    tenantIds: string[];
    preferences: UserPreferences;
  };
  session: {
    handle: string;
    userId: string;
    userDataInJWT: Record<string, any>;
  };
}

export interface FormField {
  id: string;
  value: string;
}

export interface AuthError {
  message: string;
  status: number;
}
