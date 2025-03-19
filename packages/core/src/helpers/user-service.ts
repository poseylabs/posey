import { User, UserRole, UserPreferences } from '@/types/user';
import { AuthResponse, SuperTokensResponse, AuthError } from '@/types/auth';
import { DEFAULT_USER } from '@/config/defaults';

const AGENT_API = process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT || 'http://localhost:9999';

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
async function handleError(response: Response): Promise<never> {
  const error: any = await response.json();
  throw new Error(error.detail || 'Request failed');
}

/**
 * Gets user preferences
 */
export async function getUserPreferences(userId: string): Promise<UserPreferences> {
  const response = await fetch(`${AGENT_API}/user/${userId}/preferences`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response) {
    throw new Error('No response from server');
  }

  if (!response?.ok) {
    await handleError(response);
  }

  const data: any = await response?.json();
  return data.data; // Due to standardize_response wrapper
}

/**
 * Updates user data including metadata and preferences
 */
export async function updateUserData(userData: Partial<User>): Promise<User> {

  const response = await fetch(`${AGENT_API}/auth/user`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(userData)
  });

  if (!response.ok) {
    await handleError(response);
  }

  const data: any = await response.json();
  return data.data; // Due to standardize_response wrapper
}

/**
 * Lists users with optional filtering
 */
export async function listUsers(params: {
  status?: 'active' | 'inactive' | 'suspended';
  limit?: number;
  offset?: number;
}): Promise<User[]> {
  const queryParams = new URLSearchParams();
  if (params.status) queryParams.append('status', params.status);
  if (params.limit) queryParams.append('limit', params.limit.toString());
  if (params.offset) queryParams.append('offset', params.offset.toString());

  const response = await fetch(`${AGENT_API}/user?${queryParams}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });

  if (!response.ok) {
    await handleError(response);
  }

  const data: any = await response.json();
  return data.data; // Due to standardize_response wrapper
} 
