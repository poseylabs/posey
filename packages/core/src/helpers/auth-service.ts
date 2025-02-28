import { User, UserRole } from '@/types/user';
import { AuthResponse, SuperTokensResponse, FormField, AuthError } from '@/types/auth';
import { DEFAULT_USER } from '@/config/defaults';
import { UserPreferences } from '@/types/user';

const AUTH_API = process.env.NEXT_PUBLIC_AUTH_API_ENDPOINT || 'http://localhost:3001';

/**
 * Formats the SuperTokens response into our standard AuthResponse format
 */
function formatAuthResponse(response: SuperTokensResponse): AuthResponse {

  const user: User = {
    ...DEFAULT_USER,
    id: response.user.id,
    email: response.user.email,
    username: response.user.email.split('@')[0],
    createdAt: new Date(response.user.timeJoined),
    lastLogin: new Date(),
    role: UserRole.USER,
    metadata: {
      preferences: response.user.preferences || DEFAULT_USER.metadata.preferences,
      profile: {
        ...DEFAULT_USER.metadata.profile,
        name: response.user.email.split('@')[0]
      }
    }
  };

  const _formatted = { user, session: { sessionHandle: response?.session?.handle ?? undefined } }

  return _formatted;

}

/**
 * Handles API errors and transforms them into a standard format
 */
async function handleAuthError(response: Response): Promise<never> {
  const error = await response.json() as AuthError;
  throw new Error(error.message || 'Authentication failed');
}

/**
 * Sends a login request to the SuperTokens authentication server.
 */
export async function userLogin(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${AUTH_API}/auth/signin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      formFields: [
        { id: "email", value: email },
        { id: "password", value: password }
      ]
    }),
  });

  console.log('Login response:', response);

  if (!response.ok) {
    await handleAuthError(response);
  }

  const data: any = await response.json();

  if (data.status === 'OK') {
    // Immediately get session after login
    const session = await getSession();
    if (session) {
      return {
        user: session.user,
        session: session.session
      };
    }
  }

  throw new Error('Login failed');
}

/**
 * Signs up a new user with the SuperTokens authentication server.
 */
export async function userRegister({
  user
}: {
  user: {
    email: string, password: string, username: string
  }
}): Promise<AuthResponse> {
  const { email, password, username } = user;

  const formFields = [
    { id: "email", value: email },
    { id: "password", value: password },
    { id: "username", value: username }
  ]

  const response: any = await fetch(`${AUTH_API}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      formFields
    }),
  }).catch((err) => {
    console.warn('API ERROR:', err);
    throw err;
  });

  if (!response.ok) {
    await handleAuthError(response);
  }

  const data = await response.json();

  if (data?.status === 'OK') {
    return formatAuthResponse(data);
  }

  console.clear();
  console.log('Response NOT OK:', {
    data
  });
  return { user: null, session: null };
}

/**
 * Logs out the current user by calling the SuperTokens signout endpoint.
 */
export async function logout(): Promise<void> {
  try {
    const response = await fetch(`${AUTH_API}/auth/signout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    });

    if (!response.ok) {
      await handleAuthError(response);
    }
  } catch (error) {
    console.error('Logout  error:', error);
    throw error;
  }
}

/**
 * Gets the current session information if it exists.
 */
export async function getSession(): Promise<{ user: User; session: any } | null> {
  try {
    const response = await fetch(`${AUTH_API}/auth/session`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      if (response.status === 401) {
        return null;
      }
      throw new Error('Failed to get session');
    }

    const data: any = await response.json();

    if (data.status === 'OK' && data.user) {
      return {
        user: data.user,
        session: data.session
      };
    }

    return null;
  } catch (error) {
    console.error('Error getting session:', error);
    return null;
  }
}

/**
 * Checks if there is an active session.
 */
export async function isAuthenticated(): Promise<boolean> {
  try {
    const session = await getSession();
    return session !== null && session.user !== null;
  } catch {
    return false;
  }
}

/**
 * Refreshes the session if needed.
 * Note: SuperTokens handles token refresh automatically through cookies,
 * but this method can be used to explicitly check/refresh the session.
 */
export async function refreshSession(): Promise<AuthResponse | null> {
  const response: any = await fetch(`${AUTH_API}/auth/session/refresh`, {
    method: 'POST',
    credentials: 'include',
  });

  if (!response.ok) {
    if (response.status === 401) {
      return null; // Session is not refreshable
    }
    throw new Error('Failed to refresh session');
  }

  const data: SuperTokensResponse = await response.json();
  return formatAuthResponse(data);
}

/**
 * Sends a request to update user data.
 *
 * @param updateData - Partial data to update on the user.
 * @returns The updated user data.
 * @throws An error if the update request fails.
 */
export async function updateAuthUser(user: Partial<User>): Promise<AuthResponse> {
  // Clean metadata before sending to avoid nesting
  const cleanMetadata = {
    preferences: user.metadata?.preferences || {},
    profile: user.metadata?.profile || {}
  };

  const response = await fetch(`${AUTH_API}/auth/user`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      metadata: cleanMetadata
    })
  });

  if (!response.ok) {
    await handleAuthError(response);
  }

  const data: any = await response.json();
  return formatAuthResponse(data);
}

export async function initiateOAuthFlow(provider: string): Promise<string> {
  const response: any = await fetch(`${AUTH_API}/auth/authorize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      provider,
      redirect_uri: '/auth/callback'
    }),
  });

  if (!response.ok) {
    await handleAuthError(response);
  }

  const { url } = await response.json();
  return url;
}

export async function handleOAuthCallback(code: string): Promise<AuthResponse> {
  const response: any = await fetch(`${AUTH_API}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  });

  if (!response.ok) {
    await handleAuthError(response);
  }

  const data = await response.json();
  return formatAuthResponse(data);
}

export async function updateUserPreferences(preferences: Partial<UserPreferences>): Promise<void> {
  // Clean preferences to avoid nesting
  const cleanPreferences = {
    ...preferences,
    metadata: undefined // Remove any nested metadata
  };

  const response = await fetch(`${AUTH_API}/auth/preferences`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(cleanPreferences),
  });

  if (!response.ok) {
    await handleAuthError(response);
  }
} 
