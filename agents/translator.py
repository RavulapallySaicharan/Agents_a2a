from python_a2a import A2AServer, skill, agent, TaskStatus, TaskState
import os
from dotenv import load_dotenv
import openai
import re

# Load environment variables from .env file
load_dotenv()

@agent(
    name="Translator Agent",
    description="Translates text into specified target languages using OpenAI API",
    version="1.0.0"
)
class TranslatorAgent(A2AServer):
    
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
        name="Translate Text",
        description="Translate text to a specified target language",
        tags=["translate", "language", "multilingual"]
    )
    def translate_text(self, text, target_language):
        """Translate the provided text to the target language using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful translator assistant."},
                    {"role": "user", "content": f"Translate the following text to {target_language}:\n\n{text}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error translating text: {str(e)}"
    
    def handle_task(self, task):
        """Handle incoming task requests for translation."""
        # Extract text content and target language from message
        message_data = task.message or {}
        content = message_data.get("content", {})
        
        # Handle different content formats
        if isinstance(content, dict):
            text = content.get("text", "")
        elif isinstance(content, str):
            text = content
        else:
            text = ""
        
        # Try to extract target language from the text
        target_language = "Spanish"  # Default language
        language_pattern = r"(?:translate|convert)(?:\s+this)?(?:\s+to)?\s+([a-zA-Z]+)"
        match = re.search(language_pattern, text, re.IGNORECASE)
        
        if match:
            target_language = match.group(1).capitalize()
            # Remove the instruction part from the text to be translated
            text = re.sub(language_pattern, "", text, flags=re.IGNORECASE).strip()
        
        if not text:
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={"role": "agent", "content": {"type": "text", 
                         "text": "Please provide text content to translate and a target language."}}
            )
            return task
        
        # Generate translation
        translation = self.translate_text(text, target_language)
        
        # Create response
        task.artifacts = [{
            "parts": [{"type": "text", "text": translation}]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        return task


if __name__ == "__main__":
    from python_a2a import run_server
    
    # Get port from environment or use default
    port = int(os.getenv("TRANSLATOR_PORT", 5002))
    
    # Create and run the server
    agent = TranslatorAgent()
    run_server(agent, port=port) 