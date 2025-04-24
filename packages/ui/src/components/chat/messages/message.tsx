'use client';
import './message.css'
import { PlayIcon, PauseIcon, DownloadIcon, BookmarkIcon, ExternalLinkIcon, BrainIcon } from 'lucide-react'
// import ReactMarkdown from 'react-markdown'
// import remarkGfm from 'remark-gfm'
import { useEffect, useState } from 'react'
// import { remark } from 'remark';
// import html from 'remark-html';
import DOMPurify from 'dompurify';

import { Message, PoseyState } from "@posey.ai/core";
import { config } from '@posey.ai/core/config'
import { usePoseyState } from '@posey.ai/state';

import { poseyAvatar } from '../../posey/avatar'
import { Button } from '../../form';

interface MediaItem {
  type: string;
  url: string;
  metadata?: Record<string, any>;
}

interface WebSearchResult {
  title: string;
  url: string;
  snippet?: string;
  content?: {
    title?: string;
    text?: string;
  };
}

const { models } = config
// const { availableModels } = models.llm

export function ChatMessage({
  debug = false,
  message,
  isSpeaking,
  onPlayPause
}: {
  debug?: boolean,
  message: Message;
  isSpeaking: string | null;
  onPlayPause: (messageId: string, text: string) => void;
}) {
  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [reasoning, setReasoning] = useState<string | null>(null);
  const [showReasoning, setShowReasoning] = useState(false);
  const [messageContent, setMessageContent] = useState<string | null>(null);

  const isAgent = message.sender_type !== 'human';

  const state = usePoseyState();
  const {
    user
  } = state.select((state: PoseyState) => ({
    user: state.user
  }));

  const getAvatar = () => {
    if (isAgent) return poseyAvatar;
    return user?.metadata?.profile?.avatar;
  }

  // Handle media array
  const media = (message.metadata?.media || []) as MediaItem[];
  const hasMedia = media.length > 0;

  const _avatar = getAvatar() || null;

  const isPlaying = isSpeaking === message.id;

  const likeMessage = async () => {
    if (!user?.id) return;

    try {
      setIsSaving(true);
      const response = await fetch('/api/likes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: user.id,
          messageId: message.id,
          conversationId: message.conversation_id,
          content: message.content,
          metadata: message.metadata
        })
      });

      if (response.ok) {
        setIsSaved(true);
      }
    } catch (error) {
      console.error('Error saving message:', error);
    } finally {
      setIsSaving(false);
    }
  };

  useEffect(() => {
    if ((message?.content && typeof message?.content === 'string') || (message && typeof message === 'string')) {

      const message_content: any = message?.content || message;
      const thinkMatch = message_content?.match(/<think>([\s\S]*?)<\/think>/);
      let processedContent = message_content;

      if (thinkMatch) {
        // Extract content between think tags
        setReasoning(thinkMatch[1].trim());
        // Remove think tags from displayed content
        processedContent = message_content?.replace(/<think>[\s\S]*?<\/think>/, '').trim()
      }

      if (processedContent !== messageContent) {
        setMessageContent(processedContent);
      }
    }
  }, [message, messageContent]);

  useEffect(() => {
    if (message) {
      console.log('Render message:', message);
    }
  }, [message]);

  const renderContent = () => {
    switch (message.metadata?.type) {
      case 'image':
        return (
          <>
            <div className="chat-content whitespace-pre-wrap">{message.content}</div>
            {message.metadata?.media?.map((media: any, index: number) => (
              <div key={index} className="mt-2">
                <img
                  src={media.url}
                  alt={media.metadata?.prompt || 'Generated image'}
                  className="rounded-lg max-w-full"
                />
                {media.metadata?.prompt && (
                  <div className="text-xs text-base-content/70 mt-1">
                    Prompt: {media.metadata.prompt}
                  </div>
                )}
              </div>
            ))}
          </>
        );
      case 'file':
        return (
          <>
            <div className="chat-content whitespace-pre-wrap">{message.content}</div>
            {message.metadata?.file && (
              <div className="mt-2 p-2 bg-base-300 rounded-lg flex items-center gap-2">
                <div className="flex-1">
                  <div className="font-medium">{message.metadata.file.name}</div>
                  <div className="text-xs text-base-content/70">
                    {message.metadata.file.type} • {(message.metadata.file.size / 1024).toFixed(1)}KB
                  </div>
                </div>
                {message.metadata.file.url && (
                  <a
                    href={message.metadata.file.url}
                    download={message.metadata.file.name}
                    className="btn btn-ghost btn-sm"
                  >
                    <DownloadIcon className="w-4 h-4" />
                  </a>
                )}
              </div>
            )}
          </>
        );
      default:
        // Fallback plain text content (after <think> tag removal)
        const plainTextContent = typeof messageContent === 'string' ? messageContent : '';
        // Check for pre-rendered HTML in both possible locations
        const htmlContent = message.metadata?.contentHtml || message.metadata?.analysis?.contentHtml;

        if (htmlContent && typeof htmlContent === 'string') {
          // Sanitize and render the HTML
          const sanitizedHtml = DOMPurify.sanitize(htmlContent, {
            ADD_ATTR: ['target', 'rel'], // Allow target and rel attributes for links
            ADD_TAGS: ['a'], // Ensure anchor tags are allowed
          });

          return (
            <div
              className="chat-content prose prose-sm prose-neutral dark:prose-invert max-w-none
                        prose-a:text-primary prose-a:no-underline hover:prose-a:underline
                        prose-p:my-1 prose-headings:my-2"
              dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
            />
          );
        } else {
          console.debug('Message metadata structure:', message.metadata);
          // Fallback to rendering plain text content with link detection
          return (
            <div className="chat-content whitespace-pre-wrap break-words">
              {plainTextContent.split(/\b(https?:\/\/[^\s]+)\b/).map((part, i) => {
                if (part.match(/^https?:\/\//)) {
                  return (
                    <a
                      key={i}
                      href={part}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      {part}
                    </a>
                  );
                }
                return part;
              })}
            </div>
          );
        }
    }
  };

  return (
    <div className={`chat message w-full pr-4 ${isAgent ? "chat-start" : "chat-end"}`}>
      {_avatar && <div className="chat-image avatar flex-">
        <div className="w-10 rounded-full">
          <img
            alt="Tailwind CSS chat bubble component"
            src={_avatar} />
        </div>
      </div>}
      <div className="chat-header mb-2">
        <span className="text-sm font-bold inline-block mr-2">
          {!isAgent ? "You" : "Posey"} ({message.sender_type})
        </span>
        <time className="text-xs opacity-50">12:45</time>
      </div>
      <div className="chat-bubble max-w-4xl">
        {renderContent()}
        {/* {message?.content} */}

        {isAgent && <div>
          {/* Show reasoning if available */}
          {reasoning && (
            <div className="reasoning-section mt-4 border-t border-base-300 pt-4">
              {showReasoning && (
                <div className="bg-base-200 rounded-lg p-4 mt-2">
                  {reasoning}
                </div>
              )}
            </div>
          )}

          {/* Show web search results if available */}
          {message.metadata?.references && message.metadata.references.length > 0 && (
            <div className="web-search-results mt-4 border-t border-base-300 pt-4">
              <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                <ExternalLinkIcon size={14} />
                References
              </h4>
              <ul className="text-sm space-y-2">
                {message.metadata.references.map((result: WebSearchResult, index: number) => (
                  <li key={`search-result-${index}`} className="flex items-start">
                    <span className="mr-2 text-xs opacity-50">{index + 1}.</span>
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-primary transition-colors duration-200 hover:underline"
                    >
                      {result.title || result.content?.title || 'External Link'}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* <div className="message-footer">
            <div className="message-footer-left">
              {message.metadata?.model && (
                <span className="opacity-70">
                  via {message.metadata?.model}
                </span>
              )}
            </div>

            <div className="message-footer-right">
              <div>
                <Button
                  onClick={() => setShowReasoning(!showReasoning)}
                  className="btn btn-ghost btn-xs gap-2 mb-2"
                >
                  <BrainIcon size={14} />
                  {showReasoning ? 'Hide reasoning' : 'Show reasoning'}
                </Button>
              </div>
              <Button
                onClick={() => onPlayPause(message.id, message.content)}
                className="ml-2 btn btn-ghost btn-xs"
                aria-label={isPlaying ? 'Pause' : 'Play'}
              >
                {isPlaying ? <PauseIcon size={16} /> : <PlayIcon size={16} />}
              </Button>
              
              <Button
                className={`ml-2 btn btn-ghost btn-xs ${isSaved ? 'text-primary' : ''}`}
              >
                <DownloadIcon size={16} />
              </Button>

              <Button
                onClick={likeMessage}
                disabled={isSaving || isSaved}
                className={`ml-2 btn btn-ghost btn-xs ${isSaved ? 'text-primary' : ''}`}
              >
                <BookmarkIcon size={16} />
              </Button>
            </div>
          </div> */}
        </div>}


      </div>
      <div className="chat-footer opacity-50">Delivered</div>
    </div>
  )
}
