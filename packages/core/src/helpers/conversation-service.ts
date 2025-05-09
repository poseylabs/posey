import { Conversation, ConversationStatus, Message } from "@/types/conversation";
import { AgentConfig } from "@/config/agents";
import { FetchResponse } from "@/types/network";

const AGENT_API = `${process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT || 'http://localhost:5555'}`;
const DEFAULT_AGENT = AgentConfig.default;

export class ConversationService {

  apiBase: string = `${AGENT_API}/conversations`;
  currentConversationId: string;
  conversation: Conversation | undefined;
  isReady: boolean = false;
  userID: string;

  constructor({
    currentConversationId = '',
    conversation = undefined,
    user = '',
    fetchData = false
  }: {
    currentConversationId?: string;
    conversation?: Conversation;
    user?: string;
    fetchData?: boolean;
  }) {

    this.currentConversationId = currentConversationId ?? '';
    this.userID = user ?? '';

    if (!user) {
      console.error('Refusing to start conversation without user.');
      return;
    }

    if (typeof conversation === 'object') {
      this.conversation = conversation;
      this.isReady = true;
    } else if (fetchData && currentConversationId) {
      this.getConversation(currentConversationId).then((_conversation) => {
        this.conversation = _conversation;
        this.isReady = true;
      }).catch(err => {
        console.error(`Failed to fetch conversation ${currentConversationId} during construction:`, err);
        this.isReady = false;
      })
    } else {
      this.isReady = true;
    }

  }

  async addMessage({
    content,
    sender,
    role,
    metadata
  }: {
    content: string;
    sender: string;
    role?: string;
    metadata?: Record<string, any>;
  }) {
    this.validate(true);

    // Simplify metadata processing: Use the passed object directly, default to empty object
    const finalMetadata = (metadata && typeof metadata === 'object') ? metadata : {};

    console.log("Final metadata:", finalMetadata);

    const message = this.promptToMessage({
      content,
      sender,
      role,
      metadata: finalMetadata
    });

    try {
      const request: FetchResponse = await fetch(`${this.apiBase}/${this.currentConversationId}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(message)
      });

      if (!request.ok) {
        throw new Error('Failed to add message');
      }

      const response = await request.json();
      // response.data should be the message object *as saved in the DB*
      // including the metadata field if the backend saved it correctly.
      console.log("Response from addMessage API:", response.data);
      return response.data;

    } catch (error) {
      console.error('Error adding message:', error);
      throw error;
    }
  }

  async deleteMessage(messageId: string) {
    this.validate(true);

    try {
      const response: FetchResponse = await fetch(`${this.apiBase}/${this.currentConversationId}/messages/${messageId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to delete message');
      }

      return await response.json();
    } catch (error) {
      console.error('Error deleting message:', error);
      throw error;
    }
  }

  async deleteConversation(conversationId: string) {
    try {
      const response: FetchResponse = await fetch(`${this.apiBase}/${conversationId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to delete conversation');
      }

      if (conversationId === this.currentConversationId) {
        this.currentConversationId = '';
        this.conversation = undefined;
        this.isReady = false;
      }

      return await response.json();
    } catch (error) {
      console.error('Error deleting conversation:', error);
      throw error;
    }
  }

  generateTitle(): string {

    if (this?.conversation?.title) return this?.conversation?.title

    return `Conversation ${new Date().toLocaleString(
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
  }

  async getAllConversations(): Promise<Conversation[]> {
    const response: FetchResponse = await fetch(`${this.apiBase}`, {
      credentials: 'include'
    });
    if (!response.ok) {
      throw new Error('Failed to fetch conversations');
    }
    return await response.json();
  }

  async getConversation(conversationId: string): Promise<Conversation> {
    try {
      this.currentConversationId = conversationId;
      const response: FetchResponse = await fetch(`${this.apiBase}/${conversationId}`, {
        credentials: 'include'
      });
      if (!response.ok) {
        throw new Error('Failed to fetch conversation');
      }

      const conversation: Conversation = await response.json();

      // Fix for optional messages check
      const fallback_status = (conversation?.messages?.length ?? 0) > 0 ?
        ConversationStatus.ACTIVE :
        ConversationStatus.ACTIVE; // Changed from NEW to ACTIVE as default

      const status: ConversationStatus = conversation?.status ?? fallback_status;

      return {
        id: conversationId,
        title: conversation?.title || this.generateTitle(),
        user_id: this.userID,
        status,
        created_at: conversation?.created_at || new Date(),
        updated_at: new Date(),
        agent_id: conversation?.agent_id || DEFAULT_AGENT.id,
        metadata: conversation?.metadata || {},
        messages: conversation?.messages || []
      };
    } catch (error) {
      console.error('Error fetching conversation:', error);
      throw error;
    }
  }

  /**
   * Converts a text prompt to a properly formatted conversation message
   * @param prompt - The prompt to convert
   * @returns Formatted message
   */
  promptToMessage({
    content,
    metadata,
    role = '',
    sender,
    timestamp
  }: {
    content: string
    metadata?: Record<string, any>
    role?: string
    sender: string
    timestamp?: Date
  }): Message {
    let sender_type: 'human' | 'ai' | 'system' = 'human';
    let message_role: 'user' | 'assistant' | 'system';

    if (!role) {
      if (sender === this.userID) {
        message_role = 'user';
      } else {
        message_role = 'assistant';
      }
    } else {
      message_role = role as 'user' | 'assistant' | 'system';
    }

    if (message_role !== 'user') {
      sender_type = 'ai';
    }

    const message: Message = {
      id: '',
      content,
      role: message_role,
      sender_type,
      conversation_id: this.currentConversationId,
      created_at: timestamp || new Date(),
      metadata: metadata || {}
    };

    return message;
  }

  setID(id: string) {
    this.currentConversationId = id;
  }

  setConversation(conversation: Conversation) {
    const self = this;
    if (conversation?.id && self.conversation?.id !== conversation?.id) {
      this.conversation = conversation;
      this.currentConversationId = conversation.id;
      this.isReady = true;
      console.log('CONVERSATION SERVICE SET CONVERSATION:', conversation.id);
    } else {
      console.log('CONVERSATION SERVICE SET CONVERSATION: SKIPPED', {
        conversationId: conversation?.id,
        selfConversationId: self.currentConversationId,
        selfConversation: self.conversation,
        isReady: self.isReady
      });
    }
  }

  async start(content: string) {
    try {
      // Create new conversation first
      const response: FetchResponse = await fetch(this.apiBase, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          title: this.generateTitle(),
          meta: {},
          project_id: null
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create conversation');
      }

      const newConversation = await response.json();

      // Set the conversation data
      this.currentConversationId = newConversation.data.id;
      this.conversation = newConversation.data;
      this.isReady = true;

      // Now add the first message
      const messageResponse = await this.addMessage({
        content,
        sender: this.userID,
        role: 'user',
        metadata: {}
      });

      // Add the message response to the conversation object before returning
      // Assuming the conversation object has a 'messages' array
      if (this.conversation && messageResponse) {
          if (!this.conversation.messages) {
              this.conversation.messages = [];
          }
          this.conversation.messages.push(messageResponse);
      }

      // Return the full conversation object, including the ID and the newly added message
      return this.conversation;
    } catch (error) {
      console.error('Error starting conversation:', error);
      throw error;
    }
  }

  throwError(message: string) {
    throw new Error(message);
  }

  async updateConversation(conversation: Partial<Conversation>) {
    this.validate(true);

    try {
      const response: FetchResponse = await fetch(`${this.apiBase}/${this.currentConversationId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(conversation)
      });

      if (!response.ok) {
        throw new Error('Failed to update conversation');
      }

      const data = await response.json();
      this.conversation = data.data;
      return data.data;
    } catch (error) {
      console.error('Error updating conversation:', error);
      throw error;
    }
  }

  async updateMessage(messageId: string, updates: Partial<Message>) {
    this.validate(true);

    try {
      const response: FetchResponse = await fetch(`${this.apiBase}/${this.currentConversationId}/messages/${messageId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(updates)
      });

      if (!response.ok) {
        throw new Error('Failed to update message');
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating message:', error);
      throw error;
    }
  }

  validate(requireConversation: boolean = true) {
    if (!this.isReady) {
      this.throwError('Conversation is not ready');
    }
    if (!this.currentConversationId) {
      this.throwError('Conversation is missing  conversation ID');
    }

    if (requireConversation && typeof this.conversation === 'undefined') {
      this.throwError('Conversation is not defined :(');
    }
  }

  async updateStatus(status: ConversationStatus) {
    if (!this.currentConversationId) return;

    try {
      await this.updateConversation({
        status
      });
    } catch (error) {
      console.error('Error updating conversation status:', error);
      throw error;
    }
  }

}
