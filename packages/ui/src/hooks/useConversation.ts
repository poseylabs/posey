import { useEffect, useState, useCallback } from 'react';
import { Message, ConversationService, PoseyState, Conversation, ConversationStatus } from '@posey.ai/core';
import { usePoseyState } from '@posey.ai/state';
import { agentService } from '@posey.ai/core';

export interface UseConversationProps {
  fetchData?: boolean;
  initialConversationId?: string;
}

export const useConversation = ({
  fetchData = false,
  initialConversationId
}: UseConversationProps = {}) => {

  const state = usePoseyState();

  const {
    addMessage,
    updateMessage,
    user,
    chat,
    setState
  } = state.select((_state: PoseyState) => ({
    addMessage: _state.addMessage,
    updateMessage: _state.updateMessage,
    user: _state.user,
    chat: _state.chat,
    setState: _state.setState
  }));

  const [isConversationLoading, setIsConversationLoading] = useState(false);

  const [conversationService] = useState(() => {
    // Get the initial conversation object from the state IF the initialConversationId matches.
    // This relies on ChatProvider setting the state before this hook runs, which *should* happen now.
    const initialConvoFromState = initialConversationId === chat.currentConversation?.id ? chat.currentConversation : undefined;
    // console.log(`[useConversation init] Initializing ConversationService. Prop ID: ${initialConversationId}, State ID: ${chat.currentConversation?.id}, Using initial conversation from state: ${!!initialConvoFromState}`);

    return new ConversationService({
      user: user?.id,
      // Pass the conversation object from state if it matches the ID prop
      conversation: initialConvoFromState,
      // Use the passed ID preferentially for initialization
      currentConversationId: initialConversationId || chat.currentConversation?.id,
      fetchData
    });
  });

  const callAgent = useCallback(async ({
    message,
    metadata,
    firstContact = false,
  }: {
    message: string,
    metadata?: any,
    firstContact?: boolean
  }) => {
    // Get state *inside* the callback to ensure freshness
    const currentState = usePoseyState.getState();
    let currentConversationId = initialConversationId || currentState.chat.currentConversation?.id;

    try {
      setIsConversationLoading(true);

      // Log initial state check using fresh state
      console.log(`callAgent - Initial check. Store ID: ${currentState.chat.currentConversation?.id}, Service ID: ${conversationService.currentConversationId}, Using ID: ${currentConversationId}`);

      const currentMessages = currentState.chat.currentConversation?.messages || [];
      console.log('callAgent - Starting with messages count:', currentMessages.length);

      const messages = [...currentMessages];
      let userMessage: Message | undefined;

      if (!firstContact) {
        // --- Check ID before adding USER message ---
        if (!currentConversationId) {
           const errorMsg = "Cannot add user message: Conversation ID is missing.";
           console.error(`callAgent - ${errorMsg}`);
           throw new Error(errorMsg);
        }
        // Sync service ID *right before* the call using the latest derived ID
        if (conversationService.currentConversationId !== currentConversationId) {
            console.log(`callAgent - Syncing service ID to ${currentConversationId} before adding user message.`);
            conversationService.setID(currentConversationId);
            // Optional: Sync full conversation object if needed
            const currentConvoFromState = usePoseyState.getState().chat.currentConversation;
            if (currentConvoFromState && currentConvoFromState.id === currentConversationId) {
                conversationService.setConversation(currentConvoFromState);
            } else {
                console.warn(`callAgent - Could not sync full conversation object to service. State had: ${currentConvoFromState?.id}`);
            }
        }

        const newUserMessage = await conversationService.addMessage({
          content: message,
          sender: user?.id || 'anonymous',
          role: 'user',
          metadata: {
            user,
            ...metadata
          }
        });
        console.log('callAgent - Added user message:', newUserMessage.id);
        addMessage(newUserMessage);
        messages.push(newUserMessage);
        userMessage = newUserMessage;

        // If adding the message somehow provided the ID (e.g., from a local creation), update our variable
        if (!currentConversationId && conversationService.currentConversationId) {
            console.log(`callAgent - Updated currentConversationId from service after addMessage: ${conversationService.currentConversationId}`);
            currentConversationId = conversationService.currentConversationId;
        }
      }

      // --- Check ID before calling AGENT service ---
      if (!currentConversationId && !firstContact) {
         // If it's the first contact, the agent service might create the ID.
         // Otherwise, we should have had one from adding the user message.
         const errorMsg = "Cannot call agent service: Conversation ID is missing.";
         console.error(`callAgent - ${errorMsg}`);
         throw new Error(errorMsg);
      }
      // For firstContact, pass undefined ID - backend should handle creation
      const idToSend = firstContact ? undefined : currentConversationId;
      // --------------------------------------------

      // Send to agent
      console.log(`callAgent - Calling agent service for conversation ${idToSend || '(new)'} with ${messages.length} messages.`);

      const response: any = await agentService.call({
        messages,
        conversationId: idToSend, // Pass potentially undefined for new convos
        metadata: {
          ...user?.metadata
        }
      });

      if (!response?.success) {
        const errorMsg = response?.error || 'Agent call failed';
        console.error('Fatal error calling agent:', {
          errorMsg,
          response
        });
        throw new Error(errorMsg);
      }

      // Log the received metadata for debugging/inspection
      console.log('callAgent - Received agent response:', response?.data);

      // --- IMPORTANT: Update service/state with ID from response ---
      // Backend *must* return the conversation ID, especially if newly created.
      // Adjust property access based on actual API response structure.
      // Common places: response.conversationId, response.data.conversationId, response.data.metadata.conversationId
      const returnedConversationId = response?.data?.metadata?.conversationId || response?.data?.conversationId || response?.conversationId;

      if (returnedConversationId && returnedConversationId !== currentConversationId) {
          console.log(`callAgent - Updating conversation ID from agent response. Old: ${currentConversationId}, New: ${returnedConversationId}`);
          currentConversationId = returnedConversationId; // Update local variable
          conversationService.setID(returnedConversationId); // Update service instance

          // Optionally update the store if the ID was missing or changed
          if (!chat.currentConversation?.id || chat.currentConversation.id !== returnedConversationId) {
             console.warn(`callAgent - Updating store conversation ID. Store had: ${chat.currentConversation?.id}`);
             // Fetching the full conversation might be better, but for now, just update the ID
             const currentConvo = chat.currentConversation;
             setState({
               chat: {
                 ...chat,
                 currentConversation: {
                   ...(currentConvo || { messages: [], status: ConversationStatus.ACTIVE }), // Use existing convo or default
                   id: returnedConversationId, // Update the ID
                 } as Conversation, // Assert type
               },
             });
          }
      } else if (!returnedConversationId && !currentConversationId) {
         // If no ID was returned and we didn't have one (e.g., firstContact failed?), we can't proceed.
         const errorMsg = "Cannot add agent message: Conversation ID missing after agent response.";
         console.error(`callAgent - ${errorMsg}`);
         throw new Error(errorMsg);
      } else if (!returnedConversationId && currentConversationId) {
          console.warn(`callAgent - Agent response did not return a conversation ID, continuing with existing ID: ${currentConversationId}`);
      }
      // -------------------------------------------------------------

      // --- Sync ID before adding AGENT message ---
      // Use the potentially updated currentConversationId from agent response
      if (currentConversationId && conversationService.currentConversationId !== currentConversationId) {
          console.log(`callAgent - Syncing service ID to ${currentConversationId} before adding agent message.`);
          conversationService.setID(currentConversationId);
          // Optional: Sync full conversation object if needed
          const currentConvoFromState = usePoseyState.getState().chat.currentConversation;
          if (currentConvoFromState && currentConvoFromState.id === currentConversationId) {
              conversationService.setConversation(currentConvoFromState);
          }
      }
      // Check if service ID is now set
       if (!conversationService.currentConversationId) {
            const errorMsg = "Cannot add agent message: ConversationService ID is missing after agent response.";
            console.error(`callAgent - ${errorMsg} (Current local ID: ${currentConversationId})`);
            throw new Error(errorMsg);
       }
       // -------------------------------------------

      // Add agent response to conversation
      const agentMessage = await conversationService.addMessage({
        content: response?.data?.answer,
        sender: 'agent',
        role: 'assistant',
        metadata: response?.data?.metadata // This metadata might contain the ID again
      });
      console.log('callAgent - Added agent message:', agentMessage.id);

      addMessage(agentMessage);

      // Double-check the state update with a timeout
      setTimeout(() => {
        const finalState = usePoseyState.getState(); // Get latest state directly
        const afterMessages = finalState.chat?.currentConversation?.messages || [];
        console.log(`callAgent - After state update - Store ID: ${finalState.chat?.currentConversation?.id}, messages count: ${afterMessages.length}`);
      }, 500);

      return agentMessage;

    } catch (error: any) {
      console.error('Error sending message:', error);
      // Potentially update UI state here to show error feedback
      throw error; // Re-throw for the calling component
    } finally {
      setIsConversationLoading(false);
    }
  }, [
      conversationService,
      addMessage,
      user,
      chat,
      setIsConversationLoading,
      setState,
      // Include status setters if passed as props/context
      // agentService // Add if it's not static/imported globally
  ]);

  const getAllConversations = useCallback(async () => {
    const conversations = await conversationService.getAllConversations();
    return conversations;
  }, [conversationService]);

  const likeMessage = useCallback(async (messageId: string) => {
    try {
      if (!user?.id) return;

      // Sync service ID before the call
      const currentId = usePoseyState.getState().chat.currentConversation?.id;
      if (currentId && conversationService.currentConversationId !== currentId) {
          console.log(`likeMessage - Syncing service ID to ${currentId}`);
          conversationService.setID(currentId);
      }
      if (!conversationService.currentConversationId) throw new Error("Cannot like message: Conversation ID missing");

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
  }, [user, chat, conversationService, updateMessage]);

  const loadConversation = useCallback(async (conversationId: string) => {
    try {
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
  }, [conversationService, setState, chat]);

  const startConversation = useCallback(async (content: string) => {
    try {
      console.log(`[useConversation] Starting new conversation with content: "${content.substring(0, 50)}..."`);
      // Call the service method to create the conversation on the backend
      // This method MUST return the full new Conversation object including the ID
      // and potentially the initial messages array.
      const newConversation: Conversation | null = await conversationService.start(content);

      if (!newConversation || !newConversation.id) {
        throw new Error('Backend failed to return a valid conversation object with ID after start.');
      }

      console.log(`[useConversation] Conversation started successfully. ID: ${newConversation.id}`);

      // Update the global state with the new conversation
      // Note: We are NOT adding the initial message via addMessage here,
      // assuming the `newConversation` object returned by the service
      // already contains the initial message(s) in its `messages` array.
      // If not, we might need to call addMessage separately.
      setState({
        chat: {
          ...chat,
          currentConversation: newConversation
        }
      });

      // Return the newly created conversation object to the caller
      return newConversation;

    } catch (error) {
      console.error('Error in startConversation hook:', error);
      // Optionally update UI state to show error
      // Example: setErrorState('Failed to start conversation.');
      throw error; // Re-throw the error so the component can handle it
    }
  }, [conversationService, setState, chat, addMessage]);

  const unlikeMessage = useCallback(async (messageId: string) => {
    try {
      if (!user?.id) return;

      // Sync service ID before the call
      const currentId = usePoseyState.getState().chat.currentConversation?.id;
      if (currentId && conversationService.currentConversationId !== currentId) {
         console.log(`unlikeMessage - Syncing service ID to ${currentId}`);
         conversationService.setID(currentId);
      }
      if (!conversationService.currentConversationId) throw new Error("Cannot unlike message: Conversation ID missing");

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
  }, [user, chat, conversationService, updateMessage]);

  const setID = useCallback((id: string) => {
    conversationService.setID(id);
  }, [conversationService]);

  const setConversation = useCallback((conversation: Conversation) => {
    conversationService.setConversation(conversation);
  }, [conversationService]);

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
