'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { usePoseyState } from '@posey.ai/state';
import { Conversation, ConversationStatus } from '@posey.ai/core';
import type { Message } from "@posey.ai/core";

import {
  ChatInput,
  MessageList,
  ChatStatus,
  useConversation,
} from '@posey.ai/ui';

import './interface.css';
import { isEqual } from 'lodash';

interface ChatInterfaceProps {
  initialConversation: Conversation | null;
}

// Define a type for the location data
interface LocationData {
  latitude?: number; // Make optional
  longitude?: number; // Make optional
  city?: string; // Optional: if reverse geocoding is done later
  error?: string; // To store potential errors
}

export function ChatInterface({ initialConversation }: ChatInterfaceProps) {

  // Refs
  const processedConversations = useRef(new Set<string>());
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const titleInputRef = useRef<HTMLInputElement>(null);

  // State
  const [conversationTitle, setConversationTitle] = useState<string>('New Conversation');
  const [input, setInput] = useState<string>("");
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingState, setProcessingState] = useState<{
    id: string | null;
    status: 'pending' | 'processing' | 'completed' | 'error';
  }>({ id: null, status: 'pending' });
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [status, setStatus] = useState<string>('idle');
  const [browserLocation, setBrowserLocation] = useState<LocationData | null>(null);

  const state = usePoseyState();
  const messages = state.chat.currentConversation?.messages || [];

  const currentConversation = usePoseyState((state) => state.chat.currentConversation);
  const conversationId = currentConversation?.id;
  const conversationStatus = usePoseyState((state) => state.chat.currentConversation?.status);
  const updateConversation = usePoseyState((state) => state.updateConversation);

  const { callAgent } = useConversation({
    initialConversationId: initialConversation?.id || '',
  });

  // --- Fetch Browser Location on Mount --- 
  useEffect(() => {
    if ('geolocation' in navigator) {
      console.log('Geolocation is supported, fetching current position...');

      navigator.geolocation.getCurrentPosition(
        (position) => {
          setBrowserLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          });
          console.log('Browser location acquired:', position.coords);
        },
        (error) => {
          console.warn(`Geolocation error: ${error.message}`);
          // Now valid as lat/lon are optional
          setBrowserLocation({ error: error.message });
        },
        { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 } // Options: Increased timeout, force fresh location
      );
    } else {
      console.log('Geolocation is not supported by this browser.');
      // Now valid as lat/lon are optional
      setBrowserLocation({ error: 'Geolocation not supported' });
    }
  }, []); // Run only once on mount
  // --- End Fetch Browser Location --- 

  const handleSubmit = async (data: any) => {
    const messageContent = data.message;
    if (!messageContent.trim()) return;

    try {
      setStatus('loading');
      setStatusMessage('Sending message to agent...');

      const browserMetadata = {
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        language: navigator.language,
        user_agent: navigator.userAgent,
        // Add location data if available
        location: browserLocation,
      };

      const response = await callAgent({
        message: messageContent,
        metadata: {
          browser: browserMetadata
        },
      });

      console.log("AGENT RESPONSE", response);

      setInput('');
      setStatus('idle');
      setStatusMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
      setStatus('error');
      setStatusMessage('Failed to send message. Please try again.');
    }
  };

  const handleTitleClick = useCallback(() => {
    setIsEditingTitle(true);
    setTimeout(() => {
      titleInputRef.current?.focus();
      titleInputRef.current?.select();
    }, 0);
  }, []);

  const handleTitleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleTitleUpdate();
    } else if (e.key === 'Escape') {
      setIsEditingTitle(false);
    }
  }, []);

  const handleTitleUpdate = useCallback(async () => {
    if (!conversationId) return;
    try {
      await updateConversation(conversationId, { title: conversationTitle });
      setIsEditingTitle(false);
    } catch (error) {
      console.error('Error updating conversation:', error);
    }
  }, [conversationId, conversationTitle]);

  const [hasFetched, setHasFetched] = useState(false);

  useEffect(() => {
    // Only process if:
    // 1. We have a valid conversation
    // 2. The conversation is NEW
    // 3. It has exactly 1 message
    // 4. We haven't processed this conversation before
    // 5. We're not currently processing anything
    if (
      currentConversation?.id &&
      // currentConversation.status === ConversationStatus.NEW && // MODIFIED
      // currentConversation.messages?.length === 1 && // MODIFIED
      conversationStatus === ConversationStatus.NEW && // Use specific selector
      messages?.length === 1 && // Use specific selector length
      !processedConversations.current.has(currentConversation.id) &&
      processingState.status !== 'processing' && processingState.status !== 'error'
    ) {

      if (!hasFetched) {
        setHasFetched(true);
        console.log("Starting to process conversation:", currentConversation.id);

        // Immediately mark as processing to prevent duplicate calls
        setProcessingState({ id: currentConversation.id, status: 'processing' });
        processedConversations.current.add(currentConversation.id);
        setIsProcessing(true);
        setStatus('loading');
        setStatusMessage('Processing your message...');

        const firstMessage = messages?.[0];
        console.log("FIRST MESSAGE", firstMessage);

        const browserMetadata = {
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          language: navigator.language,
          user_agent: navigator.userAgent,
          // Add location data if available
          location: browserLocation,
        };

        callAgent({
          message: firstMessage?.content || '',
          metadata: {
            browser: browserMetadata
          },
          firstContact: true
        })
          .then((response: any) => {
            console.log("AGENT RESPONSE", response);
            setStatus('idle');
            setStatusMessage('');
            setProcessingState({ id: currentConversation.id, status: 'completed' });
          })
          .catch((error: any) => {
            console.error('Error processing new conversation:', error);
            setStatus('error');
            setStatusMessage('Failed to process message. Please try again.');
            // Remove from processed set on error to allow retry
            processedConversations.current.delete(currentConversation.id);
            setProcessingState({ id: currentConversation.id, status: 'error' });
            setHasFetched(false);
          })
          .finally(() => {
            setIsProcessing(false);
          });
      }

    }
  }, [
    currentConversation?.id,
    // currentConversation?.status, // REMOVED
    // currentConversation?.messages?.length, // REMOVED
    conversationStatus, // Use specific selector
    messages?.length ?? 0, // Add fallback for initial undefined state
    processingState.status,
    hasFetched,
    setIsProcessing,
    setStatus,
    setStatusMessage,
    callAgent,
    setProcessingState,
    browserLocation
  ]);

  return (
    <div className="chat-interface">

      {/* Chat Header */}
      <div className="chat-interface-header">
        <div className="px-4 flex items-center">
          {isEditingTitle ? (
            <input
              ref={titleInputRef}
              type="text"
              className="text-2xl font-bold bg-transparent border-b border-gray-300 focus:border-primary focus:outline-none w-full"
              value={conversationTitle}
              onChange={(e) => setConversationTitle(e.target.value)}
              onBlur={handleTitleUpdate}
              onKeyDown={handleTitleKeyDown}
            />
          ) : (
            <h1
              className="text-2xl font-bold cursor-pointer hover:text-primary transition-colors"
              onClick={handleTitleClick}
              title="Click to edit title"
            >
              {conversationTitle}
            </h1>
          )}
        </div>
      </div>

      <div
        ref={scrollAreaRef}
        className="chat-interface-content-main"
      >
        <div className="chat-interface-content">
          <MessageList
            key={`messages-${conversationId}-${messages.length}`}
            messages={messages}
          />
        </div>
      </div>

      {/* Chat Footer */}
      <div className="chat-interface-footer">
        <div>
          {status !== 'idle' && statusMessage && <ChatStatus
            status={status}
            message={statusMessage}
          />}
        </div>

        <ChatInput
          onSubmit={handleSubmit}
          placeholder="Message Posey..."
          className=""
          disabled={status === 'loading'}
          defaultValue=""
          hasActiveTasks={false}
          id="chat-input"
          label="Chat Input"
          value={input}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setInput(e.target.value)}
        />
      </div>
    </div>
  );
}
