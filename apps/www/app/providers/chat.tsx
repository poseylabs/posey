'use client';

import { useEffect, useRef } from 'react';
import { Conversation, PoseyState } from '@posey.ai/core';
import { ChatInterface } from '@posey.ai/ui';
import { usePoseyState } from '@posey.ai/state';

export function ChatProvider({
  conversation,
}: {
  conversation: Conversation | null
}) {
  // Add ref to track if we've already set this conversation
  const hasSetConversation = useRef(false);

  const state = usePoseyState();

  const {
    currentConversation,
    setCurrentConversation,
  } = state.select((state: PoseyState) => ({
    currentConversation: state.chat.currentConversation,
    setCurrentConversation: state.setCurrentConversation,
  }));

  useEffect(() => {
    // Only set the conversation if:
    // 1. We have a valid conversation from the server
    // 2. Either it's different from the current one OR we haven't set one yet
    // 3. We haven't already handled this specific conversation (prevents double processing)
    if (
      conversation &&
      conversation.id &&
      (conversation.id !== currentConversation?.id || !currentConversation) &&
      !hasSetConversation.current
    ) {
      // Mark that we've handled this conversation
      hasSetConversation.current = true;

      // Set the conversation in state
      setCurrentConversation(conversation);
    }
  }, [conversation, currentConversation, setCurrentConversation]);

  return <ChatInterface />;
}
