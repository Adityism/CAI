import sys
import os
from check_ollama import check_ollama_ready
from app import app
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_ssl_files():
    """Ensure SSL certificate files exist"""
    ssl_dir = os.path.join(os.path.dirname(__file__), 'ssl')
    cert_path = os.path.join(ssl_dir, 'cert.pem')
    key_path = os.path.join(ssl_dir, 'key.pem')
    
    if not os.path.exists(ssl_dir):
        os.makedirs(ssl_dir)
    
    if not (os.path.exists(cert_path) and os.path.exists(key_path)):
        from OpenSSL import crypto
        
        # Generate key
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 2048)
        
        # Generate self-signed certificate
        cert = crypto.X509()
        cert.get_subject().C = "IN"
        cert.get_subject().ST = "Uttarakhand"
        cert.get_subject().L = "Dehradun"
        cert.get_subject().O = "UPES"
        cert.get_subject().OU = "Campus Connect AI"
        cert.get_subject().CN = "localhost"
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365*24*60*60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha256')
        
        # Save certificate
        with open(cert_path, "wb") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        
        # Save private key
        with open(key_path, "wb") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
            
    return cert_path, key_path

MODEL_NAME = os.getenv("MODEL_NAME", "llama3:latest")  # Set to a valid model name

def main():
    try:
        # Check if Ollama is running
        logger.info("Checking Ollama service...")
        
        try:
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code != 200:
                logger.error("Ollama is not responding correctly")
                logger.info("Please start Ollama with: ollama serve")
                return
            
            models = response.json().get('models', [])
            logger.info(f"Available models: {[m.get('name') for m in models]}")
            
            if not any(m.get('name') == MODEL_NAME for m in models):
                logger.error(f"Model {MODEL_NAME} not found")
                logger.info(f"Please install the model with: ollama pull {MODEL_NAME}")
                return
                
        except requests.exceptions.ConnectionError:
            logger.error("Could not connect to Ollama")
            logger.info("Please start Ollama with: ollama serve")
            return

        # Run the Flask app
        logger.info("Starting Flask server...")
        app.run(
            host='127.0.0.1',
            port=5001,
            debug=True
        )

    except Exception as e:
        logger.exception("Failed to start server")
        raise

if __name__ == "__main__":
    main()
