#!/usr/bin/env python3
"""
PDF Outline Extractor using PP-DocLayout-M
Adobe India Hackathon Round 1A Solution

Extracts structured document outlines (title, H1/H2/H3 headings) from PDFs
using PaddleOCR PP-DocLayout-M model with multi-core processing.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from multiprocessing import Pool, cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed

from src.pdf_processor import PDFProcessor
from src.config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_single_pdf(pdf_path: Path) -> dict:
    """Process a single PDF file and extract its outline."""
    try:
        processor = PDFProcessor()
        outline = processor.process_pdf(pdf_path)

        # Save JSON output
        output_path = Config.OUTPUT_DIR / f"{pdf_path.stem}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(outline, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ Processed: {pdf_path.name} -> {output_path.name}")
        return {"pdf": pdf_path.name, "status": "success", "output": output_path.name}

    except Exception as e:
        logger.error(f"✗ Failed to process {pdf_path.name}: {str(e)}")
        return {"pdf": pdf_path.name, "status": "error", "error": str(e)}

def main():
    """Main entry point for batch PDF processing."""
    start_time = time.time()

    # Ensure output directory exists
    Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Find all PDF files in input directory
    pdf_files = list(Config.INPUT_DIR.glob("*.pdf"))

    if not pdf_files:
        logger.warning("No PDF files found in input directory")
        return

    logger.info(f"Found {len(pdf_files)} PDF files to process")
    logger.info(f"Using {Config.MAX_WORKERS} worker processes")

    # Process PDFs in parallel
    results = []
    with ProcessPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
        future_to_pdf = {executor.submit(process_single_pdf, pdf): pdf for pdf in pdf_files}

        for future in as_completed(future_to_pdf):
            result = future.result()
            results.append(result)

    # Summary statistics
    successful = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "error")

    elapsed_time = time.time() - start_time

    logger.info(f"\n{'='*50}")
    logger.info(f"PROCESSING COMPLETE")
    logger.info(f"{'='*50}")
    logger.info(f"Total PDFs: {len(pdf_files)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total time: {elapsed_time:.2f} seconds")
    logger.info(f"Average time per PDF: {elapsed_time/len(pdf_files):.2f} seconds")

    if failed > 0:
        logger.warning(f"Some files failed to process. Check logs above for details.")

if __name__ == "__main__":
    main()
