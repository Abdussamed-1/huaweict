"""
GraphRAG Builder
Builds a knowledge graph from medical Q&A pairs and stores in Milvus
"""
import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
from collections import defaultdict
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available. GPU acceleration disabled.")

try:
    from pymilvus import connections, Collection, utility, FieldSchema, CollectionSchema, DataType
    from pymilvus import MilvusClient  # For serverless Milvus
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    logging.warning("pymilvus not available. Milvus features will be disabled.")

from langchain_huggingface import HuggingFaceEmbeddings
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class GraphRAGBuilder:
    """Builds GraphRAG structure from medical Q&A pairs."""
    
    def __init__(
        self,
        milvus_host: str,
        milvus_port: str,
        collection_name: str,
        embedding_model_name: str = "sentence-transformers/all-mpnet-base-v2",
        milvus_api_key: str = None,
        milvus_user: str = None,
        milvus_password: str = None,
        use_cloud: bool = False,
        device: str = "auto"
    ):
        """
        Initialize GraphRAG builder.
        
        Args:
            milvus_host: Milvus server host (or cloud endpoint)
            milvus_port: Milvus server port
            collection_name: Name of the collection
            embedding_model_name: Embedding model name
            milvus_api_key: API key for Milvus Cloud (if using cloud)
            milvus_user: Username for authentication
            milvus_password: Password for authentication
            use_cloud: Whether using Milvus Cloud cluster
            device: Device to use for embeddings ('cuda', 'cpu', or 'auto')
        """
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        self.collection_name = collection_name
        self.milvus_api_key = milvus_api_key
        self.milvus_user = milvus_user
        self.milvus_password = milvus_password
        self.use_cloud = use_cloud
        self.collection = None
        self.milvus_client = None  # For serverless Milvus
        
        # Determine device for embeddings
        self.device = self._determine_device(device)
        
        # Initialize embedding model
        try:
            logger.info(f"Loading embedding model: {embedding_model_name}")
            logger.info(f"Using device: {self.device}")
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=embedding_model_name,
                model_kwargs={'device': self.device}
            )
            self.embedding_dim = self._get_embedding_dim(embedding_model_name)
            logger.info(f"Embedding model loaded. Dimension: {self.embedding_dim}, Device: {self.device}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            raise
        
        self._connect()
    
    def _determine_device(self, device: str) -> str:
        """Determine the device to use for embeddings."""
        if device == "auto":
            # Auto-detect: prefer GPU if available
            if TORCH_AVAILABLE and torch.cuda.is_available():
                device = "cuda"
                logger.info(f"✅ GPU detected: {torch.cuda.get_device_name(0)}")
                logger.info(f"   CUDA Version: {torch.version.cuda}")
                logger.info(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
            else:
                device = "cpu"
                if TORCH_AVAILABLE:
                    logger.info("⚠️ GPU not available, using CPU")
                else:
                    logger.info("⚠️ PyTorch not available, using CPU")
        elif device == "cuda":
            if TORCH_AVAILABLE and torch.cuda.is_available():
                logger.info(f"✅ Using GPU: {torch.cuda.get_device_name(0)}")
            else:
                logger.warning("⚠️ CUDA requested but not available, falling back to CPU")
                device = "cpu"
        else:
            logger.info(f"Using device: {device}")
        
        return device
    
    def _get_embedding_dim(self, model_name: str) -> int:
        """Get embedding dimension for the model."""
        # Common embedding dimensions
        dim_map = {
            "sentence-transformers/all-mpnet-base-v2": 768,
            "sentence-transformers/all-MiniLM-L6-v2": 384,
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2": 768,
            "sentence-transformers/all-mpnet-base-v2": 768
        }
        
        # Try to get from model or use default
        if model_name in dim_map:
            return dim_map[model_name]
        
        # Default: test with a sample
        try:
            test_embedding = self.embedding_model.embed_query("test")
            return len(test_embedding)
        except:
            return 768  # Default fallback
    
    def _connect(self):
        """Connect to Milvus server (local or cloud)."""
        if not MILVUS_AVAILABLE:
            logger.warning("Milvus not available. Skipping connection.")
            return
        
        try:
            # Check if API key is provided for cloud
            if self.use_cloud and not self.milvus_api_key:
                raise ValueError("MILVUS_API_KEY is required for Milvus Cloud. Please set it in .env file")
            
            # For serverless Milvus, use MilvusClient with URI format
            if self.use_cloud and "serverless" in self.milvus_host.lower():
                # Serverless Milvus requires URI format: https://host:port
                port = int(self.milvus_port) if isinstance(self.milvus_port, str) else self.milvus_port
                uri = f"https://{self.milvus_host}:{port}"
                
                logger.info(f"Connecting to serverless Milvus: {uri}")
                logger.info(f"Using API key: {self.milvus_api_key[:20]}..." if self.milvus_api_key else "No API key")
                
                # Use MilvusClient for serverless
                self.milvus_client = MilvusClient(
                    uri=uri,
                    token=self.milvus_api_key
                )
                logger.info(f"✅ Connected to serverless Milvus using MilvusClient")
                
                # Also connect using traditional method for Collection API compatibility
                try:
                    connections.connect(
                        alias="default",
                        host=self.milvus_host,
                        port=port,
                        token=self.milvus_api_key,
                        secure=True  # Enable secure connection for serverless
                    )
                    logger.info(f"✅ Also connected using traditional method")
                except Exception as e:
                    logger.warning(f"Traditional connection method failed (using MilvusClient only): {e}")
            else:
                # Traditional Milvus connection
                port = int(self.milvus_port) if isinstance(self.milvus_port, str) else self.milvus_port
                
                connection_params = {
                    "alias": "default",
                    "host": self.milvus_host,
                    "port": port
                }
                
                if self.use_cloud:
                    if self.milvus_api_key:
                        connection_params["token"] = self.milvus_api_key
                        logger.info("Using API key authentication for Milvus Cloud")
                    elif self.milvus_user and self.milvus_password:
                        connection_params["user"] = self.milvus_user
                        connection_params["password"] = self.milvus_password
                        logger.info("Using username/password authentication")
                
                connections.connect(**connection_params)
                logger.info(f"✅ Connected to Milvus at {self.milvus_host}:{port}")
                
        except Exception as e:
            logger.error(f"❌ Error connecting to Milvus: {str(e)}")
            logger.error(f"Host: {self.milvus_host}, Port: {self.milvus_port}, Use Cloud: {self.use_cloud}")
            if self.use_cloud:
                logger.error("Please verify:")
                logger.error("1. MILVUS_API_KEY is set correctly in .env file")
                logger.error("2. MILVUS_HOST is correct (without https://)")
                logger.error("3. MILVUS_PORT is 443 for serverless")
            raise
    
    def create_collection(self, drop_existing: bool = False):
        """
        Create Milvus collection for GraphRAG.
        
        Args:
            drop_existing: Whether to drop existing collection
        """
        if not MILVUS_AVAILABLE:
            logger.warning("Milvus not available. Cannot create collection.")
            return
        
        try:
            # Check if collection exists
            if utility.has_collection(self.collection_name):
                if drop_existing:
                    utility.drop_collection(self.collection_name)
                    logger.info(f"Dropped existing collection: {self.collection_name}")
                else:
                    logger.info(f"Collection {self.collection_name} already exists.")
                    self.collection = Collection(self.collection_name)
                    # Check and create missing indexes
                    self._ensure_indexes()
                    self.collection.load()
                    return
            
            # Define schema
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
                FieldSchema(name="question", dtype=DataType.VARCHAR, max_length=5000),
                FieldSchema(name="response", dtype=DataType.VARCHAR, max_length=10000),
                FieldSchema(name="question_embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
                FieldSchema(name="response_embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
                FieldSchema(name="combined_embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
                FieldSchema(name="metadata", dtype=DataType.JSON),
                FieldSchema(name="related_nodes", dtype=DataType.JSON)  # List of related node IDs
            ]
            
            schema = CollectionSchema(
                fields=fields,
                description="Medical Q&A GraphRAG Collection"
            )
            
            # Create collection
            self.collection = Collection(
                name=self.collection_name,
                schema=schema
            )
            
            # Create indexes for all vector fields
            self._create_indexes()
            
            logger.info(f"Collection {self.collection_name} created successfully")
        
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            raise
    
    def _create_indexes(self):
        """Create indexes for all vector fields."""
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        
        # Vector fields that need indexes
        vector_fields = ["question_embedding", "response_embedding", "combined_embedding"]
        
        for field_name in vector_fields:
            try:
                logger.info(f"Creating index for field: {field_name}")
                self.collection.create_index(
                    field_name=field_name,
                    index_params=index_params
                )
                logger.info(f"Index created for {field_name}")
            except Exception as e:
                logger.warning(f"Could not create index for {field_name}: {str(e)}")
                # Index might already exist, continue
    
    def _ensure_indexes(self):
        """Ensure all vector fields have indexes. Create missing ones."""
        from pymilvus import utility
        
        # Get existing indexes
        existing_indexes = {}
        try:
            indexes = self.collection.indexes
            for index in indexes:
                # Get field name from index
                for field in index.field_name.split(","):
                    existing_indexes[field.strip()] = True
        except Exception as e:
            logger.warning(f"Could not get existing indexes: {str(e)}")
        
        # Vector fields that need indexes
        vector_fields = ["question_embedding", "response_embedding", "combined_embedding"]
        
        # Check which indexes are missing
        missing_indexes = [field for field in vector_fields if field not in existing_indexes]
        
        if missing_indexes:
            logger.info(f"Creating missing indexes for: {missing_indexes}")
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            
            for field_name in missing_indexes:
                try:
                    logger.info(f"Creating index for field: {field_name}")
                    self.collection.create_index(
                        field_name=field_name,
                        index_params=index_params
                    )
                    logger.info(f"Index created for {field_name}")
                except Exception as e:
                    logger.error(f"Error creating index for {field_name}: {str(e)}")
                    raise
        else:
            logger.info("All required indexes already exist")
    
    def build_graph_from_qa_pairs(
        self,
        qa_pairs: List[Dict],
        similarity_threshold: float = 0.7,
        batch_size: int = None
    ):
        """
        Build graph from Q&A pairs.
        
        Args:
            qa_pairs: List of Q&A pair dictionaries
            similarity_threshold: Threshold for creating edges
            batch_size: Batch size for processing (None = auto-detect based on device)
        """
        if not self.collection:
            raise ValueError("Collection not created. Call create_collection() first.")
        
        # Auto-determine batch size based on device
        if batch_size is None:
            if self.device == "cuda":
                batch_size = 200  # Larger batch for GPU
                logger.info(f"Using GPU-optimized batch size: {batch_size}")
            else:
                batch_size = 50  # Smaller batch for CPU
                logger.info(f"Using CPU batch size: {batch_size}")
        
        try:
            logger.info(f"Building graph from {len(qa_pairs)} Q&A pairs...")
            logger.info(f"Device: {self.device}, Batch size: {batch_size}")
            
            # Step 1: Generate embeddings for all Q&A pairs
            logger.info("Step 1: Generating embeddings...")
            embeddings_data = self._generate_embeddings(qa_pairs, batch_size)
            
            # Step 2: Build similarity graph
            logger.info("Step 2: Building similarity graph...")
            graph_edges = self._build_similarity_graph(
                embeddings_data,
                similarity_threshold
            )
            
            # Step 3: Store in Milvus
            logger.info("Step 3: Storing in Milvus...")
            self._store_in_milvus(qa_pairs, embeddings_data, graph_edges, batch_size)
            
            logger.info("GraphRAG build completed successfully!")
        
        except Exception as e:
            logger.error(f"Error building graph: {str(e)}")
            raise
    
    def _generate_embeddings(
        self,
        qa_pairs: List[Dict],
        batch_size: int
    ) -> List[Dict]:
        """Generate embeddings for questions and responses using GPU if available."""
        embeddings_data = []
        total_pairs = len(qa_pairs)
        
        # Log GPU info if using CUDA
        if self.device == "cuda" and TORCH_AVAILABLE:
            logger.info(f"🚀 Using GPU acceleration for embeddings")
            logger.info(f"   GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"   Batch size: {batch_size}")
        
        for i in range(0, total_pairs, batch_size):
            batch = qa_pairs[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_pairs + batch_size - 1) // batch_size
            
            # Extract texts
            questions = [item["question"] for item in batch]
            responses = [item["response"] for item in batch]
            combined_texts = [
                f"Question: {q}\nAnswer: {r}"
                for q, r in zip(questions, responses)
            ]
            
            # Generate embeddings
            try:
                # GPU'da batch processing daha hızlı
                question_embeddings = self.embedding_model.embed_documents(questions)
                response_embeddings = self.embedding_model.embed_documents(responses)
                combined_embeddings = self.embedding_model.embed_documents(combined_texts)
                
                # Store embeddings
                for j, item in enumerate(batch):
                    embeddings_data.append({
                        "id": item["id"],
                        "question_embedding": question_embeddings[j],
                        "response_embedding": response_embeddings[j],
                        "combined_embedding": combined_embeddings[j]
                    })
                
                # Progress logging
                processed = min(i + batch_size, total_pairs)
                progress_pct = (processed / total_pairs) * 100
                logger.info(
                    f"Generated embeddings: {processed}/{total_pairs} ({progress_pct:.1f}%) "
                    f"[Batch {batch_num}/{total_batches}]"
                )
                
                # GPU memory info (if using CUDA)
                if self.device == "cuda" and TORCH_AVAILABLE:
                    allocated = torch.cuda.memory_allocated(0) / 1024**3
                    reserved = torch.cuda.memory_reserved(0) / 1024**3
                    logger.debug(f"   GPU Memory: {allocated:.2f}GB allocated, {reserved:.2f}GB reserved")
            
            except Exception as e:
                logger.error(f"Error generating embeddings for batch {batch_num}: {str(e)}")
                if self.device == "cuda":
                    logger.error("Consider reducing batch_size if GPU memory error")
                continue
        
        logger.info(f"✅ Completed embedding generation for {len(embeddings_data)} Q&A pairs")
        return embeddings_data
    
    def _build_similarity_graph(
        self,
        embeddings_data: List[Dict],
        similarity_threshold: float
    ) -> Dict[str, List[str]]:
        """Build graph edges based on similarity."""
        graph_edges = defaultdict(list)
        
        # Extract combined embeddings
        embeddings_matrix = np.array([item["combined_embedding"] for item in embeddings_data])
        ids = [item["id"] for item in embeddings_data]
        
        logger.info("Computing similarity matrix...")
        
        # Compute cosine similarity
        similarity_matrix = cosine_similarity(embeddings_matrix)
        
        # Build edges
        for i, id1 in enumerate(ids):
            for j, id2 in enumerate(ids):
                if i != j and similarity_matrix[i][j] >= similarity_threshold:
                    graph_edges[id1].append({
                        "target": id2,
                        "similarity": float(similarity_matrix[i][j])
                    })
            
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1} nodes for graph building...")
        
        logger.info(f"Built graph with {sum(len(edges) for edges in graph_edges.values())} edges")
        
        return dict(graph_edges)
    
    def _store_in_milvus(
        self,
        qa_pairs: List[Dict],
        embeddings_data: List[Dict],
        graph_edges: Dict[str, List[str]],
        batch_size: int
    ):
        """Store Q&A pairs with embeddings and graph structure in Milvus."""
        # Create mapping for quick lookup
        embeddings_map = {item["id"]: item for item in embeddings_data}
        qa_map = {item["id"]: item for item in qa_pairs}
        
        # Prepare data for insertion
        data_to_insert = []
        
        for qa_pair in qa_pairs:
            qa_id = qa_pair["id"]
            
            # Get embeddings
            emb_data = embeddings_map.get(qa_id, {})
            
            # Get related nodes
            related_nodes = [
                edge["target"] for edge in graph_edges.get(qa_id, [])
            ]
            
            # Prepare data
            data_item = {
                "id": qa_id,
                "question": qa_pair["question"][:5000],  # Truncate if needed
                "response": qa_pair["response"][:10000],  # Truncate if needed
                "question_embedding": emb_data.get("question_embedding", []),
                "response_embedding": emb_data.get("response_embedding", []),
                "combined_embedding": emb_data.get("combined_embedding", []),
                "metadata": qa_pair.get("metadata", {}),
                "related_nodes": related_nodes[:50]  # Limit to top 50 related nodes
            }
            
            data_to_insert.append(data_item)
        
        # Insert in batches
        logger.info(f"Inserting {len(data_to_insert)} records into Milvus...")
        
        for i in range(0, len(data_to_insert), batch_size):
            batch = data_to_insert[i:i + batch_size]
            
            try:
                self.collection.insert(batch)
                logger.info(f"Inserted batch {i // batch_size + 1} ({len(batch)} records)")
            except Exception as e:
                logger.error(f"Error inserting batch {i // batch_size + 1}: {str(e)}")
                continue
        
        # Flush to ensure data is written
        self.collection.flush()
        logger.info("All data inserted and flushed successfully")
