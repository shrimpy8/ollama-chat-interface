"""
Pytest configuration and fixtures for ollama-chat-interface tests.

Provides reusable test fixtures and setup/teardown logic.

Author: Harsh
"""

import os
import sys
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any
import pytest
import yaml

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Provide a sample configuration dictionary for testing."""
    return {
        'ollama': {
            'base_url': 'http://localhost:11434',
            'api_endpoint': '/api/generate',
            'model_name': 'deepseek-r1:latest',
            'parameters': {
                'temperature': 0.7,
                'top_p': 0.9,
                'top_k': 40,
                'num_predict': 2048
            }
        },
        'request': {
            'timeout': 120,
            'retry': {
                'max_attempts': 3,
                'min_wait': 2,
                'max_wait': 10,
                'multiplier': 2
            }
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': 'ollama_chat.log',
            'console': True,
            'file_logging': True
        },
        'ui': {
            'title': 'DeepSeek-R1 AI Chat Interface',
            'description': 'Chat with DeepSeek-R1 model via local Ollama server',
            'theme': 'default',
            'share': False,
            'server': {
                'port': 7860,
                'host': '127.0.0.1'
            },
            'components': {
                'input': {
                    'placeholder': 'Type your message here...',
                    'lines': 3,
                    'max_lines': 10
                },
                'output': {
                    'placeholder': 'Response will appear here...',
                    'lines': 10
                }
            },
            'history': {
                'max_messages': 20,
                'show_timestamps': True
            }
        },
        'conversation': {
            'system_prompt': 'You are a helpful AI assistant powered by DeepSeek-R1.',
            'memory_enabled': True,
            'context_window': 4096
        }
    }


@pytest.fixture
def config_yaml_file(sample_config, tmp_path) -> Path:
    """Create a temporary config.yaml file for testing."""
    config_file = tmp_path / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(sample_config, f)
    return config_file


@pytest.fixture
def minimal_config() -> Dict[str, Any]:
    """Provide minimal configuration for testing defaults."""
    return {
        'ollama': {
            'model_name': 'deepseek-r1:latest'
        }
    }


@pytest.fixture
def invalid_yaml_file(tmp_path) -> Path:
    """Create a temporary invalid YAML file for testing error handling."""
    config_file = tmp_path / "invalid.yaml"
    with open(config_file, 'w') as f:
        f.write("invalid: yaml: content: [incomplete")
    return config_file


@pytest.fixture
def temp_log_file(tmp_path) -> Path:
    """Create a temporary log file path for testing."""
    return tmp_path / "test.log"


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration before each test."""
    # Get the test logger name
    test_logger_name = 'tests.test_logging_config'

    # Remove all handlers from root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Remove handlers from test module logger
    test_logger = logging.getLogger(test_logger_name)
    for handler in test_logger.handlers[:]:
        handler.close()
        test_logger.removeHandler(handler)

    # Reset logger level
    test_logger.setLevel(logging.NOTSET)
    test_logger.propagate = True

    yield

    # Cleanup after test
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)

    for handler in test_logger.handlers[:]:
        handler.close()
        test_logger.removeHandler(handler)

    # Reset logger level again
    test_logger.setLevel(logging.NOTSET)
    test_logger.propagate = True


@pytest.fixture
def mock_conversation_history():
    """Provide sample conversation history for testing."""
    return [
        ("Hello", "Hi there! How can I help you today?"),
        ("What is Python?", "Python is a high-level programming language..."),
        ("Tell me more", "Python was created by Guido van Rossum...")
    ]


@pytest.fixture
def mock_api_response() -> Dict[str, Any]:
    """Provide sample Ollama API response for testing."""
    return {
        "model": "deepseek-r1:latest",
        "created_at": "2025-12-03T10:00:00.000Z",
        "response": "This is a test response from the model.",
        "done": True,
        "context": [1, 2, 3, 4, 5],
        "total_duration": 1500000000,
        "load_duration": 100000000,
        "prompt_eval_count": 10,
        "eval_count": 20
    }


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Provide path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def mock_gradio_interface():
    """Mock Gradio interface for testing UI components."""
    class MockInterface:
        def __init__(self):
            self.launched = False

        def launch(self, **kwargs):
            self.launched = True
            return self

    return MockInterface()


# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (>1s)"
    )
    config.addinivalue_line(
        "markers", "requires_ollama: mark test as requiring Ollama server"
    )
    config.addinivalue_line(
        "markers", "requires_config: mark test as requiring config.yaml"
    )
