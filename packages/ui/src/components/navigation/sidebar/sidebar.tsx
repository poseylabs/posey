'use client';
import { config, UserPreferences, getUpdatedLLMAdapters } from '@posey.ai/core';
import { PoseyState, usePoseyState } from '@posey.ai/state';
import { useEffect, useState, useCallback } from 'react';
import { usePoseyRouter } from '../../../hooks/router';
import { VoiceSelector } from '../../preferences/voice-selector';
import './sidebar.css'
import { isEqual } from 'lodash';

const { ui } = config;

const { themes } = ui
const AGENT_API = process.env.NEXT_PUBLIC_AGENT_API_ENDPOINT || 'http://localhost:5555';
const API_ENDPOINT = process.env.NEXT_PUBLIC_API_ENDPOINT || 'http://localhost:8888/api';

const liClass = "menu-item mb-2";
const sectionClass = "flex flex-col pb-2";

const style = {
  h3: "font-bold ",
  label: "text-sm font-bold mb-2 block mt-4",
}

export default function Sidebar({
  useHashLinks = false
}: {
  useHashLinks?: boolean;
}) {

  const { linkTo } = usePoseyRouter({ useHashLinks });

  const store = usePoseyState();

  const {
    user,
    setUser,
    setUserPreferences,
    conversations,
    status,
    debouncedUpdateProfile,
    currentConversation,
  } = store.select((state: PoseyState) => ({
    currentConversation: state.chat.currentConversation,
    user: state.user,
    setUser: state.setUser,
    setUserPreferences: state.setUserPreferences,
    conversations: state.chat.conversations,
    status: state.status,
    debouncedUpdateProfile: state.debouncedUpdateProfile,
  }));

  // Destructure for cleaner access
  const preferences = user?.metadata?.preferences;
  const profile = user?.metadata?.profile;

  const [sidebarClass, setSidebarClass] = useState('sidebar');
  const [speechAbility, setSpeechAbility] = useState<any>(null);
  const [currentConversationId, setCurrentConversationId] = useState<string>('');

  useEffect(() => {
    setSidebarClass(status.isSidebarOpen ? 'sidebar sidebar-open' : 'sidebar sidebar-closed');
  }, [status.isSidebarOpen]);

  // Types
  interface ModelOption {
    id: string;
    name: string;
    provider: string;
  }

  interface LLMAdapter {
    id: string;
    name: string;
    models: ModelOption[];
  }

  // State for models and adapters
  const [modelOptions, setModelOptions] = useState<ModelOption[]>([]);
  const [selectedProvider, setSelectedProvider] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [filteredModels, setFilteredModels] = useState<ModelOption[]>([]);
  const [llmAdapters, setLlmAdapters] = useState<LLMAdapter[]>([]);
  const [imageAdapters, setImageAdapters] = useState<any[]>([]);
  const [hasFetchedModels, setHasFetchedModels] = useState(false);

  // State for user interface
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [selectedTheme, setSelectedTheme] = useState('');
  const [selectedImageAdapter, setSelectedImageAdapter] = useState('');
  const [selectedImageModel, setSelectedImageModel] = useState('');
  const [availableImageModels, setAvailableImageModels] = useState<string[]>([]);
  const [hasUserUpdated, setHasUserUpdated] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [passwordError, setPasswordError] = useState('');
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [username, setUsername] = useState('');

  // State for TTS
  const [selectedTTS, setSelectedTTS] = useState(false);

  // Add all preferences as local state
  const [localPreferences, setLocalPreferences] = useState<Partial<UserPreferences>>(preferences || {});

  // Update local preferences when store preferences change
  useEffect(() => {
    if (preferences) {
      setLocalPreferences(preferences);
    }
  }, [preferences]);

  useEffect(() => {
    if (localPreferences.preferred_model && !selectedModel) {
      setSelectedModel(localPreferences.preferred_model);
    }

    if (localPreferences.preferred_provider && !selectedProvider) {
      setSelectedProvider(localPreferences.preferred_provider);
    }
  }, [localPreferences]);

  // Update helper function
  const updatePreferences = useCallback((updates: Partial<UserPreferences>) => {
    const newPreferences = {
      ...localPreferences,
      ...updates
    };

    // Update local state immediately
    setLocalPreferences(newPreferences);

    // Update store/backend
    setUserPreferences({
      preferences: newPreferences
    });
  }, [localPreferences, setUserPreferences]);

  useEffect(() => {
    if (user) {
      if (profile?.name !== name) setName(profile?.name || '');
      if (user?.email !== email) setEmail(user?.email || '');
      if (user?.username !== username) setUsername(user?.username || '');
    }
  }, [user]);

  useEffect(() => {
    if (localPreferences) {
      const adapter = localPreferences.preferred_image_adapter;
      const model = adapter ? localPreferences.preferred_image_models?.[adapter] : undefined;

      if (adapter && (adapter !== selectedImageAdapter || model !== selectedImageModel)) {
        if (adapter) setSelectedImageAdapter(adapter);
        if (model) setSelectedImageModel(model);
      }
    }
  }, [localPreferences]);

  useEffect(() => {
    if (localPreferences) {
      if (localPreferences.preferred_provider && !selectedProvider) {
        setSelectedProvider(localPreferences.preferred_provider);
        const filtered = modelOptions.filter(model => model.provider === localPreferences.preferred_provider);
        setFilteredModels(filtered);
      }

      // Set model if it exists in preferences
      if (localPreferences.preferred_model && !selectedModel) {
        setSelectedModel(localPreferences.preferred_model);
      }

      // Set theme if it exists
      if (typeof localPreferences?.theme === 'string' && !selectedTheme) {
        setSelectedTheme(localPreferences.theme);
      }
    }
  }, [localPreferences, modelOptions]);

  useEffect(() => {
    if (localPreferences?.theme) {
      document.documentElement.setAttribute('data-theme', localPreferences.theme);
      document.body.setAttribute('data-theme', localPreferences.theme);
    }
  }, [localPreferences?.theme]);

  // Update hand

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newName = e.target.value;
    setName(newName);
    debouncedUpdateProfile({ name: newName });
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newEmail = e.target.value;
    setEmail(newEmail);
    debouncedUpdateProfile({ email: newEmail });
  };

  const handleUsernameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newUsername = e.target.value;
    setUsername(newUsername);
    debouncedUpdateProfile({ username: newUsername });
  };

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !user?.id) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', user.id);
    setIsUpdating(true);

    try {
      const response = await fetch(`${API_ENDPOINT}/upload/file`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload file');
      }

      const { url } = await response.json();

      // Update both state and backend
      await debouncedUpdateProfile({ avatar: url });
      e.target.value = '';

    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleAdapterChange = (provider: string) => {
    setSelectedProvider(provider);

    // Reset model selection based on provider and preferences
    let nextModel = ''; // Default to no model selected
    if (provider === localPreferences.preferred_provider && localPreferences.preferred_model) {
      // Check if the preferred model exists within the *full* model list for the selected provider
      const providerHasPreferredModel = modelOptions.some(
        model => model.provider === provider && model.id === localPreferences.preferred_model
      );
      if (providerHasPreferredModel) {
        nextModel = localPreferences.preferred_model;
      }
    }
    setSelectedModel(nextModel); // Set the determined model (could be '' or the preferred one)
    // The filtering logic is now handled by a dedicated useEffect hook
  };

  const handleModelChange = useCallback(async (modelId: string) => {
    try {
      setSelectedModel(modelId); // Update UI state first
      updatePreferences({
        preferred_model: modelId,
        preferred_provider: selectedProvider // Ensure provider is also updated
      });
    } catch (error) {
      console.error('Error changing model:', error);
      // Optional: Add error handling/reversion logic here if needed
      // For now, keep the UI state as selected, log the error
    }
    // Added missing dependencies
  }, [selectedProvider, updatePreferences]);

  const handleThemeChange = useCallback((theme: string) => {
    setSelectedTheme(theme);
    updatePreferences({ theme });
  }, [updatePreferences]);

  const handleConversationChange = ({
    conversationId
  }: {
    conversationId: string;
  }) => {
    linkTo(`/posey/chat/${conversationId}`);
  }

  const handlePasswordUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');

    if (!user?.id) return;

    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      return;
    }

    setIsUpdating(true);
    try {
      const response = await fetch(`${API_ENDPOINT}/user/${user.id}/password`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          currentPassword,
          newPassword,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || error.error || 'Failed to update password');
      }

      // Clear form and hide it
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setShowPasswordForm(false);

      // const passwordUpdatedModal = document.getElementById('password-updated') as HTMLDialogElement;
      // if (passwordUpdatedModal) {
      //   passwordUpdatedModal.showModal();
      // }

    } catch (error: any) {
      setPasswordError(error.message || 'Failed to update password');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleImageAdapterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const adapter = e.target.value;
    setSelectedImageAdapter(adapter);
    updatePreferences({ preferred_image_adapter: adapter });
  };

  const handleImageModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const model = e.target.value;
    setSelectedImageModel(model);
    updatePreferences({
      preferred_image_models: {
        ...localPreferences.preferred_image_models,
        [selectedImageAdapter]: model
      }
    });
  };

  const toggleTTS = () => {
    updatePreferences({
      tts_enabled: !localPreferences.tts_enabled
    });
  };

  // Update TTS state when preferences change
  useEffect(() => {
    if (localPreferences?.tts_enabled !== undefined) {
      setSelectedTTS(localPreferences.tts_enabled);
    }
  }, [localPreferences?.tts_enabled]);

  const getImageListFromAdapters = (adapters: any) => {
    const modelList: any = {}
    Object.keys(adapters).forEach((key: string) => {
      const adapter: any = adapters[key];
      adapter?.models?.forEach((model: any) => {
        if (model.id && key) {
          modelList[`${key}___${model.id}`] = {
            ...model,
            adapter: key
          };
        }
      });
    });
    return Object.values(modelList);
  }

  const getModelListFromAdapters = (adapters: any) => {
    const modelList: any = {}
    Object.keys(adapters).forEach((key: string, index: number) => {
      const adapter: any = adapters[key];

      adapter?.models?.forEach((model: any) => {
        modelList[model.id] = {
          ...model,
          adapter: adapter.id
        };
      });
    });
    // Return as array 
    return Object.values(modelList);
  }

  useEffect(() => {
    const _models: any = getModelListFromAdapters(config.models.llm.adapters)
    if (!isEqual(_models, llmAdapters)) {
      setLlmAdapters(_models);
    }
  }, [config.models.llm.adapters]);

  useEffect(() => {
    const _models = getImageListFromAdapters(config.models.image.adapters)
    if (!isEqual(_models, imageAdapters)) {
      setImageAdapters(_models);
    }
  }, [config.models.image.adapters]);

  const handleLanguageChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const language = e.target.value;
    updatePreferences({ language });
  }

  // Load models including dynamic Ollama models
  useEffect(() => {
    const loadModels = async () => {
      setHasFetchedModels(true);

      try {
        const adapters = await getUpdatedLLMAdapters();
        const _models: any = getModelListFromAdapters(adapters);
        if (!isEqual(_models, modelOptions)) {
          setModelOptions(_models);
        }
        setHasFetchedModels(true); // Set true only after successful fetch/update
      } catch (error) {
        console.error('Error loading models:', error);
        setHasFetchedModels(false); // Keep false on error to potentially allow retry
      }
    };

    // Fetch models if we haven't successfully fetched them yet
    if (!hasFetchedModels) {
      loadModels();
    }
  }, [hasFetchedModels]);

  useEffect(() => {
    if (currentConversation?.id && !currentConversationId) {
      if (typeof window !== 'undefined') {
        const _id = window.location.pathname.split('/posey/chat/')[1];
        setCurrentConversationId(_id);
      }
    }

  }, [currentConversation]);

  // NEW: useEffect to filter models when provider or model list changes
  useEffect(() => {
    if (selectedProvider && modelOptions.length > 0) {
      const filtered = modelOptions.filter(model => model.provider === selectedProvider);
      setFilteredModels(filtered);

      // If a model was selected but is not in the new filtered list, clear it
      // This prevents displaying a model that doesn't belong to the selected provider
      if (selectedModel && !filtered.some(m => m.id === selectedModel)) {
        setSelectedModel('');
      }

    } else {
      setFilteredModels([]); // Clear filtered models if no provider is selected or no models loaded
    }
    // Depend on the provider selection and the full list of models
  }, [selectedProvider, modelOptions, selectedModel]);

  return (
    <div className={sidebarClass}>
      <div className={`sidebar-content bg-base-300 text-base-content overflow-y-auto p-4 ${sidebarClass}`}>
        {/* Base */}
        <section className={sectionClass} id="base-settings">
          <ul className="menu-vertical">
            <li>
              <label className={style.label} htmlFor="conversationId">Jump to conversation</label>
              <select
                className="select"
                id="conversationId"
                value={currentConversationId || ''}
                onChange={(e) => handleConversationChange({
                  conversationId: e.target.value
                })}
              >
                {conversations?.length > 0 && (
                  <option value="">Select a conversation</option>
                )}
                {conversations?.map((conversation: any) => (
                  <option
                    key={conversation.id}
                    value={conversation.id}>{conversation.title}
                  </option>
                ))}
              </select>
            </li>
          </ul>
        </section>

        <div className="divider divider-secondary mb-0">Posey Settings</div>

        {/* Posey Settings */}
        <section className={sectionClass} id="posey-settings">
          <ul className="menu-vertical">

            {/* Theme */}
            <li className={liClass}>
              <label className={style.label} htmlFor="theme">Theme</label>
              <select
                id="theme"
                className="select select-bordered mb-1"
                value={selectedTheme}
                onChange={(e) => handleThemeChange(e.target.value)}
              >
                {themes.map((theme: any) => (
                  <option key={theme.value} value={theme.value}>{theme.label}</option>
                ))}
              </select>
            </li>

            <li className={liClass}>
              <div className="divider divider-neutral mb-0">LLM Settings</div>
              <ul>
                {/* Adapter Selector */}
                <li className={liClass}>
                  <label className={style.label} htmlFor="provider">Provider</label>
                  <select
                    id="provider"
                    className="select select-bordered mb-1"
                    value={selectedProvider}
                    onChange={(e) => handleAdapterChange(e.target.value)}
                  >
                    <option value="">Select an adapter</option>
                    {/* Ensure modelOptions is used here to derive providers */}
                    {Array.from(new Set(modelOptions.map(model => model.provider))).map((provider: string) => (
                      <option key={provider} value={provider}>
                        {/* You might want a mapping for prettier provider names */}
                        {provider}
                      </option>
                    ))}
                  </select>
                </li>

                {/* Model Selector - Uses filteredModels */}
                {selectedProvider && (
                  <li className={liClass}>
                    <label className={style.label} htmlFor="model">Model</label>
                    <select
                      id="model"
                      className="select select-bordered mb-1"
                      value={selectedModel}
                      onChange={(e) => handleModelChange(e.target.value)}
                    >
                      <option value="">Select a model</option>
                      {/* Ensure filteredModels is correctly typed or cast */}
                      {filteredModels.map((model: ModelOption) => (
                        <option
                          key={model.id} // Use unique model id
                          value={model.id} // Value should be model id
                        >
                          {model.name} {/* Display model name */}
                        </option>
                      ))}
                    </select>
                  </li>
                )}
              </ul>
            </li>

            {/* Image Generator Selector */}
            <li className={liClass} id="image-generator-settings">
              <div className="divider divider-neutral mb-0">Image Settings</div>
              <label className={style.label} htmlFor="imageAdapter">Image Generator</label>
              <select
                id="imageAdapter"
                className="select select-bordered mb-1"
                value={selectedImageAdapter}
                onChange={handleImageAdapterChange}
              >
                {imageAdapters.map((adapter, index: number) => {
                  return (
                    <option
                      key={index}
                      value={adapter.id}
                    >
                      {adapter?.name ?? adapter?.id}
                    </option>
                  )
                })}
              </select>
            </li>

            <li className={liClass}>
              <div className="divider divider-neutral mb-0">Voice Settings</div>
              <div>
                {/* Model Selector (only show if models are available) */}
                {availableImageModels.length > 0 && (
                  <select
                    id="imageModel"
                    className="select select-bordered mt-1"
                    value={selectedImageModel}
                    onChange={handleImageModelChange}
                  >
                    {availableImageModels.map((model) => (
                      <option key={model} value={model}>
                        {model}
                      </option>
                    ))}
                  </select>
                )}
                <div className="form-control w-52">
                  <label className="label cursor-pointer">
                    <span className="label-text">Enable TTS</span>
                    <input
                      type="checkbox"
                      id="ttsEnabled"
                      className="toggle toggle-primary"
                      checked={localPreferences.tts_enabled || false}
                      onChange={toggleTTS}
                    />
                  </label>
                </div>

                {localPreferences.tts_enabled && <VoiceSelector speechAbility={speechAbility} />}
              </div>
            </li>

            {/* Language */}
            <li className={liClass}>
              <div className="divider divider-neutral mb-0">Localization Settings</div>
              <label className={style.label} htmlFor="language">Preferred Language</label>
              <select
                id="language"
                className="select select-bordered mb-1"
                value={localPreferences.language || 'en'}
                onChange={handleLanguageChange}
              >
                <option value="en">English</option>
                <option value="vi">Vietnamese</option>
              </select>
            </li>

          </ul>
        </section>

        {/* TODO: Move user settings to separate settings page */}
        <div className="divider divider-secondary mb-0">User Settings</div>

        {/* User Settings */}
        <section className={sectionClass}>
          <h3 className={style.h3}></h3>
          <ul className="menu-vertical">

            {/* Username */}
            <li className={liClass}>
              <label className="form-control w-full max-w-xs" htmlFor="username">
                <div className="label">
                  <span className="label-text">Username</span>
                </div>
                <input
                  id="username"
                  autoComplete="on"
                  type="text"
                  placeholder="maxwell"
                  className="input input-bordered w-full max-w-xs"
                  value={username}
                  onChange={handleUsernameChange}
                  disabled={isUpdating}
                />
              </label>
            </li>

            {/* Name */}
            <li className={liClass}>
              <label className="form-control w-full max-w-xs" htmlFor="name">
                <div className="label">
                  <span className="label-text">Name</span>
                </div>
                <input
                  id="name"
                  autoComplete="on"
                  type="text"
                  placeholder="Maxwell S. Hammer"
                  className="input input-bordered w-full max-w-xs"
                  value={name}
                  onChange={handleNameChange}
                  disabled={isUpdating}
                />
              </label>
            </li>

            {/* Email */}
            <li className={liClass}>
              <label className="form-control w-full max-w-xs" htmlFor="email">
                <div className="label">
                  <span className="label-text">Email</span>
                </div>
                <input
                  id="email"
                  autoComplete="on"
                  type="email"
                  placeholder="max@hammered.io"
                  className="input input-bordered w-full max-w-xs"
                  value={email}
                  onChange={handleEmailChange}
                  disabled={isUpdating}
                />
              </label>
            </li>

            {/* Avatar */}
            <li className={liClass}>
              <label className="form-control w-full max-w-xs">
                <div className="label">
                  <span className="label-text">Avatar</span>
                </div>
                <input
                  id="avatar"
                  autoComplete="off"
                  type="file"
                  className="file-input file-input-sm w-full max-w-xs"
                  onChange={handleAvatarChange}
                  accept="image/*"
                  disabled={isUpdating}
                />
              </label>
            </li>

            {/* Password Update */}
            <li className={liClass}>
              <span className="form-control w-full max-w-xs">
                <div className="label">
                  <span className="label-text">Password</span>
                </div>
                {!showPasswordForm && (
                  <button
                    type="button"
                    className="btn btn-primary btn-sm w-full"
                    onClick={() => setShowPasswordForm(true)}
                  >
                    Change Password
                  </button>
                )}
                {showPasswordForm && (
                  <form onSubmit={handlePasswordUpdate} className="space-y-2">
                    <input
                      id="currentPassword"
                      type={showPassword ? "text" : "password"}
                      placeholder="Current Password"
                      className="input input-bordered w-full max-w-xs mb-2"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      disabled={isUpdating}
                    />
                    <input
                      id="newPassword"
                      type={showPassword ? "text" : "password"}
                      placeholder="New Password"
                      className="input input-bordered w-full max-w-xs mb-2"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      disabled={isUpdating}
                    />
                    <input
                      id="confirmPassword"
                      type={showPassword ? "text" : "password"}
                      placeholder="Confirm New Password"
                      className="input input-bordered w-full max-w-xs mb-2"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      disabled={isUpdating}
                    />

                    <div className="flex items-center gap-2 mb-2">
                      <label className="label cursor-pointer">
                        <input
                          id="showPassword"
                          type="checkbox"
                          className="checkbox checkbox-sm"
                          checked={showPassword}
                          onChange={() => setShowPassword(!showPassword)}
                        />
                        <span className="label-text ml-2">Show password</span>
                      </label>
                    </div>

                    {passwordError && (
                      <div className="text-error text-sm mb-2">
                        {passwordError}
                      </div>
                    )}

                    <div className="flex gap-2">
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm flex-1"
                        onClick={() => {
                          setCurrentPassword('');
                          setNewPassword('');
                          setConfirmPassword('');
                          setPasswordError('');
                          setShowPasswordForm(false);
                        }}
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="btn btn-primary btn-sm flex-1"
                        disabled={isUpdating || !currentPassword || !newPassword || !confirmPassword}
                      >
                        {isUpdating ? 'Updating...' : 'Update Password'}
                      </button>
                    </div>
                  </form>
                )}
              </span>
            </li>

          </ul>
        </section>

      </div>

      <dialog id="password-updated" className="modal modal-bottom sm:modal-middle">
        <div className="modal-box">
          <h3 className="font-bold text-lg">Password Updated</h3>
          <p className="py-4">Your password has been updated successfully</p>
          <div className="modal-action">
            <form method="dialog">
              <button className="btn">Great</button>
            </form>
          </div>
        </div>
      </dialog>

    </div>
  );
}

