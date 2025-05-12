import json
import subprocess
import logging
import threading
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CONFIG_PATH = "agents/config.json"
LOG_FILE = "agent_runner.log"

# Configure logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Store running agent file paths
running_agents = {}

def load_config():
    with open(CONFIG_PATH, "r") as file:
        return json.load(file)["agents"]

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
        if event.src_path.endswith(CONFIG_PATH):
            logging.info("Detected change in config.json. Checking for new agents...")
            try:
                current_agents = load_config()
                current_files = {agent["file"] for agent in current_agents}
                existing_files = set(running_agents.keys())

                new_files = current_files - existing_files
                for agent in current_agents:
                    if agent["file"] in new_files:
                        run_agent(agent)
            except Exception as e:
                logging.error(f"Failed to reload config: {e}")

def watch_config():
    observer = Observer()
    handler = ConfigChangeHandler()
    observer.schedule(handler, path=".", recursive=False)
    observer.start()
    logging.info("Started watchdog to monitor config.json changes.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    agents = load_config()
    launch_all_agents(agents)
    watch_config()
