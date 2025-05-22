from dotenv import load_dotenv
from python_a2a import AgentNetwork, AIAgentRouter, Message, Conversation, MessageRole, TextContent, A2AClient
from runnable_config import SessionConfig
import openai
import os
import time
import requests
import json
import subprocess
import sys
from uuid import uuid4, UUID

def load_agent_config():
    with open('agents/config.json', 'r') as f:
        return json.load(f)

def display_available_agents(config):
    print("\nAvailable Agents:")
    print("================")
    for idx, agent in enumerate(config['agents'], 1):
        print(f"{idx}. {agent['name']} - {agent['description']}")
        print(f"   Skills: {', '.join(skill['name'] for skill in agent['skills'])}")
        print()

def get_agent_url(port, agent_file):
    # Construct the path to the agent file
    # agent_path = os.path.join('agents', agent_file)
    
    # # Check if the file exists
    # if not os.path.exists(agent_path):
    #     raise FileNotFoundError(f"Agent file not found: {agent_path}")
    
    # try:
    #     # Run the agent file in the background
    #     if sys.platform == 'win32':
    #         # Windows
    #         subprocess.Popen([sys.executable, agent_path], 
    #                        creationflags=subprocess.CREATE_NEW_CONSOLE)
    #     else:
    #         # Unix-like systems
    #         subprocess.Popen([sys.executable, agent_path],
    #                        stdout=subprocess.DEVNULL,
    #                        stderr=subprocess.DEVNULL)
        
    #     # Wait a moment for the agent to start
    #     time.sleep(2)
        
    #     return f"http://localhost:{port}"
    # except Exception as e:
    #     raise Exception(f"Failed to start agent: {str(e)}")
    return f"http://localhost:{port}"

def collect_agent_inputs(agent):
    """Collect all required inputs for the selected agent based on its configuration."""
    inputs = {}
    
    # Get all skills and their required inputs
    for skill in agent['skills']:
        print(f"\nCollecting inputs for skill: {skill['name']}")
        print(f"Description: {skill['description']}")
        
        for input_param in skill['inputs']:
            # Handle special cases for certain input types
            if input_param == 'target_language':
                print("\nAvailable languages:")
                print("1. Spanish")
                print("2. French")
                print("3. German")
                print("4. Italian")
                print("5. Portuguese")
                print("6. Chinese")
                print("7. Japanese")
                print("8. Korean")
                print("9. Russian")
                print("10. Arabic")
                lang_choice = input(f"Select target language (1-10): ")
                lang_map = {
                    "1": "Spanish", "2": "French", "3": "German", "4": "Italian",
                    "5": "Portuguese", "6": "Chinese", "7": "Japanese", "8": "Korean",
                    "9": "Russian", "10": "Arabic"
                }
                inputs[input_param] = lang_map.get(lang_choice, "English")
            
            elif input_param == 'analysis_type':
                print("\nAvailable analysis types:")
                print("1. Sentiment Analysis")
                print("2. Topic Analysis")
                print("3. Keyword Extraction")
                print("4. Entity Recognition")
                analysis_choice = input(f"Select analysis type (1-4): ")
                analysis_map = {
                    "1": "sentiment", "2": "topic", "3": "keywords", "4": "entities"
                }
                inputs[input_param] = analysis_map.get(analysis_choice, "sentiment")
            
            elif input_param == 'chart_type':
                print("\nAvailable chart types:")
                print("1. Bar Chart")
                print("2. Line Chart")
                print("3. Pie Chart")
                print("4. Scatter Plot")
                print("5. Heat Map")
                chart_choice = input(f"Select chart type (1-5): ")
                chart_map = {
                    "1": "bar", "2": "line", "3": "pie", "4": "scatter", "5": "heatmap"
                }
                inputs[input_param] = chart_map.get(chart_choice, "bar")
            
            elif input_param == 'query_type':
                print("\nAvailable query types:")
                print("1. SELECT")
                print("2. INSERT")
                print("3. UPDATE")
                print("4. DELETE")
                query_choice = input(f"Select query type (1-4): ")
                query_map = {
                    "1": "select", "2": "insert", "3": "update", "4": "delete"
                }
                inputs[input_param] = query_map.get(query_choice, "select")
            
            else:
                # For other input parameters, just ask for text input
                value = input(f"Enter {input_param}: ")
                inputs[input_param] = value
    
    return inputs

def format_inputs_for_agent(inputs):
    """Format the collected inputs into a structured message for the agent."""
    # Convert inputs to a JSON-like string format
    formatted_inputs = json.dumps(inputs, indent=2)
    return formatted_inputs

def main():
    # Initialize session management
    session_id = uuid4()
    session_config = SessionConfig()
    session_config.create_session(session_id)
    
    print(f"Created new session with ID: {session_id}")
    
    # Load agent configuration
    config = load_agent_config()
    
    # Display available agents
    display_available_agents(config)
    
    # Get user's agent selection
    while True:
        try:
            selection = int(input("Select an agent (enter number): "))
            if 1 <= selection <= len(config['agents']):
                selected_agent = config['agents'][selection - 1]
                break
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")
    
    try:
        # Create client for selected agent
        agent_url = get_agent_url(selected_agent['port'], selected_agent['file'])
        client = A2AClient(agent_url)
        
        print(f"\nConnected to {selected_agent['name']} on port {selected_agent['port']}")
        
        # Collect all required inputs for the agent
        agent_inputs = collect_agent_inputs(selected_agent)
        
        # Format the inputs into a message
        formatted_inputs = format_inputs_for_agent(agent_inputs)
        
        # Create a message with the formatted inputs
        user_message = Message(
            content=TextContent(text=formatted_inputs),
            role=MessageRole.USER
        )
        
        # Add user message to session
        session_config.add_conversation_message(session_id, user_message)
        
        try:
            # Print "thinking" indicator
            print(f"\nAgent is thinking...", end="", flush=True)
            
            # Time the response
            start_time = time.time()
            
            # Get the response by sending the message
            bot_response = client.send_message(user_message)
            
            # Add bot response to session
            session_config.add_conversation_message(session_id, bot_response)
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            
            # Clear the "thinking" indicator
            print("\r" + " " * 30 + "\r", end="", flush=True)
            
            # Print the response with timing info
            print(f"Agent ({elapsed_time:.2f}s): {bot_response.content.text}\n")

        except Exception as e:
            # Clear the "thinking" indicator
            print("\r" + " " * 30 + "\r", end="", flush=True)
            
            print(f"\n❌ Error: {e}")
            print("Try sending a different message.\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Failed to start the agent. Please try again.")
        return

    # Get conversation history from session
    conversation_history = session_config.get_conversation_history(session_id)
    
    # Print the full conversation summary at the end
    print("=================================================================")
    print(f"Session ID: {session_id}")
    print(f"\n=== Conversation Summary ===")
    print(f"Total messages: {len(conversation_history)}")
    print(f"User messages: {sum(1 for m in conversation_history if m.role == MessageRole.USER)}")
    print(f"Assistant messages: {sum(1 for m in conversation_history if m.role == MessageRole.AGENT)}")
    
    # Print conversation history
    print("\n=== Conversation History ===")
    for msg in conversation_history:
        print(f"{msg.role.value}: {msg.content.text}")

if __name__ == "__main__":
    main()