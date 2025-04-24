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
    if (
      conversation &&
      conversation.id &&
      (conversation.id !== currentConversation?.id || !currentConversation) &&
      !hasSetConversation.current // Check the ref again, though the above block should handle the initial set
    ) {
      hasSetConversation.current = true;

      // Set the conversation in state
      setCurrentConversation(conversation);
    }
  }, [conversation, currentConversation, setCurrentConversation, state.chat.currentConversation]);

  return <ChatInterface initialConversation={currentConversation} />;

}