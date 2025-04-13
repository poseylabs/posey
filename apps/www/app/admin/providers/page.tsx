'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { ApiHelper } from '@posey.ai/core'; // Import ApiHelper

// TODO: Define Provider type based on backend API response
type Provider = {
  id: string;
  name: string;
  slug: string;
  api_base_url: string | null;
  api_key_secret_name: string | null;
  created_at: string;
  updated_at: string;
};

// Instantiate ApiHelper - In a real app, manage token via context/state
const api = new ApiHelper({});

export default function AdminProvidersPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // TODO: Add state for managing create/edit modal

  // Function to fetch providers
  const fetchProviders = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get('/admin/llm-providers'); // Use ApiHelper
      // TODO: Validate data structure matches Provider type
      setProviders(data.providers || data || []); // Adjust based on actual API response structure
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load providers');
      console.error(err);
      setProviders([]); // Clear data on error
    } finally {
      setIsLoading(false);
    }
  }, []); // No dependencies needed if api instance is stable

  useEffect(() => {
    fetchProviders(); // Call the fetch function
  }, [fetchProviders]); // Re-run if fetchProviders changes (it shouldn't in this case)

  const handleCreate = () => {
    // TODO: Open create modal
    console.log('Open create provider modal');
  };

  const handleEdit = (provider: Provider) => {
    // TODO: Open edit modal with provider data
    console.log('Open edit provider modal for:', provider.name);
  };

  const handleDelete = async (providerId: string) => {
    if (!confirm('Are you sure you want to delete this provider?')) {
      return;
    }
    try {
      await api.delete(`/admin/llm-providers/${providerId}`);
      // Refresh provider list on success
      await fetchProviders();
      // TODO: Add success notification/toast
      console.log('Provider deleted successfully:', providerId);
    } catch (err) {
      // TODO: Add error notification/toast
      const errorMsg = err instanceof Error ? err.message : 'Failed to delete provider';
      setError(errorMsg);
      console.error('Delete error:', err);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Manage LLM Providers</h1>
        <button className="btn btn-primary" onClick={handleCreate}>
          Create New Provider
        </button>
      </div>

      {isLoading && <span className="loading loading-spinner text-primary"></span>}
      {error && <div className="alert alert-error shadow-lg"><div><span>Error: {error}</span></div></div>}

      {!isLoading && !error && (
        <div className="overflow-x-auto">
          <table className="table table-zebra w-full">
            <thead>
              <tr>
                <th>Name</th>
                <th>Slug</th>
                <th>API Base URL</th>
                <th>API Key Secret</th>
                <th>Created At</th>
                <th>Updated At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {providers.map((provider) => (
                <tr key={provider.id}>
                  <td>{provider.name}</td>
                  <td>{provider.slug}</td>
                  <td>{provider.api_base_url || 'N/A'}</td>
                  <td>{provider.api_key_secret_name || 'N/A'}</td>
                  <td>{new Date(provider.created_at).toLocaleString()}</td>
                  <td>{new Date(provider.updated_at).toLocaleString()}</td>
                  <td>
                    <button
                      className="btn btn-xs btn-outline btn-info mr-2"
                      onClick={() => handleEdit(provider)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn btn-xs btn-outline btn-error"
                      onClick={() => handleDelete(provider.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* TODO: Add Modal component for Create/Edit Provider Form */}
    </div>
  );
} 