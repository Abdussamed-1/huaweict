"""
OBS (Object Storage Service) Client for Huawei Cloud
Handles document upload, download, and management in OBS buckets.
"""
import logging
from typing import Optional, List
from config import OBS_ACCESS_KEY, OBS_SECRET_KEY, OBS_ENDPOINT, OBS_BUCKET_NAME

logger = logging.getLogger(__name__)

try:
    from obs import ObsClient
    OBS_AVAILABLE = True
except ImportError:
    OBS_AVAILABLE = False
    logger.warning("esdk-obs-python not available. OBS features will be disabled.")


class OBSClient:
    """Client for interacting with Huawei Cloud OBS."""
    
    def __init__(self):
        """Initialize OBS client."""
        if not OBS_AVAILABLE:
            logger.error("OBS SDK not available. Install esdk-obs-python.")
            self.client = None
            return
        
        if not all([OBS_ACCESS_KEY, OBS_SECRET_KEY, OBS_ENDPOINT, OBS_BUCKET_NAME]):
            logger.warning("OBS credentials not fully configured. OBS features disabled.")
            self.client = None
            return
        
        try:
            self.client = ObsClient(
                access_key_id=OBS_ACCESS_KEY,
                secret_access_key=OBS_SECRET_KEY,
                server=OBS_ENDPOINT
            )
            self.bucket_name = OBS_BUCKET_NAME
            logger.info(f"✅ OBS client initialized for bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Error initializing OBS client: {e}")
            self.client = None
    
    def upload_document(self, file_path: str, object_key: str) -> bool:
        """
        Upload document to OBS.
        
        Args:
            file_path: Local file path to upload
            object_key: OBS object key (path in bucket)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("OBS client not available")
            return False
        
        try:
            resp = self.client.putFile(
                Bucket=self.bucket_name,
                Key=object_key,
                file_path=file_path
            )
            if resp.status < 300:
                logger.info(f"✅ Uploaded {file_path} to OBS: {object_key}")
                return True
            else:
                logger.error(f"OBS upload failed with status: {resp.status}")
                return False
        except Exception as e:
            logger.error(f"OBS upload error: {e}")
            return False
    
    def download_document(self, object_key: str, local_path: str) -> bool:
        """
        Download document from OBS.
        
        Args:
            object_key: OBS object key (path in bucket)
            local_path: Local file path to save downloaded file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("OBS client not available")
            return False
        
        try:
            resp = self.client.getObject(
                Bucket=self.bucket_name,
                Key=object_key,
                downloadPath=local_path
            )
            if resp.status < 300:
                logger.info(f"✅ Downloaded {object_key} from OBS to {local_path}")
                return True
            else:
                logger.error(f"OBS download failed with status: {resp.status}")
                return False
        except Exception as e:
            logger.error(f"OBS download error: {e}")
            return False
    
    def list_documents(self, prefix: str = "") -> List[str]:
        """
        List documents in bucket with optional prefix filter.
        
        Args:
            prefix: Prefix to filter objects (e.g., "raw-documents/")
            
        Returns:
            List of object keys
        """
        if not self.client:
            logger.error("OBS client not available")
            return []
        
        try:
            resp = self.client.listObjects(
                Bucket=self.bucket_name,
                prefix=prefix
            )
            if resp.status < 300 and resp.body.contents:
                return [obj.key for obj in resp.body.contents]
            return []
        except Exception as e:
            logger.error(f"OBS list error: {e}")
            return []
    
    def delete_document(self, object_key: str) -> bool:
        """
        Delete document from OBS.
        
        Args:
            object_key: OBS object key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("OBS client not available")
            return False
        
        try:
            resp = self.client.deleteObject(
                Bucket=self.bucket_name,
                Key=object_key
            )
            if resp.status < 300:
                logger.info(f"✅ Deleted {object_key} from OBS")
                return True
            else:
                logger.error(f"OBS delete failed with status: {resp.status}")
                return False
        except Exception as e:
            logger.error(f"OBS delete error: {e}")
            return False
    
    def get_document_url(self, object_key: str, expires: int = 3600) -> Optional[str]:
        """
        Generate temporary URL for document access.
        
        Args:
            object_key: OBS object key
            expires: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Temporary URL or None if error
        """
        if not self.client:
            logger.error("OBS client not available")
            return None
        
        try:
            resp = self.client.createSignedUrl(
                method='GET',
                bucket=self.bucket_name,
                objectKey=object_key,
                expires=expires
            )
            if resp.status < 300:
                return resp.signedUrl
            return None
        except Exception as e:
            logger.error(f"OBS URL generation error: {e}")
            return None

