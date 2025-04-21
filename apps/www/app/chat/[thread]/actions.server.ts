'use server';

import { cookies } from 'next/headers';
import type { Conversation } from '@posey.ai/core';

export async function getConversation(thread: string): Promise<Conversation | null> {
  if (!thread) {
    console.warn('No thread provided', { thread });
    return null;
  }

  console.log(`[getConversation] Attempting to fetch thread: ${thread}`);

  try {
    const apiBase = process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT || 'http://localhost:5555';
    console.log(`[getConversation] Using API base: ${apiBase}`);
    const cookieStore = await cookies();
    const cookieHeader = [];
    
    // Get the SuperTokens access token cookie
    const accessToken = cookieStore.get('sAccessToken');
    if (accessToken) {
      cookieHeader.push(`sAccessToken=${accessToken.value}`);
    }
    
    console.log(`[getConversation] Access token found: ${!!accessToken}`);
    
    // Get the SuperTokens refresh token cookie
    const refreshToken = cookieStore.get('sIdRefreshToken');
    if (refreshToken) {
      cookieHeader.push(`sIdRefreshToken=${refreshToken.value}`);
    }
    
    console.log(`[getConversation] Refresh token found: ${!!refreshToken}`);
    
    if (cookieHeader.length === 0) {
      console.warn('No authentication cookies found for API request');
      return null;
    }
    
    const fetchUrl = `${apiBase}/conversations/${thread}`;
    console.log(`[getConversation] Fetching URL: ${fetchUrl}`);
    
    const response = await fetch(`${apiBase}/conversations/${thread}`, {
      headers: {
        'Content-Type': 'application/json',
        'Cookie': cookieHeader.join('; ')
      }
    });

    if (!response.ok) {
      const responseBody = await response.text(); // Get raw response body
      console.error(`[getConversation] Failed to fetch conversation. Status: ${response.status} ${response.statusText}. URL: ${fetchUrl}`);
      console.error(`[getConversation] Raw error response body: ${responseBody}`);
      return null;
    }

    const result = await response.json();
    
    if (result.success || result.data) {
      return result.data as Conversation;
    }

    return null;
  } catch (error) {
    console.error('Failed to fetch conversation from server:', error);
    // We'll rely on client-side fetching instead
    return null;
  }
}
