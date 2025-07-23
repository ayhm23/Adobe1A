"""Intelligent hierarchy management for PDF outline extraction."""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .config import Config

@dataclass
class HeadingCandidate:
    """Represents a potential heading with its properties."""
    text: str
    level: str
    page: int
    bbox: List[float]
    height: float
    score: float
    position_y: float
    label: str

class HierarchyManager:
    """Manages the intelligent classification of headings into H1, H2, H3 levels."""

    def __init__(self):
        """Initialize hierarchy detection patterns."""
        self.patterns = {
            'h1': [
                re.compile(r'^\d+\.\s+', re.IGNORECASE),           # "1. Introduction"
                re.compile(r'^[IVX]+\.\s+', re.IGNORECASE),         # "I. Overview"  
                re.compile(r'^Chapter\s+\d+', re.IGNORECASE),       # "Chapter 1"
                re.compile(r'^Section\s+\d+', re.IGNORECASE),       # "Section 1"
                re.compile(r'^Part\s+[IVX]+', re.IGNORECASE),        # "Part I"
                re.compile(r'^\d+\s+[A-Z]', re.IGNORECASE),         # "1 INTRODUCTION"
            ],
            'h2': [
                re.compile(r'^\d+\.\d+\s+', re.IGNORECASE),       # "1.1 Overview"
                re.compile(r'^[A-Z]\.\s+', re.IGNORECASE),          # "A. Methods"
                re.compile(r'^\d+\.\d+\.?\s+', re.IGNORECASE),   # "2.1. Results"
                re.compile(r'^\([A-Z]\)\s+', re.IGNORECASE),       # "(A) Analysis"
            ],
            'h3': [
                re.compile(r'^\d+\.\d+\.\d+\s+', re.IGNORECASE), # "1.1.1 Details"
                re.compile(r'^[a-z]\)\s+', re.IGNORECASE),           # "a) Methods"  
                re.compile(r'^\([a-z]\)\s+', re.IGNORECASE),        # "(a) Results"
                re.compile(r'^[ivx]+\.\s+', re.IGNORECASE),          # "i. Summary"
                re.compile(r'^\d+\.\d+\.\d+\.\s+', re.IGNORECASE), # "1.1.1. Item"
            ]
        }

    def extract_document_outline(self, layout_elements: List[Dict]) -> Dict[str, Any]:
        """
        Extract structured document outline from layout elements.

        Args:
            layout_elements: List of detected layout elements from all pages

        Returns:
            Dictionary with title and hierarchical outline
        """
        # Step 1: Extract document title
        title = self._extract_document_title(layout_elements)

        # Step 2: Get heading candidates
        heading_candidates = self._get_heading_candidates(layout_elements)

        # Step 3: Classify heading levels
        classified_headings = self._classify_heading_levels(heading_candidates)

        # Step 4: Build final outline structure
        outline = self._build_outline_structure(classified_headings)

        return {
            "title": title,
            "outline": outline
        }

    def _extract_document_title(self, elements: List[Dict]) -> str:
        """Extract the main document title."""
        # Look for title elements on the first page
        page_1_elements = [elem for elem in elements if elem.get('page', 1) == 1]

        # Priority order: doc_title > title > large paragraph_title
        title_candidates = []

        for elem in page_1_elements:
            label = elem.get('label', '')
            height = elem.get('height', 0)
            y_pos = elem.get('center_y', 0)
            text = elem.get('text', '').strip()

            if not text or len(text) < 3:
                continue

            # Score based on label, size, and position    
            score = 0
            if label == 'doc_title':
                score += 10
            elif label == 'title':  
                score += 8
            elif label == 'paragraph_title' and height > Config.TITLE_HEIGHT_THRESHOLD:
                score += 6
            elif label == 'text' and height > Config.TITLE_HEIGHT_THRESHOLD * 1.5:
                score += 4

            # Boost score for elements near top of page
            if y_pos < 200:  # Top 200 pixels
                score += 3
            elif y_pos < 400:  # Top 400 pixels
                score += 1

            # Boost score for larger text
            if height > 25:
                score += 2
            elif height > 20:
                score += 1

            if score > 0:
                title_candidates.append({
                    'text': text,
                    'score': score,
                    'height': height,
                    'y_pos': y_pos
                })

        if title_candidates:
            # Sort by score (highest first), then by position (topmost first)
            title_candidates.sort(key=lambda x: (-x['score'], x['y_pos']))
            return title_candidates[0]['text']

        return "Document"  # Default title

    def _get_heading_candidates(self, elements: List[Dict]) -> List[HeadingCandidate]:
        """Get potential heading elements from layout detection."""
        candidates = []

        for elem in elements:
            label = elem.get('label', '')
            text = elem.get('text', '').strip()

            # Skip elements that are clearly not headings
            if not text or len(text) > 200:  # Too long to be a heading
                continue

            if label in ['paragraph_title', 'title']:
                # Skip if this looks like the document title
                if (elem.get('page', 1) == 1 and 
                    elem.get('center_y', 0) < 300 and 
                    elem.get('height', 0) > Config.TITLE_HEIGHT_THRESHOLD):
                    continue

                candidate = HeadingCandidate(
                    text=text,
                    level='unknown',
                    page=elem.get('page', 1),
                    bbox=elem.get('bbox', []),
                    height=elem.get('height', 0),
                    score=elem.get('score', 0),
                    position_y=elem.get('center_y', 0),
                    label=label
                )
                candidates.append(candidate)

        return candidates

    def _classify_heading_levels(self, candidates: List[HeadingCandidate]) -> List[HeadingCandidate]:
        """Classify heading candidates into H1, H2, H3 levels."""
        for candidate in candidates:
            candidate.level = self._determine_heading_level(candidate.text, candidate.height)

        # Sort by page and position for hierarchical consistency
        candidates.sort(key=lambda x: (x.page, x.position_y))

        # Apply contextual refinements
        candidates = self._refine_hierarchy_context(candidates)

        return candidates

    def _determine_heading_level(self, text: str, height: float) -> str:
        """Determine the hierarchical level of a heading based on patterns and formatting."""
        text = text.strip()

        # Pattern-based classification (highest priority)
        for level, patterns in self.patterns.items():
            for pattern in patterns:
                if pattern.match(text):
                    return level.upper()  # Return H1, H2, H3

        # Size-based fallback classification
        if height > 18:
            return 'H1'
        elif height > 14:
            return 'H2'
        else:
            return 'H3'

    def _refine_hierarchy_context(self, candidates: List[HeadingCandidate]) -> List[HeadingCandidate]:
        """Refine hierarchy based on document context and consistency."""
        if not candidates:
            return candidates

        # Group by height ranges for consistency
        height_groups = {}
        for candidate in candidates:
            height_key = round(candidate.height / 2) * 2  # Round to nearest 2
            if height_key not in height_groups:
                height_groups[height_key] = []
            height_groups[height_key].append(candidate)

        # Assign consistent levels to similar height groups
        sorted_heights = sorted(height_groups.keys(), reverse=True)
        level_mapping = {}

        for i, height in enumerate(sorted_heights[:3]):  # Max 3 levels
            level_mapping[height] = ['H1', 'H2', 'H3'][i]

        # Apply height-based consistency where pattern-based detection failed
        for candidate in candidates:
            if candidate.level == 'H3':  # Default from size-based detection
                height_key = round(candidate.height / 2) * 2
                if height_key in level_mapping:
                    candidate.level = level_mapping[height_key]

        return candidates

    def _build_outline_structure(self, headings: List[HeadingCandidate]) -> List[Dict[str, Any]]:
        """Build the final outline structure for JSON output."""
        outline = []

        for heading in headings:
            outline_entry = {
                "level": heading.level,
                "text": heading.text,
                "page": heading.page
            }
            outline.append(outline_entry)

        return outline

    def validate_outline_structure(self, outline: List[Dict]) -> List[Dict]:
        """Validate and clean up the outline structure."""
        if not outline:
            return outline

        cleaned_outline = []
        prev_level_num = 0

        for entry in outline:
            level = entry.get('level', 'H3')
            text = entry.get('text', '').strip()

            # Skip empty entries
            if not text:
                continue

            # Convert level to number for comparison
            level_num = {'H1': 1, 'H2': 2, 'H3': 3}.get(level, 3)

            # Ensure hierarchical consistency (no level skipping)
            if prev_level_num > 0 and level_num > prev_level_num + 1:
                level_num = prev_level_num + 1
                level = f'H{level_num}'
                entry['level'] = level

            prev_level_num = level_num
            cleaned_outline.append(entry)

        return cleaned_outline
