'use client';

import { Conversation } from '@posey.ai/core';
import { ChatProvider } from '@/providers/chat';

interface ChatClientProps {
  conversation: Conversation | null;
}

export function ChatClient({ conversation }: ChatClientProps) {
  return <ChatProvider conversation={conversation} />;
} 