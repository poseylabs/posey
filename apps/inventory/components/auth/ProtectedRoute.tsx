'use client';

import React, { ReactNode } from 'react';
import { usePoseyState } from '@posey.ai/state';

interface ProtectedRouteProps {
  children: ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const user = usePoseyState((state) => state.user);
  const isAuthenticated = !!user?.id;

  // The AuthProvider already handles redirection logic
  // This component is just a safety check to prevent rendering children if not authenticated
  return isAuthenticated ? <>{children}</> : null;
} 