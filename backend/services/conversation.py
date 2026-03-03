"""
ConversationManager — manages chat history and context window for a session.

Phase 4: Supports dynamic system prompts from prompt templates and
token-aware truncation using word-count estimation.
"""
from typing import List, Dict


class ConversationManager:
    """Manages chat history and context window for a session."""

    # Rough estimate: 1 word ≈ 1.33 tokens (conservative for English)
    TOKENS_PER_WORD = 1.33

    def __init__(
        self,
        system_prompt: str = "You are an AI job interviewer. Keep questions technical and professional.",
        max_context_tokens: int = 6144,  # Leave headroom from the 8192 context window
    ):
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]
        self._max_context_tokens = max_context_tokens

    def add_user_message(self, text: str):
        self.history.append({"role": "user", "content": text})
        self._auto_truncate()

    def add_assistant_message(self, text: str):
        self.history.append({"role": "assistant", "content": text})
        self._auto_truncate()

    def get_history(self) -> List[Dict[str, str]]:
        return self.history

    def _estimate_tokens(self) -> int:
        """Estimate total token count from word count."""
        total_words = sum(len(msg["content"].split()) for msg in self.history)
        return int(total_words * self.TOKENS_PER_WORD)

    def _auto_truncate(self):
        """
        Token-aware truncation: drop oldest non-system messages
        until the conversation fits within the context budget.
        """
        while self._estimate_tokens() > self._max_context_tokens and len(self.history) > 2:
            # Remove the oldest non-system message (index 1)
            self.history.pop(1)

    def truncate_history(self, max_messages: int = 20):
        """Simple message-count truncation (kept for backward compat)."""
        if len(self.history) > max_messages:
            self.history = [self.history[0]] + self.history[-(max_messages - 1):]

    def clear(self):
        self.history = [self.history[0]]
