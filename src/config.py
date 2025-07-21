"""Configuration settings for PDF Outline Extractor."""

import json
import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Configuration management for the PDF processing application."""

    # Directory paths
    INPUT_DIR = Path("/app/input")
    OUTPUT_DIR = Path("/app/output")
    CONFIG_FILE = Path("/app/config.json")

    # Default processing settings
    MAX_WORKERS = min(8, os.cpu_count() or 4)
    PDF_DPI = 200
    IMAGE_QUALITY = 85

    # Model settings
    MODEL_NAME = "PP-DocLayout_plus-L" 
    CONFIDENCE_THRESHOLD = 0.5
    LAYOUT_NMS = True
    USE_GPU = False
    LANG = "en"

    # Hierarchy detection settings
    TITLE_HEIGHT_THRESHOLD = 20
    HEADING_PATTERNS = {
        "h1": [r"^\d+\.", r"^[IVX]+\.", r"^Chapter \d+", r"^Section \d+"],
        "h2": [r"^\d+\.\d+", r"^[A-Z]\.", r"^\d+\.\d+ "],  
        "h3": [r"^\d+\.\d+\.\d+", r"^[a-z]\)", r"^\([a-z]\)"]
    }

    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """Load configuration from config.json file."""
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                # Update class attributes from config
                cls.MODEL_NAME = config_data.get("model", {}).get("name", cls.MODEL_NAME)
                cls.CONFIDENCE_THRESHOLD = config_data.get("model", {}).get("confidence_threshold", cls.CONFIDENCE_THRESHOLD)
                cls.LAYOUT_NMS = config_data.get("model", {}).get("layout_nms", cls.LAYOUT_NMS)
                cls.USE_GPU = config_data.get("model", {}).get("use_gpu", cls.USE_GPU)
                cls.LANG = config_data.get("model", {}).get("lang", cls.LANG)

                cls.MAX_WORKERS = config_data.get("processing", {}).get("max_workers", cls.MAX_WORKERS)
                cls.PDF_DPI = config_data.get("processing", {}).get("pdf_dpi", cls.PDF_DPI)
                cls.IMAGE_QUALITY = config_data.get("processing", {}).get("image_quality", cls.IMAGE_QUALITY)

                cls.TITLE_HEIGHT_THRESHOLD = config_data.get("hierarchy", {}).get("title_height_threshold", cls.TITLE_HEIGHT_THRESHOLD)
                cls.HEADING_PATTERNS.update(config_data.get("hierarchy", {}).get("heading_patterns", {}))

                return config_data
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")

        return {}

    @classmethod
    def get_paddleocr_kwargs(cls) -> Dict[str, Any]:
        """Get PaddleOCR initialization arguments."""
        return {
            "use_angle_cls": True,
            "lang": cls.LANG,
            "use_gpu": cls.USE_GPU,
            "show_log": False,
            "cpu_threads": 4,  # Per-process threads
            "enable_mkldnn": True,
            "det_limit_side_len": 960,
            "det_limit_type": "max",
            "det_db_thresh": 0.3,
            "det_db_box_thresh": 0.6,
            "det_db_unclip_ratio": 1.5
        }
