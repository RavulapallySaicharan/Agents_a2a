from dotenv import load_dotenv
from python_a2a import AgentNetwork, AIAgentRouter, Message, Conversation, MessageRole, TextContent, A2AClient
import openai
import os
import time
import requests


client = A2AClient("http://localhost:5051")


# Create a conversation
conversation = Conversation()

try:
    while True:
        # Get user input
        user_input = input("You: ")
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit", "q"]:
            print("\nExiting interactive mode.")
            break
        
        # Skip empty messages
        if not user_input.strip():
            continue
        
        # Create a message and add it to the conversation
        user_message = Message(
            content=TextContent(text=user_input),
            role=MessageRole.USER
        )
        conversation.add_message(user_message)
        
        try:
            # Print "thinking" indicator
            print(f"\nAgent is thinking...", end="", flush=True)
            
            # Time the response
            start_time = time.time()
            
            # Get the response by sending the conversation
            # conversation = client.send_conversation(conversation)
            bot_response = client.send_message(user_message)

            # print(bot_response)

            conversation.add_message(bot_response)
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            
            # Clear the "thinking" indicator
            print("\r" + " " * 30 + "\r", end="", flush=True)
            
            # Extract the latest response
            latest_response = conversation.messages[-1]
            
            # Print the response with timing info
            print(f"Agent ({elapsed_time:.2f}s): {latest_response.content.text}\n")


        except Exception as e:
            # Clear the "thinking" indicator
            print("\r" + " " * 30 + "\r", end="", flush=True)
            
            print(f"\n❌ Error: {e}")
            print("Try sending a different message.\n")

except KeyboardInterrupt:
    print("\n\nSession ended by user.")

# Print the full conversation summary at the end
print("=================================================================")
print(conversation)
message_count = len(conversation.messages)
print(f"\n=== Conversation Summary ===")
print(f"Total messages: {message_count}")
print(f"User messages: {sum(1 for m in conversation.messages if m.role == MessageRole.USER)}")
print(f"Assistant messages: {sum(1 for m in conversation.messages if m.role == MessageRole.AGENT)}")