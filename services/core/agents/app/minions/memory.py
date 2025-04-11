from typing import Dict, Any, List, Optional
from pydantic_ai import RunContext, Agent
from app.utils.memory_store import MemoryStore
from app.config import logger
from pydantic import BaseModel
from app.config.prompts import PromptLoader
from app.config.prompts.base import (
    generate_base_prompt,
    get_default_context,
    BasePromptContext,
    UserContext,
    MemoryContext,
    SystemContext
)
from app.config.defaults import LLM_CONFIG
from datetime import datetime
from app.abilities.memory import MemoryAbility
from app.minions.base import BaseMinion
import time
from uuid import uuid4
import os
import traceback
from app.config.settings import settings
import asyncio

# LangChain/LangGraph imports
from langchain_community.vectorstores import Qdrant
from langchain_core.vectorstores import VectorStore
from langchain_core.embeddings import Embeddings
from langchain.memory import VectorStoreRetrieverMemory
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.retrievers import TimeWeightedVectorStoreRetriever
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain.storage import LocalFileStore
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.http import models as rest
from qdrant_client.http.models import Filter, PointStruct

# Update imports for langchain-qdrant if available
try:
    from langchain_qdrant import Qdrant
    logger.info("Using langchain_qdrant for Qdrant integration")
except ImportError:
    from langchain_community.vectorstores import Qdrant
    logger.info("Using langchain_community for Qdrant integration (consider upgrading to langchain_qdrant)")

class MemoryRequest(BaseModel):
    """Model for memory operation requests"""
    operation: str  # store, retrieve, analyze, consolidate
    content: Optional[str] = None
    query: Optional[str] = None
    memory_ids: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None

class MemoryResponse(BaseModel):
    """Model for memory operation responses"""
    status: str = "success"
    operation: str
    result: Optional[Dict[str, Any]] = None
    memories: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class MemoryMinion(BaseMinion):
    """Memory management minion using LangGraph memory"""

    def __init__(self, db_conn):
        # Assign db connection *before* calling super().__init__ which calls setup()
        self.db = db_conn 
        # Note: BaseMinion.__init__() calls self._load_prompts() which requires PromptLoader
        super().__init__(
            name="memory",
            description="Analyze, store and retrieve memory information"
        )
        self.vector_store = None
        self.semantic_memory = None
        self.episodic_memory = None
        self.procedural_memory = None
        
    async def setup(self):
        """Initialize the memory minion with LangGraph memory components (async)"""
        logger.info("Initializing memory minion with LangGraph (async setup)")
        
        # Setup ability and store (keeping original components for compatibility)
        self.ability = MemoryAbility()
        self.store = MemoryStore()
        
        # Get base prompt with default context for initialization (keeping original prompt system)
        base_prompt = generate_base_prompt(get_default_context())
        
        # Override system prompt to include base prompt (keeping original prompt system)
        custom_system_prompt = "\n".join([
            base_prompt,  # Start with shared base prompt
            self.get_system_prompt()
        ])
        
        # Initialize embeddings - using the project's configured embedding model
        embedding_model = os.environ.get("EMBEDDING_MODEL", "thenlper/gte-large")
        cache_dir = os.environ.get("EMBEDDING_CACHE_DIR", "./models")
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            cache_folder=cache_dir,
        )
        logger.info(f"Initialized embeddings with model: {embedding_model}")
        
        # Initialize vector store for long-term memory
        try:
            # Use the shared Qdrant client from the db object
            # Check the underlying client directly first, like in health check
            if not self.db._qdrant_client:
                logger.warning("Qdrant client not found during MemoryMinion setup. Attempting connection...")
                connection_successful = await self.db.connect_qdrant() # Attempt connection
                # Check again after attempting connection
                if not connection_successful or not self.db._qdrant_client:
                    logger.error("Qdrant client connection failed after explicit attempt in MemoryMinion setup.")
                    # Match the error type raised by the property for consistency
                    raise RuntimeError("Qdrant not initialized even after connection attempt")
                else:
                    logger.info("Qdrant connection successful after explicit attempt in MemoryMinion setup.")

            # Now we are sure _qdrant_client exists and is an AsyncQdrantClient
            client: AsyncQdrantClient = self.db._qdrant_client
            collection_name = settings.QDRANT_COLLECTION_NAME # Use setting for consistency

            # Check if collection exists using the async client
            try:
                collections_response = await client.get_collections()
                collection_names = [c.name for c in collections_response.collections]
            except Exception as e:
                logger.error(f"Failed to get collections from Qdrant: {e}")
                raise RuntimeError("Failed to communicate with Qdrant to check collections") from e

            if collection_name not in collection_names:
                logger.info(f"Creating new Qdrant collection '{collection_name}'")
                # Embedding needs to happen synchronously for now
                try:
                    sample_embedding = self.embeddings.embed_query("Sample text")
                    vector_size = len(sample_embedding)
                except Exception as e:
                     logger.error(f"Failed to generate sample embedding: {e}")
                     raise RuntimeError("Failed to generate embedding for Qdrant collection creation") from e

                try:
                    await client.create_collection(
                        collection_name=collection_name,
                        vectors_config=rest.VectorParams(size=vector_size, distance=rest.Distance.COSINE)
                    )
                    logger.info(f"Created new Qdrant collection '{collection_name}' with vector size {vector_size}")
                except Exception as e:
                    logger.error(f"Failed to create Qdrant collection '{collection_name}': {e}")
                    # Check if collection was created concurrently
                    await asyncio.sleep(1) # Small delay before re-checking
                    try:
                        collections_response = await client.get_collections()
                        collection_names = [c.name for c in collections_response.collections]
                        if collection_name not in collection_names:
                             raise RuntimeError(f"Failed to create or find Qdrant collection '{collection_name}'") from e
                        else:
                            logger.warning(f"Qdrant collection '{collection_name}' found after initial creation error (possibly concurrent creation).")
                    except Exception as check_e:
                         raise RuntimeError(f"Failed to create Qdrant collection '{collection_name}' and failed subsequent check: {check_e}") from e
            else:
                 logger.info(f"Using existing Qdrant collection '{collection_name}'")

            # Initialize the vector store with the async client
            # NOTE: Switching to langchain_qdrant.Qdrant is highly recommended for async client usage.
            # Using langchain_community.vectorstores.Qdrant might lead to blocking calls or errors.
            # For now, we proceed with langchain_community, but be aware of potential issues.
            self.vector_store = Qdrant(
                client=client, # Pass the AsyncQdrantClient instance
                collection_name=collection_name,
                embeddings=self.embeddings
                # async_client=True # This argument likely doesn't exist in langchain_community version
            )
            logger.info(f"Successfully initialized Langchain Qdrant vector store wrapper for MemoryMinion with Async Client")

            # Initialize time-weighted retriever
            # NOTE: TimeWeightedVectorStoreRetriever is likely synchronous and may block.
            self.semantic_retriever = TimeWeightedVectorStoreRetriever(
                vectorstore=self.vector_store,
                search_kwargs={"k": 5},
                decay_rate=0.01,
                k=5
            )

            # Initialize semantic memory
            # NOTE: VectorStoreRetrieverMemory and as_retriever() are likely synchronous.
            self.semantic_memory = VectorStoreRetrieverMemory(
                retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
                memory_key="semantic_memory",
                input_key="query"
            )

            # Create file storage for episodic memory (sync is fine here)
            fs = LocalFileStore("./data/episodic_memory")

            # Initialize procedural memory
            # NOTE: VectorStoreRetrieverMemory and as_retriever() are likely synchronous.
            self.procedural_memory = VectorStoreRetrieverMemory(
                retriever=self.vector_store.as_retriever(
                    search_kwargs={"filter": {"memory_type": "procedural"}} # Qdrant filter format might differ
                ),
                memory_key="procedural_memory"
            )

            # Create agent
            self.agent = self.create_agent(result_type=MemoryResponse, model_key="memory")
            logger.info(f"Memory agent initialized with model: {LLM_CONFIG['memory']['model']}")

        except RuntimeError as re: # Catch the specific error raised earlier
             logger.critical(f"MemoryMinion Qdrant setup failed critically: {re}")
             raise # Re-raise critical errors
        except Exception as e:
            logger.error(f"Failed during MemoryMinion setup: {type(e).__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            # Depending on the error, decide whether to raise or allow degraded functionality
            raise RuntimeError(f"Memory Minion setup failed: {e}") from e
        
    def create_prompt_context(self, context: Dict[str, Any], extra_memory_data: Dict[str, Any] = None) -> BasePromptContext:
        """Create a prompt context object for memory operations
        
        Args:
            context: The raw context dictionary
            extra_memory_data: Additional memory data to include in the MemoryContext
            
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
        
        # Create memory context with memory types from LangGraph
        memory_data = {
            "memory_types": {
                "semantic": "Factual knowledge and concepts",
                "episodic": "Personal experiences and events",
                "procedural": "How to perform tasks and actions"
            }
        }
        
        # Add any extra memory data
        if extra_memory_data:
            memory_data.update(extra_memory_data)
        
        memory_context = MemoryContext(
            recent_memories=context.get("recent_memories", []),
            relevant_memories=context.get("relevant_memories", []),
            **memory_data
        )
        
        # Create system context
        system_context = SystemContext(
            current_time=datetime.now().isoformat(),
            agent_capabilities=["memory_storage", "memory_retrieval", "memory_analysis"],
            **context.get("system", {})
        )
        
        # Return complete context
        return BasePromptContext(
            user=user_context,
            memory=memory_context,
            system=system_context
        )
    
    async def store_memory(self, content: str, context: Dict[str, Any]) -> MemoryResponse:
        """Store a new memory using LangGraph memory concepts (async)"""
        start_time = time.time()
        if not self.vector_store:
             return MemoryResponse(status="error", operation="store", error="Vector store not initialized")

        try:
            user_id = context.get("user_id", "anonymous")
            memory_type = self.classify_memory_type(content)
            memory_id = str(uuid4())

            doc = Document(
                page_content=content,
                metadata={
                    "user_id": user_id,
                    "agent_id": "memory",
                    "timestamp": datetime.now().isoformat(),
                    "memory_type": memory_type,
                    "id": memory_id # Use the generated UUID as ID
                    # Ensure metadata keys match Qdrant indexing/filtering needs
                }
            )

            # Store in vector store
            # NOTE: add_documents in langchain_community.Qdrant is SYNC.
            # This will block the event loop. For true async, use client.upsert directly
            # or switch to langchain_qdrant which might have an async version.
            try:
                # Example using client directly (preferred for async):
                # point = PointStruct(
                #     id=memory_id,
                #     vector=self.embeddings.embed_query(content), # Embed synchronously for now
                #     payload=doc.metadata
                # )
                # await self.db._qdrant_client.upsert(
                #     collection_name=settings.QDRANT_COLLECTION_NAME,
                #     points=[point],
                #     wait=True # Or False for fire-and-forget
                # )
                # logger.debug(f"Upserted memory {memory_id} directly via async client.")

                # Using Langchain wrapper (potential blocking call):
                ids_added = self.vector_store.add_documents([doc], ids=[memory_id])
                logger.debug(f"Added document via Langchain wrapper: {ids_added}")

            except Exception as store_e:
                 logger.error(f"Failed to add document to Qdrant: {store_e}")
                 return MemoryResponse(status="error", operation="store", error=f"Failed to store memory in vector database: {store_e}")

            # Create memory-specific context for prompt
            memory_data = {
                "current_operation": "store",
                "memory_type": memory_type,
                "memory_id": memory_id
            }
            
            # Create proper prompt context
            prompt_context = self.create_prompt_context(context, memory_data)
            
            # Get task prompt from configuration with proper context
            user_prompt = self.get_task_prompt(
                "store_memory",
                context=prompt_context,
                content=content,
                current_time=datetime.now().isoformat(),
                memory_type=memory_type
            )
            
            execution_time = time.time() - start_time
            logger.info(f"Memory storage completed in {execution_time:.2f}s for ID {memory_id}")
            
            return MemoryResponse(
                operation="store",
                result={
                    "memory_id": memory_id,
                    "content": content[:100] + "..." if len(content) > 100 else content,
                    "memory_type": memory_type,
                    "execution_time": execution_time
                }
            )

        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            logger.error(traceback.format_exc())
            execution_time = time.time() - start_time

            return MemoryResponse(
                status="error",
                operation="store",
                error=str(e)
            )
    
    def classify_memory_type(self, content: str) -> str:
        """Classify memory type based on content
        
        This is a simple implementation that could be enhanced with LLM classification
        """
        # Simple keyword-based classification
        if any(word in content.lower() for word in ["do", "steps", "procedure", "how to"]):
            return "procedural"
        elif any(word in content.lower() for word in ["happened", "occurred", "experienced", "event"]):
            return "episodic"
        else:
            return "semantic"
    
    async def retrieve_memory(self, params: Dict[str, Any], context: Dict[str, Any]) -> MemoryResponse:
        """Retrieve memories based on query or filters using LangGraph memory (async)"""
        start_time = time.time()
        if not self.vector_store or not self.db._qdrant_client:
             return MemoryResponse(status="error", operation="retrieve", error="Vector store or Qdrant client not initialized")

        try:
            query = params.get("query", "")
            filters_in = params.get("filters", {})
            k = params.get("k", 5) # Allow specifying number of results

            if not query and not filters_in:
                return MemoryResponse(
                    status="error", operation="retrieve", error="No query or filters provided"
                )

            # Build Qdrant filter from input filters
            qdrant_filter_conditions = []
            for key, value in filters_in.items():
                 # Adapt key names if necessary (e.g., context -> metadata.context)
                 # Assuming direct mapping for now, might need 'metadata.' prefix
                 qdrant_filter_conditions.append(
                     rest.FieldCondition(key=f"metadata.{key}", match=rest.MatchValue(value=value))
                 )

            # Add user_id from context if not explicitly filtered
            user_id = context.get("user_id")
            if user_id and "user_id" not in filters_in:
                 qdrant_filter_conditions.append(
                     rest.FieldCondition(key="metadata.user_id", match=rest.MatchValue(value=user_id))
                 )

            qdrant_filter = rest.Filter(must=qdrant_filter_conditions) if qdrant_filter_conditions else None
            logger.debug(f"Constructed Qdrant filter: {qdrant_filter}")

            # Retrieve memories using the async client directly for proper async/filtering
            retrieved_points = []
            if query:
                try:
                     # Embed query synchronously for now
                     query_vector = self.embeddings.embed_query(query)
                     # Use async search
                     retrieved_points = await self.db._qdrant_client.search(
                         collection_name=settings.QDRANT_COLLECTION_NAME,
                         query_vector=query_vector,
                         query_filter=qdrant_filter,
                         limit=k,
                         with_payload=True, # Include metadata
                         with_vectors=False # Don't need vectors back
                     )
                     logger.debug(f"Qdrant search returned {len(retrieved_points)} points for query '{query}'")
                except Exception as search_e:
                     logger.error(f"Qdrant search failed: {search_e}")
                     return MemoryResponse(status="error", operation="retrieve", error=f"Vector search failed: {search_e}")
            elif qdrant_filter:
                 # If no query but filters exist, use scroll API (or search with dummy vector)
                 # Scroll is better for pure filtering without semantic search
                 logger.warning("Retrieval without query, using filter only. Consider Qdrant scroll API for efficiency.")
                 try:
                      # Fallback to search with a dummy vector (less efficient than scroll)
                      dummy_vector = [0.0] * len(self.embeddings.embed_query("dummy")) # Get correct dimension
                      retrieved_points = await self.db._qdrant_client.search(
                          collection_name=settings.QDRANT_COLLECTION_NAME,
                          query_vector=dummy_vector, # Required for search
                          query_filter=qdrant_filter,
                          limit=k,
                          with_payload=True,
                          with_vectors=False
                      )
                      # Alternative: Implement scroll
                      # scroll_response, _ = await self.db._qdrant_client.scroll(
                      #     collection_name=settings.QDRANT_COLLECTION_NAME,
                      #     scroll_filter=qdrant_filter,
                      #     limit=k,
                      #     with_payload=True,
                      #     with_vectors=False
                      # )
                      # retrieved_points = scroll_response
                      logger.debug(f"Qdrant filter-only search returned {len(retrieved_points)} points")
                 except Exception as filter_search_e:
                      logger.error(f"Qdrant filter-only search failed: {filter_search_e}")
                      return MemoryResponse(status="error", operation="retrieve", error=f"Vector filter search failed: {filter_search_e}")

            # Convert Qdrant points (ScoredPoint) to Langchain Document-like structure for compatibility
            memories = []
            for point in retrieved_points:
                # Qdrant ScoredPoint has id, score, payload
                metadata = point.payload if point.payload else {}
                # Add ID back into metadata if it's not already there (depends on how data was stored)
                if 'id' not in metadata:
                     metadata['id'] = point.id

                memories.append({
                    # Assuming content is stored in a 'page_content' field in the payload
                    "content": metadata.get("page_content", "Error: Content not found in payload"),
                    "score": point.score,
                    "metadata": metadata # Use the whole payload as metadata
                })
                # Remove 'page_content' from metadata dict if it exists and you only want it at top level
                if "page_content" in metadata:
                     del metadata["page_content"]

            # Create memory-specific context for prompt
            memory_data = {
                "current_operation": "retrieve",
                "query": query,
                "filters": filters_in,
                "retrieved_memories": memories
            }
            
            # Create proper prompt context
            prompt_context = self.create_prompt_context(context, memory_data)
            
            # Get task prompt from configuration with proper context
            user_prompt = self.get_task_prompt(
                "retrieve_memory",
                context=prompt_context,
                query=query,
                filters=filters_in,
                memory_count=len(memories)
            )
            
            execution_time = time.time() - start_time
            logger.info(f"Memory retrieval completed in {execution_time:.2f}s, found {len(memories)} memories")
            
            return MemoryResponse(
                operation="retrieve",
                memories=memories,
                result={
                    "count": len(memories),
                    "query": query,
                    "filters": filters_in,
                    "execution_time": execution_time
                }
            )

        except Exception as e:
            logger.error(f"Error retrieving memories: {str(e)}")
            logger.error(traceback.format_exc())
            execution_time = time.time() - start_time

            return MemoryResponse(
                status="error",
                operation="retrieve",
                error=str(e)
            )
    
    async def analyze_memory(self, params: Dict[str, Any], context: Dict[str, Any]) -> MemoryResponse:
        """Analyze memories for patterns, insights, or specific information (async)"""
        start_time = time.time()
        if not self.vector_store or not self.db._qdrant_client:
             return MemoryResponse(status="error", operation="analyze", error="Vector store or Qdrant client not initialized")

        try:
            memory_ids = params.get("memory_ids", [])
            query = params.get("query", "") # Analysis query/instruction

            if not memory_ids and not query:
                return MemoryResponse(status="error", operation="analyze", error="No memory_ids or query provided")

            memories_to_analyze = []

            # 1. Retrieve memories by ID if provided
            if memory_ids:
                try:
                     # Use async client retrieve by IDs
                     points = await self.db._qdrant_client.retrieve(
                         collection_name=settings.QDRANT_COLLECTION_NAME,
                         ids=memory_ids,
                         with_payload=True,
                         with_vectors=False
                     )
                     for point in points:
                          metadata = point.payload if point.payload else {}
                          memories_to_analyze.append({
                              "content": metadata.get("page_content", "Error: Content not found"),
                              "id": point.id,
                              "timestamp": metadata.get("timestamp"),
                              "memory_type": metadata.get("memory_type"),
                              # Include other relevant metadata if needed
                          })
                     logger.debug(f"Retrieved {len(points)} memories by ID for analysis.")
                except Exception as retrieve_e:
                     logger.error(f"Failed to retrieve memories by ID for analysis: {retrieve_e}")
                     # Decide whether to continue without these memories or fail
                     return MemoryResponse(status="error", operation="analyze", error=f"Failed to retrieve memories by ID: {retrieve_e}")

            # 2. If no IDs or retrieval failed, and a query exists, retrieve relevant memories via search
            if not memories_to_analyze and query:
                 logger.info(f"No specific IDs provided or retrieved, searching relevant memories for analysis query: '{query}'")
                 # Use the existing retrieve_memory method (which now uses async client directly)
                 retrieve_params = {"query": query, "k": 10} # Retrieve more memories for analysis context
                 retrieve_response = await self.retrieve_memory(retrieve_params, context)
                 if retrieve_response.status == "success" and retrieve_response.memories:
                     memories_to_analyze = retrieve_response.memories # Use the retrieved memories
                     logger.debug(f"Retrieved {len(memories_to_analyze)} relevant memories via search for analysis.")
                 else:
                     logger.warning(f"Memory search for analysis query failed or returned no results. Status: {retrieve_response.status}, Error: {retrieve_response.error}")
                     # Continue analysis with potentially empty list if needed, or error out

            if not memories_to_analyze:
                return MemoryResponse(
                    status="error", operation="analyze", error="No memories found or retrieved to analyze"
                )

            # Prepare context for the LLM analysis call
            analysis_prompt_context = self.create_prompt_context(context, {
                "current_operation": "analyze",
                "analysis_query": query,
                "memories_to_analyze": [ # Send simplified list to LLM
                     {k: v for k, v in m.items() if k != 'metadata'} # Exclude raw metadata initially
                     for m in memories_to_analyze
                ],
                "memory_types_present": list(set(m.get("memory_type", "unknown") for m in memories_to_analyze))
            })

            # Get the analysis task prompt
            # Ensure the prompt template expects 'analysis_query' and 'memories'
            analysis_user_prompt = self.get_task_prompt(
                "analyze_memory",
                context=analysis_prompt_context,
                memories=[m['content'] for m in memories_to_analyze], # Pass content list
                query=query,
                memory_count=len(memories_to_analyze)
            )

            # Call the agent to perform the analysis
            logger.info(f"Analyzing {len(memories_to_analyze)} memories with query: '{query}'")
            # Assuming self.agent.run is async
            analysis_result_raw = await self.agent.run(analysis_user_prompt)

            execution_time = time.time() - start_time

            # Process the LLM response
            if isinstance(analysis_result_raw, MemoryResponse):
                 analysis_response = analysis_result_raw
                 # Add execution time if not already present
                 if analysis_response.result and "execution_time" not in analysis_response.result:
                      analysis_response.result["execution_time"] = execution_time
                 elif not analysis_response.result:
                      analysis_response.result = {"execution_time": execution_time}

            elif isinstance(analysis_result_raw, dict): # Handle raw dict response
                 analysis_response = MemoryResponse(
                     operation="analyze",
                     result={**analysis_result_raw, "execution_time": execution_time}
                 )
            elif isinstance(analysis_result_raw, str): # Handle simple string response
                 analysis_response = MemoryResponse(
                     operation="analyze",
                     result={
                         "analysis_summary": analysis_result_raw,
                         "memory_count": len(memories_to_analyze),
                         "execution_time": execution_time
                     }
                 )
            else: # Fallback for unexpected types
                logger.warning(f"Unexpected analysis result type: {type(analysis_result_raw)}. Creating default response.")
                analysis_response = MemoryResponse(
                    operation="analyze",
                    result={
                        "raw_output": str(analysis_result_raw),
                        "insights": "Analysis failed or returned unexpected format.",
                        "memory_count": len(memories_to_analyze),
                        "execution_time": execution_time
                    }
                )

            analysis_response.operation = "analyze" # Ensure operation is set correctly
            logger.info(f"Memory analysis completed in {execution_time:.2f}s")
            return analysis_response

        except Exception as e:
            logger.error(f"Error analyzing memories: {str(e)}")
            logger.error(traceback.format_exc())
            execution_time = time.time() - start_time

            return MemoryResponse(
                status="error",
                operation="analyze",
                error=str(e)
            )
    
    async def search_recent(
        self,
        user_id: str,
        limit: int = 5,
        memory_type: Optional[str] = None,
        context_filter: Optional[str] = None, # Renamed from 'context' for clarity
        include_conversation: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most recent memories for a user using Qdrant directly (async).
        Memories are primarily sorted by a 'timestamp' field in the metadata.
        """
        if not self.db._qdrant_client:
             logger.error("Qdrant client not available for search_recent")
             return []

        try:
            logger.info(f"Retrieving {limit} recent memories for user {user_id}")

            # Build filter conditions
            filter_conditions = [
                rest.FieldCondition(key="metadata.user_id", match=rest.MatchValue(value=user_id))
            ]
            if memory_type:
                filter_conditions.append(
                    rest.FieldCondition(key="metadata.memory_type", match=rest.MatchValue(value=memory_type))
                )
            if context_filter:
                 filter_conditions.append(
                     rest.FieldCondition(key="metadata.context_type", match=rest.MatchValue(value=context_filter))
                 )
            # Add conversation filter if requested and no specific context filter provided
            if include_conversation and not context_filter:
                 # This logic might need refinement. Do we want *only* conversation,
                 # or conversation *in addition* to other types if memory_type isn't specified?
                 # Assuming for now: if include_conversation=True and no specific context,
                 # we don't add a context_type filter, allowing all contexts (incl. conversation).
                 # If you *only* want conversation when include_conversation=True, add the filter:
                 # filter_conditions.append(
                 #    rest.FieldCondition(key="metadata.context_type", match=rest.MatchValue(value="conversation"))
                 # )
                 pass # No extra filter needed if we want all contexts including conversation

            qdrant_filter = rest.Filter(must=filter_conditions)

            # Retrieve using scroll API, ordered by timestamp descending
            # NOTE: Requires the 'timestamp' field in metadata to be indexed appropriately in Qdrant
            #       and ideally be of a type that supports ordering (e.g., ISO format string, integer timestamp).
            try:
                scroll_response, _ = await self.db._qdrant_client.scroll(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    scroll_filter=qdrant_filter,
                    limit=limit, # Fetch the exact limit needed
                    order_by=rest.OrderBy(key="metadata.timestamp", direction=rest.Direction.DESC),
                    with_payload=True,
                    with_vectors=False
                )
                retrieved_points = scroll_response
                logger.debug(f"Qdrant scroll for recent memories returned {len(retrieved_points)} points.")

            except Exception as scroll_e:
                 # Qdrant might raise error if order_by field isn't indexed correctly or doesn't exist
                 logger.error(f"Qdrant scroll failed (potentially ORDER BY issue on 'metadata.timestamp'): {scroll_e}")
                 # Fallback: Retrieve more via search and sort manually (less efficient)
                 logger.warning("Falling back to less efficient search+sort for recent memories.")
                 try:
                     # Search requires a vector; use a dummy one
                      dummy_vector = [0.0] * len(self.embeddings.embed_query("dummy"))
                      search_results = await self.db._qdrant_client.search(
                          collection_name=settings.QDRANT_COLLECTION_NAME,
                          query_vector=dummy_vector,
                          query_filter=qdrant_filter,
                          limit=limit * 2, # Get more to sort
                          with_payload=True,
                          with_vectors=False
                      )
                      retrieved_points = search_results # Use search results instead
                 except Exception as fallback_e:
                      logger.error(f"Fallback search also failed: {fallback_e}")
                      return [] # Give up if both fail

            # Convert points to the desired dictionary format
            memories = []
            for point in retrieved_points:
                 metadata = point.payload if point.payload else {}
                 # Add ID back if needed
                 if 'id' not in metadata:
                     metadata['id'] = point.id

                 memories.append({
                     "content": metadata.get("page_content", "Error: Content not found"),
                     "metadata": metadata # Keep the full metadata dict
                 })
                 # Clean up metadata dict if content was pulled out
                 if "page_content" in metadata:
                     del metadata["page_content"]

            # If fallback search was used, sort manually now
            if 'search_results' in locals(): # Check if fallback occurred
                memories.sort(
                    key=lambda x: x.get("metadata", {}).get("timestamp", ""),
                    reverse=True
                )
                memories = memories[:limit] # Apply limit after sorting

            logger.info(f"Retrieved {len(memories)} recent memories for user {user_id}")
            if not memories:
                logger.warning("No recent memories found for this user/filter combination.")

            return memories

        except Exception as e:
            logger.error(f"Error in search_recent: {str(e)}")
            logger.exception("Full traceback for search_recent error:")
            return []
    
    async def check_database_status(self) -> MemoryResponse:
        """Check the status of the memory database and return detailed information (async)"""
        start_time = time.time()
        status_info = {
            "qdrant_status": "unavailable",
            "collections": [],
            "total_memories": 0,
            "memory_types": {},
            "sample_memories": {}
        }

        try:
            # Check Qdrant connection status first
            if self.db._qdrant_client:
                 try:
                      # Simple check like getting collections
                      await self.db._qdrant_client.get_collections()
                      status_info["qdrant_status"] = "connected"
                      logger.debug("Qdrant connection confirmed for status check.")

                      collection_name = settings.QDRANT_COLLECTION_NAME
                      status_info["collections"].append(collection_name)

                      # Get total count (async)
                      total_count = await self._get_vector_count()
                      status_info["total_memories"] = total_count

                      # Get type breakdown (async)
                      type_counts = await self._get_memory_type_counts()
                      status_info["memory_types"] = type_counts

                      # Get samples (async)
                      samples = await self._get_sample_memories(limit_per_type=1)
                      if samples:
                           status_info["sample_memories"][collection_name] = samples

                 except Exception as qdrant_check_e:
                      logger.error(f"Qdrant check failed during database status: {qdrant_check_e}")
                      status_info["qdrant_status"] = f"error: {qdrant_check_e}"
            else:
                 logger.warning("Qdrant client not initialized for database status check.")

            execution_time = time.time() - start_time
            status_info["execution_time"] = execution_time

            return MemoryResponse(
                operation="check_database",
                result={ "status_info": status_info }
            )

        except Exception as e:
            logger.error(f"Error checking memory database status: {str(e)}")
            execution_time = time.time() - start_time

            return MemoryResponse(
                status="error",
                operation="check_database",
                error=str(e),
                # Include partial status if available
                result={ "status_info": {**status_info, "execution_time": execution_time}}
            )
    
    async def _get_vector_count(self) -> int:
        """Get count of vectors in the Qdrant collection (async)"""
        if not self.db._qdrant_client:
             logger.warning("Qdrant client not available for _get_vector_count")
             return 0
        try:
            collection_info = await self.db._qdrant_client.count(
                collection_name=settings.QDRANT_COLLECTION_NAME
            )
            return collection_info.count
        except Exception as e:
            # Handle case where collection might not exist yet
            if "not found" in str(e).lower():
                 logger.warning(f"Collection '{settings.QDRANT_COLLECTION_NAME}' not found during count.")
                 return 0
            logger.error(f"Error getting vector count from Qdrant: {e}")
            return -1 # Indicate error
    
    async def _get_memory_type_counts(self) -> Dict[str, int]:
        """Get counts of each memory type from Qdrant (async)"""
        memory_types_counts = { "semantic": 0, "episodic": 0, "procedural": 0, "unknown": 0}
        if not self.db._qdrant_client:
            logger.warning("Qdrant client not available for _get_memory_type_counts")
            return memory_types_counts

        try:
            all_types = list(memory_types_counts.keys())[:-1] # Exclude 'unknown'
            tasks = []
            for mem_type in all_types:
                 # Define the filter for Qdrant count
                 type_filter = rest.Filter(
                     must=[
                         rest.FieldCondition(
                             key="metadata.memory_type", # Ensure this path is correct
                             match=rest.MatchValue(value=mem_type)
                         )
                     ]
                 )
                 # Create an async task for each count
                 tasks.append(
                     self.db._qdrant_client.count(
                         collection_name=settings.QDRANT_COLLECTION_NAME,
                         count_filter=type_filter,
                         exact=True # Use exact count
                     )
                 )

            # Run all count tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            total_counted = 0
            for i, result in enumerate(results):
                 mem_type = all_types[i]
                 if isinstance(result, Exception):
                      logger.error(f"Error counting memory type '{mem_type}': {result}")
                      memory_types_counts[mem_type] = -1 # Indicate error
                 elif hasattr(result, 'count'):
                      memory_types_counts[mem_type] = result.count
                      total_counted += result.count
                 else:
                      logger.error(f"Unexpected result type when counting '{mem_type}': {type(result)}")
                      memory_types_counts[mem_type] = -1

            # Estimate unknown count if total is available
            total_vectors = await self._get_vector_count()
            if total_vectors >= 0 and all(c >= 0 for c in memory_types_counts.values()):
                 memory_types_counts["unknown"] = total_vectors - total_counted

        except Exception as e:
            logger.error(f"Error getting memory type counts: {e}")
            # Return counts as -1 or keep existing zeros on error? Returning errors.
            for k in memory_types_counts: memory_types_counts[k] = -1

        return memory_types_counts
    
    async def _get_sample_memories(self, limit_per_type: int = 1) -> List[Dict[str, Any]]:
        """Get sample memories from Qdrant for each type (async)"""
        samples = []
        if not self.db._qdrant_client:
            logger.warning("Qdrant client not available for _get_sample_memories")
            return samples

        memory_types_to_sample = ["semantic", "episodic", "procedural"]
        try:
             tasks = []
             for mem_type in memory_types_to_sample:
                  type_filter = rest.Filter(
                       must=[rest.FieldCondition(key="metadata.memory_type", match=rest.MatchValue(value=mem_type))]
                  )
                  # Use scroll to get samples based on filter
                  tasks.append(
                       self.db._qdrant_client.scroll(
                            collection_name=settings.QDRANT_COLLECTION_NAME,
                            scroll_filter=type_filter,
                            limit=limit_per_type,
                            with_payload=True,
                            with_vectors=False
                       )
                  )

             # Run scrolls concurrently
             results = await asyncio.gather(*tasks, return_exceptions=True)

             # Process results
             for i, result in enumerate(results):
                  mem_type = memory_types_to_sample[i]
                  if isinstance(result, Exception):
                       logger.error(f"Error scrolling for sample memories (type '{mem_type}'): {result}")
                  elif isinstance(result, tuple) and len(result) > 0: # scroll returns (points, next_offset)
                       points, _ = result
                       for point in points:
                            payload = point.payload if point.payload else {}
                            samples.append({
                                "content": payload.get("page_content", "N/A")[:100] + "...", # Truncate content
                                "memory_type": mem_type, # Use the requested type
                                "id": point.id,
                                "timestamp": payload.get("timestamp", "N/A")
                            })
                  elif not result:
                       logger.debug(f"No sample memories found for type '{mem_type}'")

        except Exception as e:
            logger.error(f"Error getting sample memories: {e}")

        return samples
    
    async def execute(self, params: Dict[str, Any], context: RunContext) -> Dict[str, Any]:
        """Execute memory operations (now async)"""
        operation = params.get("operation", "retrieve")
        # Ensure context.deps is passed correctly if needed by operations
        deps = context.deps if hasattr(context, 'deps') else {}

        try:
            if operation == "store":
                content = params.get("content", "")
                if not content:
                    return MemoryResponse(status="error", operation="store", error="No content provided").model_dump()
                response = await self.store_memory(content, deps)
                return response.model_dump()

            elif operation == "retrieve":
                response = await self.retrieve_memory(params, deps)
                return response.model_dump()

            elif operation == "analyze":
                response = await self.analyze_memory(params, deps)
                return response.model_dump()

            elif operation == "check_database":
                response = await self.check_database_status()
                return response.model_dump()

            else:
                return MemoryResponse(
                    status="error",
                    operation=operation,
                    error=f"Unsupported memory operation: {operation}",
                    result={"supported_operations": ["store", "retrieve", "analyze", "check_database"]}
                ).model_dump()
        except Exception as e:
            logger.error(f"Error during memory minion execution (operation: {operation}): {e}")
            logger.error(traceback.format_exc())
            return MemoryResponse(
                status="error",
                operation=operation,
                error=f"An unexpected error occurred: {e}"
            ).model_dump()

    def _load_prompts(self) -> None:
        """Load prompts from configuration files (remains synchronous)"""
        try:
            # Load prompts from the corresponding JSON file
            self.prompts = PromptLoader.load_prompt(self.prompt_category, self.name)
            logger.info(f"Loaded prompts for {self.name} minion")
        except Exception as e:
            logger.error(f"Failed to load prompts for {self.name} minion: {e}")
            # Initialize with empty dict to prevent errors
            self.prompts = {}
