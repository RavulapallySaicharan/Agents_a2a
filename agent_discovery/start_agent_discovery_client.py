from python_a2a.discovery import DiscoveryClient
import dotenv
import os
import time
import logging
import requests
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

dotenv.load_dotenv()

registry_port = os.getenv("DISCOVERY_PORT", "8000")
registry_url = f"http://localhost:{registry_port}"

def check_registry_health(max_retries=3):
    """Check if registry server is healthy with retries."""
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{registry_url}/health", timeout=5)
            if response.status_code == 200:
                return True
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                logger.warning(f"Registry health check attempt {attempt + 1} failed: {str(e)}")
                time.sleep(2)
            else:
                logger.error(f"Registry server health check failed after {max_retries} attempts: {str(e)}")
    return False

def ensure_discovery_engine_running():
    """Ensure the discovery engine is running, start it if necessary."""
    if check_registry_health():
        return True

    logger.info("Discovery engine not running. Attempting to start it...")
    try:
        discovery_engine_path = Path("agent_discovery/start_agent_discovery_engine.py")
        if not discovery_engine_path.exists():
            logger.error("Discovery engine script not found")
            return False

        import subprocess
        process = subprocess.Popen(
            [sys.executable, str(discovery_engine_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait for the discovery engine to start
        max_retries = 10
        for attempt in range(max_retries):
            if check_registry_health(max_retries=1):
                logger.info("Discovery engine started successfully")
                return True
            time.sleep(2)

        # If we get here, the engine didn't start properly
        stdout, stderr = process.communicate()
        logger.error(f"Failed to start discovery engine. Output: {stdout}\nError: {stderr}")
        return False

    except Exception as e:
        logger.error(f"Error starting discovery engine: {str(e)}")
        return False

def discover_with_retries(client, max_retries=3):
    """Discover agents with retries."""
    for attempt in range(max_retries):
        try:
            agents = client.discover()
            return agents
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Discovery attempt {attempt + 1} failed: {str(e)}")
                time.sleep(2)
            else:
                logger.error(f"Failed to discover agents after {max_retries} attempts: {str(e)}")
                raise

def main():
    # First ensure discovery engine is running
    if not ensure_discovery_engine_running():
        logger.error("Could not start discovery engine. Please check the logs for details.")
        return

    # Create a discovery client
    client = DiscoveryClient(agent_card=None)
    client.add_registry(registry_url)

    try:
        # Discover all agents with retries
        agents = discover_with_retries(client)
        print(f"\nDiscovered {len(agents)} agents:")
        for agent in agents:
            print(f"- {agent.name} at {agent.url}")
            print(f"  Capabilities: {agent.capabilities}")
    except Exception as e:
        logger.error(f"Failed to discover agents: {str(e)}")

if __name__ == "__main__":
    main()