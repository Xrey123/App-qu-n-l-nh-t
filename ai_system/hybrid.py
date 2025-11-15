"""
Hybrid AI System - Groq API (online) + Phi3:mini + RAG (offline)
Enhanced with LangChain Memory & Smart Prompts
"""

import sqlite3
import json
import time
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests


class HybridAI:
    """
    Hybrid AI với 2 modes + LangChain enhancements:
    - Online: Groq API (Llama 3.3 70B) - Cực thông minh, cực nhanh
    - Offline: Phi3:mini + RAG - Tạm được, offline OK
    - LangChain: Long-term memory, smart prompts, feedback learning
    """

    def __init__(
        self,
        db_path: str = "fapp.db",
        main_window=None,
        current_user_role: str = "staff",
        current_user_id: int = None,
    ):
        self.db_path = db_path
        self.main_window = main_window
        self.current_user_role = current_user_role
        self.current_user_id = current_user_id or 1

        # Load configs
        self.config = self._load_config()
        self.db_queries = self._load_json("ai/db_queries.json", {})
        self.memory = self._load_json("ai/memory.json", {})
        self.app_knowledge = self._load_json("ai/app_knowledge_enhanced.json", {})
        if not self.app_knowledge:
            self.app_knowledge = self._load_json("ai/app_knowledge.json", {})

        # LangChain Memory System
        try:
            from .langchain_memory import EnhancedMemory

            self.enhanced_memory = EnhancedMemory(
                user_id=str(self.current_user_id), user_role=self.current_user_role
            )
        except Exception as e:
            print(f"⚠️ LangChain memory disabled: {e}")
            self.enhanced_memory = None

        # Smart Prompt System
        try:
            from .prompt_manager import PromptManager

            self.prompt_manager = PromptManager()
        except Exception as e:
            print(f"⚠️ Prompt manager disabled: {e}")
            self.prompt_manager = None

        # Conversation history (legacy - for fallback)
        self.conversation_history = []
        self.max_history = 10  # Keep last 10 Q&A pairs

        # Initialize AI mode
        self.groq_api_key = self.config.get("groq_api_key", "")
        self.use_groq = self._check_groq_available()

        if self.use_groq:
            self.ai_mode = "online"
            self.model_name = (
                "llama-3.3-70b-versatile"  # Updated: llama-3.1 decommissioned
            )
            print("✅ AI Mode: ONLINE (Groq API - Llama 3.3 70B + LangChain)")
        else:
            self.ai_mode = "offline"
            self.ollama_url = "http://localhost:11434/api/generate"
            self.model_name = "phi3:mini"
            print("⚠️ AI Mode: OFFLINE (Phi3:mini + RAG + LangChain)")

        # Cache
        self.query_cache: Dict[str, tuple] = {}
        self.cache_ttl = 300

        # Initialize Actions System
        try:
            from .actions import AIActionSystem

            self.action_system = AIActionSystem(
                main_window=main_window, current_user_role=current_user_role
            )
        except:
            self.action_system = None

    def _load_config(self) -> dict:
        """Load config (Groq API key, etc.)"""
        config_path = "ai/config.json"
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return {}

    def _save_config(self):
        """Save config"""
        config_path = "ai/config.json"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def set_groq_api_key(self, api_key: str):
        """Set Groq API key and switch to online mode"""
        self.groq_api_key = api_key
        self.config["groq_api_key"] = api_key
        self._save_config()

        # Try to connect
        if self._check_groq_available():
            self.use_groq = True
            self.ai_mode = "online"
            self.model_name = "llama-3.3-70b-versatile"  # Updated model
            return True, "✅ Đã kết nối Groq API! AI giờ thông minh gấp 35 lần!"
        else:
            return False, "❌ API key không hợp lệ. Vui lòng kiểm tra lại."

    def _check_groq_available(self) -> bool:
        """Check if Groq API is available"""
        if not self.groq_api_key or not self.groq_api_key.startswith("gsk_"):
            return False

        try:
            from groq import Groq

            client = Groq(api_key=self.groq_api_key)

            # Test connection
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Updated model
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10,
            )
            return True
        except:
            return False

    def _ask_groq(self, question: str, context: str = "") -> str:
        """Ask Groq API (Llama 3.3 70B) with conversation history"""
        try:
            from groq import Groq

            client = Groq(api_key=self.groq_api_key)

            # Build prompt with context
            if not context:
                context = self._build_context()

            # Build messages with history
            messages = [{"role": "system", "content": context}]

            # Add conversation history (last N pairs)
            for hist in self.conversation_history[-6:]:  # Last 3 Q&A pairs (6 messages)
                messages.append({"role": "user", "content": hist["question"]})
                messages.append({"role": "assistant", "content": hist["answer"]})

            # Add current question
            messages.append({"role": "user", "content": question})

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=800,  # Increased from 500 for longer answers
                temperature=0.5,
            )

            answer = response.choices[0].message.content.strip()

            # Save to history
            self.conversation_history.append({"question": question, "answer": answer})

            # Keep only last N pairs
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[
                    -self.max_history :
                ]

            return answer

        except Exception as e:
            # Fallback to offline if error
            print(f"⚠️ Groq API error: {e}. Switching to offline mode...")
            self.use_groq = False
            self.ai_mode = "offline"

            # Try offline mode first
            offline_answer = self._ask_offline(question, context)
            if offline_answer:
                return offline_answer

            # If offline also fails, try to answer from knowledge base
            # Check for common questions
            q_lower = question.lower()
            if any(
                kw in q_lower
                for kw in ["bạn là ai", "bạn là gì", "tên bạn", "giới thiệu"]
            ):
                return """Tôi là AI trợ lý của **HỆ THỐNG QUẢN LÝ CỬA HÀNG NHỚT**.

**Tôi có thể giúp bạn:**
- 📱 Hướng dẫn sử dụng 14 tabs trong app
- 🛢️ Giải thích cách tính giá (lẻ/buôn/VIP)
- 📊 Hướng dẫn workflow: Nhận hàng → Bán hàng → Xuất hóa đơn
- 💡 Trả lời câu hỏi về chức năng app
- 🔍 Tra cứu thông tin sản phẩm, kho, hóa đơn

**Lưu ý:** Hiện tại AI đang ở chế độ offline do Groq API đạt giới hạn. Hãy hỏi tôi về tabs, workflows, hoặc chức năng trong app! 😊"""

            # Return empty to continue normal flow
            return ""

    def _ask_offline(self, question: str, context: str = "") -> str:
        """Ask Ollama Phi3:mini (offline)"""
        try:
            if not context:
                context = self._build_context()

            full_prompt = f"{context}\n\nCâu hỏi: {question}\nTrả lời:"

            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"temperature": 0.5, "num_predict": 200},
                },
                timeout=15,
            )

            if response.status_code == 200:
                return response.json().get("response", "").strip()
        except:
            pass
        return ""

    def _build_context(self) -> str:
        """
        Build context from app knowledge, smart prompts, user memory, and auto-extracted app logic/workflow.
        Chỉ trả lời kiểu hướng dẫn sử dụng app, không trả lời về IT/kỹ thuật.
        """
        # Load app knowledge from JSON
        app_info = self.app_knowledge.get("app_info", {})
        pricing_info = self.app_knowledge.get("pricing", {})

        # Get smart prompt based on user role & experience
        smart_prompt = ""
        if self.prompt_manager and self.enhanced_memory:
            experience_level = self.enhanced_memory.get_experience_level()
            smart_prompt = self.prompt_manager.get_prompt(
                self.current_user_role, experience_level
            )

        # Get user memory context
        user_context = ""
        if self.enhanced_memory:
            user_context = self.enhanced_memory.get_context()

        # Auto extract tab/workflow/database info (chỉ mô tả, không code)
        tab_descriptions = []
        try:
            from pathlib import Path
            import re
            # Đọc file main_gui.py để lấy tên tab và mô tả chức năng
            main_gui_path = Path(__file__).parent.parent / "main_gui.py"
            if main_gui_path.exists():
                with open(main_gui_path, "r", encoding="utf-8") as f:
                    code = f.read()
                # Tìm các dòng addTab và mô tả
                tab_matches = re.findall(r'addTab\(.*?,\s*"([^"]+)"\)', code)
                for tab in tab_matches:
                    tab_descriptions.append(f"- {tab}")
        except Exception as e:
            tab_descriptions.append(f"(Không thể tự động đọc tab: {e})")

        # Auto extract database table names (chỉ tên bảng, không schema)
        db_tables = []
        try:
            db_path = Path(__file__).parent.parent / "fapp.db"
            import sqlite3
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                c = conn.cursor()
                c.execute("SELECT name FROM sqlite_master WHERE type='table'")
                db_tables = [row[0] for row in c.fetchall()]
                conn.close()
        except Exception as e:
            db_tables.append(f"(Không thể đọc database: {e})")

        # Build rich context
        context = f"""
{smart_prompt}

THÔNG TIN APP:
- Tên: {app_info.get('name', 'Hệ thống quản lý cửa hàng nhớt')}
- Database: fapp.db (SQLite)
- Các bảng dữ liệu: {', '.join(db_tables) if db_tables else '(Không có dữ liệu)'}

🗂️ CÁC TAB CHỨC NĂNG:
{chr(10).join(tab_descriptions) if tab_descriptions else '(Không có dữ liệu)'}

💡 Mỗi tab có workflow và chức năng riêng, bạn có thể hỏi chi tiết về từng tab để được hướng dẫn sử dụng.

{user_context}

📊 TRUY VẤN DỮ LIỆU (chỉ khi user yêu cầu, theo quyền):
- Nếu user hỏi về số nợ, sổ quỹ, báo cáo, sản phẩm... AI sẽ truy vấn database và trả về kết quả thật, KHÔNG tự bịa số liệu.
- Nếu user không đủ quyền, AI sẽ thông báo rõ ràng.

⚠️ LƯU Ý:
- KHÔNG trả lời về code, kỹ thuật, cấu trúc IT, schema, file, API, SQL.
- Chỉ trả lời như một người hướng dẫn sử dụng app, theo đúng quyền user.
- KHÔNG tự bịa số liệu, chỉ trả về dữ liệu thật hoặc mô tả workflow.

Nếu hỏi về model AI: Trả lời thật {"🚀 Groq API - Llama 3.3 70B" if self.use_groq else "💻 Phi3:mini offline"}
"""
        return context

    def ask(self, question: str) -> tuple[str, str]:
        """
        Main method - Route to online or offline
        Returns: (answer, conversation_id) for feedback
        """
        # Generate conversation ID for feedback tracking
        conversation_id = str(uuid.uuid4())

        # Normalize question
        question = self._normalize_question(question)
        q_lower = question.lower()

        # Check which AI is being used
        if "model nào" in q_lower or "ai nào" in q_lower:
            if self.use_groq:
                answer = f"🚀 Tôi đang dùng **Groq API - Llama 3.3 70B** (online mode). Cực thông minh và cực nhanh! 😊"
            else:
                answer = f"💻 Tôi đang dùng **Phi3:mini** (offline mode). Nếu muốn AI thông minh hơn, hãy cấu hình Groq API trong Settings!"
            self._save_conversation(question, answer, conversation_id)
            return answer, conversation_id

        # ✅ BƯỚC 1: CHECK PERMISSION
        permission_response = self._check_permission(question)
        if permission_response:
            self._save_conversation(question, permission_response, conversation_id)
            return permission_response, conversation_id

        # ✅ BƯỚC 2: FILTER IT-SENSITIVE INFO
        if self._is_it_sensitive_question(question):
            answer = "🔒 Xin lỗi, tôi không thể cung cấp thông tin về kỹ thuật hệ thống. Hãy hỏi về cách sử dụng các chức năng trong app nhé! 😊"
            self._save_conversation(question, answer, conversation_id)
            return answer, conversation_id

        # ✅ BƯỚC 2.5: CHECK IF USER WANTS REAL DATABASE DATA
        action_result = self._try_execute_action(question)
        if action_result:
            self._save_conversation(question, action_result, conversation_id)
            return action_result, conversation_id

        # Try DB query first (for data questions)
        data_keywords = ["bao nhiêu", "còn", "tồn", "danh sách", "liệt kê"]
        if any(kw in q_lower for kw in data_keywords):
            sql = self._find_query_template(question)
            if sql:
                result = self._query_db(sql)
                if result:
                    answer = self._format_db_result(result, question)
                    self._save_conversation(question, answer, conversation_id)
                    return answer, conversation_id

        # Skip app_knowledge search for logic/explanation questions
        # Let AI answer with rich context instead
        logic_keywords = [
            "cách",
            "giải thích",
            "tính",
            "tại sao",
            "như thế nào",
            "ra sao",
            "thế nào",
        ]
        should_use_ai = any(kw in q_lower for kw in logic_keywords)

        # Try app knowledge ONLY for UI/tab questions
        if not should_use_ai:
            tab_keywords = ["tab", "mở", "vào đâu", "nút", "button", "click"]
            if any(kw in q_lower for kw in tab_keywords):
                app_answer = self._search_app_knowledge(question)
                # Thử chuyển tab và lấy thông tin tab thực tế
                tab_map = (
                    getattr(self.main_window, "tab_map", {}) if self.main_window else {}
                )
                found = None
                for key, idx in tab_map.items():
                    if key in q_lower:
                        tab_name = (
                            self.main_window.tabs.tabText(idx)
                            if self.main_window
                            else key
                        )
                        # Lấy chức năng tab từ app_knowledge nếu có
                        tab_info = (
                            self.app_knowledge.get("tabs", {}).get(tab_name) or {}
                        )
                        func = tab_info.get("chức năng", "Chưa có mô tả chức năng.")
                        app_answer = f"✅ Đã chuyển đến tab **{tab_name}**\n\n🔹 Chức năng: {func}"
                        found = True
                        self._auto_switch_tab(question)
                        self._save_conversation(question, app_answer, conversation_id)
                        return app_answer, conversation_id
                # Nếu không khớp alias, fallback app_knowledge như cũ
                if app_answer:
                    self._auto_switch_tab(question)
                    self._save_conversation(question, app_answer, conversation_id)
                    return app_answer, conversation_id

        # Ask AI (online or offline) - This has rich context about pricing
        context = self._build_context()

        if self.use_groq:
            answer = self._ask_groq(question, context)
        else:
            answer = self._ask_offline(question, context)

        if answer:
            # ✅ BƯỚC 4: AUTO SWITCH TAB for AI answers too
            self._auto_switch_tab(question)
            self._save_conversation(question, answer, conversation_id)
            return answer, conversation_id

        # ✅ LAST RESORT: Try to answer from app_knowledge for general questions
        intro_keywords = [
            "bạn là ai",
            "bạn là gì",
            "giới thiệu",
            "tên bạn",
            "bạn làm gì",
        ]
        if any(kw in q_lower for kw in intro_keywords):
            answer = """Tôi là AI trợ lý của **HỆ THỐNG QUẢN LÝ CỬA HÀNG NHỚT**.

**Tôi có thể giúp bạn:**
- 📱 Hướng dẫn sử dụng 14 tabs trong app
- 🛢️ Giải thích cách tính giá (lẻ/buôn/VIP)  
- 📊 Hướng dẫn workflow: Nhận hàng → Bán hàng → Xuất hóa đơn
- 💡 Trả lời câu hỏi về chức năng app
- 🔍 Tra cứu thông tin sản phẩm, kho, hóa đơn

**Hỏi tôi ngay:**
- "liệt kê các tab"
- "cách tính giá buôn"
- "hướng dẫn bán hàng"
- "tab nào dùng để xuất hóa đơn"

⚠️ **Lưu ý:** AI đang offline (Groq API rate limit). Tôi vẫn có thể trả lời từ knowledge base! 😊"""
            self._save_conversation(question, answer, conversation_id)
            return answer, conversation_id

        # Try searching app_knowledge one more time (broader search)
        app_answer = self._search_app_knowledge(question)
        if app_answer:
            self._save_conversation(question, app_answer, conversation_id)
            return app_answer, conversation_id

        answer = "Hãy thử hỏi chi tiết hơn về tabs, workflows, sản phẩm, hoặc báo cáo nhé! 😊"
        self._save_conversation(question, answer, conversation_id)
        return answer, conversation_id

    def _save_conversation(self, question: str, answer: str, conversation_id: str):
        """Lưu conversation vào LangChain memory và database"""
        # Save to LangChain memory (long-term)
        if self.enhanced_memory:
            try:
                self.enhanced_memory.save_conversation(question, answer)
            except Exception as e:
                print(f"⚠️ Failed to save to LangChain memory: {e}")

        # Save to legacy conversation history (fallback)
        self.conversation_history.append({"question": question, "answer": answer})
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history :]

        # Save to database for feedback tracking
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                """INSERT INTO AI_Feedback 
                   (user_id, conversation_id, question, answer, is_helpful, timestamp)
                   VALUES (?, ?, ?, ?, NULL, ?)""",
                (
                    self.current_user_id,
                    conversation_id,
                    question,
                    answer,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Failed to save feedback record: {e}")

    def feedback(self, conversation_id: str, is_helpful: bool):
        """
        Lưu feedback từ user (👍 hoặc 👎)

        Args:
            conversation_id: ID của conversation
            is_helpful: True = 👍, False = 👎
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                """UPDATE AI_Feedback 
                   SET is_helpful = ?
                   WHERE conversation_id = ?""",
                (1 if is_helpful else 0, conversation_id),
            )
            conn.commit()
            conn.close()
            print(f"✅ Feedback saved: {'👍' if is_helpful else '👎'}")
        except Exception as e:
            print(f"⚠️ Failed to save feedback: {e}")

    def _load_json(self, path: str, default: Any) -> Any:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        return default

    def _normalize_question(self, question: str) -> str:
        """Normalize question"""
        q = question.lower()
        typo_map = {
            "nhiêu": "nhiêu",
            "nhieu": "nhiêu",
            "sp": "sản phẩm",
        }
        for wrong, correct in typo_map.items():
            q = q.replace(wrong, correct)
        return q

    def _query_db(self, sql: str) -> List[tuple]:
        """Query database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            result = cursor.execute(sql).fetchall()
            conn.close()
            return result
        except:
            return []

    def _find_query_template(self, question: str) -> Optional[str]:
        """Find SQL template and fill in dynamic parameters"""
        import re
        from datetime import datetime

        q_lower = question.lower()
        sorted_queries = sorted(
            self.db_queries.items(), key=lambda x: len(x[0]), reverse=True
        )

        for key, sql in sorted_queries:
            if key in q_lower:
                # Parse dynamic parameters
                result_sql = sql

                # Extract date from question (e.g., "7/11", "ngày 7/11", "2024-11-07")
                date_match = re.search(
                    r"(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{2,4}))?", question
                )
                if date_match and "{date}" in sql:
                    day = date_match.group(1).zfill(2)
                    month = date_match.group(2).zfill(2)
                    year = (
                        date_match.group(3)
                        if date_match.group(3)
                        else str(datetime.now().year)
                    )
                    if len(year) == 2:
                        year = "20" + year
                    parsed_date = f"{year}-{month}-{day}"
                    result_sql = result_sql.replace("{date}", parsed_date)

                # Extract username from question
                if "{user}" in sql:
                    # Find user name (word after "user" or before "bán")
                    user_match = re.search(r"(?:user\s+|^)(\w+)(?:\s+bán)?", q_lower)
                    if user_match:
                        username = user_match.group(1).upper()
                        result_sql = result_sql.replace("{user}", username)
                    else:
                        # If no specific user, skip this template
                        continue

                # Extract product name/keyword from question
                if "{query}" in sql:
                    # Extract product name (e.g., "2T", "KOMAT", "RACER")
                    # Try different patterns
                    query_match = re.search(
                        r"(?:của|giá)\s+(?:sản phẩm\s+)?(\w+)", q_lower
                    )
                    if not query_match:
                        # Try standalone product name
                        query_match = re.search(
                            r"\b(\w*\d+\w*)\b", q_lower
                        )  # Match word with digits

                    if query_match:
                        product_keyword = query_match.group(1).upper()
                        result_sql = result_sql.replace("{query}", product_keyword)
                    else:
                        # If no keyword, skip this template
                        continue

                return result_sql
        return None

    def _format_db_result(self, result: List[tuple], question: str) -> str:
        """Format DB result"""
        if not result:
            return "Không tìm thấy dữ liệu."

        q_lower = question.lower()

        # Sum queries (doanh thu, tổng tiền, etc.)
        if len(result) == 1 and len(result[0]) == 1:
            value = result[0][0]
            if value is None:
                return "Chưa có dữ liệu."

            # Check if it's a money value
            if (
                "doanh thu" in q_lower
                or "tổng" in q_lower
                or "giao dịch" in q_lower
                or "chênh lệch" in q_lower
            ):
                if isinstance(value, (int, float)):
                    formatted = f"{value:,.0f}".replace(",", ".")
                    if "doanh thu" in q_lower:
                        return f"💰 **Doanh thu**: {formatted} VNĐ"
                    elif "giao dịch" in q_lower:
                        return f"💵 **Tổng giao dịch**: {formatted} VNĐ"
                    elif "chênh lệch" in q_lower:
                        return f"⚖️ **Tổng chênh lệch**: {formatted} VNĐ"
                    return f"💵 **Tổng**: {formatted} VNĐ"

            # Count queries
            if isinstance(value, int):
                if "sản phẩm" in q_lower:
                    return f"📦 Hiện có **{value} sản phẩm** trong kho."
                elif "user" in q_lower:
                    return f"👥 Hiện có **{value} user** trong hệ thống."
                elif "hóa đơn" in q_lower:
                    return f"📄 Hiện có **{value} hóa đơn**."
                elif "giao dịch" in q_lower:
                    return f"💳 Có **{value} giao dịch**."
                return f"Kết quả: {value}"

        # Product list with inventory OR price query
        if (
            "sản phẩm" in q_lower
            or "tồn kho" in q_lower
            or "còn" in q_lower
            or "giá" in q_lower
        ) and len(result[0]) >= 2:
            # Check if it's a price query (4 columns: ten, gia_le, gia_buon, gia_vip)
            if len(result[0]) == 4 and all(
                isinstance(val, (int, float, type(None))) for val in result[0][1:]
            ):
                items = []
                for row in result:
                    ten = row[0]
                    gia_le = f"{row[1]:,.0f}".replace(",", ".") if row[1] else "N/A"
                    gia_buon = f"{row[2]:,.0f}".replace(",", ".") if row[2] else "N/A"
                    gia_vip = f"{row[3]:,.0f}".replace(",", ".") if row[3] else "N/A"
                    items.append(
                        f"• **{ten}**\n  - Giá lẻ: {gia_le} VNĐ\n  - Giá buôn: {gia_buon} VNĐ\n  - Giá VIP: {gia_vip} VNĐ"
                    )
                return f"💰 **Bảng giá sản phẩm:**\n\n" + "\n\n".join(items[:10])

            # Regular inventory list (2-3 columns)
            if len(result[0]) >= 2:
                items = []
                for row in result:
                    ten = row[0]
                    ton = row[1] if len(row) > 1 else 0
                    donvi = row[2] if len(row) > 2 else ""
                    items.append(f"• **{ten}**: {ton} {donvi}")
                return f"📦 **Sản phẩm trong kho:**\n\n" + "\n".join(items[:15])

        # Sales details (chi tiết bán)
        if "bán" in q_lower and len(result[0]) == 2:
            items = []
            for row in result:
                ten = row[0]
                sl = row[1] if len(row) > 1 else 0
                items.append(f"• **{ten}**: {sl} sản phẩm")
            return f"📊 **Sản phẩm đã bán:**\n\n" + "\n".join(items[:10])

        # Invoices (hóa đơn)
        if "hóa đơn" in q_lower and len(result[0]) >= 3:
            items = []
            for row in result:
                id_hd = row[0]
                khach = row[1] if len(row) > 1 else "N/A"
                tong = row[2] if len(row) > 2 else 0
                formatted = f"{tong:,.0f}".replace(",", ".")
                items.append(f"• HD#{id_hd} - **{khach}**: {formatted} VNĐ")
            return f"📄 **Hóa đơn:**\n\n" + "\n".join(items[:10])

        # User list
        if "user" in q_lower and len(result[0]) == 2:
            items = []
            for row in result:
                username = row[0]
                role = row[1] if len(row) > 1 else "N/A"
                role_icon = {"admin": "👑", "accountant": "👔", "staff": "👤"}.get(
                    role, "👤"
                )
                items.append(f"• {role_icon} **{username}** ({role})")
            return f"👥 **Danh sách User:**\n\n" + "\n".join(items)

        # Generic result (fallback)
        return f"Kết quả: {result[:3]}"

    def _search_app_knowledge(self, question: str) -> Optional[str]:
        # Nếu user hỏi về việc nên làm gì đầu tiên khi sử dụng app
        q_lower = question.lower()
        # Normalize Vietnamese (bỏ → bổ, etc.)
        q_normalized = q_lower.replace("bổ", "bỏ").replace("xuất bỗ", "xuất bỏ")
        first_steps_keywords = [
            "làm gì đầu tiên",
            "bước đầu",
            "bắt đầu sử dụng",
            "hướng dẫn bắt đầu",
            "mới sử dụng",
            "cần làm gì",
            "khởi tạo",
            "setup ban đầu",
            "lần đầu sử dụng",
            "lần đầu mình sử dụng",
            "lần đầu dùng app",
            "bắt đầu làm gì",
        ]
        if any(kw in q_normalized for kw in first_steps_keywords):
            return (
                "Khi mới sử dụng ứng dụng, bạn cần thực hiện các bước sau:<br>\n"
                "1. <b>Thêm danh sách sản phẩm</b> tại cửa hàng (tên, số lượng, các loại giá).<br>\n"
                "2. Có thể <b>thêm nhanh bằng import file Excel</b> đi kèm để tiết kiệm thời gian.<br>\n"
                "3. <b>Nhập thông số đầu kỳ</b> để khởi tạo tồn kho ban đầu.<br>\n"
                "4. Kiểm tra <b>số nợ các user</b> và những sản phẩm chưa xuất với loại giá nào.<br>\n"
                "5. Sau khi hoàn tất các bước trên, bạn có thể bắt đầu bán hàng, xuất hóa đơn và quản lý kho.<br>\n"
                "💡 Nếu cần hướng dẫn chi tiết về từng bước, hãy hỏi tôi nhé!"
            )

        # ✅ XỬ LÝ CÂU HỎI VỀ TỔNG SỐ TABS (CẢ TAB CON)
        list_all_keywords = [
            "liệt kê",
            "có bao nhiêu",
            "tất cả",
            "danh sách",
            "các tab",
        ]
        if (
            any(kw in q_normalized for kw in list_all_keywords)
            and "tab" in q_normalized
        ):
            result = ""
            # Ưu tiên lấy số tab thực tế từ MainWindow nếu có
            if self.main_window and hasattr(self.main_window, "tabs"):
                tab_widget = self.main_window.tabs
                tab_count = tab_widget.count()
                result += f"📊 **App có {tab_count} tabs chính (thực tế trên giao diện):**\n\n"
                for i in range(tab_count):
                    tab_name = tab_widget.tabText(i)
                    result += f"{i+1}. {tab_name}"
                    # Nếu là tab Ca bán hàng, liệt kê tab con
                    if "ca bán hàng" in tab_name.lower() and hasattr(
                        self.main_window, "tab_ca_banhang_tabs"
                    ):
                        sub_widget = self.main_window.tab_ca_banhang_tabs
                        sub_count = sub_widget.count()
                        sub_tabs = [sub_widget.tabText(j) for j in range(sub_count)]
                        result += f"\n   • Tab con: {', '.join(sub_tabs)}"
                    result += "\n"
                result += (
                    "\n💡 **Tip:** Hỏi tôi chi tiết về tab nào để biết cách sử dụng!"
                )
                return result
            # Nếu không có MainWindow, fallback sang app_knowledge
            tabs_dict = self.app_knowledge.get("tabs", {})
            tab_count = len(tabs_dict)
            result += f"📊 **App có {tab_count} tabs chính (theo dữ liệu):**\n\n"
            for i, (tab_name, tab_info) in enumerate(tabs_dict.items(), 1):
                tab_func = tab_info.get("chức năng", "")
                quyền = tab_info.get("quyền", "Tất cả")
                result += f"{i}. **{tab_name}** ({quyền})\n   → {tab_func}"
                if "sub_tabs" in tab_info:
                    sub_tabs = tab_info["sub_tabs"]
                    result += f"\n   • Tab con: {', '.join(sub_tabs.keys())}"
                result += "\n"
            result += "💡 **Tip:** Hỏi tôi chi tiết về tab nào để biết cách sử dụng!"
            return result

        # Nếu người dùng hỏi về chức năng các tab, liệt kê theo giao diện thực tế
        func_keywords = ["chức năng", "tác dụng", "dùng để", "công dụng", "mục đích"]
        if any(kw in q_normalized for kw in func_keywords) and "tab" in q_normalized:
            # Lấy danh sách tab thực tế từ MainWindow nếu có
            if self.main_window and hasattr(self.main_window, "tabs"):
                tab_widget = self.main_window.tabs
                tab_count = tab_widget.count()
                result = f"📊 **Chức năng của {tab_count} tabs trên giao diện:**\n\n"
                tabs_dict = self.app_knowledge.get("tabs", {})
                for i in range(tab_count):
                    tab_name = tab_widget.tabText(i)
                    tab_info = tabs_dict.get(tab_name) or tabs_dict.get(
                        tab_name.replace("🤖 ", "")
                    )
                    func = (
                        tab_info.get("chức năng", "Chưa có mô tả chức năng.")
                        if tab_info
                        else "Chưa có mô tả chức năng."
                    )
                    # Trình bày mỗi tab 1 dòng, in đậm tên tab
                    result += f"{i+1}. <b>{tab_name}</b>: {func}<br>\n"
                result += "<br>💡 <b>Tip:</b> Hỏi tôi chi tiết về tab nào để biết cách sử dụng!"
                return result
        # ...existing code...

        # Search in sub_tabs specifically
        for tab_name, tab_info in self.app_knowledge.get("tabs", {}).items():
            if "sub_tabs" in tab_info:
                for sub_name, sub_info in tab_info["sub_tabs"].items():
                    sub_name_lower = sub_name.lower().replace("bổ", "bỏ")
                    sub_keywords = [
                        kw.lower().replace("bổ", "bỏ")
                        for kw in sub_info.get("keywords", [])
                    ]

                    if sub_name_lower in q_normalized or any(
                        kw in q_normalized for kw in sub_keywords
                    ):
                        result = f"📌 **Tab {tab_name} → Sub-tab {sub_name}**\n\n"
                        result += f"🔹 Chức năng: {sub_info.get('chức năng', '')}\n"

                        # Add workflow if exists
                        if "workflow" in sub_info:
                            result += f"\n📝 Cách sử dụng:\n{sub_info['workflow']}\n"

                        return result

        return None

    def is_server_running(self) -> bool:
        """Check if AI is available"""
        if self.use_groq:
            return self._check_groq_available()
        else:
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                return response.status_code == 200
            except:
                return False

    def get_ai_mode(self) -> str:
        """Get current AI mode"""
        return self.ai_mode

    def get_model_name(self) -> str:
        """Get current model name"""
        if self.use_groq:
            return "Groq API - Llama 3.3 70B"
        else:
            return "Phi3:mini (Offline)"

    def set_current_user_role(self, role: str):
        """Update user role"""
        self.current_user_role = role
        if self.action_system:
            self.action_system.set_current_user_role(role)

    def get_current_user_role(self) -> str:
        """Get current user role"""
        return self.current_user_role

    def _check_permission(self, question: str) -> Optional[str]:
        """
        Kiểm tra quyền user trước khi trả lời.
        Staff không được xem: Sản phẩm, Lịch sử giá, Quản lý User,
        Chênh lệch, Xuất bổ, Công đoàn, Sổ quỹ, Nhập đầu kỳ
        """
        if self.current_user_role == "staff":
            q_lower = question.lower()

            # Các keywords cho tabs bị hạn chế
            restricted_keywords = {
                "sản phẩm": [
                    "sản phẩm",
                    "san pham",
                    "product",
                    "thêm sp",
                    "xóa sp",
                    "import",
                ],
                "lịch sử giá": [
                    "lịch sử giá",
                    "lich su gia",
                    "price history",
                    "thay đổi giá",
                ],
                "quản lý user": [
                    "quản lý user",
                    "quan ly user",
                    "thêm user",
                    "xóa user",
                    "user management",
                ],
                "chênh lệch": ["chênh lệch", "chenh lech", "difference"],
                "xuất bổ": ["xuất bổ", "xuất bỏ", "xuat bo", "xuất thêm"],
                "công đoàn": ["công đoàn", "cong doan", "union", "thưởng"],
                "sổ quỹ": ["sổ quỹ", "so quy", "fund", "quỹ", "chuyển tiền"],
                "nhập đầu kỳ": ["nhập đầu kỳ", "nhap dau ky", "đầu kỳ", "initial"],
            }

            for tab_name, keywords in restricted_keywords.items():
                if any(kw in q_lower for kw in keywords):
                    return f"🚫 **Xin lỗi**, tab **{tab_name}** chỉ dành cho **Admin** hoặc **Accountant**.\n\nBạn là **Staff**, bạn có thể hỏi về:\n✅ Trang chủ\n✅ Ca bán hàng (Nhận hàng, Bán hàng)\n✅ Chi tiết bán\n✅ Hóa đơn\n✅ Báo cáo\n✅ Cài đặt"

        return None

    def _try_execute_action(self, question: str) -> str:
        """
        Detect if question needs database action and execute it
        Returns formatted answer if action executed, None otherwise
        """
        if not self.action_system:
            return None

        q_lower = question.lower()
        from datetime import datetime

        # 1. User debts query
        debt_keywords = [
            "số nợ",
            "so no",
            "nợ",
            "no",
            "user nợ",
            "user no",
            "danh sách nợ",
        ]
        if any(kw in q_lower for kw in debt_keywords):
            result = self.action_system.execute_action("get_user_debts", {})

            if result.get("success"):
                users = result.get("data", [])
                if not users:
                    return "✅ Hiện tại không có user nào đang nợ tiền."

                answer = f"📊 **Danh sách users đang nợ** (Tổng: {result.get('total_debt_formatted', '0 đ')}):\n\n"
                for user in users:
                    answer += f"• **{user['username']}** (ID: {user['user_id']}): Nợ **{user['debt_formatted']}**\n"
                    if user["phone"] != "Chưa có SĐT":
                        answer += f"  📞 {user['phone']}\n"

                return answer
            else:
                return f"❌ Lỗi khi truy vấn số nợ: {result.get('message', 'Unknown error')}"

        # 2. Fund ledger query (sổ quỹ)
        fund_keywords = ["sổ quỹ", "so quy", "giao dịch", "giao dich", "thu chi"]
        if any(kw in q_lower for kw in fund_keywords):
            # Parse date range from question or use today
            today = datetime.now().strftime("%Y-%m-%d")
            start_date = today
            end_date = today

            # Check for date keywords
            if "hôm nay" in q_lower or "hom nay" in q_lower:
                start_date = end_date = today
            elif "tháng này" in q_lower or "thang nay" in q_lower:
                start_date = datetime.now().strftime("%Y-%m-01")
                end_date = today
            elif "tuần này" in q_lower or "tuan nay" in q_lower:
                # Last 7 days
                from datetime import timedelta

                start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                end_date = today

            result = self.action_system.execute_action(
                "query_so_quy", {"start_date": start_date, "end_date": end_date}
            )

            if result.get("success"):
                transactions = result.get("data", [])
                if not transactions:
                    return f"✅ Không có giao dịch nào từ {start_date} đến {end_date}."

                summary = result.get("summary", {})
                answer = f"📊 **Sổ quỹ** ({result.get('date_range', '')})\n\n"
                answer += f"**Tổng cộng:** {summary.get('total_amount_formatted', '0 đ')} ({summary.get('transaction_count', 0)} giao dịch)\n\n"
                answer += "**Chi tiết:**\n"

                for txn in transactions[:10]:  # Limit to 10 transactions
                    answer += f"• {txn['ngay']}: {txn['loai']} - **{txn['so_tien_formatted']}**\n"
                    answer += f"  👤 {txn['nguoi_thuc_hien']}"
                    if txn["nguoi_nhan"] != "N/A":
                        answer += f" → {txn['nguoi_nhan']}"
                    answer += "\n"

                if len(transactions) > 10:
                    answer += f"\n... và {len(transactions) - 10} giao dịch khác"

                return answer
            else:
                return f"❌ Lỗi khi truy vấn sổ quỹ: {result.get('message', 'Unknown error')}"

        return None  # No action needed

    def _is_it_sensitive_question(self, question: str) -> bool:
        """
        Kiểm tra câu hỏi có liên quan đến thông tin IT nhạy cảm không.

        ✅ CHO PHÉP AI XEM (READ-ONLY):
        - Dữ liệu trong các bảng: SanPham, ChiTietBan, HoaDon, GiaoDichQuy, ChenhLechXuatBo, DauKyXuatBo
        - Thông tin Users: username, role (KHÔNG password)
        - Các câu hỏi tra cứu: "bao nhiêu", "còn", "danh sách", "tổng", "giá"
        - Câu hỏi về TÊN BẢNG (để user biết app có bảng gì)

        ❌ CHẶN HOÀN TOÀN:
        - Câu hỏi về CẤU TRÚC chi tiết (schema, tên cột, primary key, foreign key)
        - Thông tin BẢO MẬT: password, api key, token, hash
        - File paths, code Python, SQL modification commands
        - Các lệnh SỬA/XÓA dữ liệu (UPDATE, DELETE, DROP, INSERT, ALTER)
        - Hỏi về bảng Users (chỉ cho phép xem username/role qua query function)
        """
        q_lower = question.lower()

        # ✅ WHITELIST: Các câu hỏi DATA query được phép (return False = không chặn)
        data_query_keywords = [
            "bao nhiêu",
            "còn",
            "tồn kho",
            "danh sách",
            "liệt kê",
            "tổng",
            "số lượng",
            "hóa đơn",
            "sản phẩm",
            "chi tiết bán",
            "giao dịch",
            "đã bán",
            "doanh thu",
            "chênh lệch",
            "xuất bỏ",
            "công đoàn",
            "sổ quỹ",
            "giá",
            "nhớt",
            "khách",
            "user nào",
            "username",
        ]

        # Nếu là câu hỏi data query → CHO PHÉP (không chặn)
        if any(kw in q_lower for kw in data_query_keywords):
            # Nhưng vẫn chặn nếu hỏi về PASSWORD hoặc CẤU TRÚC DB (không chặn tên bảng)
            forbidden_in_data = [
                "password",
                "mật khẩu user",
                "pwd",
                "hash password",
                "token",
                "api key trong",
                "schema database",
                "cột nào",
                "column nào",
                "primary key",
                "foreign key",
                "cấu trúc bảng",
                "bảng có những cột",
                "table structure",
                "create table",
            ]
            if any(kw in q_lower for kw in forbidden_in_data):
                return True  # CHẶN
            return False  # CHO PHÉP (bao gồm cả câu hỏi về tên bảng)

        # ❌ BLOCKLIST: IT keywords NGUY HIỂM (chỉ chặn SQL commands và bảo mật)
        dangerous_keywords = [
            # SQL modification commands (chặn HOÀN TOÀN)
            "update sanpham",
            "delete from",
            "drop table",
            "insert into",
            "alter table",
            "truncate",
            "câu lệnh sql",
            "sql command để",
            "viết sql",
            "execute sql",
            "run query",
            # Code & Files (chặn)
            "main_gui.py",
            ".py file",
            "python code",
            "source code",
            "đoạn code",
            "directory",
            "class mainwindow",
            "function ",
            "def ",
            "import ",
            "module",
            # Security CRITICAL (chặn)
            "password user",
            "pwd admin",
            "mật khẩu lưu",
            "mật khẩu hash",
            "token lưu",
            "secret key",
            "api key trong db",
            "groq key",
            "hash password",
            "hack",
            "exploit",
            "injection",
            "vulnerability",
            # System path (chặn)
            "fapp.db location",
            "server ip",
            "port number",
            "localhost:",
            "config.json path",
            "system architecture",
            "database file path",
        ]

        return any(kw in q_lower for kw in dangerous_keywords)

    def _auto_switch_tab(self, question: str):
        """
        Tự động chuyển đến tab tương ứng khi AI trả lời về tab đó.
        """
        if not self.main_window:
            return

        q_lower = question.lower().strip()
        tab_map = getattr(self.main_window, "tab_map", {})
        # Tập hợp alias mở rộng cho từng tab
        alias_map = {
            "trang chủ": ["trang chủ", "home", "dashboard"],
            "sản phẩm": ["sản phẩm", "san pham", "sp", "product"],
            "lịch sử giá": ["lịch sử giá", "lich su gia", "price history"],
            "ca bán hàng": ["ca bán hàng", "ca", "ban hang", "nhan hang", "ca ban"],
            "chi tiết bán": [
                "chi tiết bán",
                "chi tiet ban",
                "hang da ban",
                "da ban gi",
            ],
            "hóa đơn": ["hóa đơn", "hoa don", "invoice"],
            "báo cáo": ["báo cáo", "bao cao", "report"],
            "quản lý user": ["quản lý user", "quan ly user", "user management"],
            "chênh lệch": ["chênh lệch", "chenh lech", "difference"],
            "xuất bổ": ["xuất bổ", "xuất bỏ", "xuat bo", "xuất thêm"],
            "công đoàn": ["công đoàn", "cong doan", "union", "thưởng"],
            "sổ quỹ": ["sổ quỹ", "so quy", "fund", "quỹ", "chuyển tiền"],
            "nhập đầu kỳ": ["nhập đầu kỳ", "nhap dau ky", "đầu kỳ", "initial"],
            "cài đặt": ["cài đặt", "cai dat", "settings", "config"],
        }
        found = False
        matched_key = None
        matched_idx = None
        # Ưu tiên khớp alias mở rộng
        for tab_name, aliases in alias_map.items():
            # Loại bỏ icon khi so sánh tên tab (ví dụ: '⚙️ Cài đặt')
            tab_name_compare = tab_name
            for key in tab_map.keys():
                key_no_icon = key.replace("⚙️ ", "").strip()
                if key_no_icon == tab_name:
                    tab_name_compare = key
                    break
            for alias in aliases:
                if alias in q_lower:
                    idx = tab_map.get(tab_name_compare)
                    if idx is not None:
                        matched_key = tab_name_compare
                        matched_idx = idx
                        found = True
                        break
            if found:
                break
        if found and matched_idx is not None:
            self.main_window.tabs.setCurrentIndex(matched_idx)
            print(
                f"[AI] Chuyển tab: '{matched_key}' (index: {matched_idx}) từ câu hỏi: '{question}'"
            )
            # Xử lý sub-tab Ca bán hàng rõ ràng
            if matched_key == "ca bán hàng" and hasattr(
                self.main_window, "tab_ca_banhang_tabs"
            ):
                if any(
                    x in q_lower
                    for x in ["nhận hàng", "nhan hang", "receive", "kiểm kê", "kiem ke"]
                ):
                    self.main_window.tab_ca_banhang_tabs.setCurrentIndex(0)
                elif any(
                    x in q_lower
                    for x in [
                        "bán hàng",
                        "ban hang",
                        "sell",
                        "thanh toán",
                        "thanh toan",
                    ]
                ):
                    self.main_window.tab_ca_banhang_tabs.setCurrentIndex(1)
            return
        # Nếu không tìm thấy, thử khớp alias cũ trong tab_map
        for key, idx in tab_map.items():
            if key in q_lower:
                self.main_window.tabs.setCurrentIndex(idx)
                print(
                    f"[AI] Chuyển tab: '{key}' (index: {idx}) từ câu hỏi: '{question}' [fallback]"
                )
                # Xử lý sub-tab Ca bán hàng
                if key == "ca bán hàng" and hasattr(
                    self.main_window, "tab_ca_banhang_tabs"
                ):
                    if any(
                        x in q_lower
                        for x in [
                            "nhận hàng",
                            "nhan hang",
                            "receive",
                            "kiểm kê",
                            "kiem ke",
                        ]
                    ):
                        self.main_window.tab_ca_banhang_tabs.setCurrentIndex(0)
                    elif any(
                        x in q_lower
                        for x in [
                            "bán hàng",
                            "ban hang",
                            "sell",
                            "thanh toán",
                            "thanh toan",
                        ]
                    ):
                        self.main_window.tab_ca_banhang_tabs.setCurrentIndex(1)
                return
        # Nếu không tìm thấy, không chuyển tab

    def execute_action(
        self, action_name: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute action with permission check"""
        if not self.action_system:
            return {"success": False, "message": "Action system not initialized"}
        return self.action_system.execute_action(action_name, params)


# Alias for backward compatibility
AIAssistant = HybridAI
