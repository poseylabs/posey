import { Conversation, Message } from './conversation';
import { User, UserPreferences, UserProfile } from './user';
import { Agent } from './agent';

export enum StatusMessageType {
  ERROR = 'error',
  INFO = 'info',
  WARNING = 'warning',
  SUCCESS = 'success'
}

export interface StatusMessage {
  type: StatusMessageType;
  message: string;
  timestamp: Date;
  context?: any;
}

export interface AppState {
  activeConversationId: string | null;
  isSidebarOpen: boolean;
  isErrored: boolean;
  isLoading: boolean;
  isInitialized: boolean;
  isReady: boolean;
  messages: {
    error: StatusMessage[];
    info: StatusMessage[];
    warning: StatusMessage[];
    success: StatusMessage[];
  }
}


export interface ChatState {
  agent: Agent;
  conversations: Conversation[];
  currentConversation: Conversation | null;
  draft: {
    input: string;
    timestamp: Date;
  }
}

export type PoseySelector<T> = (state: PoseyState) => T;

export interface PoseyState {
  user: User;
  status: AppState;
  conversations: Conversation[];
  _cache: Map<string, any>;
  chat: ChatState;
  currentConversation: Conversation | null;
  errors: StatusMessage[];
  hasHydrated: boolean;

  // Setters & Getters
  addMessage: (message: Message) => void;
  debouncedUpdateProfile: (updates: Partial<UserProfile & {
    name?: string;
    email?: string;
    username?: string;
  }>) => Promise<void>;
  initState: (params: {
    user?: User;
    status?: AppState;
  }) => Promise<void>;
  logout: () => void;
  select: <T>(selector: PoseySelector<T>) => T;
  setConversations: (conversations: Conversation[]) => void;
  setCurrentConversation: (conversation: Conversation) => void;
  setError: (error: StatusMessage) => void;
  setSidebarOpen: (isOpen: boolean) => void;
  setState: (updater: Partial<PoseyState>) => PoseyState;
  setStatus: ({ key, value }: { key: string, value: any }) => void;
  setStatusMessage: ({ key, value }: { key: string, value: any }) => void;
  setUser: ({
    save,
    user,
  }: {
    save?: boolean;
    user: User;
  }) => void;
  setUserPreferences: (params: { preferences: Partial<UserPreferences>; save?: boolean }) => void;
  toggleSidebar: () => void;
  updateConversation: (conversationId: string, updates: Partial<Conversation>) => void;
  updateMessage: (messageId: string, updates: Partial<Message>) => void;
  updateUser: (updates: Partial<User>) => void;
  setHasHydrated: (state: boolean) => void;
}

export type PoseyStateHook = {
  <T>(selector: PoseySelector<T>, equalityFn?: (a: T, b: T) => boolean): T;
  // ... other store methods
};

export type Migration = (state: PoseyState) => any;
