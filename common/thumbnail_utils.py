import os
import uuid
import tempfile
import threading
from PIL import Image
from google.cloud import storage
import cv2
import traceback

from common.analytics import get_logger
from config.default import Default

logger = get_logger(__name__)
config = Default()

def _download_blob(gcs_uri: str, temp_path: str):
    """Downloads a blob from a GCS URI to a local path."""
    client = storage.Client()
    # gs://bucket_name/path/to/blob
    parts = gcs_uri.replace("gs://", "").split("/", 1)
    bucket_name = parts[0]
    blob_path = parts[1]
    
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.download_to_filename(temp_path)
    return bucket_name

def _upload_thumbnail(local_path: str, source_bucket: str) -> str:
    """Uploads a local thumbnail to the thumbnails folder in GCS."""
    client = storage.Client()
    bucket = client.bucket(source_bucket)
    
    filename = f"{uuid.uuid4()}.webp"
    destination_path = f"thumbnails/{filename}"
    
    blob = bucket.blob(destination_path)
    blob.upload_from_filename(local_path, content_type="image/webp")
    
    return f"gs://{source_bucket}/{destination_path}"

def _generate_video_thumbnail(local_video_path: str, out_image_path: str, size=(256, 256)):
    """Extracts first frame of a video using OpenCV and resizes it."""
    cap = cv2.VideoCapture(local_video_path)
    if not cap.isOpened():
        raise Exception("Failed to open video file with OpenCV.")
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        raise Exception("Failed to read the first frame from the video.")
    
    # Convert BGR (OpenCV) to RGB (Pillow)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb_frame)
    img.thumbnail(size)
    img.save(out_image_path, format="WEBP", quality=80)

def _generate_image_thumbnail(local_image_path: str, out_image_path: str, size=(256, 256)):
    """Resizes an image using Pillow."""
    with Image.open(local_image_path) as img:
        # Convert to RGB to avoid issues with saving as WEBP if it's RGBA
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail(size)
        img.save(out_image_path, format="WEBP", quality=80)

def generate_thumbnail_sync(gcs_uri: str, mime_type: str) -> str | None:
    """Generates a thumbnail for a given GCS URI and uploads it to GCS.
    Returns the new GCS URI of the thumbnail, or None if failed.
    """
    if not gcs_uri or not gcs_uri.startswith("gs://"):
        return None
        
    temp_in = None
    temp_out = None
    try:
        _, ext_in = os.path.splitext(gcs_uri)
        if not ext_in:
            ext_in = ".tmp"
            
        temp_in = tempfile.mktemp(suffix=ext_in)
        temp_out = tempfile.mktemp(suffix=".webp")
        
        logger.info(f"Generating thumbnail for {gcs_uri}")
        bucket_name = _download_blob(gcs_uri, temp_in)
        
        if mime_type.startswith("video/"):
            _generate_video_thumbnail(temp_in, temp_out)
        elif mime_type.startswith("image/"):
            _generate_image_thumbnail(temp_in, temp_out)
        else:
            logger.info(f"Thumbnail generation not supported for mime_type: {mime_type}")
            return None
            
        thumbnail_uri = _upload_thumbnail(temp_out, bucket_name)
        logger.info(f"Successfully generated thumbnail: {thumbnail_uri}")
        return thumbnail_uri
        
    except Exception as e:
        logger.error(f"Error generating thumbnail for {gcs_uri}: {e}")
        traceback.print_exc()
        return None
        
    finally:
        # Cleanup temp files
        if temp_in and os.path.exists(temp_in):
            os.remove(temp_in)
        if temp_out and os.path.exists(temp_out):
            os.remove(temp_out)

def trigger_thumbnail_generation(media_item_id: str, gcs_uri: str, mime_type: str):
    """Fires a background thread to generate a thumbnail and update Firestore."""
    if not media_item_id or not gcs_uri:
        return
        
    def _worker():
        try:
            from config.firebase_config import FirebaseClient
            db = FirebaseClient(database_id=config.GENMEDIA_FIREBASE_DB).get_client()
            
            thumbnail_uri = generate_thumbnail_sync(gcs_uri, mime_type)
            if thumbnail_uri:
                # Update Firestore document with new thumbnail URI
                doc_ref = db.collection(config.GENMEDIA_COLLECTION_NAME).document(media_item_id)
                doc_ref.update({"thumbnail_uri": thumbnail_uri})
                logger.info(f"Updated media item {media_item_id} with thumbnail_uri")
        except Exception as e:
            logger.error(f"Background thumbnail worker failed for {media_item_id}: {e}")
            
    # Run in background to avoid blocking UI
    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
