"""
Configuration utilities for FinOps360 cost analysis.
"""
import os
import yaml
from typing import Dict, Any, Optional


class FinOpsConfig:
    """Configuration class for FinOps360 cost analysis."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        """Initialize the configuration with a dictionary."""
        for key, value in config_dict.items():
            setattr(self, key, value)
            
        # Extract BigQuery properties for easy access
        if hasattr(self, 'bigquery'):
            for key, value in self.bigquery.items():
                setattr(self, f"bigquery_{key}", value)
    
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
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        # Set defaults
        if 'output_dir' not in config_dict:
            config_dict['output_dir'] = 'reports'
            
        return FinOpsConfig(config_dict)
    except Exception as e:
        raise ValueError(f"Error loading configuration from {config_path}: {e}")