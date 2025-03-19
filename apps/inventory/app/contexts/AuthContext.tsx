"use client";

import { createContext, useContext, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { usePoseyState } from '@posey.ai/state';

interface AuthContextType {
  forceLogout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthContextProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const setUser = usePoseyState(state => state.setUser);
  const initState = usePoseyState(state => state.initState);
  const status = usePoseyState(state => state.status);
  
  const forceLogout = useCallback(() => {
    // Clear auth token
    if (typeof window !== 'undefined') {
      localStorage.removeItem('authToken');
    }
    
    // Update global state
    initState({
      user: undefined,
      status: {
        ...status,
        isInitialized: true,
        isLoading: false
      }
    });
    
    // Redirect to login page
    router.push('/auth/login');
  }, [router, initState, status]);
  
  return (
    <AuthContext.Provider value={{ forceLogout }}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to use the auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthContextProvider');
  }
  return context;
}
