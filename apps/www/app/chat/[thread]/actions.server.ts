'use server';

import { cookies as nextCookies } from 'next/headers';
import { ApiHelper, Conversation } from '@posey.ai/core';

const api: any = new ApiHelper({
  apiBase: process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT
});

export async function getConversation(thread: string): Promise<Conversation | null> {

  const cookies = await nextCookies();
  const accessToken = cookies.get('sAccessToken')?.value;

  if (accessToken) {
    api.setAccessToken(accessToken);
  }

  if (!thread) {
    console.warn('No thread provided', { thread });
    return null;
  }

  try {
    const _conversation = await api.get(`/conversations/${thread}`);

    if (_conversation.success) {
      return _conversation?.data as Conversation;
    }

    return null;
  } catch (error) {
    console.error('Failed to fetch conversation:', error);
    return null;
  }
}
