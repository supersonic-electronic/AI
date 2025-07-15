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
        self._load_built_in_extractors()
        self._load_plugin_extractors()
    
    def _load_built_in_extractors(self) -> None:
        """Load built-in extractors."""
        try:
            from .extractors.pdf import PDFExtractor
            self.extractors.append(PDFExtractor())
            self.logger.info("Loaded built-in PDF extractor")
        except ImportError as e:
            self.logger.warning(f"Could not load PDF extractor: {e}")
    
    def _load_plugin_extractors(self) -> None:
        """Load plugin extractors via entry points using importlib.metadata."""
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
            
            # Load each plugin
            plugins_loaded = 0
            for entry_point in eps:
                try:
                    # Load the plugin class
                    plugin_class = entry_point.load()
                    
                    # Verify it's a valid extractor
                    if isinstance(plugin_class, type) and issubclass(plugin_class, BaseExtractor):
                        # Instantiate the extractor
                        extractor = plugin_class()
                        self.extractors.append(extractor)
                        plugins_loaded += 1
                        self.logger.info(f"Loaded plugin extractor: {extractor.extractor_name} from {entry_point.name}")
                    else:
                        self.logger.warning(f"Plugin {entry_point.name} is not a valid BaseExtractor subclass")
                        
                except Exception as e:
                    self.logger.error(f"Failed to load plugin extractor {entry_point.name}: {e}")
            
            if plugins_loaded > 0:
                self.logger.info(f"Successfully loaded {plugins_loaded} plugin extractors")
            else:
                self.logger.debug("No plugin extractors found or loaded")
                    
        except Exception as e:
            self.logger.debug(f"Plugin loading failed, continuing with built-in extractors only: {e}")
    
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