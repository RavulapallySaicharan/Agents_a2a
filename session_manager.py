from typing import Dict, Optional
from uuid import UUID
from runnable_config import SessionConfig
from datetime import datetime, timedelta
import threading

class SessionManager:
    def __init__(self, base_dir: str = "temp_storage", max_age_hours: int = 4):
        self._sessions: Dict[UUID, SessionConfig] = {}
        self._lock = threading.Lock()
        self.base_dir = base_dir
        self.max_age_hours = max_age_hours
        self.max_age = timedelta(hours=max_age_hours)
        
    def get_session(self, session_id: UUID) -> Optional[SessionConfig]:
        """Get a session configuration by ID."""
        with self._lock:
            return self._sessions.get(session_id)
            
    def create_session(self, session_id: UUID) -> SessionConfig:
        """Create a new session configuration."""
        with self._lock:
            if session_id not in self._sessions:
                session_config = SessionConfig(
                    base_dir=f"{self.base_dir}/{session_id}",
                    max_age_hours=self.max_age_hours
                )
                self._sessions[session_id] = session_config
                session_config.create_session(session_id)
            return self._sessions[session_id]
            
    def cleanup_old_sessions(self) -> None:
        """Remove sessions older than max_age."""
        current_time = datetime.utcnow()
        with self._lock:
            sessions_to_remove = []
            for session_id, session_config in self._sessions.items():
                session = session_config.get_session(session_id)
                if session:
                    created_at = datetime.fromisoformat(session["created_at"])
                    if current_time - created_at > self.max_age:
                        sessions_to_remove.append(session_id)
                        
            for session_id in sessions_to_remove:
                del self._sessions[session_id]
                
    def cleanup_all(self) -> None:
        """Remove all sessions."""
        with self._lock:
            self._sessions.clear()
            
    def get_all_sessions(self) -> Dict[str, Dict]:
        """Get information about all active sessions."""
        with self._lock:
            sessions_info = {}
            for session_id, session_config in self._sessions.items():
                session = session_config.get_session(session_id)
                if session:
                    # Count unique files (each file is a dict with one key)
                    file_count = len(session.get("files", []))
                    sessions_info[str(session_id)] = {
                        "created_at": session["created_at"],
                        "last_updated": session["last_updated"],
                        "file_count": file_count,
                        "dataframe_count": len(session.get("dataframes", {})),
                        "message_count": len(session.get("conversation", {}).get("messages", []))
                    }
            return sessions_info 