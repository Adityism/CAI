from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response, stream_with_context
import requests
import os
import logging
import time
import json
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = "llama3"  # Changed from llama3:latest to just llama3
MAX_RETRIES = 3  # Number of retries for API calls

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

# Configure connection pooling and retries
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[408, 429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(
    max_retries=retries,
    pool_connections=10,
    pool_maxsize=10,
    pool_block=False
)
session.mount('http://', adapter)
session.mount('https://', adapter)

# Increase default timeout for urllib3
urllib3.Timeout.DEFAULT_TIMEOUT = 300

def is_ollama_running():
    """Check if Ollama service is running"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            logger.info("Ollama is running")
            logger.info(f"Available models: {response.json()}")
            return True
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama is not running: {e}")
        return False

def verify_model_exists():
    """Verify if the model exists and is ready"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            for model in models:
                if model.get('name') == MODEL_NAME:  # Exact match check
                    return True
        return False
    except Exception as e:
        logger.error(f"Error verifying model: {e}")
        return False

def query_deepseek(prompt):
    """Query the Llama 3 model through Ollama's local API"""
    try:
        if not is_ollama_running():
            return "Error: Ollama is not running. Please start it with 'ollama serve' command."

        logger.info(f"Sending request to model: {MODEL_NAME}")
        
        # Format for Ollama's /api/generate endpoint
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "system": "You are a helpful AI assistant.",
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 1024
            }
        }

        # Use /api/generate endpoint directly
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=30
        )
        
        logger.info(f"Response status: {response.status_code}")
        logger.debug(f"Response content: {response.text[:200]}")
        
        if response.status_code != 200:
            logger.error(f"Ollama API error: {response.status_code} - {response.text}")
            return f"Error: Ollama API returned status {response.status_code}"

        result = response.json()
        
        # Handle response from /api/generate
        if 'response' in result:
            return result['response'].strip()
        elif 'message' in result and result['message'].get('content'):
            return result['message']['content'].strip()
        else:
            logger.error(f"Unexpected response format: {result}")
            # Try one more time with fallback format
            fallback_payload = {
                "model": MODEL_NAME,
                "prompt": prompt
            }
            fallback_response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=fallback_payload,
                timeout=30
            )
            fallback_result = fallback_response.json()
            if 'response' in fallback_result:
                return fallback_result['response'].strip()
            return "Error: Could not generate response"

    except Exception as e:
        logger.exception("Error in query_deepseek")
        return f"Error: {str(e)}"

def stream_deepseek_response(prompt):
    """Stream responses from Ollama with Llama 3"""
    data = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True,
        "system": "You are a helpful AI assistant.",
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 1024
        }
    }
    
    try:
        with session.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=data,
            stream=True,
            timeout=(30, 300)
        ) as response:
            response.raise_for_status()
            buffer = ""
            
            for line in response.iter_lines():
                if line:
                    try:
                        decoded_line = json.loads(line.decode('utf-8'))
                        if 'response' in decoded_line:
                            buffer += decoded_line['response']
                        elif 'message' in decoded_line and decoded_line['message'].get('content'):
                            buffer += decoded_line['message']['content']
                            
                        # Break down buffer into words
                        while ' ' in buffer:
                            word, buffer = buffer.split(' ', 1)
                            yield f"data: {json.dumps({'token': word + ' '})}\n\n"
                            time.sleep(0.02)
                                
                    except json.JSONDecodeError:
                        continue
                        
            if buffer:
                yield f"data: {json.dumps({'token': buffer})}\n\n"
                
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@app.route('/')
def index():
    return render_template('caichat.html')

@app.route('/api/query', methods=['POST'])
def ai_query():
    try:
        if not request.is_json:
            logger.error("Request is not JSON")
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        if not data:
            logger.error("Empty request body")
            return jsonify({"error": "Request body is empty"}), 400

        prompt = data.get('prompt')
        if not prompt:
            logger.error("No prompt in request")
            return jsonify({"error": "prompt is required"}), 400

        logger.info(f"Processing prompt: {prompt[:50]}...")
        response_text = query_deepseek(prompt)
        
        if response_text.startswith("Error:"):
            error_msg = response_text[6:].strip()
            logger.error(f"Error from query_deepseek: {error_msg}")
            return jsonify({"error": error_msg}), 500
        
        return jsonify({"response": response_text})

    except Exception as e:
        logger.exception("Unexpected error in endpoint")
        return jsonify({"error": str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/health')
def health_check():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Set to port 5001 for testing
