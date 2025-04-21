'use client';

import React, { useState, useEffect, useCallback, ChangeEvent, FormEvent, useMemo } from 'react';
import { ApiHelper } from '@posey.ai/core';

// --- Types --- //
type LLMProvider = {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  // Add other fields if needed from your actual Provider type
};

// Define sortable columns explicitly for type safety
type SortableColumn = 'is_active' | 'supports_thinking' | 'supports_tool_use' | 'supports_computer_use' | 'name' | 'model_id' | 'context_window' | 'max_tokens' | 'cost_per_token';

type LLMModel = {
  id: string;
  provider_id: string;
  name: string;
  model_id: string; // e.g., gpt-4o, claude-3-opus-20240229
  context_window: number;
  max_tokens: number | null;
  cost_per_token: number | null;
  is_active: boolean;
  capabilities: string[];
  supports_embeddings: boolean; // Assuming this exists from schema
  embedding_dimensions: number | null; // Assuming this exists from schema
  supports_thinking: boolean; // Added
  supports_tool_use: boolean; // Added
  supports_computer_use: boolean; // Added
  created_at: string;
  updated_at: string;
  provider?: { id: string; name: string }; // Updated to match API response
};

// Instantiate ApiHelper
const api = new ApiHelper({});

// --- Component --- //
export default function AdminModelsPage() {
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(null);
  const [models, setModels] = useState<LLMModel[]>([]);
  const [isLoadingProviders, setIsLoadingProviders] = useState(true);
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [togglingField, setTogglingField] = useState<{ modelId: string; field: keyof LLMModel } | null>(null);
  const [isSyncing, setIsSyncing] = useState(false); // Add state for sync loading
  const [syncResultMessage, setSyncResultMessage] = useState<string | null>(null); // State for sync result message
  const [syncResultStatus, setSyncResultStatus] = useState<'success' | 'error' | 'skipped' | null>(null);
  // Add state for edit modal
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingModelId, setEditingModelId] = useState<string | null>(null);
  const [editFormData, setEditFormData] = useState<Partial<LLMModel>>({}); // Use partial type for flexibility
  const [isEditSubmitting, setIsEditSubmitting] = useState(false);
  const [editModalError, setEditModalError] = useState<string | null>(null);

  // State for sorting
  const [sortColumn, setSortColumn] = useState<SortableColumn | null>('is_active'); // Default to sorting by 'is_active'
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');      // Default to ascending (true first)

  // --- Data Fetching --- //
  const fetchProviders = useCallback(async () => {
    setIsLoadingProviders(true);
    setError(null);
    try {
      // Fetch ALL providers initially
      const data = await api.get('/admin/llm-providers');
      const allProviders = data.providers || data || [];
      // Filter for active providers on the client-side
      const activeProviders = allProviders.filter((p: LLMProvider) => p.is_active);
      setProviders(activeProviders);
      // Select the first active provider by default if available
      if (activeProviders.length > 0 && !selectedProviderId) {
        setSelectedProviderId(activeProviders[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load providers');
      console.error('Provider fetch error:', err);
      setProviders([]);
    } finally {
      setIsLoadingProviders(false);
    }
  }, [selectedProviderId]);

  const fetchModelsForProvider = useCallback(async (providerId: string) => {
    if (!providerId) return;
    setIsLoadingModels(true);
    setError(null);
    setModels([]); // Clear previous models
    try {
      // Fetch models specifically for the selected provider
      const data = await api.get(`/admin/llm-models?provider_id=${providerId}`);
      setModels(data.models || data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to load models for provider ${providerId}`);
      console.error('Model fetch error:', err);
      setModels([]);
    } finally {
      setIsLoadingModels(false);
    }
  }, []);

  // Fetch providers on initial mount
  useEffect(() => {
    fetchProviders();
  }, [fetchProviders]);

  // Fetch models when selectedProviderId changes
  useEffect(() => {
    if (selectedProviderId) {
      fetchModelsForProvider(selectedProviderId);
    }
  }, [selectedProviderId, fetchModelsForProvider]);

  // --- Sorting Logic --- //
  const sortedModels = useMemo(() => {
    if (!sortColumn) return models; // No sorting applied

    return [...models].sort((a, b) => {
      const aValue = a[sortColumn];
      const bValue = b[sortColumn];

      // Handle null/undefined values (treat nulls as smaller)
      if (aValue === null || aValue === undefined) return sortDirection === 'asc' ? -1 : 1;
      if (bValue === null || bValue === undefined) return sortDirection === 'asc' ? 1 : -1;

      let comparison = 0;
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        comparison = aValue.localeCompare(bValue);
      } else if (typeof aValue === 'number' && typeof bValue === 'number') {
        comparison = aValue - bValue;
      } else if (typeof aValue === 'boolean' && typeof bValue === 'boolean') {
        comparison = aValue === bValue ? 0 : aValue ? -1 : 1; // True comes first when ascending
      }
      // Add more type checks if needed

      return sortDirection === 'asc' ? comparison : comparison * -1;
    });
  }, [models, sortColumn, sortDirection]);

  // --- Event Handlers --- //

  const handleProviderSelect = (providerId: string) => {
    setSelectedProviderId(providerId);
    // Model fetching is handled by the useEffect watching selectedProviderId
  };

  // Generic handler for toggling boolean fields
  const handleToggleField = async (modelId: string, fieldName: keyof LLMModel, currentStatus: boolean) => {
    setTogglingField({ modelId, field: fieldName });
    setError(null);
    setSyncResultMessage(null); // Clear sync message too
    try {
      const payload = { [fieldName]: !currentStatus };
      await api.put(`/admin/llm-models/${modelId}`, payload);
      // Refresh models list on success
      if (selectedProviderId) {
        await fetchModelsForProvider(selectedProviderId);
      }
      console.log(`Model ${modelId} field ${fieldName} toggled successfully.`);
      // TODO: Add success notification/toast
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || (err instanceof Error ? err.message : `Failed to toggle model field ${fieldName}`);
      setError(errorDetail);
      console.error(`Toggle ${fieldName} error:`, err);
      // TODO: Add error notification/toast
    } finally {
      setTogglingField(null);
    }
  };

  const handleCreate = () => {
    // TODO: Open create modal, likely needs selectedProviderId
    console.log('Open create model modal for provider:', selectedProviderId);
  };

  const handleEdit = (model: LLMModel) => {
    setEditingModelId(model.id);
    setEditFormData({
      name: model.name || '',
      context_window: model.context_window ?? 0,
      max_tokens: model.max_tokens ?? undefined,
      cost_per_token: model.cost_per_token ?? undefined,
      capabilities: model.capabilities || [],
    });
    setEditModalError(null);
    setIsEditModalOpen(true);
  };

  const handleCloseEditModal = () => {
    setIsEditModalOpen(false);
    setEditingModelId(null);
    setEditFormData({});
    setEditModalError(null);
    setIsEditSubmitting(false);
  };

  const handleEditInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;

    setEditFormData((prevData) => ({
      ...prevData,
      [name]: type === 'number'
        ? (value === '' ? undefined : Number(value))
        : name === 'capabilities'
          ? value.split(',').map(s => s.trim()).filter(s => s)
          : value,
    }));
  };

  const handleEditFormSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editingModelId) return;

    setIsEditSubmitting(true);
    setEditModalError(null);

    const payload: any = {
      name: editFormData.name,
      context_window: editFormData.context_window ?? 0,
      max_tokens: editFormData.max_tokens === undefined ? null : editFormData.max_tokens,
      cost_per_token: editFormData.cost_per_token === undefined ? null : editFormData.cost_per_token,
      capabilities: editFormData.capabilities || [],
    };

    try {
      await api.put(`/admin/llm-models/${editingModelId}`, payload);
      console.log('Model updated successfully');
      if (selectedProviderId) {
        await fetchModelsForProvider(selectedProviderId);
      }
      handleCloseEditModal();
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || (err instanceof Error ? err.message : 'An unknown error occurred');
      setEditModalError(`Failed to update model: ${errorDetail}`);
      console.error('Update model error:', err);
    } finally {
      setIsEditSubmitting(false);
    }
  };

  const handleDelete = async (modelId: string) => {
    if (!confirm('Are you sure you want to delete this model? This might affect existing configurations.')) {
      return;
    }
    setError(null); // Clear general errors
    setSyncResultMessage(null); // Clear sync messages
    try {
      await api.delete(`/admin/llm-models/${modelId}`);
      // Re-fetch models for the current provider
      if (selectedProviderId) {
        await fetchModelsForProvider(selectedProviderId);
      }
      console.log('Model deleted successfully:', modelId);
      // TODO: Add success notification/toast
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || (err instanceof Error ? err.message : 'Failed to delete model');
      setError(errorDetail);
      console.error('Delete model error:', err);
      // TODO: Add error notification/toast
    }
  };

  const handleSyncModels = async () => {
    if (!selectedProviderId) return;
    setIsSyncing(true);
    setError(null); // Clear previous errors
    setSyncResultMessage(null); // Clear previous sync messages
    console.log('Trigger sync for provider:', selectedProviderId);

    try {
      const result = await api.post(`/admin/llm-models/sync?provider_id=${selectedProviderId}`, {});
      setSyncResultStatus(result.status);
      setSyncResultMessage(result.message || `${result.new_models_added} new models added.`);
      // Refresh the models list if sync was successful or skipped (might have found existing)
      if (result.status === 'success' || result.status === 'skipped') {
        await fetchModelsForProvider(selectedProviderId);
      }
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail || (err instanceof Error ? err.message : 'Failed to sync models');
      setError(errorDetail); // Use general error state for sync failure
      setSyncResultStatus('error');
      setSyncResultMessage(null); // Clear specific message on generic error
      console.error('Sync error:', err);
    } finally {
      setIsSyncing(false);
    }
  }

  // --- Sorting Handler --- //
  const handleSort = (column: SortableColumn) => {
    if (sortColumn === column) {
      // Toggle direction if same column clicked
      setSortDirection(prevDirection => prevDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // Sort by new column, default to ascending
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  // --- Rendering --- //

  // Determine active tab styles
  const getTabClassName = (providerId: string) => {
    const baseClasses = "tab tab-lifted mr-1"; // Added mr-1 for spacing between tabs
    return selectedProviderId === providerId
      ? `${baseClasses} tab-active font-semibold`
      : baseClasses;
  };

  // Helper to check if a specific toggle is loading
  const isToggling = (modelId: string, field: keyof LLMModel) => {
    return togglingField?.modelId === modelId && togglingField?.field === field;
  }

  // Helper to get sort indicator
  const getSortIndicator = (column: SortableColumn) => {
    if (sortColumn !== column) return null;
    return sortDirection === 'asc' ? ' ▲' : ' ▼';
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Manage LLM Models</h1>
        <div>
          {/* Add Sync Button - only show if a provider is selected */}
          {selectedProviderId && (
            <button
              className="btn btn-secondary mr-4"
              onClick={handleSyncModels}
              disabled={isSyncing} // Disable while syncing
            >
              {isSyncing ? (
                <><span className="loading loading-spinner loading-xs"></span> Syncing...</>
              ) : (
                'Sync Models'
              )}
            </button>
          )}
          <button className="btn btn-primary" onClick={handleCreate} disabled={!selectedProviderId || isSyncing}>
            Create New Model
          </button>
        </div>
      </div>

      {/* Provider Tabs */}
      {isLoadingProviders ? (
        <span className="loading loading-spinner text-primary mb-4"></span>
      ) : providers.length > 0 ? (
        <div role="tablist" className="tabs tabs-lifted mb-6">
          {providers.map((provider) => (
            <a
              key={provider.id}
              role="tab"
              className={getTabClassName(provider.id)}
              onClick={() => handleProviderSelect(provider.id)}
            >
              {provider.name}
            </a>
          ))}
          {/* Add a filler tab to extend the bottom border */}
          <a role="tab" className="tab tab-lifted flex-grow"></a>
        </div>
      ) : (
        <div className="alert alert-info shadow-lg mb-4"><div><span>No active providers found. Create or activate providers first.</span></div></div>
      )}

      {/* Error Display */}
      {error && <div className="alert alert-error shadow-lg mb-4"><div><span>Error: {error}</span></div></div>}
      {/* Sync Result Message Display - Made success less prominent */}
      {syncResultMessage && (
        <div className={`alert shadow-lg mb-4 ${syncResultStatus === 'success' ? 'alert-success' : syncResultStatus === 'error' ? 'alert-error' : 'alert-info'}`}>
          <div className="flex items-center"> {/* Use flex for alignment */}
            {/* Only show icons for error and skipped */}
            {syncResultStatus === 'error' && <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
            {syncResultStatus === 'skipped' && <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6 mr-2"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>}
            <span>{syncResultMessage}</span>
          </div>
        </div>
      )}

      {/* Models Table */}
      {selectedProviderId && (
        isLoadingModels ? (
          <div className="flex justify-center"><span className="loading loading-spinner text-primary"></span></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table table-zebra table-sm w-full">
              <thead>
                <tr>
                  <th className="w-12">
                    <button className="btn btn-ghost btn-xs" onClick={() => handleSort('is_active')}>
                      Active{getSortIndicator('is_active')}
                    </button>
                  </th>
                  <th className="w-12">
                    <button className="btn btn-ghost btn-xs" onClick={() => handleSort('supports_thinking')}>
                      Thinking{getSortIndicator('supports_thinking')}
                    </button>
                  </th>
                  <th className="w-12">
                    <button className="btn btn-ghost btn-xs" onClick={() => handleSort('supports_tool_use')}>
                      Tool Use{getSortIndicator('supports_tool_use')}
                    </button>
                  </th>
                  <th className="w-12">
                    <button className="btn btn-ghost btn-xs" onClick={() => handleSort('supports_computer_use')}>
                      Comp. Use{getSortIndicator('supports_computer_use')}
                    </button>
                  </th>
                  <th>
                    <button className="btn btn-ghost btn-xs" onClick={() => handleSort('name')}>
                      Name{getSortIndicator('name')}
                    </button>
                  </th>
                  <th>
                    <button className="btn btn-ghost btn-xs" onClick={() => handleSort('model_id')}>
                      Model ID{getSortIndicator('model_id')}
                    </button>
                  </th>
                  <th>
                    <button className="btn btn-ghost btn-xs" onClick={() => handleSort('context_window')}>
                      Context{getSortIndicator('context_window')}
                    </button>
                  </th>
                  <th>
                    <button className="btn btn-ghost btn-xs" onClick={() => handleSort('max_tokens')}>
                      Max Tok{getSortIndicator('max_tokens')}
                    </button>
                  </th>
                  <th>
                    <button className="btn btn-ghost btn-xs" onClick={() => handleSort('cost_per_token')}>
                      Cost/Tok{getSortIndicator('cost_per_token')}
                    </button>
                  </th>
                  <th>Capabilities</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedModels.length === 0 && !isLoadingModels && (
                  <tr>
                    <td colSpan={11} className="text-center">No models found for this provider. Try syncing models.</td>
                  </tr>
                )}
                {sortedModels.map((model) => (
                  <tr key={model.id} className={model.is_active ? '' : 'opacity-60'}>
                    <td>
                      <input
                        type="checkbox"
                        className="toggle toggle-success toggle-xs"
                        checked={model.is_active}
                        onChange={() => handleToggleField(model.id, 'is_active', model.is_active)}
                        disabled={isToggling(model.id, 'is_active')}
                      />
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        className="toggle toggle-info toggle-xs"
                        checked={model.supports_thinking}
                        onChange={() => handleToggleField(model.id, 'supports_thinking', model.supports_thinking)}
                        disabled={isToggling(model.id, 'supports_thinking')}
                      />
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        className="toggle toggle-info toggle-xs"
                        checked={model.supports_tool_use}
                        onChange={() => handleToggleField(model.id, 'supports_tool_use', model.supports_tool_use)}
                        disabled={isToggling(model.id, 'supports_tool_use')}
                      />
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        className="toggle toggle-info toggle-xs"
                        checked={model.supports_computer_use}
                        onChange={() => handleToggleField(model.id, 'supports_computer_use', model.supports_computer_use)}
                        disabled={isToggling(model.id, 'supports_computer_use')}
                      />
                    </td>
                    <td>{model.name}</td>
                    <td className="font-mono text-xs">{model.model_id}</td>
                    <td>{model.context_window.toLocaleString()}</td>
                    <td>{model.max_tokens?.toLocaleString() || 'N/A'}</td>
                    <td>{model.cost_per_token !== null ? `$${model.cost_per_token.toFixed(8)}` : 'N/A'}</td>
                    <td>
                      <div className="flex flex-wrap gap-1">
                        {model.capabilities.map(cap => (
                          <div key={cap} className="badge badge-outline badge-xs">{cap.replace('_', ' ')}</div>
                        ))}
                      </div>
                    </td>
                    <td>
                      <button
                        className="btn btn-xs btn-outline btn-info mr-1"
                        onClick={() => handleEdit(model)}
                      >
                        Edit
                      </button>
                      <button
                        className="btn btn-xs btn-outline btn-error"
                        onClick={() => handleDelete(model.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}

      {/* Edit Modal */}
      {isEditModalOpen && editingModelId && (
        <dialog id="edit_model_modal" className="modal modal-open">
          <div className="modal-box w-11/12 max-w-2xl">
            <h3 className="font-bold text-lg mb-4">Edit LLM Model ({editFormData.name || '...'})</h3>

            {editModalError && (
              <div className="alert alert-error shadow-lg mb-4">
                <div>
                  <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <span>{editModalError}</span>
                </div>
              </div>
            )}

            <form onSubmit={handleEditFormSubmit}>
              {/* Model Name */}
              <div className="form-control w-full mb-4">
                <label className="label">
                  <span className="label-text">Model Name<span className="text-error">*</span></span>
                </label>
                <input
                  type="text"
                  placeholder="e.g., Claude 3.7 Sonnet"
                  name="name"
                  value={editFormData.name || ''}
                  onChange={handleEditInputChange}
                  className="input input-bordered w-full"
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                {/* Context Window */}
                <div className="form-control">
                  <label className="label"><span className="label-text">Context Window<span className="text-error">*</span></span></label>
                  <input
                    type="number"
                    placeholder="e.g., 200000"
                    name="context_window"
                    value={editFormData.context_window ?? ''}
                    onChange={handleEditInputChange}
                    className="input input-bordered w-full"
                    min="0"
                    required
                  />
                </div>
                {/* Max Tokens */}
                <div className="form-control">
                  <label className="label"><span className="label-text">Max Tokens (Optional)</span></label>
                  <input
                    type="number"
                    placeholder="e.g., 4096"
                    name="max_tokens"
                    value={editFormData.max_tokens ?? ''}
                    onChange={handleEditInputChange}
                    className="input input-bordered w-full"
                    min="0"
                  />
                </div>
                {/* Cost Per Token */}
                <div className="form-control">
                  <label className="label"><span className="label-text">Cost/Token (Optional)</span></label>
                  <input
                    type="number"
                    placeholder="e.g., 0.000015"
                    name="cost_per_token"
                    value={editFormData.cost_per_token ?? ''}
                    onChange={handleEditInputChange}
                    className="input input-bordered w-full"
                    min="0"
                    step="0.00000001"
                  />
                </div>
              </div>

              {/* Capabilities */}
              <div className="form-control w-full mb-4">
                <label className="label">
                  <span className="label-text">Capabilities (comma-separated)</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g., text_generation, tool_use, vision"
                  name="capabilities"
                  value={(editFormData.capabilities || []).join(', ')}
                  onChange={handleEditInputChange}
                  className="input input-bordered w-full"
                />
                <label className="label">
                  <span className="label-text-alt">Enter capabilities like text_generation, tool_use etc. separated by commas.</span>
                </label>
              </div>

              <div className="modal-action">
                <button type="button" className="btn" onClick={handleCloseEditModal} disabled={isEditSubmitting}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={isEditSubmitting}>
                  {isEditSubmitting ? <span className="loading loading-spinner loading-xs"></span> : 'Update Model'}
                </button>
              </div>
            </form>
          </div>
          <form method="dialog" className="modal-backdrop">
            <button type="button" onClick={handleCloseEditModal}>close</button>
          </form>
        </dialog>
      )}
    </div>
  );
} 