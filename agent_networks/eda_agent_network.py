from python_a2a import AgentNetwork, AIAgentRouter, A2AClient, Message, TextContent, MessageRole
import os
from dotenv import load_dotenv
import asyncio
import openai
import pandas as pd
import json

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

class EDAAgentNetwork:
    """A network of EDA agents with intelligent routing."""
    
    def __init__(self):
        """Initialize the agent network with Data Analysis, Visualization, and Wrangling agents."""
        # Set up agent network
        self.network = AgentNetwork(name="EDA Network")
        
        # Add agents to the network with ports starting from 5003
        analysis_url = f"http://localhost:{os.getenv('DATA_ANALYSIS_PORT', '5003')}"
        visualization_url = f"http://localhost:{os.getenv('DATA_VISUALIZATION_PORT', '5004')}"
        wrangling_url = f"http://localhost:{os.getenv('DATA_WRANGLING_PORT', '5005')}"
        
        self.network.add("data_analysis", analysis_url)
        self.network.add("data_visualization", visualization_url)
        self.network.add("data_wrangling", wrangling_url)
        
        # Create an OpenAI client for routing decisions with fallback
        self.openai_client = initialize_openai_client()
        
        # Create the router
        self.router = AIRouterWithOpenAI(
            llm_client=self.openai_client,
            agent_network=self.network
        )
        
    async def process_dataframe(self, df: pd.DataFrame, query: str):
        """Process a DataFrame by routing it to the appropriate agent."""
        # Determine which agent should handle the query
        agent_name, confidence = self.router.route_query(query)
        
        # Get the selected agent
        agent = self.network.get_agent(agent_name)
        
        # Create a message to send to the agent
        message = Message(
            content={
                "dataframe": df.to_json(orient='split'),
                "query": query
            },
            role=MessageRole.USER
        )
        
        # Send the message to the agent and get the response
        response = agent.ask(message)
        
        # Format the response according to the new structure
        formatted_response = {
            "dataType": "data",  # Default to data type
            "message": response
        }
        
        # If the response is a list, it might be a table or buttons
        if isinstance(response, list):
            if all(isinstance(item, (dict, list)) for item in response):
                formatted_response["dataType"] = "table"
            else:
                formatted_response["dataType"] = "buttons"
        
        return {
            "agent": agent_name,
            "confidence": confidence,
            "response": formatted_response
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
                model=os.getenv("OPENAI_MODEL", "o4-mini-2025-04-16"),
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0
            )
            
            result = response.choices[0].message.content.strip().lower()
            
            # Parse the response to determine the agent and confidence
            if "data_analysis" in result:
                return "data_analysis", 0.9 if "high confidence" in result else 0.7
            elif "data_visualization" in result:
                return "data_visualization", 0.9 if "high confidence" in result else 0.7
            elif "data_wrangling" in result:
                return "data_wrangling", 0.9 if "high confidence" in result else 0.7
            else:
                # Default to data analysis if unclear
                return "data_analysis", 0.5
                
        except Exception as e:
            print(f"Error routing query: {str(e)}")
            # Default to data analysis on error
            return "data_analysis", 0.5
    
    def _build_routing_prompt(self, query):
        """Build a prompt for the routing decision."""
        return f"""
You are a query router for a data analysis system. Your job is to determine which agent should handle a given query based on its content.

Available agents:
1. data_analysis: {self.agent_descriptions.get('data_analysis', 'Performs exploratory data analysis and provides summary statistics')}
2. data_visualization: {self.agent_descriptions.get('data_visualization', 'Creates visualizations and plots from the data')}
3. data_wrangling: {self.agent_descriptions.get('data_wrangling', 'Cleans and preprocesses the data')}

Guidelines:
- If the query asks for statistics, summaries, or insights about the data, route to 'data_analysis'
- If the query mentions plots, charts, or visualizations, route to 'data_visualization'
- If the query mentions cleaning, preprocessing, or transforming the data, route to 'data_wrangling'
- Look for explicit keywords like 'analyze', 'statistics', 'plot', 'visualize', 'clean', 'preprocess'
- If the query mentions both analysis and visualization, determine the primary intent
- If you're very confident in your decision, include "high confidence" in your response

Reply with only the name of the agent (data_analysis, data_visualization, or data_wrangling) and your confidence level.
"""


async def process_user_input(network):
    """Process a single user input through the agent network."""
    print("\nEnter your data analysis query (or 'exit' to quit):")
    user_input = input("> ").strip()
    
    if user_input.lower() == 'exit':
        return False
    
    if not user_input:
        print("Please enter a query to process.")
        return True
    
    try:
        # Create a sample DataFrame for testing
        df = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': ['a', 'b', 'c', 'd', 'e'],
            'C': [1.1, 2.2, 3.3, 4.4, 5.5]
        })
        
        result = await network.process_dataframe(df, user_input)
        print(f"\nQuery: {user_input}")
        print(f"Routed to: {result['agent']} (confidence: {result['confidence']:.2f})")
        print(f"Response: {result['response']['message']}")
    except Exception as e:
        print(f"Error processing input: {str(e)}")
    
    return True


if __name__ == "__main__":
    # Create the agent network
    network = EDAAgentNetwork()
    
    # List available agents
    print("\nAvailable Agents:")
    for agent in network.list_agents():
        print(f"- {agent.get('name', 'Unnamed')}: {agent.get('description', 'No description')}")
    
    print("\nWelcome to the EDA Network!")
    print("You can ask for data analysis, visualization, or preprocessing.")
    print("Examples:")
    print("- Analyze the data and show summary statistics")
    print("- Create a histogram of column A")
    print("- Clean the data by handling missing values")
    print("Type 'exit' to quit the program.")
    
    # Main interaction loop
    async def main_loop():
        should_continue = True
        while should_continue:
            should_continue = await process_user_input(network)
    
    # Run the main loop
    asyncio.run(main_loop())
    print("\nThank you for using the EDA Network!") 