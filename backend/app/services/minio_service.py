from minio import Minio
from minio.error import S3Error
import os
import logging

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "files")

logger = logging.getLogger(__name__)

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

def upload_file_to_minio(file_data, file_name, content_type="application/pdf"):
    try:
        if not minio_client.bucket_exists(MINIO_BUCKET):
            minio_client.make_bucket(MINIO_BUCKET)
        
        minio_client.put_object(
            MINIO_BUCKET,
            file_name,
            file_data,
            length=-1,
            part_size=10*1024*1024,
            content_type=content_type
        )
        url = minio_client.presigned_get_object(MINIO_BUCKET, file_name)
        return url
    except S3Error as e:
        logger.error(f"Error uploading file to MinIO: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading file: {e}")
        raise

def delete_file_from_minio(file_name):
    """
    Delete a file from MinIO storage
    - file_name: Name of the file to delete from the bucket
    Returns: True if deleted successfully, False otherwise
    """
    try:
        # Check if file exists
        try:
            minio_client.stat_object(MINIO_BUCKET, file_name)
        except S3Error as e:
            if e.code == 'NoSuchKey':
                logger.warning(f"File {file_name} does not exist in MinIO")
                return False
            raise
        
        # Delete the file
        minio_client.remove_object(MINIO_BUCKET, file_name)
        logger.info(f"Successfully deleted file {file_name} from MinIO")
        return True
        
    except S3Error as e:
        logger.error(f"S3 error deleting file {file_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deleting file {file_name}: {e}")
        return False

def get_file_from_minio(file_name):
    """
    Get a file object from MinIO storage
    - file_name: Name of the file to retrieve
    Returns: File data stream
    """
    try:
        response = minio_client.get_object(MINIO_BUCKET, file_name)
        return response
    except S3Error as e:
        logger.error(f"Error getting file {file_name} from MinIO: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting file {file_name}: {e}")
        raise

def get_file_url_from_minio(file_name, expires=3600):
    """
    Get a presigned URL for a file in MinIO
    - file_name: Name of the file
    - expires: URL expiration time in seconds (default: 1 hour)
    Returns: Presigned URL string
    """
    try:
        url = minio_client.presigned_get_object(
            MINIO_BUCKET, 
            file_name, 
            expires=expires
        )
        return url
    except S3Error as e:
        logger.error(f"Error generating URL for file {file_name}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating URL for file {file_name}: {e}")
        raise

def list_files_in_minio(prefix=""):
    """
    List all files in the MinIO bucket
    - prefix: Optional prefix to filter files
    Returns: List of file names
    """
    try:
        objects = minio_client.list_objects(
            MINIO_BUCKET, 
            prefix=prefix, 
            recursive=True
        )
        return [obj.object_name for obj in objects]
    except S3Error as e:
        logger.error(f"Error listing files in MinIO: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing files: {e}")
        raise

def file_exists_in_minio(file_name):
    """
    Check if a file exists in MinIO bucket
    - file_name: Name of the file to check
    Returns: True if exists, False otherwise
    """
    try:
        minio_client.stat_object(MINIO_BUCKET, file_name)
        return True
    except S3Error as e:
        if e.code == 'NoSuchKey':
            return False
        logger.error(f"Error checking file existence {file_name}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error checking file {file_name}: {e}")
        raise