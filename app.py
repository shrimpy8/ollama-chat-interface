"""
Ollama Chat Interface - Production-Ready Implementation

A robust chat interface for interacting with DeepSeek-R1 model via local Ollama server.
Features comprehensive error handling, structured logging, retry logic, and conversation memory.

This application showcases:
- Configuration management via YAML
- Structured logging with file and console handlers
- Retry logic with exponential backoff for network resilience
- Conversation history and context management
- Type-safe implementation with comprehensive error handling
- Production-ready code patterns

Author: Harsh
Repository: https://github.com/shrimpy8
"""

import json
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
import gradio as gr
from dotenv import load_dotenv
import os

# Import common utilities
from common import (
    setup_logging,
    load_config,
    api_request_with_retry,
    export_to_json,
    export_to_markdown,
    save_export_file
)

# Load environment variables (optional for Ollama)
try:
    load_dotenv()
except Exception as e:
    print(f"Note: Could not load .env file: {str(e)}")

# Load configuration
config = load_config()

# Configure structured logging
logging_config = config.get_logging_config()
logger = setup_logging(
    __name__,
    level=logging_config["level"],
    log_format=logging_config["format"],
    log_file=logging_config["file"],
    console=logging_config["console"],
    file_logging=logging_config["file_logging"]
)

# Global conversation history
conversation_history: List[Dict[str, str]] = []


def build_prompt_with_history(user_message: str) -> str:
    """
    Build a prompt that includes system prompt, conversation history, and current message.

    Args:
        user_message: The current user message

    Returns:
        Combined prompt with system prompt, conversation history, and current message

    Example:
        >>> prompt = build_prompt_with_history("What's the weather?")
        >>> # Returns: "System: You are helpful...\n\nPrevious conversation:\nUser: ...\nAssistant: ...\n\nCurrent: What's the weather?"
    """
    prompt_parts = []

    # 1. Add system prompt first (if configured)
    system_prompt = config.get_system_prompt()
    if system_prompt:
        prompt_parts.append(f"System: {system_prompt}")
        logger.debug(f"System prompt added: {system_prompt[:50]}...")

    # 2. Add conversation history if enabled
    if config.get_memory_enabled() and conversation_history:
        history_config = config.get_history_config()
        max_messages = history_config.get('max_messages', 20)
        recent_history = conversation_history[-max_messages:]

        if recent_history:
            prompt_parts.append("\nPrevious conversation:")
            for entry in recent_history:
                prompt_parts.append(f"User: {entry['user']}")
                prompt_parts.append(f"Assistant: {entry['assistant']}")

    # 3. Add current message
    prompt_parts.append(f"\nCurrent question: {user_message}")

    return "\n".join(prompt_parts)


def generate_response(
    user_input: str,
    history: List[Tuple[str, str]],
    temperature: float,
    top_p: float,
    top_k: int,
    max_tokens: int
) -> Tuple[List[Tuple[str, str]], str]:
    """
    Generate a response from the Ollama API with comprehensive error handling.

    This function:
    1. Validates user input
    2. Builds prompt with conversation history
    3. Makes API request with retry logic using provided parameters
    4. Handles errors gracefully
    5. Updates conversation history with parameters
    6. Returns formatted response

    Args:
        user_input: The user's message/prompt
        history: Gradio chat history (list of tuples)
        temperature: Temperature parameter for generation (0.0-1.0)
        top_p: Top-P parameter for nucleus sampling (0.0-1.0)
        top_k: Top-K parameter for vocabulary limit (1-100)
        max_tokens: Maximum tokens to generate (256-4096)

    Returns:
        Tuple of (updated_history, empty_string_for_input_clear)

    Raises:
        None - All exceptions are caught and returned as user-friendly error messages

    Example:
        >>> history, _ = generate_response("Hello", [], 0.7, 0.9, 40, 2048)
        >>> print(history)
        [("Hello", "Hi! How can I help you today?")]
    """
    global conversation_history

    try:
        # Input validation
        if not user_input or not isinstance(user_input, str):
            logger.warning(f"Invalid input received: {user_input}")
            error_msg = "Error: Please enter a valid message."
            history.append((user_input or "", error_msg))
            return history, ""

        if not user_input.strip():
            logger.warning("Empty input received")
            error_msg = "Error: Message cannot be empty."
            history.append((user_input, error_msg))
            return history, ""

        logger.info(f"Processing user input: {user_input[:100]}...")  # Log first 100 chars

        # Build prompt with conversation context
        full_prompt = build_prompt_with_history(user_input)

        # Prepare API request payload with UI-provided parameters
        payload = {
            "model": config.get_model_name(),
            "stream": False,
            "prompt": full_prompt,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": int(top_k),
                "num_predict": int(max_tokens)
            }
        }

        # Log parameters
        logger.debug(f"Parameters - temp: {temperature}, top_p: {top_p}, "
                     f"top_k: {top_k}, max_tokens: {max_tokens}")

        # Make API request with retry logic
        logger.info(f"Sending request to Ollama API: {config.get_full_api_url()}")

        response = api_request_with_retry(
            url=config.get_full_api_url(),
            method="POST",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=config.get_request_timeout()
        )

        # Parse response
        response_data = response.json()
        assistant_response = response_data.get("response", "")

        if not assistant_response:
            logger.warning("Empty response received from Ollama API")
            error_msg = "Error: Received empty response from the model."
            history.append((user_input, error_msg))
            return history, ""

        logger.info(f"Response generated successfully: {len(assistant_response)} characters")

        # Update conversation history with parameters
        if config.get_memory_enabled():
            conversation_history.append({
                "user": user_input,
                "assistant": assistant_response,
                "timestamp": datetime.now().isoformat(),
                "parameters": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "max_tokens": max_tokens
                }
            })

            # Trim history if it exceeds max_messages
            max_messages = config.get_history_config().get('max_messages', 20)
            if len(conversation_history) > max_messages:
                conversation_history = conversation_history[-max_messages:]
                logger.info(f"Trimmed conversation history to {max_messages} messages")

        # Update Gradio history
        history.append((user_input, assistant_response))

        return history, ""

    except json.JSONDecodeError as e:
        error_msg = "Error: Invalid response format from Ollama API."
        logger.error(f"JSON decode error: {str(e)}", exc_info=True)
        history.append((user_input, error_msg))
        return history, ""

    except ConnectionError as e:
        error_msg = "Error: Cannot connect to Ollama server. Please ensure Ollama is running (ollama serve)."
        logger.error(f"Connection error: {str(e)}", exc_info=True)
        history.append((user_input, error_msg))
        return history, ""

    except TimeoutError as e:
        error_msg = f"Error: Request timed out after {config.get_request_timeout()} seconds. Try a shorter prompt."
        logger.error(f"Timeout error: {str(e)}", exc_info=True)
        history.append((user_input, error_msg))
        return history, ""

    except KeyError as e:
        error_msg = f"Error: Missing expected data in API response: {str(e)}"
        logger.error(f"Key error: {str(e)}", exc_info=True)
        history.append((user_input, error_msg))
        return history, ""

    except Exception as e:
        error_msg = f"Error: An unexpected error occurred. Please check the logs."
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        history.append((user_input, error_msg))
        return history, ""


def clear_conversation() -> Tuple[List, str]:
    """
    Clear the conversation history.

    Returns:
        Tuple of (empty_history, empty_input)

    Example:
        >>> history, input_text = clear_conversation()
        >>> print(history)
        []
    """
    global conversation_history
    conversation_history = []
    logger.info("Conversation history cleared by user")
    return [], ""


def export_conversation(
    history: List[Tuple[str, str]],
    format_type: str = "markdown"
) -> str:
    """
    Export conversation to downloadable file.

    Args:
        history: Gradio chat history (not used directly, uses global conversation_history)
        format_type: Export format ("json" or "markdown")

    Returns:
        Filepath of the exported file, or empty string on error

    Example:
        >>> filepath = export_conversation([], "json")
        >>> assert filepath.endswith(".json")
    """
    try:
        model_name = config.get_model_name()
        system_prompt = config.get_system_prompt()

        if format_type == "json":
            content = export_to_json(conversation_history, model_name, system_prompt)
        else:
            content = export_to_markdown(conversation_history, model_name, system_prompt)

        filepath = save_export_file(content, format_type)
        logger.info(f"Conversation exported to {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Error exporting conversation: {str(e)}", exc_info=True)
        return ""


def generate_response_with_status(
    user_input: str,
    history: List[Tuple[str, str]],
    temperature: float,
    top_p: float,
    top_k: int,
    max_tokens: int,
    progress=gr.Progress()
) -> Tuple[List[Tuple[str, str]], str]:
    """
    Wrapper for generate_response with visual status indicator.

    Args:
        user_input: The user's message/prompt
        history: Gradio chat history (list of tuples)
        temperature: Temperature parameter for generation (0.0-1.0)
        top_p: Top-P parameter for nucleus sampling (0.0-1.0)
        top_k: Top-K parameter for vocabulary limit (1-100)
        max_tokens: Maximum tokens to generate (256-4096)
        progress: Gradio Progress component for status updates

    Returns:
        Tuple of (updated_history, empty_string_for_input_clear)

    Example:
        >>> history, _ = generate_response_with_status("Hello", [], 0.7, 0.9, 40, 2048)
        >>> print(history)
        [("Hello", "Hi! How can I help you today?")]
    """
    try:
        progress(0, desc="🤔 Thinking...")
        progress(0.3, desc="⏳ Generating response...")

        result = generate_response(
            user_input, history, temperature, top_p, top_k, max_tokens
        )

        progress(1.0, desc="✅ Complete!")
        return result

    except Exception as e:
        logger.error(f"Error in status wrapper: {str(e)}", exc_info=True)
        # Fallback to non-status generation
        return generate_response(
            user_input, history, temperature, top_p, top_k, max_tokens
        )


def create_ui() -> gr.Blocks:
    """
    Create and configure the Gradio user interface.

    Builds a production-ready Gradio interface with:
    - Chat interface with message history
    - Input textbox with configurable placeholder
    - Submit and clear buttons
    - Responsive layout
    - Configuration from YAML

    Returns:
        Configured Gradio Blocks interface ready to launch

    Raises:
        Exception: If UI creation fails (logged and re-raised)

    Example:
        >>> ui = create_ui()
        >>> ui.launch()
    """
    try:
        logger.info("Creating Gradio UI")

        # Get UI configuration
        input_config = config.get_input_config()
        output_config = config.get_output_config()

        # Create custom CSS for better styling with larger fonts and darker borders
        custom_css = """
        .gradio-container {
            font-family: 'Arial', sans-serif;
            font-size: 16px !important;
        }
        /* Darker borders throughout */
        .border, [class*="border"] {
            border-color: #bbb !important;
        }
        input, textarea, select {
            border: 2px solid #ccc !important;
        }
        input:focus, textarea:focus, select:focus {
            border-color: #2196F3 !important;
        }
        .message-box {
            border-radius: 8px;
            font-size: 16px !important;
            border: 2px solid #ddd !important;
        }
        /* Conversation badge with background */
        .chatbot .label-wrap {
            background-color: #2196F3 !important;
            color: white !important;
            padding: 5px 12px !important;
            border-radius: 5px !important;
            font-weight: 600 !important;
        }
        .instructions-callout {
            background-color: #e8f4fd;
            border-left: 4px solid #2196F3;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            font-size: 15px !important;
            border: 1px solid #b3d9f7 !important;
        }
        .instructions-callout h3 {
            font-size: 18px !important;
        }
        .instructions-callout li {
            font-size: 15px !important;
            margin-bottom: 5px;
        }
        /* Example questions styling */
        .example-questions {
            margin: 15px 0;
            padding: 12px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border: 2px solid #ddd;
        }
        .example-questions h4 {
            margin: 0 0 10px 0;
            font-size: 16px !important;
            color: #333;
        }
        /* Parameter guidance styling */
        .param-guidance {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border: 2px solid #ddd;
        }
        .param-guidance ul {
            list-style-type: disc;
            padding-left: 25px;
            margin: 10px 0;
        }
        .param-guidance li {
            font-size: 13px !important;
            margin-bottom: 8px;
            line-height: 1.6;
        }
        .param-guidance li::marker {
            font-size: 18px !important;
            color: #2196F3;
        }
        .param-col {
            padding: 0 10px;
        }
        /* Slider controls - increase height and width for better value visibility */
        .slider-container input[type="range"] {
            height: 8px !important;
        }
        .slider-container input[type="number"] {
            height: 48px !important;
            min-height: 48px !important;
            min-width: 120px !important;
            width: 120px !important;
            font-size: 14px !important;
            padding: 1px 5px 22px 5px !important;
            line-height: 1.2 !important;
            box-sizing: border-box !important;
            vertical-align: middle !important;
            display: block !important;
        }
        /* Target Gradio's slider number input specifically */
        input[type="number"].svelte-number-input {
            min-width: 120px !important;
            width: 120px !important;
            height: 48px !important;
            min-height: 48px !important;
            font-size: 14px !important;
            padding: 1px 5px 23px 5px !important;
            line-height: 1.2 !important;
            vertical-align: middle !important;
            display: block !important;
        }
        .slider-container .info {
            min-height: 28px !important;
            font-size: 14px !important;
        }
        .question-chip {
            display: inline-block;
            background-color: #fff;
            border: 2px solid #2196F3;
            color: #2196F3;
            padding: 8px 14px;
            margin: 5px 5px 5px 0;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px !important;
            transition: all 0.2s;
        }
        .question-chip:hover {
            background-color: #2196F3;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        /* Increase input/textarea font sizes */
        textarea, input {
            font-size: 16px !important;
            border: 2px solid #ccc !important;
        }
        /* Increase button font sizes */
        button {
            font-size: 16px !important;
            border: 2px solid transparent !important;
        }
        /* Increase label font sizes */
        label {
            font-size: 15px !important;
        }
        /* Increase markdown text sizes */
        .markdown-text, .prose {
            font-size: 16px !important;
        }
        /* Increase chat message font size */
        .message {
            font-size: 16px !important;
        }
        /* Increase slider labels */
        .slider-label {
            font-size: 15px !important;
        }
        /* Accordion borders */
        .accordion {
            border: 2px solid #ddd !important;
        }
        """

        # Create the Gradio interface
        with gr.Blocks(
            title=config.get_ui_title(),
            theme=config.get_ui_theme(),
            css=custom_css
        ) as demo:
            # 2-Column Layout
            with gr.Row():
                # LEFT COLUMN - Conversation Display (70% width)
                with gr.Column(scale=7):
                    chatbot = gr.Chatbot(
                        label="Conversation",
                        height=630,  # Increased by 5% (600 -> 630)
                        show_label=True,
                        elem_classes=["message-box"],
                        type="tuples"
                    )

                    # Example Questions - 3 Column Layout underneath conversation
                    gr.Markdown("### 💡 Try these example questions:")
                    with gr.Row():
                        # Column 1: AI Product Management
                        with gr.Column(scale=1):
                            gr.HTML("""
                            <div class="example-questions">
                                <h4 style="text-align: center; margin-bottom: 12px;">🤖 AI Product Management</h4>
                                <span class="question-chip" onclick="document.querySelector('textarea').value='How do I prioritize AI features in a product roadmap?'; document.querySelector('textarea').dispatchEvent(new Event('input', {bubbles: true}));">How do I prioritize AI features in a product roadmap?</span>
                                <span class="question-chip" onclick="document.querySelector('textarea').value='What are key metrics for measuring AI product success?'; document.querySelector('textarea').dispatchEvent(new Event('input', {bubbles: true}));">What are key metrics for measuring AI product success?</span>
                            </div>
                            """)

                        # Column 2: Environment
                        with gr.Column(scale=1):
                            gr.HTML("""
                            <div class="example-questions">
                                <h4 style="text-align: center; margin-bottom: 12px;">🌍 Environment</h4>
                                <span class="question-chip" onclick="document.querySelector('textarea').value='What are the most effective ways to reduce carbon footprint?'; document.querySelector('textarea').dispatchEvent(new Event('input', {bubbles: true}));">What are the most effective ways to reduce carbon footprint?</span>
                                <span class="question-chip" onclick="document.querySelector('textarea').value='How does renewable energy compare to traditional energy sources?'; document.querySelector('textarea').dispatchEvent(new Event('input', {bubbles: true}));">How does renewable energy compare to traditional energy sources?</span>
                            </div>
                            """)

                        # Column 3: Technology Trends
                        with gr.Column(scale=1):
                            gr.HTML("""
                            <div class="example-questions">
                                <h4 style="text-align: center; margin-bottom: 12px;">📱 Current Technology Trends</h4>
                                <span class="question-chip" onclick="document.querySelector('textarea').value='What are the latest trends in edge computing?'; document.querySelector('textarea').dispatchEvent(new Event('input', {bubbles: true}));">What are the latest trends in edge computing?</span>
                                <span class="question-chip" onclick="document.querySelector('textarea').value='How is quantum computing affecting cryptography?'; document.querySelector('textarea').dispatchEvent(new Event('input', {bubbles: true}));">How is quantum computing affecting cryptography?</span>
                            </div>
                            """)

                    # Advanced Settings Accordion (moved to left column for better visibility)
                    with gr.Accordion("⚙️ Advanced Settings", open=False):
                        # Parameter Guidance in 2-column layout
                        gr.HTML("""
                        <div class="param-guidance">
                            <h3 style="margin-top: 0; margin-bottom: 12px; font-size: 15px;">📖 Parameter Guidance</h3>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                <div class="param-col">
                                    <ul>
                                        <li><strong>Temperature</strong>: Controls creativity (0.0 = deterministic, 1.0 = creative)</li>
                                        <li><strong>Top-P</strong>: Nucleus sampling (0.0-1.0, higher = more diverse)</li>
                                    </ul>
                                </div>
                                <div class="param-col">
                                    <ul>
                                        <li><strong>Top-K</strong>: Vocabulary limit (1-100, higher = more variety)</li>
                                        <li><strong>Max Tokens</strong>: Maximum response length (256-4096)</li>
                                    </ul>
                                </div>
                            </div>
                            <p style="margin: 10px 0 0 0; font-style: italic; font-size: 12px; color: #666;">
                                Defaults from config.yaml. Changes apply to current session only.
                            </p>
                        </div>
                        """)

                        model_params = config.get_model_parameters()

                        # 2-Column Layout for sliders
                        with gr.Row():
                            with gr.Column(scale=1):
                                temperature_slider = gr.Slider(
                                    minimum=0.0, maximum=1.0,
                                    value=model_params.get('temperature', 0.7),
                                    step=0.05, label="Temperature",
                                    info=f"Default: {model_params.get('temperature', 0.7)}",
                                    elem_classes=["slider-container"]
                                )
                                top_p_slider = gr.Slider(
                                    minimum=0.0, maximum=1.0,
                                    value=model_params.get('top_p', 0.9),
                                    step=0.05, label="Top-P",
                                    info=f"Default: {model_params.get('top_p', 0.9)}",
                                    elem_classes=["slider-container"]
                                )

                            with gr.Column(scale=1):
                                top_k_slider = gr.Slider(
                                    minimum=1, maximum=100,
                                    value=model_params.get('top_k', 40),
                                    step=1, label="Top-K",
                                    info=f"Default: {model_params.get('top_k', 40)}",
                                    elem_classes=["slider-container"]
                                )
                                max_tokens_slider = gr.Slider(
                                    minimum=256, maximum=4096,
                                    value=model_params.get('num_predict', 2048),
                                    step=256, label="Max Tokens",
                                    info=f"Default: {model_params.get('num_predict', 2048)}",
                                    elem_classes=["slider-container"]
                                )

                # RIGHT COLUMN - All Controls (30% width)
                with gr.Column(scale=3):
                    # Title and Description
                    gr.Markdown(f"# {config.get_ui_title()}")
                    gr.Markdown(f"*{config.get_ui_description()}*")
                    gr.Markdown(f"**Model**: {config.get_model_name()} | **Temp**: {config.get_temperature()}")

                    # Instructions Callout (moved up)
                    gr.HTML("""
                    <div class="instructions-callout">
                        <h3 style="margin-top: 0;">📋 Instructions</h3>
                        <ul style="margin-bottom: 0;">
                            <li>Type your message and click <strong>Send</strong> or press <strong>Enter</strong></li>
                            <li>Use <strong>Clear</strong> to reset the conversation</li>
                            <li>Ensure Ollama is running: <code>ollama serve</code></li>
                            <li>Model responses may take a few seconds</li>
                        </ul>
                    </div>
                    """)

                    # Input Textbox
                    user_input = gr.Textbox(
                        label="Your Message",
                        placeholder=input_config.get('placeholder', 'Type your message here...'),
                        lines=input_config.get('lines', 3),
                        max_lines=input_config.get('max_lines', 10),
                        show_label=True
                    )

                    # Send and Clear Buttons
                    with gr.Row():
                        submit_btn = gr.Button("Send", variant="primary", size="lg")
                        clear_btn = gr.Button("Clear", variant="secondary", size="lg")

                    # Export Controls (at bottom of right column)
                    gr.Markdown("---")  # Separator line
                    gr.Markdown("### 📤 Export Conversation")
                    export_format = gr.Radio(
                        choices=["markdown", "json"],
                        value="markdown",
                        label="Export Format",
                        info="Choose your preferred export format"
                    )
                    export_btn = gr.Button("Export Conversation", variant="secondary", size="lg")
                    export_file = gr.File(label="Download")

            # Event handlers
            submit_btn.click(
                fn=generate_response_with_status,
                inputs=[user_input, chatbot, temperature_slider, top_p_slider,
                        top_k_slider, max_tokens_slider],
                outputs=[chatbot, user_input],
                show_progress=True
            )

            user_input.submit(
                fn=generate_response_with_status,
                inputs=[user_input, chatbot, temperature_slider, top_p_slider,
                        top_k_slider, max_tokens_slider],
                outputs=[chatbot, user_input],
                show_progress=True
            )

            clear_btn.click(
                fn=clear_conversation,
                inputs=None,
                outputs=[chatbot, user_input]
            )

            export_btn.click(
                fn=export_conversation,
                inputs=[chatbot, export_format],
                outputs=export_file
            )

        logger.info("Gradio UI created successfully")
        return demo

    except Exception as e:
        logger.error(f"Error creating UI: {str(e)}", exc_info=True)
        raise


# Launch the application
if __name__ == "__main__":
    try:
        logger.info("=" * 60)
        logger.info("Starting Ollama Chat Interface")
        logger.info(f"Model: {config.get_model_name()}")
        logger.info(f"API URL: {config.get_full_api_url()}")
        logger.info(f"Temperature: {config.get_temperature()}")
        logger.info(f"Conversation Memory: {'Enabled' if config.get_memory_enabled() else 'Disabled'}")
        logger.info(f"Max History: {config.get_history_config().get('max_messages', 20)} messages")
        logger.info("=" * 60)

        # Get server configuration
        server_config = config.get_server_config()

        # Create and launch UI
        ui = create_ui()
        ui.launch(
            server_name=server_config.get('host', '127.0.0.1'),
            server_port=server_config.get('port', 7860),
            share=config.get_ui_share()
        )

    except Exception as e:
        logger.critical(f"Failed to launch application: {str(e)}", exc_info=True)
        print(f"\n{'='*60}")
        print(f"CRITICAL ERROR: {str(e)}")
        print(f"{'='*60}")
        print("Please check ollama_chat.log for details")
        print("\nTroubleshooting:")
        print("1. Ensure Ollama is installed and running: ollama serve")
        print("2. Verify the model is available: ollama list")
        print(f"3. Pull the model if needed: ollama pull {config.get_model_name()}")
        print("4. Check config.yaml for correct settings")
        print(f"{'='*60}\n")
