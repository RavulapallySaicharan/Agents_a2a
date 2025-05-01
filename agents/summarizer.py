from python_a2a import A2AServer, skill, agent, TaskStatus, TaskState
import os
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()

@agent(
    name="Summarizer Agent",
    description="Summarizes text content using OpenAI API",
    version="1.0.0"
)
class SummarizerAgent(A2AServer):
    
    def __init__(self):
        super().__init__()
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
    
    @skill(
        name="Summarize Text",
        description="Summarize the given text into a concise format",
        tags=["summarize", "content", "text"]
    )
    def summarize_text(self, text):
        """Summarize the provided text using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes text."},
                    {"role": "user", "content": f"Summarize the following text in a concise manner:\n\n{text}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def handle_task(self, task):
        """Handle incoming task requests for summarization."""
        # Extract text content from message
        message_data = task.message or {}
        content = message_data.get("content", {})
        
        # Handle different content formats
        if isinstance(content, dict):
            text = content.get("text", "")
        elif isinstance(content, str):
            text = content
        else:
            text = ""
        
        if not text:
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={"role": "agent", "content": {"type": "text", 
                         "text": "Please provide text content to summarize."}}
            )
            return task
        
        # Generate summary
        summary = self.summarize_text(text)
        
        # Create response
        task.artifacts = [{
            "parts": [{"type": "text", "text": summary}]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        return task


if __name__ == "__main__":
    from python_a2a import run_server
    
    # Get port from environment or use default
    port = int(os.getenv("SUMMARIZER_PORT", 5001))
    
    # Create and run the server
    agent = SummarizerAgent()
    run_server(agent, port=port) 