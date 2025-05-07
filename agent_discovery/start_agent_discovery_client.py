from python_a2a.discovery import DiscoveryClient
import dotenv
import os

dotenv.load_dotenv()

registry_port = os.getenv("DISCOVERY_PORT")

registry_url = f"http://localhost:{registry_port}"

# Create a discovery client for discovering agents
client = DiscoveryClient(agent_card=None)  # No agent card needed for discovery only
client.add_registry(registry_url)

# Discover all agents
agents = client.discover()
print(f"Discovered {len(agents)} agents:")
for agent in agents:
    print(f"- {agent.name} at {agent.url}")
    print(f"  Capabilities: {agent.capabilities}")