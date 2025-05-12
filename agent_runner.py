import subprocess
import json
import os
import logging
import signal
import sys
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CONFIG_PATH = "agents/config.json"
running_processes: Dict[str, subprocess.Popen] = {}

def load_agent_configs() -> List[Dict]:
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)["agents"]
    except Exception as e:
        logger.error(f"Failed to load agent configs: {e}")
        return []

def start_agent(agent_config: Dict):
    agent_name = agent_config["name"]
    uds_path = agent_config["uds_path"]
    agent_file = agent_config["file"]
    
    # Remove existing socket if it exists
    if os.path.exists(uds_path):
        try:
            os.remove(uds_path)
        except Exception as e:
            logger.error(f"Failed to remove existing socket for {agent_name}: {e}")
            return
    
    # Start the agent process
    try:
        process = subprocess.Popen([
            "uvicorn",
            f"agents.{agent_file.replace('.py', '')}:app",
            "--uds", uds_path,
            "--log-level", "info"
        ])
        running_processes[agent_name] = process
        logger.info(f"Started agent: {agent_name}")
    except Exception as e:
        logger.error(f"Failed to start agent {agent_name}: {e}")

def stop_all_agents():
    for agent_name, process in running_processes.items():
        try:
            process.terminate()
            process.wait(timeout=5)
            logger.info(f"Stopped agent: {agent_name}")
        except Exception as e:
            logger.error(f"Failed to stop agent {agent_name}: {e}")
            try:
                process.kill()
            except:
                pass

def signal_handler(signum, frame):
    logger.info("Received shutdown signal")
    stop_all_agents()
    sys.exit(0)

def main():
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load and start agents
    agents = load_agent_configs()
    for agent in agents:
        start_agent(agent)
    
    # Keep the script running
    try:
        while True:
            # Check if any processes have died
            for agent_name, process in list(running_processes.items()):
                if process.poll() is not None:
                    logger.error(f"Agent {agent_name} died unexpectedly")
                    del running_processes[agent_name]
                    # Restart the agent
                    agent_config = next((a for a in agents if a["name"] == agent_name), None)
                    if agent_config:
                        start_agent(agent_config)
            
            # Sleep for a bit
            signal.pause()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        stop_all_agents()

if __name__ == "__main__":
    main() 