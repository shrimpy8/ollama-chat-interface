"""
Tests for export utilities.

Tests JSON and Markdown export functionality for conversation history.

Author: Harsh
"""

import json
import pytest
from common.export_utils import export_to_json, export_to_markdown


@pytest.fixture
def sample_conversation():
    """Provide sample conversation for testing."""
    return [
        {
            "user": "Hello",
            "assistant": "Hi! How can I help?",
            "timestamp": "2025-12-03T10:00:00",
            "parameters": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "max_tokens": 2048
            }
        },
        {
            "user": "What is Python?",
            "assistant": "Python is a high-level programming language.",
            "timestamp": "2025-12-03T10:01:00",
            "parameters": {
                "temperature": 0.8,
                "top_p": 0.95,
                "top_k": 50,
                "max_tokens": 1024
            }
        }
    ]


@pytest.mark.unit
def test_export_to_json(sample_conversation):
    """Test JSON export format."""
    result = export_to_json(
        sample_conversation,
        "deepseek-r1:latest",
        "You are helpful"
    )
    data = json.loads(result)

    assert "export_metadata" in data
    assert "conversation" in data
    assert data["export_metadata"]["total_messages"] == 2
    assert data["export_metadata"]["model"] == "deepseek-r1:latest"
    assert data["export_metadata"]["system_prompt"] == "You are helpful"
    assert len(data["conversation"]) == 2


@pytest.mark.unit
def test_export_to_json_empty_conversation():
    """Test JSON export with empty conversation."""
    result = export_to_json([], "model", "prompt")
    data = json.loads(result)

    assert data["export_metadata"]["total_messages"] == 0
    assert len(data["conversation"]) == 0


@pytest.mark.unit
def test_export_to_markdown(sample_conversation):
    """Test Markdown export format."""
    result = export_to_markdown(
        sample_conversation,
        "deepseek-r1:latest",
        "You are helpful"
    )

    # Check header
    assert "# Ollama Chat Conversation Export" in result
    assert "## Metadata" in result
    assert "deepseek-r1:latest" in result
    assert "Total Messages**: 2" in result

    # Check system prompt
    assert "## System Prompt" in result
    assert "You are helpful" in result

    # Check conversation exchanges
    assert "Hello" in result
    assert "Hi! How can I help?" in result
    assert "What is Python?" in result
    assert "Python is a high-level programming language." in result

    # Check parameters
    assert "Parameters:" in result
    assert "temp=0.7" in result
    assert "top_p=0.9" in result


@pytest.mark.unit
def test_export_to_markdown_empty_conversation():
    """Test Markdown export with empty conversation."""
    result = export_to_markdown([], "model", "prompt")

    assert "# Ollama Chat Conversation Export" in result
    assert "Total Messages**: 0" in result


@pytest.mark.unit
def test_json_export_preserves_structure(sample_conversation):
    """Test that JSON export preserves exact conversation structure."""
    result = export_to_json(sample_conversation, "model", "prompt")
    data = json.loads(result)

    # Check that conversation data is preserved exactly
    original_entry = sample_conversation[0]
    exported_entry = data["conversation"][0]

    assert exported_entry["user"] == original_entry["user"]
    assert exported_entry["assistant"] == original_entry["assistant"]
    assert exported_entry["timestamp"] == original_entry["timestamp"]
    assert exported_entry["parameters"]["temperature"] == original_entry["parameters"]["temperature"]


@pytest.mark.unit
def test_markdown_export_handles_missing_parameters():
    """Test Markdown export handles entries without parameters."""
    conversation = [{
        "user": "Test",
        "assistant": "Response",
        "timestamp": "2025-12-03T10:00:00"
        # No parameters
    }]

    result = export_to_markdown(conversation, "model", "prompt")

    # Should not raise error, should handle gracefully
    assert "Test" in result
    assert "Response" in result


@pytest.mark.unit
def test_json_export_unicode_support():
    """Test that JSON export supports unicode characters."""
    conversation = [{
        "user": "Hello 你好 مرحبا",
        "assistant": "Hi! 안녕하세요 👋",
        "timestamp": "2025-12-03T10:00:00"
    }]

    result = export_to_json(conversation, "model", "prompt")
    data = json.loads(result)

    # Unicode should be preserved
    assert "你好" in data["conversation"][0]["user"]
    assert "👋" in data["conversation"][0]["assistant"]


@pytest.mark.unit
def test_markdown_export_unicode_support():
    """Test that Markdown export supports unicode characters."""
    conversation = [{
        "user": "Hello 你好",
        "assistant": "Hi! 👋",
        "timestamp": "2025-12-03T10:00:00"
    }]

    result = export_to_markdown(conversation, "model", "prompt")

    # Unicode should be preserved
    assert "你好" in result
    assert "👋" in result
