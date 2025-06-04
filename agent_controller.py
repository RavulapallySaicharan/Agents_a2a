import subprocess
import os
import time
import signal
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class AgentController:
    def __init__(self):
        self.manager_process = None
        self.stop_file = "agents/stop_signal.txt"

    def start_agent_manager(self):
        """Start the agent server manager as a subprocess"""
        try:
            # Ensure the agents directory exists
            os.makedirs("agents", exist_ok=True)
            
            # Start the agent manager
            self.manager_process = subprocess.Popen(
                [sys.executable, "agent_server_manager.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            logging.info(f"Agent manager started with PID: {self.manager_process.pid}")
            return True
        except Exception as e:
            logging.error(f"Failed to start agent manager: {e}")
            return False

    def stop_agent_manager(self):
        """Stop the agent server manager gracefully"""
        if not self.manager_process:
            logging.warning("No agent manager process is running")
            return False

        try:
            # Create stop signal file
            with open(self.stop_file, "w") as f:
                f.write("stop")
            
            # Wait for graceful shutdown (max 10 seconds)
            for _ in range(10):
                if self.manager_process.poll() is not None:
                    break
                time.sleep(1)
            
            # If process is still running, force kill it
            if self.manager_process.poll() is None:
                logging.warning("Force killing agent manager process")
                self.manager_process.kill()
            
            # Clean up stop signal file if it exists
            if os.path.exists(self.stop_file):
                os.remove(self.stop_file)
            
            logging.info("Agent manager stopped successfully")
            self.manager_process = None
            return True
            
        except Exception as e:
            logging.error(f"Error stopping agent manager: {e}")
            return False

    def is_running(self):
        """Check if the agent manager is running"""
        if not self.manager_process:
            return False
        return self.manager_process.poll() is None

def main():
    controller = AgentController()
    
    # Start the agent manager
    if controller.start_agent_manager():
        logging.info("Agent manager started successfully")
        
        # Example: Let it run for 10 seconds
        time.sleep(10)
        
        # Stop the agent manager
        controller.stop_agent_manager()

if __name__ == "__main__":
    main() 