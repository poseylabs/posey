'use client';

import { useEffect, useRef } from 'react';
import { Conversation, PoseyState } from '@posey.ai/core';
import { usePoseyState } from '@posey.ai/state';
import { ChatInterface } from '@/components/chat/interface';

export function ChatProvider({
  conversation,
}: {
  conversation: Conversation | null
}) {

  const hasSetConversation = useRef(false);
  const state = usePoseyState();

  // Use custom select method
  const {
    currentConversation,
    setCurrentConversation,
  } = state.select((state: PoseyState) => ({
    currentConversation: state.chat.currentConversation,
    setCurrentConversation: state.setCurrentConversation,
  }));

  useEffect(() => {
    console.log('[ChatProvider useEffect] Running effect. Conversation prop:', conversation);
    console.log('[ChatProvider useEffect] Current state conversation:', currentConversation);
    console.log('[ChatProvider useEffect] Current state conversation (RAW):', state.chat.currentConversation);
    console.log('[ChatProvider useEffect] Has already set conversation ref:', hasSetConversation.current);
    // --- This useEffect might become redundant or act as a fallback --- 
    // We keep it for now to handle potential updates if the conversation prop changes later
    if (
      conversation &&
      conversation.id &&
      (conversation.id !== currentConversation?.id || !currentConversation) &&
      !hasSetConversation.current // Check the ref again, though the above block should handle the initial set
    ) {
      console.log(`[ChatProvider useEffect] Conditions met (Effect Fallback/Update). Setting conversation in state with ID: ${conversation.id}`);
      // Mark that we've handled this conversation (redundant if render logic worked, but safe)
      hasSetConversation.current = true;

      // Set the conversation in state
      setCurrentConversation(conversation);
    } else {
      // Avoid logging "skipped" if the render logic already handled it.
      if (!(conversation && conversation.id && hasSetConversation.current && currentConversation?.id === conversation.id)) {
        console.log('[ChatProvider useEffect] Conditions NOT met or already handled. State update skipped.');
      }
    }
  }, [conversation, currentConversation, setCurrentConversation, state.chat.currentConversation]);

  return <ChatInterface initialConversation={currentConversation} />;
  // return <div>Chat Provider</div>;
}