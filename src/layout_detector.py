import numpy as np
import cv2
import re   
import time
from typing import List, Dict, Any
from paddleocr import LayoutDetection
import pytesseract
import os
import fitz  # PyMuPDF
from .config import Config


class LayoutDetector:
    """PaddleOCR PP-DocLayoutPlus-L layout detection wrapper."""

    def __init__(self, model_path=None):
        """Initialize the layout detection model."""
        # Check for provided model path first
        if model_path and os.path.exists(model_path) and self._validate_hf_model(model_path):
            print(f"[DEBUG] Using provided model from {model_path}")
            self.model = LayoutDetection(model_dir=model_path)
        else:
            # Check for HuggingFace model path
            hf_model_path = "/opt/pp_doclayout"
            
            if os.path.exists(hf_model_path) and self._validate_hf_model(hf_model_path):
                print(f"[DEBUG] Using HuggingFace model from {hf_model_path}")
                self.model = LayoutDetection(model_dir=hf_model_path)
            else:
                print(f"[DEBUG] HuggingFace model not found, using default model")
                # Fallback to default model
                self.model = LayoutDetection(
                    model_name=Config.MODEL_NAME,
                    layout_nms=Config.LAYOUT_NMS
                )
        
        # Define heading labels for filtering
        self.heading_labels = {
            "title", "heading", "section_title", "doc_title",
            "paragraph_title", "figure_title", "abstract"
        }

    def _validate_hf_model(self, model_path: str) -> bool:
        """Validate that the HuggingFace model has required files."""
        required_files = ["inference.pdiparams", "inference.yml"]
        for file in required_files:
            if not os.path.exists(os.path.join(model_path, file)):
                print(f"[DEBUG] Missing required file: {file}")
                return False
        return True


    def detect_layout(self, image: np.ndarray, page_num: int, pdf_name: str = "unknown", pdf_path: str = "unknown") -> List[Dict[str, Any]]:
        """
        Detect layout elements in an image using PP-DocLayoutPlus-L model.
        """
        detection_start_time = time.time()
        print(f"[DEBUG] Starting layout detection for page {page_num} at {time.strftime('%H:%M:%S', time.localtime(detection_start_time))}")
        
        try:
            # Run layout detection  
            detection_start_time1 = time.time()
            results = self.model.predict(image, batch_size=1, layout_nms=Config.LAYOUT_NMS)
            detection_end_time1 = time.time()
            print(f"[DEBUG] Layout detection took {detection_end_time1 - detection_start_time1:.2f} seconds")

            layout_elements = []
            
            # Process DetResult objects
            start_time2 = time.time()
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
            detection_end_time2 = time.time()
            print(f"[DEBUG] Processed {len(layout_elements)} layout elements in {detection_end_time2 - start_time2:.2f} seconds")
            # Sort by top-to-bottom
            layout_elements.sort(key=lambda x: x['center_y'])

            allowed_labels = ['title', 'paragraph_title', 'doc_title', 'heading', 'section_title', 'figure_title', 'table_title']
            filtered_elements = []

            # Filter and extract text in one loop
            start_time3 = time.time()
            for elem in layout_elements:
                # print(f"[DEBUG] Processing element: {elem['label']} with score {elem['score']}")
                if elem['score'] >= 0.55 and elem['label'] in allowed_labels:
                    # Only collect the element, do not extract text here
                    filtered_elements.append(elem)
            end_time3 = time.time()
            print(f"[DEBUG] Filtered {len(filtered_elements)} elements in {end_time3 - start_time3:.2f} seconds")

            # print("[DEBUG] layout_elements after score filtering:")
            for elem in filtered_elements:
                print(f"  label: {elem['label']}, score: {elem['score']}")

            detection_end_time = time.time()
            detection_duration = detection_end_time - detection_start_time
            print(f"[DEBUG] Layout detection completed for page {page_num} at {time.strftime('%H:%M:%S', time.localtime(detection_end_time))} (took {detection_duration:.2f}s)")
            print("\n\n")

            return filtered_elements

        except Exception as e:
            detection_end_time = time.time()
            detection_duration = detection_end_time - detection_start_time
            print(f"[LayoutDetector] Error after {detection_duration:.2f}s: {e}")
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
    
    def extract_text_fast(self, pdf_path: str,
                      page_number: int,
                      x1: float, y1: float, x2: float, y2: float,
                      dpi: int = 300) -> str:
        """
        Fast text extraction from a rectangular region of a PDF page.
        Falls back to OCR only if no digital text is present.

        Parameters
        ----------
        pdf_path : str
            Path to the PDF file.
        page_number : int
            Zero-based page index.
        x1, y1, x2, y2 : float
            Rectangle in pixel coordinates at the chosen DPI.
        dpi : int, optional
            Resolution assumed by the pixel coords (default 300).

        Returns
        -------
        str
            Trimmed text from the region (empty string if nothing found).
        """
        # 1 Load page -------------------------------------------------------------
        doc = fitz.open(pdf_path)
                        
        start_time4 = time.time()
        page = doc[page_number]

        # 2 Convert pixel rectangle → PDF points ---------------------------------
        # PDF units are 1/72 inch; pixel→pt = px * 72 / dpi
        scale = 72.0 / dpi
        rect = fitz.Rect(x1 * scale, y1 * scale, x2 * scale, y2 * scale)

        # 3 Try native extraction first ------------------------------------------
        # Check for digital glyphs by attempting to extract text
        text = page.get_text("text",
                             clip=rect,
                             flags=fitz.TEXTFLAGS_TEXT).strip()
        end_time4 = time.time()
        print(f"[DEBUG] Text extraction 1 took {end_time4 - start_time4:.2f} seconds")
        if text:
            doc.close()
            return " ".join(text.split())  # normalize whitespace

        # Secondary attempt—word-level filter for micro-rects
        # words = page.get_text("words", clip=rect)
        # if words:
        #     doc.close()
        #     return " ".join(w[4] for w in words)

        doc.close()
        return ""  # nothing found

    def _extract_text_from_region(self, image: np.ndarray, x1: float, y1: float, x2: float, y2: float, pdf_name: str = "unknown") -> str:
        """Improved text extraction with robust OCR preprocessing."""
        try:
            start_time = time.time()
            # Ensure integer coordinates and clamp within image
            # x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            h, w = image.shape[:2]
            x1i = max(0, min(int(np.floor(x1)), w-1))
            y1i = max(0, min(int(np.floor(y1)), h-1))
            x2i = max(x1i+1, min(int(np.ceil(x2)), w))
            y2i = max(y1i+1, min(int(np.ceil(y2)), h))
            cropped = image[y1i:y2i, x1i:x2i]

            # Save cropped image for debugging in separate folder per PDF
            # import os
            # import time
            # debug_dir = f"/app/debug_crops/{pdf_name}"
            # os.makedirs(debug_dir, exist_ok=True)
            # timestamp = int(time.time() * 1000000)  # microseconds for uniqueness
            # crop_filename = f"{debug_dir}/crop_{timestamp}_{x1i}_{y1i}_{x2i}_{y2i}.png"
            # cv2.imwrite(crop_filename, cropped)
            # print(f"[DEBUG] Saved cropped image: {crop_filename}")

            # Step 1: Convert to grayscale
            gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
            # cv2.imwrite(f"{debug_dir}/gray_{timestamp}_{x1i}_{y1i}_{x2i}_{y2i}.png", gray)

            
            # Step 4: Try multiple Tesseract configurations
            ocr_configs = [
                '--psm 6',   # Uniform block of text
                '--psm 7',   # Single text line
                '--psm 13',  # Raw line
            ]
            for config in ocr_configs:
                text = pytesseract.image_to_string(gray, config=config)
                if text and text.strip():
                    cleaned_text = self._clean_extracted_text(text)
                    if cleaned_text:
                        end_time = time.time()
                        print(f"[DEBUG] OCR extraction took {end_time - start_time:.2f} seconds")
                        return cleaned_text
                        
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
