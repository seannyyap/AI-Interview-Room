"""
Unit tests for ConversationManager — history, truncation, token estimation.
"""
from backend.services.conversation import ConversationManager


class TestConversationBasics:
    def test_initial_state_has_system_prompt(self):
        cm = ConversationManager(system_prompt="Test prompt")
        history = cm.get_history()
        assert len(history) == 1
        assert history[0]["role"] == "system"
        assert history[0]["content"] == "Test prompt"

    def test_add_user_message(self):
        cm = ConversationManager()
        cm.add_user_message("Hello")
        assert len(cm.get_history()) == 2
        assert cm.get_history()[-1] == {"role": "user", "content": "Hello"}

    def test_add_assistant_message(self):
        cm = ConversationManager()
        cm.add_assistant_message("Hi there")
        assert len(cm.get_history()) == 2
        assert cm.get_history()[-1] == {"role": "assistant", "content": "Hi there"}

    def test_message_ordering(self):
        cm = ConversationManager()
        cm.add_user_message("Q1")
        cm.add_assistant_message("A1")
        cm.add_user_message("Q2")
        roles = [m["role"] for m in cm.get_history()]
        assert roles == ["system", "user", "assistant", "user"]


class TestConversationTruncation:
    def test_auto_truncation_removes_oldest_non_system(self):
        cm = ConversationManager(system_prompt="sys", max_context_tokens=10)
        # Each message adds ~1.33 tokens per word, so many messages will hit 10 quickly
        for i in range(20):
            cm.add_user_message(f"message number {i} with some extra words here")
        # System prompt should always remain
        assert cm.get_history()[0]["role"] == "system"
        assert cm.get_history()[0]["content"] == "sys"
        # Total should be within budget
        assert cm._estimate_tokens() <= cm._max_context_tokens or len(cm.get_history()) <= 2

    def test_system_prompt_never_removed(self):
        cm = ConversationManager(system_prompt="important", max_context_tokens=5)
        for i in range(50):
            cm.add_user_message(f"padding message {i}")
        assert cm.get_history()[0]["content"] == "important"

    def test_truncate_history_by_count(self):
        cm = ConversationManager(max_context_tokens=99999)
        for i in range(30):
            cm.add_user_message(f"msg {i}")
        cm.truncate_history(max_messages=10)
        assert len(cm.get_history()) == 10
        assert cm.get_history()[0]["role"] == "system"

    def test_clear_keeps_system_prompt(self):
        cm = ConversationManager(system_prompt="keep me")
        cm.add_user_message("gone")
        cm.add_assistant_message("also gone")
        cm.clear()
        assert len(cm.get_history()) == 1
        assert cm.get_history()[0]["content"] == "keep me"


class TestTokenEstimation:
    def test_estimate_returns_int(self):
        cm = ConversationManager()
        cm.add_user_message("one two three four")
        result = cm._estimate_tokens()
        assert isinstance(result, int)

    def test_more_words_more_tokens(self):
        cm1 = ConversationManager(system_prompt="a")
        cm2 = ConversationManager(system_prompt="a")
        cm1.add_user_message("short")
        cm2.add_user_message("this is a much longer message with many words in it")
        assert cm2._estimate_tokens() > cm1._estimate_tokens()
