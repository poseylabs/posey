from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Literal
import os
from crawl4ai import AsyncWebCrawler
from browser_use import Agent
from datetime import datetime
import logging
from langchain_openai import ChatOpenAI  # For default LLM

# Import search adapters (use absolute import from src)
from search_adapters import BaseSearchAdapter, GoogleAdapter, BraveAdapter

logger = logging.getLogger(__name__)

os.environ['CRAWL4AI_CACHE_DIR'] = '/home/voyager/cache'

router = APIRouter(
    prefix="/voyager",
    tags=["voyager"]
)

class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    time_range: str = "any"
    provider: Literal["google", "brave"] = "google"

class ScrapeRequest(BaseModel):
    url: str
    mode: Literal["simple", "interactive"] = "simple"
    extraction_config: Dict[str, Any] = {}
    interaction_steps: Optional[List[Dict[str, Any]]] = None
    browser_config: Optional[Dict[str, Any]] = None

class InteractRequest(BaseModel):
    url: str
    interaction_steps: List[Dict[str, Any]]
    browser_config: Optional[Dict[str, Any]] = None
    task: Optional[str] = None  # Optional task description
    llm_config: Optional[Dict[str, Any]] = None  # Optional LLM configuration

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any] = {}

class ScrapeResponse(BaseModel):
    content: Dict[str, Any]
    interaction_results: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}

class InteractResponse(BaseModel):
    content: Dict[str, Any]
    interaction_results: List[Dict[str, Any]]
    metadata: Dict[str, Any] = {}

# --- Search Adapter Factory ---
# Store adapter CLASSES, not instances
ADAPTER_CLASSES: Dict[str, type[BaseSearchAdapter]] = {
    "google": GoogleAdapter,
    "brave": BraveAdapter
}

# Cache for instantiated adapters (optional, but good practice)
_adapter_instances: Dict[str, BaseSearchAdapter] = {}

def get_search_adapter(provider: str) -> BaseSearchAdapter:
    # Check cache first
    if provider in _adapter_instances:
        return _adapter_instances[provider]

    AdapterClass = ADAPTER_CLASSES.get(provider)
    if not AdapterClass:
        raise HTTPException(status_code=400, detail=f"Unsupported search provider: {provider}")

    # Instantiate the adapter HERE (lazily)
    try:
        adapter = AdapterClass()
    except Exception as e:
        logger.error(f"Failed to instantiate adapter for {provider}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to initialize search provider: {provider}")

    # Check if Brave adapter is usable AFTER instantiation
    if provider == "brave":
        # Access api_key directly now that it's instantiated
        if not getattr(adapter, 'api_key', None):
            logger.error("Brave adapter instantiated but API key is still missing!")
            raise HTTPException(status_code=503, detail="Brave search provider is not configured (missing API key).")
        else:
             logger.info("Brave adapter instantiated successfully with API key.")
    # Add check for Google adapter
    elif provider == "google":
         if not getattr(adapter, 'api_key', None) or not getattr(adapter, 'cse_id', None):
             logger.error("Google adapter instantiated but API key or CSE ID is missing!")
             raise HTTPException(status_code=503, detail="Google search provider is not configured (missing API key or CSE ID).")
         else:
             logger.info("Google adapter instantiated successfully with API key and CSE ID.")

    _adapter_instances[provider] = adapter
    return adapter


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Execute a web search using the specified provider (Google or Brave)."""
    # --- TEMPORARY DEBUGGING --- 
    brave_key_check = os.getenv("BRAVE_SEARCH_API_KEY")
    if request.provider == "brave":
        if brave_key_check:
            logger.info(f"[DEBUG /search] BRAVE_SEARCH_API_KEY found by os.getenv in endpoint: {brave_key_check[:4]}...")
        else:
            logger.error("[DEBUG /search] BRAVE_SEARCH_API_KEY NOT found by os.getenv in endpoint!")
    # --- END DEBUGGING ---
    try:
        adapter = get_search_adapter(request.provider)
        search_results = await adapter.search(
            query=request.query,
            limit=request.limit,
            time_range=request.time_range
        )

        return SearchResponse(
            results=search_results,
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "query": request.query,
                "search_engine": request.provider
            }
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Search error with provider {request.provider}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during search with {request.provider}.")

@router.post("/run", response_model=ScrapeResponse)
async def run_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """Execute web crawling using Crawl4AI"""
    try:
        crawler = AsyncWebCrawler()
        content = await crawler.crawl(
            request.url,
            config=request.extraction_config
        )

        return ScrapeResponse(
            content=content,
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "mode": "crawl4ai",
                "url": request.url
            }
        )
    except Exception as e:
        logger.error(f"Crawl4AI error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/use", response_model=InteractResponse)
async def run_interactive_browser(request: InteractRequest, background_tasks: BackgroundTasks):
    """Execute interactive browser automation using browser-use"""
    try:
        # Set default task if none provided
        task = request.task or "Navigate and interact with the webpage according to the provided steps"
        
        # Configure LLM - use provided config or default to OpenAI
        if request.llm_config:
            llm = ChatOpenAI(**request.llm_config)
        else:
            llm = ChatOpenAI(
                model="gpt-4",  # Default to GPT-4 for reliable web interaction
                temperature=0.7,
                api_key=os.getenv("OPENAI_API_KEY")
            )

        voyager = Agent(
            task=task,
            llm=llm
        )
        
        result = await voyager.interact(
            url=request.url,
            steps=request.interaction_steps,
            config=request.browser_config or {}
        )

        return InteractResponse(
            content=result.get("content", {}),
            interaction_results=result.get("steps_results", []),
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "mode": "browser-use",
                "url": request.url,
                "task": task,
                "steps_completed": len(result.get("steps_results", []))
            }
        )
    except Exception as e:
        logger.error(f"Browser-use error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
