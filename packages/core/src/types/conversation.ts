export enum ConversationStatus {
  ACTIVE = 'active',
  ARCHIVED = 'archived',
  DELETED = 'deleted',
  NEW = 'new',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  ERROR = 'error',
  CANCELLED = 'cancelled',
  PAUSED = 'paused',
  RESUMED = 'resumed'
}

export interface Conversation {
  id: string;
  title: string;
  user_id: string;
  agent_id: string;
  status: ConversationStatus;
  metadata?: Record<string, any>;
  created_at: Date;
  updated_at: Date;
  messages?: Message[];
}

export interface ConversationCreate {
  title?: string;
  user_id: string;  // UUID4
  initial_message?: string;
  context?: Record<string, any>;
}

export interface LLMMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  sender_type: 'human' | 'ai' | 'system';
  metadata?: {
    type?: string;
    model?: string;
    prompt?: string;
    imageUrl?: string;
    media?: Array<{
      type: string;
      url?: string;
      metadata?: any;
    }>;
    references?: Array<{
      title: string;
      url: string;
      snippet?: string;
      content?: {
        status?: string;
        title?: string;
        text?: string;
      };
    }>;
    [key: string]: any;
  };
  created_at: Date;
}

