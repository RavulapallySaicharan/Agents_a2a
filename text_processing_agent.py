from python_a2a import AgentNetwork, AIAgentRouter, A2AClient, Message, TextContent, MessageRole
import os
from dotenv import load_dotenv
import asyncio
import openai

# Load environment variables
load_dotenv()

def initialize_openai_client():
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

class TextProcessingAgent:
    """A network of text processing agents with intelligent routing."""
    
    def __init__(self):
        """Initialize the agent network with Summarizer and Translator agents."""
        # Set up agent network
        self.network = AgentNetwork(name="Text Processing Network")
        
        # Add agents to the network
        summarizer_url = f"http://localhost:{os.getenv('SUMMARIZER_PORT', '5001')}"
        translator_url = f"http://localhost:{os.getenv('TRANSLATOR_PORT', '5002')}"
        
        self.network.add("summarizer", summarizer_url)
        self.network.add("translator", translator_url)
        
        # Create an OpenAI client for routing decisions with fallback
        self.openai_client = initialize_openai_client()
        
        # Create the router
        self.router = AIRouterWithOpenAI(
            llm_client=self.openai_client,
            agent_network=self.network
        )
        
    async def process_text(self, query):
        """Process a text query by routing it to the appropriate agent."""
        # Determine which agent should handle the query
        agent_name, confidence = self.router.route_query(query)
        
        # Get the selected agent
        agent = self.network.get_agent(agent_name)
        
        # Create a message to send to the agent
        message = Message(
            content=TextContent(text=query),
            role=MessageRole.USER
        )
        
        # Send the message to the agent and get the response
        response = agent.ask(message)
        
        return {
            "agent": agent_name,
            "confidence": confidence,
            "result": response
        }
        
    def list_agents(self):
        """List all available agents in the network."""
        return self.network.list_agents()


class AIRouterWithOpenAI(AIAgentRouter):
    """AI-powered router using OpenAI to make routing decisions."""
    
    def __init__(self, llm_client, agent_network):
        """Initialize the router with an OpenAI client and agent network."""
        self.client = llm_client
        self.agent_network = agent_network
        self.agent_descriptions = self._get_agent_descriptions()
        
    def _get_agent_descriptions(self):
        """Get descriptions of all agents in the network."""
        descriptions = {}
        for agent_info in self.agent_network.list_agents():
            name = agent_info.get("name", "")
            descriptions[name] = agent_info.get("description", "")
        return descriptions
    
    def route_query(self, query):
        """Route a query to the most appropriate agent."""
        prompt = self._build_routing_prompt(query)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0
            )
            
            result = response.choices[0].message.content.strip().lower()
            
            # Parse the response to determine the agent and confidence
            if "summarizer" in result:
                return "summarizer", 0.9 if "high confidence" in result else 0.7
            elif "translator" in result:
                return "translator", 0.9 if "high confidence" in result else 0.7
            else:
                # Default to summarizer if unclear
                return "summarizer", 0.5
                
        except Exception as e:
            print(f"Error routing query: {str(e)}")
            # Default to summarizer on error
            return "summarizer", 0.5
    
    def _build_routing_prompt(self, query):
        """Build a prompt for the routing decision."""
        return f"""
You are a query router for a text processing system. Your job is to determine which agent should handle a given query based on its content.

Available agents:
1. summarizer: {self.agent_descriptions.get('summarizer', 'Summarizes text')}
2. translator: {self.agent_descriptions.get('translator', 'Translates text to other languages')}

Guidelines:
- If the query asks to summarize text or create a summary, route to 'summarizer'
- If the query mentions translation or converting text to another language, route to 'translator'
- Look for explicit keywords like 'summarize', 'summary', 'translate', 'translation', or language names
- If the query mentions both summarization and translation, determine the primary intent
- If you're very confident in your decision, include "high confidence" in your response

Reply with only the name of the agent (summarizer or translator) and your confidence level.
"""


async def process_user_input(network):
    """Process a single user input through the agent network."""
    print("\nEnter your text to process (or 'exit' to quit):")
    user_input = input("> ").strip()
    
    if user_input.lower() == 'exit':
        return False
    
    if not user_input:
        print("Please enter some text to process.")
        return True
    
    try:
        result = await network.process_text(user_input)
        print(f"\nQuery: {user_input}")
        print(f"Routed to: {result['agent']} (confidence: {result['confidence']:.2f})")
        print(f"Response: {result['result']}")
    except Exception as e:
        print(f"Error processing input: {str(e)}")
    
    return True


if __name__ == "__main__":
    # Create the agent network
    network = TextProcessingAgent()
    
    # List available agents
    print("\nAvailable Agents:")
    for agent in network.list_agents():
        print(f"- {agent.get('name', 'Unnamed')}: {agent.get('description', 'No description')}")
    
    print("\nWelcome to the Text Processing Network!")
    print("You can ask for text summarization or translation.")
    print("Examples:")
    print("- Summarize this text: [your text]")
    print("- Translate this to French: [your text]")
    print("Type 'exit' to quit the program.")
    
    # Main interaction loop
    async def main_loop():
        should_continue = True
        while should_continue:
            should_continue = await process_user_input(network)
    
    # Run the main loop
    asyncio.run(main_loop())
    print("\nThank you for using the Text Processing Network!") 