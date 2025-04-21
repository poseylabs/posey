'use client';
import { useEffect, useLayoutEffect, useState } from 'react';
import { Sidebar } from '../navigation';
import { ContentWrapper } from './content-wrapper';
import { usePoseyState } from '@posey.ai/state';
import { PoseyState } from '@posey.ai/core';
import { mergeClasses } from '../../utils/cn';
import { useConversation } from '../../hooks/useConversation';

import './drawer.css';

// Use this to avoid hydration mismatch
const useIsomorphicLayoutEffect = typeof window !== 'undefined' ? useLayoutEffect : useEffect;

export function DrawerContent({
  children,
  className = '',
  stickyFooter = false,
  sidebar = <Sidebar />
}: {
  children?: React.ReactNode;
  className?: string;
  sidebar?: React.ReactNode;
  stickyFooter?: boolean;
}) {
  const [isClient, setIsClient] = useState(false);
  const [hasFetched, setHasFetched] = useState(false);
  const state = usePoseyState();

  const { getAllConversations } = useConversation();

  const { status, chat } = state.select((state: PoseyState) => ({
    chat: state.chat,
    status: state.status,
    setSidebarOpen: state.setSidebarOpen
  }));

  const { conversations } = chat;
  const drawerClass = status.isSidebarOpen ? 'show-drawer' : '';
  const stickyFooterClass = stickyFooter ? 'sticky-footer' : '';

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (!hasFetched && isClient) {
      setHasFetched(true);
      getAllConversations().then((_conversations: any) => {
        if (_conversations?.success && _conversations?.data) {
          state.setConversations(_conversations?.data);
        } else {
          console.error("Error getting conversations", _conversations);
          setHasFetched(false);
        }
      }).catch((error: any) => {
        console.error("Error getting conversations", error);
        setHasFetched(false);
      });
    }
  }, [conversations, hasFetched]);

  return (
    <div className={mergeClasses('posey-drawer', className, drawerClass)}>
      <div className={mergeClasses('posey-sidebar', drawerClass)}>
        {sidebar}
      </div>
      <div className={mergeClasses('posey-drawer-content', drawerClass, stickyFooterClass)}>
        {children}
      </div>
    </div>
  );
}
