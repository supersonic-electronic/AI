"""
Pluggable extractors for different file formats.
"""

from .base import BaseExtractor
from .pdf import PDFExtractor
from .html import HTMLExtractor
from .docx import DOCXExtractor
from .xml import XMLExtractor
from .latex import LaTeXExtractor
from .epub import EPUBExtractor
from .document_detector import DocumentDetector

__all__ = [
    'BaseExtractor',
    'PDFExtractor',
    'HTMLExtractor',
    'DOCXExtractor',
    'XMLExtractor',
    'LaTeXExtractor',
    'EPUBExtractor',
    'DocumentDetector',
]