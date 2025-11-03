"""
Multimodal Examples (Phase 4)

Demonstrates OCR, Vision API, and Advanced PDF Processing
"""

import asyncio
from pathlib import Path
from src.tools import OCRTool, VisionTool, AdvancedPDFProcessor
from src.utils import get_config


# ============================================================================
# Example 1: OCR - Extract Text from Images
# ============================================================================

async def example_ocr_basic():
    """
    Basic OCR text extraction from images
    """
    print("=" * 60)
    print("Example 1: OCR Text Extraction")
    print("=" * 60)

    # Initialize OCR tool
    ocr = OCRTool(
        languages=["ch", "en"],  # Chinese and English
        use_gpu=False,           # Use CPU (set True if GPU available)
    )

    print("\nOCR Tool initialized")
    print(f"Supported languages: {ocr.get_supported_languages()[:5]}...")

    # Example 1a: Extract text from image
    print("\n" + "-" * 60)
    print("1a. Extract text from image")
    print("-" * 60)

    # Note: You need to have an actual image file to test this
    image_path = "test_image.png"  # Replace with your image

    if Path(image_path).exists():
        result = await ocr.extract_text(image_path, return_structured=True)

        print(f"\nImage: {result['image_path']}")
        print(f"Detected {result['line_count']} lines of text\n")
        print("Extracted text:")
        print("-" * 40)
        print(result['text'])
        print("-" * 40)

        if result.get('structured_data'):
            print(f"\nStructured data: {len(result['structured_data'])} text regions")
            for i, region in enumerate(result['structured_data'][:3], 1):
                print(f"\nRegion {i}:")
                print(f"  Text: {region['text']}")
                print(f"  Confidence: {region['confidence']:.2f}")
    else:
        print(f"\n⚠️  Image file '{image_path}' not found")
        print("To test OCR, create a test image with text and update the path")

    # Example 1b: Batch processing
    print("\n" + "-" * 60)
    print("1b. Batch OCR (multiple images)")
    print("-" * 60)

    image_paths = ["image1.png", "image2.png", "image3.png"]
    existing_images = [p for p in image_paths if Path(p).exists()]

    if existing_images:
        print(f"Processing {len(existing_images)} images...")
        results = await ocr.extract_text_from_multiple(existing_images)

        for i, result in enumerate(results, 1):
            print(f"\nImage {i}: {result['image_path']}")
            print(f"  Lines: {result['line_count']}")
            print(f"  Preview: {result['text'][:100]}...")
    else:
        print("⚠️  No images found for batch processing")


# ============================================================================
# Example 2: Vision API - Image Understanding
# ============================================================================

async def example_vision_basic():
    """
    Basic vision API usage for image understanding
    """
    print("\n" + "=" * 60)
    print("Example 2: Vision API - Image Understanding")
    print("=" * 60)

    config = get_config()

    # Check if API key is configured
    if not config.multimodal.vision.api_key:
        print("\n⚠️  GOOGLE_API_KEY not configured")
        print("To use Vision API:")
        print("1. Get API key from: https://makersuite.google.com/app/apikey")
        print("2. Set GOOGLE_API_KEY in .env file or config.yaml")
        return

    # Initialize Vision tool
    vision = VisionTool(
        api_key=config.multimodal.vision.api_key,
        model="gemini-2.0-flash-exp",
    )

    print("\nVision Tool initialized")

    # Example 2a: General image analysis
    print("\n" + "-" * 60)
    print("2a. General image analysis")
    print("-" * 60)

    image_path = "photo.jpg"  # Replace with your image

    if Path(image_path).exists():
        result = await vision.analyze_image(
            image_path,
            prompt="Describe this image in detail, including objects, colors, scene, and any notable features."
        )

        print(f"\nImage: {result['image_path']}")
        print(f"Model: {result['model']}\n")
        print("Analysis:")
        print("-" * 40)
        print(result['analysis'])
        print("-" * 40)
    else:
        print(f"\n⚠️  Image '{image_path}' not found")

    # Example 2b: Document analysis
    print("\n" + "-" * 60)
    print("2b. Document/Receipt analysis")
    print("-" * 60)

    document_path = "receipt.jpg"  # Replace with receipt/invoice image

    if Path(document_path).exists():
        result = await vision.analyze_document(document_path)

        print(f"\nDocument: {result['image_path']}\n")
        print("Structured Analysis:")
        print("-" * 40)
        print(result['analysis'])
        print("-" * 40)
    else:
        print(f"\n⚠️  Document '{document_path}' not found")

    # Example 2c: Chart/Graph analysis
    print("\n" + "-" * 60)
    print("2c. Chart/Diagram analysis")
    print("-" * 60)

    chart_path = "chart.png"  # Replace with chart/graph image

    if Path(chart_path).exists():
        result = await vision.analyze_chart_or_diagram(chart_path)

        print(f"\nChart: {result['image_path']}\n")
        print("Analysis:")
        print("-" * 40)
        print(result['analysis'])
        print("-" * 40)
    else:
        print(f"\n⚠️  Chart '{chart_path}' not found")


# ============================================================================
# Example 3: Image Comparison
# ============================================================================

async def example_vision_comparison():
    """
    Compare multiple images using Vision API
    """
    print("\n" + "=" * 60)
    print("Example 3: Image Comparison")
    print("=" * 60)

    config = get_config()

    if not config.multimodal.vision.api_key:
        print("\n⚠️  Vision API not configured (see Example 2)")
        return

    vision = VisionTool(api_key=config.multimodal.vision.api_key)

    # Compare 2-4 images
    image_paths = ["before.jpg", "after.jpg"]

    existing_images = [p for p in image_paths if Path(p).exists()]

    if len(existing_images) >= 2:
        print(f"\nComparing {len(existing_images)} images...\n")

        result = await vision.compare_images(
            existing_images,
            comparison_prompt="Compare these images. Highlight similarities and differences."
        )

        print(f"Images: {result['image_count']}")
        print(f"Paths: {', '.join([Path(p).name for p in result['image_paths']])}\n")
        print("Comparison:")
        print("-" * 60)
        print(result['comparison'])
        print("-" * 60)
    else:
        print("\n⚠️  Need at least 2 images for comparison")
        print("Create 'before.jpg' and 'after.jpg' to test this feature")


# ============================================================================
# Example 4: Advanced PDF Processing
# ============================================================================

async def example_advanced_pdf():
    """
    Intelligent PDF processing with automatic strategy selection
    """
    print("\n" + "=" * 60)
    print("Example 4: Advanced PDF Processing")
    print("=" * 60)

    config = get_config()

    # Initialize tools
    ocr = OCRTool(languages=["ch", "en"])
    vision = None

    if config.multimodal.vision.api_key:
        vision = VisionTool(api_key=config.multimodal.vision.api_key)
        print("✓ Vision API enabled")
    else:
        print("⚠️  Vision API disabled (no API key)")

    # Initialize processor
    processor = AdvancedPDFProcessor(
        ocr_tool=ocr,
        vision_tool=vision,
        use_ocr=True,
        use_vision=(vision is not None),
        dpi=200,
    )

    print(f"\nCapabilities: {processor.get_capabilities()}")

    # Example 4a: Process entire PDF
    print("\n" + "-" * 60)
    print("4a. Process PDF with auto-detection")
    print("-" * 60)

    pdf_path = "sample.pdf"  # Replace with your PDF

    if Path(pdf_path).exists():
        print(f"\nProcessing: {pdf_path}")
        print("Strategy: auto (detect page type automatically)\n")

        result = await processor.process_pdf(
            pdf_path,
            strategy="auto"  # Auto-detect: text/scanned/complex
        )

        print(f"\n{'='*60}")
        print("Processing Results:")
        print(f"{'='*60}")
        print(f"Total pages: {result['total_pages']}")
        print(f"Processed: {result['processed_pages']}")
        print(f"Strategy: {result['processing_strategy']}")

        print(f"\nPage type distribution:")
        for page_type, count in result['page_type_distribution'].items():
            print(f"  {page_type}: {count} pages")

        # Show per-page details
        print(f"\n{'='*60}")
        print("Per-page details:")
        print(f"{'='*60}")

        for page_result in result['pages']:
            print(f"\nPage {page_result['page_num']}:")
            print(f"  Type: {page_result['page_type']}")
            print(f"  Method: {page_result['method']}")

            if page_result.get('word_count'):
                print(f"  Words: {page_result['word_count']}")

            if page_result.get('vision_analysis'):
                print(f"  Vision: {page_result['vision_analysis'][:100]}...")

        # Show full text preview
        print(f"\n{'='*60}")
        print("Full text preview:")
        print(f"{'='*60}")
        print(result['full_text'][:500] + "...")

    else:
        print(f"\n⚠️  PDF '{pdf_path}' not found")
        print("\nTo test PDF processing:")
        print("1. Place a PDF file named 'sample.pdf' in the project directory")
        print("2. Or update the pdf_path variable with your PDF path")

    # Example 4b: Process specific pages
    print("\n" + "-" * 60)
    print("4b. Process specific pages only")
    print("-" * 60)

    if Path(pdf_path).exists():
        print(f"\nProcessing pages 0, 1, 2 from: {pdf_path}\n")

        result = await processor.process_pdf(
            pdf_path,
            pages=[0, 1, 2],  # Only first 3 pages
            strategy="auto"
        )

        print(f"Processed {result['processed_pages']} pages")
        for page_result in result['pages']:
            print(f"  Page {page_result['page_num']}: {page_result['page_type']}")

    # Example 4c: Extract tables
    print("\n" + "-" * 60)
    print("4c. Extract tables from PDF")
    print("-" * 60)

    if Path(pdf_path).exists() and processor.use_pdfplumber:
        print(f"\nExtracting tables from: {pdf_path}\n")

        tables = await processor.extract_tables_from_pdf(pdf_path)

        if tables:
            print(f"Found {len(tables)} tables:\n")
            for table in tables:
                print(f"Page {table['page_num']}, Table {table['table_num']}:")
                print(f"  Size: {table['row_count']} rows x {table['col_count']} columns")

                # Show first few rows
                print(f"  Preview:")
                for row in table['data'][:3]:
                    print(f"    {row}")
        else:
            print("No tables found in PDF")
    elif not processor.use_pdfplumber:
        print("\n⚠️  pdfplumber not available (install with: pip install pdfplumber)")


# ============================================================================
# Example 5: Combined OCR and Vision
# ============================================================================

async def example_ocr_vs_vision():
    """
    Compare OCR and Vision approaches for text extraction
    """
    print("\n" + "=" * 60)
    print("Example 5: OCR vs Vision Comparison")
    print("=" * 60)

    config = get_config()

    if not config.multimodal.vision.api_key:
        print("\n⚠️  Vision API not configured")
        return

    ocr = OCRTool(languages=["ch", "en"])
    vision = VisionTool(api_key=config.multimodal.vision.api_key)

    image_path = "text_image.png"  # Image with text

    if not Path(image_path).exists():
        print(f"\n⚠️  Image '{image_path}' not found")
        return

    print(f"\nProcessing: {image_path}")

    # Method 1: OCR
    print("\n" + "-" * 60)
    print("Method 1: OCR (PaddleOCR)")
    print("-" * 60)

    ocr_result = await ocr.extract_text(image_path)
    print(f"\nLines detected: {ocr_result['line_count']}")
    print("Extracted text:")
    print("-" * 40)
    print(ocr_result['text'])
    print("-" * 40)

    # Method 2: Vision API
    print("\n" + "-" * 60)
    print("Method 2: Vision API (Gemini)")
    print("-" * 60)

    vision_result = await vision.extract_text_from_image(image_path)
    print("\nExtracted text:")
    print("-" * 40)
    print(vision_result['text'])
    print("-" * 40)

    # Comparison
    print("\n" + "-" * 60)
    print("Comparison:")
    print("-" * 60)
    print(f"OCR length: {len(ocr_result['text'])} chars")
    print(f"Vision length: {len(vision_result['text'])} chars")
    print("\nRecommendations:")
    print("  - OCR: Best for simple text extraction, faster, no API cost")
    print("  - Vision: Better for complex layouts, understands context")


# ============================================================================
# Example 6: Batch Processing
# ============================================================================

async def example_batch_processing():
    """
    Process multiple images in batch
    """
    print("\n" + "=" * 60)
    print("Example 6: Batch Image Processing")
    print("=" * 60)

    config = get_config()

    if not config.multimodal.vision.api_key:
        print("\n⚠️  Vision API not configured")
        return

    vision = VisionTool(api_key=config.multimodal.vision.api_key)

    # Batch process multiple images
    image_paths = [
        "image1.jpg",
        "image2.jpg",
        "image3.jpg",
    ]

    existing_images = [p for p in image_paths if Path(p).exists()]

    if existing_images:
        print(f"\nBatch processing {len(existing_images)} images...\n")

        results = await vision.batch_analyze(
            existing_images,
            prompt="Briefly describe this image in 1-2 sentences"
        )

        for i, result in enumerate(results, 1):
            print(f"Image {i}: {Path(result['image_path']).name}")
            print(f"  {result['analysis']}\n")

        print(f"✓ Processed {len(results)} images")
    else:
        print("\n⚠️  No images found for batch processing")


# ============================================================================
# Main
# ============================================================================

async def main():
    """Run all multimodal examples"""

    print("\n" + "=" * 60)
    print("MULTIMODAL EXAMPLES (Phase 4)")
    print("=" * 60)
    print("\nNote: Some examples require actual image/PDF files to work.")
    print("Update the file paths in the examples to test with your own files.\n")

    await example_ocr_basic()
    await example_vision_basic()
    await example_vision_comparison()
    await example_advanced_pdf()
    await example_ocr_vs_vision()
    await example_batch_processing()

    print("\n" + "=" * 60)
    print("All multimodal examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
