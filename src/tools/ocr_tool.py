"""OCR Tool - Extract text from images using PaddleOCR"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from paddleocr import PaddleOCR
from PIL import Image

from src.utils.logger import get_logger

logger = get_logger(__name__)


class OCRTool:
    """Extract text from images using PaddleOCR (supports Chinese and English)"""

    def __init__(
        self,
        languages: Optional[List[str]] = None,
        use_gpu: bool = False,
        use_angle_cls: bool = True,
        show_log: bool = False,
    ):
        """
        Initialize OCR Tool

        Args:
            languages: List of language codes (e.g., ['ch', 'en'])
            use_gpu: Whether to use GPU acceleration
            use_angle_cls: Whether to use angle classifier
            show_log: Whether to show PaddleOCR logs
        """
        if languages is None:
            languages = ["ch", "en"]  # Chinese and English

        self.languages = languages
        self.use_gpu = use_gpu

        # Determine primary language
        primary_lang = languages[0] if languages else "ch"

        try:
            logger.info(f"Initializing PaddleOCR (lang: {primary_lang}, gpu: {use_gpu})")
            self.ocr = PaddleOCR(
                use_angle_cls=use_angle_cls,
                lang=primary_lang,
                use_gpu=use_gpu,
                show_log=show_log,
            )
            logger.info("PaddleOCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise

    async def extract_text(
        self,
        image_path: str,
        return_structured: bool = False,
    ) -> Dict[str, Any]:
        """
        Extract text from an image

        Args:
            image_path: Path to image file
            return_structured: Return structured results with bounding boxes

        Returns:
            Dict with extracted text and optional structure
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            logger.info(f"Extracting text from: {image_path}")
            result = self.ocr.ocr(str(image_path), cls=True)

            if not result or not result[0]:
                logger.warning(f"No text detected in {image_path}")
                return {
                    "image_path": str(image_path),
                    "text": "",
                    "text_lines": [],
                    "structured_data": [],
                }

            # Parse results
            text_lines = []
            structured_data = []

            for line in result[0]:
                bbox, (text, confidence) = line

                text_lines.append(text)

                if return_structured:
                    structured_data.append({
                        "text": text,
                        "confidence": float(confidence),
                        "bbox": {
                            "top_left": bbox[0],
                            "top_right": bbox[1],
                            "bottom_right": bbox[2],
                            "bottom_left": bbox[3],
                        },
                    })

            # Combine all text
            full_text = "\n".join(text_lines)

            result_dict = {
                "image_path": str(image_path),
                "text": full_text,
                "text_lines": text_lines,
                "line_count": len(text_lines),
            }

            if return_structured:
                result_dict["structured_data"] = structured_data

            logger.info(f"Extracted {len(text_lines)} text lines from {image_path}")
            return result_dict

        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {e}")
            return {
                "image_path": str(image_path),
                "error": str(e),
                "text": "",
                "text_lines": [],
            }

    async def extract_text_from_multiple(
        self,
        image_paths: List[str],
        return_structured: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Extract text from multiple images

        Args:
            image_paths: List of image paths
            return_structured: Return structured results

        Returns:
            List of extraction results
        """
        results = []

        for image_path in image_paths:
            result = await self.extract_text(image_path, return_structured)
            results.append(result)

        logger.info(f"Processed {len(image_paths)} images")
        return results

    async def extract_text_from_pdf_page(
        self,
        pdf_path: str,
        page_num: int,
        dpi: int = 200,
    ) -> Dict[str, Any]:
        """
        Extract text from a PDF page using OCR

        Args:
            pdf_path: Path to PDF file
            page_num: Page number (0-indexed)
            dpi: DPI for rendering (higher = better quality, slower)

        Returns:
            Extraction result
        """
        try:
            import fitz as pymupdf

            # Open PDF
            doc = pymupdf.open(pdf_path)

            if page_num >= len(doc):
                raise ValueError(f"Page {page_num} does not exist in PDF")

            # Render page to image
            page = doc[page_num]
            mat = pymupdf.Matrix(dpi / 72, dpi / 72)  # Scale for DPI
            pix = page.get_pixmap(matrix=mat)

            # Save temporary image
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            pix.save(temp_file.name)
            temp_file.close()

            # Extract text
            result = await self.extract_text(temp_file.name)

            # Add PDF metadata
            result["pdf_path"] = pdf_path
            result["page_num"] = page_num
            result["total_pages"] = len(doc)

            # Clean up
            import os
            os.unlink(temp_file.name)
            doc.close()

            logger.info(f"OCR extracted text from {pdf_path} page {page_num}")
            return result

        except Exception as e:
            logger.error(f"Error processing PDF page: {e}")
            return {
                "pdf_path": pdf_path,
                "page_num": page_num,
                "error": str(e),
                "text": "",
            }

    async def detect_text_regions(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        Detect text regions without recognition

        Args:
            image_path: Path to image

        Returns:
            Dict with detected text regions
        """
        try:
            result = self.ocr.ocr(str(image_path), det=True, rec=False, cls=False)

            regions = []
            if result and result[0]:
                for bbox in result[0]:
                    regions.append({
                        "bbox": {
                            "top_left": bbox[0],
                            "top_right": bbox[1],
                            "bottom_right": bbox[2],
                            "bottom_left": bbox[3],
                        }
                    })

            logger.info(f"Detected {len(regions)} text regions in {image_path}")
            return {
                "image_path": str(image_path),
                "region_count": len(regions),
                "regions": regions,
            }

        except Exception as e:
            logger.error(f"Error detecting text regions: {e}")
            return {
                "image_path": str(image_path),
                "error": str(e),
                "regions": [],
            }

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages

        Returns:
            List of language codes
        """
        # PaddleOCR supports 80+ languages
        supported = [
            "ch",  # Chinese
            "en",  # English
            "french",
            "german",
            "korean",
            "japan",
            # Add more as needed
        ]
        return supported
