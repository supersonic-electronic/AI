"""
XML extractor using lxml.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from lxml import etree, html

from .base import BaseExtractor


class XMLExtractor(BaseExtractor):
    """
    XML document extractor using lxml.
    
    Extracts text and metadata from XML files with configurable options
    for namespace handling, element filtering, and structure preservation.
    """
    
    def __init__(self):
        """Initialize the XML extractor."""
        self.tree = None
        self.root = None
        self.namespaces = {}
    
    def can_handle(self, file_path: Path) -> bool:
        """
        Check if this extractor can handle XML files.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file has .xml extension, False otherwise
        """
        return file_path.suffix.lower() == '.xml'
    
    def extract_text(self, file_path: Path, config: Dict[str, Any]) -> str:
        """
        Extract text from an XML file using lxml.
        
        Args:
            file_path: Path to the XML file
            config: Configuration dictionary
            
        Returns:
            Extracted text content
            
        Raises:
            Exception: If XML cannot be opened or processed
        """
        try:
            # Parse XML file
            self._parse_xml(file_path, config)
            
            # Extract text based on configuration
            extraction_mode = config.get('xml_extraction_mode', 'all_text')
            
            if extraction_mode == 'xpath':
                text = self._extract_by_xpath(config)
            elif extraction_mode == 'elements':
                text = self._extract_by_elements(config)
            elif extraction_mode == 'structured':
                text = self._extract_structured(config)
            else:  # 'all_text'
                text = self._extract_all_text(config)
            
            # Clean and normalize text
            text = self._clean_text(text, config)
            
            return text
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise
    
    def _parse_xml(self, file_path: Path, config: Dict[str, Any]) -> None:
        """
        Parse XML file and handle encoding.
        
        Args:
            file_path: Path to the XML file
            config: Configuration dictionary
        """
        # Try to parse with different approaches
        parser_options = {
            'recover': config.get('xml_recover', True),
            'strip_cdata': config.get('xml_strip_cdata', False),
            'resolve_entities': config.get('xml_resolve_entities', False),
        }
        
        parser = etree.XMLParser(**parser_options)
        
        try:
            # First try with UTF-8
            with open(file_path, 'rb') as f:
                self.tree = etree.parse(f, parser)
        except (etree.XMLSyntaxError, UnicodeDecodeError):
            # Try with different encoding
            encoding = config.get('xml_encoding', 'latin-1')
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                self.tree = etree.fromstring(content.encode('utf-8'), parser)
            except:
                # Last resort: try as HTML (more forgiving)
                if config.get('fallback_to_html', True):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    self.tree = html.fromstring(content)
                else:
                    raise
        
        if hasattr(self.tree, 'getroot'):
            self.root = self.tree.getroot()
        else:
            self.root = self.tree
        
        # Extract namespaces
        self.namespaces = self._extract_namespaces()
    
    def _extract_namespaces(self) -> Dict[str, str]:
        """
        Extract namespace mappings from the XML document.
        
        Returns:
            Dictionary of namespace prefix to URI mappings
        """
        namespaces = {}
        
        try:
            # Get namespaces from root element
            if hasattr(self.root, 'nsmap') and self.root.nsmap:
                namespaces = {k if k else 'default': v for k, v in self.root.nsmap.items()}
            
            # Add common namespaces if not present
            common_ns = {
                'xml': 'http://www.w3.org/XML/1998/namespace',
                'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            }
            
            for prefix, uri in common_ns.items():
                if prefix not in namespaces:
                    namespaces[prefix] = uri
        
        except Exception:
            # Fallback to empty namespaces
            pass
        
        return namespaces
    
    def _extract_all_text(self, config: Dict[str, Any]) -> str:
        """
        Extract all text content from the XML document.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            All text content
        """
        # Get all text content
        if hasattr(self.root, 'itertext'):
            texts = list(self.root.itertext())
        else:
            texts = [self.root.text or '']
        
        # Filter and clean texts
        preserve_structure = config.get('preserve_xml_structure', True)
        
        if preserve_structure:
            # Add element structure information
            structured_texts = []
            for element in self.root.iter():
                if element.text and element.text.strip():
                    tag_name = element.tag
                    # Remove namespace prefix for readability
                    if '}' in tag_name:
                        tag_name = tag_name.split('}')[1]
                    
                    if config.get('include_element_names', True):
                        structured_texts.append(f"[{tag_name}] {element.text.strip()}")
                    else:
                        structured_texts.append(element.text.strip())
            
            return '\n'.join(structured_texts)
        else:
            # Simple text concatenation
            return ' '.join(text.strip() for text in texts if text.strip())
    
    def _extract_by_xpath(self, config: Dict[str, Any]) -> str:
        """
        Extract text using XPath expressions.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Text extracted using XPath
        """
        xpath_expressions = config.get('xpath_expressions', ['//text()'])
        texts = []
        
        for xpath in xpath_expressions:
            try:
                results = self.root.xpath(xpath, namespaces=self.namespaces)
                for result in results:
                    if isinstance(result, str):
                        texts.append(result.strip())
                    elif hasattr(result, 'text') and result.text:
                        texts.append(result.text.strip())
                    elif hasattr(result, 'itertext'):
                        texts.extend(text.strip() for text in result.itertext() if text.strip())
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"XPath expression '{xpath}' failed: {e}")
        
        return '\n'.join(filter(None, texts))
    
    def _extract_by_elements(self, config: Dict[str, Any]) -> str:
        """
        Extract text from specific XML elements.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Text from specified elements
        """
        target_elements = config.get('target_elements', [])
        if not target_elements:
            return self._extract_all_text(config)
        
        texts = []
        include_attributes = config.get('include_attributes', False)
        
        for element_name in target_elements:
            # Handle namespaced elements
            xpath = f".//{element_name}"
            if ':' in element_name and self.namespaces:
                # Use namespace-aware search
                try:
                    elements = self.root.xpath(xpath, namespaces=self.namespaces)
                except:
                    # Fallback to simple search
                    elements = self.root.iter(element_name)
            else:
                # Simple element search
                elements = self.root.iter(element_name)
            
            for element in elements:
                element_texts = []
                
                # Extract text content
                if element.text and element.text.strip():
                    element_texts.append(element.text.strip())
                
                # Extract from child elements
                for child_text in element.itertext():
                    if child_text.strip() and child_text.strip() not in element_texts:
                        element_texts.append(child_text.strip())
                
                # Include attributes if requested
                if include_attributes and element.attrib:
                    attr_texts = [f"{k}={v}" for k, v in element.attrib.items()]
                    element_texts.extend(attr_texts)
                
                if element_texts:
                    texts.append(' '.join(element_texts))
        
        return '\n'.join(texts)
    
    def _extract_structured(self, config: Dict[str, Any]) -> str:
        """
        Extract text with XML structure preserved.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Structured text representation
        """
        lines = []
        max_depth = config.get('max_structure_depth', 10)
        include_empty_elements = config.get('include_empty_elements', False)
        
        def process_element(element, depth=0):
            if depth > max_depth:
                return
            
            indent = '  ' * depth
            tag_name = element.tag
            
            # Remove namespace prefix for readability
            if '}' in tag_name:
                tag_name = tag_name.split('}')[1]
            
            # Element with text content
            if element.text and element.text.strip():
                lines.append(f"{indent}{tag_name}: {element.text.strip()}")
            elif include_empty_elements:
                lines.append(f"{indent}{tag_name}:")
            
            # Process attributes
            if element.attrib and config.get('include_attributes_in_structure', True):
                for key, value in element.attrib.items():
                    lines.append(f"{indent}  @{key}: {value}")
            
            # Process children
            for child in element:
                process_element(child, depth + 1)
        
        process_element(self.root)
        return '\n'.join(lines)
    
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
        Extract metadata from an XML file.
        
        Args:
            file_path: Path to the XML file
            config: Configuration dictionary
            
        Returns:
            Dictionary containing XML metadata
            
        Raises:
            Exception: If XML cannot be opened or metadata cannot be extracted
        """
        try:
            # If not already parsed, parse the XML
            if self.root is None:
                self._parse_xml(file_path, config)
            
            metadata = {
                'filename': file_path.name,
                'file_size': file_path.stat().st_size,
            }
            
            # Extract root element information
            root_tag = self.root.tag
            if '}' in root_tag:
                namespace, local_name = root_tag.split('}')
                metadata['root_element'] = local_name
                metadata['root_namespace'] = namespace.lstrip('{')
            else:
                metadata['root_element'] = root_tag
            
            # Extract namespaces
            if self.namespaces:
                metadata['namespaces'] = self.namespaces
            
            # Extract XML declaration info
            if hasattr(self.tree, 'docinfo'):
                docinfo = self.tree.docinfo
                if docinfo.encoding:
                    metadata['encoding'] = docinfo.encoding
                if docinfo.xml_version:
                    metadata['xml_version'] = docinfo.xml_version
                if docinfo.standalone is not None:
                    metadata['standalone'] = docinfo.standalone
            
            # Extract document structure
            if config.get('include_structure_metadata', True):
                structure = self._extract_structure_metadata()
                metadata.update(structure)
            
            # Extract specific metadata elements
            if config.get('extract_metadata_elements', True):
                element_metadata = self._extract_metadata_elements(config)
                metadata.update(element_metadata)
            
            # Remove empty values
            metadata = {k: v for k, v in metadata.items() if v}
            
            return metadata
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            raise
    
    def _extract_structure_metadata(self) -> Dict[str, Any]:
        """
        Extract document structure information.
        
        Returns:
            Dictionary with structure information
        """
        structure = {}
        
        # Count elements
        element_counts = {}
        max_depth = 0
        
        def analyze_element(element, depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, depth)
            
            tag = element.tag
            if '}' in tag:
                tag = tag.split('}')[1]
            
            element_counts[tag] = element_counts.get(tag, 0) + 1
            
            for child in element:
                analyze_element(child, depth + 1)
        
        analyze_element(self.root)
        
        structure['element_counts'] = element_counts
        structure['max_depth'] = max_depth
        structure['total_elements'] = sum(element_counts.values())
        
        return structure
    
    def _extract_metadata_elements(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract specific metadata from known XML elements.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {}
        
        # Common metadata element patterns
        metadata_patterns = config.get('metadata_elements', {
            'title': ['title', 'dc:title', 'name'],
            'author': ['author', 'creator', 'dc:creator'],
            'description': ['description', 'abstract', 'dc:description'],
            'date': ['date', 'created', 'dc:date'],
            'subject': ['subject', 'topic', 'dc:subject'],
            'identifier': ['id', 'identifier', 'dc:identifier'],
        })
        
        for metadata_key, element_names in metadata_patterns.items():
            for element_name in element_names:
                try:
                    # Try different search methods
                    elements = []
                    
                    # Direct search
                    elements.extend(self.root.iter(element_name))
                    
                    # Namespace-aware search if applicable
                    if ':' in element_name and self.namespaces:
                        xpath = f".//{element_name}"
                        try:
                            elements.extend(self.root.xpath(xpath, namespaces=self.namespaces))
                        except:
                            pass
                    
                    # Extract text from found elements
                    values = []
                    for element in elements:
                        if element.text and element.text.strip():
                            values.append(element.text.strip())
                    
                    if values:
                        if len(values) == 1:
                            metadata[metadata_key] = values[0]
                        else:
                            metadata[metadata_key] = values
                        break  # Use first successful pattern
                
                except Exception:
                    continue
        
        return metadata
    
    @property
    def supported_extensions(self) -> list[str]:
        """
        List of file extensions this extractor supports.
        
        Returns:
            List containing '.xml'
        """
        return ['.xml']
    
    @property
    def extractor_name(self) -> str:
        """
        Human-readable name of this extractor.
        
        Returns:
            Name of the XML extractor
        """
        return "XML Extractor (lxml)"