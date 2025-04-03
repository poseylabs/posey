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
from qdrant_client import QdrantClient

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

    def __init__(self):
        # Note: BaseMinion.__init__() calls self._load_prompts() which requires PromptLoader
        super().__init__(
            name="memory",
            description="Analyze, store and retrieve memory information"
        )
        self.vector_store = None
        self.semantic_memory = None
        self.episodic_memory = None
        self.procedural_memory = None
        
    def setup(self):
        """Initialize the memory minion with LangGraph memory components"""
        logger.info("Initializing memory minion with LangGraph")
        
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
            # Use QdrantClient directly to handle collection creation properly
            qdrant_url = self.get_qdrant_url()
            client = QdrantClient(url=qdrant_url)
            collection_name = "agent_memories"
            
            # Check if collection exists
            collections = client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if collection_name in collection_names:
                logger.info(f"Connecting to existing Qdrant collection '{collection_name}'")
            else:
                logger.info("Creating new Qdrant collection")
                sample_embedding = self.embeddings.embed_query("Sample text")
                vector_size = len(sample_embedding)

                client.create_collection(
                    collection_name=collection_name,
                    vectors_config={"size": vector_size, "distance": "Cosine"}
                )
                logger.info(f"Created new Qdrant collection '{collection_name}' with vector size {vector_size}")
            
            # Initialize the vector store with the client
            # Using embeddings parameter with proper type to avoid deprecation warnings
            self.vector_store = Qdrant(
                client=client,
                collection_name=collection_name,
                embeddings=self.embeddings,  # Using 'embeddings' instead of 'embedding_function'
            )
            logger.info(f"Successfully initialized Qdrant vector store")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {str(e)}")
            raise
        
        # Initialize time-weighted retriever for semantic memory
        # This gives more weight to recent memories
        self.semantic_retriever = TimeWeightedVectorStoreRetriever(
            vectorstore=self.vector_store,
            search_kwargs={"k": 5},
            decay_rate=0.01,  # Memories decay slowly over time
            k=5  # Number of results to return
        )
        
        # Initialize semantic memory - use standard retriever instead of TimeWeightedVectorStoreRetriever
        # since the latter doesn't support the expected interface
        self.semantic_memory = VectorStoreRetrieverMemory(
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
            memory_key="semantic_memory",
            input_key="query"
        )
        
        # Create file storage for episodic memory
        # This stores conversation histories
        fs = LocalFileStore("./data/episodic_memory")
        
        # Initialize procedural memory
        # This will store how to perform tasks
        self.procedural_memory = VectorStoreRetrieverMemory(
            retriever=self.vector_store.as_retriever(
                search_kwargs={"filter": {"memory_type": "procedural"}}
            ),
            memory_key="procedural_memory"
        )
        
        # Create agent with memory response result type (keeping original agent creation)
        self.agent = self.create_agent(result_type=MemoryResponse, model_key="memory")
        logger.info(f"Memory agent initialized with model: {LLM_CONFIG['memory']['model']}")
        
    def get_qdrant_url(self) -> str:
        """Get Qdrant URL from config"""
        # Get from environment variables
        qdrant_host = os.environ.get("QDRANT_HOST", "http://qdrant:6333")
        return qdrant_host
    
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
        """Store a new memory using LangGraph memory concepts"""
        start_time = time.time()
        
        try:
            # Extract user information from context
            user_id = context.get("user_id", "anonymous")
            
            # Determine memory type based on content or metadata
            memory_type = self.classify_memory_type(content)
            
            # Create a document with appropriate metadata
            doc = Document(
                page_content=content,
                metadata={
                    "user_id": user_id,
                    "agent_id": "memory",
                    "timestamp": datetime.now().isoformat(),
                    "memory_type": memory_type,
                    "id": str(uuid4())
                }
            )
            
            # Store in vector store
            self.vector_store.add_documents([doc])
            
            memory_id = doc.metadata["id"]
            
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
            logger.info(f"Memory storage completed in {execution_time:.2f}s")
            
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
        """Retrieve memories based on query or filters using LangGraph memory"""
        start_time = time.time()
        
        try:
            # Extract parameters
            query = params.get("query", "")
            filters = params.get("filters", {})
            
            if not query and not filters:
                return MemoryResponse(
                    status="error",
                    operation="retrieve",
                    error="No query or filters provided for memory retrieval"
                )
            
            # Build search filter
            search_filter = {}
            if filters:
                for key, value in filters.items():
                    if key == "user_id":
                        search_filter["user_id"] = value
                    elif key == "memory_type":
                        search_filter["memory_type"] = value
                    elif key == "context_type":
                        search_filter["context_type"] = value
            
            # If no filter for user_id, add user_id from context
            if "user_id" not in search_filter and context.get("user_id"):
                search_filter["user_id"] = context.get("user_id")
            
            # Retrieve memories using the appropriate memory type
            if filters.get("memory_type") == "procedural":
                retrieved_docs = self.procedural_memory.retrieve(query)
            elif filters.get("memory_type") == "episodic":
                # Implement episodic retrieval
                retrieved_docs = self.vector_store.similarity_search(
                    query, k=5, filter={"memory_type": "episodic", **search_filter}
                )
            else:
                # Default to semantic memory
                if query:
                    # Use semantic search with query
                    retrieved_docs = self.vector_store.similarity_search(
                        query, k=5, filter=search_filter if search_filter else None
                    )
                else:
                    # Use filtering only
                    retrieved_docs = self.vector_store.similarity_search(
                        "", k=5, filter=search_filter if search_filter else None
                    )
            
            # Convert docs to memories format
            memories = []
            for doc in retrieved_docs:
                memories.append({
                    "content": doc.page_content,
                    "score": doc.metadata.get("score", 1.0) if hasattr(doc, "metadata") else 1.0,
                    "metadata": {
                        "id": doc.metadata.get("id"),
                        "user_id": doc.metadata.get("user_id"),
                        "agent_id": doc.metadata.get("agent_id"),
                        "timestamp": doc.metadata.get("timestamp"),
                        "memory_type": doc.metadata.get("memory_type"),
                        "tags": doc.metadata.get("tags", [])
                    }
                })
            
            # Create memory-specific context for prompt
            memory_data = {
                "current_operation": "retrieve",
                "query": query,
                "filters": filters,
                "retrieved_memories": memories
            }
            
            # Create proper prompt context
            prompt_context = self.create_prompt_context(context, memory_data)
            
            # Get task prompt from configuration with proper context
            user_prompt = self.get_task_prompt(
                "retrieve_memory",
                context=prompt_context,
                query=query,
                filters=filters,
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
                    "filters": filters,
                    "execution_time": execution_time
                }
            )
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {str(e)}")
            execution_time = time.time() - start_time
            
            return MemoryResponse(
                status="error",
                operation="retrieve",
                error=str(e)
            )
    
    async def analyze_memory(self, params: Dict[str, Any], context: Dict[str, Any]) -> MemoryResponse:
        """Analyze memories for patterns, insights, or specific information"""
        start_time = time.time()
        
        try:
            # Extract parameters
            memory_ids = params.get("memory_ids", [])
            query = params.get("query", "")
            
            if not memory_ids and not query:
                return MemoryResponse(
                    status="error",
                    operation="analyze",
                    error="No memory_ids or query provided for analysis"
                )
            
            # First retrieve the memories to analyze
            memories = []
            if memory_ids:
                # Retrieve memories by ID
                for memory_id in memory_ids:
                    # Note: Implement a method to get memory by ID
                    docs = self.vector_store.similarity_search("", 
                        filter={"id": memory_id}, k=1
                    )
                    if docs:
                        memories.append({
                            "content": docs[0].page_content,
                            "id": docs[0].metadata.get("id"),
                            "timestamp": docs[0].metadata.get("timestamp"),
                            "memory_type": docs[0].metadata.get("memory_type")
                        })
            
            if query and not memories:
                # Use retrieve operation to get memories
                retrieve_params = {"query": query}
                retrieve_response = await self.retrieve_memory(retrieve_params, context)
                if retrieve_response.status == "success" and retrieve_response.memories:
                    memories = retrieve_response.memories
            
            if not memories:
                return MemoryResponse(
                    status="error",
                    operation="analyze",
                    error="No memories found to analyze"
                )
            
            # Create memory-specific context for prompt
            memory_data = {
                "current_operation": "analyze",
                "query": query,
                "memories_to_analyze": memories,
                "memory_types_present": list(set([m.get("memory_type", "semantic") for m in memories]))
            }
            
            # Create proper prompt context
            prompt_context = self.create_prompt_context(context, memory_data)
            
            # Get task prompt from configuration with proper context
            user_prompt = self.get_task_prompt(
                "analyze_memory",
                context=prompt_context,
                memories=memories,
                query=query,
                memory_count=len(memories)
            )
            
            # Call the agent to analyze the memories
            logger.info(f"Analyzing {len(memories)} memories")
            analysis_result = await self.agent.run(user_prompt)
            
            execution_time = time.time() - start_time
            
            # Extract results
            if isinstance(analysis_result, MemoryResponse):
                analysis = analysis_result
            else:
                # Create a default response
                analysis = MemoryResponse(
                    operation="analyze",
                    result={
                        "insights": "No specific insights found",
                        "patterns": [],
                        "memory_count": len(memories),
                        "execution_time": execution_time
                    }
                )
                
                # Try to extract structured data if available
                if hasattr(analysis_result, 'data'):
                    analysis.result = analysis_result.data
                    analysis.result["execution_time"] = execution_time
            
            logger.info(f"Memory analysis completed in {execution_time:.2f}s")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing memories: {str(e)}")
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
        context: Optional[str] = None,
        include_conversation: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most recent memories for a user using LangGraph memory
        """
        try:
            logger.info(f"Retrieving {limit} recent memories for user {user_id}")
            
            # Create filter with required fields
            filter_dict = {"user_id": user_id}
            
            if memory_type:
                filter_dict["memory_type"] = memory_type
                
            if context:
                filter_dict["context_type"] = context
                
            # Create retrieval query
            # We'll sort the results by timestamp after retrieval
            # Empty query to match all documents with the filter
            docs = self.vector_store.similarity_search(
                "", filter=filter_dict, k=limit * 2  # Get extra to allow for sorting
            )
            
            # Convert to required format
            memories = []
            for doc in docs:
                memories.append({
                    "content": doc.page_content,
                    "metadata": {
                        "id": doc.metadata.get("id"),
                        "timestamp": doc.metadata.get("timestamp"),
                        "memory_type": doc.metadata.get("memory_type"),
                        "tags": doc.metadata.get("tags", [])
                    }
                })
            
            # Sort by timestamp (most recent first)
            memories.sort(
                key=lambda x: x.get("metadata", {}).get("timestamp", ""), 
                reverse=True
            )
            
            # Include conversation memories if requested
            if include_conversation and not context:
                conv_filter = {
                    "user_id": user_id,
                    "context_type": "conversation"
                }
                
                conv_docs = self.vector_store.similarity_search(
                    "", filter=conv_filter, k=limit
                )
                
                for doc in conv_docs:
                    memories.append({
                        "content": doc.page_content,
                        "metadata": {
                            "id": doc.metadata.get("id"),
                            "timestamp": doc.metadata.get("timestamp"),
                            "memory_type": "episodic",  # Conversations are episodic
                            "context_type": "conversation",
                            "tags": doc.metadata.get("tags", [])
                        }
                    })
                
                # Re-sort after adding conversation memories
                memories.sort(
                    key=lambda x: x.get("metadata", {}).get("timestamp", ""), 
                    reverse=True
                )
            
            # Limit to requested number
            memories = memories[:limit]
            
            logger.info(f"Retrieved {len(memories)} recent memories for user {user_id}")
            if len(memories) == 0:
                logger.warning("No memories found for this user - the memory database may be empty")
            
            return memories
            
        except Exception as e:
            logger.error(f"Error in search_recent: {str(e)}")
            logger.exception("Full traceback for search_recent error:")
            return []
    
    async def check_database_status(self) -> MemoryResponse:
        """Check the status of the memory database and return detailed information"""
        start_time = time.time()
        
        try:
            collections = []
            total_memories = 0
            memory_types = {}
            sample_memories = {}
            
            # Check vector store status
            if self.vector_store:
                # Get Qdrant collection info
                # This would need to access the Qdrant client directly
                # You'll need to implement this based on how your vector store is configured
                vector_count = await self._get_vector_count()
                
                collections.append("agent_memories")
                total_memories += vector_count
                
                # Get memory type breakdown
                memory_types = await self._get_memory_type_counts()
                
                # Get sample memories
                samples = await self._get_sample_memories()
                if samples:
                    sample_memories["agent_memories"] = samples
            
            execution_time = time.time() - start_time
            
            # Create memory-specific context for prompt
            memory_data = {
                "current_operation": "check_database",
                "collections": collections,
                "total_memories": total_memories,
                "memory_types": memory_types
            }
            
            # Create proper prompt context
            context_dict = {"user_id": "system", "system": {"operation": "database_check"}}
            prompt_context = self.create_prompt_context(context_dict, memory_data)
            
            return MemoryResponse(
                operation="check_database",
                result={
                    "status_info": {
                        "collections": collections,
                        "total_memories": total_memories,
                        "memory_types": memory_types,
                        "sample_memories": sample_memories
                    },
                    "execution_time": execution_time
                }
            )
            
        except Exception as e:
            logger.error(f"Error checking memory database status: {str(e)}")
            execution_time = time.time() - start_time
            
            return MemoryResponse(
                status="error",
                operation="check_database",
                error=str(e)
            )
    
    async def _get_vector_count(self) -> int:
        """Get count of vectors in vector store"""
        # Implementation depends on your vector store
        # For Qdrant, you might do something like:
        try:
            if hasattr(self.vector_store, "_collection"):
                collection_info = await self.vector_store._collection.count()
                return collection_info.count
        except Exception as e:
            logger.error(f"Error getting vector count: {e}")
        return 0
    
    async def _get_memory_type_counts(self) -> Dict[str, int]:
        """Get counts of each memory type"""
        memory_types = {
            "semantic": 0,
            "episodic": 0,
            "procedural": 0
        }
        
        try:
            for memory_type in memory_types.keys():
                if hasattr(self.vector_store, "_collection"):
                    count_result = await self.vector_store._collection.count(
                        filter={"must": [{"key": "memory_type", "match": {"value": memory_type}}]}
                    )
                    memory_types[memory_type] = count_result.count
        except Exception as e:
            logger.error(f"Error getting memory type counts: {e}")
            
        return memory_types
    
    async def _get_sample_memories(self) -> List[Dict[str, Any]]:
        """Get sample memories from the vector store"""
        samples = []
        try:
            # Get a few samples from each memory type
            memory_types = ["semantic", "episodic", "procedural"]
            
            for memory_type in memory_types:
                docs = self.vector_store.similarity_search(
                    "", filter={"memory_type": memory_type}, k=2
                )
                
                for doc in docs:
                    samples.append({
                        "content": doc.page_content,
                        "memory_type": memory_type,
                        "id": doc.metadata.get("id"),
                        "timestamp": doc.metadata.get("timestamp")
                    })
        except Exception as e:
            logger.error(f"Error getting sample memories: {e}")
            
        return samples
    
    async def execute(self, params: Dict[str, Any], context: RunContext) -> Dict[str, Any]:
        """Execute memory operations"""
        operation = params.get("operation", "retrieve")
        
        if operation == "store":
            content = params.get("content", "")
            if not content:
                return {
                    "status": "error",
                    "operation": "store",
                    "error": "No content provided for memory storage"
                }
                
            response = await self.store_memory(content, context.deps)
            return response.model_dump()
            
        elif operation == "retrieve":
            response = await self.retrieve_memory(params, context.deps)
            return response.model_dump()
            
        elif operation == "analyze":
            response = await self.analyze_memory(params, context.deps)
            return response.model_dump()
            
        elif operation == "check_database":
            response = await self.check_database_status()
            return response.model_dump()
            
        else:
            return {
                "status": "error",
                "operation": operation,
                "error": f"Unsupported memory operation: {operation}",
                "supported_operations": ["store", "retrieve", "analyze", "check_database"]
            }

    def _load_prompts(self) -> None:
        """Load prompts from configuration files"""
        try:
            # Load prompts from the corresponding JSON file
            self.prompts = PromptLoader.load_prompt(self.prompt_category, self.name)
            logger.info(f"Loaded prompts for {self.name} minion")
        except Exception as e:
            logger.error(f"Failed to load prompts for {self.name} minion: {e}")
            # Initialize with empty dict to prevent errors
            self.prompts = {}
