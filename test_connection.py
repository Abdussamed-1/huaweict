"""Test Milvus Cloud Connection"""
import logging
from pymilvus import connections, utility
from config import (
    MILVUS_HOST, MILVUS_PORT, MILVUS_API_KEY,
    MILVUS_COLLECTION_NAME, MILVUS_USE_CLOUD
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test Milvus Cloud connection."""
    try:
        # Connect
        # Ensure port is integer for serverless compatibility
        port = int(MILVUS_PORT) if isinstance(MILVUS_PORT, str) else MILVUS_PORT
        
        connection_params = {
            "alias": "default",
            "host": MILVUS_HOST,
            "port": port
        }
        
        if MILVUS_USE_CLOUD and MILVUS_API_KEY:
            connection_params["token"] = MILVUS_API_KEY
            # For serverless, add secure connection
            if "serverless" in MILVUS_HOST.lower():
                connection_params["secure"] = True
            logger.info("Using API key authentication")
            logger.info(f"Connecting to: {MILVUS_HOST}:{port}")
        else:
            if MILVUS_USE_CLOUD:
                logger.error("❌ MILVUS_API_KEY is required for Milvus Cloud!")
                logger.error("Please set MILVUS_API_KEY in .env file")
                return False
            logger.warning("No API key provided, using default connection")
        
        connections.connect(**connection_params)
        logger.info(f"Connected to Milvus at {MILVUS_HOST}:{MILVUS_PORT}")
        
        # List collections
        collections = utility.list_collections()
        logger.info(f"Available collections: {collections}")
        
        # Check our collection
        if MILVUS_COLLECTION_NAME in collections:
            logger.info(f"Collection '{MILVUS_COLLECTION_NAME}' exists!")
            
            from pymilvus import Collection
            collection = Collection(MILVUS_COLLECTION_NAME)
            
            # Check indexes before loading
            try:
                indexes = collection.indexes
                logger.info(f"Found {len(indexes)} indexes")
                for idx in indexes:
                    logger.info(f"   - Index on: {idx.field_name}")
            except Exception as e:
                logger.warning(f"Could not check indexes: {str(e)}")
            
            # Try to load collection
            try:
                collection.load()
            except Exception as e:
                error_msg = str(e)
                if "no vector index" in error_msg.lower():
                    logger.error("Collection cannot be loaded: Missing vector indexes!")
                    logger.error("Please run build_graphrag.py to create indexes")
                    logger.error(f"Error details: {error_msg}")
                    return False
                else:
                    raise
            
            # Get entity count
            num_entities = collection.num_entities
            logger.info(f"Collection has {num_entities} entities")
            
            # Get schema info
            schema = collection.schema
            logger.info(f"Collection schema:")
            for field in schema.fields:
                logger.info(f"   - {field.name}: {field.dtype}")
        else:
            logger.warning(f"Collection '{MILVUS_COLLECTION_NAME}' not found")
            logger.info(f"Available collections: {collections}")
        
        logger.info("\nConnection test successful!")
        return True
        
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Milvus Cloud Connection Test")
    print("=" * 60)
    print(f"Host: {MILVUS_HOST}")
    print(f"Port: {MILVUS_PORT}")
    print(f"Use Cloud: {MILVUS_USE_CLOUD}")
    print(f"Collection: {MILVUS_COLLECTION_NAME}")
    print("=" * 60)
    print()
    
    success = test_connection()
    
    if success:
        print("\n[SUCCESS] Test completed successfully!")
        print("You can now run: python test_rag.py")
    else:
        print("\n[FAILED] Test failed!")
        print("Please check:")
        print("1. .env file configuration")
        print("2. API key is correct")
        print("3. Collection exists in Zilliz Cloud")
        print("4. Indexes are created (run build_graphrag.py if needed)")
        print("5. Network connection")
