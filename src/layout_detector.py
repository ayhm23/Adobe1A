import numpy as np
import cv2
from typing import List, Dict, Any
from paddleocr import LayoutDetection
import pytesseract

from .config import Config


class LayoutDetector:
    """PaddleOCR PP-DocLayoutPlus-L layout detection wrapper."""

    def __init__(self):
        """Initialize the layout detection model."""
        self.model = LayoutDetection(
            model_name=Config.MODEL_NAME,  # e.g., "PP-DocLayout_plus_L"
            layout_nms=Config.LAYOUT_NMS
        )

        # Layout category mapping
        self.category_mapping = {
            0: "paragraph_title",
            1: "image",
            2: "text",
            3: "title",
            4: "table",
            5: "figure",
            6: "figure_caption",
            7: "formula",
            8: "table",
            9: "table_caption",
            10: "reference",
            11: "doc_title",
            12: "footnote",
            13: "header",
            14: "footer",
            15: "algorithm",
            16: "page_number",
            17: "abstract",
            18: "contents",
            19: "seal",
            20: "header_image",
            21: "footer_image",
            22: "aside_text"
        }

  
        
    def detect_layout(self, image: np.ndarray, page_num: int) -> List[Dict[str, Any]]:
        """
        Detect layout elements in an image using PP-DocLayoutPlus-L model.
        """
        try:
            # Run layout detection  
            results = self.model.predict(image, batch_size=1, layout_nms=Config.LAYOUT_NMS)
        
            layout_elements = []
            
            # Process DetResult objects
            for res in results:
                # Convert DetResult to dictionary format
                res_dict = res if isinstance(res, dict) else None
            
                if res_dict and 'boxes' in res_dict:
                    boxes_data = res_dict['boxes']
                   
                    for box_data in boxes_data:
                        score = box_data.get('score', 0.0)
                        if score < Config.CONFIDENCE_THRESHOLD:
                            continue
                            
                        # Extract coordinates - note they're in 'coordinate' field, not 'bbox'
                        x1, y1, x2, y2 = map(float, box_data['coordinate'])
                        width = x2 - x1
                        height = y2 - y1
                        area = width * height
                        aspect_ratio = width / height if height > 0 else 0
                        
                        element = {
                            "label": box_data['label'],
                            "cls_id": int(box_data['cls_id']),
                            "score": float(score),
                            "bbox": [x1, y1, x2, y2],
                            "width": width,
                            "height": height,
                            "area": area,
                            "aspect_ratio": aspect_ratio,
                            "text": self._extract_text_from_region(image, x1, y1, x2, y2),
                            "page": page_num,
                            "center_x": (x1 + x2) / 2,
                            "center_y": (y1 + y2) / 2
                        }
                        
                        layout_elements.append(element)
                
            # Sort by top-to-bottom
            layout_elements.sort(key=lambda x: x['center_y'])

        
            filtered_elements = [
                elem for elem in layout_elements
                if elem['score'] >= 0
            ]

            allowed_labels = ['title', 'paragraph_title', 'doc_title', 'heading', 'section_title']
            filtered_elements = self.filter_elements_by_type(filtered_elements, allowed_labels)

            print("[DEBUG] layout_elements after score filtering:")
            for elem in filtered_elements:
                print(f"  label: {elem['label']}, score: {elem['score']}")

            print("\n\n")

            return filtered_elements

        except Exception as e:
            print(f"[LayoutDetector] Error: {e}")
            return []



    def _extract_text_from_region(self, image: np.ndarray, x1: float, y1: float, x2: float, y2: float) -> str:
        """Dummy text extraction from a region. For real implementation, run OCR here."""
        try:
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            h, w = image.shape[:2]
            x1 = max(0, min(x1, w-1))
            y1 = max(0, min(y1, h-1))
            x2 = max(x1+1, min(x2, w))
            y2 = max(y1+1, min(y2, h))
            cropped = image[y1:y2, x1:x2]
            text = pytesseract.image_to_string(cropped)
            return text.strip()
        except Exception as e:
            print(f"OCR extraction error: {e}")
            return "Text region"


    def filter_elements_by_type(self, elements: List[Dict], 
                               element_types: List[str]) -> List[Dict]:
        """Filter layout elements by their label types."""
        return [elem for elem in elements if elem['label'] in element_types]

    def get_title_candidates(self, elements: List[Dict]) -> List[Dict]:
        """Get elements that could be document titles."""
        title_labels = ['title', 'doc_title', 'paragraph_title']
        candidates = self.filter_elements_by_type(elements, title_labels)

        # Filter by position (top of first page) and size
        page_1_candidates = [elem for elem in candidates if elem['page'] == 1]

        # Sort by position (higher on page) and size (larger)
        page_1_candidates.sort(key=lambda x: (-x['height'], x['center_y']))

        return page_1_candidates

    def get_heading_candidates(self, elements: List[Dict]) -> List[Dict]:
        """Get elements that could be section headings."""
        heading_labels = ['paragraph_title', 'title', 'doc_title', 'heading', 'section_title']
        return self.filter_elements_by_type(elements, heading_labels)
        heading_labels = ['paragraph_title', 'title', 'doc_title', 'heading', 'section_title']
        return self.filter_elements_by_type(elements, heading_labels)
