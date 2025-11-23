"""Vision Tool - Analyze images using Aliyun Qwen3-VL-Plus API"""

import base64
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI
from PIL import Image

from src.utils.logger import get_logger

logger = get_logger(__name__)


class VisionTool:
    """Analyze images using Aliyun Qwen3-VL-Plus (via OpenAI-compatible API)"""

    def __init__(
        self,
        api_key: str,
        model: str = "qwen3-vl-plus",
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        max_image_size: int = 4096,
    ):
        """
        Initialize Vision Tool with Aliyun Qwen3-VL-Plus

        Args:
            api_key: Aliyun DashScope API key
            model: Model name (qwen3-vl-plus, qwen3-vl-flash, qwen-vl-max, etc.)
            base_url: API base URL (Beijing region by default)
            max_image_size: Maximum image dimension in pixels
        """
        if not api_key:
            raise ValueError("Aliyun DashScope API key is required")

        self.api_key = api_key
        self.model_name = model
        self.max_image_size = max_image_size

        try:
            # Use OpenAI-compatible client
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url,
            )
            logger.info(f"VisionTool initialized with Aliyun {model} (OpenAI-compatible API)")
        except Exception as e:
            logger.error(f"Failed to initialize VisionTool: {e}")
            raise

    def _image_to_base64(self, image_path: str, resize: bool = True) -> str:
        """
        Convert image to base64 data URL

        Args:
            image_path: Path to image file
            resize: Resize if too large

        Returns:
            Base64 data URL string
        """
        img = Image.open(image_path)

        # Resize if needed
        if resize and max(img.size) > self.max_image_size:
            ratio = self.max_image_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            logger.debug(f"Resized image to {new_size}")

        # Convert to RGB if needed (RGBA, P, etc. → RGB)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Save to bytes
        import io
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        # Encode to base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:image/png;base64,{base64_image}"

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

            # Convert image to base64
            image_data_url = self._image_to_base64(str(image_path), resize)

            # Call Qwen3-VL-Plus API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": image_data_url}},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )

            result = {
                "image_path": str(image_path),
                "prompt": prompt,
                "analysis": response.choices[0].message.content,
                "model": self.model_name,
                "description": response.choices[0].message.content,  # Alias for compatibility
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
                "description": None,
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
            # Convert all images to base64
            image_data_urls = [self._image_to_base64(path) for path in image_paths]

            # Default comparison prompt
            if not comparison_prompt:
                comparison_prompt = f"""Compare these {len(image_paths)} images. Describe:
                1. Similarities between the images
                2. Key differences
                3. What each image shows
                4. Overall comparison summary"""

            # Build content array with all images
            content = []
            for i, image_url in enumerate(image_data_urls):
                content.append({"type": "image_url", "image_url": {"url": image_url}})
            content.append({"type": "text", "text": comparison_prompt})

            # Call API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": content}],
            )

            result = {
                "image_paths": [str(p) for p in image_paths],
                "image_count": len(image_paths),
                "comparison": response.choices[0].message.content,
                "model": self.model_name,
            }

            logger.info(f"Compared {len(image_paths)} images")
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
            total_pages = len(doc)
            result["total_pages"] = total_pages

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
