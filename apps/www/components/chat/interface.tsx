'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { usePoseyState } from '@posey.ai/state';
import { Conversation, ConversationStatus, Message } from '@posey.ai/core';

import {
  ChatInput,
  MessageList,
  ChatStatus,
  useConversation,
} from '@posey.ai/ui';

import './interface.css';

export function ChatInterface() {

  // Refs
  const processedConversations = useRef(new Set<string>());
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const titleInputRef = useRef<HTMLInputElement>(null);

  // State
  const [conversationTitle, setConversationTitle] = useState<string>('New Conversation');
  const [input, setInput] = useState<string>('');
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingState, setProcessingState] = useState<{
    id: string | null;
    status: 'pending' | 'processing' | 'completed' | 'error';
  }>({ id: null, status: 'pending' });
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [status, setStatus] = useState<string>('idle');

  // Select the whole chat slice
  const chat = usePoseyState((state) => state.chat);
  // Derive conversation and messages from the chat slice
  const currentConversation = chat.currentConversation;
  const conversationId = currentConversation?.id;
  const messages = currentConversation?.messages ?? [];

  const { callAgent, setConversation } = useConversation();

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
      };

      await callAgent({
        message: messageContent,
        metadata: {
          browser: browserMetadata
        },
      });

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

  const updateConversation = useCallback(async (id: string, updates: Partial<Conversation>) => {
    // TODO: update conversation
  }, []);

  useEffect(() => {
    // Only process if:
    // 1. We have a valid conversation
    // 2. The conversation is NEW
    // 3. It has exactly 1 message
    // 4. We haven't processed this conversation before
    // 5. We're not currently processing anything
    if (
      currentConversation?.id &&
      currentConversation.status === ConversationStatus.NEW &&
      currentConversation.messages?.length === 1 &&
      !processedConversations.current.has(currentConversation.id) &&
      processingState.status !== 'processing' && processingState.status !== 'error'
    ) {
      console.log("Starting to process conversation:", currentConversation.id);

      // Immediately mark as processing to prevent duplicate calls
      setProcessingState({ id: currentConversation.id, status: 'processing' });
      processedConversations.current.add(currentConversation.id);
      setIsProcessing(true);
      setStatus('loading');
      setStatusMessage('Processing your message...');

      const firstMessage = currentConversation.messages[0];
      console.log("FIRST MESSAGE", firstMessage);

      const browserMetadata = {
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        language: navigator.language,
        user_agent: navigator.userAgent,
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
        })
        .finally(() => {
          setIsProcessing(false);
        });
    }
  }, [
    currentConversation?.id,
    currentConversation?.status,
    currentConversation?.messages?.length,
    processingState.status,
    setIsProcessing,
    setStatus,
    setStatusMessage,
    callAgent,
    setProcessingState
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
          <MessageList messages={messages as any as Message[]} />
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
