from agent_creation_scripts.create_agent_script import create_agent_file

file_path = create_agent_file(
    agent_name="My Agent",
    agent_url="https://api.example.com",
    agent_inputs=["input1", "input2"],
    agent_skills=["skill1", "skill2"],
    agent_description="My agent description",
    agent_goal="My agent goal",
    agent_tags=["tag1", "tag2"],
    agent_port=5002,  # Custom port
    overwrite=True
)