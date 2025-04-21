'use client';

import React, { useState, useEffect, useCallback, ChangeEvent, FormEvent } from 'react';
import { ApiHelper } from '@posey.ai/core'; // Import ApiHelper

// TODO: Define Provider type based on backend API response
type Provider = {
  id: string;
  name: string;
  slug: string;
  api_base_url: string | null;
  api_key_secret_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

// Define the shape of the form data
type ProviderFormData = {
  name: string;
  slug: string;
  api_base_url?: string;
  api_key_secret_name?: string;
};

const initialFormData: ProviderFormData = {
  name: '',
  slug: '',
  api_base_url: '',
  api_key_secret_name: '',
};

// Instantiate ApiHelper - In a real app, manage token via context/state
const api = new ApiHelper({});

export default function AdminProvidersPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false); // For form submission loading state
  const [modalError, setModalError] = useState<string | null>(null); // Error specific to the modal
  const [editingProviderId, setEditingProviderId] = useState<string | null>(null); // Track editing provider ID
  const [formData, setFormData] = useState<ProviderFormData>(initialFormData);
  const [togglingProviderId, setTogglingProviderId] = useState<string | null>(null); // State to disable checkbox during toggle

  // Function to fetch providers
  const fetchProviders = useCallback(async () => {
    // Keep isLoading for table, not necessarily full page reload
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get('/admin/llm-providers');
      // TODO: Validate data structure matches Provider type
      setProviders(data.providers || data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load providers');
      console.error(err);
      setProviders([]);
    } finally {
      setIsLoading(false);
    }
  }, []); // api instance is stable

  useEffect(() => {
    fetchProviders();
  }, [fetchProviders]);

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  const handleCreate = () => {
    setEditingProviderId(null); // Ensure we are in create mode
    setFormData(initialFormData); // Reset form for new entry
    setModalError(null); // Clear previous modal errors
    setIsModalOpen(true);
  };

  const handleEdit = (provider: Provider) => {
    setEditingProviderId(provider.id); // Set the ID of the provider being edited
    // Populate form with existing provider data
    setFormData({
      name: provider.name,
      slug: provider.slug,
      api_base_url: provider.api_base_url || '',
      api_key_secret_name: provider.api_key_secret_name || '',
    });
    setModalError(null); // Clear previous modal errors
    setIsModalOpen(true); // Open the modal
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingProviderId(null); // Clear editing state
    setFormData(initialFormData); // Reset form data
    setModalError(null);
  };

  const handleFormSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);
    setModalError(null);

    // Prepare data, ensuring optional fields are handled
    // Exclude slug from payload if editing, as it's immutable here
    const payload: Omit<ProviderFormData, 'slug'> & { slug?: string } = {
      name: formData.name,
      // Only include slug if creating
      ...(editingProviderId === null && { slug: formData.slug }),
    };
    // Only include optional fields if they have a value
    if (formData.api_base_url) payload.api_base_url = formData.api_base_url;
    if (formData.api_key_secret_name) payload.api_key_secret_name = formData.api_key_secret_name;

    try {
      if (editingProviderId) {
        // Update existing provider (PUT request)
        await api.put(`/admin/llm-providers/${editingProviderId}`, payload);
        console.log('Provider updated successfully');
        // TODO: Add success notification/toast for update
      } else {
        // Create new provider (POST request)
        await api.post('/admin/llm-providers', { ...payload, slug: formData.slug }); // Ensure slug is included for create
        console.log('Provider created successfully');
        // TODO: Add success notification/toast for create
      }
      await fetchProviders(); // Refresh the list
      handleCloseModal(); // Close modal on success
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || (err instanceof Error ? err.message : 'An unknown error occurred');
      const action = editingProviderId ? 'update' : 'create';
      setModalError(`Failed to ${action} provider: ${errorDetail}`);
      console.error(`${action} error:`, err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Function to handle toggling the active state
  const handleToggleActive = async (providerId: string, currentStatus: boolean) => {
    setTogglingProviderId(providerId); // Disable checkbox while updating
    setError(null); // Clear previous main errors
    try {
      await api.put(`/admin/llm-providers/${providerId}`, { is_active: !currentStatus });
      // Optimistic update (optional, can remove if fetchProviders is fast enough)
      // setProviders(prev => prev.map(p => p.id === providerId ? { ...p, is_active: !currentStatus } : p));
      await fetchProviders(); // Refresh the full list to ensure consistency
      console.log(`Provider ${providerId} active status toggled successfully.`);
      // TODO: Add success notification/toast
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || (err instanceof Error ? err.message : 'Failed to toggle provider status');
      setError(errorDetail); // Set main page error for toggle failures
      console.error('Toggle active error:', err);
      // TODO: Add error notification/toast
      // Revert optimistic update if needed (or just rely on fetchProviders)
    } finally {
      setTogglingProviderId(null); // Re-enable checkbox
    }
  };

  const handleDelete = async (providerId: string) => {
    if (!confirm('Are you sure you want to delete this provider?')) {
      return;
    }
    // Set local loading/error state if needed, or rely on table loading
    try {
      await api.delete(`/admin/llm-providers/${providerId}`);
      await fetchProviders(); // Refresh provider list
      console.log('Provider deleted successfully:', providerId);
      // TODO: Add success notification/toast
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || (err instanceof Error ? err.message : 'Failed to delete provider');
      setError(errorDetail); // Set main page error for delete failures
      console.error('Delete error:', err);
      // TODO: Add error notification/toast
    }
  };

  return (
    <div>
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
            {/* Table Head */}
            <thead>
              <tr>
                <th>Active</th>
                <th>Name</th>
                <th>Slug</th>
                <th>API Base URL</th>
                <th>API Key Secret</th>
                <th>Created At</th>
                <th>Updated At</th>
                <th>Actions</th>
              </tr>
            </thead>
            {/* Table Body */}
            <tbody>
              {providers.length === 0 && (
                <tr>
                  <td colSpan={8} className="text-center">No providers found.</td>
                </tr>
              )}
              {providers.map((provider) => (
                <tr key={provider.id}>
                  <td>
                    <input
                      type="checkbox"
                      className="toggle toggle-success toggle-sm"
                      checked={provider.is_active}
                      onChange={() => handleToggleActive(provider.id, provider.is_active)}
                      disabled={togglingProviderId === provider.id}
                    />
                  </td>
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

      {/* Create/Edit Provider Modal */}
      {isModalOpen && (
        <dialog id="provider_modal" className="modal modal-open">
          <div className="modal-box">
            <h3 className="font-bold text-lg mb-4">
              {editingProviderId ? 'Edit LLM Provider' : 'Create New LLM Provider'}
            </h3>

            {modalError && (
              <div className="alert alert-error shadow-lg mb-4">
                <div>
                  <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <span>{modalError}</span>
                </div>
              </div>
            )}


            <form onSubmit={handleFormSubmit}>
              <div className="form-control w-full mb-4">
                <label className="label">
                  <span className="label-text">Provider Name<span className="text-error">*</span></span>
                </label>
                <input
                  type="text"
                  placeholder="e.g., OpenAI"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="input input-bordered w-full"
                  required
                />
              </div>
              <div className="form-control w-full mb-4">
                <label className="label">
                  <span className="label-text">Provider Slug<span className="text-error">*</span></span>
                </label>
                <input
                  type="text"
                  placeholder="e.g., openai"
                  name="slug"
                  value={formData.slug}
                  onChange={handleInputChange}
                  className="input input-bordered w-full"
                  required
                  disabled={!!editingProviderId} // Disable slug editing when editing
                />
                <label className="label">
                  <span className="label-text-alt">Must be unique. Lowercase, numbers, hyphens only. Cannot be changed after creation.</span>
                </label>
              </div>
              <div className="form-control w-full mb-4">
                <label className="label">
                  <span className="label-text">API Base URL (Optional)</span>
                </label>
                <input
                  type="url"
                  placeholder="https://api.openai.com/v1"
                  name="api_base_url"
                  value={formData.api_base_url || ''}
                  onChange={handleInputChange}
                  className="input input-bordered w-full"
                />
              </div>
              <div className="form-control w-full mb-4">
                <label className="label">
                  <span className="label-text">API Key Secret Name (Optional)</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g., OPENAI_API_KEY"
                  name="api_key_secret_name"
                  value={formData.api_key_secret_name || ''}
                  onChange={handleInputChange}
                  className="input input-bordered w-full"
                />
                <label className="label">
                  <span className="label-text-alt">Name of the environment variable holding the API key.</span>
                </label>
              </div>

              <div className="modal-action">
                <button type="button" className="btn" onClick={handleCloseModal} disabled={isSubmitting}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <span className="loading loading-spinner loading-xs"></span>
                  ) : (
                    editingProviderId ? 'Update' : 'Save'
                  )}
                </button>
              </div>
            </form>
          </div>
          {/* Click outside to close */}
          <form method="dialog" className="modal-backdrop">
            <button type="button" onClick={handleCloseModal}>close</button>
          </form>
        </dialog>
      )}
    </div>
  );
} 