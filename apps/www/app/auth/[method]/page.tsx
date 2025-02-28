'use client';

import React, { useEffect, useState } from 'react';
import { AuthForm } from '@posey.ai/ui';
import { userLogin, userRegister } from '@posey.ai/core';
import { usePoseyState } from '@posey.ai/state';
import { useRouter, useParams } from 'next/navigation';

export default function AuthPage() {
  const { method } = useParams();
  const setUser = usePoseyState((state) => state.setUser);
  const router = useRouter();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!['login', 'register'].includes(method as string)) {
      console.warn(`Invalid auth method: ${method}. Redirecting to login.`);
      // router.replace('/auth/login');
    }
  }, [method, router]);

  useEffect(() => {
    // Check for HTTPS in production
    if (process.env.NODE_ENV === 'production' &&
      window.location.protocol !== 'https:') {
      console.error('Authentication requires HTTPS');
      // router.push('/error?message=secure-connection-required');
    }
  }, []);

  const handleSubmit = async (formData: any) => {
    setErrorMessage(null);
    try {
      // Add basic client-side validation
      if (!formData.password || formData.password.length < 8) {
        setErrorMessage('Password must be at least 8 characters');
        return;
      }

      // Add rate limiting
      const rateLimitKey = `auth_attempts_${method}_${Date.now()}`;
      const attempts = localStorage.getItem(rateLimitKey) || '0';
      if (parseInt(attempts) > 5) {
        setErrorMessage('Too many attempts. Please try again later.');
        return;
      }
      localStorage.setItem(rateLimitKey, (parseInt(attempts) + 1).toString());

      let session;
      if (method === 'login') {
        session = await userLogin(formData.email, formData.password);
      } else if (method === 'register') {
        session = await userRegister({
          user: {
            email: formData.email,
            password: formData.password,
            username: formData.username,
          },
        });
      }

      if (session && session?.user) {
        // Save the session token in localStorage for API requests
        if (session.session?.sessionHandle) {
          localStorage.setItem('authToken', session.session.sessionHandle);
        }

        await setUser({ user: session.user });
        router.push('/');
      } else {
        const errorMsg = method === 'register' ? 'Failed to register. Please check your information.' : 'Invalid email or password.';
        console.error(`Authentication failed:`, session);
        setErrorMessage(errorMsg);
      }
    } catch (error: any) {
      console.error(`${method} error:`, error);
      setErrorMessage(error.message || 'Authentication failed. Please try again.');
    }
  };

  const formTitle = method === 'login' ? 'Login to Posey' : 'Register for Posey';
  const formDescription = method === 'login' ? 'Enter your credentials to continue' : 'Create an account to get started';
  const toggleMethodText = method === 'login' ? 'Create one' : 'Already have an account?';
  const toggleMethodLink = method === 'login' ? '/auth/register' : '/auth/login';
  const toggleMethodLabel = method === 'login' ? 'Register' : 'Login';

  if (!['login', 'register'].includes(method as string)) {
    return null;
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="p-6 m-10 rounded-lg w-full max-w-md">
        <div className="text-center">
          <h1 className="text-2xl font-bold">{formTitle}</h1>
          <p className="mt-2 text-sm text-gray-500">{formDescription}</p>
        </div>

        {errorMessage && (
          <div className="mt-4 text-center text-red-500">
            {errorMessage}
          </div>
        )}

        <div className="mt-4" suppressHydrationWarning>
          <AuthForm mode={method as 'login' | 'register'} onSubmit={handleSubmit} />
        </div>

        <div className="mt-4 text-center">
          <p className="text-sm text-gray-600">
            {toggleMethodText}{' '}
            <a href={toggleMethodLink} className="text-primary hover:underline">
              {toggleMethodLabel}
            </a>
          </p>
        </div>
      </div>
    </div>
  );
} 
