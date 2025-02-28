import { useEffect, useState } from 'react';
import { Message, ConversationService, PoseyState, Conversation } from '@posey.ai/core';
import { usePoseyState } from '@posey.ai/state';
import { agentService } from '@posey.ai/core';

export const useConversation = () => {

  const store = usePoseyState();

  const {
    addMessage,
    updateMessage,
    user,
    chat,
    setState
  } = store.select((state: PoseyState) => ({
    addMessage: state.addMessage,
    updateMessage: state.updateMessage,
    user: state.user,
    chat: state.chat,
    setState: state.setState
  }));

  const [isConversationLoading, setIsConversationLoading] = useState(false);

  const [conversationService] = useState(() => new ConversationService({
    user: user?.id || '',
    currentConversationId: chat.currentConversation?.id
  }));

  useEffect(() => {
    if (chat.currentConversation?.id && !conversationService.currentConversationId) {
      conversationService.setConversation(chat.currentConversation);
    }
  }, [chat]);

  const ensureConversationID = () => {
    if (chat.currentConversation?.id && !conversationService.currentConversationId) {
      conversationService.setConversation(chat.currentConversation);
    }
  }

  const callAgent = async ({
    message,
    firstContact = false,
  }: {
    message: string,
    firstContact?: boolean
  }) => {
    try {
      setIsConversationLoading(true);
      ensureConversationID();

      // Send to agent
      const response: any = await agentService.call(message);

      if (!response?.success) {
        console.error('Error calling agent:', response?.error);
        throw new Error(response?.error);
      }

      if (!firstContact) {
        // Add message to existing conversation
        const userMessage = await conversationService.addMessage({
          content: message,
          sender: user?.id || '',
          role: 'user',
          metadata: {}
        });
        addMessage(userMessage);
      }

      // Add agent response to conversation
      const agentMessage = await conversationService.addMessage({
        content: response?.data?.answer,
        sender: 'agent',
        role: 'assistant',
        metadata: response?.data?.metadata || {}
      });

      addMessage(agentMessage);
      return agentMessage;

    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    } finally {
      setIsConversationLoading(false);
    }
  };

  const getAllConversations = async () => {
    const conversations = await conversationService.getAllConversations();
    return conversations;
  }

  const likeMessage = async (messageId: string) => {
    try {
      if (!user?.id) return;
      ensureConversationID();

      const message = chat?.currentConversation?.messages?.find(
        (msg: Message) => msg.id === messageId
      );

      if (!message) return;

      // Update message metadata to include like status
      const response = await conversationService.updateMessage(messageId, {
        metadata: {
          ...message.metadata,
          liked: true
        }
      });

      if (response.success) {
        updateMessage(messageId, {
          metadata: {
            ...message.metadata,
            liked: true
          }
        });
      }

      return response.success;
    } catch (error) {
      console.error('Error favoriting message:', error);
      return false;
    }
  };

  const loadConversation = async (conversationId: string) => {
    try {
      ensureConversationID();
      const conversation = await conversationService.getConversation(conversationId);
      if (conversation) {
        setState({
          chat: {
            ...chat,
            currentConversation: conversation
          }
        });
      }
      return conversation;
    } catch (error) {
      console.error('Error loading conversation:', error);
      throw error;
    }
  };

  const startConversation = async (content: string) => {
    try {
      ensureConversationID();
      const newMessage = await conversationService.start(content);
      setState({
        chat: {
          ...chat,
          currentConversation: conversationService.conversation || null
        }
      });
      addMessage(newMessage);
      return conversationService.conversation;
    } catch (error) {
      console.error('Error starting conversation:', error);
      throw error;
    }
  };

  const unlikeMessage = async (messageId: string) => {
    try {
      if (!user?.id) return;
      ensureConversationID();

      const message = chat?.currentConversation?.messages?.find(
        (msg: Message) => msg.id === messageId
      );

      if (!message) return;

      // Update message metadata to remove like status
      const response = await conversationService.updateMessage(messageId, {
        metadata: {
          ...message.metadata,
          liked: false
        }
      });

      if (response.success) {
        updateMessage(messageId, {
          metadata: {
            ...message.metadata,
            liked: false
          }
        });
      }

      return response.success;
    } catch (error) {
      console.error('Could not unlike message:', error);
      return false;
    }
  };

  const setID = (id: string) => {
    conversationService.setID(id);
  }

  const setConversation = (conversation: Conversation) => {
    conversationService.setConversation(conversation);
  }

  return {
    callAgent,
    getAllConversations,
    likeMessage,
    unlikeMessage,
    loadConversation,
    startConversation,
    isConversationLoading,
    setID,
    setConversation
  };
};
