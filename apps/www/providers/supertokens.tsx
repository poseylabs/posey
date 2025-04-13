'use client';

import { AuthProvider, PageLoading } from '@posey.ai/ui';
import type { SuperTokensProviderProps } from '@posey.ai/ui/types';
import { useEffect } from 'react';
import { useState } from 'react';
import SuperTokensReact from 'supertokens-auth-react';

export function SuperTokensProvider(props: SuperTokensProviderProps) {

  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (!initialized && typeof window !== 'undefined') {
      setInitialized(true);
      SuperTokensReact.init(props.supertokensConfig);
    }
  }, [initialized]);

  if (!initialized) return <PageLoading />;

  return (
    <AuthProvider {...props} />
  );

}