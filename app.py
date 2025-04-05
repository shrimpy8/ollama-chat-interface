# Import required libraries
import requests  # For making HTTP requests to the Ollama API
import json  # For parsing and formatting JSON data
import gradio as gr  # For creating the web interface

# Define the Ollama API endpoint
# This is the URL where Ollama is running and exposing its API
url = "http://localhost:11434/api/generate"

# Define the model to use in one place so it can be referenced elsewhere
MODEL_NAME = "deepseek-r1:latest"

# Set request headers
# The Content-Type header tells the server we're sending JSON data
headers = {
    'Content-Type': 'application/json'
}

def generate_response(prompt):
    """
    Send a prompt to the Ollama API and get a response from the model.
    
    Args:
        prompt (str): The user's input text to send to the model
        
    Returns:
        str: The model's generated response text
        
    This function:
    1. Prepares the request data with the model name and prompt
    2. Makes a POST request to the Ollama API
    3. Parses the JSON response
    4. Returns the model's generated text or an error message
    """
    # Prepare the request data
    data = {
        "model": MODEL_NAME,  # Specify which model to use
        "stream": False,  # Disable streaming for simpler processing
        "prompt": prompt  # The user's input text
    }

    # Send the POST request to the Ollama API
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the response text as JSON
        response_txt = response.text
        data = json.loads(response_txt)
        
        # Extract the actual model response from the JSON
        actual_response = data["response"]
        return actual_response
    else:
        # If there was an error, print it and return an error message
        print("Error:", response.status_code, response.text)
        return f"Error: Failed to get response from model (Status code: {response.status_code})"

# Create the Gradio interface
# This sets up a simple web UI with a text input and text output
iface = gr.Interface(
    fn=generate_response,  # The function to call when input is submitted
    inputs=["text"],       # The input type (text field)
    outputs=["text"],      # The output type (text field)
    title=f"{MODEL_NAME} AI Chat Interface",  # Use the model name in the title
    description=f"Enter your prompt below to get a response from the {MODEL_NAME} model"  # Use the model name in the description
)

# Launch the web interface when this script is run directly
if __name__ == "__main__":
    iface.launch()  # Start the Gradio web server