import os
import sys
import requests
import openai
import json
from typing import List, Optional, Dict, Any
from pathlib import Path

def update_config_json(agent_info: Dict[str, Any], config_path: Path) -> None:
    """
    Update the config.json file with new agent information.
    
    Args:
        agent_info: Dictionary containing agent metadata
        config_path: Path to the config.json file
    """
    # Create config file if it doesn't exist
    if not config_path.exists():
        config = {
            "agents": []
        }
    else:
        # Read existing config
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    # Check if agent already exists
    for i, agent in enumerate(config["agents"]):
        if agent["name"] == agent_info["name"]:
            # Update existing agent
            config["agents"][i] = agent_info
            break
    else:
        # Add new agent
        config["agents"].append(agent_info)
    
    # Sort agents by name for better readability
    config["agents"].sort(key=lambda x: x["name"])
    
    # Write updated config with proper formatting
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4, sort_keys=True)

def create_agent_file(
    agent_name: str,
    agent_url: Optional[str] = None,
    agent_inputs: List[str] = None,
    agent_description: str = None,
    agent_goal: str = None,
    agent_tags: Optional[List[str]] = None,
    agent_port: int = 5001,
    overwrite: bool = False
) -> str:
    """
    Create a new agent file based on the provided specifications.
    
    Args:
        agent_name: Name of the agent (used for filename)
        agent_url: API or endpoint to be used by the agent (optional)
        agent_inputs: List of input variables or expected parameters
        agent_description: Description of the agent's purpose
        agent_goal: Definition of what the agent aims to achieve
        agent_tags: Optional metadata tags for categorization
        agent_port: Port number for the agent server (default: 5001)
        overwrite: Whether to overwrite existing file
        
    Returns:
        str: Path to the created file
    """
    # Convert agent name to proper filename format
    filename = f"{agent_name.lower().replace(' ', '_')}_agent.py"
    agents_dir = Path("agents")
    file_path = agents_dir / filename
    
    # Check if file exists and handle accordingly
    if file_path.exists() and not overwrite:
        raise FileExistsError(f"Agent file {filename} already exists. Use overwrite=True to replace it.")
    
    # Create agents directory if it doesn't exist
    agents_dir.mkdir(exist_ok=True)
    
    # Generate the agent code
    code = f'''from python_a2a import A2AServer, skill, agent, TaskStatus, TaskState
import os
import requests
import openai
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@agent(
    name="{agent_name}",
    description="{agent_description}",
    version="1.0.0"
)
class {agent_name.replace(' ', '')}Agent(A2AServer):
    
    def __init__(self):
        super().__init__()
        self.url = "{agent_url}"
        self.goal = "{agent_goal}"
        self.tags = {agent_tags or []}
        self.port = {agent_port}
        self.client = self._initialize_openai_client()
    
    def _initialize_openai_client(self):
        """Initialize OpenAI client with fallback to Azure OpenAI."""
        try:
            # Try to initialize the default OpenAI client
            return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            print(f"Failed to initialize OpenAI client: {{str(e)}}")
            print("Falling back to Azure OpenAI...")
            
            # Fall back to Azure OpenAI
            try:
                return openai.AzureOpenAI(
                    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
                )
            except Exception as azure_error:
                print(f"Failed to initialize Azure OpenAI client: {{str(azure_error)}}")
                raise Exception("Failed to initialize any OpenAI client. Please check your API keys and configurations.")
    
    def _call_api(self, inputs: Dict[str, Any]) -> str:
        """
        Make API call to the configured endpoint.
        
        Args:
            inputs: Dictionary of input parameters
            
        Returns:
            str: API response content
        """
        try:
            response = requests.post(self.url, json=inputs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return f"API call failed: {{str(e)}}"
    
    def _call_llm(self, inputs: Dict[str, Any]) -> str:
        """
        Make LLM call using OpenAI API.
        
        Args:
            inputs: Dictionary of input parameters
            
        Returns:
            str: LLM response content
        """
        try:
            # Create a prompt based on the agent's goal and inputs
            prompt = f"Goal: {{self.goal}}\\n\\nInputs: {{inputs}}\\n\\nPlease process these inputs according to the goal."
            
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "o4-mini-2025-04-16"),,
                messages=[
                    {{"role": "system", "content": f"You are an AI agent with the following goal: {{self.goal}}"}},
                    {{"role": "user", "content": prompt}}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"LLM call failed: {{str(e)}}"
    
    @skill(
        name="{agent_name}",
        description="{agent_description}",
        tags={agent_tags or []}
    )
    def process_input(self, **kwargs):
        """
        Process the input data using the agent's skills.
        
        Args:
            **kwargs: Input parameters as specified in agent_inputs
        """
        try:
            # Validate required inputs
            for required_input in {agent_inputs}:
                if required_input not in kwargs:
                    raise ValueError(f"Missing required input: {{required_input}}")
            
            # Choose between API call and LLM call based on URL availability
            if self.url != "None":
                result = self._call_api(kwargs)
            else:
                result = self._call_llm(kwargs)
            
            return result
        except Exception as e:
            return str(e)
    
    def handle_task(self, task):
        """Handle incoming task requests."""
        # Extract content from message
        message_data = task.message or {{}}
        content = message_data.get("content", {{}})
        
        # Handle different content formats
        if isinstance(content, dict):
            inputs = content
        else:
            inputs = {{"raw_input": content}}
        
        if not inputs:
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={{
                    "role": "agent",
                    "content": {{
                        "dataType": "data",
                        "message": "Please provide required input parameters."
                    }}
                }}
            )
            return task
        
        # Process the input and make appropriate call
        result = self.process_input(**inputs)
        
        # Create response
        task.artifacts = [{{
            "parts": [{{
                "type": "text",
                "text": str(result)
            }}]
        }}]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        return task


if __name__ == "__main__":
    from python_a2a import run_server
    
    # Get port from environment or use the configured port
    port = int(os.getenv("AGENT_PORT", {agent_port}))
    
    # Create and run the server
    agent = {agent_name.replace(' ', '')}Agent()
    run_server(agent, port=port)
'''
    
    # Write the code to file
    with open(file_path, 'w') as f:
        f.write(code)
    
    # Update config.json with new agent information
    agent_info = {
        "name": agent_name,
        "description": agent_description,
        "version": "1.0.0",
        "port": agent_port,
        "file": filename,
        "skills": [
            {
                "name": agent_name,
                "description": agent_description,
                "tags": agent_tags or [],
                "inputs": agent_inputs or ["text"]
            }
        ]
    }
    
    config_path = Path("agents") / "config.json"
    update_config_json(agent_info, config_path)
    
    return str(file_path)

def main():
    """CLI interface for creating agent files."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create a new agent file")
    parser.add_argument("--name", required=True, help="Name of the agent")
    parser.add_argument("--url", help="API or endpoint URL (optional)")
    parser.add_argument("--inputs", required=True, nargs="+", help="List of input parameters")
    parser.add_argument("--description", required=True, help="Agent description")
    parser.add_argument("--goal", required=True, help="Agent goal")
    parser.add_argument("--tags", nargs="+", help="Optional metadata tags")
    parser.add_argument("--port", type=int, default=5001, help="Port number for the agent server (default: 5001)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing file")
    
    args = parser.parse_args()
    
    try:
        file_path = create_agent_file(
            agent_name=args.name,
            agent_url=args.url,
            agent_inputs=args.inputs,
            agent_description=args.description,
            agent_goal=args.goal,
            agent_tags=args.tags,
            agent_port=args.port,
            overwrite=args.overwrite
        )
        print(f"Successfully created agent file: {file_path}")
    except Exception as e:
        print(f"Error creating agent file: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 