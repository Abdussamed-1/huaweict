"""
Context Integration Module
Integrates context from Milvus Vector & Graph DB and OBS storage.
Part of the Data & Memory Layer (Access Layer).
"""
import logging
from typing import List, Dict, Optional, Tuple
try:
    from pymilvus import connections, Collection, utility
    from pymilvus import FieldSchema, CollectionSchema, DataType
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    logging.warning("pymilvus not available. Milvus features will be disabled.")

logger = logging.getLogger(__name__)


class ContextIntegrator:
    """Integrates context from vector database and graph database."""
    
    def __init__(
        self,
        milvus_host: str,
        milvus_port: str,
        collection_name: str,
        milvus_api_key: str = None,
        milvus_user: str = None,
        milvus_password: str = None,
        use_cloud: bool = False
    ):
        """
        Initialize context integrator with Milvus connection.
        
        Args:
            milvus_host: Milvus server host (or cloud endpoint)
            milvus_port: Milvus server port
            collection_name: Name of the collection to use
            milvus_api_key: API key for Milvus Cloud (if using cloud)
            milvus_user: Username for authentication (if using username/password)
            milvus_password: Password for authentication (if using username/password)
            use_cloud: Whether using Milvus Cloud cluster
        """
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.collection_name = collection_name
        self.milvus_api_key = milvus_api_key
        self.milvus_user = milvus_user
        self.milvus_password = milvus_password
        self.use_cloud = use_cloud
        self.collection = None
        
        self._connect()
    
    def _connect(self):
        """Connect to Milvus server (local or cloud)."""
        if not MILVUS_AVAILABLE:
            logger.warning("Milvus not available. Skipping connection.")
            return
        
        try:
            # Prepare connection parameters
            # For serverless Milvus, ensure port is integer
            port = int(self.milvus_port) if isinstance(self.milvus_port, str) else self.milvus_port
            
            connection_params = {
                "alias": "default",
                "host": self.milvus_host,
                "port": port
            }
            
            # Add authentication for cloud cluster
            if self.use_cloud:
                if self.milvus_api_key:
                    # Use API key authentication (preferred for Milvus Cloud)
                    connection_params["token"] = self.milvus_api_key
                    logger.info("Using API key authentication for Milvus Cloud")
                elif self.milvus_user and self.milvus_password:
                    # Use username/password authentication
                    connection_params["user"] = self.milvus_user
                    connection_params["password"] = self.milvus_password
                    logger.info("Using username/password authentication")
                else:
                    logger.warning("Milvus Cloud enabled but no authentication provided")
            
            # Check if API key is provided for cloud
            if self.use_cloud and not self.milvus_api_key:
                logger.error("MILVUS_API_KEY is required for Milvus Cloud. Please set it in .env file")
                return
            
            # For serverless, add secure=True
            if self.use_cloud and "serverless" in self.milvus_host.lower():
                connection_params["secure"] = True
            
            connections.connect(**connection_params)
            logger.info(f"✅ Connected to Milvus at {self.milvus_host}:{port}")
            
            # Load collection if it exists
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                self.collection.load()
                logger.info(f"Loaded collection: {self.collection_name}")
            else:
                logger.warning(f"Collection {self.collection_name} does not exist yet.")
        except Exception as e:
            logger.error(f"Error connecting to Milvus: {str(e)}")
            # Fallback: collection will be None, will use fallback retrieval
    
    def retrieve_graphrag_context(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        max_depth: int = 2
    ) -> Dict:
        """
        Retrieve context using GraphRAG approach - PRIMARY METHOD.
        
        Args:
            query_embedding: Query vector embedding
            top_k: Number of top initial results to retrieve
            max_depth: Maximum depth for graph traversal
            
        Returns:
            Dictionary containing retrieved Q&A pairs and graph context
        """
        if not self.collection:
            logger.warning("Milvus collection not available, returning empty results")
            return {"nodes": [], "edges": [], "context": "", "qa_pairs": []}
        
        try:
            # Step 1: Find initial similar Q&A pairs using vector search
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            results = self.collection.search(
                data=[query_embedding],
                anns_field="combined_embedding",
                param=search_params,
                limit=top_k,
                output_fields=["id", "question", "response", "related_nodes", "metadata"]
            )
            
            # Step 2: Extract initial nodes
            initial_nodes = []
            initial_node_ids = []
            
            for hits in results:
                for hit in hits:
                    node_data = {
                        "id": hit.id,
                        "question": hit.entity.get("question", ""),
                        "response": hit.entity.get("response", ""),
                        "similarity": 1 - hit.distance,  # Convert distance to similarity
                        "metadata": hit.entity.get("metadata", {})
                    }
                    
                    initial_nodes.append(node_data)
                    initial_node_ids.append(hit.id)
            
            # Step 3: Traverse graph to find related nodes
            graph_nodes = initial_nodes.copy()
            graph_edges = []
            visited_nodes = set(initial_node_ids)
            
            # Get related nodes from graph
            current_level = initial_node_ids
            for depth in range(max_depth):
                if not current_level:
                    break
                
                next_level = []
                for node_id in current_level:
                    # Get related nodes from Milvus
                    related_node_ids = self._get_related_nodes_from_milvus(node_id)
                    
                    for related_id in related_node_ids:
                        if related_id not in visited_nodes:
                            visited_nodes.add(related_id)
                            next_level.append(related_id)
                            
                            # Get full node data
                            node_data = self._get_node_data_from_milvus(related_id)
                            if node_data:
                                graph_nodes.append(node_data)
                            
                            # Add edge
                            graph_edges.append({
                                "source": node_id,
                                "target": related_id,
                                "type": "semantic_similarity"
                            })
                
                current_level = next_level
            
            # Step 4: Build context string
            context = self._build_graphrag_context(graph_nodes, graph_edges)
            
            return {
                "nodes": graph_nodes,
                "edges": graph_edges,
                "context": context,
                "qa_pairs": graph_nodes,  # Q&A pairs are the nodes
                "depth": max_depth
            }
        
        except Exception as e:
            logger.error(f"Error retrieving GraphRAG context: {str(e)}")
            return {"nodes": [], "edges": [], "context": "", "qa_pairs": []}
    
    def retrieve_vector_context(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """
        Retrieve relevant context from vector database (DEPRECATED - use retrieve_graphrag_context).
        
        Args:
            query_embedding: Query vector embedding
            top_k: Number of top results to retrieve
            
        Returns:
            List of retrieved documents with metadata
        """
        logger.warning("retrieve_vector_context is deprecated. Use retrieve_graphrag_context instead.")
        graph_result = self.retrieve_graphrag_context(query_embedding, top_k, max_depth=0)
        return graph_result.get("qa_pairs", [])
    
    def _get_related_nodes_from_milvus(self, node_id: str) -> List[str]:
        """Get related node IDs from Milvus for a given node."""
        if not self.collection:
            return []
        
        try:
            # Query Milvus to get related_nodes field
            expr = f'id == "{node_id}"'
            results = self.collection.query(
                expr=expr,
                output_fields=["related_nodes"]
            )
            
            if results and len(results) > 0:
                related_nodes = results[0].get("related_nodes", [])
                return related_nodes[:20]  # Limit to top 20 related nodes
            
            return []
        
        except Exception as e:
            logger.error(f"Error getting related nodes for {node_id}: {str(e)}")
            return []
    
    def _get_node_data_from_milvus(self, node_id: str) -> Optional[Dict]:
        """Get full node data from Milvus."""
        if not self.collection:
            return None
        
        try:
            expr = f'id == "{node_id}"'
            results = self.collection.query(
                expr=expr,
                output_fields=["id", "question", "response", "metadata"]
            )
            
            if results and len(results) > 0:
                result = results[0]
                return {
                    "id": result.get("id", node_id),
                    "question": result.get("question", ""),
                    "response": result.get("response", ""),
                    "similarity": 0.0,  # Will be calculated if needed
                    "metadata": result.get("metadata", {})
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting node data for {node_id}: {str(e)}")
            return None
    
    def _build_graphrag_context(self, nodes: List[Dict], edges: List[Dict]) -> str:
        """Build context string from GraphRAG nodes (Q&A pairs) and edges."""
        if not nodes:
            return ""
        
        context_parts = []
        context_parts.append("=== Relevant Medical Q&A Information ===\n")
        
        # Add Q&A pairs (nodes)
        for i, node in enumerate(nodes[:10], 1):  # Limit to top 10
            question = node.get("question", "")
            response = node.get("response", "")
            similarity = node.get("similarity", 0.0)
            
            context_parts.append(f"[{i}] Question: {question}")
            context_parts.append(f"    Answer: {response}")
            if similarity > 0:
                context_parts.append(f"    Relevance: {similarity:.3f}")
            context_parts.append("")
        
        # Add graph structure info if available
        if edges:
            context_parts.append(f"\n=== Related Medical Concepts (Graph Connections: {len(edges)}) ===")
            # Show some edge examples
            for edge in edges[:5]:
                context_parts.append(f"Related: {edge['source']} -> {edge['target']}")
        
        return "\n".join(context_parts)
    
    def integrate_contexts(self, vector_results: List[Dict] = None, graph_results: Dict = None) -> str:
        """
        Integrate contexts into a unified context string.
        Now primarily uses GraphRAG results.
        
        Args:
            vector_results: Results from vector search (optional, deprecated)
            graph_results: Results from GraphRAG traversal
            
        Returns:
            Integrated context string
        """
        # If graph_results provided, use it directly
        if graph_results and graph_results.get('context'):
            return graph_results['context']
        
        # Fallback to vector results if available
        context_parts = []
        if vector_results:
            context_parts.append("=== Relevant Medical Information ===")
            for i, result in enumerate(vector_results[:5], 1):
                context_parts.append(f"\n[{i}] {result.get('text', result.get('question', ''))}")
                if result.get('response'):
                    context_parts.append(f"    Answer: {result.get('response', '')}")
                if result.get('metadata'):
                    context_parts.append(f"   Metadata: {result['metadata']}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def store_document(self, text: str, embedding: List[float], metadata: Dict = None):
        """
        Store a document in Milvus (for future use).
        
        NOTE: This method requires the Milvus collection schema to match the data structure.
        The collection should have fields: 'text' (VARCHAR), 'embedding' (FLOAT_VECTOR), 
        'metadata' (JSON), and optionally 'entity_id' (VARCHAR).
        
        Args:
            text: Document text
            embedding: Document embedding vector
            metadata: Additional metadata
        """
        if not self.collection:
            logger.warning("Cannot store document: Milvus collection not available")
            return
        
        try:
            # Prepare data for insertion
            # NOTE: Data structure must match collection schema
            data = [{
                "text": text,
                "embedding": embedding,
                "metadata": metadata or {}
            }]
            
            # Insert into collection
            self.collection.insert(data)
            self.collection.flush()
            
            logger.info("Document stored successfully")
        
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            logger.warning("Make sure the collection schema matches the data structure")

