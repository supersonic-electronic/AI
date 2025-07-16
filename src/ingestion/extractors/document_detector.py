"""
Automatic document type detection and extractor selection.
"""

import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .base import BaseExtractor
from .pdf import PDFExtractor
from .html import HTMLExtractor
from .docx import DOCXExtractor
from .xml import XMLExtractor
from .latex import LaTeXExtractor


class DocumentDetector:
    """
    Automatic document type detector and extractor selector.
    
    Determines the best extractor for a given file based on extension,
    MIME type, and content analysis.
    """
    
    def __init__(self):
        """Initialize the document detector with available extractors."""
        self.extractors = [
            PDFExtractor(),
            HTMLExtractor(),
            DOCXExtractor(),
            XMLExtractor(),
            LaTeXExtractor(),
        ]
        
        # Build extension to extractor mapping
        self.extension_map = {}
        for extractor in self.extractors:
            for ext in extractor.supported_extensions:
                if ext not in self.extension_map:
                    self.extension_map[ext] = []
                self.extension_map[ext].append(extractor)
        
        # Initialize mimetypes
        mimetypes.init()
    
    def detect_document_type(self, file_path: Path, config: Dict[str, Any] = None) -> Optional[BaseExtractor]:
        """
        Detect the document type and return the appropriate extractor.
        
        Args:
            file_path: Path to the file to analyze
            config: Configuration dictionary
            
        Returns:
            Best extractor for the file, or None if no suitable extractor found
        """
        if config is None:
            config = {}
        
        # Method 1: Extension-based detection
        extractor = self._detect_by_extension(file_path)
        if extractor and config.get('trust_extensions', True):
            return extractor
        
        # Method 2: MIME type detection
        if config.get('use_mime_detection', True):
            mime_extractor = self._detect_by_mime_type(file_path)
            if mime_extractor:
                return mime_extractor
        
        # Method 3: Content-based detection
        if config.get('use_content_detection', True):
            content_extractor = self._detect_by_content(file_path, config)
            if content_extractor:
                return content_extractor
        
        # Fallback to extension-based if enabled
        if not config.get('trust_extensions', True) and extractor:
            return extractor
        
        return None
    
    def _detect_by_extension(self, file_path: Path) -> Optional[BaseExtractor]:
        """
        Detect document type based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extractor based on file extension, or None
        """
        extension = file_path.suffix.lower()
        
        if extension in self.extension_map:
            # Return the first (primary) extractor for this extension
            return self.extension_map[extension][0]
        
        return None
    
    def _detect_by_mime_type(self, file_path: Path) -> Optional[BaseExtractor]:
        """
        Detect document type based on MIME type.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extractor based on MIME type, or None
        """
        try:
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            if not mime_type:
                return None
            
            # Map MIME types to extractors
            mime_map = {
                'application/pdf': PDFExtractor,
                'text/html': HTMLExtractor,
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': DOCXExtractor,
                'application/xml': XMLExtractor,
                'text/xml': XMLExtractor,
                'text/x-tex': LaTeXExtractor,
                'application/x-tex': LaTeXExtractor,
            }
            
            extractor_class = mime_map.get(mime_type)
            if extractor_class:
                return extractor_class()
        
        except Exception:
            # MIME detection failed, continue with other methods
            pass
        
        return None
    
    def _detect_by_content(self, file_path: Path, config: Dict[str, Any]) -> Optional[BaseExtractor]:
        """
        Detect document type based on file content analysis.
        
        Args:
            file_path: Path to the file
            config: Configuration dictionary
            
        Returns:
            Extractor based on content analysis, or None
        """
        try:
            # Read a sample of the file for analysis
            sample_size = config.get('content_detection_sample_size', 8192)
            
            # Try binary read first
            try:
                with open(file_path, 'rb') as f:
                    binary_sample = f.read(sample_size)
                
                # Check for binary signatures
                if binary_sample.startswith(b'%PDF'):
                    return PDFExtractor()
                
                if binary_sample.startswith(b'PK\x03\x04'):
                    # ZIP-based format (could be DOCX)
                    if b'word/' in binary_sample or b'document.xml' in binary_sample:
                        return DOCXExtractor()
            
            except Exception:
                pass
            
            # Try text-based analysis
            try:
                # Try UTF-8 first, then fallback encodings
                encodings = ['utf-8', 'latin-1', 'cp1252']
                text_sample = None
                
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            text_sample = f.read(sample_size)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if text_sample:
                    return self._analyze_text_content(text_sample, config)
            
            except Exception:
                pass
        
        except Exception:
            # Content detection failed
            pass
        
        return None
    
    def _analyze_text_content(self, content: str, config: Dict[str, Any]) -> Optional[BaseExtractor]:
        """
        Analyze text content to determine document type.
        
        Args:
            content: Text content sample
            config: Configuration dictionary
            
        Returns:
            Extractor based on content analysis, or None
        """
        content_lower = content.lower().strip()
        
        # HTML detection
        html_indicators = [
            '<!doctype html', '<html', '<head>', '<body>', '<div', '<p>',
            '<script', '<style', '<meta', '<link'
        ]
        
        html_score = sum(1 for indicator in html_indicators if indicator in content_lower)
        
        # XML detection
        xml_indicators = [
            '<?xml', '<root', 'xmlns:', 'xsi:', '<config', '<data'
        ]
        
        xml_score = sum(1 for indicator in xml_indicators if indicator in content_lower)
        
        # LaTeX detection
        latex_indicators = [
            '\\documentclass', '\\begin{document}', '\\usepackage', '\\section',
            '\\chapter', '\\title', '\\author', '\\maketitle'
        ]
        
        latex_score = sum(1 for indicator in latex_indicators if indicator in content_lower)
        
        # Determine best match based on scores
        scores = {
            'html': html_score,
            'xml': xml_score,
            'latex': latex_score,
        }
        
        # Require minimum confidence
        min_confidence = config.get('content_detection_min_confidence', 2)
        max_score = max(scores.values())
        
        if max_score >= min_confidence:
            best_type = max(scores, key=scores.get)
            
            if best_type == 'html':
                return HTMLExtractor()
            elif best_type == 'xml':
                return XMLExtractor()
            elif best_type == 'latex':
                return LaTeXExtractor()
        
        return None
    
    def get_available_extractors(self) -> List[BaseExtractor]:
        """
        Get list of all available extractors.
        
        Returns:
            List of all registered extractors
        """
        return self.extractors.copy()
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of all supported file extensions.
        
        Returns:
            List of supported file extensions
        """
        extensions = set()
        for extractor in self.extractors:
            extensions.update(extractor.supported_extensions)
        return sorted(list(extensions))
    
    def get_extractor_for_extension(self, extension: str) -> List[BaseExtractor]:
        """
        Get extractors that support a specific extension.
        
        Args:
            extension: File extension (with or without dot)
            
        Returns:
            List of extractors that support the extension
        """
        if not extension.startswith('.'):
            extension = '.' + extension
        
        return self.extension_map.get(extension.lower(), [])
    
    def register_extractor(self, extractor: BaseExtractor) -> None:
        """
        Register a new extractor.
        
        Args:
            extractor: Extractor instance to register
        """
        if extractor not in self.extractors:
            self.extractors.append(extractor)
            
            # Update extension mapping
            for ext in extractor.supported_extensions:
                if ext not in self.extension_map:
                    self.extension_map[ext] = []
                if extractor not in self.extension_map[ext]:
                    self.extension_map[ext].append(extractor)
    
    def get_detection_info(self, file_path: Path, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get detailed information about document type detection.
        
        Args:
            file_path: Path to the file
            config: Configuration dictionary
            
        Returns:
            Dictionary with detection information and confidence scores
        """
        if config is None:
            config = {}
        
        info = {
            'file_path': str(file_path),
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            'extension': file_path.suffix.lower(),
            'detection_methods': {},
            'selected_extractor': None,
            'confidence': 0.0,
        }
        
        # Extension-based detection
        ext_extractor = self._detect_by_extension(file_path)
        info['detection_methods']['extension'] = {
            'extractor': ext_extractor.extractor_name if ext_extractor else None,
            'confidence': 0.8 if ext_extractor else 0.0,
        }
        
        # MIME type detection
        mime_extractor = self._detect_by_mime_type(file_path)
        info['detection_methods']['mime_type'] = {
            'extractor': mime_extractor.extractor_name if mime_extractor else None,
            'confidence': 0.7 if mime_extractor else 0.0,
        }
        
        # Content-based detection
        content_extractor = None
        content_confidence = 0.0
        
        if file_path.exists():
            try:
                content_extractor = self._detect_by_content(file_path, config)
                content_confidence = 0.9 if content_extractor else 0.0
            except Exception:
                pass
        
        info['detection_methods']['content'] = {
            'extractor': content_extractor.extractor_name if content_extractor else None,
            'confidence': content_confidence,
        }
        
        # Select best extractor
        selected = self.detect_document_type(file_path, config)
        if selected:
            info['selected_extractor'] = selected.extractor_name
            
            # Calculate overall confidence
            method_confidences = [
                method['confidence'] for method in info['detection_methods'].values()
                if method['extractor'] == selected.extractor_name
            ]
            
            if method_confidences:
                info['confidence'] = max(method_confidences)
        
        return info