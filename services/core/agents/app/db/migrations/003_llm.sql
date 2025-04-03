CREATE TABLE IF NOT EXISTS llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    base_url VARCHAR(255),
    api_version VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS llm_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES llm_providers(id),
    name VARCHAR(255) NOT NULL,
    model_id VARCHAR(255) NOT NULL,
    context_window INTEGER NOT NULL,
    max_tokens INTEGER,
    supports_embeddings BOOLEAN DEFAULT false,
    embedding_dimensions INTEGER,
    cost_per_token DECIMAL(10, 8),
    is_active BOOLEAN DEFAULT true,
    capabilities JSONB DEFAULT '[]'::jsonb,
    config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider_id, model_id)
);

CREATE TABLE IF NOT EXISTS llm_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES llm_providers(id),
    key_name VARCHAR(255) NOT NULL,
    api_key TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);
