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
    
    def __init__(self, milvus_host: str, milvus_port: str, collection_name: str):
        """
        Initialize context integrator with Milvus connection.
        
        Args:
            milvus_host: Milvus server host
            milvus_port: Milvus server port
            collection_name: Name of the collection to use
        """
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.collection_name = collection_name
        self.collection = None
        self._connect()
    
    def _connect(self):
        """Connect to Milvus server."""
        if not MILVUS_AVAILABLE:
            logger.warning("Milvus not available. Skipping connection.")
            return
        
        try:
            connections.connect(
                alias="default",
                host=self.milvus_host,
                port=self.milvus_port
            )
            logger.info(f"Connected to Milvus at {self.milvus_host}:{self.milvus_port}")
            
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
    
    def retrieve_vector_context(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """
        Retrieve relevant context from vector database.
        
        Args:
            query_embedding: Query vector embedding
            top_k: Number of top results to retrieve
            
        Returns:
            List of retrieved documents with metadata
        """
        if not self.collection:
            logger.warning("Milvus collection not available, returning empty results")
            return []
        
        try:
            # Search in Milvus
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }
            
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["text", "metadata", "entity_id"]
            )
            
            # Format results
            retrieved_docs = []
            for hits in results:
                for hit in hits:
                    retrieved_docs.append({
                        "id": hit.id,
                        "text": hit.entity.get("text", ""),
                        "metadata": hit.entity.get("metadata", {}),
                        "score": hit.distance,
                        "entity_id": hit.entity.get("entity_id", None)
                    })
            
            return retrieved_docs
        
        except Exception as e:
            logger.error(f"Error retrieving vector context: {str(e)}")
            return []
    
    def retrieve_graph_context(self, entity_ids: List[str], max_depth: int = 3) -> Dict:
        """
        Retrieve graph context using GraphRAG approach.
        
        Args:
            entity_ids: List of entity IDs to start graph traversal from
            max_depth: Maximum depth for graph traversal
            
        Returns:
            Dictionary containing graph context and relationships
        """
        if not self.collection or not entity_ids:
            return {"nodes": [], "edges": [], "context": ""}
        
        try:
            # Retrieve entities and their relationships
            # This is a simplified GraphRAG implementation
            # In production, you would use Milvus's graph capabilities or Neo4j
            
            nodes = []
            edges = []
            visited_entities = set()
            
            # Start from initial entities
            current_level = entity_ids
            for depth in range(max_depth):
                if not current_level:
                    break
                
                next_level = []
                for entity_id in current_level:
                    if entity_id in visited_entities:
                        continue
                    
                    visited_entities.add(entity_id)
                    
                    # Retrieve entity information
                    entity_info = self._get_entity_info(entity_id)
                    if entity_info:
                        nodes.append(entity_info)
                        
                        # Get related entities
                        related = self._get_related_entities(entity_id)
                        for rel_entity_id, relation_type in related:
                            edges.append({
                                "source": entity_id,
                                "target": rel_entity_id,
                                "type": relation_type
                            })
                            if rel_entity_id not in visited_entities:
                                next_level.append(rel_entity_id)
                
                current_level = next_level
            
            # Build context string from graph
            context = self._build_graph_context(nodes, edges)
            
            return {
                "nodes": nodes,
                "edges": edges,
                "context": context,
                "depth": max_depth
            }
        
        except Exception as e:
            logger.error(f"Error retrieving graph context: {str(e)}")
            return {"nodes": [], "edges": [], "context": ""}
    
    def _get_entity_info(self, entity_id: str) -> Optional[Dict]:
        """Get information about a specific entity."""
        # Placeholder: In production, query Milvus or graph DB for entity info
        return {
            "id": entity_id,
            "type": "medical_entity",
            "name": entity_id
        }
    
    def _get_related_entities(self, entity_id: str) -> List[Tuple[str, str]]:
        """Get entities related to the given entity."""
        # Placeholder: In production, query graph relationships
        return []
    
    def _build_graph_context(self, nodes: List[Dict], edges: List[Dict]) -> str:
        """Build a context string from graph nodes and edges."""
        if not nodes:
            return ""
        
        context_parts = []
        
        # Add node information
        for node in nodes[:10]:  # Limit to first 10 nodes
            context_parts.append(f"Entity: {node.get('name', node.get('id', ''))}")
        
        # Add relationship information
        for edge in edges[:10]:  # Limit to first 10 edges
            context_parts.append(
                f"Relationship: {edge['source']} --{edge['type']}--> {edge['target']}"
            )
        
        return "\n".join(context_parts)
    
    def integrate_contexts(self, vector_results: List[Dict], graph_results: Dict) -> str:
        """
        Integrate vector and graph contexts into a unified context string.
        
        Args:
            vector_results: Results from vector search
            graph_results: Results from graph traversal
            
        Returns:
            Integrated context string
        """
        context_parts = []
        
        # Add vector search results
        if vector_results:
            context_parts.append("=== Relevant Medical Information ===")
            for i, result in enumerate(vector_results[:5], 1):
                context_parts.append(f"\n[{i}] {result.get('text', '')}")
                if result.get('metadata'):
                    context_parts.append(f"   Metadata: {result['metadata']}")
        
        # Add graph context
        if graph_results.get('context'):
            context_parts.append("\n=== Related Medical Concepts ===")
            context_parts.append(graph_results['context'])
        
        return "\n".join(context_parts)
    
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

