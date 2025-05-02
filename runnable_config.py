from datetime import datetime, timedelta
import os
import json
import pandas as pd
from typing import Dict, List, Optional, Any
from uuid import UUID
import shutil
from pathlib import Path

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
                "dataframes": {}
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
        
    def add_dataframe(self, session_id: UUID, name: str, df: pd.DataFrame) -> None:
        """Add a DataFrame to the session configuration."""
        config_file = self.get_session_dir(session_id) / "config.json"
        if not config_file.exists():
            self.create_session(session_id)
            
        with open(config_file, "r") as f:
            config = json.load(f)
            
        # Save DataFrame to CSV
        df_path = self.get_session_dir(session_id) / f"{name}.csv"
        df.to_csv(df_path, index=False)
        
        config["dataframes"][name] = {
            "path": str(df_path),
            "added_at": datetime.utcnow().isoformat()
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