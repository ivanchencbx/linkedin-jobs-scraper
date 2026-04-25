"""
Helper utilities for LinkedIn scraper
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any


def setup_logging(config: Dict[str, Any]) -> None:
    """
    Setup logging configuration
    
    Args:
        config: Configuration dictionary with logging settings
    """
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO').upper())
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = log_config.get('file', 'scraper.log')
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def load_config(config_path: str = 'config/config.yaml') -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def save_config(config: Dict[str, Any], config_path: str = 'config/config.yaml') -> None:
    """
    Save configuration to YAML file
    
    Args:
        config: Configuration dictionary
        config_path: Path to configuration file
    """
    config_file = Path(config_path)
    
    # Ensure directory exists
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    logging.getLogger(__name__).info(f"Configuration saved to {config_path}")


def save_display_name_to_config(display_name: str, config_path: str = 'config/config.yaml') -> None:
    """
    Save display name to configuration file
    
    Args:
        display_name: LinkedIn display name
        config_path: Path to configuration file
    """
    config = load_config(config_path)
    
    if 'linkedin' not in config:
        config['linkedin'] = {}
    
    config['linkedin']['username_display'] = display_name
    
    save_config(config, config_path)
    logging.getLogger(__name__).info(f"Saved display_name to config: {display_name}")