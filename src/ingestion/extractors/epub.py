"""
EPUB extractor using ebooklib.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import zipfile

from bs4 import BeautifulSoup, Comment
from ebooklib import epub
import ebooklib

from .base import BaseExtractor


class EPUBExtractor(BaseExtractor):
    """
    EPUB document extractor using ebooklib.
    
    Extracts text and metadata from EPUB files with configurable options
    for chapter processing, mathematical content handling, and structure preservation.
    Supports both EPUB2 and EPUB3 formats.
    """
    
    def __init__(self):
        """Initialize the EPUB extractor."""
        self.book = None
    
    def can_handle(self, file_path: Path) -> bool:
        """
        Check if this extractor can handle EPUB files.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file has .epub extension, False otherwise
        """
        return file_path.suffix.lower() == '.epub'
    
    def extract_text(self, file_path: Path, config: Dict[str, Any]) -> str:
        """
        Extract text from an EPUB file using ebooklib.
        
        Args:
            file_path: Path to the EPUB file
            config: Configuration dictionary
            
        Returns:
            Extracted text content with chapter boundaries preserved
            
        Raises:
            Exception: If EPUB cannot be opened or processed
        """
        try:
            # Load the EPUB book
            self.book = epub.read_epub(str(file_path))
            
            # Extract text from all chapters
            chapters_text = []
            
            # Get all document items (chapters)
            items = list(self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
            
            # Process chapters individually to preserve structure
            process_individually = config.get('process_chapters_individually', True)
            
            for i, item in enumerate(items):
                chapter_text = self._extract_chapter_text(item, config)
                
                if chapter_text.strip():
                    if process_individually:
                        # Add chapter marker
                        chapter_title = self._get_chapter_title(item, i + 1)
                        chapters_text.append(f"[CHAPTER {i + 1}: {chapter_title}]\n\n{chapter_text}")
                    else:
                        chapters_text.append(chapter_text)
            
            # Join all chapters
            if process_individually:
                text = '\n\n[CHAPTER BREAK]\n\n'.join(chapters_text)
            else:
                text = '\n\n'.join(chapters_text)
            
            # Clean and normalize text
            text = self._clean_text(text, config)
            
            return text
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise
    
    def _extract_chapter_text(self, item, config: Dict[str, Any]) -> str:
        """
        Extract text from a single chapter item.
        
        Args:
            item: EPUB chapter item
            config: Configuration dictionary
            
        Returns:
            Extracted chapter text
        """
        try:
            # Get HTML content
            content = item.get_content()
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            
            # Parse HTML with BeautifulSoup
            parser = config.get('html_parser', 'lxml')
            soup = BeautifulSoup(content, parser)
            
            # Remove unwanted elements
            self._remove_unwanted_elements(soup, config)
            
            # Handle mathematical content (MathML)
            if config.get('extract_mathml', True):
                self._process_mathml_content(soup, config)
            
            # Extract text
            text = soup.get_text(separator='\n', strip=True)
            
            return text
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error extracting chapter text: {e}")
            return ""
    
    def _get_chapter_title(self, item, chapter_num: int) -> str:
        """
        Extract chapter title from item or generate default.
        
        Args:
            item: EPUB chapter item
            chapter_num: Chapter number
            
        Returns:
            Chapter title or default name
        """
        try:
            # Try to get title from item
            if hasattr(item, 'title') and item.title:
                return item.title
            
            # Try to get from content
            content = item.get_content()
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            
            soup = BeautifulSoup(content, 'lxml')
            
            # Look for title in h1, h2, title tags
            for tag in ['h1', 'h2', 'h3', 'title']:
                title_elem = soup.find(tag)
                if title_elem and title_elem.get_text(strip=True):
                    return title_elem.get_text(strip=True)
            
            # Fallback to filename
            if hasattr(item, 'file_name') and item.file_name:
                return Path(item.file_name).stem
                
        except Exception:
            pass
        
        # Default chapter name
        return f"Chapter {chapter_num}"
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup, config: Dict[str, Any]) -> None:
        """
        Remove unwanted HTML elements from the soup.
        
        Args:
            soup: BeautifulSoup object
            config: Configuration dictionary
        """
        # Default elements to remove
        remove_tags = config.get('remove_tags', [
            'script', 'style', 'nav', 'header', 'footer', 'aside'
        ])
        
        # Remove specified tags
        for tag_name in remove_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # Remove comments
        if config.get('remove_comments', True):
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()
        
        # Remove empty paragraphs
        if config.get('remove_empty_paragraphs', True):
            for p in soup.find_all('p'):
                if not p.get_text(strip=True):
                    p.decompose()
    
    def _process_mathml_content(self, soup: BeautifulSoup, config: Dict[str, Any]) -> None:
        """
        Process MathML content and convert to LaTeX format.
        
        Args:
            soup: BeautifulSoup object
            config: Configuration dictionary
        """
        # Find all MathML elements
        mathml_elements = soup.find_all(['math', 'mml:math'])
        
        for math_elem in mathml_elements:
            try:
                # Extract MathML content
                mathml_content = str(math_elem)
                
                # Convert to LaTeX (basic conversion)
                latex_content = self._mathml_to_latex(math_elem, config)
                
                # Replace MathML with LaTeX notation
                if latex_content:
                    # Create a new text node with LaTeX
                    latex_text = f" ${latex_content}$ "
                    math_elem.replace_with(latex_text)
                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Error processing MathML: {e}")
                # Keep original content if conversion fails
                continue
    
    def _mathml_to_latex(self, math_elem, config: Dict[str, Any]) -> str:
        """
        Convert MathML element to LaTeX format.
        
        Args:
            math_elem: MathML element
            config: Configuration dictionary
            
        Returns:
            LaTeX representation of the mathematical expression
        """
        try:
            # Basic MathML to LaTeX conversion
            # This is a simplified conversion - full MathML parsing would require more sophisticated logic
            
            # Get text content and clean it
            math_text = math_elem.get_text(strip=True)
            
            # Handle common mathematical symbols
            symbol_map = {
                '∫': r'\int',
                '∑': r'\sum',
                '∏': r'\prod',
                '∂': r'\partial',
                '∇': r'\nabla',
                '∞': r'\infty',
                '≤': r'\leq',
                '≥': r'\geq',
                '≠': r'\neq',
                '≈': r'\approx',
                '±': r'\pm',
                '×': r'\times',
                '÷': r'\div',
                '√': r'\sqrt',
                'α': r'\alpha',
                'β': r'\beta',
                'γ': r'\gamma',
                'δ': r'\delta',
                'ε': r'\epsilon',
                'θ': r'\theta',
                'λ': r'\lambda',
                'μ': r'\mu',
                'π': r'\pi',
                'ρ': r'\rho',
                'σ': r'\sigma',
                'τ': r'\tau',
                'φ': r'\phi',
                'ψ': r'\psi',
                'ω': r'\omega',
            }
            
            # Replace symbols
            for symbol, latex in symbol_map.items():
                math_text = math_text.replace(symbol, latex)
            
            # Handle fractions (basic pattern)
            # Look for mfrac elements
            mfrac_elements = math_elem.find_all('mfrac')
            for mfrac in mfrac_elements:
                children = mfrac.find_all(['mn', 'mi', 'mo'])
                if len(children) >= 2:
                    numerator = children[0].get_text(strip=True)
                    denominator = children[1].get_text(strip=True)
                    frac_latex = f"\\frac{{{numerator}}}{{{denominator}}}"
                    # This is a simplified replacement
                    math_text = math_text.replace(mfrac.get_text(strip=True), frac_latex)
            
            # Handle superscripts and subscripts
            msup_elements = math_elem.find_all('msup')
            for msup in msup_elements:
                children = msup.find_all(['mn', 'mi', 'mo'])
                if len(children) >= 2:
                    base = children[0].get_text(strip=True)
                    superscript = children[1].get_text(strip=True)
                    sup_latex = f"{base}^{{{superscript}}}"
                    math_text = math_text.replace(msup.get_text(strip=True), sup_latex)
            
            msub_elements = math_elem.find_all('msub')
            for msub in msub_elements:
                children = msub.find_all(['mn', 'mi', 'mo'])
                if len(children) >= 2:
                    base = children[0].get_text(strip=True)
                    subscript = children[1].get_text(strip=True)
                    sub_latex = f"{base}_{{{subscript}}}"
                    math_text = math_text.replace(msub.get_text(strip=True), sub_latex)
            
            return math_text
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Error in MathML to LaTeX conversion: {e}")
            return math_elem.get_text(strip=True)
    
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
        Extract metadata from an EPUB file.
        
        Args:
            file_path: Path to the EPUB file
            config: Configuration dictionary
            
        Returns:
            Dictionary containing EPUB metadata
            
        Raises:
            Exception: If EPUB cannot be opened or metadata cannot be extracted
        """
        try:
            # If book not already loaded, load it
            if self.book is None:
                self.book = epub.read_epub(str(file_path))
            
            metadata = {
                'filename': file_path.name,
                'file_size': file_path.stat().st_size,
                'format': 'EPUB',
            }
            
            # Extract Dublin Core metadata
            dublin_core = self._extract_dublin_core_metadata()
            metadata.update(dublin_core)
            
            # Extract EPUB-specific metadata
            epub_metadata = self._extract_epub_metadata()
            metadata.update(epub_metadata)
            
            # Extract table of contents
            if config.get('include_toc', True):
                toc = self._extract_table_of_contents()
                if toc:
                    metadata['table_of_contents'] = toc
            
            # Extract document statistics
            if config.get('include_statistics', True):
                stats = self._extract_document_statistics()
                metadata.update(stats)
            
            # Extract chapter information
            if config.get('include_structure', True):
                structure = self._extract_document_structure()
                metadata.update(structure)
            
            # Remove empty values
            metadata = {k: v for k, v in metadata.items() if v is not None and v != ""}
            
            return metadata
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            raise
    
    def _extract_dublin_core_metadata(self) -> Dict[str, Any]:
        """
        Extract Dublin Core metadata from EPUB.
        
        Returns:
            Dictionary with Dublin Core metadata
        """
        metadata = {}
        
        try:
            # Title
            title = self.book.get_metadata('DC', 'title')
            if title:
                metadata['title'] = title[0][0] if title[0] else None
            
            # Creator/Author
            creator = self.book.get_metadata('DC', 'creator')
            if creator:
                metadata['author'] = creator[0][0] if creator[0] else None
            
            # Subject
            subject = self.book.get_metadata('DC', 'subject')
            if subject:
                metadata['subject'] = subject[0][0] if subject[0] else None
            
            # Description
            description = self.book.get_metadata('DC', 'description')
            if description:
                metadata['description'] = description[0][0] if description[0] else None
            
            # Publisher
            publisher = self.book.get_metadata('DC', 'publisher')
            if publisher:
                metadata['publisher'] = publisher[0][0] if publisher[0] else None
            
            # Date
            date = self.book.get_metadata('DC', 'date')
            if date:
                metadata['publication_date'] = date[0][0] if date[0] else None
            
            # Language
            language = self.book.get_metadata('DC', 'language')
            if language:
                metadata['language'] = language[0][0] if language[0] else None
            
            # Identifier
            identifier = self.book.get_metadata('DC', 'identifier')
            if identifier:
                metadata['identifier'] = identifier[0][0] if identifier[0] else None
            
            # Rights
            rights = self.book.get_metadata('DC', 'rights')
            if rights:
                metadata['rights'] = rights[0][0] if rights[0] else None
            
            # Coverage
            coverage = self.book.get_metadata('DC', 'coverage')
            if coverage:
                metadata['coverage'] = coverage[0][0] if coverage[0] else None
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Error extracting Dublin Core metadata: {e}")
        
        return metadata
    
    def _extract_epub_metadata(self) -> Dict[str, Any]:
        """
        Extract EPUB-specific metadata.
        
        Returns:
            Dictionary with EPUB metadata
        """
        metadata = {}
        
        try:
            # EPUB version
            if hasattr(self.book, 'version'):
                metadata['epub_version'] = self.book.version
            
            # Spine information (reading order)
            if hasattr(self.book, 'spine'):
                metadata['reading_order_count'] = len(self.book.spine)
            
            # Get all items count
            all_items = list(self.book.get_items())
            metadata['total_items'] = len(all_items)
            
            # Count different item types
            document_items = list(self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
            metadata['document_count'] = len(document_items)
            
            image_items = list(self.book.get_items_of_type(ebooklib.ITEM_IMAGE))
            metadata['image_count'] = len(image_items)
            
            style_items = list(self.book.get_items_of_type(ebooklib.ITEM_STYLE))
            metadata['style_count'] = len(style_items)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Error extracting EPUB metadata: {e}")
        
        return metadata
    
    def _extract_table_of_contents(self) -> Optional[List[Dict[str, Any]]]:
        """
        Extract table of contents structure.
        
        Returns:
            List of TOC entries or None
        """
        try:
            toc = []
            
            # Get navigation document (EPUB3) or NCX (EPUB2)
            nav_items = list(self.book.get_items_of_type(ebooklib.ITEM_NAVIGATION))
            
            if nav_items:
                # EPUB3 navigation document
                nav_item = nav_items[0]
                content = nav_item.get_content()
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='ignore')
                
                soup = BeautifulSoup(content, 'lxml')
                
                # Find navigation lists
                nav_lists = soup.find_all('ol')
                for nav_list in nav_lists:
                    toc.extend(self._parse_nav_list(nav_list))
            
            else:
                # Fallback: try to extract from spine order
                spine_items = []
                for item_id, _ in self.book.spine:
                    item = self.book.get_item_with_id(item_id)
                    if item:
                        title = self._get_chapter_title(item, len(spine_items) + 1)
                        spine_items.append({
                            'title': title,
                            'href': item.file_name if hasattr(item, 'file_name') else '',
                            'level': 1
                        })
                toc = spine_items
            
            return toc if toc else None
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Error extracting table of contents: {e}")
            return None
    
    def _parse_nav_list(self, nav_list, level: int = 1) -> List[Dict[str, Any]]:
        """
        Parse navigation list recursively.
        
        Args:
            nav_list: Navigation list element
            level: Current nesting level
            
        Returns:
            List of navigation entries
        """
        entries = []
        
        for li in nav_list.find_all('li', recursive=False):
            entry = {'level': level}
            
            # Find the anchor tag
            anchor = li.find('a')
            if anchor:
                entry['title'] = anchor.get_text(strip=True)
                entry['href'] = anchor.get('href', '')
            else:
                # No anchor, just text
                entry['title'] = li.get_text(strip=True).split('\n')[0]
                entry['href'] = ''
            
            entries.append(entry)
            
            # Check for nested lists
            nested_ol = li.find('ol')
            if nested_ol:
                entries.extend(self._parse_nav_list(nested_ol, level + 1))
        
        return entries
    
    def _extract_document_statistics(self) -> Dict[str, Any]:
        """
        Extract document statistics.
        
        Returns:
            Dictionary with document statistics
        """
        stats = {}
        
        try:
            # Count chapters
            document_items = list(self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
            stats['chapter_count'] = len(document_items)
            
            # Count total characters and words
            total_chars = 0
            total_words = 0
            
            for item in document_items:
                try:
                    content = item.get_content()
                    if isinstance(content, bytes):
                        content = content.decode('utf-8', errors='ignore')
                    
                    # Parse and extract text
                    soup = BeautifulSoup(content, 'lxml')
                    text = soup.get_text()
                    
                    total_chars += len(text)
                    total_words += len(text.split())
                    
                except Exception:
                    continue
            
            stats['character_count'] = total_chars
            stats['word_count'] = total_words
            
            # Estimate page count (rough calculation)
            stats['estimated_page_count'] = max(1, total_chars // 2500)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Error extracting document statistics: {e}")
        
        return stats
    
    def _extract_document_structure(self) -> Dict[str, Any]:
        """
        Extract document structure information.
        
        Returns:
            Dictionary with structure information
        """
        structure = {}
        
        try:
            # Get spine order
            spine_info = []
            for item_id, linear in self.book.spine:
                item = self.book.get_item_with_id(item_id)
                if item:
                    spine_info.append({
                        'id': item_id,
                        'href': item.file_name if hasattr(item, 'file_name') else '',
                        'linear': linear
                    })
            
            structure['spine'] = spine_info
            
            # Extract headings from all chapters
            all_headings = []
            document_items = list(self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
            
            for i, item in enumerate(document_items):
                try:
                    content = item.get_content()
                    if isinstance(content, bytes):
                        content = content.decode('utf-8', errors='ignore')
                    
                    soup = BeautifulSoup(content, 'lxml')
                    
                    # Find headings
                    for level in range(1, 7):  # h1 to h6
                        headings = soup.find_all(f'h{level}')
                        for heading in headings:
                            heading_text = heading.get_text(strip=True)
                            if heading_text:
                                all_headings.append({
                                    'level': level,
                                    'text': heading_text,
                                    'chapter': i + 1
                                })
                
                except Exception:
                    continue
            
            if all_headings:
                structure['headings'] = all_headings
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Error extracting document structure: {e}")
        
        return structure
    
    @property
    def supported_extensions(self) -> list[str]:
        """
        List of file extensions this extractor supports.
        
        Returns:
            List containing '.epub'
        """
        return ['.epub']
    
    @property
    def extractor_name(self) -> str:
        """
        Human-readable name of this extractor.
        
        Returns:
            Name of the EPUB extractor
        """
        return "EPUB Extractor (ebooklib)"