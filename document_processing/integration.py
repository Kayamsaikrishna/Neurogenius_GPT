import requests

def query_model(model_key, conversation=None, images=None, pdf_path=None, question=None):
    """
    Query the selected model using the Ollama server.
    :param model_key: The key representing the model to use (e.g., "granite_3_2_vision", "llama_3_2_vision", "gemma_3_vision").
    :param conversation: List of dictionaries containing the conversation (optional).
    :param images: List of image file paths (optional).
    :param pdf_path: Path to a PDF file (optional).
    :param question: Question or text input for the model.
    :return: The model's response as a string.
    """
    try:
        # Prepare the prompt
        prompt = question or ""
        if conversation:
            for message in conversation:
                prompt += f"\n{message['role'].capitalize()}: {message['content']}"

        # Prepare the request payload
        payload = {
            "model": model_key,
            "prompt": prompt,
            "stream": False
        }

        # Send the request to the Ollama server
        response = requests.post(
            "http://localhost:11434/api/generate",  # Ollama server endpoint
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json().get("response", "No response from model")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Connection error: {str(e)}"