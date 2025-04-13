'use client';
import { Conversation } from '@posey.ai/core';
import { ChatProvider } from '@posey.ai/ui';

export function ChatContent({ conversation }: { conversation: Conversation | null }) {
  return (
    <ChatProvider conversation={conversation} />
  );
}
