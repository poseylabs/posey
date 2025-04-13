"use client";

import { useRouter } from 'next/navigation';
import Session from 'supertokens-web-js/recipe/session';
import { useEffect, useState } from 'react';

export default function HomePage() {
  const router = useRouter();
  const [didError, setDidError] = useState(false);

  useEffect(() => {
    void Session.attemptRefreshingSession()
      .then((hasSession) => {
        if (hasSession) {
          router.replace('/dashboard');
        } else {
          console.log("B");
          router.replace('/auth/login');
        }
      })
      .catch((err: any) => {
        setDidError(true);
        console.log("Auth Error", err);
      });
  }, [router]);

  return null;

}
