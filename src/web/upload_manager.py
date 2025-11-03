"""File Upload Manager for Web UI"""

import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import shutil

from fastapi import UploadFile
from PIL import Image

from src.utils import get_logger

logger = get_logger(__name__)


class UploadManager:
    """Manages file uploads for documents and images"""

    def __init__(self, base_upload_dir: str = "src/web/uploads"):
        self.base_upload_dir = Path(base_upload_dir)
        self.documents_dir = self.base_upload_dir / "rag_documents"
        self.images_dir = self.base_upload_dir / "images"
        self.temp_dir = self.base_upload_dir / "temp"

        # Create directories if they don't exist
        for directory in [self.documents_dir, self.images_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    async def save_document(self, file: UploadFile) -> dict:
        """
        Save uploaded document

        Returns:
            dict with file info including path, size, hash, etc.
        """
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_hash = hashlib.md5(await file.read()).hexdigest()[:8]
            await file.seek(0)  # Reset file pointer

            # Keep original extension
            original_name = file.filename
            extension = Path(original_name).suffix
            safe_filename = f"{timestamp}_{file_hash}_{Path(original_name).stem}{extension}"

            # Save to dated subfolder
            date_folder = self.documents_dir / datetime.now().strftime("%Y-%m")
            date_folder.mkdir(parents=True, exist_ok=True)

            file_path = date_folder / safe_filename

            # Write file
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            file_size = len(content)

            logger.info(f"Saved document: {file_path} ({file_size} bytes)")

            return {
                "filename": original_name,
                "saved_filename": safe_filename,
                "filepath": str(file_path),
                "relative_path": str(file_path.relative_to(self.base_upload_dir)),
                "file_size": file_size,
                "file_type": extension.lstrip('.'),
                "file_hash": file_hash,
                "upload_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error saving document: {e}", exc_info=True)
            raise

    async def save_image(self, file: UploadFile, create_thumbnail: bool = True) -> dict:
        """
        Save uploaded image with optional thumbnail

        Returns:
            dict with image info including path, dimensions, thumbnail, etc.
        """
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_hash = hashlib.md5(await file.read()).hexdigest()[:8]
            await file.seek(0)

            # Keep original extension
            original_name = file.filename
            extension = Path(original_name).suffix.lower()

            # Validate image extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            if extension not in valid_extensions:
                raise ValueError(f"Invalid image extension: {extension}")

            safe_filename = f"{timestamp}_{file_hash}_{Path(original_name).stem}{extension}"

            # Save to dated subfolder
            date_folder = self.images_dir / datetime.now().strftime("%Y-%m")
            date_folder.mkdir(parents=True, exist_ok=True)

            file_path = date_folder / safe_filename

            # Write file
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            file_size = len(content)

            # Get image dimensions
            with Image.open(file_path) as img:
                width, height = img.size

            result = {
                "filename": original_name,
                "saved_filename": safe_filename,
                "filepath": str(file_path),
                "relative_path": str(file_path.relative_to(self.base_upload_dir)),
                "file_size": file_size,
                "file_type": extension.lstrip('.'),
                "file_hash": file_hash,
                "width": width,
                "height": height,
                "upload_timestamp": datetime.now().isoformat(),
                "thumbnail_path": None
            }

            # Create thumbnail
            if create_thumbnail:
                try:
                    thumb_path = await self._create_thumbnail(file_path)
                    result["thumbnail_path"] = str(thumb_path.relative_to(self.base_upload_dir))
                except Exception as e:
                    logger.warning(f"Failed to create thumbnail: {e}")

            logger.info(f"Saved image: {file_path} ({file_size} bytes, {width}x{height})")

            return result

        except Exception as e:
            logger.error(f"Error saving image: {e}", exc_info=True)
            raise

    async def _create_thumbnail(self, image_path: Path, max_size: tuple = (200, 200)) -> Path:
        """Create thumbnail for image"""
        thumb_dir = image_path.parent / "thumbnails"
        thumb_dir.mkdir(exist_ok=True)

        thumb_path = thumb_dir / f"thumb_{image_path.name}"

        with Image.open(image_path) as img:
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                img = img.convert('RGB')

            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            img.save(thumb_path, quality=85, optimize=True)

        return thumb_path

    async def validate_file(
            self,
            file: UploadFile,
            allowed_types: Optional[List[str]] = None,
            max_size: int = 50 * 1024 * 1024  # 50MB default
    ) -> bool:
        """
        Validate uploaded file

        Args:
            file: Upload file
            allowed_types: List of allowed extensions (e.g., ['pdf', 'txt'])
            max_size: Maximum file size in bytes

        Returns:
            bool: True if valid

        Raises:
            ValueError: If validation fails
        """
        # Check extension
        extension = Path(file.filename).suffix.lstrip('.').lower()

        if allowed_types and extension not in allowed_types:
            raise ValueError(f"File type '.{extension}' not allowed. Allowed types: {allowed_types}")

        # Check size
        content = await file.read()
        await file.seek(0)  # Reset file pointer

        if len(content) > max_size:
            max_mb = max_size / (1024 * 1024)
            raise ValueError(f"File too large. Maximum size: {max_mb:.1f}MB")

        return True

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file"""
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()

                # Delete thumbnail if exists
                if path.parent.name != "thumbnails":
                    thumb_path = path.parent / "thumbnails" / f"thumb_{path.name}"
                    if thumb_path.exists():
                        thumb_path.unlink()

                logger.info(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {e}", exc_info=True)
            return False

    async def cleanup_old_files(self, days: int = 7) -> int:
        """
        Clean up files older than specified days

        Returns:
            Number of files deleted
        """
        count = 0
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for directory in [self.temp_dir]:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            count += 1
                        except Exception as e:
                            logger.warning(f"Failed to delete {file_path}: {e}")

        if count > 0:
            logger.info(f"Cleaned up {count} old files")

        return count

    def get_file_url(self, relative_path: str) -> str:
        """Get public URL for uploaded file"""
        return f"/uploads/{relative_path}"

    def get_upload_stats(self) -> dict:
        """Get upload directory statistics"""
        stats = {}

        for name, directory in [
            ("documents", self.documents_dir),
            ("images", self.images_dir),
            ("temp", self.temp_dir)
        ]:
            files = list(directory.rglob("*"))
            files = [f for f in files if f.is_file()]

            total_size = sum(f.stat().st_size for f in files)

            stats[name] = {
                "count": len(files),
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            }

        return stats


# Global instance
upload_manager = UploadManager()
