from python_a2a import A2AServer, skill, agent, TaskStatus, TaskState
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@agent(
    name="[YOUR_AGENT_NAME]",  # Replace with your agent's name
    description="[YOUR_AGENT_DESCRIPTION]",  # Replace with your agent's description
    version="1.0.0"
)
class GuidelineAgent(A2AServer):
    """
    Template agent class that demonstrates the structure and components needed
    to create a new agent. Use this as a starting point for your own agent implementation.
    """
    
    def __init__(self):
        """
        Initialize your agent here.
        - Set up any required clients (e.g., API clients, database connections)
        - Initialize any necessary state variables
        - Load configurations
        """
        super().__init__()
        # Initialize your clients/services here
        # Example: self.client = self._initialize_client()
    
    def _initialize_client(self):
        """
        Example method showing how to initialize external clients/services.
        Replace with your own initialization logic.
        """
        try:
            # Add your client initialization code here
            # Example: return SomeClient(api_key=os.getenv("API_KEY"))
            pass
        except Exception as e:
            print(f"Failed to initialize client: {str(e)}")
            raise Exception("Failed to initialize client. Please check your configurations.")
    
    @skill(
        name="[YOUR_SKILL_NAME]",  # Replace with your skill's name
        description="[YOUR_SKILL_DESCRIPTION]",  # Replace with your skill's description
        tags=["tag1", "tag2", "tag3"]  # Replace with relevant tags
    )
    def your_skill_method(self, input_param1, input_param2):
        """
        Define your agent's main skill/functionality here.
        This is where the core logic of your agent should be implemented.
        
        Args:
            input_param1: Description of first parameter
            input_param2: Description of second parameter
            
        Returns:
            The result of your agent's processing
        """
        try:
            # Implement your skill's logic here
            result = "Your processed result"
            return result
        except Exception as e:
            return f"Error processing request: {str(e)}"
    
    def handle_task(self, task):
        """
        Handle incoming task requests. This is the main entry point for your agent.
        
        Args:
            task: The task object containing the request data
            
        Returns:
            The task object with updated status and results
        """
        # Extract data from the incoming task
        message_data = task.message or {}
        content = message_data.get("content", {})
        
        # Process the input data
        # Example: Extract and validate input parameters
        if isinstance(content, dict):
            input_data = content.get("input_field", "")
        elif isinstance(content, str):
            input_data = content
        else:
            input_data = ""
        
        # Validate input
        if not input_data:
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={
                    "role": "agent",
                    "content": {
                        "dataType": "data",
                        "message": "Please provide required input data."
                    }
                }
            )
            return task
        
        # Process the input using your skill
        result = self.your_skill_method(input_data, "additional_param")
        
        # Format and return the response
        task.artifacts = [{
            "parts": [{
                "type": "text",
                "dataType": "data",
                "message": result
            }]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        return task

    def run(self):
        """
        Example method showing how to test your agent locally.
        This is not part of the A2A framework but useful for development and testing.
        """
        # Create a sample task
        sample_task = type('Task', (), {
            'message': {
                'content': {
                    'input_field': 'Sample input data'
                }
            }
        })
        
        # Process the sample task
        result = self.handle_task(sample_task)
        
        # Print the result
        print("Sample task result:", result.artifacts[0]['parts'][0]['message'])


if __name__ == "__main__":
    from python_a2a import run_server
    
    # Get port from environment or use default
    port = int(os.getenv("AGENT_PORT", 5000))
    
    # Create and run the server
    agent = GuidelineAgent()
    
    # For local testing, you can use the run() method
    # agent.run()
    
    # For running as a server
    run_server(agent, port=port) 