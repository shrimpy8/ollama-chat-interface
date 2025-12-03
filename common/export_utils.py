"""
Export Utilities for Ollama Chat Interface

Provides functions to export conversation history to various formats.
Supports JSON (with metadata) and Markdown (human-readable) exports.

Author: Harsh
"""

import json
from typing import List, Dict, Any
from datetime import datetime


def export_to_json(
    conversation_history: List[Dict[str, Any]],
    model_name: str,
    system_prompt: str
) -> str:
    """
    Export conversation history to JSON with metadata.

    Args:
        conversation_history: List of conversation entries with user/assistant messages
        model_name: Name of the model used for generation
        system_prompt: System prompt used in the conversation

    Returns:
        JSON string with metadata and conversation history

    Example:
        >>> history = [{"user": "Hi", "assistant": "Hello!", "timestamp": "2025-12-03T10:00:00"}]
        >>> json_str = export_to_json(history, "deepseek-r1:latest", "You are helpful")
        >>> data = json.loads(json_str)
        >>> print(data["export_metadata"]["total_messages"])
        1
    """
    export_data = {
        "export_metadata": {
            "timestamp": datetime.now().isoformat(),
            "model": model_name,
            "system_prompt": system_prompt,
            "total_messages": len(conversation_history),
            "export_version": "1.0"
        },
        "conversation": conversation_history
    }
    return json.dumps(export_data, indent=2, ensure_ascii=False)


def export_to_markdown(
    conversation_history: List[Dict[str, Any]],
    model_name: str,
    system_prompt: str
) -> str:
    """
    Export conversation history to human-readable Markdown.

    Args:
        conversation_history: List of conversation entries with user/assistant messages
        model_name: Name of the model used for generation
        system_prompt: System prompt used in the conversation

    Returns:
        Markdown-formatted string with headers, exchanges, and metadata

    Example:
        >>> history = [{"user": "Hi", "assistant": "Hello!", "timestamp": "2025-12-03T10:00:00"}]
        >>> md_str = export_to_markdown(history, "deepseek-r1:latest", "You are helpful")
        >>> assert "# Ollama Chat Conversation Export" in md_str
        >>> assert "Hello!" in md_str
    """
    lines = []

    # Header
    lines.append("# Ollama Chat Conversation Export")
    lines.append("")
    lines.append("## Metadata")
    lines.append(f"- **Export Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **Model**: {model_name}")
    lines.append(f"- **Total Messages**: {len(conversation_history)}")
    lines.append("")
    lines.append("## System Prompt")
    lines.append(f"> {system_prompt}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Conversation")
    lines.append("")

    # Messages
    for i, entry in enumerate(conversation_history, 1):
        timestamp = entry.get('timestamp', 'N/A')
        user_msg = entry.get('user', '')
        assistant_msg = entry.get('assistant', '')
        params = entry.get('parameters', {})

        lines.append(f"### Exchange {i}")
        if timestamp != 'N/A':
            lines.append(f"*{timestamp}*")
        lines.append("")
        lines.append("**User:**")
        lines.append(f"> {user_msg}")
        lines.append("")
        lines.append("**Assistant:**")
        lines.append(f"> {assistant_msg}")
        lines.append("")

        if params:
            lines.append(f"*Parameters: temp={params.get('temperature')}, "
                        f"top_p={params.get('top_p')}, top_k={params.get('top_k')}, "
                        f"max_tokens={params.get('max_tokens')}*")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def save_export_file(content: str, format_type: str) -> str:
    """
    Save exported content to file with timestamp.

    Args:
        content: The content to save (JSON or Markdown string)
        format_type: Format type ("json" or "markdown")

    Returns:
        Filename of the saved file

    Raises:
        IOError: If file cannot be written

    Example:
        >>> content = "# Test Export"
        >>> filename = save_export_file(content, "markdown")
        >>> assert filename.startswith("ollama_conversation_")
        >>> assert filename.endswith(".md")
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    extension = "json" if format_type == "json" else "md"
    filename = f"ollama_conversation_{timestamp}.{extension}"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    return filename
