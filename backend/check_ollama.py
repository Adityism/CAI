import requests
import time
import subprocess
import sys
import platform
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_ollama_running():
    """Check if Ollama is running by making a request to its health endpoint"""
    try:
        # Try multiple endpoints to verify Ollama is running properly
        endpoints = [
            ("GET", "/api/tags"),
            ("GET", "/"),
            ("POST", "/api/generate")
        ]
        
        for method, endpoint in endpoints:
            try:
                url = f"http://localhost:11434{endpoint}"
                logger.info(f"Checking Ollama endpoint: {url}")
                
                if method == "GET":
                    response = requests.get(url, timeout=5)
                else:
                    response = requests.post(url, 
                                          json={"model": "deepseek", "prompt": "test"},
                                          timeout=5)
                                          
                if response.status_code == 200:
                    logger.info(f"Successfully connected to Ollama via {endpoint}")
                    return True
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to connect to {endpoint}: {e}")
                continue
                
        logger.error("Could not connect to any Ollama endpoint")
        return False
        
    except Exception as e:
        logger.error(f"Error checking Ollama status: {e}")
        return False

def start_ollama():
    """Attempt to start Ollama service"""
    system = platform.system().lower()
    
    try:
        if system == "darwin":  # macOS
            logger.info("Attempting to start Ollama on macOS...")
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
        elif system == "linux":
            logger.info("Attempting to start Ollama on Linux...")
            subprocess.Popen(["systemctl", "start", "ollama"], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
        else:
            logger.error(f"Unsupported operating system: {system}")
            return False
            
        # Wait for service to start
        for i in range(10):  # Try for 10 seconds
            logger.info(f"Waiting for Ollama to start (attempt {i+1}/10)...")
            if is_ollama_running():
                logger.info("Ollama service started successfully!")
                return True
            time.sleep(1)
            
        logger.error("Timed out waiting for Ollama to start")
        return False
        
    except Exception as e:
        logger.error(f"Failed to start Ollama: {e}")
        return False

def ensure_model_pulled():
    """Ensure the DeepSeek model is pulled"""
    try:
        # First check if model exists
        response = requests.get("http://localhost:11434/api/tags")
        models = response.json()
        
        if any(model.get('name') == 'deepseek' for model in models.get('models', [])):
            logger.info("DeepSeek model is already pulled")
            return True
            
        # If not, pull the model
        logger.info("Pulling DeepSeek model... this may take a while")
        response = requests.post("http://localhost:11434/api/pull", 
                               json={"name": "deepseek"},
                               timeout=600)  # 10 minute timeout for pull
        
        if response.status_code == 200:
            logger.info("DeepSeek model successfully pulled")
            return True
            
        logger.error(f"Failed to pull model: {response.text}")
        return False
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to pull model: {e}")
        return False

def check_ollama_ready():
    """Main function to ensure Ollama is running and model is ready"""
    if not is_ollama_running():
        logger.info("Ollama is not running. Attempting to start...")
        if not start_ollama():
            logger.error("Failed to start Ollama service")
            return False
    
    if not ensure_model_pulled():
        logger.error("Failed to ensure DeepSeek model is available")
        return False
        
    return True

if __name__ == "__main__":
    if check_ollama_ready():
        logger.info("Ollama is ready with DeepSeek model!")
        sys.exit(0)
    else:
        logger.error("Failed to prepare Ollama")
        sys.exit(1)
