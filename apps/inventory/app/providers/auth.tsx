'use client';

import { useCallback, useEffect, useState } from 'react';
import { getSession } from '@posey.ai/core';
import { AuthError, PageLoading } from '@posey.ai/ui';
import { usePoseyState } from '@posey.ai/state';
import type { PoseyState } from '@posey.ai/core/types';
import SuperTokens from 'supertokens-auth-react';
import { usePathname, useRouter } from 'next/navigation';
import { AuthContextProvider, useAuth } from '../contexts/AuthContext';

import { frontendConfig } from '@/config/supertokens';

// Initialize SuperTokens only on client side
if (typeof window !== 'undefined') {
  SuperTokens.init(frontendConfig);
}

// Routes that don't require authentication
const publicRoutes = ['/auth/login', '/auth/register'];
// Home route is special - we show loading and handle redirects 
const HOME_ROUTE = '/';

function AuthProviderInner({
  authRequired = false,
  children
}: {
  authRequired?: boolean,
  children: React.ReactNode
}) {
  const state = usePoseyState();
  const [isClient, setIsClient] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [sessionChecked, setSessionChecked] = useState(false);
  const [shouldRedirect, setShouldRedirect] = useState<string | null>(null);
  const pathname = usePathname();
  const router = useRouter();
  const { forceLogout } = useAuth();

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
  const isAuthRoute = publicRoutes.includes(pathname);
  const isHomeRoute = pathname === HOME_ROUTE;

  // useEffect(() => {
  //   let redirectTimer: NodeJS.Timeout;

  //   if (shouldRedirect && sessionChecked) {
  //     console.log('Redirecting to:', shouldRedirect);
  //     redirectTimer = setTimeout(() => {
  //       router.push(shouldRedirect);
  //       setShouldRedirect(null);
  //     }, 500);
  //   }

  //   return () => {
  //     if (redirectTimer) clearTimeout(redirectTimer);
  //   };
  // }, [shouldRedirect, sessionChecked, router]);

  // useEffect(() => {
  //   if (!isLoading && sessionChecked) {
  //     if (isAuthRoute && isLoggedIn) {
  //       console.log('User is logged in but on auth route, redirecting to dashboard');
  //       setShouldRedirect('/dashboard');
  //     } else if (!isAuthRoute && !isLoggedIn) {
  //       console.log('User is not logged in, redirecting to login');
  //       setShouldRedirect('/auth/login');
  //     } else if (isHomeRoute && !isLoggedIn) {
  //       console.log('User is not logged in on home route, redirecting to login');
  //       setShouldRedirect('/auth/login');
  //     } else if (isHomeRoute && isLoggedIn) {
  //       console.log('User is logged in on home route, redirecting to dashboard');
  //       setShouldRedirect('/dashboard');
  //     }
  //   }
  // }, [isLoading, sessionChecked, isAuthRoute, isLoggedIn, isHomeRoute, pathname]);

  const getUserSession = useCallback(async () => {
    try {
      console.log('Checking user session...');
      const authToken = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;

      if (!authToken) {
        console.log('No auth token in localStorage');
        await initState({
          user: undefined,
          status: {
            ...status,
            isInitialized: true,
            isLoading: false
          }
        });
        setSessionChecked(true);
        return false;
      }

      const data = await getSession();
      const user = data?.user;
      const session = data?.session;

      if (session?.sessionHandle && user?.id && user?.email) {
        console.log('Valid session found:', user.email);
        console.log('User ID:', user.id);
        await setUser({ user });
        await initState({
          user,
          status: {
            ...status,
            isInitialized: true,
            isLoading: false
          }
        });
        setSessionChecked(true);
        return true;
      }

      console.log('No valid session found');
      forceLogout();
      setSessionChecked(true);
      return false;
    } catch (error) {
      console.error('Session check error:', error);
      forceLogout();
      setSessionChecked(true);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [forceLogout, initState, setUser, status]);

  // useEffect(() => {
  //   setIsClient(true);
  // }, []);

  // useEffect(() => {
  //   if (isClient) {
  //     getUserSession();
  //   }
  // }, [getUserSession, isClient]);

  useEffect(() => {
    console.log('authRequired', authRequired);
  }, [authRequired]);

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <PageLoading />
      </div>
    );
  }

  return (
    <div className="w-full h-full">
      {(!isAuthRoute && !isLoggedIn && !isHomeRoute) ? (
        <AuthError message="This page requires you to be logged in." redirect={false} />
      ) : (
        children
      )}
    </div>
  );
}

// Wrapper component that provides the AuthContext
export function AuthProvider(props: {
  authRequired?: boolean,
  children: React.ReactNode
}) {
  return (
    // <AuthProviderInner {...props} />
    // <AuthContextProvider>
    //   <AuthProviderInner {...props} />
    // </AuthContextProvider>
  );
}

const handleLogout = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('authToken');
    window.location.href = '/auth/login';
  }
};

if (typeof window !== 'undefined') {
  window.forceLogout = handleLogout;
}

// Create a no-hooks version of the logout function
// const logoutWithoutHooks = () => {
//   if (typeof window !== 'undefined') {
//     localStorage.removeItem('authToken');
//     window.location.href = '/auth/login';
//   }
// };

// Now this useEffect is inside the component
// useEffect(() => {
//   if (typeof window !== 'undefined') {
//     // Assign the non-hooks version to window
//     window.forceLogout = logoutWithoutHooks;
//   }
  
//   return () => {
//     if (typeof window !== 'undefined') {
//       delete window.forceLogout;
//     }
//   };
// }, []); // No dependency on props anymore

// Add TypeScript declaration at the top of the file (outside components)
declare global {
  interface Window {
    forceLogout?: () => void;
  }
} 