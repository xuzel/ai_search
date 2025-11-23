"""Advanced PDF Processor - Intelligent multi-modal PDF processing

Combines multiple strategies for optimal PDF processing:
1. PyMuPDF - Fast text extraction for text-based pages
2. OCRTool - Text extraction from scanned/image-heavy pages
3. VisionTool - Understanding complex layouts (charts, tables, diagrams)
4. pdfplumber - Precise table extraction

Automatically detects the best strategy for each page.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz as pymupdf

from src.utils.logger import get_logger

logger = get_logger(__name__)


class PageType:
    """Page type classification"""
    TEXT = "text"  # Text-based page (use PyMuPDF)
    SCANNED = "scanned"  # Scanned/image-heavy (use OCR)
    COMPLEX = "complex"  # Charts/tables/diagrams (use Vision)
    MIXED = "mixed"  # Mixed content (combine strategies)


class AdvancedPDFProcessor:
    """
    Intelligent PDF processor that uses multiple strategies

    Features:
    - Automatic page type detection
    - Strategy selection per page
    - Table extraction
    - Chart/diagram understanding
    - Multi-modal content extraction
    """

    def __init__(
        self,
        ocr_tool: Optional[Any] = None,
        vision_tool: Optional[Any] = None,
        use_ocr: bool = True,
        use_vision: bool = True,
        dpi: int = 200,
    ):
        """
        Initialize Advanced PDF Processor

        Args:
            ocr_tool: OCRTool instance (optional)
            vision_tool: VisionTool instance (optional)
            use_ocr: Enable OCR processing
            use_vision: Enable vision-based processing
            dpi: DPI for rendering PDF pages to images
        """
        self.ocr_tool = ocr_tool
        self.vision_tool = vision_tool
        self.use_ocr = use_ocr and ocr_tool is not None
        self.use_vision = use_vision and vision_tool is not None
        self.dpi = dpi

        # Try to import pdfplumber for table extraction
        try:
            import pdfplumber
            self.pdfplumber = pdfplumber
            self.use_pdfplumber = True
            logger.info("pdfplumber available for table extraction")
        except ImportError:
            self.pdfplumber = None
            self.use_pdfplumber = False
            logger.warning("pdfplumber not available, table extraction disabled")

    def _detect_page_type(
        self,
        page: pymupdf.Page,
        text_density_threshold: float = 0.3,
        image_area_threshold: float = 0.3,
    ) -> str:
        """
        Detect page type based on content analysis

        Args:
            page: PyMuPDF page object
            text_density_threshold: Minimum text density for TEXT classification
            image_area_threshold: Minimum image area for SCANNED/COMPLEX

        Returns:
            PageType string
        """
        # Get page dimensions
        page_area = page.rect.width * page.rect.height

        # Analyze text content
        text = page.get_text()
        text_blocks = page.get_text("blocks")
        text_area = sum(block[2] * block[3] for block in text_blocks if len(block) >= 7)
        text_density = text_area / page_area if page_area > 0 else 0

        # Analyze images
        image_list = page.get_images()
        image_area = 0
        for img in image_list:
            try:
                xref = img[0]
                bbox = page.get_image_bbox(img[7] if len(img) > 7 else xref)
                if bbox:
                    image_area += bbox.width * bbox.height
            except Exception:
                pass

        image_ratio = image_area / page_area if page_area > 0 else 0

        # Detect tables and diagrams (indicators of complex layout)
        # Simple heuristic: look for table-like patterns
        has_tables = self._detect_tables_heuristic(page)
        has_diagrams = len(image_list) > 0 and image_ratio > 0.1

        # Classification logic
        if text_density > text_density_threshold and image_ratio < 0.1:
            # Mostly text, minimal images
            return PageType.TEXT

        elif image_ratio > image_area_threshold and len(text.strip()) < 100:
            # Mostly images, minimal text (likely scanned)
            return PageType.SCANNED

        elif has_tables or has_diagrams or (text_density > 0.1 and image_ratio > 0.1):
            # Complex layout with mixed content
            return PageType.COMPLEX

        elif image_ratio > 0.2:
            # Significant image content
            return PageType.MIXED

        else:
            # Default to text
            return PageType.TEXT

    def _detect_tables_heuristic(self, page: pymupdf.Page) -> bool:
        """
        Simple heuristic to detect tables

        Args:
            page: PyMuPDF page

        Returns:
            True if tables likely present
        """
        # Look for table-like patterns (many horizontal/vertical lines)
        drawings = page.get_drawings()

        if not drawings:
            return False

        # Count horizontal and vertical lines
        h_lines = 0
        v_lines = 0

        for drawing in drawings:
            for item in drawing.get("items", []):
                # ✅ Check if item is a line and has enough elements
                if item and len(item) > 0 and item[0] == "l":  # Line
                    # ✅ Safely check tuple length before unpacking
                    if len(item) >= 5:
                        x1, y1, x2, y2 = item[1], item[2], item[3], item[4]
                        if abs(y1 - y2) < 1:  # Horizontal line
                            h_lines += 1
                        elif abs(x1 - x2) < 1:  # Vertical line
                            v_lines += 1

        # If many perpendicular lines, likely a table
        return h_lines >= 3 and v_lines >= 3

    async def _process_text_page(
        self,
        page: pymupdf.Page,
        page_num: int,
    ) -> Dict[str, Any]:
        """
        Process text-based page with PyMuPDF

        Args:
            page: PyMuPDF page
            page_num: Page number

        Returns:
            Processing result
        """
        text = page.get_text()

        return {
            "page_num": page_num,
            "page_type": PageType.TEXT,
            "text": text,
            "method": "pymupdf",
            "word_count": len(text.split()),
        }

    async def _process_scanned_page(
        self,
        page: pymupdf.Page,
        page_num: int,
    ) -> Dict[str, Any]:
        """
        Process scanned page with OCR

        Args:
            page: PyMuPDF page
            page_num: Page number

        Returns:
            Processing result
        """
        if not self.use_ocr:
            logger.warning(f"OCR disabled, falling back to PyMuPDF for page {page_num}")
            return await self._process_text_page(page, page_num)

        # Render page to image
        temp_file = self._render_page_to_image(page)

        try:
            # Use OCR
            result = await self.ocr_tool.extract_text(temp_file.name)

            return {
                "page_num": page_num,
                "page_type": PageType.SCANNED,
                "text": result.get("text", ""),
                "method": "ocr",
                "line_count": result.get("line_count", 0),
            }
        finally:
            # Clean up
            import os
            os.unlink(temp_file.name)

    async def _process_complex_page(
        self,
        page: pymupdf.Page,
        page_num: int,
    ) -> Dict[str, Any]:
        """
        Process complex page with Vision API

        Args:
            page: PyMuPDF page
            page_num: Page number

        Returns:
            Processing result
        """
        # Extract text with PyMuPDF first
        text_content = page.get_text()

        # If vision not available, return text only
        if not self.use_vision:
            logger.warning(f"Vision disabled, using PyMuPDF only for page {page_num}")
            return {
                "page_num": page_num,
                "page_type": PageType.COMPLEX,
                "text": text_content,
                "method": "pymupdf",
            }

        # Render page to image
        temp_file = self._render_page_to_image(page)

        try:
            # Use Vision API for comprehensive analysis
            vision_result = await self.vision_tool.analyze_image(
                temp_file.name,
                prompt="""Analyze this document page comprehensively. Extract:
                1. All text content (preserving structure)
                2. Description of any charts, graphs, or diagrams
                3. Description and content of any tables
                4. Overall page layout and structure

                Format the output to be clear and structured.""",
                resize=False,
            )

            # Extract tables if pdfplumber available
            tables = []
            if self.use_pdfplumber:
                tables = await self._extract_tables(page)

            return {
                "page_num": page_num,
                "page_type": PageType.COMPLEX,
                "text": text_content,  # Raw text from PyMuPDF
                "vision_analysis": vision_result.get("analysis", ""),
                "tables": tables,
                "method": "vision+pymupdf",
            }
        finally:
            # Clean up
            import os
            os.unlink(temp_file.name)

    async def _process_mixed_page(
        self,
        page: pymupdf.Page,
        page_num: int,
    ) -> Dict[str, Any]:
        """
        Process mixed-content page with combined strategies

        Args:
            page: PyMuPDF page
            page_num: Page number

        Returns:
            Processing result
        """
        # Extract text with PyMuPDF
        text_content = page.get_text()

        result = {
            "page_num": page_num,
            "page_type": PageType.MIXED,
            "text": text_content,
            "method": "pymupdf",
        }

        # Render page to image
        temp_file = self._render_page_to_image(page)

        try:
            # Try OCR if available and text is sparse
            if self.use_ocr and len(text_content.strip()) < 100:
                ocr_result = await self.ocr_tool.extract_text(temp_file.name)
                result["ocr_text"] = ocr_result.get("text", "")
                result["method"] = "pymupdf+ocr"

            # Try Vision if available
            if self.use_vision:
                vision_result = await self.vision_tool.analyze_image(
                    temp_file.name,
                    prompt="Describe this document page, focusing on any visual elements (charts, images, diagrams) and overall structure.",
                    resize=False,
                )
                result["vision_analysis"] = vision_result.get("analysis", "")
                result["method"] = result.get("method", "pymupdf") + "+vision"

            return result
        finally:
            # Clean up
            import os
            os.unlink(temp_file.name)

    def _render_page_to_image(self, page: pymupdf.Page) -> Any:
        """
        Render PDF page to temporary image file

        Args:
            page: PyMuPDF page

        Returns:
            NamedTemporaryFile object
        """
        mat = pymupdf.Matrix(self.dpi / 72, self.dpi / 72)
        pix = page.get_pixmap(matrix=mat)

        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        pix.save(temp_file.name)
        temp_file.close()

        return temp_file

    async def _extract_tables(self, page: pymupdf.Page) -> List[Dict[str, Any]]:
        """
        Extract tables from page using pdfplumber

        Args:
            page: PyMuPDF page

        Returns:
            List of table data
        """
        if not self.use_pdfplumber:
            return []

        # Note: This is a placeholder as integrating pdfplumber with PyMuPDF
        # requires additional handling. In practice, you'd process the PDF
        # separately with pdfplumber.
        # For now, return empty list
        return []

    async def process_pdf(
        self,
        pdf_path: str,
        pages: Optional[List[int]] = None,
        strategy: str = "auto",
    ) -> Dict[str, Any]:
        """
        Process entire PDF with intelligent strategy selection

        Args:
            pdf_path: Path to PDF file
            pages: Optional list of page numbers to process (0-indexed)
                  If None, process all pages
            strategy: Processing strategy:
                     - "auto": Automatic detection (default)
                     - "text": Force text extraction
                     - "ocr": Force OCR
                     - "vision": Force vision-based

        Returns:
            Dict with processing results
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            logger.info(f"Processing PDF: {pdf_path}")
            doc = pymupdf.open(pdf_path)

            # Determine which pages to process
            if pages is None:
                pages_to_process = list(range(len(doc)))
            else:
                pages_to_process = [p for p in pages if 0 <= p < len(doc)]

            # Process pages
            page_results = []
            page_type_counts = {
                PageType.TEXT: 0,
                PageType.SCANNED: 0,
                PageType.COMPLEX: 0,
                PageType.MIXED: 0,
            }

            for page_num in pages_to_process:
                page = doc[page_num]

                # Detect page type (unless strategy is forced)
                if strategy == "auto":
                    page_type = self._detect_page_type(page)
                elif strategy == "text":
                    page_type = PageType.TEXT
                elif strategy == "ocr":
                    page_type = PageType.SCANNED
                elif strategy == "vision":
                    page_type = PageType.COMPLEX
                else:
                    page_type = PageType.TEXT

                page_type_counts[page_type] += 1

                # Process based on type
                if page_type == PageType.TEXT:
                    result = await self._process_text_page(page, page_num)
                elif page_type == PageType.SCANNED:
                    result = await self._process_scanned_page(page, page_num)
                elif page_type == PageType.COMPLEX:
                    result = await self._process_complex_page(page, page_num)
                else:  # MIXED
                    result = await self._process_mixed_page(page, page_num)

                page_results.append(result)
                logger.debug(f"Processed page {page_num} as {page_type}")

            # Aggregate results
            all_text = []
            for result in page_results:
                # Combine all text sources
                text_parts = [result.get("text", "")]

                if "ocr_text" in result:
                    text_parts.append(result["ocr_text"])

                if "vision_analysis" in result:
                    text_parts.append(f"\n[Visual Analysis]\n{result['vision_analysis']}")

                combined_text = "\n".join(filter(None, text_parts))
                all_text.append(combined_text)

            # ✅ Save total_pages BEFORE closing the document
            total_pages = len(doc)
            doc.close()

            return {
                "pdf_path": str(pdf_path),
                "total_pages": total_pages,  # ✅ Use saved value
                "processed_pages": len(page_results),
                "page_type_distribution": page_type_counts,
                "pages": page_results,
                "full_text": "\n\n".join(all_text),
                "processing_strategy": strategy,
            }

        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}", exc_info=True)
            # ✅ Return complete error response with all expected fields
            return {
                "pdf_path": str(pdf_path),
                "error": str(e),
                "pages": [],
                "full_text": "",
                "total_pages": 0,  # ✅ Add missing field
                "processed_pages": 0,
                "page_type_distribution": {},  # ✅ Add missing field
                "processing_strategy": strategy,
            }

    async def extract_tables_from_pdf(
        self,
        pdf_path: str,
        pages: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extract all tables from PDF

        Args:
            pdf_path: Path to PDF
            pages: Optional list of page numbers

        Returns:
            List of table data
        """
        if not self.use_pdfplumber:
            logger.warning("pdfplumber not available, cannot extract tables")
            return []

        try:
            tables = []

            with self.pdfplumber.open(pdf_path) as pdf:
                pages_to_process = pages if pages else range(len(pdf.pages))

                for page_num in pages_to_process:
                    if page_num >= len(pdf.pages):
                        continue

                    page = pdf.pages[page_num]
                    page_tables = page.extract_tables()

                    for table_idx, table in enumerate(page_tables):
                        tables.append({
                            "page_num": page_num,
                            "table_num": table_idx,
                            "data": table,
                            "row_count": len(table),
                            "col_count": len(table[0]) if table else 0,
                        })

            logger.info(f"Extracted {len(tables)} tables from {pdf_path}")
            return tables

        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            return []

    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get processor capabilities

        Returns:
            Dict of available features
        """
        return {
            "text_extraction": True,  # Always available (PyMuPDF)
            "ocr": self.use_ocr,
            "vision": self.use_vision,
            "table_extraction": self.use_pdfplumber,
        }
