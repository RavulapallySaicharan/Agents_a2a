import os
import json
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RouterAgentGenerator:
    """Generates router-based multi-agent setup files based on provided configurations."""
    
    def __init__(self):
        """Initialize the generator with OpenAI client."""
        self.openai_client = self._initialize_openai_client()
        
    def _initialize_openai_client(self):
        """Initialize OpenAI client with fallback to Azure OpenAI."""
        try:
            return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            print(f"Failed to initialize OpenAI client: {str(e)}")
            print("Falling back to Azure OpenAI...")
            
            try:
                return openai.AzureOpenAI(
                    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
                )
            except Exception as azure_error:
                print(f"Failed to initialize Azure OpenAI client: {str(azure_error)}")
                raise Exception("Failed to initialize any OpenAI client. Please check your API keys and configurations.")

    def validate_agent_configs(self, agent_configs: List[Dict[str, Any]]) -> bool:
        """Validate the provided agent configurations."""
        required_fields = {'name', 'type', 'port', 'description'}
        
        for config in agent_configs:
            if not all(field in config for field in required_fields):
                missing = required_fields - set(config.keys())
                raise ValueError(f"Missing required fields in agent config: {missing}")
            
            if not isinstance(config['name'], str) or not config['name'].strip():
                raise ValueError("Agent name must be a non-empty string")
            
            if not isinstance(config['port'], (int, str)):
                raise ValueError("Port must be a number or string")
            
            if not isinstance(config['description'], str):
                raise ValueError("Description must be a string")
        
        return True

    def generate_router_file(self, agent_configs: List[Dict[str, Any]], target_agent_name: str) -> str:
        """Generate the router-based multi-agent setup file content."""
        if not self.validate_agent_configs(agent_configs):
            return ""

        # Generate the file content
        file_content = self._generate_imports()
        file_content += self._generate_agent_network_class(agent_configs, target_agent_name)
        file_content += self._generate_router_class(agent_configs)
        file_content += self._generate_main_block(target_agent_name)
        
        return file_content

    def _generate_imports(self) -> str:
        """Generate the imports section of the file."""
        return '''from python_a2a import AgentNetwork, AIAgentRouter, A2AClient, Message, TextContent, MessageRole
import os
from dotenv import load_dotenv
import asyncio
import openai

# Load environment variables
load_dotenv()

'''

    def _generate_agent_network_class(self, agent_configs: List[Dict[str, Any]], target_agent_name: str) -> str:
        """Generate the agent network class."""
        class_name = f"{target_agent_name.capitalize()}Agent"
        
        # Generate agent initialization code
        agent_init_code = "        # Set up agent network\n"
        agent_init_code += f"        self.network = AgentNetwork(name=\"{target_agent_name.capitalize()} Network\")\n\n"
        agent_init_code += "        # Add agents to the network\n"
        
        for config in agent_configs:
            agent_init_code += f"        {config['name']}_url = f\"http://localhost:{config['port']}\"\n"
            agent_init_code += f"        self.network.add(\"{config['name']}\", {config['name']}_url)\n"
        
        agent_init_code += "\n        # Create an OpenAI client for routing decisions\n"
        agent_init_code += "        self.openai_client = self._initialize_openai_client()\n\n"
        agent_init_code += "        # Create the router\n"
        agent_init_code += "        self.router = AIRouterWithOpenAI(\n"
        agent_init_code += "            llm_client=self.openai_client,\n"
        agent_init_code += "            agent_network=self.network\n"
        agent_init_code += "        )\n"

        return f'''class {class_name}:
    """A network of {target_agent_name} agents with intelligent routing."""
    
    def __init__(self):
        """Initialize the agent network with configured agents."""
{agent_init_code}
    
    def _initialize_openai_client(self):
        """Initialize OpenAI client with fallback to Azure OpenAI."""
        try:
            return openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            print(f"Failed to initialize OpenAI client: {{str(e)}}")
            print("Falling back to Azure OpenAI...")
            
            try:
                return openai.AzureOpenAI(
                    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
                )
            except Exception as azure_error:
                print(f"Failed to initialize Azure OpenAI client: {{str(azure_error)}}")
                raise Exception("Failed to initialize any OpenAI client. Please check your API keys and configurations.")
    
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
        
        # Extract the message from the response
        message_text = ""
        if hasattr(response, 'artifacts') and response.artifacts:
            for artifact in response.artifacts:
                if 'parts' in artifact:
                    for part in artifact['parts']:
                        if part.get('type') == 'text':
                            message_text = part.get('message', '')
                            break
        
        # Format the response
        formatted_response = {{
            "dataType": "data",
            "message": message_text
        }}
        
        if isinstance(message_text, list):
            if all(isinstance(item, (dict, list)) for item in message_text):
                formatted_response["dataType"] = "table"
            else:
                formatted_response["dataType"] = "buttons"
        
        return {{
            "agent": agent_name,
            "confidence": confidence,
            "response": formatted_response
        }}
    
    def list_agents(self):
        """List all available agents in the network."""
        return self.network.list_agents()

'''

    def _generate_router_class(self, agent_configs: List[Dict[str, Any]]) -> str:
        """Generate the router class."""
        # Generate agent descriptions for the prompt
        agent_descriptions = "\n".join([
            f"{i+1}. {config['name']}: {config['description']}"
            for i, config in enumerate(agent_configs)
        ])
        
        # Generate routing guidelines
        routing_guidelines = "\n".join([
            f"- If the query is related to {config['description'].lower()}, route to '{config['name']}'"
            for config in agent_configs
        ])

        return f'''class AIRouterWithOpenAI(AIAgentRouter):
    """AI-powered router using OpenAI to make routing decisions."""
    
    def __init__(self, llm_client, agent_network):
        """Initialize the router with an OpenAI client and agent network."""
        self.client = llm_client
        self.agent_network = agent_network
        self.agent_descriptions = self._get_agent_descriptions()
    
    def _get_agent_descriptions(self):
        """Get descriptions of all agents in the network."""
        descriptions = {{}}
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
                    {{"role": "system", "content": prompt}},
                    {{"role": "user", "content": query}}
                ],
                temperature=0
            )
            
            result = response.choices[0].message.content.strip().lower()
            
            # Parse the response to determine the agent and confidence
            for agent_config in {agent_configs}:
                if agent_config['name'] in result:
                    return agent_config['name'], 0.9 if "high confidence" in result else 0.7
            
            # Default to first agent if unclear
            return {agent_configs[0]['name']}, 0.5
                
        except Exception as e:
            print(f"Error routing query: {{str(e)}}")
            # Default to first agent on error
            return {agent_configs[0]['name']}, 0.5
    
    def _build_routing_prompt(self, query):
        """Build a prompt for the routing decision."""
        return f"""
You are a query router for a multi-agent system. Your job is to determine which agent should handle a given query based on its content.

Available agents:
{agent_descriptions}

Guidelines:
{routing_guidelines}
- Look for explicit keywords related to each agent's functionality
- If the query could be handled by multiple agents, determine the primary intent
- If you're very confident in your decision, include "high confidence" in your response

Reply with only the name of the agent and your confidence level.
"""

'''

    def _generate_main_block(self, target_agent_name: str) -> str:
        """Generate the main execution block."""
        class_name = f"{target_agent_name.capitalize()}Agent"
        
        return f'''
async def process_user_input(network):
    """Process a single user input through the agent network."""
    print("\\nEnter your text to process (or 'exit' to quit):")
    user_input = input("> ").strip()
    
    if user_input.lower() == 'exit':
        return False
    
    if not user_input:
        print("Please enter some text to process.")
        return True
    
    try:
        result = await network.process_text(user_input)
        print(f"\\nQuery: {{user_input}}")
        print(f"Routed to: {{result['agent']}} (confidence: {{result['confidence']:.2f}})")
        print(f"Response: {{result['response']['message']}}")
    except Exception as e:
        print(f"Error processing input: {{str(e)}}")
    
    return True


if __name__ == "__main__":
    # Create the agent network
    network = {class_name}()
    
    # List available agents
    print("\\nAvailable Agents:")
    for agent in network.list_agents():
        print(f"- {{agent.get('name', 'Unnamed')}}: {{agent.get('description', 'No description')}}")
    
    print(f"\\nWelcome to the {target_agent_name.capitalize()} Network!")
    print("You can interact with the following agents:")
    for agent in network.list_agents():
        print(f"- {{agent.get('description', 'No description')}}")
    print("Type 'exit' to quit the program.")
    
    # Main interaction loop
    async def main_loop():
        should_continue = True
        while should_continue:
            should_continue = await process_user_input(network)
    
    # Run the main loop
    asyncio.run(main_loop())
    print(f"\\nThank you for using the {target_agent_name.capitalize()} Network!")
'''

def main():
    """Main function to demonstrate usage."""
    # Example agent configurations
    example_configs = [
        {
            "name": "summarizer",
            "type": "text",
            "port": 5001,
            "description": "Summarizes text content"
        },
        {
            "name": "translator",
            "type": "text",
            "port": 5002,
            "description": "Translates text to other languages"
        }
    ]
    
    # Create the generator
    generator = RouterAgentGenerator()
    
    # Generate the router file
    target_agent_name = "text_processing_1"
    file_content = generator.generate_router_file(example_configs, target_agent_name)
    
    # Write the generated content to a file
    output_filename = f"{target_agent_name}_router.py"
    with open(output_filename, "w") as f:
        f.write(file_content)
    
    print(f"Generated router file: {output_filename}")

if __name__ == "__main__":
    main() 