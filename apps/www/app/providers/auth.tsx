'use client';

import { useEffect, useState } from 'react';
import { getSession } from '@posey.ai/core';
import { AuthError, PageLoading } from '@posey.ai/ui';
import { usePoseyState } from '@posey.ai/state';
import type { PoseyState } from '@posey.ai/core/types';
import SuperTokens from 'supertokens-auth-react';

import { frontendConfig } from '@/config/supertokens';

// Initialize SuperTokens only on client side
if (typeof window !== 'undefined') {
  SuperTokens.init(frontendConfig);
}

export function AuthProvider({
  authRequired = false,
  children
}: {
  authRequired?: boolean,
  children: React.ReactNode
}) {
  const state = usePoseyState();
  const [isClient, setIsClient] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const {
    user,
    setUser,
    status,
    initState
  } = state.select((state: PoseyState) => ({
    user: state.user,
    setUser: state.setUser,
    status: state.status,
    initState: state.initState,
  }));

  const isLoggedIn = !!user?.id && !!user?.email;

  const getUserSession = async () => {
    try {
      const data = await getSession();
      const user = data?.user;
      const session = data?.session;

      if (session?.sessionHandle && user?.id && user?.email) {

        await setUser({ user });
        // Initialize state after successful user setup
        await initState({
          user,
          status: {
            ...status,
            isInitialized: true,
            isLoading: false
          }
        });
        return true;
      }

      await initState({
        user: undefined,
        status: {
          ...status,
          isInitialized: true,
          isLoading: false
        }
      });
      return false;
    } catch (error) {
      await initState({
        user: undefined,
        status: {
          ...status,
          isInitialized: true,
          isLoading: false,
          isErrored: true
        }
      });
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (isClient) {
      getUserSession();
    }
  }, [isClient]);

  // Handle auth required redirects
  useEffect(() => {
    if (!isLoading && authRequired && !isLoggedIn) {
      // redirect is handled by AuthError
    }
  }, [authRequired, isLoading, isLoggedIn]);

  if (isLoading) {
    return <PageLoading />;
  }

  if (!isLoading && isClient && authRequired && !isLoggedIn) {
    return <AuthError message="This page requires you to be logged in." redirect />;
  }

  return (
    <div className="w-full h-full">
      {children}
    </div>
  );
}
