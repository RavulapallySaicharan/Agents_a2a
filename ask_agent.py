from dotenv import load_dotenv
from python_a2a import A2AClient, AgentNetwork, AIAgentRouter
import openai
import os
import time

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

def create_agent_client(url, max_retries=3, retry_delay=2):
    """Create an A2A client with retry logic."""
    for attempt in range(max_retries):
        try:
            client = A2AClient(url)
            # Test the connection with a simple message
            test_response = client.ask({"content": {"text": "test connection"}})
            if test_response:
                return client
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed to connect to {url}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect to {url} after {max_retries} attempts: {str(e)}")
                return None

# Create an agent network
network = AgentNetwork(name="Sentiment Analysis Network")

# Add agents to the network with their respective ports
agent_url = "http://localhost:5013"
agent_client = create_agent_client(agent_url)
if agent_client:
    network.add("sentiment_agent", agent_url)
    print(f"Successfully connected to sentiment_agent at {agent_url}")
else:
    print(f"Failed to connect to sentiment_agent at {agent_url}. Please ensure the agent is running.")

# Create a router to intelligently direct queries to the best agent
try:
    router = AIAgentRouter(
        llm_client=initialize_openai_client(),
        agent_network=network
    )
    print("Successfully initialized AIAgentRouter")
except Exception as e:
    print(f"Failed to initialize AIAgentRouter: {str(e)}")
    exit(1)

def get_agent_response(query):
    """Get response from the most appropriate agent with error handling."""
    try:
        # Route the query to the best agent
        agent_name, confidence = router.route_query(query)
        print(f"Routing to {agent_name} with {confidence:.2f} confidence")
        
        # Get the selected agent and ask the question
        agent = network.get_agent(agent_name)
        if agent:
            # Format the message properly
            message = {"content": {"text": query}}
            response = agent.ask(message)
            return response
        else:
            return f"Error: Agent {agent_name} not found in the network"
    except Exception as e:
        return f"Error processing query: {str(e)}"

# Test the agents
if __name__ == "__main__":
    # List all available agents
    print("\nAvailable Agents:")
    for agent_info in network.list_agents():
        print(f"- {agent_info['name']}: {agent_info['url']}")
    
    # Only proceed with query if we have agents
    if network.list_agents():
        query = "I didn't like the movie which we watched yesterday"
        print(f"\nSending query: {query}")
        response = get_agent_response(query)
        print(f"\nResponse: {response}")
    else:
        print("\nNo agents available. Please ensure at least one agent is running.")
