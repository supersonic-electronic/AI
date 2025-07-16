"""
Configuration validation module using JSON Schema.

This module provides validation for config.yaml files to ensure they
conform to the expected schema and contain valid values.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
import jsonschema
from jsonschema import ValidationError, SchemaError


logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors."""
    pass


def load_schema(schema_path: str = "config_schema.json") -> Dict[str, Any]:
    """
    Load JSON schema from file.
    
    Args:
        schema_path: Path to the JSON schema file
        
    Returns:
        Schema dictionary
        
    Raises:
        ConfigValidationError: If schema cannot be loaded or parsed
    """
    try:
        schema_file = Path(schema_path)
        if not schema_file.exists():
            raise ConfigValidationError(f"Schema file not found: {schema_path}")
        
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # Validate the schema itself
        jsonschema.Draft7Validator.check_schema(schema)
        return schema
        
    except json.JSONDecodeError as e:
        raise ConfigValidationError(f"Invalid JSON in schema file: {e}")
    except SchemaError as e:
        raise ConfigValidationError(f"Invalid JSON schema: {e}")
    except Exception as e:
        raise ConfigValidationError(f"Failed to load schema: {e}")


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the config YAML file
        
    Returns:
        Configuration dictionary
        
    Raises:
        ConfigValidationError: If config cannot be loaded or parsed
    """
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            raise ConfigValidationError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if config is None:
            raise ConfigValidationError("Configuration file is empty")
        
        if not isinstance(config, dict):
            raise ConfigValidationError("Configuration must be a YAML object/dictionary")
        
        return config
        
    except yaml.YAMLError as e:
        raise ConfigValidationError(f"Invalid YAML in config file: {e}")
    except Exception as e:
        raise ConfigValidationError(f"Failed to load config: {e}")


def validate_config(config: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate configuration against JSON schema.
    
    Args:
        config: Configuration dictionary to validate
        schema: JSON schema dictionary
        
    Raises:
        ConfigValidationError: If validation fails
    """
    try:
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(config))
        
        if errors:
            error_messages = []
            for error in errors:
                path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
                error_messages.append(f"  {path}: {error.message}")
            
            raise ConfigValidationError(
                f"Configuration validation failed:\n" + "\n".join(error_messages)
            )
            
    except ValidationError as e:
        path = " -> ".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
        raise ConfigValidationError(f"Validation error at {path}: {e.message}")
    except Exception as e:
        raise ConfigValidationError(f"Unexpected validation error: {e}")


def validate_config_file(
    config_path: str = "config.yaml", 
    schema_path: str = "config_schema.json",
    exit_on_error: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Load and validate configuration file against schema.
    
    Args:
        config_path: Path to configuration file
        schema_path: Path to JSON schema file
        exit_on_error: Whether to exit the program on validation errors
        
    Returns:
        Validated configuration dictionary, or None if validation fails
        and exit_on_error is False
        
    Raises:
        ConfigValidationError: If validation fails and exit_on_error is False
    """
    try:
        logger.info(f"Loading configuration from {config_path}")
        config = load_config(config_path)
        
        logger.info(f"Loading schema from {schema_path}")
        schema = load_schema(schema_path)
        
        logger.info("Validating configuration against schema")
        validate_config(config, schema)
        
        logger.info("Configuration validation successful")
        return config
        
    except ConfigValidationError as e:
        error_msg = f"Configuration validation failed: {e}"
        logger.error(error_msg)
        
        if exit_on_error:
            print(f"ERROR: {error_msg}", file=sys.stderr)
            print("\nPlease check your config.yaml file and fix the validation errors.", file=sys.stderr)
            print("See config_schema.json for the expected configuration format.", file=sys.stderr)
            sys.exit(1)
        else:
            raise


def transform_legacy_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform legacy configuration format to new schema-compliant format.
    
    This function maps the current config.yaml structure to the new schema
    structure expected by the JSON schema.
    
    Args:
        config: Legacy configuration dictionary
        
    Returns:
        Transformed configuration dictionary
    """
    transformed = {}
    
    # Map data paths
    if any(key in config for key in ['input_dir', 'text_dir', 'meta_dir', 'chroma_persist_directory']):
        transformed['data_paths'] = {}
        if 'input_dir' in config:
            transformed['data_paths']['source_directory'] = config['input_dir']
        if 'text_dir' in config:
            transformed['data_paths']['output_directory'] = config['text_dir']
        if 'chroma_persist_directory' in config:
            transformed['data_paths']['chunks_directory'] = config['chroma_persist_directory']
        if 'meta_dir' in config:
            transformed['data_paths']['cache_directory'] = config['meta_dir']
    
    # Map processing settings
    processing_keys = ['chunk_size', 'chunk_overlap', 'parallel_workers', 'embedding_batch_size', 'max_retries']
    if any(key in config for key in processing_keys):
        transformed['processing'] = {}
        if 'chunk_size' in config:
            transformed['processing']['chunk_size'] = config['chunk_size']
        if 'chunk_overlap' in config:
            transformed['processing']['chunk_overlap'] = config['chunk_overlap']
        if 'parallel_workers' in config:
            transformed['processing']['max_workers'] = config['parallel_workers']
        if 'embedding_batch_size' in config:
            transformed['processing']['batch_size'] = config['embedding_batch_size']
        if 'max_retries' in config:
            transformed['processing']['timeout_seconds'] = config.get('retry_delay', 1) * config['max_retries']
    
    # Map extractor settings
    if 'preserve_reading_order' in config or 'extract_math' in config:
        transformed['extractors'] = {}
        if 'preserve_reading_order' in config:
            transformed['extractors']['pdf'] = {
                'enabled': True,
                'preserve_layout': config['preserve_reading_order']
            }
    
    # Map math detection settings
    math_keys = ['extract_math', 'math_detection_threshold', 'math_ocr_fallback']
    if any(key in config for key in math_keys):
        transformed['math_detection'] = {}
        if 'extract_math' in config:
            transformed['math_detection']['enabled'] = config['extract_math']
        if 'math_detection_threshold' in config:
            # Convert threshold to confidence (normalize to 0-1 range)
            threshold = config['math_detection_threshold']
            confidence = min(1.0, max(0.0, threshold / 10.0))  # Assume max threshold is 10
            transformed['math_detection']['confidence_threshold'] = confidence
        if 'math_ocr_fallback' in config:
            transformed['math_detection']['use_improved_detector'] = config['math_ocr_fallback']
    
    # Map vector store settings
    vector_keys = ['embedding_model', 'pinecone_api_key', 'chroma_persist_directory']
    if any(key in config for key in vector_keys):
        transformed['vector_store'] = {}
        if 'embedding_model' in config:
            transformed['vector_store']['embedding_model'] = config['embedding_model']
        if 'pinecone_api_key' in config and config['pinecone_api_key']:
            transformed['vector_store']['type'] = 'pinecone'
        elif 'chroma_persist_directory' in config:
            transformed['vector_store']['type'] = 'chroma'
        else:
            transformed['vector_store']['type'] = 'local'
    
    # Map logging settings
    log_keys = ['log_level', 'log_file']
    if any(key in config for key in log_keys):
        transformed['logging'] = {}
        if 'log_level' in config:
            transformed['logging']['level'] = config['log_level'].upper()
        if 'log_file' in config:
            transformed['logging']['file'] = config['log_file']
    
    # Map API keys
    api_keys = ['openai_api_key', 'pinecone_api_key']
    if any(key in config for key in api_keys):
        transformed['api_keys'] = {}
        if 'openai_api_key' in config and config['openai_api_key']:
            transformed['api_keys']['openai'] = config['openai_api_key']
        if 'pinecone_api_key' in config and config['pinecone_api_key']:
            transformed['api_keys']['pinecone'] = config['pinecone_api_key']
    
    return transformed


def validate_and_transform_config(
    config_path: str = "config.yaml",
    schema_path: str = "config_schema.json",
    exit_on_error: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Load, transform, and validate configuration file.
    
    This function handles both legacy and new configuration formats,
    transforming legacy configs to the new schema format before validation.
    
    Args:
        config_path: Path to configuration file
        schema_path: Path to JSON schema file
        exit_on_error: Whether to exit the program on validation errors
        
    Returns:
        Validated and transformed configuration dictionary
    """
    try:
        logger.info(f"Loading configuration from {config_path}")
        raw_config = load_config(config_path)
        
        logger.info(f"Loading schema from {schema_path}")
        schema = load_schema(schema_path)
        
        # Try to validate as-is first
        try:
            logger.info("Attempting validation of configuration as-is")
            validate_config(raw_config, schema)
            logger.info("Configuration validation successful (new format)")
            return raw_config
        except ConfigValidationError:
            logger.info("Configuration appears to be in legacy format, attempting transformation")
        
        # Transform legacy format
        transformed_config = transform_legacy_config(raw_config)
        
        logger.info("Validating transformed configuration against schema")
        validate_config(transformed_config, schema)
        
        logger.info("Configuration validation successful (transformed from legacy format)")
        logger.warning("Consider updating your config.yaml to the new format. See config_schema.json for reference.")
        
        return transformed_config
        
    except ConfigValidationError as e:
        error_msg = f"Configuration validation failed: {e}"
        logger.error(error_msg)
        
        if exit_on_error:
            print(f"ERROR: {error_msg}", file=sys.stderr)
            print("\nPlease check your config.yaml file and fix the validation errors.", file=sys.stderr)
            print("See config_schema.json for the expected configuration format.", file=sys.stderr)
            sys.exit(1)
        else:
            raise