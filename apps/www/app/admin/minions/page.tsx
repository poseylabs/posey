'use client';

import React, { useState, useEffect, useCallback, useMemo, ChangeEvent, FormEvent } from 'react';
import { ApiHelper } from '@posey.ai/core'; // Import ApiHelper

// --- Types --- //

// Model type including provider info (assuming API returns this)
type LLMModelWithProvider = {
  id: string;
  name: string;
  model_id: string; // The actual model identifier (e.g., gpt-4o)
  provider_id: string;
  is_active: boolean;
  provider: {
    id: string;
    name: string;
    slug: string;
  };
};

// Type for the Minion LLM Configuration data from the API
type MinionLLMConfig = {
  id: string;
  config_key: string; // e.g., 'content_analysis', 'synthesis', 'default_research'
  llm_model_id: string;
  temperature: number | null; // Allow null
  max_tokens: number | null; // Allow null
  top_p: number | null; // Allow null
  frequency_penalty: number | null; // Allow null
  presence_penalty: number | null; // Allow null
  additional_settings: Record<string, any> | null;
  created_at: string;
  updated_at: string;
  // Include model/provider names if joined (adjust based on actual API response)
  model?: { id: string; name: string; provider?: { id: string; name: string } };
  // Add minion status information
  minion_info?: {
    is_active: boolean;
    display_name: string;
    description: string;
  };
};

// Type for the form data
type MinionConfigFormData = {
  config_key: string;
  llm_model_id: string; // Store the selected model ID
  temperature: string; // Use string for form input flexibility
  max_tokens: string;
  top_p: string;
  frequency_penalty: string;
  presence_penalty: string;
  additional_settings: string; // Use string for JSON textarea
  is_active: string; // Added for minion activation status
};

// Initial form data state
const initialFormData: MinionConfigFormData = {
  config_key: '',
  llm_model_id: '',
  temperature: '0.7', // Sensible defaults
  max_tokens: '',
  top_p: '1.0',
  frequency_penalty: '0',
  presence_penalty: '0',
  additional_settings: '{}',
  is_active: 'false',
};

// Instantiate ApiHelper
const api = new ApiHelper({});

export default function AdminMinionConfigsPage() {
  const [configs, setConfigs] = useState<MinionLLMConfig[]>([]);
  const [allModels, setAllModels] = useState<LLMModelWithProvider[]>([]); // Store all active models
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingModels, setIsLoadingModels] = useState(true); // Separate loading for models
  const [error, setError] = useState<string | null>(null);
  const [togglingMinion, setTogglingMinion] = useState<string | null>(null); // Track which minion is being toggled

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);
  const [editingConfigId, setEditingConfigId] = useState<string | null>(null);
  const [formData, setFormData] = useState<MinionConfigFormData>(initialFormData);

  // State to manage the selected provider in the form for filtering models
  const [selectedProviderIdForForm, setSelectedProviderIdForForm] = useState<string>('');

  // --- Data Fetching --- //

  const fetchMinionConfigs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Use ApiHelper to directly connect to the agents API
      const data = await api.get('/admin/minion-configs?include_minion_info=true');
      setConfigs(data.configs || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load minion configurations');
      console.error('Fetch minion configs error:', err);
      setConfigs([]); // Clear configs on error
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchModels = useCallback(async () => {
    setIsLoadingModels(true);
    // Don't clear main error here, models are for the form
    try {
      // Fetch only active models and include provider info
      const data = await api.get('/admin/llm-models?include_provider=true&is_active=true');
      setAllModels(data.models || []);
    } catch (err) {
      // Set modal error if models fail to load, as it affects the form
      setModalError('Failed to load LLM models for selection.');
      console.error('Fetch models error:', err);
      setAllModels([]);
    } finally {
      setIsLoadingModels(false);
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    fetchMinionConfigs();
    fetchModels(); // Fetch models needed for the create/edit form
  }, [fetchMinionConfigs, fetchModels]);

  // --- Derived State & Memos --- //

  // Get unique providers from the fetched models for the dropdown
  const providersForForm = useMemo(() => {
    const uniqueProviders: { id: string; name: string }[] = [];
    const providerIds = new Set<string>();
    allModels.forEach(model => {
      if (model.provider && !providerIds.has(model.provider.id)) {
        providerIds.add(model.provider.id);
        uniqueProviders.push({ id: model.provider.id, name: model.provider.name });
      }
    });
    // Sort providers alphabetically by name
    return uniqueProviders.sort((a, b) => a.name.localeCompare(b.name));
  }, [allModels]);

  // Filter models based on the selected provider in the form
  const modelsForSelectedProvider = useMemo(() => {
    if (!selectedProviderIdForForm) {
      return [];
    }
    return allModels
      .filter(model => model.provider_id === selectedProviderIdForForm && model.is_active)
      // Sort models alphabetically by name within the provider
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [allModels, selectedProviderIdForForm]);

  // --- Event Handlers --- //

  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));

    // If the provider changes, reset the selected model
    if (name === 'provider_id') {
      setSelectedProviderIdForForm(value); // Update the provider selection state
      setFormData((prevData) => ({ ...prevData, llm_model_id: '' })); // Reset model selection
    }
  };

  // Separate handler specifically for provider dropdown change
  const handleProviderChange = (e: ChangeEvent<HTMLSelectElement>) => {
    const providerId = e.target.value;
    setSelectedProviderIdForForm(providerId);
    // Reset model selection when provider changes
    setFormData(prev => ({ ...prev, llm_model_id: '' }));
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingConfigId(null);
    setFormData(initialFormData);
    setModalError(null);
    setSelectedProviderIdForForm(''); // Reset provider selection
    setIsSubmitting(false); // Ensure submitting state is reset
  };

  const handleCreate = () => {
    setEditingConfigId(null);
    setFormData(initialFormData);
    setSelectedProviderIdForForm(''); // Reset provider selection
    setModalError(null);
    setIsModalOpen(true);
  };

  const handleEdit = (config: MinionLLMConfig) => {
    setEditingConfigId(config.id);
    setModalError(null);

    // Find the full model info to get the provider ID
    const modelInfo = allModels.find(m => m.id === config.llm_model_id);
    const providerId = modelInfo?.provider_id || '';
    setSelectedProviderIdForForm(providerId);

    // Populate form data
    setFormData({
      config_key: config.config_key,
      llm_model_id: config.llm_model_id,
      // Convert numbers/nulls to strings for form fields, provide defaults
      temperature: config.temperature?.toString() ?? '0.7',
      max_tokens: config.max_tokens?.toString() ?? '',
      top_p: config.top_p?.toString() ?? '1.0',
      frequency_penalty: config.frequency_penalty?.toString() ?? '0',
      presence_penalty: config.presence_penalty?.toString() ?? '0',
      // Stringify JSON for textarea, handle null
      additional_settings: config.additional_settings ? JSON.stringify(config.additional_settings, null, 2) : '{}',
      is_active: config.minion_info?.is_active ? 'true' : 'false',
    });

    setIsModalOpen(true);
  };

  const handleDelete = async (configId: string) => {
    if (!confirm('Are you sure you want to delete this minion configuration?')) {
      return;
    }
    setError(null);
    // Optionally, add a loading state specific to the row being deleted
    try {
      await api.delete(`/admin/minion-configs/${configId}`);
      await fetchMinionConfigs(); // Refresh the list
      // TODO: Add success notification
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || (err instanceof Error ? err.message : 'Failed to delete configuration');
      setError(errorDetail);
      console.error('Delete error:', err);
      // TODO: Add error notification
    }
  };

  const handleFormSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);
    setModalError(null);

    // Validate JSON
    let parsedAdditionalSettings: Record<string, any> | null = null;
    try {
      if (formData.additional_settings.trim() && formData.additional_settings.trim() !== '{}') {
        parsedAdditionalSettings = JSON.parse(formData.additional_settings);
      }
    } catch (jsonError) {
      setModalError('Invalid JSON in Additional Settings.');
      setIsSubmitting(false);
      return;
    }

    // Prepare payload, converting form strings back to numbers/nulls
    const payload = {
      config_key: formData.config_key,
      llm_model_id: formData.llm_model_id,
      temperature: formData.temperature !== '' ? parseFloat(formData.temperature) : null,
      max_tokens: formData.max_tokens !== '' ? parseInt(formData.max_tokens, 10) : null,
      top_p: formData.top_p !== '' ? parseFloat(formData.top_p) : null,
      frequency_penalty: formData.frequency_penalty !== '' ? parseFloat(formData.frequency_penalty) : null,
      presence_penalty: formData.presence_penalty !== '' ? parseFloat(formData.presence_penalty) : null,
      additional_settings: parsedAdditionalSettings,
      is_active: formData.is_active === 'true'
    };

    // Validate required fields
    if (!payload.config_key || !payload.llm_model_id) {
      setModalError('Config Key and Model selection are required.');
      setIsSubmitting(false);
      return;
    }

    try {
      if (editingConfigId) {
        // Update existing config
        await api.put(`/admin/minion-configs/${editingConfigId}`, payload);
      } else {
        // Create new config
        await api.post('/admin/minion-configs', payload);
      }
      await fetchMinionConfigs(); // Refresh list
      handleCloseModal(); // Close modal on success
      // TODO: Add success notification
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || (err instanceof Error ? err.message : 'An unknown error occurred');
      const action = editingConfigId ? 'update' : 'create';
      setModalError(`Failed to ${action} configuration: ${errorDetail}`);
      console.error(`${action} error:`, err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Add handler for toggling minion activation
  const handleToggleMinion = async (configKey: string, isCurrentlyActive: boolean) => {
    setTogglingMinion(configKey);
    setError(null);
    try {
      // Find the config that matches this config_key
      const configToUpdate = configs.find(c => c.config_key === configKey);
      if (!configToUpdate) {
        throw new Error(`Could not find configuration with key: ${configKey}`);
      }

      // Use the new toggle-status endpoint
      await api.put(`/admin/minion-configs/${configToUpdate.id}/toggle-status`, {
        is_active: !isCurrentlyActive
      });

      // Refresh the configs after toggle
      await fetchMinionConfigs();
      console.log(`Minion ${configKey} activation status toggled successfully.`);
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || (err instanceof Error ? err.message : `Failed to toggle minion status`);
      setError(errorDetail);
      console.error(`Toggle minion status error:`, err);
    } finally {
      setTogglingMinion(null);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Manage Minion LLM Configurations</h1>
        <button className="btn btn-primary" onClick={handleCreate}>
          Create New Configuration
        </button>
      </div>

      {isLoading && <span className="loading loading-spinner text-primary"></span>}
      {error && <div className="alert alert-error shadow-lg"><div><span>Error: {error}</span></div></div>}

      {!isLoading && !error && (
        <div className="overflow-x-auto">
          <table className="table table-zebra w-full">
            <thead>
              <tr>
                <th>Active</th>
                <th>Config Key</th>
                <th>Minion</th>
                <th>Model</th>
                <th>Provider</th>
                <th>Temp</th>
                <th>Max Tokens</th>
                <th>Top P</th>
                <th>Freq Pen.</th>
                <th>Pres Pen.</th>
                <th>Additional Settings</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {configs.map((config) => (
                <tr key={config.id} className={config.minion_info?.is_active ? '' : 'opacity-60'}>
                  <td>
                    <input
                      type="checkbox"
                      className="toggle toggle-success toggle-xs"
                      checked={config.minion_info?.is_active || false}
                      onChange={() => handleToggleMinion(config.config_key, config.minion_info?.is_active || false)}
                      disabled={togglingMinion === config.config_key}
                    />
                    {togglingMinion === config.config_key && (
                      <span className="loading loading-spinner loading-xs ml-2"></span>
                    )}
                  </td>
                  <td className="font-mono">{config.config_key}</td>
                  <td>
                    {config.minion_info?.display_name || config.config_key}
                    {config.minion_info?.description && (
                      <div className="text-xs text-gray-500">{config.minion_info.description}</div>
                    )}
                  </td>
                  <td>{config.model?.name || 'N/A'}</td>
                  <td>{config.model?.provider?.name || 'N/A'}</td>
                  <td>{config.temperature !== null ? config.temperature : 'N/A'}</td>
                  <td>{config.max_tokens !== null ? config.max_tokens : 'N/A'}</td>
                  <td>{config.top_p !== null ? config.top_p : 'N/A'}</td>
                  <td>{config.frequency_penalty !== null ? config.frequency_penalty : 'N/A'}</td>
                  <td>{config.presence_penalty !== null ? config.presence_penalty : 'N/A'}</td>
                  <td>
                    {config.additional_settings ? (
                      <pre className="text-xs bg-base-200 p-1 rounded max-w-xs overflow-auto">
                        {JSON.stringify(config.additional_settings, null, 2)}
                      </pre>
                    ) : (
                      'N/A'
                    )}
                  </td>
                  <td>
                    <button
                      className="btn btn-xs btn-outline btn-info mr-2"
                      onClick={() => handleEdit(config)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn btn-xs btn-outline btn-error"
                      onClick={() => handleDelete(config.id)}
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

      {/* Modal for Create/Edit Minion Config */}
      {isModalOpen && (
        <div className="modal modal-open">
          <div className="modal-box max-w-2xl">
            <h3 className="font-bold text-lg">
              {editingConfigId ? 'Edit Minion Configuration' : 'Create Minion Configuration'}
            </h3>

            {modalError && (
              <div className="alert alert-error mt-4">
                <span>{modalError}</span>
              </div>
            )}

            <form onSubmit={handleFormSubmit} className="mt-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {/* Config Key */}
                <div className="form-control">
                  <label className="label">
                    <span className="label-text">Config Key</span>
                    <span className="label-text-alt text-error">*Required</span>
                  </label>
                  <input
                    type="text"
                    name="config_key"
                    placeholder="e.g., content_analysis, reasoning, default"
                    className="input input-bordered w-full"
                    value={formData.config_key}
                    onChange={handleInputChange}
                    required
                  />
                  <label className="label">
                    <span className="label-text-alt">Unique identifier for this minion configuration</span>
                  </label>
                </div>

                {/* LLM Provider Dropdown */}
                <div className="form-control">
                  <label className="label">
                    <span className="label-text">Provider</span>
                    <span className="label-text-alt text-error">*Required</span>
                  </label>
                  <select
                    name="provider_id"
                    className="select select-bordered w-full"
                    value={selectedProviderIdForForm}
                    onChange={handleProviderChange}
                    required
                  >
                    <option value="">Select Provider</option>
                    {providersForForm.map((provider) => (
                      <option key={provider.id} value={provider.id}>
                        {provider.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* LLM Model Dropdown (filtered by selected provider) */}
                <div className="form-control">
                  <label className="label">
                    <span className="label-text">Model</span>
                    <span className="label-text-alt text-error">*Required</span>
                  </label>
                  <select
                    name="llm_model_id"
                    className="select select-bordered w-full"
                    value={formData.llm_model_id}
                    onChange={handleInputChange}
                    required
                    disabled={!selectedProviderIdForForm}
                  >
                    <option value="">
                      {selectedProviderIdForForm
                        ? 'Select Model'
                        : 'Select a Provider first'}
                    </option>
                    {modelsForSelectedProvider.map((model) => (
                      <option key={model.id} value={model.id}>
                        {model.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Temperature */}
                <div className="form-control">
                  <label className="label">
                    <span className="label-text">Temperature</span>
                  </label>
                  <input
                    type="number"
                    name="temperature"
                    placeholder="0.7"
                    className="input input-bordered w-full"
                    value={formData.temperature}
                    onChange={handleInputChange}
                    min="0"
                    max="2"
                    step="0.01"
                  />
                  <label className="label">
                    <span className="label-text-alt">Controls randomness (0-2)</span>
                  </label>
                </div>

                {/* Max Tokens */}
                <div className="form-control">
                  <label className="label">
                    <span className="label-text">Max Tokens</span>
                  </label>
                  <input
                    type="number"
                    name="max_tokens"
                    placeholder="1000"
                    className="input input-bordered w-full"
                    value={formData.max_tokens}
                    onChange={handleInputChange}
                    min="1"
                  />
                  <label className="label">
                    <span className="label-text-alt">Leave empty for model default</span>
                  </label>
                </div>

                {/* Top P */}
                <div className="form-control">
                  <label className="label">
                    <span className="label-text">Top P</span>
                  </label>
                  <input
                    type="number"
                    name="top_p"
                    placeholder="1.0"
                    className="input input-bordered w-full"
                    value={formData.top_p}
                    onChange={handleInputChange}
                    min="0"
                    max="1"
                    step="0.01"
                  />
                </div>

                {/* Frequency Penalty */}
                <div className="form-control">
                  <label className="label">
                    <span className="label-text">Frequency Penalty</span>
                  </label>
                  <input
                    type="number"
                    name="frequency_penalty"
                    placeholder="0"
                    className="input input-bordered w-full"
                    value={formData.frequency_penalty}
                    onChange={handleInputChange}
                    min="-2"
                    max="2"
                    step="0.01"
                  />
                </div>

                {/* Presence Penalty */}
                <div className="form-control">
                  <label className="label">
                    <span className="label-text">Presence Penalty</span>
                  </label>
                  <input
                    type="number"
                    name="presence_penalty"
                    placeholder="0"
                    className="input input-bordered w-full"
                    value={formData.presence_penalty}
                    onChange={handleInputChange}
                    min="-2"
                    max="2"
                    step="0.01"
                  />
                </div>

                {/* Minion Activation */}
                <div className="form-control">
                  <label className="label">
                    <span className="label-text">Activate Minion</span>
                  </label>
                  <div className="flex items-center space-x-4 h-12 px-4 border rounded-lg">
                    <label className="cursor-pointer flex items-center">
                      <input
                        type="radio"
                        name="is_active"
                        value="true"
                        className="radio radio-sm mr-2"
                        checked={formData.is_active === 'true'}
                        onChange={handleInputChange}
                      />
                      <span>Active</span>
                    </label>
                    <label className="cursor-pointer flex items-center">
                      <input
                        type="radio"
                        name="is_active"
                        value="false"
                        className="radio radio-sm mr-2"
                        checked={formData.is_active === 'false'}
                        onChange={handleInputChange}
                      />
                      <span>Inactive</span>
                    </label>
                  </div>
                  <label className="label">
                    <span className="label-text-alt">Enable or disable this minion</span>
                  </label>
                </div>
              </div>

              {/* Additional Settings (JSON) */}
              <div className="form-control mt-4">
                <label className="label">
                  <span className="label-text">Additional Settings (JSON)</span>
                </label>
                <textarea
                  name="additional_settings"
                  className="textarea textarea-bordered h-32 font-mono"
                  placeholder="{}"
                  value={formData.additional_settings}
                  onChange={handleInputChange}
                />
                <label className="label">
                  <span className="label-text-alt">Model-specific settings in JSON format</span>
                </label>
              </div>

              <div className="modal-action mt-6">
                <button
                  type="button"
                  className="btn"
                  onClick={handleCloseModal}
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className={`btn btn-primary ${isSubmitting ? 'loading' : ''}`}
                  disabled={isSubmitting || isLoadingModels}
                >
                  {editingConfigId ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
          <div className="modal-backdrop" onClick={handleCloseModal}></div>
        </div>
      )}
    </div>
  );
} 