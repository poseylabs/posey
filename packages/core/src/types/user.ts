import { PhysicalLocation } from './location';
import { PreferredVoices } from './preferences';
import { VoiceSettings } from './abilities';

export enum UserRole {
  SUPER = 'super',
  ADMIN = 'admin',
  DEVELOPER = 'developer',
  FAMILY = 'family',
  FRIEND = 'friend',
  GUEST = 'guest',
  ANON = 'anonymous',
  USER = 'user'
}

export interface User {
  id: string;
  email: string;
  username: string;
  role: UserRole;
  lastLogin: Date;
  createdAt: Date;
  metadata: UserMetadata;
}

// New interface for SuperTokens metadata
export interface UserMetadata {
  profile: UserProfile | {};
  preferences: UserPreferences | {};
}

export interface UserProfile {
  name?: string;
  avatar?: string | null;
  occupation?: string | null;
  location?: PhysicalLocation | null;
  interests?: string[] | null;
  role?: UserRole | null;
  birthDate?: Date | null;
  gender?: string | null;
}

export interface UserPreferences {
  theme: string;
  language: string;
  notification_preferences: Record<string, boolean>;
  timezone: string;
  preferred_image_adapter: string;
  preferred_image_models: {
    [adapter: string]: string;
  };
  preferred_model: string;
  preferred_provider: string;
  preferred_voices: PreferredVoices;
  date_format?: string;
  tts_enabled: boolean;
  internet_enabled: boolean;
  voice_settings: VoiceSettings;
}

