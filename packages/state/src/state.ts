'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  isEqual,
  debounce
} from 'lodash';
import {
  config,
  Conversation,
  StatusMessage,
  UserPreferences,
  UserRole,
  logout,
  updateUserData,
  ConversationStatus
} from '@posey.ai/core';
import type {
  AppState,
  Migration as storeMigration,
  PoseyState,
  User,
  ChatState,
  UserProfile,
  Message
} from '@posey.ai/core';
import { getUserPreferencesFromDB } from './fetchers/user';
import { updateUserPreferences } from '@posey.ai/core';
import { UseBoundStore, StoreApi } from 'zustand';

const DEFAULT_USER = config.defaults.user;
const DEFAULT_AGENT = config.agent.default;
const AGENT_API = `${process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT || 'http://localhost:5555'}`;

const DEFAULT_CONVERSATION_TITLE = `Conversation ${new Date().toLocaleString(
  'en-US',
  {
    month: '2-digit',
    day: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  }
)}`;

const STORE_NAME = 'posey-store';
const STORE_VERSION = 1;
const APP_DEFAULTS = config.defaults;

const migrations: Record<number, storeMigration> = {
  0: (state: PoseyState) => ({ ...state, version: 1 }),
  1: (state: PoseyState) => ({
    ...state,
    version: STORE_VERSION + 1
  })
};

const Migration = (persistedState: any, version: number) => {
  let state = persistedState;
  while (version < 2) {
    state = migrations[version](state);
    version++;
  }
  return state;
}

const INITIAL_STATUS: AppState = {
  activeConversationId: null,
  isErrored: false,
  isSidebarOpen: true,
  isInitialized: false,
  isLoading: true,
  isReady: true,
  messages: {
    error: [],
    info: [],
    warning: [],
    success: []
  }
};

const INITIAL_CHAT_STATE: ChatState = {
  agent: APP_DEFAULTS.agent,
  conversations: [],
  currentConversation: null,
  draft: {
    input: '',
    timestamp: new Date()
  }
};

const Partialize = (state: any) => {
  const partial = {
    user: state.user,
    status: {
      ...INITIAL_STATUS,  // Ensure all status fields have defaults
      ...state.status     // Override with current values
    },
    chat: {
      agent: state.chat.agent,
      conversations: state.chat.conversations,
    },
    errors: state.errors,
    version: 2
  };
  return partial;
};

const STORE_CONFIG = {
  name: STORE_NAME,
  version: STORE_VERSION,
  migrate: Migration,
  partialize: Partialize,
  storage: {
    getItem: (name: string) => {
      const value = localStorage.getItem(name);
      return Promise.resolve(JSON.parse(value || 'null'));
    },
    setItem: (name: string, value: any) => {
      localStorage.setItem(name, JSON.stringify(value));
      return Promise.resolve();
    },
    removeItem: (name: string) => {
      localStorage.removeItem(name);
      return Promise.resolve();
    },
  }
}

const formatUserForStore = (user: User) => {
  return {
    ...user,
    metadata: {
      ...user.metadata,
      preferences: user.metadata?.preferences || APP_DEFAULTS.user.metadata.preferences
    }
  }
}

export const usePoseyState = create<PoseyState>()(
  persist(
    (set, get) => {
      return ({
        chat: INITIAL_CHAT_STATE,
        user: null,
        status: INITIAL_STATUS,
        _cache: new Map(),
        errors: [],
        hasHydrated: false,

        initState: async ({
          user,
          status: newStatus
        }: {
          user?: User;
          status?: Partial<AppState>;
        }) => {
          try {
            // Always allow initialization to ensure proper state
            set((state: PoseyState) => {
              const nextState = {
                ...state,
                user: user || state.user,
                status: {
                  ...state.status,
                  ...newStatus
                },
                _cache: new Map() // Clear cache with new state
              };

              return nextState;
            });

          } catch (error) {
            console.error('Error initializing store:', error);
            set((state: PoseyState) => ({
              ...state,
              status: {
                ...state.status,
                isErrored: true,
                isLoading: false
              }
            }));
          }
        },

        logout: async () => {
          try {
            await logout(); // Call SuperTokens logout
            set({
              user: null,
              chat: INITIAL_CHAT_STATE,
              conversations: [],
              status: {
                ...INITIAL_STATUS,
                isInitialized: true,
                isLoading: false
              }
            });
          } catch (error) {
            console.error('Logout error:', error);
            // Still clear the store even if logout fails
            set({ user: null });
          }
        },

        select: <T>(selector: (state: PoseyState) => T): T => {

          const cache = get()._cache;
          const key = selector.toString();

          if (!cache.has(key)) {
            cache.set(key, selector(get()));
          }

          return cache.get(key);
        },

        setState: (updater: Partial<PoseyState>) => {
          set((state: PoseyState) => {
            const newState = {
              ...state,
              ...updater,
              _cache: new Map()
            };
            return newState;
          });
        },

        setStatus: ({ key, value }: { key: string, value: any }) => {
          set((state: PoseyState) => {
            return {
              ...state,
              status: {
                ...state.status,
                [key]: value
              },
              _cache: new Map()
            };
          });
        },

        setStatusMessage: ({ key, value }: { key: string, value: any }) => {
          set((state: PoseyState) => {
            state._cache.clear();
            return {
              ...state,
              status: {
                ...state.status,
                messages: {
                  ...state.status.messages,
                  [key]: value
                }
              }
            };
          });
        },

        setUser: async ({
          save = false,
          user,
        }: {
          save?: boolean;
          user: User
        }) => {
          const _user = formatUserForStore(user);

          // Update backend if we have an ID
          if (_user.id && save) {
            try {
              await updateUserData(_user);
            } catch (error) {
              console.error('Error syncing user::', error);
            }
          }

          set({ user: _user });
        },


        getUserPreferences: async () => {
          const _user = get().user;
          const preferences = await getUserPreferencesFromDB(_user?.id);

          set({
            user: {
              ..._user,
              id: _user?.id || '',
              name: _user?.name || '',
              email: _user?.email || '',
              role: _user?.role || UserRole.GUEST,
              preferences: preferences
            }
          });
          return preferences;
        },

        setUserPreferences: async (params: { preferences: Partial<UserPreferences>; save?: boolean }) => {
          try {
            const { preferences, save = true } = params;
            const currentUser = get().user;
            if (!currentUser) return;

            const updatedMetadata = {
              ...currentUser.metadata,
              preferences: {
                ...currentUser.metadata.preferences,
                ...preferences
              }
            };

            if (!isEqual(currentUser.metadata.preferences, updatedMetadata.preferences)) {
              if (save) {
                await updateUserPreferences(updatedMetadata.preferences);
              }

              set((state: any) => ({
                ...state,
                user: {
                  ...state.user,
                  metadata: updatedMetadata
                }
              }));
            }
          } catch (error) {
            get().setError({
              type: 'preference',
              message: 'Failed to update preferences',
              timestamp: new Date(),
              context: error
            });
          }
        },

        setSidebarOpen: (isOpen: boolean) => {
          set((state: PoseyState) => {
            state._cache.clear();
            return {
              ...state,
              status: {
                ...state.status,
                isSidebarOpen: isOpen
              }
            };
          });
        },

        toggleSidebar: () => {
          set((state: PoseyState) => {
            state._cache.clear();
            return {
              ...state,
              status: {
                ...state.status,
                isSidebarOpen: !state.status.isSidebarOpen
              }
            };
          });
        },

        setError: (error: StatusMessage) => {
          set((state: PoseyState) => ({
            errors: [...state.errors, error]
          }));
        },

        getConversationTitle: async (conversationId: string) => {
          try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_ENDPOINT}/conversations/${conversationId}`);
            if (!response.ok) {
              throw new Error('Failed to fetch conversation title');
            }
            const data = await response.json();
            return data.title || 'New Conversation';
          } catch (error) {
            console.error('Error fetching conversation title:', error);
            return 'New Conversation';
          }
        },

        updateConversationTitle: async (conversationId: string, title: string) => {
          try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_ENDPOINT}/conversations/${conversationId}`, {
              method: 'PATCH',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ title }),
            });

            if (!response.ok) {
              throw new Error('Failed to update conversation title');
            }

            // Update local state
            set((state: PoseyState) => ({
              conversations: state.conversations.map((conversation: Conversation) =>
                conversation.id === conversationId ? { ...conversation, title } : conversation
              ),
            }));

          } catch (error) {
            console.error('Error updating conversation title:', error);
            throw error;
          }
        },

        getConversation: async (conversationId: string) => {
          try {
            const response = await fetch(`${AGENT_API}/conversations/${conversationId}`);
            if (!response.ok) {
              throw new Error('Failed to fetch conversation');
            }
            const conversation = await response.json();
            return conversation || {
              id: conversationId,
              title: conversation?.title || DEFAULT_CONVERSATION_TITLE,
              user_id: get().user?.id || DEFAULT_USER.id,
              status: conversation?.status || 'active',
              created_at: conversation?.created_at || new Date(),
              updated_at: new Date(),
              agent_id: conversation?.agent_id || DEFAULT_AGENT.id,
              metadata: conversation?.metadata
            };
          } catch (error) {
            console.error('Error fetching conversation:', error);
            throw error;
          }
        },

        createConversation: async ({
          title,
          user_id,
          agent_id,
          metadata,
          initial_message
        }: {
          title?: string;
          user_id?: string;
          agent_id?: string;
          metadata?: Record<string, any>;
          initial_message?: string;
        }) => {
          try {
            const response = await fetch(`${AGENT_API}/conversations`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                title: title || DEFAULT_CONVERSATION_TITLE,
                user_id: user_id || get().user?.id || DEFAULT_USER.id,
                agent_id: agent_id || DEFAULT_AGENT.id,
                metadata: metadata,
                initial_message: initial_message
              }),
            });

            if (!response.ok) {
              throw new Error('Failed to create conversation');
            }

            const conversation = await response.json();
            return conversation;
          } catch (error) {
            console.error('Error creating conversation:', error);
            throw error;
          }
        },

        updateConversation: async (conversationId: string, updates: Partial<Conversation>) => {
          try {
            const response = await fetch(`${AGENT_API}/conversations/${conversationId}`, {
              method: 'PATCH',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify(updates),
            });

            if (!response.ok) {
              throw new Error('Failed to update conversation');
            }

            // Update local state
            set((state: PoseyState) => ({
              conversations: state.conversations.map((conv) =>
                conv.id === conversationId ? { ...conv, ...updates } : conv
              ),
            }));

          } catch (error) {
            console.error('Error updating conversation:', error);
            throw error;
          }
        },

        debouncedUpdateProfile: debounce(async (updates: Partial<UserProfile>) => {
          try {
            const currentUser = get().user;
            if (!currentUser) return;

            // Create updated user object
            const updatedUser = {
              ...currentUser,
              metadata: {
                ...currentUser.metadata,
                profile: {
                  ...currentUser.metadata.profile,
                  ...updates
                }
              }
            };

            // Update backend
            await updateUserData(updatedUser);

            set((state: PoseyState) => ({
              ...state,
              user: updatedUser
            }));

          } catch (error) {
            console.error('Error updating profile:', error);
            get().setError({
              type: 'profile',
              message: 'Failed to update profile',
              timestamp: new Date(),
              context: error
            });
          }
        }, 1000),

        addMessage: (message: Message) => {
          set((state: PoseyState) => {
            // Log the conversation ID being updated
            console.log('[Zustand addMessage] Updating conversation:', state.chat.currentConversation?.id);
            console.log('[Zustand addMessage] Adding message:', message.id, message.content.substring(0, 50));
            // Clear the selector cache
            state._cache.clear(); 
            return {
              ...state,
              chat: {
                ...state.chat,
                currentConversation: {
                  ...state.chat.currentConversation,
                  messages: [...(state.chat.currentConversation?.messages || []), message]
                }
              }
            };
          });
        },

        updateMessage: (messageId: string, updates: Partial<Message>) => {
          set((state: PoseyState) => {
            // Clear the selector cache
            state._cache.clear();
            return {
              ...state,
              chat: {
                ...state.chat,
                currentConversation: {
                  ...state.chat.currentConversation,
                  messages: state?.chat?.currentConversation?.messages?.map(msg =>
                    msg.id === messageId ? { ...msg, ...updates } : msg
                  ) || []
                }
              }
            };
          });
        },

        setCurrentConversation: (conversation: Conversation | null) => {
          if (!conversation) {
            set((state: PoseyState) => ({
              ...state,
              chat: {
                ...state.chat,
                currentConversation: null
              }
            }));
            return;
          }

          // Check if the current value in state is already the same object or has the same ID
          // Using get() ensures we read the absolute latest state before deciding
          const currentState = get();
          if (currentState.chat.currentConversation === conversation || currentState.chat.currentConversation?.id === conversation.id) {
             console.log('[Zustand setCurrentConversation] Skipped update, conversation ID already set:', conversation.id);
             return; 
          }

          set((state: PoseyState) => ({
            ...state,
            chat: {
              ...state.chat,
              // Ensure we set a copy, not the original object reference
              currentConversation: { ...conversation },
            },
            // Clear the cache to potentially help selectors update
            _cache: new Map() // Assign a NEW empty Map
          }));
        },

        setConversations: (conversations: Conversation[]) => {
          set((state: PoseyState) => ({
            ...state,
            chat: {
              ...state.chat,
              conversations: conversations
            }
          }));
        }
      })
    },
    STORE_CONFIG
  )
) as UseBoundStore<StoreApi<PoseyState>>;
