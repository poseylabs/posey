import { useState, FormEvent } from 'react';
import { Input } from '../form';
import { Button } from '../form/button';

/**
 * Props for the AuthForm component.
 */
export interface AuthFormProps {
  /**
   * Callback invoked when the form is submitted.
   */
  onSubmit: (formData: {
    email: string;
    password: string;
    username?: string;
    inviteCode?: string;
  }) => Promise<void>;
  /**
   * Determines whether the component is in 'login' or 'register' mode.
   */
  mode?: 'login' | 'register';
}

/**
 * AuthForm is a shared component to be used across web, React Native, and Electron apps.
 * It provides a basic authentication form with email and password fields.
 *
 * @example
 * <AuthForm
 *   onSubmit={async (formData) => {
 *     // Execute your login logic here.
 *   }}
 *   mode="login"
 * />
 */
export function AuthForm({ onSubmit, mode = 'login' }: AuthFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_AUTH_API_URL || 'http://localhost:9999';

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === 'register') {
        await onSubmit({ email, password, username, inviteCode });
      } else {
        await onSubmit({ email, password });
      }

      // After successful auth, force a session check
      // window.location.href = '/'; // Use hard redirect to ensure clean session state
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  const handleOAuthLogin = async (provider: string) => {
    try {
      const response = await fetch(`${API_URL}/auth/authorize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider,
          client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID,
          redirect_uri: window.location.origin + '/auth/callback'
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to initialize OAuth flow');
      }

      const { url } = await response.json();
      window.location.href = url;
    } catch (err: any) {
      setError(err.message || 'OAuth login failed');
    }
  };

  const validatePassword = async (password: string) => {
    if (password.length < 5) {
      return "Password must be at least 5 characters long";
    }

    // Require at least 2 numbers
    if ((password.match(/\d/g) || []).length < 2) {
      return "Password must contain at least 2 numbers";
    }

    // Require special characters
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      return "Password must contain at least one special character";
    }

    // No validation error
    return undefined;
  };

  return (
    <div className="grid items-center">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full p-10" suppressHydrationWarning>
        {mode === 'register' && (
          <Input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            label="Username"
            required
          />
        )}
        <Input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          label="Email"
          required
        />
        <Input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          label="Password"
          required
          validate={validatePassword}
        />
        {mode === 'register' && (
          <Input
            type="text"
            placeholder="Invite Code"
            value={inviteCode}
            onChange={(e) => setInviteCode(e.target.value)}
            label="Invite Code"
            required
          />
        )}
        {error && <p className="text-error text-sm">{error}</p>}
        <Button type="submit" disabled={loading}>
          {loading ? 'Loading...' : mode === 'login' ? 'Login' : 'Sign Up'}
        </Button>

        <div className="divider">OR</div>

        <Button
          type="button"
          onClick={() => handleOAuthLogin('google')}
          variant="outline"
        >
          Continue with Google
        </Button>
      </form>
    </div>
  );
} 
