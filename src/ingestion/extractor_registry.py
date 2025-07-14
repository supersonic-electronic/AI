"""
Registry for document extractors with plugin support.
"""

import importlib
from pathlib import Path
from typing import Dict, List, Optional

from .extractors.base import BaseExtractor


class ExtractorRegistry:
    """
    Registry for managing document extractors.
    
    Supports both built-in extractors and plugin discovery via entry points.
    """
    
    def __init__(self):
        """Initialize the extractor registry."""
        self.extractors: List[BaseExtractor] = []
        self._load_built_in_extractors()
        self._load_plugin_extractors()
    
    def _load_built_in_extractors(self):
        """Load built-in extractors."""
        try:
            from .extractors.pdf import PDFExtractor
            self.extractors.append(PDFExtractor())
        except ImportError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not load PDF extractor: {e}")
    
    def _load_plugin_extractors(self):
        """Load plugin extractors via entry points."""
        try:
            import pkg_resources
            
            for entry_point in pkg_resources.iter_entry_points('ingestion.extractors'):
                try:
                    extractor_class = entry_point.load()
                    extractor = extractor_class()
                    if isinstance(extractor, BaseExtractor):
                        self.extractors.append(extractor)
                        
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"Loaded plugin extractor: {extractor.extractor_name}")
                    else:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Plugin {entry_point.name} does not inherit from BaseExtractor")
                        
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to load plugin extractor {entry_point.name}: {e}")
                    
        except ImportError:
            # pkg_resources not available, skip plugin loading
            pass
    
    def get_extractor(self, file_path: Path) -> Optional[BaseExtractor]:
        """
        Get the appropriate extractor for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extractor instance if one can handle the file, None otherwise
        """
        for extractor in self.extractors:
            if extractor.can_handle(file_path):
                return extractor
        return None
    
    def get_supported_extensions(self) -> Dict[str, str]:
        """
        Get all supported file extensions and their extractor names.
        
        Returns:
            Dictionary mapping extensions to extractor names
        """
        extensions = {}
        for extractor in self.extractors:
            for ext in extractor.supported_extensions:
                extensions[ext] = extractor.extractor_name
        return extensions
    
    def list_extractors(self) -> List[BaseExtractor]:
        """
        Get list of all registered extractors.
        
        Returns:
            List of extractor instances
        """
        return self.extractors.copy()


# Global registry instance
_registry = None


def get_registry() -> ExtractorRegistry:
    """
    Get the global extractor registry.
    
    Returns:
        ExtractorRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ExtractorRegistry()
    return _registry