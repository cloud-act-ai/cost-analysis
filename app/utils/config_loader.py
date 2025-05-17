"""
Configuration utilities for FinOps360 cost analysis.
"""
import os
import yaml
import logging
from typing import Dict, Any, Optional

from app.utils.config_default import get_default_config

logger = logging.getLogger(__name__)

class FinOpsConfig:
    """Configuration class for FinOps360 cost analysis."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        """Initialize the configuration with a dictionary."""
        # Apply defaults and update with provided values
        self._config = self._apply_defaults(config_dict)
        
        # Set attributes based on config dictionary
        for key, value in self._config.items():
            setattr(self, key, value)
            
        # Extract BigQuery properties for easy access
        if hasattr(self, 'bigquery'):
            for key, value in self.bigquery.items():
                setattr(self, f"bigquery_{key}", value)
        
        # Ensure BigQuery is always enabled
        if hasattr(self, 'bigquery') and not hasattr(self, 'bigquery_use_bigquery'):
            setattr(self, 'bigquery_use_bigquery', True)
    
    def _apply_defaults(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for missing configuration."""
        defaults = get_default_config()
        result = {}
        
        # Recursive function to merge dictionaries
        def merge_dicts(defaults, overrides, result_dict):
            for key, default_value in defaults.items():
                if key in overrides:
                    if isinstance(default_value, dict) and isinstance(overrides[key], dict):
                        result_dict[key] = {}
                        merge_dicts(default_value, overrides[key], result_dict[key])
                    else:
                        result_dict[key] = overrides[key]
                else:
                    result_dict[key] = default_value
            
            # Add any keys from overrides that aren't in defaults
            for key, value in overrides.items():
                if key not in defaults:
                    result_dict[key] = value
                    
        merge_dicts(defaults, config_dict, result)
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-like getter for compatibility with existing code."""
        if hasattr(self, key):
            return getattr(self, key)
        return default


def load_config(config_path: str) -> FinOpsConfig:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        FinOpsConfig object with configuration values
    """
    # Get absolute path relative to this file
    if not os.path.isabs(config_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(base_dir, config_path)
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_dict = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {config_path}")
        else:
            logger.warning(f"Configuration file {config_path} not found, using defaults")
            config_dict = {}
        
        # Set defaults
        if 'output_dir' not in config_dict:
            config_dict['output_dir'] = 'reports'
            
        return FinOpsConfig(config_dict)
    except Exception as e:
        logger.error(f"Error loading configuration from {config_path}: {e}")
        logger.info("Using default configuration")
        return FinOpsConfig({})