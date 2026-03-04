"""MinIO object storage utilities"""
from minio import Minio
from minio.error import S3Error
import os
from typing import Optional
from io import BytesIO

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"


class StorageManager:
    """MinIO storage manager"""
    
    def __init__(self):
        self.client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        self._ensure_buckets()
    
    def _ensure_buckets(self):
        """Ensure required buckets exist"""
        buckets = ["reports", "audit-documents", "imports"]
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
            except S3Error as e:
                print(f"Bucket creation error for {bucket}: {e}")
    
    def upload_file(self, bucket: str, object_name: str, data: bytes, 
                   content_type: str = "application/octet-stream") -> bool:
        """
        Upload file to storage.
        
        Args:
            bucket: Bucket name
            object_name: Object name/path
            data: File data
            content_type: Content type
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.put_object(
                bucket,
                object_name,
                BytesIO(data),
                length=len(data),
                content_type=content_type
            )
            return True
        except S3Error as e:
            print(f"Upload error: {e}")
            return False
    
    def download_file(self, bucket: str, object_name: str) -> Optional[bytes]:
        """
        Download file from storage.
        
        Args:
            bucket: Bucket name
            object_name: Object name/path
            
        Returns:
            File data or None if not found
        """
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            print(f"Download error: {e}")
            return None
    
    def delete_file(self, bucket: str, object_name: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            bucket: Bucket name
            object_name: Object name/path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.remove_object(bucket, object_name)
            return True
        except S3Error as e:
            print(f"Delete error: {e}")
            return False
    
    def list_files(self, bucket: str, prefix: str = "") -> list:
        """
        List files in bucket.
        
        Args:
            bucket: Bucket name
            prefix: Object prefix filter
            
        Returns:
            List of object names
        """
        try:
            objects = self.client.list_objects(bucket, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"List error: {e}")
            return []


# Global storage manager instance
storage_manager = StorageManager()
