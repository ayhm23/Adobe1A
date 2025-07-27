import numpy as np
import cv2
import re   
from typing import List, Dict, Any
from paddleocr import LayoutDetection


from .config import Config


class LayoutDetector:
    """PaddleOCR PP-DocLayout-M layout detection wrapper."""

    def __init__(self):
        """Initialize the layout detection model."""
        MODEL_DIR = "/opt/pp_doclayout_M"          # absolute path inside container
        self.model = LayoutDetection(model_name='PP-DocLayout-M', 
                                    model_dir = MODEL_DIR, # NOT model_name!
                           layout_nms=True)

        # Layout category mapping
    
        
    def detect_layout(self, image: np.ndarray, page_num: int, pdf_name: str = "unknown") -> List[Dict[str, Any]]:
        """
        Detect layout elements in an image using PP-DocLayout-M model.
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

            allowed_labels = ['title', 'paragraph_title', 'doc_title', 'heading', 'section_title', 'figure_title', 'table_title']
            filtered_elements = []

            # Filter and extract text in one loop
            for elem in layout_elements:
                print(f"[DEBUG] Processing element: {elem['label']} with score {elem['score']}")
                if elem['score'] >= 0.55 and elem['label'] in allowed_labels:
                    x1, y1, x2, y2 = elem['bbox']
                    # elem['text'] = self._extract_text_from_region(image, x1, y1, x2, y2, pdf_name)
                    filtered_elements.append(elem)

            print("[DEBUG] layout_elements after score filtering:")
            for elem in filtered_elements:
                print(f"  label: {elem['label']}, score: {elem['score']}")

            print("\n\n")

            return filtered_elements

        except Exception as e:
            print(f"[LayoutDetector] Error: {e}")
            return []

    def _clean_extracted_text(self, text: str) -> str:
        """Clean extracted text by removing unwanted elements."""
        import re
        
        if not text:
            return ""
        
        # Remove newlines and replace with spaces
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Enhanced URL/link removal patterns
        url_patterns = [
            r'https?://\S+',                    # http:// or https:// URLs
            r'www\s*\.\s*\S+',                 # www. URLs (with possible spaces)
            r'WWW\s*\.\s*\S+',                 # WWW. URLs (with possible spaces)
            r'\S+\s*\.\s*com\S*',              # .com domains (with possible spaces)
            r'\S+\s*\.\s*org\S*',              # .org domains (with possible spaces)
            r'\S+\s*\.\s*net\S*',              # .net domains (with possible spaces)
            r'\S+\s*\.\s*edu\S*',              # .edu domains (with possible spaces)
            r'\S+\s*\.\s*gov\S*',              # .gov domains (with possible spaces)
            r'\S+\s*\.\s*COM\S*',              # Uppercase domains (with possible spaces)
            r'WWW\s*\.\s*[A-Z]+[A-Z0-9]*',     # Specific pattern for WWW .TOPJUMPCOM
            r'www\s*\.\s*[a-z]+[a-z0-9]*',     # Lowercase version
        ]
        
        for pattern in url_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+\.\S+', '', text)
        
        # Remove common social media handles and hashtags
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#\w+', '', text)
        
        # Remove phone numbers (basic patterns)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '', text)
        
        # Remove excessive whitespace (multiple spaces, tabs)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove common OCR artifacts
        text = re.sub(r'[|_]{2,}', '', text)  # Lines of underscores or pipes
        text = re.sub(r'[-]{3,}', '', text)   # Lines of dashes
        
        # Remove standalone punctuation
        text = re.sub(r'\s+[!.,:;]+\s*$', '', text)  # Trailing punctuation
        
        return text



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
      
