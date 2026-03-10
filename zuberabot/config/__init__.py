"""Configuration module for zuberabot."""

from zuberabot.config.loader import load_config, get_config_path
from zuberabot.config.schema import Config

__all__ = ["Config", "load_config", "get_config_path"]
