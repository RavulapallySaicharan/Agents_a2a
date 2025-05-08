from python_a2a import A2AClient, AgentNetwork, AIAgentRouter

# Create an agent network
network = AgentNetwork(name="My Agent Network")

# Add agents to the network with their respective ports
network.add("agent1", "http://localhost:5011")
network.add("agent2", "http://localhost:5012")
network.add("agent3", "http://localhost:5013")

# Create a router to intelligently direct queries to the best agent
router = AIAgentRouter(
    llm_client=A2AClient("http://localhost:5011"),  # Using agent1 as the LLM for routing
    agent_network=network
)

# Function to get response from the most appropriate agent
def get_agent_response(query):
    # Route the query to the best agent
    agent_name, confidence = router.route_query(query)
    print(f"Routing to {agent_name} with {confidence:.2f} confidence")
    
    # Get the selected agent and ask the question
    agent = network.get_agent(agent_name)
    response = agent.ask(query)
    return response

# Test the agents
query = "I didn't like the movie which we watched yesterday"
response = get_agent_response(query)
print(f"\nResponse: {response}")

# List all available agents
print("\nAvailable Agents:")
for agent_info in network.list_agents():
    print(f"- {agent_info['name']}: {agent_info['url']}")
