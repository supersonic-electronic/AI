"""
PDF extractor using PyMuPDF.
"""

import re
from pathlib import Path
from typing import Any, Dict

import fitz  # PyMuPDF

from .base import BaseExtractor


class PDFExtractor(BaseExtractor):
    """
    PDF document extractor using PyMuPDF.
    
    Extracts text and metadata from PDF files with configurable options
    for reading order, empty page handling, and DOI detection.
    """
    
    def __init__(self):
        """Initialize the PDF extractor."""
        self.doi_pattern = None
        self.doi_prefixes = []
    
    def can_handle(self, file_path: Path) -> bool:
        """
        Check if this extractor can handle PDF files.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file has .pdf extension, False otherwise
        """
        return file_path.suffix.lower() == '.pdf'
    
    def extract_text(self, file_path: Path, config: Dict[str, Any]) -> str:
        """
        Extract text from a PDF file using PyMuPDF.
        
        Args:
            file_path: Path to the PDF file
            config: Configuration dictionary
            
        Returns:
            Extracted text content from all pages
            
        Raises:
            Exception: If PDF cannot be opened or processed
        """
        try:
            doc = fitz.open(file_path)
            text_content = []
            empty_pages = []
            
            # Get streaming configuration
            chunk_size = config.get('pdf_chunk_size', 0)  # 0 = no chunking
            
            if chunk_size > 0:
                # Use chunked processing for large PDFs
                return self._extract_text_chunked(doc, file_path, config, chunk_size)
            
            # Standard processing
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Extract text with reading order preserved if configured
                sort_text = config.get('preserve_reading_order', True)
                page_text = page.get_text(sort=sort_text)
                
                if not page_text.strip():
                    empty_pages.append(page_num + 1)
                
                text_content.append(page_text)
            
            doc.close()
            
            # Log empty pages if configured
            if empty_pages and config.get('warn_empty_pages', True):
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Document {file_path.name} has {len(empty_pages)} empty pages: {empty_pages}")
            
            return "\n".join(text_content)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise
    
    def _extract_text_chunked(self, doc, file_path: Path, config: Dict[str, Any], chunk_size: int) -> str:
        """
        Extract text using chunked processing to reduce memory usage.
        
        Args:
            doc: Opened PyMuPDF document
            file_path: Path to the PDF file
            config: Configuration dictionary
            chunk_size: Number of pages to process at once
            
        Returns:
            Extracted text content
        """
        text_parts = []
        empty_pages = []
        sort_text = config.get('preserve_reading_order', True)
        
        for start_page in range(0, len(doc), chunk_size):
            end_page = min(start_page + chunk_size, len(doc))
            chunk_text = []
            
            for page_num in range(start_page, end_page):
                page = doc.load_page(page_num)
                page_text = page.get_text(sort=sort_text)
                
                if not page_text.strip():
                    empty_pages.append(page_num + 1)
                
                chunk_text.append(page_text)
                page = None  # Explicit cleanup to reduce memory usage
            
            text_parts.append('\n'.join(chunk_text))
        
        # Log empty pages if configured
        if empty_pages and config.get('warn_empty_pages', True):
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Document {file_path.name} has {len(empty_pages)} empty pages: {empty_pages}")
        
        return '\n'.join(text_parts)
    
    def extract_metadata(self, file_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from a PDF file with improved DOI detection.
        
        Args:
            file_path: Path to the PDF file
            config: Configuration dictionary
            
        Returns:
            Dictionary containing PDF metadata
            
        Raises:
            Exception: If PDF cannot be opened or metadata cannot be extracted
        """
        try:
            doc = fitz.open(file_path)
            metadata = doc.metadata
            doc.close()
            
            # Clean and structure metadata
            clean_metadata = {
                'filename': file_path.name,
                'file_size': file_path.stat().st_size,
                'title': metadata.get('title', '').strip(),
                'author': metadata.get('author', '').strip(),
                'subject': metadata.get('subject', '').strip(),
                'creator': metadata.get('creator', '').strip(),
                'producer': metadata.get('producer', '').strip(),
                'creation_date': metadata.get('creationDate', '').strip(),
                'modification_date': metadata.get('modDate', '').strip(),
                'keywords': metadata.get('keywords', '').strip(),
            }
            
            # Enhanced DOI extraction using regex
            doi = self._extract_doi(clean_metadata, config)
            clean_metadata['doi'] = doi
            
            # Remove empty values
            clean_metadata = {k: v for k, v in clean_metadata.items() if v}
            
            return clean_metadata
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            raise
    
    def _extract_doi(self, metadata: Dict[str, Any], config: Dict[str, Any]) -> str:
        """
        Extract DOI using regex patterns from metadata fields.
        
        Args:
            metadata: Metadata dictionary to search
            config: Configuration dictionary
            
        Returns:
            Extracted DOI string or empty string if not found
        """
        # Initialize regex pattern if not done already
        if self.doi_pattern is None:
            doi_regex = config.get('doi_regex', r'10\.[0-9]{4,}[-._;()/:a-zA-Z0-9]*')
            self.doi_pattern = re.compile(doi_regex)
            self.doi_prefixes = config.get('doi_prefixes', ['doi:', 'DOI:', 'https://doi.org/', 'http://dx.doi.org/'])
        
        # Search in multiple fields
        search_fields = ['title', 'subject', 'keywords', 'author']
        
        for field in search_fields:
            field_value = metadata.get(field, '')
            if not field_value:
                continue
                
            # First try to find DOI with prefixes
            for prefix in self.doi_prefixes:
                if prefix.lower() in field_value.lower():
                    # Extract text after prefix
                    start_idx = field_value.lower().find(prefix.lower()) + len(prefix)
                    remaining_text = field_value[start_idx:].strip()
                    
                    # Apply regex to extract DOI
                    match = self.doi_pattern.search(remaining_text)
                    if match:
                        return match.group(0)
            
            # Also try direct regex search without prefix
            match = self.doi_pattern.search(field_value)
            if match:
                return match.group(0)
        
        return ''
    
    @property
    def supported_extensions(self) -> list[str]:
        """
        List of file extensions this extractor supports.
        
        Returns:
            List containing '.pdf'
        """
        return ['.pdf']
    
    @property
    def extractor_name(self) -> str:
        """
        Human-readable name of this extractor.
        
        Returns:
            Name of the PDF extractor
        """
        return "PDF Extractor (PyMuPDF)"