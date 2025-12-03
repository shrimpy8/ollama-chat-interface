"""
Tests for configuration loader module.

Tests configuration loading, validation, default values, and error handling.

Author: Harsh
"""

import pytest
import yaml
from pathlib import Path
from common.config_loader import ConfigLoader, load_config


@pytest.mark.unit
class TestConfigLoaderInitialization:
    """Test ConfigLoader initialization and error handling."""

    def test_load_valid_config(self, config_yaml_file):
        """Test loading a valid configuration file."""
        config = ConfigLoader(str(config_yaml_file))
        assert config.config is not None
        assert isinstance(config.config, dict)

    def test_singleton_pattern(self, config_yaml_file):
        """Test that ConfigLoader follows singleton pattern."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config1 = ConfigLoader(str(config_yaml_file))
        config2 = ConfigLoader(str(config_yaml_file))

        assert config1 is config2
        assert id(config1) == id(config2)

    def test_file_not_found(self, tmp_path):
        """Test error handling when config file doesn't exist."""
        # Reset singleton for test
        ConfigLoader._instance = None

        nonexistent_file = str(tmp_path / "nonexistent.yaml")
        with pytest.raises(FileNotFoundError) as exc_info:
            ConfigLoader(nonexistent_file)

        assert "Configuration file not found" in str(exc_info.value)

    def test_invalid_yaml(self, invalid_yaml_file):
        """Test error handling with invalid YAML syntax."""
        # Reset singleton for test
        ConfigLoader._instance = None

        with pytest.raises(yaml.YAMLError):
            ConfigLoader(str(invalid_yaml_file))

    def test_convenience_function(self, config_yaml_file):
        """Test load_config convenience function."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = load_config(str(config_yaml_file))
        assert isinstance(config, ConfigLoader)
        assert config.config is not None


@pytest.mark.unit
class TestOllamaConfiguration:
    """Test Ollama-related configuration methods."""

    def test_get_ollama_base_url(self, config_yaml_file):
        """Test retrieving Ollama base URL."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        base_url = config.get_ollama_base_url()

        assert base_url == 'http://localhost:11434'
        assert isinstance(base_url, str)

    def test_get_ollama_api_endpoint(self, config_yaml_file):
        """Test retrieving Ollama API endpoint."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        endpoint = config.get_ollama_api_endpoint()

        assert endpoint == '/api/generate'
        assert isinstance(endpoint, str)

    def test_get_full_api_url(self, config_yaml_file):
        """Test retrieving complete API URL."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        full_url = config.get_full_api_url()

        assert full_url == 'http://localhost:11434/api/generate'
        assert isinstance(full_url, str)

    def test_get_model_name(self, config_yaml_file):
        """Test retrieving model name."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        model_name = config.get_model_name()

        assert model_name == 'deepseek-r1:latest'
        assert isinstance(model_name, str)

    def test_get_model_parameters(self, config_yaml_file):
        """Test retrieving model parameters."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        params = config.get_model_parameters()

        assert isinstance(params, dict)
        assert 'temperature' in params
        assert 'top_p' in params
        assert 'top_k' in params
        assert 'num_predict' in params
        assert params['temperature'] == 0.7

    def test_get_temperature(self, config_yaml_file):
        """Test retrieving temperature setting."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        temperature = config.get_temperature()

        assert temperature == 0.7
        assert isinstance(temperature, float)


@pytest.mark.unit
class TestRequestConfiguration:
    """Test request-related configuration methods."""

    def test_get_request_timeout(self, config_yaml_file):
        """Test retrieving request timeout."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        timeout = config.get_request_timeout()

        assert timeout == 120
        assert isinstance(timeout, int)

    def test_get_retry_config(self, config_yaml_file):
        """Test retrieving retry configuration."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        retry_config = config.get_retry_config()

        assert isinstance(retry_config, dict)
        assert 'max_attempts' in retry_config
        assert 'min_wait' in retry_config
        assert 'max_wait' in retry_config
        assert 'multiplier' in retry_config
        assert retry_config['max_attempts'] == 3


@pytest.mark.unit
class TestLoggingConfiguration:
    """Test logging-related configuration methods."""

    def test_get_logging_config(self, config_yaml_file):
        """Test retrieving logging configuration."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        logging_config = config.get_logging_config()

        assert isinstance(logging_config, dict)
        assert 'level' in logging_config
        assert 'format' in logging_config
        assert 'file' in logging_config
        assert 'console' in logging_config
        assert logging_config['level'] == 'INFO'


@pytest.mark.unit
class TestUIConfiguration:
    """Test UI-related configuration methods."""

    def test_get_ui_title(self, config_yaml_file):
        """Test retrieving UI title."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        title = config.get_ui_title()

        assert title == 'DeepSeek-R1 AI Chat Interface'
        assert isinstance(title, str)

    def test_get_ui_description(self, config_yaml_file):
        """Test retrieving UI description."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        description = config.get_ui_description()

        assert isinstance(description, str)
        assert len(description) > 0

    def test_get_ui_theme(self, config_yaml_file):
        """Test retrieving UI theme."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        theme = config.get_ui_theme()

        assert theme == 'default'
        assert isinstance(theme, str)

    def test_get_ui_share(self, config_yaml_file):
        """Test retrieving UI share setting."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        share = config.get_ui_share()

        assert share is False
        assert isinstance(share, bool)

    def test_get_server_config(self, config_yaml_file):
        """Test retrieving server configuration."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        server_config = config.get_server_config()

        assert isinstance(server_config, dict)
        assert 'port' in server_config
        assert 'host' in server_config
        assert server_config['port'] == 7860
        assert server_config['host'] == '127.0.0.1'

    def test_get_input_config(self, config_yaml_file):
        """Test retrieving input component configuration."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        input_config = config.get_input_config()

        assert isinstance(input_config, dict)
        assert 'placeholder' in input_config
        assert 'lines' in input_config

    def test_get_output_config(self, config_yaml_file):
        """Test retrieving output component configuration."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        output_config = config.get_output_config()

        assert isinstance(output_config, dict)
        assert 'placeholder' in output_config

    def test_get_history_config(self, config_yaml_file):
        """Test retrieving history configuration."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        history_config = config.get_history_config()

        assert isinstance(history_config, dict)
        assert 'max_messages' in history_config
        assert 'show_timestamps' in history_config
        assert history_config['max_messages'] == 20


@pytest.mark.unit
class TestConversationConfiguration:
    """Test conversation-related configuration methods."""

    def test_get_system_prompt(self, config_yaml_file):
        """Test retrieving system prompt."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        system_prompt = config.get_system_prompt()

        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0

    def test_get_memory_enabled(self, config_yaml_file):
        """Test retrieving memory enabled setting."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        memory_enabled = config.get_memory_enabled()

        assert memory_enabled is True
        assert isinstance(memory_enabled, bool)

    def test_get_context_window(self, config_yaml_file):
        """Test retrieving context window setting."""
        # Reset singleton for test
        ConfigLoader._instance = None

        config = ConfigLoader(str(config_yaml_file))
        context_window = config.get_context_window()

        assert context_window == 4096
        assert isinstance(context_window, int)


@pytest.mark.unit
class TestDefaultValues:
    """Test default values when configuration is missing."""

    def test_defaults_with_minimal_config(self, tmp_path):
        """Test that default values are provided for missing configuration."""
        # Reset singleton for test
        ConfigLoader._instance = None

        # Create minimal config
        minimal_config = {'ollama': {}}
        config_file = tmp_path / "minimal.yaml"

        with open(config_file, 'w') as f:
            yaml.dump(minimal_config, f)

        config = ConfigLoader(str(config_file))

        # Test defaults
        assert config.get_ollama_base_url() == 'http://localhost:11434'
        assert config.get_model_name() == 'deepseek-r1:latest'
        assert config.get_request_timeout() == 120
        assert config.get_temperature() == 0.7
