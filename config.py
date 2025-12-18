"""
Configuration file for Huawei Cloud services and application settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ------------------ API Keys ------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")  # For Huawei ModelArts DeepSeek integration

# ------------------ Milvus Configuration ------------------
# For Milvus Cloud Cluster:
# MILVUS_HOST: Public endpoint URL (e.g., xxx.gcp-us-west1.vectordb.zillizcloud.com)
# MILVUS_PORT: Usually 443 (HTTPS) or 19530
# MILVUS_API_KEY: API key/token from Milvus Cloud console
# MILVUS_USER: Username (if using username/password auth)
# MILVUS_PASSWORD: Password (if using username/password auth)
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))  # Convert to int for serverless compatibility
MILVUS_API_KEY = os.getenv("MILVUS_API_KEY", "")  # For Milvus Cloud authentication
MILVUS_USER = os.getenv("MILVUS_USER", "")
MILVUS_PASSWORD = os.getenv("MILVUS_PASSWORD", "")
MILVUS_COLLECTION_NAME = os.getenv("MILVUS_COLLECTION_NAME", "medical_knowledge_base")
MILVUS_USE_CLOUD = os.getenv("MILVUS_USE_CLOUD", "false").lower() == "true"  # Set to true for cloud cluster

# ------------------ OBS (Object Storage Service) Configuration ------------------
OBS_ACCESS_KEY = os.getenv("OBS_ACCESS_KEY", "")
OBS_SECRET_KEY = os.getenv("OBS_SECRET_KEY", "")
OBS_ENDPOINT = os.getenv("OBS_ENDPOINT", "")
OBS_BUCKET_NAME = os.getenv("OBS_BUCKET_NAME", "")

# ------------------ ModelArts Configuration ------------------
MODELARTS_ENDPOINT = os.getenv("MODELARTS_ENDPOINT", "")
MODELARTS_PROJECT_ID = os.getenv("MODELARTS_PROJECT_ID", "")
MODELARTS_MODEL_NAME = os.getenv("MODELARTS_MODEL_NAME", "deepseek-v3.1")

# ------------------ Embedding Configuration ------------------
# Using all-mpnet-base-v2 for better medical text understanding (768 dimensions)
# Alternative: "sentence-transformers/all-MiniLM-L6-v2" (384 dimensions, faster)
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-mpnet-base-v2")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))
# GPU Configuration: 'cuda' for GPU, 'cpu' for CPU, 'auto' to auto-detect
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "auto")  # auto, cuda, cpu

# ------------------ LLM Configuration ------------------
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")  # Can be switched to DeepSeek v3.1
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))

# ------------------ RAG Configuration ------------------
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
RETRIEVAL_SCORE_THRESHOLD = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.7"))

# ------------------ GraphRAG Configuration ------------------
GRAPH_RAG_ENABLED = os.getenv("GRAPH_RAG_ENABLED", "true").lower() == "true"
GRAPH_MAX_NODES = int(os.getenv("GRAPH_MAX_NODES", "10"))
GRAPH_MAX_DEPTH = int(os.getenv("GRAPH_MAX_DEPTH", "2"))  # Default depth for graph traversal
GRAPH_SIMILARITY_THRESHOLD = float(os.getenv("GRAPH_SIMILARITY_THRESHOLD", "0.7"))  # For edge creation

# ------------------ Agentic RAG Configuration ------------------
AGENTIC_RAG_ENABLED = os.getenv("AGENTIC_RAG_ENABLED", "true").lower() == "true"
AGENT_MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "5"))
AGENT_REASONING_ENABLED = os.getenv("AGENT_REASONING_ENABLED", "true").lower() == "true"

# ------------------ RDS (Relational Database) Configuration ------------------
RDS_HOST = os.getenv("RDS_HOST", "")
RDS_PORT = os.getenv("RDS_PORT", "5432")
RDS_DB = os.getenv("RDS_DB", "medical_db")
RDS_USER = os.getenv("RDS_USER", "")
RDS_PASSWORD = os.getenv("RDS_PASSWORD", "")
RDS_ENGINE = os.getenv("RDS_ENGINE", "postgresql")  # postgresql or mysql

# ------------------ Application Configuration ------------------
VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", "./medical_vectorstore")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

