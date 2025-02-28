import { AuthProvider } from '@/app/providers/auth';
import { Conversation } from '@posey.ai/core';
import { ChatProvider } from '@/app/providers/chat';
import { getConversation } from './actions.server';

export default async function Page({
  params
}: {
  params: Promise<{ thread: string }>
}) {
  const thread = (await params).thread;
  const conversation: Conversation|null = await getConversation(thread);

  return (
    <AuthProvider authRequired={true}>
      <ChatProvider conversation={conversation} />
    </AuthProvider>
  );
}
