"""
Database Migration Script - Migrate data from external database to Milvus
Supports: SQL databases, CSV, JSON, Excel files
"""
import logging
import os
import json
import uuid
from typing import List, Dict, Optional, Any, Iterator
from datetime import datetime
import pandas as pd
from config import (
    MILVUS_HOST, MILVUS_PORT, MILVUS_API_KEY, MILVUS_COLLECTION_NAME,
    MILVUS_USE_CLOUD, EMBEDDING_MODEL_NAME, EMBEDDING_DIMENSION
)

try:
    from pymilvus import connections, Collection, utility
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    logging.error("pymilvus not available!")

try:
    from langchain_huggingface import HuggingFaceEmbeddings
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False
    logging.error("langchain_huggingface not available!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Migrate data from external sources to Milvus vector database."""
    
    def __init__(self):
        """Initialize migrator with Milvus connection and embedding model."""
        if not MILVUS_AVAILABLE:
            raise RuntimeError("Milvus not available. Install pymilvus.")
        
        if not EMBEDDING_AVAILABLE:
            raise RuntimeError("Embedding model not available. Install langchain_huggingface.")
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME
        )
        self.embedding_dim = EMBEDDING_DIMENSION
        logger.info(f"✅ Embedding model loaded (dimension: {self.embedding_dim})")
        
        # Connect to Milvus
        self._connect_milvus()
        
        # Load collection
        if utility.has_collection(MILVUS_COLLECTION_NAME):
            self.collection = Collection(MILVUS_COLLECTION_NAME)
            self.collection.load()
            logger.info(f"✅ Collection '{MILVUS_COLLECTION_NAME}' loaded")
        else:
            raise RuntimeError(f"Collection '{MILVUS_COLLECTION_NAME}' does not exist! Create it first.")
    
    def _connect_milvus(self):
        """Connect to Milvus."""
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
        logger.info(f"✅ Connected to Milvus at {MILVUS_HOST}:{port}")
    
    def migrate_from_sql(
        self,
        connection_string: str,
        query: str,
        question_column: str,
        response_column: str,
        id_column: Optional[str] = None,
        metadata_columns: Optional[List[str]] = None,
        batch_size: int = 100
    ):
        """
        Migrate data from SQL database.
        
        Args:
            connection_string: SQLAlchemy connection string (e.g., 'postgresql://user:pass@host/db')
            query: SQL query to fetch data
            question_column: Column name for questions
            response_column: Column name for responses
            id_column: Column name for IDs (if None, generates UUIDs)
            metadata_columns: List of column names to include in metadata
            batch_size: Number of records to process in each batch
        """
        try:
            import sqlalchemy
            engine = sqlalchemy.create_engine(connection_string)
            logger.info("✅ Connected to SQL database")
        except ImportError:
            raise RuntimeError("sqlalchemy not installed. Install: pip install sqlalchemy")
        
        # Fetch data
        logger.info(f"Executing query: {query}")
        df = pd.read_sql(query, engine)
        logger.info(f"✅ Fetched {len(df)} records from SQL database")
        
        # Process and insert
        self._process_dataframe(
            df=df,
            question_column=question_column,
            response_column=response_column,
            id_column=id_column,
            metadata_columns=metadata_columns,
            batch_size=batch_size
        )
    
    def migrate_from_csv(
        self,
        csv_path: str,
        question_column: str,
        response_column: str,
        id_column: Optional[str] = None,
        metadata_columns: Optional[List[str]] = None,
        batch_size: int = 100,
        encoding: str = 'utf-8'
    ):
        """
        Migrate data from CSV file.
        
        Args:
            csv_path: Path to CSV file
            question_column: Column name for questions
            response_column: Column name for responses
            id_column: Column name for IDs (if None, generates UUIDs)
            metadata_columns: List of column names to include in metadata
            batch_size: Number of records to process in each batch
            encoding: File encoding (default: utf-8)
        """
        logger.info(f"Reading CSV file: {csv_path}")
        df = pd.read_csv(csv_path, encoding=encoding)
        logger.info(f"✅ Loaded {len(df)} records from CSV")
        
        self._process_dataframe(
            df=df,
            question_column=question_column,
            response_column=response_column,
            id_column=id_column,
            metadata_columns=metadata_columns,
            batch_size=batch_size
        )
    
    def migrate_from_json(
        self,
        json_path: str,
        question_key: str,
        response_key: str,
        id_key: Optional[str] = None,
        metadata_keys: Optional[List[str]] = None,
        batch_size: int = 100
    ):
        """
        Migrate data from JSON file.
        
        Args:
            json_path: Path to JSON file
            question_key: Key name for questions in JSON objects
            response_key: Key name for responses in JSON objects
            id_key: Key name for IDs (if None, generates UUIDs)
            metadata_keys: List of keys to include in metadata
            batch_size: Number of records to process in each batch
        """
        logger.info(f"Reading JSON file: {json_path}")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert to DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # If JSON is a dict with a list value
            df = pd.DataFrame(list(data.values())[0]) if data else pd.DataFrame()
        else:
            raise ValueError("JSON must be a list or dict with list values")
        
        logger.info(f"✅ Loaded {len(df)} records from JSON")
        
        # Rename columns to match expected format
        column_mapping = {
            question_key: 'question',
            response_key: 'response'
        }
        if id_key:
            column_mapping[id_key] = 'id'
        
        df = df.rename(columns=column_mapping)
        
        # Process metadata
        metadata_cols = []
        if metadata_keys:
            for key in metadata_keys:
                if key in df.columns:
                    metadata_cols.append(key)
        
        self._process_dataframe(
            df=df,
            question_column='question',
            response_column='response',
            id_column='id' if id_key else None,
            metadata_columns=metadata_cols,
            batch_size=batch_size
        )
    
    def migrate_from_excel(
        self,
        excel_path: str,
        sheet_name: str = 0,
        question_column: str = None,
        response_column: str = None,
        id_column: Optional[str] = None,
        metadata_columns: Optional[List[str]] = None,
        batch_size: int = 100
    ):
        """
        Migrate data from Excel file.
        
        Args:
            excel_path: Path to Excel file
            sheet_name: Sheet name or index (default: first sheet)
            question_column: Column name for questions
            response_column: Column name for responses
            id_column: Column name for IDs (if None, generates UUIDs)
            metadata_columns: List of column names to include in metadata
            batch_size: Number of records to process in each batch
        """
        logger.info(f"Reading Excel file: {excel_path}")
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        logger.info(f"✅ Loaded {len(df)} records from Excel")
        
        self._process_dataframe(
            df=df,
            question_column=question_column,
            response_column=response_column,
            id_column=id_column,
            metadata_columns=metadata_columns,
            batch_size=batch_size
        )
    
    def _process_dataframe(
        self,
        df: pd.DataFrame,
        question_column: str,
        response_column: str,
        id_column: Optional[str],
        metadata_columns: Optional[List[str]],
        batch_size: int
    ):
        """
        Process DataFrame and insert into Milvus.
        
        Args:
            df: DataFrame with data
            question_column: Column name for questions
            response_column: Column name for responses
            id_column: Column name for IDs
            metadata_columns: List of metadata columns
            batch_size: Batch size for processing
        """
        # Validate columns
        if question_column not in df.columns:
            raise ValueError(f"Column '{question_column}' not found in data")
        if response_column not in df.columns:
            raise ValueError(f"Column '{response_column}' not found in data")
        
        # Generate IDs if not provided
        if id_column and id_column in df.columns:
            df['_id'] = df[id_column].astype(str)
        else:
            df['_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        
        # Prepare metadata
        metadata_cols = metadata_columns or []
        
        total_records = len(df)
        logger.info(f"Processing {total_records} records in batches of {batch_size}...")
        
        # Process in batches
        for batch_start in range(0, total_records, batch_size):
            batch_end = min(batch_start + batch_size, total_records)
            batch_df = df.iloc[batch_start:batch_end]
            
            logger.info(f"Processing batch {batch_start//batch_size + 1} ({batch_start+1}-{batch_end}/{total_records})...")
            
            # Prepare batch data
            batch_data = self._prepare_batch(
                batch_df,
                question_column,
                response_column,
                metadata_cols
            )
            
            # Insert into Milvus
            try:
                self.collection.insert(batch_data)
                logger.info(f"✅ Inserted batch {batch_start//batch_size + 1}")
            except Exception as e:
                logger.error(f"❌ Error inserting batch {batch_start//batch_size + 1}: {e}")
                raise
        
        # Flush and build graph relationships
        logger.info("Flushing collection...")
        self.collection.flush()
        
        logger.info("Building graph relationships...")
        self._build_graph_relationships()
        
        logger.info(f"✅ Migration complete! Inserted {total_records} records")
    
    def _prepare_batch(
        self,
        df: pd.DataFrame,
        question_column: str,
        response_column: str,
        metadata_columns: List[str]
    ) -> List[Dict]:
        """
        Prepare batch data for Milvus insertion.
        
        Args:
            df: DataFrame batch
            question_column: Question column name
            response_column: Response column name
            metadata_columns: Metadata columns
            
        Returns:
            List of dictionaries ready for Milvus insertion
        """
        batch_data = []
        
        for _, row in df.iterrows():
            question = str(row[question_column]) if pd.notna(row[question_column]) else ""
            response = str(row[response_column]) if pd.notna(row[response_column]) else ""
            
            # Skip empty rows
            if not question or not response:
                continue
            
            # Generate embeddings
            question_embedding = self.embedding_model.embed_query(question)
            response_embedding = self.embedding_model.embed_query(response)
            
            # Combined embedding (question + response)
            combined_text = f"{question} {response}"
            combined_embedding = self.embedding_model.embed_query(combined_text)
            
            # Prepare metadata
            metadata = {}
            for col in metadata_columns:
                if col in row.index and pd.notna(row[col]):
                    metadata[col] = str(row[col])
            
            # Add migration metadata
            metadata['migrated_at'] = datetime.now().isoformat()
            metadata['source'] = 'database_migration'
            
            # Prepare record
            record = {
                "id": str(row['_id']),
                "question": question[:5000],  # Limit to max_length
                "response": response[:10000],  # Limit to max_length
                "question_embedding": question_embedding,
                "response_embedding": response_embedding,
                "combined_embedding": combined_embedding,
                "metadata": metadata,
                "related_nodes": []  # Will be populated by _build_graph_relationships
            }
            
            batch_data.append(record)
        
        return batch_data
    
    def _build_graph_relationships(self, similarity_threshold: float = 0.7):
        """
        Build graph relationships between nodes based on similarity.
        
        Args:
            similarity_threshold: Minimum similarity to create an edge
        """
        logger.info("Building graph relationships...")
        
        # Get all records
        all_records = self.collection.query(
            expr="id >= \"\"",
            output_fields=["id", "combined_embedding"]
        )
        
        if len(all_records) < 2:
            logger.info("Not enough records to build relationships")
            return
        
        logger.info(f"Processing {len(all_records)} records for graph relationships...")
        
        # Calculate similarities and build relationships
        embeddings = [r['combined_embedding'] for r in all_records]
        ids = [r['id'] for r in all_records]
        
        # Batch process similarities
        batch_size = 100
        related_nodes_dict = {}
        
        for i in range(0, len(embeddings), batch_size):
            batch_embeddings = embeddings[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            # Calculate cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            batch_array = np.array(batch_embeddings)
            similarities = cosine_similarity(batch_array)
            
            # Find related nodes
            for j, record_id in enumerate(batch_ids):
                related = []
                for k, other_id in enumerate(ids):
                    if record_id != other_id:
                        if i <= k < i + len(batch_ids):
                            sim = similarities[j][k - i]
                        else:
                            # Calculate similarity with other batch
                            sim = cosine_similarity(
                                [embeddings[ids.index(record_id)]],
                                [embeddings[k]]
                            )[0][0]
                        
                        if sim >= similarity_threshold:
                            related.append(other_id)
                
                # Keep top 20 related nodes
                related_nodes_dict[record_id] = related[:20]
        
        # Update records with related_nodes
        logger.info("Updating records with related nodes...")
        for record_id, related_nodes in related_nodes_dict.items():
            try:
                self.collection.upsert([{
                    "id": record_id,
                    "related_nodes": related_nodes
                }])
            except Exception as e:
                logger.warning(f"Could not update related_nodes for {record_id}: {e}")
        
        self.collection.flush()
        logger.info("✅ Graph relationships built!")


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate data to Milvus')
    parser.add_argument('--source', type=str, required=True,
                        choices=['sql', 'csv', 'json', 'excel'],
                        help='Source data type')
    parser.add_argument('--input', type=str, required=True,
                        help='Input file path or SQL connection string')
    parser.add_argument('--question', type=str, required=True,
                        help='Question column/key name')
    parser.add_argument('--response', type=str, required=True,
                        help='Response column/key name')
    parser.add_argument('--id', type=str, default=None,
                        help='ID column/key name (optional)')
    parser.add_argument('--metadata', type=str, nargs='*',
                        help='Metadata columns/keys to include')
    parser.add_argument('--batch-size', type=int, default=100,
                        help='Batch size for processing')
    
    # SQL-specific
    parser.add_argument('--query', type=str,
                        help='SQL query (for SQL source)')
    
    # Excel-specific
    parser.add_argument('--sheet', type=str, default=0,
                        help='Sheet name or index (for Excel)')
    
    args = parser.parse_args()
    
    migrator = DatabaseMigrator()
    
    try:
        if args.source == 'sql':
            if not args.query:
                raise ValueError("--query is required for SQL source")
            migrator.migrate_from_sql(
                connection_string=args.input,
                query=args.query,
                question_column=args.question,
                response_column=args.response,
                id_column=args.id,
                metadata_columns=args.metadata,
                batch_size=args.batch_size
            )
        elif args.source == 'csv':
            migrator.migrate_from_csv(
                csv_path=args.input,
                question_column=args.question,
                response_column=args.response,
                id_column=args.id,
                metadata_columns=args.metadata,
                batch_size=args.batch_size
            )
        elif args.source == 'json':
            migrator.migrate_from_json(
                json_path=args.input,
                question_key=args.question,
                response_key=args.response,
                id_key=args.id,
                metadata_keys=args.metadata,
                batch_size=args.batch_size
            )
        elif args.source == 'excel':
            migrator.migrate_from_excel(
                excel_path=args.input,
                sheet_name=args.sheet,
                question_column=args.question,
                response_column=args.response,
                id_column=args.id,
                metadata_columns=args.metadata,
                batch_size=args.batch_size
            )
        
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

