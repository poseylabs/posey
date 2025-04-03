from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Literal
import os
from crawl4ai import AsyncWebCrawler
from browser_use import Agent
from datetime import datetime
import logging
import duckduckgo_search
from langchain_openai import ChatOpenAI  # For default LLM

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

@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """Execute a web search using DuckDuckGo"""
    try:
        ddg_results = duckduckgo_search.ddg(
            request.query,
            max_results=request.limit,
            time_range=request.time_range
        )
        results = []
        for result in ddg_results:
            results.append({
                "title": result["title"],
                "url": result["href"],
                "snippet": result["body"]
            })

        return SearchResponse(
            results=results,
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "query": request.query,
                "search_engine": "duckduckgo"
            }
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
