"""
Base extractor class for document processing.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict


class BaseExtractor(ABC):
    """
    Abstract base class for document extractors.
    
    All extractors must implement methods to check if they can handle
    a file type and extract text and metadata from supported files.
    """
    
    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """
        Check if this extractor can handle the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if this extractor can process the file, False otherwise
        """
        pass
    
    @abstractmethod
    def extract_text(self, file_path: Path, config: Dict[str, Any]) -> str:
        """
        Extract text content from the file.
        
        Args:
            file_path: Path to the file to process
            config: Configuration dictionary
            
        Returns:
            Extracted text content
            
        Raises:
            Exception: If extraction fails
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from the file.
        
        Args:
            file_path: Path to the file to process
            config: Configuration dictionary
            
        Returns:
            Dictionary containing extracted metadata
            
        Raises:
            Exception: If metadata extraction fails
        """
        pass
    
    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """
        List of file extensions this extractor supports.
        
        Returns:
            List of file extensions (including the dot, e.g., ['.pdf', '.txt'])
        """
        pass
    
    @property
    @abstractmethod
    def extractor_name(self) -> str:
        """
        Human-readable name of this extractor.
        
        Returns:
            Name of the extractor
        """
        pass