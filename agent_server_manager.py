import json
import subprocess
import logging
import threading
import time
import os
import signal
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CONFIG_PATH = "agents/config.json"
LOG_FILE = "agent_runner.log"
STOP_FILE = "agents/stop_signal.txt"  # File to signal stop

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
# Also log to console for easier debugging
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

# Store running agent file paths
running_agents = {}

def load_config():
    try:
        with open(CONFIG_PATH, "r") as file:
            return json.load(file)["agents"]
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return []

def run_agent(agent):
    file_path = os.path.join("agents", agent["file"])
    if file_path in running_agents:
        logging.info(f"Agent already running: {file_path}")
        return
    logging.info(f"Starting agent: {agent['name']} ({file_path})")
    proc = subprocess.Popen(["python", file_path])
    running_agents[file_path] = proc

def launch_all_agents(agents):
    for agent in agents:
        run_agent(agent)

class ConfigChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # Convert both paths to absolute paths for comparison
        abs_config_path = os.path.abspath(CONFIG_PATH)
        abs_event_path = os.path.abspath(event.src_path)
        
        logging.info(f"File change detected: {abs_event_path}")
        logging.info(f"Looking for changes in: {abs_config_path}")
        
        if abs_event_path == abs_config_path:
            logging.info("Config file change detected!")
            try:
                current_agents = load_config()
                current_files = {os.path.join("agents", agent["file"]) for agent in current_agents}
                existing_files = set(running_agents.keys())

                new_files = current_files - existing_files
                logging.info(f"New files to start: {new_files}")
                
                for agent in current_agents:
                    if os.path.join("agents", agent["file"]) in new_files:
                        run_agent(agent)
            except Exception as e:
                logging.error(f"Failed to reload config: {e}")

def check_stop_signal():
    """Check if stop signal file exists and remove it if found"""
    if os.path.exists(STOP_FILE):
        try:
            os.remove(STOP_FILE)
            return True
        except Exception as e:
            logging.error(f"Error removing stop signal file: {e}")
    return False

def watch_config():
    observer = Observer()
    handler = ConfigChangeHandler()
    observer.schedule(handler, path="agents", recursive=False)
    observer.start()
    logging.info(f"Started watchdog to monitor {CONFIG_PATH}")
    try:
        while True:
            if check_stop_signal():
                logging.info("Stop signal detected")
                shutdown_agents()
                break
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    finally:
        observer.stop()
        observer.join()

def shutdown_agents():
    logging.info("Shutting down all running agents...")
    for file_path, process in running_agents.items():
        try:
            logging.info(f"Terminating agent: {file_path}")
            process.terminate()
            process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
        except subprocess.TimeoutExpired:
            logging.warning(f"Force killing agent: {file_path}")
            process.kill()
        except Exception as e:
            logging.error(f"Error shutting down agent {file_path}: {e}")
    running_agents.clear()
    logging.info("All agents have been shut down")

def signal_handler(signum, frame):
    logging.info(f"Received signal {signum}")
    shutdown_agents()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    agents = load_config()
    launch_all_agents(agents)
    try:
        watch_config()
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt")
        shutdown_agents()
