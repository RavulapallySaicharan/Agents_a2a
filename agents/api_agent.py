from python_a2a import A2AServer, skill, agent, TaskStatus, TaskState
import os
import requests
import openai
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@agent(
    name="API Agent",
    description="Processes data through an external API",
    version="1.0.0"
)
class APIAgentAgent(A2AServer):
    
    def __init__(self):
        super().__init__()
        self.url = "https://api.example.com"
        self.goal = "Transform input data using external API"
        self.tags = ['api', 'data']
        self.port = 5002
        self.client = self._initialize_openai_client()
    
    def _initialize_openai_client(self):
        """Initialize OpenAI client with fallback to Azure OpenAI."""
        try:
            # Try to initialize the default OpenAI client
            return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            print(f"Failed to initialize OpenAI client: {str(e)}")
            print("Falling back to Azure OpenAI...")
            
            # Fall back to Azure OpenAI
            try:
                return openai.AzureOpenAI(
                    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
                )
            except Exception as azure_error:
                print(f"Failed to initialize Azure OpenAI client: {str(azure_error)}")
                raise Exception("Failed to initialize any OpenAI client. Please check your API keys and configurations.")
    
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
    
    def _call_llm(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make LLM call using OpenAI API.
        
        Args:
            inputs: Dictionary of input parameters
            
        Returns:
            Dict containing LLM response
        """
        try:
            # Create a prompt based on the agent's goal and inputs
            prompt = f"Goal: {self.goal}\n\nInputs: {inputs}\n\nPlease process these inputs according to the goal."
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are an AI agent with the following goal: {self.goal}"},
                    {"role": "user", "content": prompt}
                ]
            )
            return {"status": "success", "result": response.choices[0].message.content}
        except Exception as e:
            return {"status": "error", "message": f"LLM call failed: {str(e)}"}
    
    @skill(
        name="Process Input",
        description="Process the input data according to agent specifications",
        tags=['api', 'data']
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
            
            # Choose between API call and LLM call based on URL availability
            if self.url:
                result = self._call_api(kwargs)
            else:
                result = self._call_llm(kwargs)
            
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
        
        # Process the input and make appropriate call
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
    agent = APIAgentAgent()
    run_server(agent, port=port)
