"""
RDS Client for Huawei Cloud PostgreSQL/MySQL
Handles relational database operations for metadata, relations, and analytics.
"""
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, execute_values
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False
    logging.warning("psycopg2 not available. PostgreSQL features disabled.")

try:
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    logging.warning("pymysql not available. MySQL features disabled.")

from config import (
    RDS_HOST, RDS_PORT, RDS_DB, RDS_USER, RDS_PASSWORD, RDS_ENGINE
)

logger = logging.getLogger(__name__)


class RDSClient:
    """Client for interacting with Huawei Cloud RDS (PostgreSQL/MySQL)."""
    
    def __init__(self):
        """Initialize RDS client."""
        self.host = RDS_HOST
        self.port = RDS_PORT
        self.database = RDS_DB
        self.user = RDS_USER
        self.password = RDS_PASSWORD
        self.engine = getattr(RDS_ENGINE, 'postgresql', 'postgresql').lower()
        
        if not all([self.host, self.port, self.database, self.user, self.password]):
            logger.warning("RDS credentials not fully configured. RDS features disabled.")
            self.conn = None
            return
        
        self._connect()
    
    def _connect(self):
        """Connect to RDS database."""
        try:
            if self.engine == 'postgresql':
                if not POSTGRESQL_AVAILABLE:
                    logger.error("psycopg2 not installed. Install: pip install psycopg2-binary")
                    self.conn = None
                    return
                
                self.conn = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    connect_timeout=10
                )
                logger.info(f"✅ Connected to PostgreSQL RDS at {self.host}:{self.port}")
            
            elif self.engine == 'mysql':
                if not MYSQL_AVAILABLE:
                    logger.error("pymysql not installed. Install: pip install pymysql")
                    self.conn = None
                    return
                
                self.conn = pymysql.connect(
                    host=self.host,
                    port=int(self.port),
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    connect_timeout=10
                )
                logger.info(f"✅ Connected to MySQL RDS at {self.host}:{self.port}")
            
            else:
                logger.error(f"Unsupported database engine: {self.engine}")
                self.conn = None
        
        except Exception as e:
            logger.error(f"Error connecting to RDS: {e}")
            self.conn = None
    
    def get_metadata(self, qa_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for Q&A pair.
        
        Args:
            qa_id: Q&A pair ID
            
        Returns:
            Metadata dictionary or None
        """
        if not self.conn:
            return None
        
        try:
            if self.engine == 'postgresql':
                with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT * FROM medical_qa_metadata WHERE id = %s",
                        (qa_id,)
                    )
                    result = cur.fetchone()
                    return dict(result) if result else None
            
            elif self.engine == 'mysql':
                with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
                    cur.execute(
                        "SELECT * FROM medical_qa_metadata WHERE id = %s",
                        (qa_id,)
                    )
                    return cur.fetchone()
        
        except Exception as e:
            logger.error(f"Error getting metadata for {qa_id}: {e}")
            return None
    
    def insert_metadata(
        self,
        qa_id: str,
        category: str = None,
        subcategory: str = None,
        source: str = None,
        source_type: str = None,
        author: str = None,
        publication_date: str = None,
        tags: List[str] = None
    ) -> bool:
        """
        Insert metadata for Q&A pair.
        
        Args:
            qa_id: Q&A pair ID
            category: Category name
            subcategory: Subcategory name
            source: Source name
            source_type: Type of source
            author: Author name
            publication_date: Publication date
            tags: List of tags
            
        Returns:
            True if successful, False otherwise
        """
        if not self.conn:
            return False
        
        try:
            if self.engine == 'postgresql':
                with self.conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO medical_qa_metadata 
                        (id, category, subcategory, source, source_type, author, publication_date, tags, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            category = EXCLUDED.category,
                            subcategory = EXCLUDED.subcategory,
                            source = EXCLUDED.source,
                            source_type = EXCLUDED.source_type,
                            author = EXCLUDED.author,
                            publication_date = EXCLUDED.publication_date,
                            tags = EXCLUDED.tags,
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        (qa_id, category, subcategory, source, source_type, author, publication_date, tags, datetime.now())
                    )
                    self.conn.commit()
                    logger.info(f"✅ Inserted metadata for {qa_id}")
                    return True
            
            elif self.engine == 'mysql':
                with self.conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO medical_qa_metadata 
                        (id, category, subcategory, source, source_type, author, publication_date, tags, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            category = VALUES(category),
                            subcategory = VALUES(subcategory),
                            source = VALUES(source),
                            source_type = VALUES(source_type),
                            author = VALUES(author),
                            publication_date = VALUES(publication_date),
                            tags = VALUES(tags),
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        (qa_id, category, subcategory, source, source_type, author, publication_date, json.dumps(tags) if tags else None, datetime.now())
                    )
                    self.conn.commit()
                    logger.info(f"✅ Inserted metadata for {qa_id}")
                    return True
        
        except Exception as e:
            logger.error(f"Error inserting metadata for {qa_id}: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def get_relations(self, qa_id: str) -> List[Dict[str, Any]]:
        """
        Get relations for Q&A pair.
        
        Args:
            qa_id: Q&A pair ID
            
        Returns:
            List of relation dictionaries
        """
        if not self.conn:
            return []
        
        try:
            if self.engine == 'postgresql':
                with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT * FROM medical_qa_relations 
                        WHERE source_id = %s OR target_id = %s
                        ORDER BY confidence DESC
                        """,
                        (qa_id, qa_id)
                    )
                    return [dict(row) for row in cur.fetchall()]
            
            elif self.engine == 'mysql':
                with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
                    cur.execute(
                        """
                        SELECT * FROM medical_qa_relations 
                        WHERE source_id = %s OR target_id = %s
                        ORDER BY confidence DESC
                        """,
                        (qa_id, qa_id)
                    )
                    return cur.fetchall()
        
        except Exception as e:
            logger.error(f"Error getting relations for {qa_id}: {e}")
            return []
    
    def insert_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        confidence: float = None
    ) -> bool:
        """
        Insert relation between two Q&A pairs.
        
        Args:
            source_id: Source Q&A ID
            target_id: Target Q&A ID
            relation_type: Type of relation
            confidence: Confidence score
            
        Returns:
            True if successful, False otherwise
        """
        if not self.conn:
            return False
        
        try:
            if self.engine == 'postgresql':
                with self.conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO medical_qa_relations 
                        (source_id, target_id, relation_type, confidence, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (source_id, target_id, relation_type) DO UPDATE SET
                            confidence = EXCLUDED.confidence
                        """,
                        (source_id, target_id, relation_type, confidence, datetime.now())
                    )
                    self.conn.commit()
                    return True
            
            elif self.engine == 'mysql':
                with self.conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO medical_qa_relations 
                        (source_id, target_id, relation_type, confidence, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            confidence = VALUES(confidence)
                        """,
                        (source_id, target_id, relation_type, confidence, datetime.now())
                    )
                    self.conn.commit()
                    return True
        
        except Exception as e:
            logger.error(f"Error inserting relation: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def log_query(
        self,
        qa_id: str,
        query_text: str,
        response_text: str = None,
        user_id: str = None,
        session_id: str = None,
        response_time: float = None,
        similarity_score: float = None,
        user_feedback: str = None
    ) -> bool:
        """
        Log user query.
        
        Args:
            qa_id: Q&A pair ID that was returned
            query_text: User query text
            response_text: Generated response text
            user_id: User ID
            session_id: Session ID
            response_time: Response time in seconds
            similarity_score: Similarity score
            user_feedback: User feedback
            
        Returns:
            True if successful, False otherwise
        """
        if not self.conn:
            return False
        
        try:
            if self.engine == 'postgresql':
                with self.conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO query_logs 
                        (qa_id, query_text, response_text, user_id, session_id, 
                         response_time, similarity_score, user_feedback, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (qa_id, query_text, response_text, user_id, session_id,
                         response_time, similarity_score, user_feedback, datetime.now())
                    )
                    self.conn.commit()
                    return True
            
            elif self.engine == 'mysql':
                with self.conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO query_logs 
                        (qa_id, query_text, response_text, user_id, session_id, 
                         response_time, similarity_score, user_feedback, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (qa_id, query_text, response_text, user_id, session_id,
                         response_time, similarity_score, user_feedback, datetime.now())
                    )
                    self.conn.commit()
                    return True
        
        except Exception as e:
            logger.error(f"Error logging query: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def get_sources(self, qa_id: str) -> List[Dict[str, Any]]:
        """
        Get document sources for Q&A pair.
        
        Args:
            qa_id: Q&A pair ID
            
        Returns:
            List of source dictionaries
        """
        if not self.conn:
            return []
        
        try:
            if self.engine == 'postgresql':
                with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "SELECT * FROM document_sources WHERE qa_id = %s ORDER BY created_at",
                        (qa_id,)
                    )
                    return [dict(row) for row in cur.fetchall()]
            
            elif self.engine == 'mysql':
                with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
                    cur.execute(
                        "SELECT * FROM document_sources WHERE qa_id = %s ORDER BY created_at",
                        (qa_id,)
                    )
                    return cur.fetchall()
        
        except Exception as e:
            logger.error(f"Error getting sources for {qa_id}: {e}")
            return []
    
    def insert_source(
        self,
        qa_id: str,
        document_name: str,
        document_path: str = None,
        page_number: int = None,
        section: str = None,
        excerpt: str = None
    ) -> bool:
        """
        Insert document source for Q&A pair.
        
        Args:
            qa_id: Q&A pair ID
            document_name: Document name
            document_path: OBS path
            page_number: Page number
            section: Section name
            excerpt: Excerpt text
            
        Returns:
            True if successful, False otherwise
        """
        if not self.conn:
            return False
        
        try:
            if self.engine == 'postgresql':
                with self.conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO document_sources 
                        (qa_id, document_name, document_path, page_number, section, excerpt, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (qa_id, document_name, document_path, page_number, section, excerpt, datetime.now())
                    )
                    self.conn.commit()
                    return True
            
            elif self.engine == 'mysql':
                with self.conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO document_sources 
                        (qa_id, document_name, document_path, page_number, section, excerpt, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (qa_id, document_name, document_path, page_number, section, excerpt, datetime.now())
                    )
                    self.conn.commit()
                    return True
        
        except Exception as e:
            logger.error(f"Error inserting source: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def get_analytics(
        self,
        metric_name: str = None,
        qa_id: str = None,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get analytics data.
        
        Args:
            metric_name: Metric name to filter
            qa_id: Q&A ID to filter
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of analytics records
        """
        if not self.conn:
            return []
        
        try:
            conditions = []
            params = []
            
            if metric_name:
                conditions.append("metric_name = %s")
                params.append(metric_name)
            
            if qa_id:
                conditions.append("qa_id = %s")
                params.append(qa_id)
            
            if start_date:
                conditions.append("date >= %s")
                params.append(start_date)
            
            if end_date:
                conditions.append("date <= %s")
                params.append(end_date)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            if self.engine == 'postgresql':
                with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        f"SELECT * FROM analytics WHERE {where_clause} ORDER BY date DESC",
                        params
                    )
                    return [dict(row) for row in cur.fetchall()]
            
            elif self.engine == 'mysql':
                with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
                    cur.execute(
                        f"SELECT * FROM analytics WHERE {where_clause} ORDER BY date DESC",
                        params
                    )
                    return cur.fetchall()
        
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return []
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("RDS connection closed")


