import os
import subprocess
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def start_agent(agent_file, name):
    """Start an agent in a new process."""
    print(f"Starting {name} Agent...")
    try:
        process = subprocess.Popen([sys.executable, agent_file], 
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   text=True)
        return process
    except Exception as e:
        print(f"Error starting {name} Agent: {str(e)}")
        return None

def main():
    """Main function to start the agent network."""
    # Check if either OpenAI API key or Azure OpenAI credentials are set
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_azure = (bool(os.getenv("AZURE_OPENAI_API_KEY")) and 
                bool(os.getenv("AZURE_OPENAI_ENDPOINT")) and 
                bool(os.getenv("AZURE_OPENAI_API_VERSION")))
    
    if not (has_openai or has_azure):
        print("Error: No valid API credentials found.")
        print("Please create a .env file with either:")
        print("1. OPENAI_API_KEY for standard OpenAI usage, or")
        print("2. All of the following for Azure OpenAI:")
        print("   - AZURE_OPENAI_API_KEY")
        print("   - AZURE_OPENAI_ENDPOINT")
        print("   - AZURE_OPENAI_API_VERSION")
        sys.exit(1)
    
    if has_openai:
        print("Using OpenAI credentials")
    elif has_azure:
        print("Using Azure OpenAI credentials")
    
    # Set default ports if not specified
    if not os.getenv("SUMMARIZER_PORT"):
        os.environ["SUMMARIZER_PORT"] = "5001"
    if not os.getenv("TRANSLATOR_PORT"):
        os.environ["TRANSLATOR_PORT"] = "5002"
    
    # Start the agents
    summarizer_process = start_agent("agents/summarizer.py", "Summarizer")
    translator_process = start_agent("agents/translator.py", "Translator")
    
    # Wait for agents to start up
    print("Waiting for agents to start up...")
    time.sleep(3)
    
    # Test the agent network
    print("\nStarting Agent Network for testing...")
    try:
        # Run the agent network test
        network_process = subprocess.Popen([sys.executable, "agent_network.py"],
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          text=True)
        
        # Display the output in real-time
        for line in network_process.stdout:
            print(line.strip())
        
        # Wait for completion
        network_process.wait()
        
    except KeyboardInterrupt:
        print("\nStopping all processes...")
    finally:
        # Clean up processes
        if summarizer_process:
            summarizer_process.terminate()
        if translator_process:
            translator_process.terminate()
        
        print("All processes terminated.")

if __name__ == "__main__":
    main() 