"""
Configuration Loader for Ollama Chat Interface

Provides type-safe configuration management with YAML file support.
Uses singleton pattern for efficient configuration access throughout the application.

Author: Harsh
"""

import os
import logging
from typing import Dict, Any, Optional, List
import yaml

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Type-safe configuration loader for Ollama Chat Interface.

    Loads configuration from config.yaml and provides typed access methods
    for various configuration sections.

    Attributes:
        config (Dict[str, Any]): The loaded configuration dictionary

    Example:
        >>> config = ConfigLoader()
        >>> model_name = config.get_model_name()
        >>> print(model_name)
        'deepseek-r1:latest'
    """

    _instance: Optional['ConfigLoader'] = None

    def __new__(cls, config_path: str = "config.yaml"):
        """Implement singleton pattern to avoid reloading config."""
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the configuration loader.

        Args:
            config_path: Path to the YAML configuration file

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
        """
        # Only initialize once (singleton pattern)
        if self._initialized:
            return

        try:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Configuration file not found: {config_path}")

            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)

            logger.info(f"Configuration loaded successfully from {config_path}")
            self._initialized = True

        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise

    # Ollama Configuration Methods
    def get_ollama_base_url(self) -> str:
        """Get Ollama server base URL."""
        return self.config.get('ollama', {}).get('base_url', 'http://localhost:11434')

    def get_ollama_api_endpoint(self) -> str:
        """Get Ollama API endpoint path."""
        return self.config.get('ollama', {}).get('api_endpoint', '/api/generate')

    def get_full_api_url(self) -> str:
        """Get complete Ollama API URL (base + endpoint)."""
        base = self.get_ollama_base_url()
        endpoint = self.get_ollama_api_endpoint()
        return f"{base}{endpoint}"

    def get_model_name(self) -> str:
        """Get Ollama model name."""
        return self.config.get('ollama', {}).get('model_name', 'deepseek-r1:latest')

    def get_model_parameters(self) -> Dict[str, Any]:
        """
        Get model generation parameters.

        Returns:
            Dictionary with temperature, top_p, top_k, num_predict
        """
        return self.config.get('ollama', {}).get('parameters', {
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 40,
            'num_predict': 2048
        })

    def get_temperature(self) -> float:
        """Get model temperature setting."""
        return self.get_model_parameters().get('temperature', 0.7)

    # Request Configuration Methods
    def get_request_timeout(self) -> int:
        """Get API request timeout in seconds."""
        return self.config.get('request', {}).get('timeout', 120)

    def get_retry_config(self) -> Dict[str, int]:
        """
        Get retry configuration for API calls.

        Returns:
            Dictionary with max_attempts, min_wait, max_wait, multiplier
        """
        return self.config.get('request', {}).get('retry', {
            'max_attempts': 3,
            'min_wait': 2,
            'max_wait': 10,
            'multiplier': 2
        })

    # Logging Configuration Methods
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration.

        Returns:
            Dictionary with level, format, file, console, file_logging
        """
        return self.config.get('logging', {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': 'ollama_chat.log',
            'console': True,
            'file_logging': True
        })

    # UI Configuration Methods
    def get_ui_title(self) -> str:
        """Get Gradio interface title."""
        return self.config.get('ui', {}).get('title', 'DeepSeek-R1 AI Chat Interface')

    def get_ui_description(self) -> str:
        """Get Gradio interface description."""
        return self.config.get('ui', {}).get('description',
                                            'Chat with DeepSeek-R1 model via local Ollama server')

    def get_ui_theme(self) -> str:
        """Get Gradio theme."""
        return self.config.get('ui', {}).get('theme', 'default')

    def get_ui_share(self) -> bool:
        """Get whether to enable public sharing."""
        return self.config.get('ui', {}).get('share', False)

    def get_server_config(self) -> Dict[str, Any]:
        """
        Get server configuration.

        Returns:
            Dictionary with port and host
        """
        return self.config.get('ui', {}).get('server', {
            'port': 7860,
            'host': '127.0.0.1'
        })

    def get_input_config(self) -> Dict[str, Any]:
        """Get input component configuration."""
        return self.config.get('ui', {}).get('components', {}).get('input', {
            'placeholder': 'Type your message here...',
            'lines': 3,
            'max_lines': 10
        })

    def get_output_config(self) -> Dict[str, Any]:
        """Get output component configuration."""
        return self.config.get('ui', {}).get('components', {}).get('output', {
            'placeholder': 'Response will appear here...',
            'lines': 10
        })

    def get_history_config(self) -> Dict[str, Any]:
        """
        Get chat history configuration.

        Returns:
            Dictionary with max_messages and show_timestamps
        """
        return self.config.get('ui', {}).get('history', {
            'max_messages': 20,
            'show_timestamps': True
        })

    # Conversation Configuration Methods
    def get_system_prompt(self) -> str:
        """Get system prompt for conversation."""
        return self.config.get('conversation', {}).get('system_prompt',
                                                       'You are a helpful AI assistant powered by DeepSeek-R1.')

    def get_memory_enabled(self) -> bool:
        """Check if conversation memory is enabled."""
        return self.config.get('conversation', {}).get('memory_enabled', True)

    def get_context_window(self) -> int:
        """Get maximum context window in tokens."""
        return self.config.get('conversation', {}).get('context_window', 4096)


# Convenience function for quick access
def load_config(config_path: str = "config.yaml") -> ConfigLoader:
    """
    Convenience function to load configuration.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        ConfigLoader instance

    Example:
        >>> config = load_config()
        >>> model = config.get_model_name()
    """
    return ConfigLoader(config_path)
