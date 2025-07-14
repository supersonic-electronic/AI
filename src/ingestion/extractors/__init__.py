"""
Pluggable extractors for different file formats.
"""

from .base import BaseExtractor
from .pdf import PDFExtractor

__all__ = ['BaseExtractor', 'PDFExtractor']