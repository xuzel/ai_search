"""Vision Tool - Analyze images using Gemini Vision API"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from PIL import Image

from src.utils.logger import get_logger

logger = get_logger(__name__)


class VisionTool:
    """Analyze images using Gemini Vision API"""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-exp",
        max_image_size: int = 4096,
    ):
        """
        Initialize Vision Tool

        Args:
            api_key: Google API key
            model: Model name (gemini-2.0-flash-exp, gemini-1.5-pro, etc.)
            max_image_size: Maximum image dimension in pixels
        """
        if not api_key:
            raise ValueError("Google API key is required")

        self.api_key = api_key
        self.model_name = model
        self.max_image_size = max_image_size

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model)
            logger.info(f"VisionTool initialized with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize VisionTool: {e}")
            raise

    async def analyze_image(
        self,
        image_path: str,
        prompt: str = "Describe this image in detail",
        resize: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze an image with a custom prompt

        Args:
            image_path: Path to image file
            prompt: Analysis prompt
            resize: Resize image if too large

        Returns:
            Dict with analysis result
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            logger.info(f"Analyzing image: {image_path}")

            # Load and optionally resize image
            img = Image.open(image_path)

            if resize and max(img.size) > self.max_image_size:
                # Resize maintaining aspect ratio
                ratio = self.max_image_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.debug(f"Resized image to {new_size}")

            # Generate content
            response = self.model.generate_content([prompt, img])

            result = {
                "image_path": str(image_path),
                "prompt": prompt,
                "analysis": response.text,
                "model": self.model_name,
            }

            logger.info(f"Image analysis complete for {image_path}")
            return result

        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {e}")
            return {
                "image_path": str(image_path),
                "prompt": prompt,
                "error": str(e),
                "analysis": None,
            }

    async def extract_text_from_image(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        Extract text from an image using vision model

        Args:
            image_path: Path to image

        Returns:
            Dict with extracted text
        """
        prompt = """Extract all text from this image.
        Return ONLY the text content, preserving the original formatting and layout as much as possible.
        If there is no text, respond with 'No text detected'."""

        result = await self.analyze_image(image_path, prompt)

        # Rename 'analysis' to 'text' for clarity
        if result.get("analysis"):
            result["text"] = result.pop("analysis")

        return result

    async def analyze_document(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        Analyze a document image (invoice, receipt, form, etc.)

        Args:
            image_path: Path to document image

        Returns:
            Dict with document analysis
        """
        prompt = """Analyze this document image. Extract:
        1. Document type (invoice, receipt, form, letter, etc.)
        2. Key information (dates, amounts, names, addresses, etc.)
        3. Main content/purpose
        4. Any notable details

        Format the response as structured information."""

        return await self.analyze_image(image_path, prompt)

    async def analyze_chart_or_diagram(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        Analyze charts, graphs, or diagrams

        Args:
            image_path: Path to chart/diagram image

        Returns:
            Dict with analysis
        """
        prompt = """Analyze this chart, graph, or diagram. Describe:
        1. Type of visualization (bar chart, line graph, pie chart, flowchart, etc.)
        2. Main data points and trends
        3. Key findings or insights
        4. Labels, legends, and axes

        Provide a comprehensive analysis."""

        return await self.analyze_image(image_path, prompt)

    async def compare_images(
        self,
        image_paths: List[str],
        comparison_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compare multiple images

        Args:
            image_paths: List of image paths (2-4 images)
            comparison_prompt: Optional custom comparison prompt

        Returns:
            Dict with comparison result
        """
        if len(image_paths) < 2:
            raise ValueError("At least 2 images are required for comparison")

        if len(image_paths) > 4:
            raise ValueError("Maximum 4 images can be compared at once")

        try:
            # Load images
            images = [Image.open(path) for path in image_paths]

            # Default comparison prompt
            if not comparison_prompt:
                comparison_prompt = f"""Compare these {len(images)} images. Describe:
                1. Similarities between the images
                2. Key differences
                3. What each image shows
                4. Overall comparison summary"""

            # Generate content with multiple images
            content = [comparison_prompt] + images
            response = self.model.generate_content(content)

            result = {
                "image_paths": [str(p) for p in image_paths],
                "image_count": len(image_paths),
                "comparison": response.text,
                "model": self.model_name,
            }

            logger.info(f"Compared {len(images)} images")
            return result

        except Exception as e:
            logger.error(f"Error comparing images: {e}")
            return {
                "image_paths": [str(p) for p in image_paths],
                "error": str(e),
                "comparison": None,
            }

    async def analyze_pdf_page_image(
        self,
        pdf_path: str,
        page_num: int,
        prompt: Optional[str] = None,
        dpi: int = 200,
    ) -> Dict[str, Any]:
        """
        Analyze a PDF page using vision model

        Args:
            pdf_path: Path to PDF
            page_num: Page number (0-indexed)
            prompt: Analysis prompt
            dpi: DPI for rendering

        Returns:
            Dict with analysis result
        """
        try:
            import fitz as pymupdf
            import tempfile

            # Open PDF and render page
            doc = pymupdf.open(pdf_path)

            if page_num >= len(doc):
                raise ValueError(f"Page {page_num} does not exist in PDF")

            page = doc[page_num]
            mat = pymupdf.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            pix.save(temp_file.name)
            temp_file.close()

            # Default prompt for PDF pages
            if not prompt:
                prompt = """Analyze this PDF page. Extract:
                1. All text content
                2. Document structure and layout
                3. Any tables, charts, or diagrams
                4. Key information and main points"""

            # Analyze the image
            result = await self.analyze_image(temp_file.name, prompt, resize=False)

            # Add PDF metadata
            result["pdf_path"] = pdf_path
            result["page_num"] = page_num
            result["total_pages"] = len(doc)

            # Clean up
            import os
            os.unlink(temp_file.name)
            doc.close()

            logger.info(f"Analyzed PDF page {page_num} from {pdf_path}")
            return result

        except Exception as e:
            logger.error(f"Error analyzing PDF page: {e}")
            return {
                "pdf_path": pdf_path,
                "page_num": page_num,
                "error": str(e),
                "analysis": None,
            }

    async def batch_analyze(
        self,
        image_paths: List[str],
        prompt: str = "Describe this image",
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple images with the same prompt

        Args:
            image_paths: List of image paths
            prompt: Analysis prompt

        Returns:
            List of analysis results
        """
        results = []

        for image_path in image_paths:
            result = await self.analyze_image(image_path, prompt)
            results.append(result)

        logger.info(f"Batch analyzed {len(image_paths)} images")
        return results
