"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function ConfigPage() {
  const [config, setConfig] = useState({
    databaseProvider: '',
    databaseUrl: '',
    useExistingPosey: false,
  });

  const [loading, setLoading] = useState(true);
  const [success, setSuccess] = useState(false);
  const [restartRequired, setRestartRequired] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchConfig() {
      try {
        const response = await fetch('/api/config');
        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            setConfig({
              databaseProvider: data.data.databaseProvider || 'sqlite',
              databaseUrl: data.data.databaseUrl || 'file:./inventory.db',
              useExistingPosey: data.data.databaseUrl?.includes('3333') || false,
            });
          }
        }
      } catch (err) {
        console.error('Error fetching config:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchConfig();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;

    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;

      if (name === 'useExistingPosey') {
        // If checked, set the PostgreSQL configuration with port 3333
        setConfig({
          ...config,
          useExistingPosey: checked,
          databaseProvider: checked ? 'postgresql' : 'sqlite',
          databaseUrl: checked
            ? 'postgresql://postgres:postgres@localhost:3333/inventory?schema=public'
            : 'file:./inventory.db',
        });
      } else {
        setConfig({
          ...config,
          [name]: checked,
        });
      }
    } else {
      // For regular inputs
      setConfig({
        ...config,
        [name]: value,
        // If provider changes, reset the connection string to defaults
        ...(name === 'databaseProvider' && {
          databaseUrl: value === 'sqlite'
            ? 'file:./inventory.db'
            : value === 'postgresql'
              ? 'postgresql://postgres:postgres@localhost:5432/inventory?schema=public'
              : '',
          useExistingPosey: false,
        }),
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccess(false);
    setRestartRequired(false);
    setError(null);

    try {
      const response = await fetch('/api/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          databaseProvider: config.databaseProvider,
          databaseUrl: config.databaseUrl,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setSuccess(true);
        setRestartRequired(data.data?.restartRequired || false);
      } else {
        setError(data.error || 'Failed to update configuration');
      }
    } catch (err) {
      console.error('Error saving config:', err);
      setError('An unexpected error occurred');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[80vh]">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-2xl">
      <div className="flex items-center mb-6">
        <Link href="/" className="btn btn-ghost btn-sm mr-4">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back
        </Link>
        <h1 className="text-3xl font-bold">Database Configuration</h1>
      </div>

      {success && (
        <div className="alert alert-success mb-6">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <span className="font-bold">Configuration saved successfully.</span>
            {restartRequired && (
              <div className="mt-1">
                <p>You must restart the application for the changes to take effect.</p>
                <p className="mt-2">
                  <code className="bg-base-300 px-2 py-1 rounded">yarn dev</code>
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {error && (
        <div className="alert alert-error mb-6">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      <div className="card bg-base-100 shadow-md">
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="form-control mb-4">
              <label className="label">
                <span className="label-text">Use with Posey AI Platform</span>
              </label>
              <label className="cursor-pointer label justify-start gap-4">
                <input
                  type="checkbox"
                  name="useExistingPosey"
                  checked={config.useExistingPosey}
                  onChange={handleChange}
                  className="checkbox checkbox-primary"
                />
                <span className="label-text">Connect to existing Posey database (port 3333)</span>
              </label>
              <div className="text-xs text-gray-500 mt-1">
                This will use the Posey platform's PostgreSQL database running on port 3333.
              </div>
            </div>

            <div className="divider">OR Configure Manually</div>

            <div className="form-control mb-4">
              <label className="label">
                <span className="label-text">Database Provider</span>
              </label>
              <select
                name="databaseProvider"
                value={config.databaseProvider}
                onChange={handleChange}
                className="select select-bordered"
                disabled={config.useExistingPosey}
              >
                <option value="sqlite">SQLite (Default)</option>
                <option value="postgresql">PostgreSQL</option>
                <option value="mysql">MySQL</option>
                <option value="sqlserver">SQL Server</option>
                <option value="mongodb">MongoDB</option>
                <option value="cockroachdb">CockroachDB</option>
              </select>
            </div>

            <div className="form-control mb-6">
              <label className="label">
                <span className="label-text">Connection String</span>
              </label>
              <input
                type="text"
                name="databaseUrl"
                value={config.databaseUrl}
                onChange={handleChange}
                className="input input-bordered"
                placeholder="Database connection string"
                disabled={config.useExistingPosey}
              />
              <div className="text-xs text-gray-500 mt-1">
                {config.databaseProvider === 'sqlite'
                  ? 'For SQLite, use file:./your-filename.db'
                  : 'Format: protocol://username:password@host:port/database?schema=public'}
              </div>
            </div>

            <div className="card-actions justify-end">
              <Link href="/" className="btn btn-ghost">
                Cancel
              </Link>
              <button
                type="submit"
                className="btn btn-primary"
              >
                Save Configuration
              </button>
            </div>
          </form>
        </div>
      </div>

      <div className="mt-8 bg-base-200 p-4 rounded-lg">
        <h3 className="font-semibold mb-2">After changing database settings</h3>
        <p className="mb-2">
          If you change your database provider or connection string, you'll need to:
        </p>
        <ol className="list-decimal pl-5 space-y-1">
          <li>Restart the application</li>
          <li>Run database migrations with <code className="bg-base-300 px-1 py-0.5 rounded">yarn prisma:migrate</code></li>
          <li>Generate Prisma client with <code className="bg-base-300 px-1 py-0.5 rounded">yarn prisma:generate</code></li>
        </ol>
        <div className="mt-4">
          <p className="mb-2">For convenience, you can run the database setup script which will handle all these steps:</p>
          <pre className="bg-base-300 p-2 rounded"><code>yarn setup-db</code></pre>
        </div>
      </div>
    </div>
  );
} 