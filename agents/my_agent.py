from python_a2a import A2AServer, skill, agent, TaskStatus, TaskState
import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@agent(
    name="My Agent",
    description="My agent description",
    version="1.0.0"
)
class MyAgentAgent(A2AServer):
    
    def __init__(self):
        super().__init__()
        self.url = "https://api.example.com"
        self.goal = "My agent goal"
        self.tags = ['tag1', 'tag2']
        self.port = 5002
    
    def _call_api(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make API call to the configured endpoint.
        
        Args:
            inputs: Dictionary of input parameters
            
        Returns:
            Dict containing API response
        """
        try:
            response = requests.post(self.url, json=inputs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"API call failed: {str(e)}"}
    
    @skill(
        name="Process Input",
        description="Process the input data according to agent specifications",
        tags=['tag1', 'tag2']
    )
    def process_input(self, **kwargs):
        """
        Process the input data using the agent's skills.
        
        Args:
            **kwargs: Input parameters as specified in agent_inputs
        """
        try:
            # Validate required inputs
            for required_input in ['input1', 'input2']:
                if required_input not in kwargs:
                    raise ValueError(f"Missing required input: {required_input}")
            
            # Make API call with validated inputs
            result = self._call_api(kwargs)
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def handle_task(self, task):
        """Handle incoming task requests."""
        # Extract content from message
        message_data = task.message or {}
        content = message_data.get("content", {})
        
        # Handle different content formats
        if isinstance(content, dict):
            inputs = content
        else:
            inputs = {"raw_input": content}
        
        if not inputs:
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={
                    "role": "agent",
                    "content": {
                        "dataType": "data",
                        "message": "Please provide required input parameters."
                    }
                }
            )
            return task
        
        # Process the input and make API call
        result = self.process_input(**inputs)
        
        # Create response
        task.artifacts = [{
            "parts": [{
                "type": "text",
                "dataType": "data",
                "message": str(result)
            }]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        return task


if __name__ == "__main__":
    from python_a2a import run_server
    
    # Get port from environment or use the configured port
    port = int(os.getenv("AGENT_PORT", 5002))
    
    # Create and run the server
    agent = MyAgentAgent()
    run_server(agent, port=port)
