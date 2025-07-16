"""
HTML extractor using BeautifulSoup.
"""

import re
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Comment

from .base import BaseExtractor


class HTMLExtractor(BaseExtractor):
    """
    HTML document extractor using BeautifulSoup.
    
    Extracts text and metadata from HTML files with configurable options
    for tag filtering, content cleaning, and metadata extraction.
    """
    
    def __init__(self):
        """Initialize the HTML extractor."""
        self.soup = None
    
    def can_handle(self, file_path: Path) -> bool:
        """
        Check if this extractor can handle HTML files.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file has .html or .htm extension, False otherwise
        """
        return file_path.suffix.lower() in ['.html', '.htm']
    
    def extract_text(self, file_path: Path, config: Dict[str, Any]) -> str:
        """
        Extract text from an HTML file using BeautifulSoup.
        
        Args:
            file_path: Path to the HTML file
            config: Configuration dictionary
            
        Returns:
            Extracted text content
            
        Raises:
            Exception: If HTML cannot be opened or processed
        """
        try:
            # Read file with encoding detection
            encoding = config.get('html_encoding', 'utf-8')
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Fallback to latin-1 if UTF-8 fails
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            
            # Parse HTML
            parser = config.get('html_parser', 'lxml')
            self.soup = BeautifulSoup(content, parser)
            
            # Remove unwanted elements
            self._remove_unwanted_elements(config)
            
            # Extract text based on configuration
            if config.get('extract_main_content', True):
                text = self._extract_main_content(config)
            else:
                text = self._extract_all_text(config)
            
            # Clean and normalize text
            text = self._clean_text(text, config)
            
            return text
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise
    
    def _remove_unwanted_elements(self, config: Dict[str, Any]) -> None:
        """
        Remove unwanted HTML elements from the soup.
        
        Args:
            config: Configuration dictionary
        """
        # Default elements to remove
        remove_tags = config.get('remove_tags', [
            'script', 'style', 'nav', 'header', 'footer', 'aside',
            'advertisement', 'ads', 'banner', 'sidebar'
        ])
        
        # Remove specified tags
        for tag in remove_tags:
            for element in self.soup.find_all(tag):
                element.decompose()
        
        # Remove comments
        if config.get('remove_comments', True):
            for comment in self.soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()
        
        # Remove elements by class or id
        remove_classes = config.get('remove_classes', ['advertisement', 'ads', 'sidebar'])
        for class_name in remove_classes:
            for element in self.soup.find_all(class_=class_name):
                element.decompose()
        
        remove_ids = config.get('remove_ids', ['sidebar', 'ads', 'navigation'])
        for id_name in remove_ids:
            element = self.soup.find(id=id_name)
            if element:
                element.decompose()
    
    def _extract_main_content(self, config: Dict[str, Any]) -> str:
        """
        Extract main content from HTML using content detection heuristics.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Extracted main content text
        """
        # Try to find main content areas in order of preference
        content_selectors = config.get('content_selectors', [
            'main', 'article', '[role="main"]', '.content', '.main-content',
            '.article-content', '.post-content', '#content', '#main'
        ])
        
        for selector in content_selectors:
            content_element = self.soup.select_one(selector)
            if content_element:
                return self._extract_text_from_element(content_element, config)
        
        # Fallback: extract from body or entire document
        body = self.soup.find('body')
        if body:
            return self._extract_text_from_element(body, config)
        
        return self._extract_all_text(config)
    
    def _extract_all_text(self, config: Dict[str, Any]) -> str:
        """
        Extract all text from the HTML document.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            All text content
        """
        return self._extract_text_from_element(self.soup, config)
    
    def _extract_text_from_element(self, element, config: Dict[str, Any]) -> str:
        """
        Extract text from a specific HTML element.
        
        Args:
            element: BeautifulSoup element
            config: Configuration dictionary
            
        Returns:
            Extracted text
        """
        # Configure text extraction
        preserve_structure = config.get('preserve_html_structure', True)
        
        if preserve_structure:
            # Add line breaks for block elements
            for tag in element.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'br']):
                tag.append('\n')
        
        # Extract text
        text = element.get_text(separator=' ' if not preserve_structure else '')
        return text
    
    def _clean_text(self, text: str, config: Dict[str, Any]) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw extracted text
            config: Configuration dictionary
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        if config.get('normalize_whitespace', True):
            # Replace multiple spaces with single space
            text = re.sub(r' +', ' ', text)
            # Replace multiple newlines with double newline
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
            # Remove leading/trailing whitespace from lines
            lines = [line.strip() for line in text.split('\n')]
            text = '\n'.join(lines)
        
        # Remove empty lines if configured
        if config.get('remove_empty_lines', True):
            lines = [line for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
        
        return text.strip()
    
    def extract_metadata(self, file_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from an HTML file.
        
        Args:
            file_path: Path to the HTML file
            config: Configuration dictionary
            
        Returns:
            Dictionary containing HTML metadata
            
        Raises:
            Exception: If HTML cannot be opened or metadata cannot be extracted
        """
        try:
            # If soup not already created, create it
            if self.soup is None:
                encoding = config.get('html_encoding', 'utf-8')
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                
                parser = config.get('html_parser', 'lxml')
                self.soup = BeautifulSoup(content, parser)
            
            metadata = {
                'filename': file_path.name,
                'file_size': file_path.stat().st_size,
            }
            
            # Extract HTML meta tags
            self._extract_meta_tags(metadata)
            
            # Extract title
            title_tag = self.soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text().strip()
            
            # Extract headings structure
            if config.get('extract_headings', True):
                metadata['headings'] = self._extract_headings()
            
            # Extract links
            if config.get('extract_links', True):
                metadata['links'] = self._extract_links(file_path, config)
            
            # Extract language
            html_tag = self.soup.find('html')
            if html_tag and html_tag.get('lang'):
                metadata['language'] = html_tag.get('lang')
            
            # Remove empty values
            metadata = {k: v for k, v in metadata.items() if v}
            
            return metadata
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            raise
    
    def _extract_meta_tags(self, metadata: Dict[str, Any]) -> None:
        """
        Extract information from HTML meta tags.
        
        Args:
            metadata: Metadata dictionary to update
        """
        meta_tags = self.soup.find_all('meta')
        
        for meta in meta_tags:
            # Standard meta tags
            if meta.get('name'):
                name = meta.get('name').lower()
                content = meta.get('content', '').strip()
                if content:
                    if name in ['description', 'keywords', 'author', 'generator']:
                        metadata[name] = content
                    elif name == 'robots':
                        metadata['robots'] = content
            
            # Open Graph tags
            elif meta.get('property', '').startswith('og:'):
                property_name = meta.get('property')[3:]  # Remove 'og:' prefix
                content = meta.get('content', '').strip()
                if content:
                    metadata[f'og_{property_name}'] = content
            
            # Twitter Card tags
            elif meta.get('name', '').startswith('twitter:'):
                property_name = meta.get('name')[8:]  # Remove 'twitter:' prefix
                content = meta.get('content', '').strip()
                if content:
                    metadata[f'twitter_{property_name}'] = content
    
    def _extract_headings(self) -> Dict[str, list]:
        """
        Extract heading structure from HTML.
        
        Returns:
            Dictionary with heading levels and their text
        """
        headings = {}
        for level in range(1, 7):  # h1 to h6
            heading_tags = self.soup.find_all(f'h{level}')
            if heading_tags:
                headings[f'h{level}'] = [tag.get_text().strip() for tag in heading_tags]
        
        return headings
    
    def _extract_links(self, file_path: Path, config: Dict[str, Any]) -> Dict[str, list]:
        """
        Extract links from HTML.
        
        Args:
            file_path: Path to the HTML file
            config: Configuration dictionary
            
        Returns:
            Dictionary with internal and external links
        """
        links = {'internal': [], 'external': []}
        base_url = config.get('base_url', file_path.parent.as_uri())
        
        for link in self.soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text().strip()
            
            if not href:
                continue
            
            # Resolve relative URLs
            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)
            
            link_info = {
                'url': href,
                'text': text,
                'full_url': full_url
            }
            
            # Categorize as internal or external
            if parsed_url.netloc == '' or href.startswith('#'):
                links['internal'].append(link_info)
            else:
                links['external'].append(link_info)
        
        return links
    
    @property
    def supported_extensions(self) -> list[str]:
        """
        List of file extensions this extractor supports.
        
        Returns:
            List containing '.html' and '.htm'
        """
        return ['.html', '.htm']
    
    @property
    def extractor_name(self) -> str:
        """
        Human-readable name of this extractor.
        
        Returns:
            Name of the HTML extractor
        """
        return "HTML Extractor (BeautifulSoup)"