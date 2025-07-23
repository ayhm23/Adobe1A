# src/page_worker.py
import os, fitz, numpy as np
from paddleocr import LayoutDetection
from pathlib import Path
from typing import Tuple, List, Dict, Any
from .config import Config                         # your existing Config

# -------- initialiser --------------------------------------------------
def init_worker(model_dir: str):
    """
    Called once per process; loads the detector into a global.
    """
    global DETECTOR
    DETECTOR = LayoutDetection(model_dir=model_dir)
    print(f"[INIT] Model loaded in PID {os.getpid()}")

# -------- per-page task -----------------------------------------------
def process_page(job: Tuple[str, int, str]) -> Tuple[str, int, List[Dict[str, Any]]]:
    """
    Parameters
    ----------
    job : (pdf_path, page_index, pdf_stem)

    Returns
    -------
    (pdf_path, page_index, layout_list)
    """
    pdf_path, page_idx, pdf_stem = job
    zoom = Config.PDF_DPI / 72.0

    doc  = fitz.open(pdf_path)
    page = doc.load_page(page_idx)

    mat  = fitz.Matrix(zoom, zoom)
    pix  = page.get_pixmap(matrix=mat, alpha=False)
    img  = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
              pix.height, pix.width, 3)

    # Call your high-level detector (no OCR here; only boxes)
    results = DETECTOR.predict(img, batch_size=1, layout_nms=True)

    # Return raw Paddle boxes; pdf_processor will post-process
    return (pdf_path, page_idx, results)
