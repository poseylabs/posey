'use client';

import React, { useState, useEffect } from 'react';

// TODO: Define MinionConfig type based on backend API response
type MinionLLMConfig = {
  id: string;
  config_key: string; // e.g., 'content_analysis', 'synthesis', 'default_research'
  llm_model_id: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  frequency_penalty: number;
  presence_penalty: number;
  additional_settings: Record<string, any> | null;
  created_at: string;
  updated_at: string;
  model?: { name: string; provider?: { name: string } }; // Include model/provider names if joined
};

export default function AdminMinionConfigsPage() {
  const [configs, setConfigs] = useState<MinionLLMConfig[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // TODO: Add state for managing create/edit modal

  useEffect(() => {
    // TODO: Implement API call to fetch minion configs (potentially with model/provider info)
    // fetch('/api/admin/minion-configs')
    //   .then(res => res.json())
    //   .then(data => {
    //     setConfigs(data);
    //     setIsLoading(false);
    //   })
    //   .catch(err => {
    //     setError('Failed to load minion configurations');
    //     setIsLoading(false);
    //     console.error(err);
    //   });
    // Mock data for now:
    setConfigs([
      {
        id: 'mc1', config_key: 'content_analysis', llm_model_id: 'm1',
        temperature: 0.5, max_tokens: 500, top_p: 0.9, frequency_penalty: 0, presence_penalty: 0,
        additional_settings: null, created_at: '2024-05-14T10:00:00Z', updated_at: '2024-05-14T10:00:00Z',
        model: { name: 'GPT-4o', provider: { name: 'OpenAI' } }
      },
      {
        id: 'mc2', config_key: 'synthesis', llm_model_id: 'm2',
        temperature: 0.7, max_tokens: 1500, top_p: 0.95, frequency_penalty: 0.1, presence_penalty: 0.1,
        additional_settings: { "stop_sequences": ["\nHuman:"] }, created_at: '2024-05-14T11:00:00Z', updated_at: '2024-05-14T11:00:00Z',
        model: { name: 'Claude 3 Opus', provider: { name: 'Anthropic' } }
      },
      {
        id: 'mc3', config_key: 'default', llm_model_id: 'm3',
        temperature: 0.8, max_tokens: 1000, top_p: 1.0, frequency_penalty: 0, presence_penalty: 0,
        additional_settings: null, created_at: '2024-05-14T12:00:00Z', updated_at: '2024-05-14T12:00:00Z',
        model: { name: 'Llama 3 8B Instruct', provider: { name: 'Ollama' } }
      },
    ]);
    setIsLoading(false);
  }, []);

  const handleCreate = () => {
    // TODO: Open create modal
    console.log('Open create minion config modal');
  };

  const handleEdit = (config: MinionLLMConfig) => {
    // TODO: Open edit modal with config data
    console.log('Open edit minion config modal for:', config.config_key);
  };

  const handleDelete = (configId: string) => {
    // TODO: Implement API call to delete config
    console.log('Delete minion config with id:', configId);
    // TODO: Refresh config list on success
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
                <th>Config Key</th>
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
                <tr key={config.id}>
                  <td className="font-mono">{config.config_key}</td>
                  <td>{config.model?.name || 'N/A'}</td>
                  <td>{config.model?.provider?.name || 'N/A'}</td>
                  <td>{config.temperature}</td>
                  <td>{config.max_tokens}</td>
                  <td>{config.top_p}</td>
                  <td>{config.frequency_penalty}</td>
                  <td>{config.presence_penalty}</td>
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

      {/* TODO: Add Modal component for Create/Edit Minion Config Form */}
    </div>
  );
} 