"""
Configuration schema validation for PDF ingestion.
"""

import logging
from typing import Any, Dict

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    logging.warning("jsonschema not available, config validation disabled")

# JSON Schema for configuration validation
CONFIG_SCHEMA = {
    "type": "object",
    "required": ["input_dir", "text_dir", "meta_dir"],
    "properties": {
        # Directory paths
        "input_dir": {
            "type": "string",
            "minLength": 1,
            "description": "Directory containing PDF files to process"
        },
        "text_dir": {
            "type": "string", 
            "minLength": 1,
            "description": "Directory for extracted text files"
        },
        "meta_dir": {
            "type": "string",
            "minLength": 1, 
            "description": "Directory for metadata JSON files"
        },
        
        # Logging configuration
        "log_level": {
            "type": "string",
            "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
            "description": "Logging level"
        },
        "log_to_file": {
            "type": "boolean",
            "description": "Whether to log to file"
        },
        "log_file": {
            "type": "string",
            "description": "Log file path"
        },
        
        # DOI extraction
        "doi_regex": {
            "type": "string",
            "minLength": 1,
            "description": "Regex pattern for DOI extraction"
        },
        "doi_prefixes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "DOI prefixes to search for"
        },
        
        # Processing options
        "parallel_workers": {
            "type": "integer",
            "minimum": 1,
            "maximum": 32,
            "description": "Number of parallel workers"
        },
        "skip_existing": {
            "type": "boolean",
            "description": "Skip files with existing outputs"
        },
        "show_progress": {
            "type": "boolean",
            "description": "Show progress bar"
        },
        
        # PyMuPDF options
        "preserve_reading_order": {
            "type": "boolean",
            "description": "Preserve reading order in text extraction"
        },
        "warn_empty_pages": {
            "type": "boolean",
            "description": "Log warnings for empty pages"
        },
        "include_images": {
            "type": "boolean",
            "description": "Extract image information"
        },
        "pdf_chunk_size": {
            "type": "integer",
            "minimum": 0,
            "description": "Pages per chunk for large PDFs (0 = no chunking)"
        },
        
        # File handling
        "encoding": {
            "type": "string",
            "enum": ["utf-8", "ascii", "latin-1", "cp1252"],
            "description": "Text file encoding"
        },
        "json_indent": {
            "type": "integer",
            "minimum": 0,
            "maximum": 8,
            "description": "JSON file indentation"
        },
        "overwrite_existing": {
            "type": "boolean",
            "description": "Overwrite existing output files"
        }
    },
    "additionalProperties": False
}


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration against the schema.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If configuration is invalid
        jsonschema.ValidationError: If schema validation fails
    """
    if not JSONSCHEMA_AVAILABLE:
        # Basic validation without jsonschema
        _validate_config_basic(config)
        return
    
    try:
        jsonschema.validate(config, CONFIG_SCHEMA)
        logging.info("Configuration validation passed")
    except jsonschema.ValidationError as e:
        error_msg = f"Configuration validation failed: {e.message}"
        if e.absolute_path:
            error_msg += f" at path: {'.'.join(str(p) for p in e.absolute_path)}"
        raise ValueError(error_msg) from e
    except jsonschema.SchemaError as e:
        raise ValueError(f"Invalid schema: {e.message}") from e


def _validate_config_basic(config: Dict[str, Any]) -> None:
    """
    Basic configuration validation without jsonschema.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    # Check required fields
    required_fields = ["input_dir", "text_dir", "meta_dir"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Required configuration field missing: {field}")
        if not isinstance(config[field], str) or not config[field].strip():
            raise ValueError(f"Configuration field '{field}' must be a non-empty string")
    
    # Validate log level if present
    if "log_level" in config:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if config["log_level"] not in valid_levels:
            raise ValueError(f"Invalid log_level: {config['log_level']}. Must be one of {valid_levels}")
    
    # Validate parallel workers if present
    if "parallel_workers" in config:
        workers = config["parallel_workers"]
        if not isinstance(workers, int) or workers < 1:
            raise ValueError("parallel_workers must be a positive integer")
    
    # Validate encoding if present
    if "encoding" in config:
        valid_encodings = ["utf-8", "ascii", "latin-1", "cp1252"]
        if config["encoding"] not in valid_encodings:
            raise ValueError(f"Invalid encoding: {config['encoding']}. Must be one of {valid_encodings}")
    
    # Validate json_indent if present
    if "json_indent" in config:
        indent = config["json_indent"]
        if not isinstance(indent, int) or indent < 0:
            raise ValueError("json_indent must be a non-negative integer")
    
    logging.info("Basic configuration validation passed")


def get_config_defaults() -> Dict[str, Any]:
    """
    Get default configuration values.
    
    Returns:
        Dictionary with default configuration
    """
    return {
        "input_dir": "./data/papers",
        "text_dir": "./data/text", 
        "meta_dir": "./data/metadata",
        "log_level": "INFO",
        "log_to_file": True,
        "log_file": "./logs/pdf_ingestion.log",
        "doi_regex": r"10\.[0-9]{4,}[-._;()/:a-zA-Z0-9]*",
        "doi_prefixes": ["doi:", "DOI:", "https://doi.org/", "http://dx.doi.org/"],
        "parallel_workers": 4,
        "skip_existing": False,
        "show_progress": True,
        "preserve_reading_order": True,
        "warn_empty_pages": True,
        "include_images": False,
        "pdf_chunk_size": 0,
        "encoding": "utf-8",
        "json_indent": 2,
        "overwrite_existing": True
    }