"""
Tests for the Settings configuration management.

These tests verify YAML loading, environment variable override,
validation, and configuration management functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

import yaml
from pydantic import ValidationError

from src.settings import Settings, get_settings, reload_settings


class TestSettingsValidation:
    """Test settings validation."""
    
    def test_default_settings(self):
        """Test default settings creation."""
        settings = Settings()
        
        assert settings.log_level == "INFO"
        assert settings.parallel_workers == 4
        assert settings.chunk_size == 500
        assert settings.chunk_overlap == 50
        assert settings.extract_math is True
    
    def test_invalid_log_level(self):
        """Test validation of invalid log level."""
        with pytest.raises(ValidationError):
            Settings(log_level="INVALID")
    
    def test_invalid_parallel_workers(self):
        """Test validation of invalid parallel workers."""
        with pytest.raises(ValidationError):
            Settings(parallel_workers=0)
        
        with pytest.raises(ValidationError):
            Settings(parallel_workers=50)
    
    def test_invalid_chunk_size(self):
        """Test validation of invalid chunk size."""
        with pytest.raises(ValidationError):
            Settings(chunk_size=10)  # Too small
        
        with pytest.raises(ValidationError):
            Settings(chunk_size=20000)  # Too large
    
    def test_invalid_chunk_overlap(self):
        """Test validation of invalid chunk overlap."""
        with pytest.raises(ValidationError):
            Settings(chunk_overlap=-1)  # Negative
        
        with pytest.raises(ValidationError):
            Settings(chunk_size=100, chunk_overlap=150)  # Overlap >= chunk_size
    
    def test_invalid_concurrent_requests(self):
        """Test validation of invalid concurrent requests."""
        with pytest.raises(ValidationError):
            Settings(concurrent_requests=0)
        
        with pytest.raises(ValidationError):
            Settings(concurrent_requests=25)
    
    def test_mathpix_validation_with_ocr_enabled(self):
        """Test Mathpix validation when OCR is enabled."""
        # Should work with Mathpix credentials
        settings = Settings(
            math_ocr_fallback=True,
            mathpix_app_id="test-id",
            mathpix_app_key="test-key"
        )
        assert settings.math_ocr_fallback is True
        
        # Should work with OpenAI as fallback
        settings = Settings(
            math_ocr_fallback=True,
            openai_api_key="test-key"
        )
        assert settings.math_ocr_fallback is True
        
        # Should fail without any credentials
        with pytest.raises(ValidationError):
            Settings(math_ocr_fallback=True)


class TestYAMLLoading:
    """Test YAML configuration loading."""
    
    def test_load_from_nonexistent_yaml(self):
        """Test loading from non-existent YAML file creates defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yaml"
            
            # Should create default config file
            settings = Settings.load_from_yaml(config_path)
            assert config_path.exists()
            assert settings.log_level == "INFO"
    
    def test_load_from_valid_yaml(self):
        """Test loading from valid YAML file."""
        config_data = {
            "log_level": "DEBUG",
            "parallel_workers": 8,
            "chunk_size": 1000,
            "extract_math": False,
            "input_dir": "./custom/input",
            "text_dir": "./custom/text"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            settings = Settings.load_from_yaml(config_path)
            
            assert settings.log_level == "DEBUG"
            assert settings.parallel_workers == 8
            assert settings.chunk_size == 1000
            assert settings.extract_math is False
            assert settings.input_dir == Path("./custom/input")
            assert settings.text_dir == Path("./custom/text")
        finally:
            os.unlink(config_path)
    
    def test_load_from_invalid_yaml(self):
        """Test loading from invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid YAML configuration file"):
                Settings.load_from_yaml(config_path)
        finally:
            os.unlink(config_path)
    
    def test_save_to_yaml(self):
        """Test saving settings to YAML file."""
        settings = Settings(
            log_level="DEBUG",
            parallel_workers=8,
            chunk_size=1000
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "output_config.yaml"
            settings.save_to_yaml(config_path)
            
            # Verify file was created and contains correct data
            assert config_path.exists()
            
            with open(config_path, 'r') as f:
                saved_data = yaml.safe_load(f)
            
            assert saved_data['log_level'] == "DEBUG"
            assert saved_data['parallel_workers'] == 8
            assert saved_data['chunk_size'] == 1000


class TestEnvironmentVariables:
    """Test environment variable override functionality."""
    
    def test_env_override_basic(self):
        """Test basic environment variable override."""
        with patch.dict(os.environ, {
            'PORTFOLIO_OPTIMIZER_LOG_LEVEL': 'DEBUG',
            'PORTFOLIO_OPTIMIZER_PARALLEL_WORKERS': '8'
        }):
            settings = Settings()
            
            assert settings.log_level == "DEBUG"
            assert settings.parallel_workers == 8
    
    def test_env_override_api_keys(self):
        """Test environment variable override for API keys."""
        with patch.dict(os.environ, {
            'PORTFOLIO_OPTIMIZER_OPENAI_API_KEY': 'test-openai-key',
            'PORTFOLIO_OPTIMIZER_PINECONE_API_KEY': 'test-pinecone-key'
        }):
            settings = Settings()
            
            assert settings.openai_api_key == "test-openai-key"
            assert settings.pinecone_api_key == "test-pinecone-key"
    
    def test_env_and_yaml_precedence(self):
        """Test that environment variables take precedence over YAML."""
        config_data = {
            "log_level": "INFO",
            "parallel_workers": 4
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            with patch.dict(os.environ, {
                'PORTFOLIO_OPTIMIZER_LOG_LEVEL': 'DEBUG',
                'PORTFOLIO_OPTIMIZER_PARALLEL_WORKERS': '8'
            }):
                settings = Settings.from_env_and_yaml(config_path)
                
                # Environment variables should override YAML values
                assert settings.log_level == "DEBUG"
                assert settings.parallel_workers == 8
        finally:
            os.unlink(config_path)


class TestDirectoryCreation:
    """Test directory creation functionality."""
    
    def test_create_directories(self):
        """Test creation of configured directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            
            settings = Settings(
                input_dir=base_path / "input",
                text_dir=base_path / "text",
                meta_dir=base_path / "meta",
                math_dir=base_path / "math",
                log_file=base_path / "logs" / "test.log",
                chroma_persist_directory=base_path / "chroma"
            )
            
            settings.create_directories()
            
            # Verify all directories were created
            assert settings.input_dir.exists()
            assert settings.text_dir.exists()
            assert settings.meta_dir.exists()
            assert settings.math_dir.exists()
            assert settings.log_file.parent.exists()
            assert settings.chroma_persist_directory.exists()


class TestAPIKeyValidation:
    """Test API key validation functionality."""
    
    def test_validate_api_keys_all_present(self):
        """Test API key validation when all keys are present."""
        settings = Settings(
            openai_api_key="test-openai",
            mathpix_app_id="test-mathpix-id",
            mathpix_app_key="test-mathpix-key",
            pinecone_api_key="test-pinecone",
            math_ocr_fallback=True
        )
        
        validation = settings.validate_api_keys()
        
        assert validation['openai_embeddings'] is True
        assert validation['openai_ocr'] is True
        assert validation['mathpix'] is True
        assert validation['pinecone'] is True
    
    def test_validate_api_keys_missing(self):
        """Test API key validation when keys are missing."""
        settings = Settings(
            embedding_model="text-embedding-3-small",
            math_ocr_fallback=True
        )
        
        validation = settings.validate_api_keys()
        
        assert validation['openai_embeddings'] is False
        assert validation['openai_ocr'] is False
    
    def test_validate_mathpix_incomplete(self):
        """Test Mathpix validation with incomplete credentials."""
        settings = Settings(
            mathpix_app_id="test-id"
            # Missing mathpix_app_key
        )
        
        validation = settings.validate_api_keys()
        
        assert validation['mathpix'] is False


class TestGlobalSettings:
    """Test global settings management."""
    
    def test_get_settings_singleton(self):
        """Test that get_settings returns singleton instance."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"log_level": "DEBUG"}, f)
            config_path = f.name
        
        try:
            # First call creates instance
            settings1 = get_settings(config_path)
            
            # Second call returns same instance
            settings2 = get_settings(config_path)
            
            assert settings1 is settings2
            assert settings1.log_level == "DEBUG"
        finally:
            os.unlink(config_path)
    
    def test_reload_settings(self):
        """Test settings reload functionality."""
        config_data = {"log_level": "INFO"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            # Get initial settings
            settings1 = get_settings(config_path)
            assert settings1.log_level == "INFO"
            
            # Update config file
            config_data["log_level"] = "DEBUG"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Reload settings
            settings2 = reload_settings(config_path)
            assert settings2.log_level == "DEBUG"
            
            # Should be new instance
            assert settings1 is not settings2
        finally:
            os.unlink(config_path)


@pytest.mark.integration
class TestSettingsIntegration:
    """Integration tests for settings functionality."""
    
    def test_full_configuration_workflow(self):
        """Test complete configuration workflow."""
        # Create test configuration
        config_data = {
            "log_level": "DEBUG",
            "parallel_workers": 6,
            "chunk_size": 800,
            "chunk_overlap": 80,
            "extract_math": True,
            "math_ocr_fallback": False,
            "input_dir": "./test/input",
            "text_dir": "./test/text",
            "meta_dir": "./test/meta",
            "math_dir": "./test/math"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.yaml"
            
            # Save configuration
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Load with environment override
            with patch.dict(os.environ, {
                'PORTFOLIO_OPTIMIZER_LOG_LEVEL': 'ERROR',
                'PORTFOLIO_OPTIMIZER_OPENAI_API_KEY': 'test-key'
            }):
                settings = Settings.from_env_and_yaml(config_path)
            
            # Verify loaded settings
            assert settings.log_level == "ERROR"  # Environment override
            assert settings.parallel_workers == 6  # From YAML
            assert settings.openai_api_key == "test-key"  # Environment
            
            # Test validation
            validation = settings.validate_api_keys()
            assert 'openai_embeddings' in validation
            
            # Test directory creation
            settings.create_directories()
            assert settings.input_dir.exists()
            
            # Test saving modified settings
            settings.parallel_workers = 8
            output_path = Path(tmpdir) / "output_config.yaml"
            settings.save_to_yaml(output_path)
            
            # Verify saved settings
            with open(output_path, 'r') as f:
                saved_data = yaml.safe_load(f)
            assert saved_data['parallel_workers'] == 8