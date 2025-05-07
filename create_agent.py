from agent_creation_scripts.create_agent_script import create_agent_file

# Example 1: Create an API-based agent
api_agent_path = create_agent_file(
    agent_name="API Agent",
    agent_url="https://api.example.com",
    agent_inputs=["input1", "input2"],
    agent_skills=["skill1", "skill2"],
    agent_description="Processes data through an external API",
    agent_goal="Transform input data using external API",
    agent_tags=["api", "data"],
    agent_port=5002,
    overwrite=True
)

# Example 2: Create an LLM-based agent
llm_agent_path = create_agent_file(
    agent_name="LLM Agent",
    agent_inputs=["text", "max_length"],
    agent_skills=["process", "validate"],
    agent_description="Processes text using LLM",
    agent_goal="Transform and analyze text using LLM capabilities",
    agent_tags=["llm", "text"],
    agent_port=5003,
    overwrite=True
)