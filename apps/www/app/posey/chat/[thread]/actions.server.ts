'use server';

import { cookies } from 'next/headers';
import type { Conversation, Message } from '@posey.ai/core';
import { marked } from 'marked';

export async function getConversation(thread: string): Promise<Conversation | null> {
  if (!thread) {
    console.warn('No thread provided', { thread });
    return null;
  }

  try {
    const apiBase = process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT || 'http://localhost:5555';
    const cookieStore = await cookies();
    const cookieHeader = [];
    
    // Get the SuperTokens access token cookie
    const accessToken = cookieStore.get('sAccessToken');
    if (accessToken) {
      cookieHeader.push(`sAccessToken=${accessToken.value}`);
    }

    const refreshToken = cookieStore.get('sIdRefreshToken');
    if (refreshToken) {
      cookieHeader.push(`sIdRefreshToken=${refreshToken.value}`);
    }
    
    if (cookieHeader.length === 0) {
      console.warn('No authentication cookies found for API request');
      return null;
    }
    
    const fetchUrl = `${apiBase}/conversations/${thread}`;
    
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
    
    if (result.success && result.data) {
      const conversation = result.data as Conversation;

      // --- Add Markdown to HTML conversion for existing messages --- 
      if (conversation.messages && Array.isArray(conversation.messages)) {
        console.debug(`[getConversation/${thread}] Processing ${conversation.messages.length} messages for HTML conversion.`);
        for (const message of conversation.messages) {
          if (typeof message.content === 'string') {
            try {
              const htmlContent = await marked.parse(message.content);
              // Ensure metadata object exists
              message.metadata = message.metadata || {}; 
              message.metadata.contentHtml = htmlContent;
              console.debug(`[getConversation/${thread}/message/${message.id}] Successfully converted message content to HTML.`);
            } catch (error) {
              console.error(`[getConversation/${thread}/message/${message.id}] Error converting message content to HTML: ${error}`);
              // Optionally keep contentHtml as null/undefined or set an error flag
              if (message.metadata) {
                message.metadata.contentHtml = null; // Keep original content on error
              }
            }
          } else {
             console.debug(`[getConversation/${thread}/message/${message.id}] Message content is not a string (type: ${typeof message.content}), skipping HTML conversion.`);
          }
        }
      }
      // --- End Markdown to HTML conversion --- 
      
      return conversation;
    }

    return null;
  } catch (error) {
    console.error('Failed to fetch conversation from server:', error);
    // We'll rely on client-side fetching instead
    return null;
  }
}
