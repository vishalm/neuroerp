"""
Configuration management for NeuroERP.

This module handles loading, validating, and providing access to system configuration
from various sources (env vars, config files, etc.)
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass

class Config:
    """Central configuration management for NeuroERP."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one config instance exists."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration system.
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
        """
        # Skip if already initialized (singleton pattern)
        if self._initialized:
            return
            
        self._config_data = {}
        self._config_path = config_path or os.environ.get('NEUROERP_CONFIG', 'config.yaml')
        self._env_prefix = 'NEUROERP_'
        
        # Load configuration from different sources
        self._load_defaults()
        self._load_config_file()
        self._load_environment_variables()
        
        self._initialized = True
        logger.info(f"Configuration initialized with {len(self._config_data)} settings")
    
    def _load_defaults(self):
        """Load default configuration values."""
        self._config_data = {
            "system": {
                "debug": False,
                "log_level": "INFO",
                "temp_dir": "/tmp/neuroerp"
            },
            "ai_engine": {
                "default_model": "general",
                "temperature": 0.7,
                "max_tokens": 1024,
                "provider": "ollama"
            },
            "neural_fabric": {
                "vector_dimensions": 768,
                "index_type": "hnsw",
                "similarity_metric": "cosine"
            },
            "event_bus": {
                "max_queue_size": 1000,
                "worker_threads": 4,
                "retry_attempts": 3
            },
            "security": {
                "token_expiry": 3600,
                "password_min_length": 10,
                "enable_2fa": True
            },
            "database": {
                "vector_db": {
                    "host": "localhost",
                    "port": 8080,
                    "username": "",
                    "password": ""
                },
                "document_db": {
                    "host": "localhost",
                    "port": 27017,
                    "username": "",
                    "password": ""
                }
            }
        }
    
    def _load_config_file(self):
        """Load configuration from file."""
        if not self._config_path:
            logger.warning("No configuration file specified.")
            return
            
        config_path = Path(self._config_path)
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return
            
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    file_config = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    file_config = json.load(f)
                else:
                    raise ConfigurationError(f"Unsupported config file format: {config_path.suffix}")
                
                # Deep merge the file config with defaults
                self._deep_update(self._config_data, file_config)
                logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration file: {e}")
            raise ConfigurationError(f"Failed to load configuration file: {e}")
    
    def _load_environment_variables(self):
        """Load configuration from environment variables.
        
        Environment variables should be prefixed with NEUROERP_ and use double underscores
        to indicate nested keys. For example, NEUROERP_DATABASE__VECTOR_DB__HOST
        """
        for key, value in os.environ.items():
            if key.startswith(self._env_prefix):
                # Strip prefix and split by double underscore for nesting
                config_key = key[len(self._env_prefix):].lower()
                key_parts = config_key.split('__')
                
                # Convert string value to appropriate type
                typed_value = self._parse_env_value(value)
                
                # Navigate to the correct nested dictionary
                config_ref = self._config_data
                for part in key_parts[:-1]:
                    if part not in config_ref:
                        config_ref[part] = {}
                    config_ref = config_ref[part]
                
                # Set the value
                config_ref[key_parts[-1]] = typed_value
                logger.debug(f"Set config value from environment: {key}")
    
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable string into appropriate Python type."""
        # Check for boolean
        if value.lower() in ['true', 'yes', '1']:
            return True
        if value.lower() in ['false', 'no', '0']:
            return False
            
        # Check for null/None
        if value.lower() in ['null', 'none']:
            return None
            
        # Check for integer
        try:
            return int(value)
        except ValueError:
            pass
            
        # Check for float
        try:
            return float(value)
        except ValueError:
            pass
            
        # Check for JSON object or array
        if (value.startswith('{') and value.endswith('}')) or \
           (value.startswith('[') and value.endswith(']')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
                
        # Default to string
        return value
    
    def _deep_update(self, target: Dict, source: Dict):
        """Recursively update a nested dictionary."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get a configuration value by its dot-notation path.
        
        Args:
            key_path: Dot-notation path (e.g., 'database.vector_db.host')
            default: Default value to return if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self._config_data
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """Set a configuration value by its dot-notation path.
        
        Args:
            key_path: Dot-notation path (e.g., 'database.vector_db.host')
            value: The value to set
        """
        keys = key_path.split('.')
        config_ref = self._config_data
        
        # Navigate to the correct nested dictionary
        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]
        
        # Set the value
        config_ref[keys[-1]] = value
    
    def save(self, config_path: Optional[str] = None):
        """Save current configuration to file.
        
        Args:
            config_path: Path to save configuration (defaults to initialized path)
        """
        save_path = Path(config_path or self._config_path)
        
        try:
            with open(save_path, 'w') as f:
                if save_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.safe_dump(self._config_data, f, default_flow_style=False)
                elif save_path.suffix.lower() == '.json':
                    json.dump(self._config_data, f, indent=2)
                else:
                    raise ConfigurationError(f"Unsupported config file format: {save_path.suffix}")
                
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def as_dict(self) -> Dict[str, Any]:
        """Return the entire configuration as a dictionary."""
        return self._config_data.copy()
    
    def validate(self, schema: Dict[str, Any]) -> List[str]:
        """Validate configuration against a JSON schema.
        
        Args:
            schema: JSON schema to validate against
            
        Returns:
            List of validation errors, empty if valid
        """
        try:
            import jsonschema
            validator = jsonschema.Draft7Validator(schema)
            errors = list(validator.iter_errors(self._config_data))
            return [error.message for error in errors]
        except ImportError:
            logger.warning("jsonschema package not installed, skipping validation")
            return []