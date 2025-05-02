from typing import Any, Dict, Optional
import openai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Agent:
    def __init__(self, model: str = "gpt-3.5-turbo", target_language: str = "en"):
        self.model = model
        self.target_language = target_language
        self._validate_credentials()
        
    def _validate_credentials(self):
        """Validate OpenAI credentials."""
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not found in environment variables")
            
    def is_entry_point(self) -> bool:
        """Check if this agent is an entry point."""
        return False
        
    def connect(self, target: 'Agent', params: Dict[str, Any] = None) -> None:
        """Connect this agent to another agent."""
        self.next_agent = target
        
    def process(self, input_data: str) -> Dict[str, Any]:
        """Process the input text and translate it."""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a helpful assistant that translates text to {self.target_language}."},
                    {"role": "user", "content": f"Please translate the following text to {self.target_language}: {input_data}"}
                ]
            )
            
            translation = response.choices[0].message.content
            
            # If there's a next agent, pass the translation to it
            if hasattr(self, 'next_agent'):
                return self.next_agent.process(translation)
                
            return {
                "agent": "translator",
                "confidence": 1.0,
                "response": translation
            }
            
        except Exception as e:
            return {
                "agent": "translator",
                "confidence": 0.0,
                "response": f"Error translating text: {str(e)}"
            }


if __name__ == "__main__":
    from python_a2a import run_server
    
    # Get port from environment or use default
    port = int(os.getenv("TRANSLATOR_PORT", 5002))
    
    # Create and run the server
    agent = Agent()
    run_server(agent, port=port) 