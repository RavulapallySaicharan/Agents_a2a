from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState
from typing import Dict, Any, Optional

@agent(
    name="Your Agent Name",  # Replace with your agent's name
    description="Description of what your agent does",  # Replace with your agent's description
    version="1.0.0"  # Replace with your agent's version
)
class YourAgent(A2AServer):
    """
    Your agent class that inherits from A2AServer.
    Add any initialization logic in __init__ if needed.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize any required resources here
        # Example: self.some_resource = SomeResource()
    
    @skill(
        name="Your Skill Name",  # Replace with your skill's name
        description="Description of what this skill does",  # Replace with your skill's description
        tags=["tag1", "tag2"]  # Replace with relevant tags
    )
    def your_skill(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implement your skill logic here.
        This is where you process the input and return the result.
        """
        try:
            # Your skill implementation
            result = {
                "status": "success",
                "data": "Your processed data"
            }
            return result
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def handle_task(self, task) -> TaskStatus:
        """
        Handle incoming tasks and route them to appropriate skills.
        This is the main entry point for processing tasks.
        """
        try:
            # Extract message data
            message_data = task.message or {}
            content = message_data.get("content", {})
            
            # Process the task based on content
            if "your_condition" in content:  # Replace with your condition
                # Call your skill
                result = self.your_skill(content)
                
                # Set task artifacts and status
                task.artifacts = [{
                    "parts": [{"type": "text", "text": str(result)}]
                }]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            else:
                # Handle unrecognized requests
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={
                        "role": "agent",
                        "content": {
                            "type": "text",
                            "text": "Please provide valid input for processing."
                        }
                    }
                )
            
            return task
            
        except Exception as e:
            # Handle errors
            task.status = TaskStatus(
                state=TaskState.ERROR,
                message={
                    "role": "agent",
                    "content": {
                        "type": "text",
                        "text": f"Error processing request: {str(e)}"
                    }
                }
            )
            return task

# Run the server
if __name__ == "__main__":
    # Create and run the agent
    agent = YourAgent()
    run_server(agent, port=5000)  # Replace with your desired port 