'use client';

// External Imports
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';

// Posey Imports
import { getSession, PoseyState } from '@posey.ai/core'; // Import from core
import { usePoseyState } from '@posey.ai/state'; // Import from state
import { PageLoading } from '@/components/status'; // Relative UI import
import { AuthError } from '@/components/auth/auth-error';

interface AuthProviderProps {
  children: React.ReactNode;
  publicPaths: string[];
}

export function AuthProvider({
  children,
  publicPaths
}: AuthProviderProps) {
  const state = usePoseyState();
  const pathname = usePathname();
  const [isClient, setIsClient] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isFetching, setIsFetching] = useState(false);

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

  // Determine if the current path requires authentication
  const isAuthRequired = !publicPaths.some(publicPath => {
    // console.log("Checking if path is public", {
    //   pathname,
    //   publicPath
    // });
    if (publicPath === '/') {
      // Exact match for the root path
      return pathname === publicPath;
    }
    // Prefix match for other public paths
    return pathname.startsWith(publicPath);
  });

  const getUserSession = useCallback(async () => {
    try {
      const data = await getSession();
      const user = data?.user;
      const session = data?.session;

      if (session?.sessionHandle && user?.id && user?.email) {
        await setUser({ user });
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
      console.error("AuthProvider Error fetching session:", error);
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
  }, [initState, setUser, status]);

  useEffect(() => {
    if (!isClient) setIsClient(true);
  }, [isClient]);

  useEffect(() => {
    if (isClient && !isFetching) {
      setIsFetching(true);
      getUserSession();
    }
  }, [getUserSession, isFetching, isClient]);

  if (isLoading) {
    return <PageLoading />;
  }

  // Check if auth is required and user is not logged in
  if (!isLoading && isClient && isAuthRequired && !isLoggedIn) {
    return <AuthError message="This page requires you to be logged in." redirect LinkComponent={Link} />;
  }

  return (
    <div className="w-full h-full">
      {children}
    </div>
  );
} 