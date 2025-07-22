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
                        # print(f"[DEBUG] Detected box: {box_data}")
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

            allowed_labels = ['title', 'paragraph_title', 'doc_title', 'heading', 'section_title', 'figure_title', 'table_title']
            filtered_elements = self.filter_elements_by_type(filtered_elements, allowed_labels)

            # Extract text only for filtered elements (after heading filtration)
            for elem in filtered_elements:
                x1, y1, x2, y2 = elem['bbox']
                elem['text'] = self._extract_text_from_region(image, x1, y1, x2, y2)

            print("[DEBUG] layout_elements after score filtering:")
            for elem in filtered_elements:
                print(f"  label: {elem['label']}, score: {elem['score']}")

            print("\n\n")

            return filtered_elements

        except Exception as e:
            print(f"[LayoutDetector] Error: {e}")
            return []



    def _extract_text_from_region(self, image: np.ndarray, x1: float, y1: float, x2: float, y2: float) -> str:
        """Improved text extraction with robust OCR preprocessing."""
        try:
            # Ensure integer coordinates and clamp within image
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
           
            h, w = image.shape[:2]
            x1i = max(0, min(int(np.floor(x1)), w-1))
            y1i = max(0, min(int(np.floor(y1)), h-1))
            x2i = max(x1i+1, min(int(np.ceil(x2)), w))
            y2i = max(y1i+1, min(int(np.ceil(y2)), h))
            cropped = image[y1i:y2i, x1i:x2i]

            # Save cropped image for debugging
            import os
            import time
            debug_dir = "/app/debug_crops"
            os.makedirs(debug_dir, exist_ok=True)
            timestamp = int(time.time() * 1000000)  # microseconds for uniqueness
            crop_filename = f"{debug_dir}/crop_{timestamp}_{x1i}_{y1i}_{x2i}_{y2i}.png"
            cv2.imwrite(crop_filename, cropped)
            print(f"[DEBUG] Saved cropped image: {crop_filename}")

            # Step 1: Convert to grayscale
            gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(f"{debug_dir}/gray_{timestamp}_{x1i}_{y1i}_{x2i}_{y2i}.png", gray)

            # Step 2: Adaptive threshold to binarize
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 15, 8
            )
            cv2.imwrite(f"{debug_dir}/binary_{timestamp}_{x1i}_{y1i}_{x2i}_{y2i}.png", binary)

            # Step 3 (Optional): Morphology to clean specks
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            cv2.imwrite(f"{debug_dir}/cleaned_{timestamp}_{x1i}_{y1i}_{x2i}_{y2i}.png", cleaned)
            
            # Step 4: Try multiple Tesseract configurations
            ocr_configs = [
                '--psm 6',   # Uniform block of text
                '--psm 7',   # Single text line
                '--psm 13',  # Raw line
            ]
            for config in ocr_configs:
                text = pytesseract.image_to_string(cleaned, config=config)
                if text and text.strip():
                    return text.strip()
            return "Text region"
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
