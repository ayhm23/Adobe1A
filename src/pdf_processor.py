"""Main PDF processing module with multi-core support."""

import fitz  # PyMuPDF
import numpy as np
import cv2
import time
import logging
from pathlib import Path
from typing import Dict, List, Any

from .layout_detector import LayoutDetector
from .hierarchy_manager import HierarchyManager
from .config import Config

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Main PDF processing class with PP-DocLayoutPlus integration."""

    def __init__(self):
        """Initialize PDF processor with layout detection and hierarchy management."""
        # Load configuration
        Config.load_config()

        # Initialize components (separate instances for each process)
        self.layout_detector = LayoutDetector()
        self.hierarchy_manager = HierarchyManager()

    def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Process a single PDF and extract its structured outline.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary containing title and outline structure
        """
        start_time = time.time()

        try:
            # Open PDF document
            doc = fitz.open(str(pdf_path))

            # Process each page and collect layout elements
            all_layout_elements = []

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)

                # Convert page to image for layout detection
                image = self._page_to_image(page)

                if image is not None:
                    # Detect layout elements
                    pdf_name = pdf_path.stem  # Get filename without extension
                    page_elements = self.layout_detector.detect_layout(image, page_num + 1, pdf_name)
                    all_layout_elements.extend(page_elements)

                    logger.debug(f"Page {page_num + 1}: Found {len(page_elements)} layout elements")

            # Close document
            doc.close()

            # Extract structured outline
            outline_data = self.hierarchy_manager.extract_document_outline(all_layout_elements)

            # Validate and clean up outline structure
            outline_data['outline'] = self.hierarchy_manager.validate_outline_structure(
                outline_data['outline']
            )

            processing_time = time.time() - start_time
            logger.info(f"Processed {pdf_path.name} in {processing_time:.2f}s - "
                       f"Found {len(outline_data['outline'])} headings")

            return outline_data

        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {str(e)}")
            return {
                "title": pdf_path.stem,
                "outline": [],
                "error": str(e)
            }

    def _page_to_image(self, page: fitz.Page) -> np.ndarray:
        """
        Convert a PDF page to a numpy image array.

        Args:
            page: PyMuPDF page object

        Returns:
            Image as numpy array (RGB)
        """
        try:
            # Create transformation matrix for desired DPI
            zoom = Config.PDF_DPI / 72.0  # 72 DPI is default
            mat = fitz.Matrix(zoom, zoom)

            # Render page to pixmap
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # Convert to numpy array
            img_data = pix.samples
            img = np.frombuffer(img_data, dtype=np.uint8).reshape(pix.height, pix.width, 3)

            # Convert RGB to BGR for OpenCV compatibility
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            return img

        except Exception as e:
            logger.warning(f"Failed to convert page to image: {e}")
            return None

    def extract_text_from_bbox(self, page: fitz.Page, bbox: List[float]) -> str:
        """
        Extract text from a specific bounding box on a page.

        Args:
            page: PyMuPDF page object
            bbox: Bounding box coordinates [x1, y1, x2, y2]

        Returns:
            Extracted text content
        """
        try:
            # Convert normalized coordinates if needed
            rect = fitz.Rect(bbox)

            # Extract text from the rectangle
            text = page.get_textbox(rect)

            return text.strip() if text else ""

        except Exception as e:
            logger.debug(f"Text extraction failed for bbox {bbox}: {e}")
            return ""

    def get_processing_stats(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Get processing statistics for a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary with file statistics
        """
        try:
            doc = fitz.open(str(pdf_path))
            stats = {
                "filename": pdf_path.name,
                "page_count": len(doc),
                "file_size_mb": pdf_path.stat().st_size / (1024 * 1024),
                "has_text": any(page.get_text().strip() for page in doc),
                "is_scanned": False  # Could be enhanced with image detection
            }
            doc.close()
            return stats

        except Exception as e:
            logger.error(f"Failed to get stats for {pdf_path.name}: {e}")
            return {
                "filename": pdf_path.name,
                "error": str(e)
            }
