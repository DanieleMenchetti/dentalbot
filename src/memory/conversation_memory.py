import json
import os
from datetime import datetime
from typing import List, Dict, Literal
from pathlib import Path


class ConversationMemory:
    def __init__(self, storage_dir: str = "./conversations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.current_session_file = self.storage_dir / "current_session.json"
        self.history_file = self.storage_dir / "conversation_history.json"

    def _load_json(self, file_path: Path) -> Dict:
        """Load JSON file if it exists, return empty dict otherwise."""
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_json(self, file_path: Path, data: Dict):
        """Save data to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_message(self, role: Literal["human", "assistant"], content: str):
        """Add a message to the current conversation."""
        messages = self._load_json(self.current_session_file)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        if "messages" not in messages:
            messages["messages"] = []
        
        messages["messages"].append(message)
        messages["last_updated"] = datetime.now().isoformat()
        
        self._save_json(self.current_session_file, messages)

    def get_conversation_history(self) -> List[Dict]:
        """Get the current conversation history."""
        data = self._load_json(self.current_session_file)
        return data.get("messages", [])

    def clear_current_session(self):
        """Clear the current session and archive it."""
        current_messages = self.get_conversation_history()
        
        if current_messages:
            # Archive current session to history
            history = self._load_json(self.history_file)
            if "sessions" not in history:
                history["sessions"] = []
            
            session = {
                "messages": current_messages,
                "started_at": current_messages[0].get("timestamp") if current_messages else datetime.now().isoformat(),
                "ended_at": datetime.now().isoformat()
            }
            
            history["sessions"].append(session)
            self._save_json(self.history_file, history)
        
        # Clear current session
        if self.current_session_file.exists():
            self.current_session_file.unlink()

    def get_formatted_history(self) -> str:
        """Get formatted conversation history for LLM context."""
        messages = self.get_conversation_history()
        formatted = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            formatted.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(formatted)

    def get_messages_for_agent(self) -> List[str]:
        """Get messages in format suitable for agents (list of strings)."""
        messages = self.get_conversation_history()
        return [msg["content"] for msg in messages]

    def save_to_history(self):
        """Save current session to history without clearing."""
        current_messages = self.get_conversation_history()
        
        if current_messages:
            history = self._load_json(self.history_file)
            if "sessions" not in history:
                history["sessions"] = []
            
            session = {
                "messages": current_messages,
                "started_at": current_messages[0].get("timestamp") if current_messages else datetime.now().isoformat(),
                "ended_at": datetime.now().isoformat()
            }
            
            history["sessions"].append(session)
            self._save_json(self.history_file, history)
