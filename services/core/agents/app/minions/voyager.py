from typing import Dict, Any, List, Optional, Literal
from pydantic_ai import RunContext, Agent
from pydantic import BaseModel, HttpUrl, Field
import httpx

from app.config.prompts.base import (
    BasePromptContext,
    UserContext,
    MemoryContext,
    SystemContext
)

from datetime import datetime

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
from sqlalchemy.ext.asyncio import AsyncSession
import pprint

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
    
    # __init__ removed - BaseMinion.__init__ called by registry
    # Initialize attributes previously set in __init__ at class level or in setup
    task_planner_agent: Optional[Agent] = None
    execution_agent: Optional[Agent] = None
    search_agent: Optional[Agent] = None
    analysis_agent: Optional[Agent] = None
    credibility_agent: Optional[Agent] = None
    available_tools = ["web_search", "web_crawling", "content_scraping"]
    client: Optional[httpx.AsyncClient] = None # Initialize in setup
    scrape_semaphore: asyncio.Semaphore = asyncio.Semaphore(5)
    search_provider: str = os.environ.get("SEARCH_PROVIDER", "duckduckgo") # Default, may be overridden by voyager service itself
    search_api_key: str = os.environ.get("SEARCH_API_KEY", "") # May be needed if directly calling API, less likely if using service
    browser: WebContentExtractor = WebContentExtractor() # Instantiate here
    # Construct the voyager service URL from environment variables
    voyager_domain: str = os.environ.get("VOYAGER_DOMAIN", "voyager")
    voyager_port: str = os.environ.get("VOYAGER_PORT", "7777")
    voyager_service_url: str = f"http://{voyager_domain}:{voyager_port}/voyager/search"
    known_credible_domains = [
        "wikipedia.org",
        "bbc.com",
        "reuters.com",
        "nature.com",
        "sciencedirect.com",
        "nih.gov",
        "edu",
        "gov"
    ]
    suspicious_tlds = [
        ".xyz", ".info", ".biz", ".cc", ".tk"
    ]

    async def setup(self, *args, **kwargs) -> None:
        """Initialize the httpx client, accepting extra args."""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=30.0)
            logger.info("VoyagerMinion httpx client initialized.")
        else:
            logger.info("VoyagerMinion httpx client already initialized.")

    def create_prompt_context(self, context: Dict[str, Any], search_data: Dict[str, Any] = None) -> BasePromptContext:
        """Create a properly structured prompt context for web search operations
        
        Args:
            context: The raw context dictionary
            search_data: Additional search-specific data to include in the context
            
        Returns:
            A BasePromptContext object with user, memory, and system contexts
        """
        # Extract user information from context
        user_id_val = context.get("user_id")
        user_id_key_used = "user_id"
        if not user_id_val:
            # Fallback: Check for 'id' key if 'user_id' is not present
            user_id_val = context.get("id", "anonymous")
            user_id_key_used = "id"
            if user_id_val == "anonymous":
                logger.warning(f"[CREATE_PROMPT_CONTEXT] Neither 'user_id' nor 'id' found in context. Defaulting to '{user_id_val}'. Context keys: {list(context.keys())}")
            else:
                logger.info(f"[CREATE_PROMPT_CONTEXT] Found user identifier using fallback key: '{user_id_key_used}'")
        else:
            logger.info(f"[CREATE_PROMPT_CONTEXT] Found user identifier using primary key: '{user_id_key_used}'")
            
        user_name = context.get("user_name", "User")
        
        # Create user context
        user_context = UserContext(
            user_id=user_id_val, # Corrected field name
            name=user_name,
            preferences=context.get("preferences", {}),
            # Also pass location if it's expected by UserContext and present in the input context
            location=context.get("location") # Add location if needed by UserContext model
        )
        
        # Create memory context
        memory_context = MemoryContext(
            recent_memories=context.get("recent_memories", []),
            relevant_memories=context.get("relevant_memories", [])
        )

        # --- Prepare data for SystemContext instantiation ---
        system_context_data = {
            "timestamp": context.get("timestamp", datetime.now().isoformat()),
            "agent_capabilities": ["web_search", "content_scraping", "source_analysis"],
            **(context.get("system", {})) # Unpack existing system context data from input
        }

        # Add search-specific data if available, attempting to match potential SystemContext fields
        if search_data:
            if "operation" in search_data:
                system_context_data['current_operation'] = search_data["operation"]
            if "strategy" in search_data:
                # Convert strategy object to dict if it's a Pydantic model, otherwise pass as is
                strategy_value = search_data["strategy"]
                if hasattr(strategy_value, 'model_dump') and callable(strategy_value.model_dump):
                    system_context_data['search_strategy'] = strategy_value.model_dump()
                elif isinstance(strategy_value, dict):
                     system_context_data['search_strategy'] = strategy_value
                else: # Pass as is if not a model or dict, log warning
                     system_context_data['search_strategy'] = strategy_value
                     logger.warning(f"Passing non-serializable search_strategy to SystemContext: {type(strategy_value)}")

            if "timestamp" in search_data: # Update timestamp if provided specifically in search_data
                system_context_data['timestamp'] = search_data["timestamp"]
            if "url" in search_data:
                system_context_data['target_url'] = search_data["url"]
            if "query" in search_data:
                system_context_data['query'] = search_data["query"]
            if "max_results" in search_data:
                system_context_data['max_results'] = search_data["max_results"]
        # --- End SystemContext data preparation ---

        # Create system context using the combined data
        try:
            # Attempt instantiation with all collected data
            system_context = SystemContext(**system_context_data)
            logger.debug(f"Successfully instantiated SystemContext with keys: {list(system_context_data.keys())}")
        except Exception as e:
             # Log error and fallback to basic instantiation if keys don't match model
             logger.error(f"Failed to instantiate SystemContext with combined data: {e}. Data keys: {list(system_context_data.keys())}", exc_info=True)
             system_context = SystemContext(
                 timestamp=context.get("timestamp", datetime.now().isoformat()),
                 agent_capabilities=["web_search", "content_scraping", "source_analysis"],
                 **(context.get("system", {})) # Use only base system data on fallback
             )
             logger.warning("Fell back to basic SystemContext instantiation.")

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
        """Perform a web search with the given query by calling the voyager service"""
        start_time = time.time()
        context = context or {} # Ensure context is at least an empty dict

        # Ensure client is initialized
        if not self.client:
            await self.setup()
            if not self.client: # Check again after setup attempt
                logger.error("VoyagerMinion client failed to initialize.")
                return {
                    "status": "error",
                    "query": query,
                    "results": [],
                    "error": "HTTP client not initialized",
                    "error_type": "configuration_error",
                    "attempted_operation": "search_web",
                    "metadata": {"execution_time": time.time() - start_time, "minion": "voyager"}
                }

        try:
            # Default strategy if not provided
            if strategy is None:
                strategy = SearchStrategy()

            # --- Optional Query Enhancement (Defensive) ---
            enhanced_query = query # Default to original query
            if self.agent:
                try:
                    # Create context data needed specifically for query enhancement prompt
                    enhancement_context_data = { k: context.get(k) for k in ["user_id", "id", "user_name", "preferences", "location"] if context.get(k) is not None}
                    # Attempt to create a minimal prompt context for enhancement
                    enhancement_prompt_context = self.create_prompt_context(enhancement_context_data)

                    # Get the task prompt for query enhancement
                    enhancement_prompt = self.get_task_prompt(
                        "enhance_search_query",
                        context=enhancement_prompt_context, # Pass the specific context
                        original_query=query
                    )

                    if enhancement_prompt:
                        logger.info(f"Attempting to enhance search query for: '{query}' using LLM.")
                        llm_result = await self.agent.run(enhancement_prompt)

                        if isinstance(llm_result, str) and llm_result.strip():
                            enhanced_query = llm_result.strip()
                            logger.info(f"LLM enhanced query to: '{enhanced_query}'")
                        elif hasattr(llm_result, 'data') and isinstance(llm_result.data, str) and llm_result.data.strip():
                            enhanced_query = llm_result.data.strip()
                            logger.info(f"LLM enhanced query (from data attribute) to: '{enhanced_query}'")
                        else:
                            logger.warning("LLM query enhancement did not return a valid string. Result: {llm_result}")
                    else:
                         logger.warning("Task prompt 'enhance_search_query' not found or invalid. Using original query.")
                except Exception as llm_err:
                    logger.error(f"Error during LLM query enhancement: {llm_err}", exc_info=True)
                    # Proceed with the original query on error
            else:
                 logger.warning("VoyagerMinion agent not available for query enhancement. Using original query.")
            # --- End Optional Query Enhancement ---

            # Prepare payload matching the voyager service's SearchRequest model
            payload = {
                "query": enhanced_query, # Use the (potentially) enhanced query
                "limit": getattr(strategy, 'max_results', 5), # Use getattr for safety
                "time_range": getattr(strategy, 'time_period', "y")
            }

            logger.info(f"[VOYAGER_SERVICE_CALL] Attempting POST to {self.voyager_service_url}")
            logger.debug(f"[VOYAGER_SERVICE_CALL] Payload: {json.dumps(payload)}")

            response = await self.client.post(self.voyager_service_url, json=payload, timeout=60.0)

            logger.info(f"[VOYAGER_SERVICE_CALL] Response Status Code: {response.status_code}")
            raw_response_text = response.text
            try:
                logger.debug(f"[VOYAGER_SERVICE_CALL] Raw Response Text: {raw_response_text[:1000]}...")
                service_results = json.loads(raw_response_text)
                # --- Store the raw response data --- 
                raw_response_data = service_results 
                # ----------------------------------
                logger.debug(f"[VOYAGER_SERVICE_CALL] Raw Response JSON: {json.dumps(service_results)}")
            except json.JSONDecodeError:
                logger.error(f"[VOYAGER_SERVICE_CALL] Failed to decode JSON response. Raw text: {response.text[:500]}...")
                service_results = {} # Set to empty dict on decode error
                # --- Ensure raw_response_data is defined even on error ---
                raw_response_data = {"error": "Failed to decode JSON response", "raw_text": raw_response_text[:500]}
                # -------------------------------------------------------

            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            search_results = service_results.get("results", [])
            logger.debug(f"[VOYAGER_SEARCH_WEB] Extracted search_results (type: {type(search_results)}): {search_results}") # Log extracted results
            if not isinstance(search_results, list):
                logger.warning(f"Voyager service response for 'results' was not a list: {type(search_results)}")
                search_results = [] # Default to empty list if type is wrong

            execution_time = time.time() - start_time
            logger.info(f"Web search via Voyager service completed in {execution_time:.2f}s for query: {query}. Found {len(search_results)} results.")

            return {
                "status": "success",
                "query": query,
                "enhanced_query_used": enhanced_query if enhanced_query != query else None,
                "results": search_results,
                "response_data": raw_response_data, # Use the stored variable
                "metadata": {
                    "execution_time": execution_time,
                    "total_results": len(search_results),
                    "strategy": strategy.model_dump() if hasattr(strategy, "model_dump") else vars(strategy),
                    "service_response_metadata": service_results.get("metadata", {}), # Still get metadata from parsed results
                    "minion": "voyager"
                }
            }

        except httpx.RequestError as req_err:
            logger.error(f"[VOYAGER_SEARCH_WEB] HTTP Request Error: {req_err}", exc_info=True) # Added exc_info
            error_msg = f"Error calling Voyager service: {req_err}"
            logger.error(error_msg)
            error_traceback = traceback.format_exc()
            return {
                "status": "error",
                "query": query,
                "results": [],
                "error": f"Network error contacting search service: {req_err}",
                "error_type": "service_connection_error",
                "attempted_operation": "search_web",
                "metadata": {"execution_time": time.time() - start_time, "traceback": error_traceback, "minion": "voyager"}
            }
        except httpx.HTTPStatusError as status_err:
            logger.error(f"[VOYAGER_SEARCH_WEB] HTTP Status Error: {status_err.response.status_code}", exc_info=True) # Added exc_info
            error_msg = f"Voyager service returned error status {status_err.response.status_code}: {status_err.response.text}"
            logger.error(error_msg)
            error_traceback = traceback.format_exc()
            return {
                "status": "error",
                "query": query,
                "results": [],
                "error": f"Search service error ({status_err.response.status_code}): {status_err.response.text[:200]}...", # Limit error text length
                "error_type": "service_error",
                "attempted_operation": "search_web",
                "metadata": {"execution_time": time.time() - start_time, "status_code": status_err.response.status_code, "traceback": error_traceback, "minion": "voyager"}
            }
        except Exception as e:
            logger.error(f"[VOYAGER_SEARCH_WEB] Unexpected Error: {e}", exc_info=True) # Added exc_info
            error_msg = f"Unexpected error during web search: {str(e)}"
            logger.error(error_msg)
            error_traceback = traceback.format_exc()
            return {
                "status": "error",
                "query": query,
                "results": [],
                "error": str(e),
                "error_type": type(e).__name__,
                "attempted_operation": "search_web",
                "metadata": {"execution_time": time.time() - start_time, "traceback": error_traceback, "minion": "voyager"}
            }

    async def scrape_url(self, url: str, cache_policy: Dict[str, Any] = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Scrape content from a specific URL"""
        logger.info(f"[VOYAGER] Entering scrape_url method for URL: {url}") # Added Log
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
        logger.info("[VOYAGER] Entering search_and_analyze method.") # Added Log
        start_time = time.time()

        # --- Ensure Query Exists (Checked in execute, but double-check defensively) ---
        query = params.get("query")
        if not query:
            logger.error("[VOYAGER_SEARCH_ANALYZE] Query parameter missing or empty.")
            return WebResponse(
                status="error",
                data={},
                error="Missing required parameter: query",
                error_type="missing_parameter",
                attempted_operation="search_and_analyze",
                confidence=0.0,
                analysis_metadata={"execution_time": time.time() - start_time}
            )
        # --- End Query Check ---

        try:
            # Extract parameters defensively
            max_results = params.get("max_results", 5)
            strategy_params = params.get("strategy", {})
            full_context = params.get("context", {}) # Get the full context dict passed from execute

            # Default strategy if params are empty or invalid
            try:
                strategy = SearchStrategy(**strategy_params)
            except Exception:
                logger.warning(f"Invalid strategy params: {strategy_params}. Falling back to default SearchStrategy.", exc_info=True)
                strategy = SearchStrategy()

            # --- Build a focused context dict for prompt creation (Defensive) ---
            context_for_prompt = {
                # Use .get() for all potentially missing keys
                "user_id": full_context.get("user_id"),
                "id": full_context.get("id"), # Keep fallback
                "user_name": full_context.get("user_name"),
                "preferences": full_context.get("preferences"), # Already defaults to {} in create_prompt_context if missing here
                "recent_memories": full_context.get("recent_memories"), # Defaults to [] in create_prompt_context
                "relevant_memories": full_context.get("relevant_memories"), # Defaults to []
                "timestamp": full_context.get("timestamp"), # Defaults to now() if missing
                "system": full_context.get("system"), # Defaults to {} if missing
                "location": full_context.get("location"), # Pass optional location
                # Add other known optional keys defensively if needed later
                # "user_profile": full_context.get("user_profile"),
                # "metadata": full_context.get("metadata"),
            }
            # Filter out None values before passing to create_prompt_context
            context_for_prompt = {k: v for k, v in context_for_prompt.items() if v is not None}
            logger.debug(f"[SEARCH_AND_ANALYZE] Filtered keys in context_for_prompt: {list(context_for_prompt.keys())}")
            # --- End focused context ---

            # Create search-specific data for prompt context
            search_data = {
                "query": query,
                "max_results": max_results,
                "operation": "search",
                "strategy": strategy # Pass the strategy object/dict
            }

            # Create prompt context (method already refactored to handle missing keys/instantiation errors)
            try:
                 prompt_context = self.create_prompt_context(context_for_prompt, search_data)
            except Exception as prompt_ctx_err:
                 logger.error(f"Error creating prompt context: {prompt_ctx_err}", exc_info=True)
                 # Proceed without rich prompt context if creation fails, but log it
                 prompt_context = None # Or create a minimal default context

            # Step 1: Perform web search (pass full_context defensively)
            # search_web now handles query enhancement internally and defensively
            search_result = await self.search_web(query, strategy, full_context or {}) # Pass empty dict if None

            search_results_list = search_result.get("results")
            if search_result.get("status") == "error" or not isinstance(search_results_list, list) or not search_results_list:
                error_msg = search_result.get("error")
                if not error_msg and not search_results_list:
                    error_msg = "No results found or search failed."
                elif not error_msg:
                    error_msg = "Search failed with an unknown error."
                logger.warning(f"Web search step failed or returned no results. Error: {error_msg}")
                return WebResponse(
                    status="error",
                    data={"query": query, "results": []},
                    error=error_msg,
                    error_type=search_result.get("error_type"),
                    attempted_operation="search_web",
                    confidence=0.0,
                    analysis_metadata={"execution_time": time.time() - start_time}
                )

            # Step 2: Analyze the results (pass full_context defensively)
            # Ensure analysis_agent exists before calling
            analysis = {} # Default empty analysis
            if hasattr(self, 'analysis_agent') and self.analysis_agent:
                analysis = await self.analyze_search_results(
                    search_results_list[:max_results], # Use the actual list
                    query,
                    full_context or {} # Pass empty dict if None
                )
            else:
                logger.warning("Analysis agent not available. Skipping analysis step.")
                analysis = {
                    "relevant_results": search_results_list[:max_results],
                    "error": "Analysis agent not configured."
                } # Provide basic structure even if skipped

            # Step 3: Scrape key sources for more detailed information (Optional step)
            scraped_content = []
            # Use analysis results if available, otherwise fallback to raw search results
            sources_to_consider = analysis.get("key_sources") if analysis.get("key_sources") else search_results_list
            urls_to_scrape = [source.get("url") for source in sources_to_consider[:3] if source.get("url")] # Limit to top 3 valid URLs

            if urls_to_scrape:
                logger.info(f"Attempting to scrape top {len(urls_to_scrape)} URLs: {urls_to_scrape}")
                scrape_tasks = []
                for url in urls_to_scrape:
                    # Pass full_context defensively
                    scrape_tasks.append(self.scrape_url(url, None, full_context or {}))

                scrape_results = await asyncio.gather(*scrape_tasks, return_exceptions=True)

                for i, scrape_result in enumerate(scrape_results):
                    source_url = urls_to_scrape[i]
                    if isinstance(scrape_result, Exception):
                        logger.error(f"Exception during scraping {source_url}: {scrape_result}", exc_info=scrape_result)
                        continue # Skip failed scrapes

                    if scrape_result and scrape_result.get("status") == "success":
                        # Get credibility assessment (optional, depends on context)
                        credibility = {"score": 0.5, "error": "Evaluation skipped or failed"} # Default
                        try:
                            # Pass full_context defensively
                            credibility = await self.evaluate_source_credibility(
                                source_url,
                                scrape_result.get("content", {}),
                                full_context or {}
                            )
                        except Exception as cred_err:
                            logger.error(f"Error evaluating credibility for {source_url}: {cred_err}", exc_info=True)

                        scraped_content.append({
                            "url": source_url,
                            "content": scrape_result.get("content"),
                            "credibility": credibility
                        })
                    elif scrape_result:
                         logger.warning(f"Scraping failed for {source_url}: {scrape_result.get('error')}")

            execution_time = time.time() - start_time
            logger.info(f"Search and analysis completed in {execution_time:.2f}s")

            # Construct the response using analysis results if available
            final_results = analysis.get("relevant_results") if analysis.get("relevant_results") else search_results_list[:max_results]

            return WebResponse(
                status="success",
                data={
                    "query": query,
                    "results": final_results,
                    "categories": analysis.get("categories", []),
                    "detailed_content": scraped_content,
                    "recommendations": analysis.get("recommendations", [])
                },
                sources=[{
                    "url": source.get("url"),
                    "title": source.get("title"),
                    "type": source.get("source_type", "website")
                } for source in final_results], # Base sources on final results used
                confidence=0.8, # Base confidence, could be adjusted based on analysis/credibility
                analysis_metadata={
                    "execution_time": execution_time,
                    "sources_scraped": len(scraped_content),
                    "total_results_found": len(search_results_list), # Original count from search
                    "analysis_performed": bool(hasattr(self, 'analysis_agent') and self.analysis_agent),
                    "analysis_error": analysis.get("error")
                }
            )

        except Exception as e:
            logger.error(f"Error in search_and_analyze: {str(e)}", exc_info=True) # Log full traceback
            execution_time = time.time() - start_time
            return WebResponse(
                status="error",
                data={
                    "query": params.get("query", "[Query unavailable due to error]"),
                },
                error=str(e),
                error_type=type(e).__name__,
                attempted_operation="search_and_analyze",
                confidence=0.0,
                analysis_metadata={
                    "execution_time": execution_time,
                    "success": False,
                    "traceback_summary": traceback.format_exc().split("\n")[-3:] # Summary
                }
            )

    async def execute(self, params: Dict[str, Any], context: RunContext) -> Dict[str, Any]:
        """Execute web research operations"""
        operation = params.get("operation", "search")
        # Use pprint for better readability of complex dicts
        params_repr = pprint.pformat(params, indent=2, width=120)
        context_deps_repr = pprint.pformat(getattr(context, 'deps', {}), indent=2, width=120)
        logger.info(f"[VOYAGER] Entering execute method. Operation: '{operation}'")
        logger.debug(f"[VOYAGER_EXECUTE] Received params:\n{params_repr}")
        logger.debug(f"[VOYAGER_EXECUTE] Received context.deps:\n{context_deps_repr}")
        start_time = time.time()

        # --- Check for essential 'query' parameter ---
        user_query = params.get("query")
        if not user_query:
             logger.error("[VOYAGER_EXECUTE] Missing required parameter: 'query'")
             return {
                 "status": "error",
                 "error": "Missing required parameter: 'query'",
                 "error_type": "missing_parameter",
                 "attempted_operation": operation,
                 "metadata": {
                     "execution_time": time.time() - start_time,
                     "minion": "voyager"
                 }
             }
        # --- End Query Check ---

        def extract_location_from_query(query: str) -> Optional[str]:
            # Simple regex for city/state/country in query (improve as needed)
            # e.g. "weather in seattle", "weather for new york", "weather in Paris, France"
            match = re.search(r"(?:in|for) ([A-Za-z ,]+)", query, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Remove trailing question mark or period
                location = re.sub(r'[?.!]$', '', location)
                return location
            return None

        try:
            run_context = context.deps if hasattr(context, "deps") else {}
            # --- Defensive Location Handling ---
            # user_query is guaranteed to exist here due to the check above
            location_from_query = extract_location_from_query(user_query)
            location_from_profile = run_context.get("user_profile", {}).get("location")
            location_from_browser = run_context.get("metadata", {}).get("browser", {}).get("location")

            final_location = None
            if location_from_query:
                final_location = location_from_query
                logger.info(f"[VOYAGER] Using location from user query: '{final_location}' (takes precedence)")
            elif location_from_profile:
                final_location = location_from_profile # This could be a dict or str, handle appropriately downstream
                logger.info(f"[VOYAGER] Using location from user profile: '{final_location}'")
            elif location_from_browser:
                final_location = location_from_browser
                logger.info(f"[VOYAGER] Using location from browser: '{final_location}'")
            else:
                logger.info("[VOYAGER] No location found in query, profile, or browser context.")

            # Inject location into params only if found and relevant (e.g., for weather queries)
            # Let downstream functions decide if/how to use params["location"]
            if final_location:
                params["location"] = final_location
                logger.info(f"[VOYAGER] Added location '{final_location}' to params for potential downstream use.")
            # --- End Defensive Location Handling ---

            # Add context to params (pass the raw deps dict)
            params["context"] = run_context

            if operation == "search":
                response = await self.search_and_analyze(params)
                final_result = response.model_dump() if hasattr(response, 'model_dump') else response
                return final_result

            elif operation == "scrape":
                logger.info("[VOYAGER_EXECUTE] Executing 'scrape' operation branch.")
                url = params.get("url")
                if not url:
                    logger.error("[VOYAGER] No URL provided for scraping.")
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
                logger.info(f"[VOYAGER] Scrape URL: {url}")
                scrape_result = await self.scrape_url(url, params.get("config"), run_context)
                scrape_result_repr = pprint.pformat(scrape_result, indent=2, width=120)
                logger.debug(f"[VOYAGER_EXECUTE / scrape] scrape_url result:\n{scrape_result_repr}")
                logger.info(f"[VOYAGER_EXECUTE] Returning result from 'scrape' operation. Status: {scrape_result.get('status')}")
                return scrape_result

            else:
                logger.error(f"[VOYAGER] Unsupported operation: {operation}")
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
            error_traceback = traceback.format_exc()
            logger.error(f"Traceback: {error_traceback}")
            final_error_result = {
                "status": "error",
                "error": str(e),
                "error_type": "voyager_exception",
                "attempted_operation": operation,
                "metadata": {
                    "operation": operation,
                    "error_traceback": error_traceback.split("\n")[-3:],
                    "execution_time": time.time() - start_time,
                    "minion": "voyager",
                    "parameters": {k: v for k, v in params.items() if k != "query"}
                }
            }
            logger.info("[VOYAGER_EXECUTE] Returning error result due to exception.")
            return final_error_result
    
    async def cleanup(self):
        """Clean up resources, close the httpx client."""
        if self.client:
            await self.client.aclose()
            logger.info("VoyagerMinion httpx client closed.")
            self.client = None
