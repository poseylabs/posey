from typing import Dict, Any, List, Optional
from pydantic_ai import RunContext, Agent
from pydantic import BaseModel, Field
from app.config import logger
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
from app.utils.ability_utils import use_ability
from datetime import datetime
import time
from app.minions.base import BaseMinion
import traceback
from sqlalchemy.ext.asyncio import AsyncSession

class ResearchStrategy(BaseModel):
    """Configuration for research strategy"""
    depth: str = Field(
        default="shallow",
        description="shallow, medium, or deep research depth"
    )
    time_range: str = Field(
        default="recent",
        description="Time range for research"
    )
    source_types: List[str] = Field(
        default=["academic", "news", "website"],
        description="Types of sources to include"
    )
    cross_reference: bool = Field(
        default=True,
        description="Whether to cross-reference information"
    )
    max_sources: int = Field(
        default=5,
        description="Maximum number of sources to analyze"
    )

class ResearchRequest(BaseModel):
    """Model for research requests"""
    query: str
    objective: str
    strategy: ResearchStrategy = Field(default_factory=ResearchStrategy)
    context: Dict[str, Any] = Field(default_factory=dict)

class ResearchResponse(BaseModel):
    """Model for research responses"""
    status: str
    findings: List[Dict[str, Any]]
    synthesis: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[Dict[str, Any]]
    gaps: List[str] = []
    next_steps: List[str] = []
    error: Optional[str] = None
    error_type: Optional[str] = None
    attempted_operation: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ResearchMinion(BaseMinion):
    """Research minion for conducting thorough research"""
    # Add type hints for agents
    planning_agent: Optional[Agent] = None
    analysis_agent: Optional[Agent] = None
    synthesis_agent: Optional[Agent] = None
    
    def create_prompt_context(self, context: Dict[str, Any], research_data: Dict[str, Any] = None) -> BasePromptContext:
        """Create a properly structured prompt context for research operations
        
        Args:
            context: The raw context dictionary
            research_data: Additional research-specific data to include in the context
            
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
            agent_capabilities=["research", "information_synthesis", "source_analysis"],
            **context.get("system", {})
        )
        
        # Add research-specific data to the appropriate context
        if research_data:
            # Add query-related info to user context
            if "query" in research_data:
                user_context.query = research_data["query"]
            if "objective" in research_data:
                user_context.objective = research_data["objective"]
                
            # Add research-specific fields to system context
            if "sources" in research_data:
                system_context.sources = research_data["sources"]
            if "analysis" in research_data:
                system_context.analysis = research_data["analysis"]
            if "strategy" in research_data:
                system_context.strategy = research_data["strategy"]
        
        # Return complete context
        return BasePromptContext(
            user=user_context,
            memory=memory_context,
            system=system_context
        )
    
    async def plan_research(self, query: str, objective: str, strategy: ResearchStrategy, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Plan the research approach based on query and objective"""
        start_time = time.time()
        context = context or {}
        
        try:
            # Create research-specific context data
            research_data = {
                "query": query,
                "objective": objective,
                "strategy": strategy.model_dump(),
                "current_operation": "research_planning"
            }
            
            # Create proper prompt context
            prompt_context = self.create_prompt_context(context, research_data)
            
            # Get task prompt from configuration with the structured context
            user_prompt = self.get_task_prompt(
                "research_planning",
                context=prompt_context,
                query=query,
                objective=objective,
                strategy=strategy.model_dump()
            )
            
            # Run the planning agent
            logger.info(f"Planning research for query: {query}")
            planning_result = await self.planning_agent.run(user_prompt)
            
            # Extract result
            if hasattr(planning_result, 'data'):
                plan = planning_result.data
            else:
                plan = {
                    "search_queries": [query],
                    "strategy": strategy.model_dump(),
                    "priority_sources": strategy.source_types
                }
            
            execution_time = time.time() - start_time
            logger.info(f"Research planning completed in {execution_time:.2f}s")
            
            return plan
            
        except Exception as e:
            logger.error(f"Error in research planning: {str(e)}")
            return {
                "search_queries": [query],
                "strategy": strategy.model_dump(),
                "priority_sources": strategy.source_types,
                "error": str(e)
            }
    
    async def gather_information(self, query: str, strategy: ResearchStrategy, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Gather information from various sources"""
        start_time = time.time()
        context = context or {}
        
        try:
            # First develop a research plan
            plan = await self.plan_research(query, "Gather comprehensive information", strategy, context)
            
            # Use search queries from the plan
            search_queries = plan.get("search_queries", [query])
            
            # Use voyager minion to search for information
            sources = []
            for search_query in search_queries[:3]:  # Limit to top 3 queries
                logger.info(f"Searching for: {search_query}")
                
                # Use ability_utils to call voyager
                search_result = await use_ability(
                    "internet_research",
                    {
                        "operation": "search",
                        "query": search_query,
                        "max_results": strategy.max_sources
                    }
                )
                
                if search_result and search_result.get("status") == "success":
                    new_sources = search_result.get("data", {}).get("sources", [])
                    logger.info(f"Found {len(new_sources)} sources for query: {search_query}")
                    sources.extend(new_sources)
                else:
                    logger.warning(f"Search failed for query: {search_query}")
            
            # Remove duplicates and limit to max_sources
            unique_sources = []
            urls_seen = set()
            for source in sources:
                url = source.get("url")
                if url and url not in urls_seen:
                    urls_seen.add(url)
                    unique_sources.append(source)
                    if len(unique_sources) >= strategy.max_sources:
                        break
            
            execution_time = time.time() - start_time
            logger.info(f"Information gathering completed in {execution_time:.2f}s, found {len(unique_sources)} sources")
            
            return unique_sources
            
        except Exception as e:
            logger.error(f"Error gathering information: {str(e)}")
            return []
    
    async def analyze_sources(self, sources: List[Dict[str, Any]], query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze gathered sources for relevance and credibility"""
        start_time = time.time()
        context = context or {}
        
        try:
            # Create research-specific context data
            research_data = {
                "query": query,
                "sources": sources,
                "current_operation": "source_analysis"
            }
            
            # Create proper prompt context
            prompt_context = self.create_prompt_context(context, research_data)
            
            # Get task prompt from configuration
            user_prompt = self.get_task_prompt(
                "source_analysis",
                context=prompt_context,
                sources=sources,
                query=query
            )
            
            # Run the analysis agent
            logger.info(f"Analyzing {len(sources)} sources")
            analysis_result = await self.analysis_agent.run(user_prompt)
            
            # Extract result
            if hasattr(analysis_result, 'data'):
                analysis = analysis_result.data
            else:
                analysis = {
                    "analyzed_sources": sources,
                    "credibility_scores": {},
                    "key_information": {}
                }
            
            execution_time = time.time() - start_time
            logger.info(f"Source analysis completed in {execution_time:.2f}s")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in source analysis: {str(e)}")
            return {
                "analyzed_sources": sources,
                "credibility_scores": {},
                "key_information": {},
                "error": str(e)
            }
    
    async def synthesize_findings(self, analysis: Dict[str, Any], query: str, objective: str, context: Dict[str, Any] = None) -> ResearchResponse:
        """Synthesize findings into a coherent response"""
        start_time = time.time()
        context = context or {}
        
        try:
            # Create research-specific context data
            research_data = {
                "query": query,
                "objective": objective,
                "analysis": analysis,
                "current_operation": "research_synthesis"
            }
            
            # Create proper prompt context
            prompt_context = self.create_prompt_context(context, research_data)
            
            # Get task prompt from configuration
            user_prompt = self.get_task_prompt(
                "research_synthesis",
                context=prompt_context,
                analysis=analysis,
                query=query,
                objective=objective
            )
            
            # Run the synthesis agent
            logger.info(f"Synthesizing research findings")
            synthesis_result = await self.synthesis_agent.run(user_prompt)
            
            # Extract result
            if isinstance(synthesis_result, ResearchResponse):
                response = synthesis_result
            elif hasattr(synthesis_result, 'data'):
                data = synthesis_result.data
                
                # Create a ResearchResponse from the data
                response = ResearchResponse(
                    status="success",
                    findings=data.get("findings", []),
                    synthesis=data.get("synthesis", "No synthesis available"),
                    confidence=data.get("confidence", 0.7),
                    sources=data.get("sources", []),
                    gaps=data.get("gaps", []),
                    next_steps=data.get("next_steps", []),
                    error=data.get("error"),
                    error_type=data.get("error_type"),
                    attempted_operation=data.get("attempted_operation"),
                    metadata=data.get("metadata", {})
                )
            else:
                # Create a default response
                response = ResearchResponse(
                    status="success",
                    findings=[{"content": "Limited information available"}],
                    synthesis="The research could not be synthesized properly.",
                    confidence=0.3,
                    sources=analysis.get("analyzed_sources", []),
                    gaps=["Research synthesis process failed"],
                    next_steps=["Retry with more specific query"],
                    error="Synthesis process failed",
                    error_type="research_synthesis_exception",
                    attempted_operation="research_synthesis",
                    metadata={}
                )
            
            execution_time = time.time() - start_time
            logger.info(f"Research synthesis completed in {execution_time:.2f}s with confidence: {response.confidence}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in research synthesis: {str(e)}")
            return ResearchResponse(
                status="error",
                findings=[],
                synthesis=f"Error during synthesis: {str(e)}",
                confidence=0.0,
                sources=[],
                gaps=["Synthesis process error"],
                next_steps=["Retry research with different parameters"],
                error=str(e),
                error_type="research_synthesis_exception",
                attempted_operation="research_synthesis",
                metadata={}
            )
    
    async def conduct_research(self, params: Dict[str, Any]) -> ResearchResponse:
        """Conduct full research process"""
        start_time = time.time()
        
        try:
            # Extract parameters
            query = params.get("query", "")
            objective = params.get("objective", "Gather comprehensive information")
            context = params.get("context", {})
            
            # Create strategy from parameters or defaults
            strategy_params = params.get("strategy", {})
            strategy = ResearchStrategy(**strategy_params)
            
            if not query:
                return ResearchResponse(
                    status="error",
                    findings=[],
                    synthesis="No query provided for research",
                    confidence=0.0,
                    sources=[],
                    error="No query provided for research",
                    error_type="research_planning_exception",
                    attempted_operation="research_planning",
                    metadata={}
                )
            
            # Step 1: Gather information from sources
            sources = await self.gather_information(query, strategy, context)
            
            if not sources:
                return ResearchResponse(
                    status="error",
                    findings=[],
                    synthesis=f"No sources found for query: {query}",
                    confidence=0.0,
                    sources=[],
                    gaps=["No information available"],
                    next_steps=["Try a different search query", "Expand search parameters"],
                    error="No sources found for query",
                    error_type="research_planning_exception",
                    attempted_operation="research_planning",
                    metadata={}
                )
            
            # Step 2: Analyze sources
            analysis = await self.analyze_sources(sources, query, context)
            
            # Step 3: Synthesize findings
            response = await self.synthesize_findings(analysis, query, objective, context)
            
            execution_time = time.time() - start_time
            logger.info(f"Research completed in {execution_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Error conducting research: {str(e)}")
            execution_time = time.time() - start_time
            logger.error(f"Research failed after {execution_time:.2f}s")
            
            return ResearchResponse(
                status="error",
                findings=[],
                synthesis=f"Research process error: {str(e)}",
                confidence=0.0,
                sources=[],
                gaps=["Process failed with error"],
                next_steps=["Retry with simplified query"],
                error=str(e),
                error_type="research_execution_exception",
                attempted_operation="research",
                metadata={
                    "error_traceback": traceback.format_exc().split("\n")[-3:],
                    "execution_time": execution_time,
                    "minion": "research",
                    "parameters": {k: v for k, v in params.items() if k != "query"}
                }
            )
    
    async def execute(self, params: Dict[str, Any], context: RunContext) -> Dict[str, Any]:
        """Execute research operations"""
        start_time = time.time()
        
        try:
            # Extract context from RunContext
            run_context = context.deps if hasattr(context, "deps") else {}
            
            # Add context to params
            params["context"] = run_context
            
            # Execute the research
            response = await self.conduct_research(params)
            return response.model_dump()
        except Exception as e:
            logger.error(f"Error in research minion execute: {str(e)}")

            error_traceback = traceback.format_exc()
            logger.error(f"Traceback: {error_traceback}")
            
            return {
                "status": "error",
                "error": str(e),
                "error_type": "research_execution_exception",
                "attempted_operation": "research",
                "findings": [],
                "synthesis": f"Error occurred during research: {str(e)}",
                "confidence": 0.0,
                "sources": [],
                "metadata": {
                    "error_traceback": error_traceback.split("\n")[-3:],
                    "execution_time": time.time() - start_time,
                    "minion": "research",
                    "parameters": {k: v for k, v in params.items() if k != "query"} # Exclude query to avoid leaking sensitive info
                }
            }
