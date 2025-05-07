from python_a2a.discovery import AgentRegistry, run_registry
import threading
import time
import os
import logging
import socket
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_port_available(port: int, host: str = 'localhost') -> bool:
    """Check if a port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except socket.error:
            return False

def start_registry(port: int = 8000) -> bool:
    """Start the registry server with proper error handling."""
    try:
        if not is_port_available(port):
            logger.error(f"Port {port} is not available for registry server")
            return False

        registry = AgentRegistry(
            name="A2A Registry Server",
            description="Central registry for agent discovery"
        )
        
        registry_thread = threading.Thread(
            target=lambda: run_registry(registry, host="localhost", port=port),
            daemon=True
        )
        registry_thread.start()
        logger.info(f"Started registry server on port {port}")
        return True
    except Exception as e:
        logger.error(f"Failed to start registry server: {e}")
        return False

def main():
    # Load environment variables
    load_dotenv()
    
    # Get registry port from environment or use default
    registry_port = int(os.getenv("DISCOVERY_PORT", "8000"))
    
    # Start registry server
    if not start_registry(registry_port):
        logger.error("Failed to start registry server")
        return
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")

if __name__ == "__main__":
    main()


