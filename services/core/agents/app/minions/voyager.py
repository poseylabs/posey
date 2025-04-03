from typing import Dict, Any, List, Optional, Literal
from pydantic_ai import RunContext, Agent
from pydantic import BaseModel, HttpUrl, Field
import httpx
from app.config import settings, logger
from app.config.prompts import load_prompt
from app.config.prompts.base import (
    generate_base_prompt,
    get_default_context,
    BasePromptContext,
    UserContext,
    MemoryContext,
    SystemContext
)
from app.config.defaults import LLM_CONFIG
from asyncio import gather, Semaphore
from itertools import chain
from string import Template
from datetime import datetime
import pytz
import time
import json
from app.minions.base import BaseMinion
import traceback
import re
from urllib.parse import urlparse
import os
import asyncio
import logging
from threading import Semaphore

# Configure logger
logger = logging.getLogger(__name__)

class SearchStrategy(BaseModel):
    """Configuration for search strategy and behavior"""
    engine: str = "duckduckgo"  # Search engine to use
    region: str = "wt-wt"  # Region for search results
    safe_search: bool = True  # Whether to filter explicit content
    time_period: str = "y"  # Time period for results (d=day, w=week, m=month, y=year)
    max_retries: int = 2  # Maximum number of retry attempts
    diversify: bool = True  # Whether to diversify results across domains

class InteractionStep(BaseModel):
    """Model for browser interaction steps"""
    action: Literal["click", "type", "scroll", "wait", "extract"]
    selector: Optional[str] = None
    value: Optional[str] = None
    wait_time: Optional[int] = None

class WebRequest(BaseModel):
    """Model for web scraping/search/interaction requests"""
    operation: Literal["search", "scrape", "interact"] = Field(..., description="'search', 'scrape', or 'interact'")
    query: str
    urls: List[HttpUrl] = []
    extraction_config: Dict[str, Any] = {}
    interaction_steps: Optional[List[InteractionStep]] = None
    max_results: int = 5
    strategy: SearchStrategy = Field(default_factory=SearchStrategy)
    browser_config: Optional[Dict[str, Any]] = None
    mode: Literal["simple", "interactive"] = "simple"

class WebResponse(BaseModel):
    """Structured response for web search and scraping operations"""
    status: str  # success or error
    data: Dict[str, Any] = {}
    error: Optional[str] = None
    error_type: Optional[str] = None
    attempted_operation: Optional[str] = None
    sources: List[Dict[str, str]] = []
    confidence: float = 0.0
    analysis_metadata: Dict[str, Any] = {}

class WebContentExtractor:
    """Class for extracting content from web pages"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        self.cache = {}  # Simple in-memory cache
    
    async def extract_content(self, url: str, cache_policy: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract content from a web page"""
        # Default cache policy
        if cache_policy is None:
            cache_policy = {"use_cache": True, "max_age_hours": 24}
        
        # Check cache if enabled
        cache_hit = False
        if cache_policy.get("use_cache", True) and url in self.cache:
            cached_result = self.cache[url]
            cache_age = datetime.now() - cached_result.get("timestamp", datetime.min)
            if cache_age.total_seconds() < cache_policy.get("max_age_hours", 24) * 3600:
                cache_hit = True
                return {**cached_result, "cache_hit": True}
        
        # Fetch content
        try:
            response = await self.client.get(url)
            if response.status_code != 200:
                return {
                    "error": f"HTTP error: {response.status_code}",
                    "content": {},
                    "metadata": {
                        "status_code": response.status_code
                    }
                }
            
            html_content = response.text
            
            # Extract metadata from HTML
            title = self._extract_title(html_content)
            description = self._extract_meta_description(html_content)
            
            # Extract main text content
            main_text = self._extract_main_text(html_content)
            
            result = {
                "content": {
                    "text": main_text,
                    "html": html_content[:10000]  # Limit HTML size
                },
                "metadata": {
                    "title": title,
                    "description": description,
                    "url": url,
                    "timestamp": datetime.now()
                },
                "cache_hit": False
            }
            
            # Store in cache
            if cache_policy.get("use_cache", True):
                self.cache[url] = result
            
            return result
        
        except Exception as e:
            error_msg = f"Error extracting content from {url}: {str(e)}"
            logger.error(error_msg)
            return {
                "error": str(e),
                "content": {},
                "metadata": {
                    "error_type": type(e).__name__
                }
            }
    
    def _extract_title(self, html: str) -> str:
        """Extract page title from HTML"""
        match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return "Unknown Title"
    
    def _extract_meta_description(self, html: str) -> str:
        """Extract meta description from HTML"""
        match = re.search(r'<meta\s+name="description"\s+content="(.*?)"', html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_main_text(self, html: str) -> str:
        """Extract main text content from HTML (simplified version)"""
        # Remove scripts and style elements
        no_script = re.sub(r'<script.*?>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        no_style = re.sub(r'<style.*?>.*?</style>', '', no_script, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', no_style)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

class VoyagerMinion(BaseMinion):
    """
    Voyager is responsible for web research, including searching, scraping, and analyzing online content.
    It uses a combination of search APIs and web scraping to gather information.
    """
    
    def __init__(self, llm_config: Dict[str, Any] = None):
        """Initialize the Voyager minion with configuration"""
        super().__init__(
            name="voyager",
            description="Web research specialist capable of searching and analyzing online content",
            abilities=[
                {
                    "name": "search",
                    "description": "Search the web for information",
                    "parameters": {
                        "query": "The search query to execute",
                        "max_results": "Maximum number of results to return (default: 5)",
                        "strategy": "Search strategy configuration"
                    }
                },
                {
                    "name": "scrape",
                    "description": "Scrape and extract content from a specific URL",
                    "parameters": {
                        "url": "The URL to scrape",
                        "cache_policy": "Configuration for caching behavior"
                    }
                }
            ],
            llm_config=llm_config or LLM_CONFIG
        )
        
        # Initialize HTTP client
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        self.scrape_semaphore = asyncio.Semaphore(5)  # Limit concurrent scraping
        
        # Search provider setup
        self.search_provider = os.environ.get("SEARCH_PROVIDER", "duckduckgo")
        self.search_api_key = os.environ.get("SEARCH_API_KEY", "")
        
        # Initialize browser instance for content extraction
        self.browser = WebContentExtractor()
        
        # List of known credible domains (example list - would be more extensive in production)
        self.known_credible_domains = [
            "wikipedia.org",
            "bbc.com",
            "reuters.com",
            "nature.com",
            "sciencedirect.com",
            "nih.gov",
            "edu",
            "gov"
        ]
        
        # List of suspicious TLDs (example list)
        self.suspicious_tlds = [
            ".xyz",
            ".info",
            ".biz",
            ".cc",
            ".tk"
        ]
        
        # Setup base prompts
        self._setup_prompts()

    def setup(self):
        """Initialize minion-specific components"""
        # Get base prompt with default context for initialization
        base_prompt = generate_base_prompt(get_default_context())
        
        # Override system prompt to include base prompt
        custom_system_prompt = "\n".join([
            base_prompt,  # Start with shared base prompt
            self.get_system_prompt()
        ])
        
        logger.debug(f"System prompt configured for voyager minion")

        # Create agents for different tasks
        self.search_agent = self.create_agent(model_key="reasoning")
        self.analysis_agent = self.create_agent(model_key="reasoning")
        self.credibility_agent = self.create_agent(model_key="reasoning")
        
        # Initialize HTTP client for web operations
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; VoyagerBot/1.0; research-assistant)"
            }
        )
        
        # Initialize semaphores for concurrent operations
        self.search_semaphore = Semaphore(3)
        
        logger.info(f"Voyager minion initialized with model: {LLM_CONFIG['reasoning']['model']}")
    
    def create_prompt_context(self, context: Dict[str, Any], search_data: Dict[str, Any] = None) -> BasePromptContext:
        """Create a properly structured prompt context for web search operations
        
        Args:
            context: The raw context dictionary
            search_data: Additional search-specific data to include in the context
            
        Returns:
            A BasePromptContext object with user, memory, and system contexts
        """
        # Extract user information from context
        user_id = context.get("user_id", "anonymous")
        user_name = context.get("user_name", "User")
        
        # Create user context
        user_context = UserContext(
            id=user_id,
            name=user_name,
            preferences=context.get("preferences", {}),
        )
        
        # Create memory context
        memory_context = MemoryContext(
            recent_memories=context.get("recent_memories", []),
            relevant_memories=context.get("relevant_memories", [])
        )
        
        # Create system context
        system_context = SystemContext(
            current_time=context.get("timestamp", datetime.now().isoformat()),
            agent_capabilities=["web_search", "content_scraping", "source_analysis"],
            **context.get("system", {})
        )
        
        # Add search-specific data to the appropriate context
        if search_data:
            # Add query-related info to user context
            if "query" in search_data:
                user_context.query = search_data["query"]
            if "max_results" in search_data:
                user_context.max_results = search_data["max_results"]
                
            # Add search-specific fields to system context
            if "operation" in search_data:
                system_context.current_operation = search_data["operation"]
            if "strategy" in search_data:
                system_context.search_strategy = search_data["strategy"]
            if "url" in search_data:
                system_context.target_url = search_data["url"]
                
        # Return complete context
        return BasePromptContext(
            user=user_context,
            memory=memory_context,
            system=system_context
        )
    
    async def evaluate_source_credibility(self, url: str, content: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate the credibility of a source based on various factors"""
        start_time = time.time()
        
        try:
            # Create credibility-specific context data
            credibility_data = {
                "url": url,
                "operation": "evaluate_credibility"
            }
            
            # Create proper prompt context
            prompt_context = self.create_prompt_context(context, credibility_data)
            
            # Basic URL analysis
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # Domain-based credibility factors
            domain_factors = {
                "is_known_source": domain in self.known_credible_domains,
                "has_suspicious_tld": parsed_url.netloc.endswith(tuple(self.suspicious_tlds)),
                "domain_age": "unknown"  # Would require external API
            }
            
            # Content-based credibility factors
            content_text = content.get("text", "")
            content_factors = {
                "has_citations": bool(re.search(r'\[\d+\]|\(\d{4}\)', content_text)),
                "content_length": len(content_text),
                "reading_level": self._estimate_reading_level(content_text)
            }
            
            # Calculate overall credibility score (simplified)
            score = 0.5  # Default neutral score
            
            if domain_factors["is_known_source"]:
                score += 0.3
            if domain_factors["has_suspicious_tld"]:
                score -= 0.3
            if content_factors["has_citations"]:
                score += 0.2
            if content_factors["content_length"] > 2000:
                score += 0.1
            
            # Cap the score between 0.1 and 0.9
            score = max(0.1, min(0.9, score))
            
            execution_time = time.time() - start_time
            
            return {
                "score": score,
                "factors": {
                    "domain": domain_factors,
                    "content": content_factors
                },
                "metadata": {
                    "execution_time": execution_time,
                    "minion": "voyager"
                }
            }
            
        except Exception as e:
            error_msg = f"Error evaluating source credibility for {url}: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            return {
                "score": 0.5,  # Neutral score on error
                "error": str(e),
                "error_type": type(e).__name__,
                "attempted_operation": "evaluate_source_credibility",
                "metadata": {
                    "execution_time": time.time() - start_time,
                    "traceback": traceback.format_exc(),
                    "minion": "voyager"
                }
            }
    
    def _estimate_reading_level(self, text: str) -> str:
        """Estimate the reading level of text based on simple heuristics"""
        if not text:
            return "unknown"
        
        # Get a sample of the text to analyze
        sample = text[:5000] if len(text) > 5000 else text
        
        # Count sentences
        sentences = re.split(r'[.!?]+', sample)
        sentence_count = len([s for s in sentences if len(s.strip()) > 0])
        
        if sentence_count == 0:
            return "unknown"
        
        # Count words
        words = re.findall(r'\b\w+\b', sample)
        word_count = len(words)
        
        # Count complex words (more than 3 syllables as a rough approximation)
        complex_word_count = 0
        for word in words:
            if len(word) >= 9:  # Crude approximation for complex words
                complex_word_count += 1
        
        # Average sentence length
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        
        # Simplified reading level estimation
        if avg_sentence_length > 25 or avg_word_length > 6 or (complex_word_count / word_count > 0.2 if word_count > 0 else False):
            return "advanced"
        elif avg_sentence_length > 15 or avg_word_length > 5 or (complex_word_count / word_count > 0.1 if word_count > 0 else False):
            return "intermediate"
        else:
            return "basic"
    
    async def _generate_query_variations(self, base_query: str) -> List[str]:
        """Generate variations of a search query for better results"""
        start_time = time.time()
        
        try:
            # Get task prompt from configuration
            user_prompt = self.get_task_prompt(
                "query_variation",
                query=base_query
            )
            
            # Run the search agent
            logger.info(f"Generating query variations for: {base_query}")
            variation_result = await self.search_agent.run(user_prompt)
            
            # Extract result
            if hasattr(variation_result, 'data') and 'variations' in variation_result.data:
                variations = variation_result.data['variations']
                if not variations or not isinstance(variations, list):
                    variations = [base_query]
            else:
                variations = [base_query]
            
            execution_time = time.time() - start_time
            logger.info(f"Generated {len(variations)} query variations in {execution_time:.2f}s")
            
            return variations
            
        except Exception as e:
            logger.error(f"Error generating query variations: {str(e)}")
            return [base_query]
    
    async def search_web(self, query: str, strategy: SearchStrategy = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Perform a web search with the given query"""
        start_time = time.time()
        
        try:
            # Default strategy if not provided
            if strategy is None:
                strategy = SearchStrategy()
            
            # Create search-specific context data
            search_data = {
                "query": query,
                "strategy": strategy.model_dump() if hasattr(strategy, "model_dump") else vars(strategy),
                "operation": "search_web"
            }
            
            # Create proper prompt context
            prompt_context = self.create_prompt_context(context, search_data)
            
            # Generate query variations for better coverage
            query_variations = await self._generate_query_variations(query)
            
            # Mock search results (would integrate with real search API)
            search_results = []
            for q in query_variations[:3]:  # Limit to 3 variations
                # Simulate different results for each variation
                mock_results = self._mock_search_results(q, 3)  # 3 results per variation
                search_results.extend(mock_results)
            
            # Remove duplicates based on URL
            unique_results = []
            seen_urls = set()
            for result in search_results:
                if result["url"] not in seen_urls:
                    unique_results.append(result)
                    seen_urls.add(result["url"])
            
            # Sort by relevance (mock implementation)
            sorted_results = sorted(
                unique_results,
                key=lambda x: x.get("relevance_score", 0),
                reverse=True
            )
            
            execution_time = time.time() - start_time
            logger.info(f"Web search completed in {execution_time:.2f}s: {query}")
            
            return {
                "status": "success",
                "query": query,
                "results": sorted_results[:10],  # Limit to top 10
                "metadata": {
                    "execution_time": execution_time,
                    "total_results": len(sorted_results),
                    "strategy": strategy.model_dump() if hasattr(strategy, "model_dump") else vars(strategy),
                    "minion": "voyager"
                }
            }
            
        except Exception as e:
            error_msg = f"Error in web search: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            return {
                "status": "error",
                "query": query,
                "results": [],
                "error": str(e),
                "error_type": type(e).__name__,
                "attempted_operation": "search_web",
                "metadata": {
                    "execution_time": time.time() - start_time,
                    "traceback": traceback.format_exc(),
                    "minion": "voyager"
                }
            }
    
    async def scrape_url(self, url: str, cache_policy: Dict[str, Any] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Scrape content from a specific URL"""
        start_time = time.time()
        
        try:
            # Default cache policy
            if cache_policy is None:
                cache_policy = {"use_cache": True, "max_age_hours": 24}
            
            # Extract content using web scraper
            result = await self.browser.extract_content(url, cache_policy)
            
            # Create scrape-specific context data
            scrape_data = {
                "url": url,
                "operation": "scrape",
                "cache_policy": cache_policy
            }
            
            # Create proper prompt context
            prompt_context = self.create_prompt_context(context, scrape_data)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            logger.info(f"URL scraping completed in {execution_time:.2f}s")
            
            # Create and return the response
            return {
                "status": "success",
                "url": url,
                "content": result.get("content", {}),
                "metadata": {
                    "title": result.get("metadata", {}).get("title", ""),
                    "description": result.get("metadata", {}).get("description", ""),
                    "execution_time": execution_time,
                    "cache_hit": result.get("cache_hit", False),
                    "text_length": len(result.get("content", {}).get("text", "")),
                    "minion": "voyager"
                }
            }
        except Exception as e:
            error_msg = f"Error scraping URL {url}: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            return {
                "status": "error",
                "url": url,
                "error": str(e),
                "error_type": type(e).__name__,
                "attempted_operation": "scrape_url",
                "metadata": {
                    "execution_time": time.time() - start_time,
                    "traceback": traceback.format_exc(),
                    "minion": "voyager"
                }
            }
    
    async def analyze_search_results(self, results: List[Dict[str, Any]], query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze search results for relevance and organization"""
        start_time = time.time()
        
        try:
            # Get task prompt from configuration
            user_prompt = self.get_task_prompt(
                "search_analysis",
                results=results,
                query=query
            )
            
            # Run the analysis agent
            logger.info(f"Analyzing {len(results)} search results for query: {query}")
            analysis_result = await self.analysis_agent.run(user_prompt)
            
            # Extract result
            if hasattr(analysis_result, 'data'):
                analysis = analysis_result.data
            else:
                analysis = {
                    "relevant_results": results,
                    "categories": [],
                    "key_sources": [],
                    "recommendations": []
                }
            
            execution_time = time.time() - start_time
            logger.info(f"Search analysis completed in {execution_time:.2f}s")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing search results: {str(e)}")
            return {
                "relevant_results": results,
                "categories": [],
                "key_sources": [],
                "recommendations": [],
                "error": str(e)
            }
    
    async def search_and_analyze(self, params: Dict[str, Any]) -> WebResponse:
        """Perform a complete search and analysis operation"""
        start_time = time.time()
        
        try:
            # Extract parameters
            query = params.get("query", "")
            max_results = params.get("max_results", 5)
            strategy_params = params.get("strategy", {})
            context = params.get("context", {})
            strategy = SearchStrategy(**strategy_params)
            
            if not query:
                return WebResponse(
                    status="error",
                    data={},
                    error="No query provided for search",
                    confidence=0.0
                )
            
            # Create search-specific context data
            search_data = {
                "query": query,
                "max_results": max_results,
                "operation": "search",
                "strategy": strategy.model_dump()
            }
            
            # Create proper prompt context
            prompt_context = self.create_prompt_context(context, search_data)
            
            # Step 1: Perform web search
            search_result = await self.search_web(query, strategy, context)
            
            if not search_result.get("results"):
                return WebResponse(
                    status="error",
                    data={
                        "query": query,
                        "results": []
                    },
                    error=search_result.get("error", "No results found"),
                    confidence=0.0
                )
            
            # Step 2: Analyze the results
            analysis = await self.analyze_search_results(
                search_result.get("results", [])[:max_results],
                query,
                context
            )
            
            # Step 3: Scrape key sources for more detailed information
            key_sources = analysis.get("key_sources", [])[:3]  # Limit to top 3 sources
            scraped_content = []
            
            if key_sources:
                for source in key_sources:
                    source_url = source.get("url")
                    if source_url:
                        scrape_result = await self.scrape_url(source_url, None, context)
                        if scrape_result.get("status") == "success":
                            # Get credibility assessment
                            credibility = await self.evaluate_source_credibility(
                                source_url,
                                scrape_result.get("content", {}),
                                context
                            )
                            
                            scraped_content.append({
                                "url": source_url,
                                "content": scrape_result.get("content"),
                                "credibility": credibility
                            })
            
            execution_time = time.time() - start_time
            logger.info(f"Research completed in {execution_time:.2f}s")
            
            # Construct the response
            return WebResponse(
                status="success",
                data={
                    "query": query,
                    "results": analysis.get("relevant_results", []),
                    "categories": analysis.get("categories", []),
                    "detailed_content": scraped_content,
                    "recommendations": analysis.get("recommendations", [])
                },
                sources=[{
                    "url": source.get("url"),
                    "title": source.get("title"),
                    "type": source.get("source_type", "website")
                } for source in search_result.get("results", [])[:max_results]],
                confidence=0.8,
                analysis_metadata={
                    "execution_time": execution_time,
                    "sources_scraped": len(scraped_content),
                    "total_results": len(search_result.get("results", []))
                }
            )
            
        except Exception as e:
            logger.error(f"Error in search and analysis: {str(e)}")
            execution_time = time.time() - start_time
            return WebResponse(
                status="error",
                data={
                    "query": params.get("query", ""),
                },
                error=str(e),
                confidence=0.0,
                analysis_metadata={
                    "execution_time": execution_time,
                    "success": False
                }
            )
    
    async def execute(self, params: Dict[str, Any], context: RunContext) -> Dict[str, Any]:
        """Execute web research operations"""
        operation = params.get("operation", "search")
        start_time = time.time()
        
        try:
            # Extract context from RunContext
            run_context = context.deps if hasattr(context, "deps") else {}
            
            # Add context to params
            params["context"] = run_context
            
            if operation == "search":
                response = await self.search_and_analyze(params)
                return response.model_dump()
                
            elif operation == "scrape":
                url = params.get("url")
                if not url:
                    return {
                        "status": "error",
                        "error": "No URL provided for scraping",
                        "error_type": "missing_parameter",
                        "attempted_operation": "scrape",
                        "metadata": {
                            "execution_time": time.time() - start_time,
                            "minion": "voyager"
                        }
                    }
                    
                scrape_result = await self.scrape_url(url, params.get("config"), run_context)
                return scrape_result
                
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported operation: {operation}",
                    "error_type": "invalid_operation",
                    "attempted_operation": operation,
                    "metadata": {
                        "supported_operations": ["search", "scrape"],
                        "execution_time": time.time() - start_time,
                        "minion": "voyager"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error in voyager minion: {str(e)}")
            
            # Get detailed error info
            error_traceback = traceback.format_exc()
            logger.error(f"Traceback: {error_traceback}")
            
            return {
                "status": "error",
                "error": str(e),
                "error_type": "voyager_exception",
                "attempted_operation": operation,
                "metadata": {
                    "operation": operation,
                    "error_traceback": error_traceback.split("\n")[-3:],
                    "execution_time": time.time() - start_time,
                    "minion": "voyager",
                    "parameters": {k: v for k, v in params.items() if k != "query"} # Exclude query to avoid leaking sensitive info
                }
            }
    
    async def cleanup(self):
        """Clean up resources"""
        await self.client.aclose()
    
    def _mock_search_results(self, query: str, count: int = 5) -> List[Dict[str, Any]]:
        """Generate mock search results for demonstration/testing purposes"""
        results = []
        
        # Some domains for variety
        domains = [
            "wikipedia.org",
            "nytimes.com",
            "github.com",
            "stackoverflow.com",
            "medium.com",
            "harvard.edu",
            "nasa.gov",
            "bbc.com",
            "cnn.com",
            "arxiv.org"
        ]
        
        # Generate mock results based on the query
        for i in range(min(count, 10)):
            domain = domains[i % len(domains)]
            result = {
                "title": f"Result {i+1} for {query}",
                "url": f"https://www.{domain}/search?q={query.replace(' ', '+')}",
                "snippet": f"This is a mock result snippet for the query '{query}' with some relevant information...",
                "source_type": "website",
                "publish_date": datetime.now().isoformat(),
                "relevance_score": 0.9 - (i * 0.05)  # Decreasing relevance
            }
            results.append(result)
        
        return results
