from uuid import uuid4
from runnable_config import SessionConfig
from python_a2a import Message, Conversation, MessageRole, TextContent, A2AClient
import os
from pathlib import Path

def main():
    # Create a new session
    session_id = uuid4()
    session_config = SessionConfig()
    
    print(f"Created new session with ID: {session_id}")
    
    # Example 1: Conversation Storage
    print("\n=== Example 1: Storing Conversation ===")
    
    # Create a conversation
    conversation = Conversation()
    
    # Add user message
    user_message = Message(
        content=TextContent(text="Can you help me analyze this data?"),
        role=MessageRole.USER
    )
    conversation.add_message(user_message)
    
    # Store user message in session - using Message object directly
    session_config.add_conversation_message(session_id, user_message)
    
    # Simulate bot response
    bot_response = Message(
        content=TextContent(text="I'd be happy to help analyze your data!"),
        role=MessageRole.AGENT
    )
    conversation.add_message(bot_response)
    
    # Store bot response in session - using Message object directly
    session_config.add_conversation_message(session_id, bot_response)
    
    # Retrieve and print conversation history
    print("\nConversation History:")
    history = session_config.get_conversation_history(session_id)
    for msg in history:
        print(f"{msg.role.value}: {msg.content.text}")
    
    # Example 2: File Processing
    print("\n=== Example 2: Processing Files ===")
    
    # Create example files
    example_dir = Path("example_files")
    example_dir.mkdir(exist_ok=True)
    
    # Create a sample CSV file
    csv_content = "name,age,city\nJohn,30,New York\nAlice,25,London"
    csv_path = example_dir / "sample.csv"
    with open(csv_path, "w") as f:
        f.write(csv_content)
    
    # Create a sample text file for PDF simulation
    pdf_content = "This is a sample PDF content.\nIt has multiple lines.\nFor demonstration purposes."
    pdf_path = example_dir / "sample.pdf"
    with open(pdf_path, "w") as f:
        f.write(pdf_content)
    
    # Process CSV file
    print("\nProcessing CSV file...")
    csv_result = session_config.process_file(session_id, str(csv_path))
    print(f"CSV Processing Result: {csv_result}")
    
    # Get the DataFrame
    df = session_config.get_dataframe(session_id, csv_result["dataframe_name"])
    print("\nDataFrame contents:")
    print(df)
    
    # Process PDF file
    print("\nProcessing PDF file...")
    pdf_result = session_config.process_file(session_id, str(pdf_path))
    print(f"PDF Processing Result: {pdf_result}")
    
    # List all files in the session
    print("\nAll files in session:")
    files = session_config.get_session_files(session_id)
    for file in files:
        print(f"- {file['path']} (type: {file['type']})")
    
    # Cleanup
    print("\nCleaning up example files...")
    for file in example_dir.glob("*"):
        file.unlink()
    example_dir.rmdir()

if __name__ == "__main__":
    main() 