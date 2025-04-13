import { Conversation } from '@posey.ai/core';
import { ChatClient } from './chat-client';
import { getConversation } from './actions.server';

export default async function Page({
  params
}: {
  params: Promise<{ thread: string }>
}) {
  const thread = (await params).thread;
  const conversation: Conversation | null = await getConversation(thread);

  return <ChatClient conversation={conversation} />;
}
