'use client';
import { useCallback, useEffect, useRef, useState, useLayoutEffect } from 'react';
import { usePoseyState } from '@posey.ai/state';
import { Conversation, ConversationStatus } from '@posey.ai/core';

import { Navbar } from '../navigation/navbar/navbar';
import { ChatInput } from './input';
import { MessageList } from './messages/message-list';
import { ChatFormData } from '../../types';
import { DrawerContent } from '../layout/drawer-content';
import { ChatStatus } from './chat-status';
import { useConversation } from '../../hooks/useConversation';

import './interface.css';

interface Message {
  id: string;
  content: string;
  role: string;
  sender_type: string;
}

export function ChatInterface() {

  // State
  const [conversationId, setConversationId] = useState<string>('');
  const [conversationTitle, setConversationTitle] = useState<string>('New Conversation');
  const [input, setInput] = useState('');
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [status, setStatus] = useState<string>('idle');
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [hasSent, setHasSent] = useState(false);
  // Add processingState to track different states more explicitly
  const [processingState, setProcessingState] = useState<{
    id: string | null;
    status: 'pending' | 'processing' | 'completed' | 'error';
  }>({ id: null, status: 'pending' });

  // Add a ref to track if we've handled this conversation
  const handledConversationRef = useRef<string | null>(null);

  // const agent = useAgent('posey');
  const currentConversation = usePoseyState((state) => state.chat.currentConversation);
  const { callAgent, setConversation } = useConversation();

  // Single ref to track processed conversations
  const processedConversations = useRef(new Set<string>());

  useEffect(() => {
    if (currentConversation?.id) {
      setConversation(currentConversation);
    }
  }, [currentConversation]);

  // Refs
  const titleInputRef = useRef<HTMLInputElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const handleTitleClick = useCallback(() => {
    setIsEditingTitle(true);
    setTimeout(() => {
      titleInputRef.current?.focus();
      titleInputRef.current?.select();
    }, 0);
  }, []);

  const updateConversation = useCallback(async (id: string, updates: Partial<Conversation>) => {
    // TODO: update conversation
  }, []);

  const handleTitleUpdate = useCallback(async () => {
    if (!conversationId) return;

    try {
      await updateConversation(conversationId, { title: conversationTitle });
      setIsEditingTitle(false);
    } catch (error) {
      console.error('Error updating conversation:', error);
    }
  }, [conversationId, conversationTitle, updateConversation]);

  const handleTitleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleTitleUpdate();
    } else if (e.key === 'Escape') {
      setIsEditingTitle(false);
    }
  }, [handleTitleUpdate]);

  const handleSubmit = async (data: ChatFormData) => {
    try {
      setStatus('loading');
      setStatusMessage('Sending message to agent...');

      await callAgent({
        message: data.message
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

  // Replace useLayoutEffect with useEffect and better state management
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
      processingState.status !== 'processing'
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

      callAgent({
        message: firstMessage?.content || '',
        firstContact: true
      })
        .then(() => {
          setStatus('idle');
          setStatusMessage('');
          setProcessingState({ id: currentConversation.id, status: 'completed' });
        })
        .catch((error) => {
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
  }, [currentConversation?.id, currentConversation?.status, currentConversation?.messages?.length, processingState.status]);

  return (
    <DrawerContent>
      <div className="chat-header">
        <Navbar />
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
        className="chat-content-main pl-4 overflow-y-auto min-h-0 max-h-full"
      >
        <MessageList messages={currentConversation?.messages ?? []} />
      </div>
      <div className="chat-footer text-center p-4">

        {status !== 'idle' && statusMessage && <ChatStatus
          status={status}
          message={statusMessage}
        />}

        <ChatInput
          onSubmit={handleSubmit}
          value={input}
        />
      </div>
    </DrawerContent>
  );
}
