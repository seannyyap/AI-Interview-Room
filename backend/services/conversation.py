from typing import List, Dict


class ConversationManager:
    """Manages chat history and context window for a session."""
    def __init__(self, system_prompt: str = "You are an AI job interviewer. Keep questions technical and professional."):
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]

    def add_user_message(self, text: str):
        self.history.append({"role": "user", "content": text})

    def add_assistant_message(self, text: str):
        self.history.append({"role": "assistant", "content": text})

    def get_history(self) -> List[Dict[str, str]]:
        return self.history

    def truncate_history(self, max_messages: int = 20):
        """Simple truncation for Phase 2. Phase 4 will use token counting."""
        if len(self.history) > max_messages:
            # Keep system prompt, then take last N-1 messages
            self.history = [self.history[0]] + self.history[-(max_messages - 1):]

    def clear(self):
        self.history = [self.history[0]]
