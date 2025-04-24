-- Add managed_minions table

CREATE TABLE IF NOT EXISTS managed_minions (
    minion_key VARCHAR(255) PRIMARY KEY, -- Unique key derived from entry point
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    entry_point_ref VARCHAR(512) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT false,
    source VARCHAR(50) NOT NULL DEFAULT 'core',
    configuration JSONB DEFAULT '{}'::jsonb,
    associated_abilities JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_managed_minions_is_active ON managed_minions (is_active);
CREATE INDEX IF NOT EXISTS idx_managed_minions_source ON managed_minions (source); 

-- Insert core minions
INSERT INTO managed_minions 
    (minion_key, display_name, description, entry_point_ref, is_active, source, configuration, associated_abilities)
VALUES
    -- Content Analysis Minion
    (
        'content_analysis', 
        'Content Analysis',
        'Analyzes user requests to determine intent and required abilities',
        'app.minions.content_analysis:ContentAnalysisMinion',
        true,
        'core',
        '{
            "requires_setup": true,
            "priority": 10
        }'::jsonb,
        '["analysis", "intent_detection"]'::jsonb
    ),
    
    -- Memory Minion
    (
        'memory',
        'Memory Manager',
        'Manages memory operations including storing, retrieving, and analyzing memories',
        'app.minions.memory:MemoryMinion',
        true,
        'core',
        '{
            "requires_setup": true,
            "priority": 20
        }'::jsonb,
        '["memory_storage", "memory_retrieval", "memory_analysis"]'::jsonb
    ),
    
    -- Image Generation Minion (inactive by default)
    (
        'image_generation',
        'Image Generation',
        'Generate images using AI models',
        'app.minions.image_generation:ImageGenerationMinion',
        false,
        'core',
        '{
            "requires_setup": true,
            "priority": 30
        }'::jsonb,
        '["image_generation", "prompt_optimization"]'::jsonb
    ),
    
    -- Image Processing Minion (inactive by default)
    (
        'image_processing',
        'Image Processing',
        'Analyzes images to extract information, identify objects, or describe content',
        'app.minions.image_processing:ImageProcessingMinion',
        false,
        'core',
        '{
            "requires_setup": true,
            "priority": 35
        }'::jsonb,
        '["image_analysis", "content_extraction"]'::jsonb
    ),

    -- Orchestrator Minion  (active by default)
    (
        'orchestrator',
        'Orchestrator',
        'Orchestrates the execution of tasks and minions',
        'app.minions.orchestrator:OrchestratorMinion',
        true,
        'core',
        '{
            "requires_setup": true,
            "priority": 100
        }'::jsonb,
        '["orchestration"]'::jsonb
    ),
    
    -- Research Minion (inactive by default)
    (
        'research',
        'Research',
        'Conducts thorough deep research on topics using various sources and strategies, compiles information, and synthesizes it into a coherent report. Will also perform web searches, web crawling, and content scraping with assistance from the voyager minion.',
        'app.minions.research:ResearchMinion',
        false,
        'core',
        '{
            "requires_setup": true,
            "priority": 40
        }'::jsonb,
        '["research", "deep_research", "information_synthesis", "source_analysis"]'::jsonb
    ),

    -- Synthesis Minion (active by default)
    (
        'synthesis',
        'Synthesis',
        'Synthesizes the final user-facing response from the execution summary.',
        'app.minions.synthesis:SynthesisMinion',
        true,
        'core',
        '{
            "requires_setup": true,
            "priority": 50
        }'::jsonb,
        '["synthesis"]'::jsonb
    ),
    -- Voyager Minion (inactive by default)
    (
        'voyager',
        'Voyager',
        'Performs web searches, web crawling, scrapes content from URLs, and analyzes online information.',
        'app.minions.voyager:VoyagerMinion',
        false,
        'core',
        '{
            "requires_setup": true,
            "priority": 50
        }'::jsonb,
        '["web_search", "web_crawling", "content_scraping"]'::jsonb
    )
ON CONFLICT (minion_key) DO UPDATE 
SET 
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    entry_point_ref = EXCLUDED.entry_point_ref,
    source = EXCLUDED.source,
    updated_at = now(); 