"""Document Processor - Extract text from various file formats"""

from pathlib import Path
from typing import Dict, List, Optional

import fitz as pymupdf  # PyMuPDF
from docx import Document

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentProcessor:
    """Process documents and extract text content"""

    SUPPORTED_FORMATS = [".pdf", ".txt", ".md", ".docx"]

    def __init__(self):
        """Initialize Document Processor"""
        pass

    def process_file(self, file_path: str) -> List[Dict[str, any]]:
        """
        Process a file and extract text content

        Args:
            file_path: Path to the file

        Returns:
            List of chunks with content and metadata
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported file format: {suffix}. "
                f"Supported formats: {self.SUPPORTED_FORMATS}"
            )

        logger.info(f"Processing file: {file_path}")

        if suffix == ".pdf":
            return self.process_pdf(str(file_path))
        elif suffix == ".txt":
            return self.process_txt(str(file_path))
        elif suffix == ".md":
            return self.process_markdown(str(file_path))
        elif suffix == ".docx":
            return self.process_docx(str(file_path))
        else:
            raise ValueError(f"Unsupported format: {suffix}")

    def process_pdf(self, file_path: str) -> List[Dict[str, any]]:
        """
        Extract text from PDF using PyMuPDF (fastest option)

        Args:
            file_path: Path to PDF file

        Returns:
            List of page contents with metadata
        """
        chunks = []
        doc = pymupdf.open(file_path)

        for page_num, page in enumerate(doc):
            text = page.get_text()

            if text.strip():  # Only add non-empty pages
                chunks.append(
                    {
                        "content": text,
                        "metadata": {
                            "source": file_path,
                            "page": page_num + 1,
                            "total_pages": len(doc),
                            "file_type": "pdf",
                        },
                    }
                )

        doc.close()
        logger.info(f"Extracted {len(chunks)} pages from PDF: {file_path}")
        return chunks

    def process_txt(self, file_path: str) -> List[Dict[str, any]]:
        """
        Read plain text file

        Args:
            file_path: Path to text file

        Returns:
            List with single chunk
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return [
            {
                "content": content,
                "metadata": {
                    "source": file_path,
                    "file_type": "txt",
                },
            }
        ]

    def process_markdown(self, file_path: str) -> List[Dict[str, any]]:
        """
        Read markdown file

        Args:
            file_path: Path to markdown file

        Returns:
            List with single chunk
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return [
            {
                "content": content,
                "metadata": {
                    "source": file_path,
                    "file_type": "markdown",
                },
            }
        ]

    def process_docx(self, file_path: str) -> List[Dict[str, any]]:
        """
        Extract text from DOCX file

        Args:
            file_path: Path to DOCX file

        Returns:
            List of paragraph chunks
        """
        doc = Document(file_path)
        chunks = []

        # Extract paragraphs
        for i, para in enumerate(doc.paragraphs):
            text = para.text.strip()
            if text:  # Only add non-empty paragraphs
                chunks.append(
                    {
                        "content": text,
                        "metadata": {
                            "source": file_path,
                            "paragraph": i + 1,
                            "file_type": "docx",
                        },
                    }
                )

        logger.info(f"Extracted {len(chunks)} paragraphs from DOCX: {file_path}")
        return chunks

    def process_directory(
        self, directory_path: str, recursive: bool = True
    ) -> List[Dict[str, any]]:
        """
        Process all supported files in a directory

        Args:
            directory_path: Path to directory
            recursive: Whether to process subdirectories

        Returns:
            List of all chunks from all files
        """
        directory = Path(directory_path)

        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory_path}")

        all_chunks = []
        pattern = "**/*" if recursive else "*"

        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                try:
                    chunks = self.process_file(str(file_path))
                    all_chunks.extend(chunks)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")

        logger.info(
            f"Processed {len(all_chunks)} chunks from directory: {directory_path}"
        )
        return all_chunks

    def extract_metadata(self, file_path: str) -> Dict[str, any]:
        """
        Extract metadata from a file

        Args:
            file_path: Path to file

        Returns:
            Dictionary with metadata
        """
        file_path = Path(file_path)

        metadata = {
            "filename": file_path.name,
            "file_type": file_path.suffix.lower()[1:],
            "file_size": file_path.stat().st_size,
            "modified_time": file_path.stat().st_mtime,
        }

        # For PDF files, extract additional metadata
        if file_path.suffix.lower() == ".pdf":
            try:
                doc = pymupdf.open(str(file_path))
                metadata.update(
                    {
                        "page_count": len(doc),
                        "pdf_metadata": doc.metadata,
                    }
                )
                doc.close()
            except Exception as e:
                logger.error(f"Error extracting PDF metadata: {e}")

        return metadata
