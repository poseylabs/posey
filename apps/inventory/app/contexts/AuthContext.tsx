"use client";

import { createContext, useContext, useCallback, ReactNode, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { usePoseyState } from '@posey.ai/state';
import { User } from "@posey.ai/core";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  forceLogout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthContextProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const router = useRouter();
  // const setUser = usePoseyState(state => state.setUser);
  const initState = usePoseyState(state => state.initState);
  const status = usePoseyState(state => state.status);
  const [user, setUserState] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  
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

  useEffect(() => {
    const fetchUser = async () => {
      const storedUser = null; // Replace with actual logic
      setUserState(storedUser);
      setLoading(false);
    };
    fetchUser();
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, forceLogout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use the auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthContextProvider');
  }
  return context;
}
