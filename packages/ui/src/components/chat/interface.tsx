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

  // Refs
  const titleInputRef = useRef<HTMLInputElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // State
  const [conversationTitle, setConversationTitle] = useState<string>('New Conversation');
  const [input, setInput] = useState<string>('');
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [status, setStatus] = useState<string>('idle');

  const currentConversation = usePoseyState((state) => state.chat.currentConversation);
  const conversationId = currentConversation?.id;

  const { callAgent, setConversation } = useConversation();

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

  console.log('Chat Interface', {
    currentConversation
  });

  return (
    <div className="interface">

      {/* Chat Header */}
      <div className="chat-header">
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

      {/* Chat Content */}
      <div
        ref={scrollAreaRef}
        className="chat-content-main pl-4 overflow-y-auto min-h-0 max-h-full"
      >
        <MessageList messages={currentConversation?.messages ?? []} />
      </div>\

      {/* Chat Footer */}
      <div className="chat-footer text-center p-4">

        <div>
          {status !== 'idle' && statusMessage && <ChatStatus
            status={status}
            message={statusMessage}
          />}
        </div>

        <ChatInput
          onSubmit={handleSubmit}
          value={input}
        />
      </div>
    </div>
  );
}
