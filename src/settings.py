"""
Centralized configuration management using Pydantic Settings.

This module provides a typed configuration system that reads from YAML files
and environment variables, with automatic validation and type conversion.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml
from pydantic import BaseSettings, Field, validator, root_validator


class Settings(BaseSettings):
    """
    Application settings with automatic YAML and environment variable loading.
    
    Settings are loaded in the following priority order:
    1. Environment variables (highest priority)
    2. YAML configuration file
    3. Default values (lowest priority)
    """
    
    # Directory Paths
    input_dir: Path = Field(default=Path("./data/papers"), description="Directory containing PDF files to process")
    text_dir: Path = Field(default=Path("./data/text"), description="Directory for extracted text files (.txt)")
    meta_dir: Path = Field(default=Path("./data/metadata"), description="Directory for metadata JSON files")
    math_dir: Path = Field(default=Path("./data/math"), description="Directory for mathematical formula files")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR")
    log_to_file: bool = Field(default=True, description="Whether to log to file in addition to console")
    log_file: Path = Field(default=Path("./logs/pdf_ingestion.log"), description="Log file path")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    
    # DOI Extraction
    doi_regex: str = Field(
        default=r"10\.[0-9]{4,}[-._;()/:a-zA-Z0-9]*",
        description="Regex pattern for DOI extraction"
    )
    doi_prefixes: List[str] = Field(
        default=["doi:", "DOI:", "https://doi.org/", "http://dx.doi.org/"],
        description="DOI prefixes to search for"
    )
    
    # Processing Options
    parallel_workers: int = Field(default=4, description="Number of parallel workers for PDF processing")
    skip_existing: bool = Field(default=False, description="Skip files that already have output")
    show_progress: bool = Field(default=True, description="Show progress bar during processing")
    
    # PyMuPDF Text Extraction Options
    preserve_reading_order: bool = Field(default=True, description="Use sort=True in get_text() for reading order")
    warn_empty_pages: bool = Field(default=True, description="Log warnings for empty pages")
    include_images: bool = Field(default=False, description="Extract image information")
    pdf_chunk_size: int = Field(default=0, description="Pages per chunk for large PDFs (0 = no chunking)")
    
    # Mathematical Formula Extraction
    extract_math: bool = Field(default=True, description="Enable mathematical formula extraction")
    math_ocr_fallback: bool = Field(default=False, description="Use OCR fallback for complex formulas")
    separate_math_files: bool = Field(default=True, description="Save mathematical blocks to separate files")
    math_detection_threshold: int = Field(default=3, description="Minimum score for mathematical content detection")
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    mathpix_app_id: Optional[str] = Field(default=None, description="Mathpix application ID")
    mathpix_app_key: Optional[str] = Field(default=None, description="Mathpix application key")
    pinecone_api_key: Optional[str] = Field(default=None, description="Pinecone API key")
    
    # Mathpix SDK Configuration
    mathpix_timeout: float = Field(default=30.0, description="Mathpix API timeout in seconds")
    mathpix_max_retries: int = Field(default=3, description="Maximum retry attempts for Mathpix API")
    mathpix_retry_delay: float = Field(default=1.0, description="Delay between Mathpix API retries")
    
    # Document Chunking and Embedding
    chunk_size: int = Field(default=500, description="Target size for text chunks (characters)")
    chunk_overlap: int = Field(default=50, description="Overlap between adjacent chunks (characters)")
    embedding_model: str = Field(default="text-embedding-3-small", description="OpenAI embedding model")
    embedding_batch_size: int = Field(default=30, description="Number of texts to embed per batch")
    max_retries: int = Field(default=3, description="Maximum retry attempts for API requests")
    retry_delay: float = Field(default=1.0, description="Base delay between retries (seconds)")
    
    # Vector Store Configuration - Pinecone
    pinecone_index_name: str = Field(default="document-embeddings", description="Pinecone index name")
    pinecone_environment: str = Field(default="us-east-1-aws", description="Pinecone environment")
    
    # Vector Store Configuration - Chroma
    chroma_persist_directory: Path = Field(
        default=Path("./data/chroma_db"),
        description="Local Chroma database directory"
    )
    chroma_collection_name: str = Field(
        default="document_embeddings",
        description="Chroma collection name"
    )
    
    # File Handling
    encoding: str = Field(default="utf-8", description="Text file encoding")
    json_indent: int = Field(default=2, description="JSON file indentation for readability")
    overwrite_existing: bool = Field(default=True, description="Overwrite existing output files")
    
    # Performance Settings
    openai_timeout: float = Field(default=60.0, description="OpenAI API timeout in seconds")
    concurrent_requests: int = Field(default=5, description="Maximum concurrent API requests")
    
    # Plugin Configuration
    plugin_search_paths: List[str] = Field(
        default_factory=lambda: ["plugins", "src.plugins"],
        description="Additional paths to search for plugins"
    )
    enable_plugins: bool = Field(default=True, description="Enable plugin system")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Allow environment variables to override YAML values
        # Format: PORTFOLIO_OPTIMIZER_<FIELD_NAME>
        env_prefix = "PORTFOLIO_OPTIMIZER_"
        
        # Custom JSON encoders for Path objects
        json_encoders = {
            Path: str
        }
        
        # Allow arbitrary types for complex validation
        arbitrary_types_allowed = True
    
    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard logging levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of: {valid_levels}")
        return v.upper()
    
    @validator("parallel_workers")
    def validate_parallel_workers(cls, v: int) -> int:
        """Validate parallel workers count is reasonable."""
        if v < 1:
            raise ValueError("parallel_workers must be at least 1")
        if v > 32:
            raise ValueError("parallel_workers should not exceed 32")
        return v
    
    @validator("chunk_size")
    def validate_chunk_size(cls, v: int) -> int:
        """Validate chunk size is reasonable."""
        if v < 50:
            raise ValueError("chunk_size must be at least 50 characters")
        if v > 10000:
            raise ValueError("chunk_size should not exceed 10000 characters")
        return v
    
    @validator("chunk_overlap")
    def validate_chunk_overlap(cls, v: int, values: Dict) -> int:
        """Validate chunk overlap is reasonable relative to chunk size."""
        if v < 0:
            raise ValueError("chunk_overlap must be non-negative")
        
        chunk_size = values.get("chunk_size", 500)
        if v >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        
        return v
    
    @validator("*", pre=True)
    def convert_paths(cls, v: Union[str, Path], field) -> Union[str, Path, int, bool, float, List]:
        """Convert string paths to Path objects for path fields."""
        if field.name.endswith(("_dir", "_file", "persist_directory")) and isinstance(v, str):
            return Path(v)
        return v
    
    @validator("concurrent_requests")
    def validate_concurrent_requests(cls, v: int) -> int:
        """Validate concurrent requests is reasonable."""
        if v < 1:
            raise ValueError("concurrent_requests must be at least 1")
        if v > 20:
            raise ValueError("concurrent_requests should not exceed 20")
        return v
    
    @root_validator
    def validate_mathpix_config(cls, values: Dict) -> Dict:
        """Validate Mathpix configuration consistency."""
        if values.get("math_ocr_fallback", False):
            if not values.get("mathpix_app_id") or not values.get("mathpix_app_key"):
                if not values.get("openai_api_key"):
                    raise ValueError(
                        "math_ocr_fallback requires either Mathpix credentials or OpenAI API key"
                    )
        return values
    
    @classmethod
    def load_from_yaml(cls, yaml_file: Union[str, Path] = "config.yaml") -> "Settings":
        """
        Load settings from a YAML file with environment variable override support.
        
        Args:
            yaml_file: Path to the YAML configuration file
            
        Returns:
            Settings instance with loaded configuration
            
        Raises:
            FileNotFoundError: If the YAML file doesn't exist
            ValueError: If the YAML file is invalid
        """
        yaml_path = Path(yaml_file)
        
        if not yaml_path.exists():
            # If no config file exists, create one with defaults
            default_settings = cls()
            default_settings.save_to_yaml(yaml_path)
            return default_settings
        
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration file: {e}")
        
        # Convert any string paths to Path objects
        for key, value in yaml_data.items():
            if key.endswith(("_dir", "_file", "persist_directory")) and isinstance(value, str):
                yaml_data[key] = Path(value)
        
        return cls(**yaml_data)
    
    @classmethod
    def from_env_and_yaml(cls, yaml_file: Union[str, Path] = "config.yaml") -> "Settings":
        """
        Create settings instance from both YAML file and environment variables.
        
        Environment variables take precedence over YAML configuration.
        
        Args:
            yaml_file: Path to the YAML configuration file
            
        Returns:
            Settings instance with merged configuration
        """
        # Load from YAML if it exists
        yaml_path = Path(yaml_file)
        yaml_data = {}
        
        if yaml_path.exists():
            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    yaml_data = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML configuration file: {e}")
        
        # Convert paths in YAML data
        for key, value in yaml_data.items():
            if key.endswith(("_dir", "_file", "persist_directory")) and isinstance(value, str):
                yaml_data[key] = Path(value)
        
        # Create instance with environment override
        return cls(**yaml_data)
    
    def save_to_yaml(self, yaml_file: Union[str, Path] = "config.yaml") -> None:
        """
        Save current settings to a YAML file.
        
        Args:
            yaml_file: Path to save the YAML configuration file
        """
        yaml_path = Path(yaml_file)
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert Path objects to strings for YAML serialization
        data = self.dict()
        for key, value in data.items():
            if isinstance(value, Path):
                data[key] = str(value)
        
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=True, indent=2)
    
    def create_directories(self) -> None:
        """Create all configured directories if they don't exist."""
        directories = [
            self.input_dir,
            self.text_dir,
            self.meta_dir,
            self.math_dir,
            self.log_file.parent,
            self.chroma_persist_directory,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """
        Validate that required API keys are present for enabled features.
        
        Returns:
            Dictionary mapping feature names to validation status
        """
        validation_results = {}
        
        # Check OpenAI API key for embeddings and OCR
        if self.embedding_model.startswith("text-embedding"):
            validation_results["openai_embeddings"] = bool(self.openai_api_key)
        
        if self.math_ocr_fallback:
            validation_results["openai_ocr"] = bool(self.openai_api_key)
        
        # Check Mathpix API keys
        if self.mathpix_app_id or self.mathpix_app_key:
            validation_results["mathpix"] = bool(self.mathpix_app_id and self.mathpix_app_key)
        
        # Check Pinecone API key
        if self.pinecone_api_key:
            validation_results["pinecone"] = bool(self.pinecone_api_key)
        
        return validation_results


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(config_file: Union[str, Path] = "config.yaml") -> Settings:
    """
    Get the global settings instance, loading from config file if not already loaded.
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        Global settings instance
    """
    global _settings
    
    if _settings is None:
        _settings = Settings.load_from_yaml(config_file)
        # Ensure directories exist
        _settings.create_directories()
    
    return _settings


def reload_settings(config_file: Union[str, Path] = "config.yaml") -> Settings:
    """
    Force reload of settings from config file.
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        Newly loaded settings instance
    """
    global _settings
    _settings = Settings.load_from_yaml(config_file)
    _settings.create_directories()
    return _settings


# Example usage and configuration validation
if __name__ == "__main__":
    # Load settings
    settings = get_settings()
    
    # Print configuration summary
    print("Portfolio Optimizer Configuration")
    print("=" * 40)
    print(f"Input directory: {settings.input_dir}")
    print(f"Text directory: {settings.text_dir}")
    print(f"Math directory: {settings.math_dir}")
    print(f"Log level: {settings.log_level}")
    print(f"Parallel workers: {settings.parallel_workers}")
    print(f"Extract math: {settings.extract_math}")
    print(f"Chunk size: {settings.chunk_size}")
    print(f"Embedding model: {settings.embedding_model}")
    
    # Validate API keys
    api_validation = settings.validate_api_keys()
    if api_validation:
        print("\nAPI Key Validation:")
        for feature, is_valid in api_validation.items():
            status = "✓" if is_valid else "✗"
            print(f"  {feature}: {status}")
    
    # Save current configuration
    settings.save_to_yaml("example_config.yaml")
    print(f"\nConfiguration saved to: example_config.yaml")