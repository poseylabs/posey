import Link from 'next/link';
import { useEffect } from 'react';
import { usePoseyRouter } from '../../hooks/router';

interface AuthErrorProps {
  message?: string;
  redirect?: boolean;
  useHashLinks?: boolean;
}

export const AuthError: React.FC<AuthErrorProps> = ({ message, redirect, useHashLinks = false }) => {
  const { linkTo } = usePoseyRouter({ useHashLinks });

  useEffect(() => {
    if (redirect) {
      console.log('redirecting to login (blocked)');
      linkTo('/auth/login');
    }
  }, [redirect]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded shadow-md max-w-md w-full">
        <h2 className="text-2xl font-bold text-red-600 mb-4">Unauthorized Access</h2>
        <p className="text-gray-700 mb-4">
          {message || 'You must be logged in to view this page.'}
        </p>
        <p className="text-gray-700">
          <Link href="/auth/login" className="text-primary hover:underline">
            Log in to continue
          </Link>
        </p>
      </div>
    </div>
  );
};
