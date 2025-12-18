"""Create missing indexes for Milvus collection"""
import logging
from pymilvus import Collection, connections, utility
from config import (
    MILVUS_HOST, MILVUS_PORT, MILVUS_API_KEY,
    MILVUS_COLLECTION_NAME, MILVUS_USE_CLOUD
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_indexes():
    """Create missing indexes for vector fields."""
    try:
        # Connect
        port = int(MILVUS_PORT) if isinstance(MILVUS_PORT, str) else MILVUS_PORT
        
        connection_params = {
            "alias": "default",
            "host": MILVUS_HOST,
            "port": port
        }
        
        if MILVUS_USE_CLOUD and MILVUS_API_KEY:
            connection_params["token"] = MILVUS_API_KEY
            if "serverless" in MILVUS_HOST.lower():
                connection_params["secure"] = True
        
        connections.connect(**connection_params)
        logger.info(f"Connected to Milvus at {MILVUS_HOST}:{port}")
        
        # Check collection exists
        if not utility.has_collection(MILVUS_COLLECTION_NAME):
            logger.error(f"Collection '{MILVUS_COLLECTION_NAME}' does not exist!")
            return False
        
        collection = Collection(MILVUS_COLLECTION_NAME)
        
        # Define index parameters
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        
        # Vector fields that need indexes
        vector_fields = ["question_embedding", "response_embedding", "combined_embedding"]
        
        # Check existing indexes
        existing_indexes = {}
        try:
            indexes = collection.indexes
            logger.info(f"Found {len(indexes)} existing indexes")
            for idx in indexes:
                # Index field_name can be a comma-separated string or a list
                if isinstance(idx.field_name, str):
                    fields = [f.strip() for f in idx.field_name.split(",")]
                else:
                    fields = idx.field_name
                
                for field in fields:
                    existing_indexes[field] = True
                    logger.info(f"  - Index exists for: {field}")
        except Exception as e:
            logger.warning(f"Could not get existing indexes: {str(e)}")
        
        # Create missing indexes
        created_count = 0
        for field_name in vector_fields:
            if field_name not in existing_indexes:
                try:
                    logger.info(f"Creating index for field: {field_name}")
                    collection.create_index(
                        field_name=field_name,
                        index_params=index_params
                    )
                    logger.info(f"Successfully created index for {field_name}")
                    created_count += 1
                except Exception as e:
                    error_msg = str(e)
                    if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                        logger.info(f"Index for {field_name} already exists (skipping)")
                    else:
                        logger.error(f"Error creating index for {field_name}: {error_msg}")
                        return False
            else:
                logger.info(f"Index for {field_name} already exists (skipping)")
        
        if created_count > 0:
            logger.info(f"\nCreated {created_count} new indexes")
            logger.info("Indexes are being built in the background...")
            logger.info("You can check status in Zilliz Cloud console")
        else:
            logger.info("\nAll required indexes already exist!")
        
        # Try to load collection to verify
        try:
            collection.load()
            logger.info("Collection loaded successfully!")
            logger.info(f"Total entities: {collection.num_entities}")
        except Exception as e:
            logger.warning(f"Could not load collection (may still be building indexes): {str(e)}")
            logger.info("Wait a few minutes and try test_connection.py again")
        
        logger.info("\nIndex creation completed!")
        return True
        
    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Create Missing Indexes")
    print("=" * 60)
    print(f"Collection: {MILVUS_COLLECTION_NAME}")
    print("=" * 60)
    print()
    
    success = create_indexes()
    
    if success:
        print("\n[SUCCESS] Index creation completed!")
        print("Run: python test_connection.py to verify")
    else:
        print("\n[FAILED] Index creation failed!")
        print("Please check the error messages above")
