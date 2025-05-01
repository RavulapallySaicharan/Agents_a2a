import os
import json
from typing import List, Dict, Any, Union, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import openai
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

class WorkflowType(Enum):
    """Enum for different workflow types."""
    LINEAR = "linear"
    PARALLEL = "parallel"
    MIXED = "mixed"

@dataclass
class AgentConfig:
    """Data class for agent configuration."""
    name: str
    type: str
    port: Union[int, str]
    description: str
    tools: Optional[List[str]] = None
    parallel_group: Optional[int] = None  # Group number for parallel execution

@dataclass
class WorkflowPattern:
    """Data class for workflow pattern."""
    type: WorkflowType
    pattern: str
    steps: List[Union[str, List[str]]]

class WorkflowPatternParser:
    """Parser for workflow pattern strings."""
    
    @staticmethod
    def parse_pattern(pattern: str) -> WorkflowPattern:
        """Parse a workflow pattern string into a WorkflowPattern object."""
        # Check if pattern contains parallel groups (comma-separated)
        if ',' in pattern:
            # Parse parallel workflow
            parallel_groups = pattern.split('->')
            steps = []
            
            for group in parallel_groups:
                if ',' in group:
                    # This is a parallel group
                    parallel_agents = [agent.strip() for agent in group.split(',')]
                    steps.append(parallel_agents)
                else:
                    # This is a sequential step
                    steps.append(group.strip())
            
            return WorkflowPattern(
                type=WorkflowType.MIXED,
                pattern=pattern,
                steps=steps
            )
        else:
            # Parse linear workflow
            steps = [step.strip() for step in pattern.split('->')]
            return WorkflowPattern(
                type=WorkflowType.LINEAR,
                pattern=pattern,
                steps=steps
            )

class WorkflowAgentGenerator:
    """Generates workflow-based multi-agent orchestration scripts."""
    
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
            
            if 'tools' in config and not isinstance(config['tools'], list):
                raise ValueError("Tools must be a list")
        
        return True

    def generate_workflow_file(
        self,
        agent_configs: List[Dict[str, Any]],
        workflow_type: WorkflowType,
        workflow_name: str,
        workflow_steps: Optional[List[str]] = None,
        workflow_pattern: Optional[str] = None
    ) -> str:
        """Generate the workflow-based multi-agent setup file content."""
        if not self.validate_agent_configs(agent_configs):
            return ""

        # Parse workflow pattern if provided
        if workflow_pattern:
            pattern = WorkflowPatternParser.parse_pattern(workflow_pattern)
            workflow_type = pattern.type
            workflow_steps = pattern.steps

        # Generate the file content
        file_content = self._generate_imports()
        file_content += self._generate_workflow_class(
            agent_configs,
            workflow_type,
            workflow_name,
            workflow_steps
        )
        file_content += self._generate_main_block(workflow_name)
        
        return file_content

    def _generate_imports(self) -> str:
        """Generate the imports section of the file."""
        return '''from python_a2a import AgentNetwork, Flow, AIAgentRouter
import asyncio
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

'''

    def _generate_workflow_class(
        self,
        agent_configs: List[Dict[str, Any]],
        workflow_type: WorkflowType,
        workflow_name: str,
        workflow_steps: Optional[List[Union[str, List[str]]]] = None
    ) -> str:
        """Generate the workflow class."""
        class_name = f"{workflow_name.capitalize()}Workflow"
        
        # Generate agent initialization code
        agent_init_code = "        # Set up agent network\n"
        agent_init_code += f"        self.network = AgentNetwork(name=\"{workflow_name.capitalize()} Network\")\n\n"
        agent_init_code += "        # Add agents to the network\n"
        
        for config in agent_configs:
            agent_init_code += f"        {config['name']}_url = f\"http://localhost:{config['port']}\"\n"
            agent_init_code += f"        self.network.add(\"{config['name']}\", {config['name']}_url)\n"
        
        agent_init_code += "\n        # Create a router\n"
        agent_init_code += "        self.router = AIAgentRouter(\n"
        agent_init_code += f"            llm_client=self.network.get_agent(\"{agent_configs[0]['name']}\"),\n"
        agent_init_code += "            agent_network=self.network\n"
        agent_init_code += "        )\n\n"
        
        # Generate workflow definition code
        workflow_code = "        # Define the workflow\n"
        workflow_code += f"        self.flow = Flow(agent_network=self.network, router=self.router, name=\"{workflow_name.capitalize()} Workflow\")\n\n"
        
        if workflow_type == WorkflowType.LINEAR:
            workflow_code += self._generate_linear_workflow(agent_configs, workflow_steps)
        elif workflow_type == WorkflowType.PARALLEL:
            workflow_code += self._generate_parallel_workflow(agent_configs, workflow_steps)
        else:  # MIXED
            workflow_code += self._generate_mixed_workflow(agent_configs, workflow_steps)

        return f'''class {class_name}:
    """A workflow-based multi-agent system for {workflow_name}."""
    
    def __init__(self):
        """Initialize the workflow with configured agents."""
{agent_init_code}{workflow_code}
    
    async def process_query(self, query: str, context: Optional[Dict] = None) -> Dict:
        """Process a query through the workflow."""
        try:
            # Prepare the initial context
            initial_context = {{"query": query}}
            if context:
                initial_context.update(context)
            
            # Execute the workflow
            result = await self.flow.run(initial_context)
            
            return {{
                "workflow": "{workflow_name}",
                "status": "completed",
                "result": result
            }}
        except Exception as e:
            raise Exception(f"Error processing query: {{str(e)}}")
    
    def list_agents(self) -> List[Dict]:
        """List all available agents in the network."""
        return [
            {{
                "name": config["name"],
                "description": config["description"],
                "tools": config.get("tools", []),
                "parallel_group": config.get("parallel_group")
            }}
            for config in {agent_configs}
        ]

'''

    def _generate_linear_workflow(
        self,
        agent_configs: List[Dict[str, Any]],
        workflow_steps: Optional[List[Union[str, List[str]]]] = None
    ) -> str:
        """Generate linear workflow steps."""
        workflow_code = "        # Define linear workflow steps\n"
        
        if workflow_steps:
            # Use provided workflow steps
            for i, step in enumerate(workflow_steps):
                if isinstance(step, list):
                    raise ValueError("Linear workflow cannot contain parallel steps")
                agent_name = step
                workflow_code += f"        # Step {i+1}: {agent_name}\n"
                workflow_code += f"        self.flow.ask(\"{agent_name}\", \"Process the query: {{query}}\")\n\n"
        else:
            # Generate default workflow steps
            for i, config in enumerate(agent_configs):
                workflow_code += f"        # Step {i+1}: {config['description']}\n"
                workflow_code += f"        self.flow.ask(\"{config['name']}\", \"Process the query: {{query}}\")\n\n"
        
        return workflow_code

    def _generate_parallel_workflow(
        self,
        agent_configs: List[Dict[str, Any]],
        workflow_steps: Optional[List[Union[str, List[str]]]] = None
    ) -> str:
        """Generate parallel workflow steps."""
        workflow_code = "        # Define parallel workflow steps\n"
        workflow_code += "        # Start parallel processing\n"
        workflow_code += "        parallel_flow = self.flow.parallel()\n\n"
        
        if workflow_steps:
            # Use provided workflow steps
            for i, step in enumerate(workflow_steps):
                if isinstance(step, list):
                    raise ValueError("Parallel workflow cannot contain linear steps")
                agent_name = step
                workflow_code += f"        # Branch {i+1}: {agent_name}\n"
                workflow_code += f"        parallel_flow.ask(\"{agent_name}\", \"Process the query: {{query}}\")\n"
                if i < len(workflow_steps) - 1:
                    workflow_code += "        parallel_flow.branch()\n"
        else:
            # Generate default workflow steps
            for i, config in enumerate(agent_configs):
                workflow_code += f"        # Branch {i+1}: {config['description']}\n"
                workflow_code += f"        parallel_flow.ask(\"{config['name']}\", \"Process the query: {{query}}\")\n"
                if i < len(agent_configs) - 1:
                    workflow_code += "        parallel_flow.branch()\n"
        
        workflow_code += "\n        # End parallel processing\n"
        workflow_code += "        parallel_flow.end_parallel()\n"
        
        return workflow_code

    def _generate_mixed_workflow(
        self,
        agent_configs: List[Dict[str, Any]],
        workflow_steps: Optional[List[Union[str, List[str]]]] = None
    ) -> str:
        """Generate mixed workflow steps with both linear and parallel execution."""
        workflow_code = "        # Define mixed workflow steps\n"
        
        if workflow_steps:
            # Use provided workflow steps
            current_step = 1
            for step in workflow_steps:
                if isinstance(step, list):
                    # This is a parallel group
                    workflow_code += f"        # Parallel Group {current_step}\n"
                    workflow_code += "        parallel_flow = self.flow.parallel()\n\n"
                    
                    for i, agent_name in enumerate(step):
                        workflow_code += f"        # Branch {i+1}: {agent_name}\n"
                        workflow_code += f"        parallel_flow.ask(\"{agent_name}\", \"Process the query: {{query}}\")\n"
                        if i < len(step) - 1:
                            workflow_code += "        parallel_flow.branch()\n"
                    
                    workflow_code += "\n        # End parallel processing\n"
                    workflow_code += "        parallel_flow.end_parallel()\n\n"
                else:
                    # This is a sequential step
                    workflow_code += f"        # Step {current_step}: {step}\n"
                    workflow_code += f"        self.flow.ask(\"{step}\", \"Process the query: {{query}}\")\n\n"
                
                current_step += 1
        else:
            # Generate default workflow steps based on parallel_group
            parallel_groups: Dict[int, List[Tuple[int, Dict[str, Any]]]] = {}
            sequential_agents: List[Tuple[int, Dict[str, Any]]] = []
            
            for i, config in enumerate(agent_configs):
                if config.get('parallel_group') is not None:
                    group = config['parallel_group']
                    if group not in parallel_groups:
                        parallel_groups[group] = []
                    parallel_groups[group].append((i, config))
                else:
                    sequential_agents.append((i, config))
            
            # Sort sequential agents by their original order
            sequential_agents.sort(key=lambda x: x[0])
            
            # Generate workflow steps
            current_step = 1
            
            for i, config in sequential_agents:
                workflow_code += f"        # Step {current_step}: {config['description']}\n"
                workflow_code += f"        self.flow.ask(\"{config['name']}\", \"Process the query: {{query}}\")\n\n"
                current_step += 1
            
            # Add parallel groups
            for group_num, group_agents in sorted(parallel_groups.items()):
                workflow_code += f"        # Parallel Group {group_num}\n"
                workflow_code += "        parallel_flow = self.flow.parallel()\n\n"
                
                for i, config in group_agents:
                    workflow_code += f"        # Branch {i+1}: {config['description']}\n"
                    workflow_code += f"        parallel_flow.ask(\"{config['name']}\", \"Process the query: {{query}}\")\n"
                    if i < len(group_agents) - 1:
                        workflow_code += "        parallel_flow.branch()\n"
                
                workflow_code += "\n        # End parallel processing\n"
                workflow_code += "        parallel_flow.end_parallel()\n\n"
        
        return workflow_code

    def _generate_main_block(self, workflow_name: str) -> str:
        """Generate the main execution block."""
        class_name = f"{workflow_name.capitalize()}Workflow"
        
        return f'''
async def main():
    """Main function to demonstrate the workflow."""
    # Create the workflow
    workflow = {class_name}()
    
    # List available agents
    print("\\nAvailable Agents:")
    for agent in workflow.list_agents():
        print(f"- {{agent['name']}}: {{agent['description']}}")
        if agent.get('tools'):
            print(f"  Tools: {{', '.join(agent['tools'])}}")
    
    print(f"\\nWelcome to the {workflow_name.capitalize()} Workflow!")
    print("You can interact with the following agents:")
    for agent in workflow.list_agents():
        print(f"- {{agent['description']}}")
    
    # Example query
    query = "Example query to process"
    context = {{"additional_context": "Some additional context"}}
    
    try:
        result = await workflow.process_query(query, context)
        print("\\nWorkflow result:")
        print(result)
    except Exception as e:
        print(f"Error: {{str(e)}}")

if __name__ == "__main__":
    asyncio.run(main())
'''

def main():
    """Main function to demonstrate usage."""
    # Example agent configurations
    example_configs = [
        {
            "name": "nlq_reconstruction",
            "type": "text",
            "port": 5007,
            "description": "Reconstructs natural language queries",
            "tools": ["query_analyzer", "context_extractor"]
        },
        {
            "name": "gating",
            "type": "text",
            "port": 5008,
            "description": "Determines if query requires SQL generation",
            "tools": ["query_classifier"]
        },
        {
            "name": "dynamic_few_shots",
            "type": "text",
            "port": 5009,
            "description": "Generates relevant few-shot examples",
            "tools": ["example_generator"]
        },
        {
            "name": "sql_generation",
            "type": "text",
            "port": 5010,
            "description": "Generates SQL queries",
            "tools": ["sql_builder", "query_validator"]
        }
    ]
    
    # Create the generator
    generator = WorkflowAgentGenerator()
    
    # Example workflow patterns
    linear_pattern = "nlq_reconstruction->gating->dynamic_few_shots->sql_generation"
    mixed_pattern = "nlq_reconstruction->gating,dynamic_few_shots->sql_generation"
    
    # Generate workflow files
    for pattern, name in [(linear_pattern, "text2sql_linear"), (mixed_pattern, "text2sql_mixed")]:
        file_content = generator.generate_workflow_file(
            example_configs,
            WorkflowType.MIXED,  # Type will be overridden by pattern
            name,
            workflow_pattern=pattern
        )
        
        # Write the workflow content to a file
        output_filename = f"{name}.py"
        with open(output_filename, "w") as f:
            f.write(file_content)
        
        print(f"Generated workflow file: {output_filename}")

if __name__ == "__main__":
    main() 