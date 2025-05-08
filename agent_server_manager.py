import os
import json
import time
import subprocess
import sys
import logging
import socket
import requests
import threading
from pathlib import Path
from typing import Dict, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from python_a2a import AgentCard, A2AServer, enable_discovery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigFileHandler(FileSystemEventHandler):
    """Handler for config.json file changes."""
    def __init__(self, agent_manager):
        self.agent_manager = agent_manager
        self.last_modified = time.time()
        self.cooldown = 1  # Cooldown period in seconds

    def on_modified(self, event):
        if event.src_path.endswith('config.json'):
            current_time = time.time()
            if current_time - self.last_modified > self.cooldown:
                self.last_modified = current_time
                logger.info("Config file modified, updating agent servers...")
                self.agent_manager.update_agents()

class AgentServerManager:
    def __init__(self):
        self.config_path = Path("agents/config.json")
        self.processes: Dict[str, Optional[subprocess.Popen]] = {}
        self.running_agents: Set[str] = set()
        self.registry_port = os.getenv("DISCOVERY_PORT", "8000")
        self.registry_url = f"http://localhost:{self.registry_port}"
        self.discovery_process: Optional[subprocess.Popen] = None
        self.registration_threads: Dict[str, threading.Thread] = {}
        self.stop_registration = threading.Event()
        self._validate_credentials()
        self._ensure_discovery_engine()

    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return False
            except socket.error:
                return True

    def _is_discovery_engine_running(self) -> bool:
        """Check if the discovery engine is running."""
        try:
            response = requests.get(f"{self.registry_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def _start_discovery_engine(self) -> bool:
        """Start the agent discovery engine if it's not running."""
        if self._is_discovery_engine_running():
            logger.info("Discovery engine is already running")
            return True

        if self._is_port_in_use(int(self.registry_port)):
            logger.error(f"Port {self.registry_port} is already in use")
            return False

        try:
            logger.info("Starting agent discovery engine...")
            # Kill any existing discovery engine process
            if self.discovery_process:
                try:
                    self.discovery_process.terminate()
                    self.discovery_process.wait(timeout=5)
                except:
                    pass

            # Start new discovery engine process
            self.discovery_process = subprocess.Popen(
                [sys.executable, "agent_discovery/start_agent_discovery_engine.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for the discovery engine to start with increased timeout
            max_retries = 15
            retry_count = 0
            while retry_count < max_retries:
                if self._is_discovery_engine_running():
                    logger.info("Discovery engine started successfully")
                    return True
                time.sleep(2)  # Increased wait time between retries
                retry_count += 1
                
                # Check if process is still running
                if self.discovery_process.poll() is not None:
                    stdout, stderr = self.discovery_process.communicate()
                    logger.error(f"Discovery engine failed to start. Output: {stdout}\nError: {stderr}")
                    return False
            
            logger.error("Failed to start discovery engine - timeout")
            return False
        except Exception as e:
            logger.error(f"Error starting discovery engine: {str(e)}")
            return False

    def _ensure_discovery_engine(self) -> None:
        """Ensure the discovery engine is running."""
        if not self._start_discovery_engine():
            raise Exception("Failed to start discovery engine. Please check the logs for details.")

    def _validate_credentials(self) -> None:
        """Validate that either OpenAI or Azure OpenAI credentials are set."""
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        has_azure = (bool(os.getenv("AZURE_OPENAI_API_KEY")) and 
                    bool(os.getenv("AZURE_OPENAI_ENDPOINT")) and 
                    bool(os.getenv("AZURE_OPENAI_API_VERSION")))
        
        if not (has_openai or has_azure):
            raise Exception("No valid API credentials found")
        
        logger.info("Using OpenAI credentials" if has_openai else "Using Azure OpenAI credentials")

    def start_agent(self, agent_info: dict) -> Optional[subprocess.Popen]:
        """Start an agent in a new process."""
        agent_name = agent_info["name"]
        agent_file = agent_info["file"]
        port = str(agent_info["port"])

        if agent_name in self.running_agents:
            logger.info(f"{agent_name} is already running")
            return self.processes.get(agent_name)

        logger.info(f"Starting {agent_name} Agent...")
        try:
            process = subprocess.Popen(
                [sys.executable, f"agents/{agent_file}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes[agent_name] = process
            self.running_agents.add(agent_name)
            self.register_agent(agent_info)
            return process
        except Exception as e:
            logger.error(f"Error starting {agent_name} Agent: {str(e)}")
            return None

    def register_agent(self, agent_info: dict) -> None:
        """Register an agent with the discovery service."""
        def periodic_registration():
            while not self.stop_registration.is_set():
                try:
                    agent_card = AgentCard(
                        name=agent_info["name"],
                        description=agent_info["description"],
                        url=f"http://localhost:{agent_info['port']}",
                        version=agent_info["version"],
                        capabilities={
                            "google_a2a_compatible": True
                        }
                    )
                    agent = A2AServer(agent_card=agent_card)
                    enable_discovery(agent, registry_url=self.registry_url)
                    logger.info(f"Successfully registered {agent_info['name']} agent")
                except Exception as e:
                    logger.error(f"Failed to register {agent_info['name']} agent: {str(e)}")
                time.sleep(30)  # Re-register every 30 seconds

        # Start periodic registration in a separate thread
        registration_thread = threading.Thread(target=periodic_registration, daemon=True)
        registration_thread.start()
        self.registration_threads[agent_info["name"]] = registration_thread

    def stop_agent(self, agent_name: str) -> None:
        """Stop a running agent."""
        if agent_name in self.processes:
            process = self.processes[agent_name]
            if process:
                process.terminate()
                process.wait()
            del self.processes[agent_name]
            self.running_agents.remove(agent_name)
            logger.info(f"Stopped {agent_name} agent")

    def load_config(self) -> dict:
        """Load the current configuration from config.json."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config file: {str(e)}")
            return {"agents": [], "server_config": {}}

    def update_agents(self) -> None:
        """Update running agents based on config.json."""
        config = self.load_config()
        current_agents = {agent["name"] for agent in config["agents"]}
        
        # Stop agents that are no longer in config
        for agent_name in list(self.running_agents):
            if agent_name not in current_agents:
                self.stop_agent(agent_name)
        
        # Start new agents
        for agent_info in config["agents"]:
            if agent_info["name"] not in self.running_agents:
                self.start_agent(agent_info)

    def start_all_agents(self) -> None:
        """Start all agents defined in config.json."""
        config = self.load_config()
        for agent_info in config["agents"]:
            self.start_agent(agent_info)

    def stop_all_agents(self) -> None:
        """Stop all running agents."""
        self.stop_registration.set()  # Signal all registration threads to stop
        
        for agent_name in list(self.running_agents):
            self.stop_agent(agent_name)
        
        # Stop discovery engine if it's running
        if self.discovery_process:
            self.discovery_process.terminate()
            self.discovery_process.wait()
            logger.info("Stopped agent discovery engine")

    def run(self) -> None:
        """Run the agent server manager with file watching."""
        try:
            # Start all agents from config
            self.start_all_agents()
            
            # Set up file watching
            event_handler = ConfigFileHandler(self)
            observer = Observer()
            observer.schedule(event_handler, path=str(self.config_path.parent), recursive=False)
            observer.start()
            
            logger.info("Agent server manager started. Watching for config changes...")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
                self.stop_all_agents()
            
            observer.join()
            
        except Exception as e:
            logger.error(f"Error in agent server manager: {str(e)}")
            self.stop_all_agents()
            raise

def main():
    """Main function to run the agent server manager."""
    manager = AgentServerManager()
    manager.run()

if __name__ == "__main__":
    main() 