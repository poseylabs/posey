'use client';

import React, { useState, useEffect, FormEvent } from 'react';

// Use a partial type for initial data and the full type for submission
// Match the types used in the admin page
type ProviderData = {
  name: string;
  slug: string;
  api_base_url: string | null;
  api_key_secret_name: string | null;
};

type Provider = ProviderData & {
  id: string;
  created_at: string;
  updated_at: string;
};

interface ProviderFormProps {
  initialData?: Partial<Provider>; // Optional initial data for editing
  onSubmit: (data: ProviderData) => Promise<void>; // Async submit handler
  onCancel: () => void;
  isSubmitting?: boolean; // Optional flag for loading state
}

export function ProviderForm({
  initialData,
  onSubmit,
  onCancel,
  isSubmitting = false
}: ProviderFormProps) {
  const [formData, setFormData] = useState<ProviderData>({
    name: '',
    slug: '',
    api_base_url: null,
    api_key_secret_name: null,
  });

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || '',
        slug: initialData.slug || '',
        api_base_url: initialData.api_base_url !== undefined ? initialData.api_base_url : null,
        api_key_secret_name: initialData.api_key_secret_name !== undefined ? initialData.api_key_secret_name : null,
      });
    }
  }, [initialData]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      // Handle potentially null/empty values correctly
      [name]: value === '' && (name === 'api_base_url' || name === 'api_key_secret_name') ? null : value,
    }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    // Basic validation (can be expanded)
    if (!formData.name || !formData.slug) {
      alert('Provider Name and Slug are required.');
      return;
    }
    await onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="form-control">
        <label className="label">
          <span className="label-text">Provider Name</span>
        </label>
        <input
          type="text"
          name="name"
          value={formData.name}
          onChange={handleChange}
          placeholder="e.g., OpenAI, Anthropic, Ollama"
          className="input input-bordered w-full"
          required
          disabled={isSubmitting}
        />
      </div>

      <div className="form-control">
        <label className="label">
          <span className="label-text">Slug</span>
        </label>
        <input
          type="text"
          name="slug"
          value={formData.slug}
          onChange={handleChange}
          placeholder="e.g., openai, anthropic, ollama (lowercase, no spaces)"
          className="input input-bordered w-full"
          required
          pattern="^[a-z0-9_-]+$" // Basic pattern for slugs
          title="Slug must be lowercase letters, numbers, hyphens, or underscores."
          disabled={isSubmitting || !!initialData} // Disable slug editing
        />
        {initialData && <span className="text-xs text-warning mt-1">Slug cannot be changed after creation.</span>}
      </div>

      <div className="form-control">
        <label className="label">
          <span className="label-text">API Base URL (Optional)</span>
        </label>
        <input
          type="text"
          name="api_base_url"
          value={formData.api_base_url || ''} // Ensure input gets empty string for null
          onChange={handleChange}
          placeholder="e.g., https://api.openai.com/v1 (Leave blank if not needed)"
          className="input input-bordered w-full"
          disabled={isSubmitting}
        />
      </div>

      <div className="form-control">
        <label className="label">
          <span className="label-text">API Key Secret Name (Optional)</span>
        </label>
        <input
          type="text"
          name="api_key_secret_name"
          value={formData.api_key_secret_name || ''} // Ensure input gets empty string for null
          onChange={handleChange}
          placeholder="e.g., OPENAI_API_KEY (K8s secret name)"
          className="input input-bordered w-full"
          disabled={isSubmitting}
        />
      </div>

      <div className="flex justify-end space-x-3 pt-4">
        <button
          type="button"
          className="btn btn-ghost"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancel
        </button>
        <button
          type="submit"
          className={`btn btn-primary ${isSubmitting ? 'loading' : ''}`}
          disabled={isSubmitting}
        >
          {initialData ? 'Update' : 'Create'} Provider
        </button>
      </div>
    </form>
  );
} 