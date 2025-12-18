"""
Build GraphRAG from Medical Dataset
This script loads the medical dataset from HuggingFace and builds a GraphRAG structure in Milvus.
"""
import logging
import sys
from dataset_loader import MedicalDatasetLoader
from graphrag_builder import GraphRAGBuilder
from config import (
    MILVUS_HOST, MILVUS_PORT, MILVUS_COLLECTION_NAME,
    MILVUS_API_KEY, MILVUS_USER, MILVUS_PASSWORD, MILVUS_USE_CLOUD,
    EMBEDDING_MODEL_NAME, GRAPH_SIMILARITY_THRESHOLD, EMBEDDING_DEVICE
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to build GraphRAG."""
    
    # Configuration
    dataset_name = "FreedomIntelligence/medical-o1-reasoning-SFT"
    dataset_subset = "en"  # Use English subset
    max_samples = None  # Set to None to process all, or a number like 1000 for testing
    
    logger.info("=" * 60)
    logger.info("GraphRAG Builder for Medical Q&A Dataset")
    logger.info("=" * 60)
    
    try:
        # Step 1: Load dataset
        logger.info("\n[Step 1/4] Loading dataset from HuggingFace...")
        loader = MedicalDatasetLoader(dataset_name)
        dataset = loader.load_dataset(split="train", subset=dataset_subset)
        
        # Step 2: Process Q&A pairs
        logger.info("\n[Step 2/4] Processing Q&A pairs...")
        qa_pairs = loader.process_qa_pairs(max_samples=max_samples)
        
        # Show statistics
        stats = loader.get_statistics()
        logger.info("\nDataset Statistics:")
        logger.info(f"  Total Q&A pairs: {stats.get('total_pairs', 0)}")
        logger.info(f"  Average question length: {stats.get('average_question_length', 0):.1f} chars")
        logger.info(f"  Average response length: {stats.get('average_response_length', 0):.1f} chars")
        
        # Show sample
        logger.info("\nSample Q&A pair:")
        sample = loader.get_sample(1)[0]
        logger.info(f"  Question: {sample['question'][:100]}...")
        logger.info(f"  Response: {sample['response'][:100]}...")
        
        # Step 3: Initialize GraphRAG builder
        logger.info("\n[Step 3/4] Initializing GraphRAG builder...")
        logger.info(f"  Milvus: {MILVUS_HOST}:{MILVUS_PORT}")
        logger.info(f"  Collection: {MILVUS_COLLECTION_NAME}")
        logger.info(f"  Embedding model: {EMBEDDING_MODEL_NAME}")
        logger.info(f"  Device: {EMBEDDING_DEVICE} (auto-detecting GPU if available)")
        logger.info(f"  Similarity threshold: {GRAPH_SIMILARITY_THRESHOLD}")
        
        builder = GraphRAGBuilder(
            milvus_host=MILVUS_HOST,
            milvus_port=MILVUS_PORT,
            collection_name=MILVUS_COLLECTION_NAME,
            embedding_model_name=EMBEDDING_MODEL_NAME,
            milvus_api_key=MILVUS_API_KEY,
            milvus_user=MILVUS_USER,
            milvus_password=MILVUS_PASSWORD,
            use_cloud=MILVUS_USE_CLOUD,
            device=EMBEDDING_DEVICE
        )
        
        # Step 4: Create collection (drop existing if needed)
        logger.info("\n[Step 4/4] Creating Milvus collection...")
        drop_existing = input("\nDrop existing collection? (y/n): ").lower() == 'y'
        builder.create_collection(drop_existing=drop_existing)
        
        # Step 5: Build graph
        logger.info("\nBuilding GraphRAG structure...")
        logger.info("This may take a while depending on dataset size...")
        
        # Batch size will be auto-determined based on device (GPU/CPU)
        builder.build_graph_from_qa_pairs(
            qa_pairs=qa_pairs,
            similarity_threshold=GRAPH_SIMILARITY_THRESHOLD,
            batch_size=None  # Auto-detect: 200 for GPU, 50 for CPU
        )
        
        logger.info("\n" + "=" * 60)
        logger.info("GraphRAG build completed successfully!")
        logger.info("=" * 60)
        logger.info(f"\nYou can now use the RAG service with GraphRAG enabled.")
        logger.info(f"Collection '{MILVUS_COLLECTION_NAME}' is ready for queries.")
        
    except KeyboardInterrupt:
        logger.warning("\nBuild interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nError building GraphRAG: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
