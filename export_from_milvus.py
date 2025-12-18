"""
Milvus Export Script - Export data from Milvus to various formats
Supports: CSV, JSON, SQL (PostgreSQL, MySQL), Excel
"""
import logging
import json
import csv
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
import pandas as pd
from config import (
    MILVUS_HOST, MILVUS_PORT, MILVUS_API_KEY, MILVUS_COLLECTION_NAME,
    MILVUS_USE_CLOUD
)

try:
    from pymilvus import connections, Collection, utility
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    logging.error("pymilvus not available!")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MilvusExporter:
    """Export data from Milvus vector database to various formats."""
    
    def __init__(self):
        """Initialize exporter with Milvus connection."""
        if not MILVUS_AVAILABLE:
            raise RuntimeError("Milvus not available. Install pymilvus.")
        
        self._connect_milvus()
        
        # Load collection
        if utility.has_collection(MILVUS_COLLECTION_NAME):
            self.collection = Collection(MILVUS_COLLECTION_NAME)
            self.collection.load()
            logger.info(f"✅ Collection '{MILVUS_COLLECTION_NAME}' loaded")
        else:
            raise RuntimeError(f"Collection '{MILVUS_COLLECTION_NAME}' does not exist!")
    
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
    
    def export_to_csv(
        self,
        output_path: str,
        include_embeddings: bool = False,
        batch_size: int = 1000
    ):
        """
        Export Milvus collection to CSV file.
        
        Args:
            output_path: Output CSV file path
            include_embeddings: Whether to include embedding vectors (can be large)
            batch_size: Number of records to fetch per batch
        """
        logger.info(f"Exporting to CSV: {output_path}")
        
        # Get total count
        total_count = self.collection.num_entities
        logger.info(f"Total records to export: {total_count}")
        
        # Fetch all records in batches
        all_records = []
        offset = 0
        
        while offset < total_count:
            limit = min(batch_size, total_count - offset)
            logger.info(f"Fetching batch: {offset+1}-{offset+limit}/{total_count}")
            
            # Query records
            results = self.collection.query(
                expr=f"id >= \"\"",
                limit=limit,
                offset=offset,
                output_fields=["id", "question", "response", "metadata", "related_nodes"]
            )
            
            if not results:
                break
            
            all_records.extend(results)
            offset += limit
        
        # Convert to DataFrame
        df_data = []
        for record in all_records:
            row = {
                "id": record.get("id", ""),
                "question": record.get("question", ""),
                "response": record.get("response", ""),
                "metadata": json.dumps(record.get("metadata", {})) if record.get("metadata") else "",
                "related_nodes": json.dumps(record.get("related_nodes", [])) if record.get("related_nodes") else ""
            }
            
            # Include embeddings if requested
            if include_embeddings:
                row["question_embedding"] = json.dumps(record.get("question_embedding", []))
                row["response_embedding"] = json.dumps(record.get("response_embedding", []))
                row["combined_embedding"] = json.dumps(record.get("combined_embedding", []))
            
            df_data.append(row)
        
        # Save to CSV
        df = pd.DataFrame(df_data)
        df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"✅ Exported {len(df_data)} records to {output_path}")
    
    def export_to_json(
        self,
        output_path: str,
        include_embeddings: bool = False,
        batch_size: int = 1000
    ):
        """
        Export Milvus collection to JSON file.
        
        Args:
            output_path: Output JSON file path
            include_embeddings: Whether to include embedding vectors
            batch_size: Number of records to fetch per batch
        """
        logger.info(f"Exporting to JSON: {output_path}")
        
        total_count = self.collection.num_entities
        logger.info(f"Total records to export: {total_count}")
        
        all_records = []
        offset = 0
        
        while offset < total_count:
            limit = min(batch_size, total_count - offset)
            logger.info(f"Fetching batch: {offset+1}-{offset+limit}/{total_count}")
            
            results = self.collection.query(
                expr=f"id >= \"\"",
                limit=limit,
                offset=offset,
                output_fields=["id", "question", "response", "metadata", "related_nodes"]
            )
            
            if not results:
                break
            
            # Prepare records
            for record in results:
                export_record = {
                    "id": record.get("id", ""),
                    "question": record.get("question", ""),
                    "response": record.get("response", ""),
                    "metadata": record.get("metadata", {}),
                    "related_nodes": record.get("related_nodes", [])
                }
                
                if include_embeddings:
                    export_record["question_embedding"] = record.get("question_embedding", [])
                    export_record["response_embedding"] = record.get("response_embedding", [])
                    export_record["combined_embedding"] = record.get("combined_embedding", [])
                
                all_records.append(export_record)
            
            offset += limit
        
        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_records, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Exported {len(all_records)} records to {output_path}")
    
    def export_to_sql(
        self,
        connection_string: str,
        table_name: str = "medical_qa",
        include_embeddings: bool = False,
        batch_size: int = 1000
    ):
        """
        Export Milvus collection to SQL database.
        
        Args:
            connection_string: SQLAlchemy connection string
            table_name: Target table name
            include_embeddings: Whether to include embedding vectors
            batch_size: Number of records to insert per batch
        """
        try:
            import sqlalchemy
            engine = sqlalchemy.create_engine(connection_string)
            logger.info("✅ Connected to SQL database")
        except ImportError:
            raise RuntimeError("sqlalchemy not installed. Install: pip install sqlalchemy")
        
        logger.info(f"Exporting to SQL table: {table_name}")
        
        total_count = self.collection.num_entities
        logger.info(f"Total records to export: {total_count}")
        
        # Create table if not exists
        self._create_sql_table(engine, table_name, include_embeddings)
        
        # Fetch and insert in batches
        offset = 0
        inserted_count = 0
        
        while offset < total_count:
            limit = min(batch_size, total_count - offset)
            logger.info(f"Processing batch: {offset+1}-{offset+limit}/{total_count}")
            
            # Fetch records
            results = self.collection.query(
                expr=f"id >= \"\"",
                limit=limit,
                offset=offset,
                output_fields=["id", "question", "response", "metadata", "related_nodes"]
            )
            
            if not results:
                break
            
            # Prepare data for SQL
            df_data = []
            for record in results:
                row = {
                    "id": record.get("id", ""),
                    "question": record.get("question", ""),
                    "response": record.get("response", ""),
                    "metadata": json.dumps(record.get("metadata", {})) if record.get("metadata") else None,
                    "related_nodes": json.dumps(record.get("related_nodes", [])) if record.get("related_nodes") else None,
                    "exported_at": datetime.now()
                }
                
                if include_embeddings:
                    row["question_embedding"] = json.dumps(record.get("question_embedding", []))
                    row["response_embedding"] = json.dumps(record.get("response_embedding", []))
                    row["combined_embedding"] = json.dumps(record.get("combined_embedding", []))
                
                df_data.append(row)
            
            # Insert to SQL
            df = pd.DataFrame(df_data)
            df.to_sql(table_name, engine, if_exists='append', index=False, method='multi')
            inserted_count += len(df_data)
            
            offset += limit
        
        logger.info(f"✅ Exported {inserted_count} records to SQL table: {table_name}")
    
    def _create_sql_table(self, engine, table_name: str, include_embeddings: bool):
        """Create SQL table if not exists."""
        import sqlalchemy
        
        # Define schema
        columns = [
            sqlalchemy.Column("id", sqlalchemy.String(100), primary_key=True),
            sqlalchemy.Column("question", sqlalchemy.Text),
            sqlalchemy.Column("response", sqlalchemy.Text),
            sqlalchemy.Column("metadata", sqlalchemy.JSON),
            sqlalchemy.Column("related_nodes", sqlalchemy.JSON),
            sqlalchemy.Column("exported_at", sqlalchemy.DateTime)
        ]
        
        if include_embeddings:
            columns.extend([
                sqlalchemy.Column("question_embedding", sqlalchemy.Text),
                sqlalchemy.Column("response_embedding", sqlalchemy.Text),
                sqlalchemy.Column("combined_embedding", sqlalchemy.Text)
            ])
        
        table = sqlalchemy.Table(table_name, sqlalchemy.MetaData(), *columns)
        table.create(engine, checkfirst=True)
        logger.info(f"✅ SQL table '{table_name}' ready")
    
    def export_to_excel(
        self,
        output_path: str,
        include_embeddings: bool = False,
        batch_size: int = 1000
    ):
        """
        Export Milvus collection to Excel file.
        
        Args:
            output_path: Output Excel file path
            include_embeddings: Whether to include embedding vectors
            batch_size: Number of records to fetch per batch
        """
        logger.info(f"Exporting to Excel: {output_path}")
        
        total_count = self.collection.num_entities
        logger.info(f"Total records to export: {total_count}")
        
        all_records = []
        offset = 0
        
        while offset < total_count:
            limit = min(batch_size, total_count - offset)
            logger.info(f"Fetching batch: {offset+1}-{offset+limit}/{total_count}")
            
            results = self.collection.query(
                expr=f"id >= \"\"",
                limit=limit,
                offset=offset,
                output_fields=["id", "question", "response", "metadata", "related_nodes"]
            )
            
            if not results:
                break
            
            for record in results:
                row = {
                    "id": record.get("id", ""),
                    "question": record.get("question", ""),
                    "response": record.get("response", ""),
                    "metadata": json.dumps(record.get("metadata", {})) if record.get("metadata") else "",
                    "related_nodes": json.dumps(record.get("related_nodes", [])) if record.get("related_nodes") else ""
                }
                
                if include_embeddings:
                    row["question_embedding"] = json.dumps(record.get("question_embedding", []))
                    row["response_embedding"] = json.dumps(record.get("response_embedding", []))
                    row["combined_embedding"] = json.dumps(record.get("combined_embedding", []))
                
                all_records.append(row)
            
            offset += limit
        
        # Save to Excel
        df = pd.DataFrame(all_records)
        df.to_excel(output_path, index=False, engine='openpyxl')
        logger.info(f"✅ Exported {len(all_records)} records to {output_path}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        total_count = self.collection.num_entities
        
        # Sample a few records to get metadata info
        sample = self.collection.query(
            expr="id >= \"\"",
            limit=10,
            output_fields=["metadata"]
        )
        
        stats = {
            "total_records": total_count,
            "collection_name": MILVUS_COLLECTION_NAME,
            "sample_size": len(sample),
            "has_metadata": any(r.get("metadata") for r in sample),
            "has_related_nodes": any(r.get("related_nodes") for r in sample)
        }
        
        return stats


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export data from Milvus')
    parser.add_argument('--format', type=str, required=True,
                        choices=['csv', 'json', 'sql', 'excel'],
                        help='Export format')
    parser.add_argument('--output', type=str, required=True,
                        help='Output file path or SQL connection string')
    parser.add_argument('--include-embeddings', action='store_true',
                        help='Include embedding vectors in export')
    parser.add_argument('--batch-size', type=int, default=1000,
                        help='Batch size for processing')
    parser.add_argument('--table-name', type=str, default='medical_qa',
                        help='SQL table name (for SQL export)')
    parser.add_argument('--stats', action='store_true',
                        help='Show collection statistics only')
    
    args = parser.parse_args()
    
    exporter = MilvusExporter()
    
    # Show stats if requested
    if args.stats:
        stats = exporter.get_collection_stats()
        print("\n" + "=" * 60)
        print("Collection Statistics")
        print("=" * 60)
        for key, value in stats.items():
            print(f"{key}: {value}")
        return 0
    
    try:
        if args.format == 'csv':
            exporter.export_to_csv(
                output_path=args.output,
                include_embeddings=args.include_embeddings,
                batch_size=args.batch_size
            )
        elif args.format == 'json':
            exporter.export_to_json(
                output_path=args.output,
                include_embeddings=args.include_embeddings,
                batch_size=args.batch_size
            )
        elif args.format == 'sql':
            exporter.export_to_sql(
                connection_string=args.output,
                table_name=args.table_name,
                include_embeddings=args.include_embeddings,
                batch_size=args.batch_size
            )
        elif args.format == 'excel':
            exporter.export_to_excel(
                output_path=args.output,
                include_embeddings=args.include_embeddings,
                batch_size=args.batch_size
            )
        
        print("\n✅ Export completed successfully!")
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

