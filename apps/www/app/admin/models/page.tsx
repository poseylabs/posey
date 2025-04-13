'use client';

import React, { useState, useEffect } from 'react';

// TODO: Define Model type based on backend API response
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
  created_at: string;
  updated_at: string;
  provider?: { name: string }; // Include provider name if joined in API
};

export default function AdminModelsPage() {
  const [models, setModels] = useState<LLMModel[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // TODO: Add state for managing create/edit modal

  useEffect(() => {
    // TODO: Implement API call to fetch models (potentially with provider info)
    // fetch('/api/admin/llm-models')
    //   .then(res => res.json())
    //   .then(data => {
    //     setModels(data);
    //     setIsLoading(false);
    //   })
    //   .catch(err => {
    //     setError('Failed to load models');
    //     setIsLoading(false);
    //     console.error(err);
    //   });
    // Mock data for now:
    setModels([
      {
        id: 'm1', provider_id: '1', name: 'GPT-4o', model_id: 'gpt-4o',
        context_window: 128000, max_tokens: 4096, cost_per_token: 0.000005,
        is_active: true, capabilities: ['text_generation', 'tool_use'],
        created_at: '2024-05-13T10:00:00Z', updated_at: '2024-05-13T10:00:00Z', provider: { name: 'OpenAI' }
      },
      {
        id: 'm2', provider_id: '2', name: 'Claude 3 Opus', model_id: 'claude-3-opus-20240229',
        context_window: 200000, max_tokens: 4096, cost_per_token: 0.000015,
        is_active: true, capabilities: ['text_generation', 'image_understanding'],
        created_at: '2024-02-29T10:00:00Z', updated_at: '2024-02-29T10:00:00Z', provider: { name: 'Anthropic' }
      },
      {
        id: 'm3', provider_id: '3', name: 'Llama 3 8B Instruct', model_id: 'llama3:8b',
        context_window: 8192, max_tokens: null, cost_per_token: null,
        is_active: true, capabilities: ['text_generation'],
        created_at: '2024-04-18T10:00:00Z', updated_at: '2024-04-18T10:00:00Z', provider: { name: 'Ollama' }
      },
    ]);
    setIsLoading(false);
  }, []);

  const handleCreate = () => {
    // TODO: Open create modal
    console.log('Open create model modal');
  };

  const handleEdit = (model: LLMModel) => {
    // TODO: Open edit modal with model data
    console.log('Open edit model modal for:', model.name);
  };

  const handleDelete = (modelId: string) => {
    // TODO: Implement API call to delete model
    console.log('Delete model with id:', modelId);
    // TODO: Refresh model list on success
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Manage LLM Models</h1>
        <button className="btn btn-primary" onClick={handleCreate}>
          Create New Model
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
                <th>Provider</th>
                <th>Model ID</th>
                <th>Context Window</th>
                <th>Max Tokens</th>
                <th>Cost/Token</th>
                <th>Active</th>
                <th>Capabilities</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {models.map((model) => (
                <tr key={model.id} className={model.is_active ? '' : 'opacity-50'}>
                  <td>{model.name}</td>
                  <td>{model.provider?.name || 'N/A'}</td>
                  <td>{model.model_id}</td>
                  <td>{model.context_window.toLocaleString()}</td>
                  <td>{model.max_tokens?.toLocaleString() || 'N/A'}</td>
                  <td>{model.cost_per_token !== null ? `$${model.cost_per_token.toFixed(8)}` : 'N/A'}</td>
                  <td>
                    <input type="checkbox" className="checkbox checkbox-sm checkbox-success" checked={model.is_active} readOnly disabled />
                  </td>
                  <td>
                    <div className="flex flex-wrap gap-1">
                      {model.capabilities.map(cap => (
                        <div key={cap} className="badge badge-outline badge-sm">{cap}</div>
                      ))}
                    </div>
                  </td>
                  <td>
                    <button
                      className="btn btn-xs btn-outline btn-info mr-2"
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
      )}

      {/* TODO: Add Modal component for Create/Edit Model Form */}
    </div>
  );
} 