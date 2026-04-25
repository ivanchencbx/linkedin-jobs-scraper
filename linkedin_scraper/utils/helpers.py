"""
Helper utilities for LinkedIn scraper
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


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


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration
    
    Returns:
        Default configuration dictionary
    """
    return {
        'linkedin': {
            'username_display': ''
        },
        'search': {
            'base_url': 'https://www.linkedin.com/jobs/search/',
            'filters': {
                'f_F': 'it',
                'f_CR': '102890883',
                'f_E': '3,4,5,6',
                'f_JT': 'F',
                'f_TPR': '2592000',
                'f_WT': '1'
            },
            'keywords': '("System"OR"Systems"OR"Software"OR"Engineer"OR"Digital"OR"Partner"OR"Product Manager"OR"Owner"OR"HEAD"OR"Lead"OR"Leader"OR"Director"OR"Manager"OR"Application"OR"CIO"OR"AI"OR"Artificial Intelligence"OR"Solution")AND("Health"OR"Healthcare"OR"Medical"OR"Medical care"OR"Life Science"OR"MedTech"OR"Devices"OR"Business"OR"HCP"OR"Customer"OR"Consumer"OR"Veeva"OR"Salesforce"OR"SFDC"OR"R%26D"OR"Tech")',
            'sort_by': 'R',
            'results_per_page': 25
        },
        'browser': {
            'headless': True,
            'window_width': 1920,
            'window_height': 1080,
            'page_load_timeout': 300,
            'implicit_wait': 10
        },
        'waits': {
            'page_load': 300,
            'element_wait': 60,
            'verification_retry': 30,
            'between_pages': 5
        },
        'storage': {
            'filename': 'linkedin_jobs.csv',
            'encoding': 'utf-8-sig'
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': 'scraper.log'
        }
    }


def find_config_file(config_path: str = 'config/config.yaml') -> Path:
    """
    Find configuration file in multiple locations
    
    Search order:
    1. Specified path from command line (--config)
    2. ./config/config.yaml (current working directory)
    3. ~/.linkedin-scraper/config.yaml (user home directory - GLOBAL)
    4. Package default config (built into the package)
    
    Args:
        config_path: Path to configuration file (from command line)
        
    Returns:
        Path to the found configuration file
    """
    # 1. 检查命令行指定的路径
    specified_path = Path(config_path)
    if specified_path.exists():
        logger.info(f"Found config at specified path: {specified_path}")
        return specified_path
    
    # 2. 检查当前工作目录的 config/config.yaml
    local_config = Path.cwd() / 'config' / 'config.yaml'
    if local_config.exists():
        logger.info(f"Found local config: {local_config}")
        return local_config
    
    # 3. 检查用户主目录的全局配置
    global_config = Path.home() / '.linkedin-scraper' / 'config.yaml'
    if global_config.exists():
        logger.info(f"Found global config: {global_config}")
        return global_config
    
    # 4. 尝试从安装包中读取默认配置
    try:
        package_config = Path(__file__).parent.parent / 'config' / 'config.yaml'
        if package_config.exists():
            logger.info(f"Found package config: {package_config}")
            return package_config
    except Exception:
        pass
    
    # 5. 如果都不存在，返回全局配置路径（用于创建）
    return global_config


def load_config(config_path: str = 'config/config.yaml') -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Search order (first found wins):
    1. Specified path from command line (--config)
    2. ./config/config.yaml (current working directory)
    3. ~/.linkedin-scraper/config.yaml (user home directory - GLOBAL)
    4. Package default config (built into the package)
    
    If none exists, creates a global config in user home directory.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    config_file = find_config_file(config_path)
    
    # 如果配置文件不存在，创建全局配置
    if not config_file.exists():
        logger.warning(f"Configuration file not found: {config_path}")
        
        # 创建全局配置目录
        global_config_dir = Path.home() / '.linkedin-scraper'
        global_config_dir.mkdir(parents=True, exist_ok=True)
        config_file = global_config_dir / 'config.yaml'
        
        # 创建默认配置
        default_config = get_default_config()
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False)
        
        logger.info(f"Created global config at: {config_file}")
        print(f"\n📝 Created global configuration at: {config_file}")
        print(f"   You can edit this file to customize your search filters.\n")
    
    # 加载配置
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded config from: {config_file}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config from {config_file}: {e}")
        # 返回默认配置作为后备
        print(f"⚠️ Failed to load config, using defaults. Error: {e}")
        return get_default_config()


def save_config(config: Dict[str, Any], config_path: str = None) -> None:
    """
    Save configuration to YAML file
    
    Args:
        config: Configuration dictionary
        config_path: Path to configuration file (defaults to global config)
    """
    if config_path:
        config_file = Path(config_path)
    else:
        # 默认保存到用户主目录
        global_config_dir = Path.home() / '.linkedin-scraper'
        global_config_dir.mkdir(parents=True, exist_ok=True)
        config_file = global_config_dir / 'config.yaml'
    
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    logger.info(f"Configuration saved to {config_file}")
    print(f"✓ Configuration saved to: {config_file}")


def save_display_name_to_config(display_name: str, config_path: str = None) -> None:
    """
    Save display name to configuration file
    
    Args:
        display_name: LinkedIn display name
        config_path: Path to configuration file
    """
    config = load_config(config_path if config_path else 'config/config.yaml')
    
    if 'linkedin' not in config:
        config['linkedin'] = {}
    
    config['linkedin']['username_display'] = display_name
    
    save_config(config, config_path)
    logger.info(f"Saved display_name to config: {display_name}")