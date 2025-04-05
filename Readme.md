# Ollama Chat Interface

A simple web interface for interacting with Ollama AI models using Gradio.

## Overview

This application provides a user-friendly web interface for sending prompts to Ollama models and displaying their responses. It uses the Ollama API to communicate with locally running Ollama models.


## Features

- Clean, simple web interface for interacting with Ollama models
- Support for the DeepSeek-r1 model (easily configurable for other models)
- Error handling for API connection issues
- Responsive text input and output areas

## Requirements

- Python 3.6+
- Ollama running locally on port 11434
- The DeepSeek-r1 model installed in Ollama (or change the MODEL_NAME constant)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/shrimpy8/ollama-chat-interface.git
   cd ollama-chat-interface
   ```

2. Install the required dependencies:
   ```
   pip install gradio requests
   ```

3. Make sure Ollama is running with the required model:
   ```
   ollama run deepseek-r1:latest
   ```

## Usage

1. Start the application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:7860
   ```

3. Enter your prompt in the text field and press "Submit" to get a response from the model.

## Customization

### Changing the Model

To use a different model, modify the `MODEL_NAME` constant at the top of the script:

```python
MODEL_NAME = "deepseek-r1:latest"  # Change to your preferred model
```

Make sure the model is installed in your Ollama installation.

### Modifying the Interface

The interface can be customized by changing the Gradio parameters in the `gr.Interface` call.

## How It Works

1. The application connects to the Ollama API running on your local machine
2. When you submit a prompt, it sends a POST request to the Ollama API
3. The API returns the model's response, which is then displayed in the interface

## Troubleshooting

- **Error connecting to API**: Make sure Ollama is running on your machine
- **Model not found**: Ensure you've installed the model specified in the MODEL_NAME constant
- **Slow responses**: Large language models can take time to generate responses, especially on less powerful hardware

## License

[MIT License](LICENSE)

## Acknowledgments

- [Ollama](https://ollama.ai/) for making local LLMs accessible
- [Gradio](https://www.gradio.app/) for the simple web interface framework