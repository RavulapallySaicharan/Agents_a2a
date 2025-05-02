from typing import Any, Dict, Optional
import openai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Agent:
    def __init__(self, model: str = "gpt-3.5-turbo", max_tokens: int = 150):
        self.model = model
        self.max_tokens = max_tokens
        self._validate_credentials()
        
    def _validate_credentials(self):
        """Validate OpenAI credentials."""
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not found in environment variables")
            
    def is_entry_point(self) -> bool:
        """Check if this agent is an entry point."""
        return True
        
    def connect(self, target: 'Agent', params: Dict[str, Any] = None) -> None:
        """Connect this agent to another agent."""
        self.next_agent = target
        
    def process(self, input_data: str) -> Dict[str, Any]:
        """Process the input text and generate a summary."""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes text."},
                    {"role": "user", "content": f"Please summarize the following text: {input_data}"}
                ],
                max_tokens=self.max_tokens
            )
            
            summary = response.choices[0].message.content
            
            # If there's a next agent, pass the summary to it
            if hasattr(self, 'next_agent'):
                return self.next_agent.process(summary)
                
            return {
                "agent": "summarizer",
                "confidence": 1.0,
                "response": summary
            }
            
        except Exception as e:
            return {
                "agent": "summarizer",
                "confidence": 0.0,
                "response": f"Error generating summary: {str(e)}"
            }


if __name__ == "__main__":
    from python_a2a import run_server
    
    # Get port from environment or use default
    port = int(os.getenv("SUMMARIZER_PORT", 5001))
    
    # Create and run the server
    agent = Agent()
    run_server(agent, port=port) 