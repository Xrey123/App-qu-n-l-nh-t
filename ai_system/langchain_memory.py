"""
LangChain Memory System - Long-term memory & User preferences
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

try:
    from langchain_community.chat_message_histories import ChatMessageHistory
    from langchain_core.messages import HumanMessage, AIMessage
except ImportError:
    # Fallback for older LangChain
    try:
        from langchain.memory import ChatMessageHistory
        from langchain.schema import HumanMessage, AIMessage
    except ImportError:
        from langchain_community.chat_message_histories import ChatMessageHistory
        from langchain.schema.messages import HumanMessage, AIMessage


class EnhancedMemory:
    """
    Enhanced memory system với:
    - Conversation history (không giới hạn)
    - User preferences
    - Context summarization
    """

    def __init__(self, user_id: str, user_role: str):
        self.user_id = user_id
        self.user_role = user_role
        self.memory_file = f"ai/memory_{user_id}.json"
        self.preferences_file = f"ai/preferences_{user_id}.json"

        # LangChain memory (simple message history)
        self.chat_history = ChatMessageHistory()

        # Load existing data
        self._load_memory()
        self._load_preferences()

    def _load_memory(self):
        """Load conversation history từ file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Restore messages vào LangChain memory
                    for msg in data.get("messages", []):
                        if msg["type"] == "human":
                            self.chat_history.add_user_message(msg["content"])
                        else:
                            self.chat_history.add_ai_message(msg["content"])
            except:
                pass

    def _load_preferences(self) -> Dict:
        """Load user preferences"""
        if os.path.exists(self.preferences_file):
            try:
                with open(self.preferences_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return self._default_preferences()

    def _default_preferences(self) -> Dict:
        """Default preferences cho user mới"""
        return {
            "experience_level": "newbie",  # newbie / intermediate / expert
            "preferred_response_style": "detailed",  # detailed / concise
            "frequently_used_tabs": [],
            "common_questions": [],
            "last_active": datetime.now().isoformat(),
        }

    def save_conversation(self, question: str, answer: str):
        """Lưu Q&A vào memory"""
        # Add vào LangChain memory
        self.chat_history.add_user_message(question)
        self.chat_history.add_ai_message(answer)

        # Save vào file
        self._save_memory()

        # Update preferences
        self._update_preferences(question)

    def _save_memory(self):
        """Save conversation history ra file"""
        messages = []
        for msg in self.chat_history.messages:
            messages.append(
                {
                    "type": "human" if isinstance(msg, HumanMessage) else "ai",
                    "content": msg.content,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump({"messages": messages}, f, ensure_ascii=False, indent=2)

    def _update_preferences(self, question: str):
        """Cập nhật preferences dựa trên usage patterns"""
        prefs = self._load_preferences()

        # Track common questions
        if question not in prefs["common_questions"]:
            prefs["common_questions"].append(question)
            if len(prefs["common_questions"]) > 20:  # Keep only last 20
                prefs["common_questions"] = prefs["common_questions"][-20:]

        # Update last active
        prefs["last_active"] = datetime.now().isoformat()

        # Auto-adjust experience level based on usage
        total_conversations = len(self.chat_history.messages) // 2
        if total_conversations > 50:
            prefs["experience_level"] = "expert"
        elif total_conversations > 20:
            prefs["experience_level"] = "intermediate"

        # Save
        os.makedirs(os.path.dirname(self.preferences_file), exist_ok=True)
        with open(self.preferences_file, "w", encoding="utf-8") as f:
            json.dump(prefs, f, ensure_ascii=False, indent=2)

    def get_context(self) -> str:
        """Lấy context từ memory để đưa cho AI"""
        prefs = self._load_preferences()

        context = f"""
USER INFO:
- User ID: {self.user_id}
- Role: {self.user_role}
- Experience Level: {prefs['experience_level']}
- Preferred Style: {prefs['preferred_response_style']}
- Total Conversations: {len(self.chat_history.messages) // 2}
"""

        # Thêm recent conversation history
        recent_messages = self.chat_history.messages[-10:]  # Last 5 Q&A pairs
        if recent_messages:
            context += "\nRECENT CONVERSATION:\n"
            for i in range(0, len(recent_messages), 2):
                if i + 1 < len(recent_messages):
                    context += f"User: {recent_messages[i].content}\n"
                    context += f"AI: {recent_messages[i+1].content}\n"

        return context

    def get_experience_level(self) -> str:
        """Lấy experience level của user"""
        prefs = self._load_preferences()
        return prefs.get("experience_level", "newbie")

    def clear_memory(self):
        """Xóa toàn bộ conversation history"""
        self.chat_history.clear()
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)

    def get_statistics(self) -> Dict:
        """Thống kê usage của user"""
        prefs = self._load_preferences()
        return {
            "total_conversations": len(self.chat_history.messages) // 2,
            "experience_level": prefs["experience_level"],
            "common_questions": prefs["common_questions"][-5:],  # Top 5 recent
            "last_active": prefs["last_active"],
        }