"use client";

import { PageLoading } from '@posey.ai/ui';

export default function HomePage() {
  // Show loading indicator and let AuthProvider handle the redirects
  return (
    <div className="min-h-screen flex items-center justify-center">
      <PageLoading />
    </div>
  );
}
