import { config } from '@posey.ai/core';

const AGENT_API = `${process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT || 'http://localhost:5555'}`;

const DEFAULT_USER = config.defaults.user;
const DEFAULT_USER_PREFERENCES = config.defaults.user.preferences;

export async function getUserPreferencesFromDB(user_id: string | undefined) {
  if (!user_id) return DEFAULT_USER_PREFERENCES;
  try {
    const response = await fetch(`${AGENT_API}/user/${user_id}/preferences`);
    const preferences = await response.json();
    return {
      ...DEFAULT_USER_PREFERENCES,
      ...(preferences?.data || {})
    };
  } catch (error) {
    console.error('Error fetching user preferences:', error);
    return DEFAULT_USER_PREFERENCES;
  }
}

export async function saveUserPreferencesToDB(user_id: string | undefined, preferences: Record<string, any>) {
  if (!user_id) return;
  try {
    const response = await fetch(`${AGENT_API}/user/${user_id}/preferences`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(preferences),
    });

    if (!response.ok) {
      throw new Error('Failed to save user preferences');
    }
  } catch (error) {
    console.error('Error saving user preferences:', error);
  }
}
