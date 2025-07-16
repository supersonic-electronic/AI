"""
Registry for document extractors with plugin support.

This module provides a registry system for discovering and managing document extractors,
including both built-in extractors and plugins discovered via entry points.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Type

from .extractors.base import BaseExtractor


class ExtractorRegistry:
    """
    Registry for managing document extractors.
    
    Supports both built-in extractors and plugin discovery via entry points.
    """
    
    def __init__(self):
        """Initialize the extractor registry."""
        self.extractors: List[BaseExtractor] = []
        self.logger = logging.getLogger(__name__)
        self._load_extractors_from_entry_points()
    
    def _load_extractors_from_entry_points(self) -> None:
        """Load all extractors (both built-in and plugins) via entry points using importlib.metadata."""
        try:
            # Try modern importlib.metadata first (Python 3.8+)
            try:
                from importlib.metadata import entry_points
                
                # Get entry points for our plugin group
                eps = entry_points(group='project.plugins')
                
            except ImportError:
                # Fallback to importlib_metadata for older Python versions
                try:
                    from importlib_metadata import entry_points
                    eps = entry_points(group='project.plugins')
                except ImportError:
                    # Final fallback to pkg_resources
                    import pkg_resources
                    eps = pkg_resources.iter_entry_points('project.plugins')
            
            # Load each extractor
            extractors_loaded = 0
            for entry_point in eps:
                try:
                    # Load the extractor class
                    extractor_class = entry_point.load()
                    
                    # Verify it's a valid extractor
                    if isinstance(extractor_class, type) and issubclass(extractor_class, BaseExtractor):
                        # Instantiate the extractor
                        extractor = extractor_class()
                        self.extractors.append(extractor)
                        extractors_loaded += 1
                        
                        # Determine if it's built-in or plugin
                        extractor_type = "built-in" if entry_point.value.startswith("src.") else "plugin"
                        self.logger.info(f"Loaded {extractor_type} extractor: {extractor.extractor_name} from {entry_point.name}")
                    else:
                        self.logger.warning(f"Entry point {entry_point.name} is not a valid BaseExtractor subclass")
                        
                except Exception as e:
                    self.logger.error(f"Failed to load extractor {entry_point.name}: {e}")
            
            if extractors_loaded > 0:
                self.logger.info(f"Successfully loaded {extractors_loaded} extractors total")
            else:
                self.logger.warning("No extractors found or loaded - falling back to manual loading")
                self._fallback_load_built_in_extractors()
                    
        except Exception as e:
            self.logger.warning(f"Entry point loading failed, falling back to manual loading: {e}")
            self._fallback_load_built_in_extractors()
    
    def _fallback_load_built_in_extractors(self) -> None:
        """Fallback method to manually load built-in extractors if entry points fail."""
        fallback_extractors = [
            ('PDF', 'src.ingestion.extractors.pdf', 'PDFExtractor'),
            ('HTML', 'src.ingestion.extractors.html', 'HTMLExtractor'),
            ('DOCX', 'src.ingestion.extractors.docx', 'DOCXExtractor'),
            ('XML', 'src.ingestion.extractors.xml', 'XMLExtractor'),
            ('LaTeX', 'src.ingestion.extractors.latex', 'LaTeXExtractor'),
        ]
        
        loaded_count = 0
        for name, module_path, class_name in fallback_extractors:
            try:
                # Dynamically import the module and class
                module = __import__(module_path, fromlist=[class_name])
                extractor_class = getattr(module, class_name)
                
                # Instantiate and register
                extractor = extractor_class()
                self.extractors.append(extractor)
                loaded_count += 1
                self.logger.info(f"Loaded built-in {name} extractor via fallback")
                
            except (ImportError, AttributeError) as e:
                self.logger.warning(f"Could not load {name} extractor via fallback: {e}")
        
        if loaded_count > 0:
            self.logger.info(f"Fallback loading completed: {loaded_count} extractors loaded")
        else:
            self.logger.error("No extractors could be loaded, even with fallback method")
    
    def register_extractor(self, extractor: BaseExtractor) -> None:
        """
        Manually register an extractor instance.
        
        Args:
            extractor: Extractor instance to register
        """
        if not isinstance(extractor, BaseExtractor):
            raise TypeError("Extractor must inherit from BaseExtractor")
        
        # Check if already registered
        for existing in self.extractors:
            if existing.extractor_name == extractor.extractor_name:
                self.logger.warning(f"Extractor {extractor.extractor_name} is already registered, skipping")
                return
        
        self.extractors.append(extractor)
        self.logger.info(f"Manually registered extractor: {extractor.extractor_name}")
    
    def unregister_extractor(self, extractor_name: str) -> bool:
        """
        Unregister an extractor by name.
        
        Args:
            extractor_name: Name of the extractor to remove
            
        Returns:
            True if extractor was found and removed, False otherwise
        """
        for i, extractor in enumerate(self.extractors):
            if extractor.extractor_name == extractor_name:
                removed = self.extractors.pop(i)
                self.logger.info(f"Unregistered extractor: {removed.extractor_name}")
                return True
        
        self.logger.warning(f"Extractor {extractor_name} not found for removal")
        return False
    
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