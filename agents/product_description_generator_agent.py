from python_a2a import A2AServer, skill, agent, TaskStatus, TaskState
import os
import requests
import openai
import json
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@agent(
    name="Product Description Generator",
    description="Generates compelling product descriptions for e-commerce listings",
    version="1.0.0"
)
class ProductDescriptionGeneratorAgent(A2AServer):
    
    def __init__(self):
        super().__init__()
        self.url = "None"
        self.goal = "Create persuasive and SEO-friendly product descriptions using given product data"
        self.tags = ['ecommerce', 'copywriting', 'product-description']
        self.port = 5014
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
            return f"API call failed: {str(e)}"
    
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
            prompt = f"Goal: {self.goal}\n\nInputs: {inputs}\n\nPlease process these inputs according to the goal."
            
            response = self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "o4-mini-2025-04-16"),
                messages=[
                    {"role": "system", "content": f"You are an AI agent with the following goal: {self.goal}"},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"LLM call failed: {str(e)}"
    
    @skill(
        name="Product Description Generator",
        description="Generates compelling product descriptions for e-commerce listings",
        tags=['ecommerce', 'copywriting', 'product-description']
    )
    def process_input(self, **kwargs):
        """
        Process the input data using the agent's skills.
        
        Args:
            **kwargs: Input parameters as specified in agent_inputs
        """
        try:
            # Validate required inputs
            kwargs = json.loads(kwargs["text"])
            for required_input in ['product_name', 'features', 'category']:
                if required_input not in kwargs:
                    raise ValueError(f"Missing required input: {required_input}")
            
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
                "text": str(result)
            }]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        return task


if __name__ == "__main__":
    from python_a2a import run_server
    
    # Get port from environment or use the configured port
    port = int(os.getenv("AGENT_PORT", 5014))
    
    # Create and run the server
    agent = ProductDescriptionGeneratorAgent()
    run_server(agent, port=port)
