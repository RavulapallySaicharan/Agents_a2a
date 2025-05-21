from datetime import datetime, timedelta
from python_a2a import Message, Conversation, MessageRole, TextContent
import os
import json
import pandas as pd
from typing import Dict, List, Optional, Any, Union
from uuid import UUID
import shutil
from pathlib import Path
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent

class SessionConfig:
    def __init__(self, base_dir: str = "temp_storage", max_age_hours: int = 4):
        self.base_dir = Path(base_dir)
        self.max_age = timedelta(hours=max_age_hours)
        self._ensure_base_dir()
        
    def _ensure_base_dir(self):
        """Ensure the base directory exists."""
        self.base_dir.mkdir(exist_ok=True)
        
    def get_session_dir(self, session_id: UUID) -> Path:
        """Get the directory for a specific session."""
        session_dir = self.base_dir / str(session_id)
        session_dir.mkdir(exist_ok=True)
        return session_dir
        
    def create_session(self, session_id: UUID) -> None:
        """Create a new session configuration."""
        session_dir = self.get_session_dir(session_id)
        config_file = session_dir / "config.json"
        
        if not config_file.exists():
            config = {
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "agent_type": None,
                "current_state": "initialized",
                "metadata": {},
                "files": [],
                "dataframes": {},
                "conversation": Conversation(),  # Initialize an empty conversation
                "dataset_descriptions": {}  # Store dataset descriptions
            }
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)
                
    def get_session(self, session_id: UUID) -> Dict[str, Any]:
        """Get the configuration for a specific session."""
        config_file = self.get_session_dir(session_id) / "config.json"
        if not config_file.exists():
            return None
            
        with open(config_file, "r") as f:
            return json.load(f)
            
    def update_context(self, session_id: UUID, context: Dict[str, Any]) -> None:
        """Update the session context."""
        config_file = self.get_session_dir(session_id) / "config.json"
        if not config_file.exists():
            self.create_session(session_id)
            
        with open(config_file, "r") as f:
            config = json.load(f)
            
        config.update(context)
        config["last_updated"] = datetime.utcnow().isoformat()
        
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
            
    def add_file_path(self, session_id: UUID, file_path: str, file_type: str) -> None:
        """Add a file path to the session configuration."""
        config_file = self.get_session_dir(session_id) / "config.json"
        if not config_file.exists():
            self.create_session(session_id)
            
        with open(config_file, "r") as f:
            config = json.load(f)
            
        config["files"].append({
            "path": file_path,
            "type": file_type,
            "added_at": datetime.utcnow().isoformat()
        })
        config["last_updated"] = datetime.utcnow().isoformat()
        
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
            
    def get_session_files(self, session_id: UUID, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all files associated with a session, optionally filtered by type."""
        config = self.get_session(session_id)
        if not config:
            return []
            
        files = config.get("files", [])
        if file_type:
            return [f for f in files if f["type"] == file_type]
        return files
        
    def get_dataset_description(self, df: pd.DataFrame) -> str:
        """Get a description of the dataset using LangChain."""
        try:
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
            agent_executor = create_pandas_dataframe_agent(
                llm,
                df,
                agent_type="tool-calling",
                verbose=False
            )
            result = agent_executor.invoke({"input": "describe the dataframe"})
            return result.get("output", "No description available")
        except Exception as e:
            return f"Error generating description: {str(e)}"

    def add_dataframe(self, session_id: UUID, name: str, df: pd.DataFrame) -> None:
        """Add a DataFrame to the session configuration with its description."""
        config_file = self.get_session_dir(session_id) / "config.json"
        if not config_file.exists():
            self.create_session(session_id)
            
        with open(config_file, "r") as f:
            config = json.load(f)
            
        # Save DataFrame to CSV
        df_path = self.get_session_dir(session_id) / f"{name}.csv"
        df.to_csv(df_path, index=False)
        
        # Get dataset description
        description = self.get_dataset_description(df)
        
        config["dataframes"][name] = {
            "path": str(df_path),
            "added_at": datetime.utcnow().isoformat(),
            "description": description
        }
        config["last_updated"] = datetime.utcnow().isoformat()
        
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
            
    def get_dataframe(self, session_id: UUID, name: str) -> Optional[pd.DataFrame]:
        """Get a DataFrame from the session configuration."""
        config = self.get_session(session_id)
        if not config:
            return None
            
        df_info = config["dataframes"].get(name)
        if not df_info:
            return None
            
        df_path = Path(df_info["path"])
        if not df_path.exists():
            return None
            
        return pd.read_csv(df_path)
        
    def get_dataframe_description(self, session_id: UUID, name: str) -> Optional[str]:
        """Get the description of a DataFrame."""
        config = self.get_session(session_id)
        if not config:
            return None
            
        df_info = config["dataframes"].get(name)
        if not df_info:
            return None
            
        return df_info.get("description")
        
    def cleanup_old_sessions(self) -> None:
        """Remove sessions older than max_age."""
        current_time = datetime.utcnow()
        for session_dir in self.base_dir.iterdir():
            if not session_dir.is_dir():
                continue
                
            config_file = session_dir / "config.json"
            if not config_file.exists():
                continue
                
            with open(config_file, "r") as f:
                config = json.load(f)
                
            created_at = datetime.fromisoformat(config["created_at"])
            if current_time - created_at > self.max_age:
                shutil.rmtree(session_dir)
                
    def cleanup_all(self) -> None:
        """Remove all session data."""
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)
        self._ensure_base_dir()

    def add_conversation_message(self, session_id: UUID, message: Union[Message, Dict[str, Any]]) -> None:
        """Add a message to the conversation history.
        
        Args:
            session_id: The session ID
            message: Either a python_a2a Message object or a dictionary with message details
        """
        config_file = self.get_session_dir(session_id) / "config.json"
        if not config_file.exists():
            self.create_session(session_id)
            
        with open(config_file, "r") as f:
            config = json.load(f)
            
        # Convert dictionary to Message if needed
        if isinstance(message, dict):
            message = Message(
                content=TextContent(text=message["content"]),
                role=MessageRole.USER if message["role"] == "user" else MessageRole.AGENT
            )

        config["conversation"].add_message(message)
        
        config["last_updated"] = datetime.utcnow().isoformat()
        
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
            
    def get_conversation_history(self, session_id: UUID) -> List[Message]:
        """Get the conversation history for a session as Message objects."""
        config = self.get_session(session_id)
        if not config:
            return []
            
        messages = []
        for msg in config.get("conversations", []):
            message = Message(
                content=TextContent(text=msg["content"]),
                role=MessageRole.USER if msg["role"] == "user" else MessageRole.AGENT
            )
            messages.append(message)
            
        return messages

    def process_pdf_file(self, session_id: UUID, file_path: str) -> str:
        """Extract text from a PDF file and store it."""
        session_dir = self.get_session_dir(session_id)
        pdf_path = Path(file_path)
        
        # Extract text from PDF
        text_content = []
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text_content.append(page.get_text())
        
        # Save extracted text
        text_file = session_dir / f"{pdf_path.stem}_text.txt"
        with open(text_file, "w", encoding="utf-8") as f:
            f.write("\n".join(text_content))
            
        return str(text_file)
        
    def process_image_file(self, session_id: UUID, file_path: str) -> str:
        """Extract text from an image file using OCR and store it."""
        session_dir = self.get_session_dir(session_id)
        image_path = Path(file_path)
        
        # Extract text using OCR
        image = Image.open(image_path)
        text_content = pytesseract.image_to_string(image)
        
        # Save extracted text
        text_file = session_dir / f"{image_path.stem}_text.txt"
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(text_content)
            
        return str(text_file)
        
    def process_csv_file(self, session_id: UUID, file_path: str) -> str:
        """Process a CSV file and store it as a DataFrame with description."""
        session_dir = self.get_session_dir(session_id)
        csv_path = Path(file_path)
        
        # Read CSV into DataFrame
        df = pd.read_csv(csv_path)
        
        # Save DataFrame with unique name
        df_name = f"df_{csv_path.stem}"
        self.add_dataframe(session_id, df_name, df)
        
        return df_name

    def process_file(self, session_id: UUID, file_path: str) -> Dict[str, Any]:
        """Process a file based on its type and store the results."""
        file_path = Path(file_path)
        file_type = file_path.suffix.lower()
        
        result = {
            "original_path": str(file_path),
            "processed_at": datetime.utcnow().isoformat(),
            "file_type": file_type
        }
        
        try:
            if file_type == ".pdf":
                result["processed_path"] = self.process_pdf_file(session_id, str(file_path))
                result["content_type"] = "text"
            elif file_type in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
                result["processed_path"] = self.process_image_file(session_id, str(file_path))
                result["content_type"] = "text"
            elif file_type == ".csv":
                result["dataframe_name"] = self.process_csv_file(session_id, str(file_path))
                result["content_type"] = "dataframe"
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
            # Add file to session configuration
            self.add_file_path(session_id, str(file_path), file_type[1:])  # Remove the dot from extension
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            return result 