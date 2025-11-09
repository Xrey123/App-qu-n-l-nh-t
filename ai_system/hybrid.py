"""
Hybrid AI System - Groq API (online) + Phi3:mini + RAG (offline)
"""

import sqlite3
import json
import time
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests


class HybridAI:
    """
    Hybrid AI với 2 modes:
    - Online: Groq API (Llama 3.3 70B) - Cực thông minh, cực nhanh
    - Offline: Phi3:mini + RAG - Tạm được, offline OK
    """
    
    def __init__(self, db_path: str = "fapp.db", main_window=None, current_user_role: str = "staff"):
        self.db_path = db_path
        self.main_window = main_window
        self.current_user_role = current_user_role
        
        # Load configs
        self.config = self._load_config()
        self.db_queries = self._load_json("ai/db_queries.json", {})
        self.memory = self._load_json("ai/memory.json", {})
        self.app_knowledge = self._load_json("ai/app_knowledge_enhanced.json", {})
        if not self.app_knowledge:
            self.app_knowledge = self._load_json("ai/app_knowledge.json", {})
        
        # Conversation history (for context memory)
        self.conversation_history = []
        self.max_history = 10  # Keep last 10 Q&A pairs
        
        # Initialize AI mode
        self.groq_api_key = self.config.get("groq_api_key", "")
        self.use_groq = self._check_groq_available()
        
        if self.use_groq:
            self.ai_mode = "online"
            self.model_name = "llama-3.3-70b-versatile"  # Updated: llama-3.1 decommissioned
            print("✅ AI Mode: ONLINE (Groq API - Llama 3.3 70B)")
        else:
            self.ai_mode = "offline"
            self.ollama_url = "http://localhost:11434/api/generate"
            self.model_name = "phi3:mini"
            print("⚠️ AI Mode: OFFLINE (Phi3:mini + RAG)")
        
        # Cache
        self.query_cache: Dict[str, tuple] = {}
        self.cache_ttl = 300
        
        # Initialize Actions System
        try:
            from .actions import AIActionSystem
            self.action_system = AIActionSystem(
                main_window=main_window,
                current_user_role=current_user_role
            )
        except:
            self.action_system = None
    
    def _load_config(self) -> dict:
        """Load config (Groq API key, etc.)"""
        config_path = "ai/config.json"
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def _save_config(self):
        """Save config"""
        config_path = "ai/config.json"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
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
                max_tokens=10
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
                temperature=0.5
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Save to history
            self.conversation_history.append({
                "question": question,
                "answer": answer
            })
            
            # Keep only last N pairs
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            return answer
            
        except Exception as e:
            # Fallback to offline if error
            print(f"⚠️ Groq API error: {e}. Switching to offline mode...")
            self.use_groq = False
            self.ai_mode = "offline"
            return self._ask_offline(question, context)
    
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
                    "options": {
                        "temperature": 0.5,
                        "num_predict": 200
                    }
                },
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json().get("response", "").strip()
        except:
            pass
        return ""
    
    def _build_context(self) -> str:
        """Build context from app knowledge"""
        
        # Load app knowledge from JSON
        app_info = self.app_knowledge.get("app_info", {})
        pricing_info = self.app_knowledge.get("pricing", {})
        
        # Build rich context
        context = f"""Bạn là AI trợ lý của HỆ THỐNG QUẢN LÝ CỬA HÀNG NHỚT.

📱 THÔNG TIN APP:
- Tên: {app_info.get('name', 'Hệ thống quản lý cửa hàng nhớt')}
- Công nghệ: {app_info.get('main_file', 'PyQt5 desktop app (main_gui.py)')}
- Database: {app_info.get('database', 'fapp.db (SQLite) - 13 bảng')}
- Launcher: {app_info.get('launcher', 'start.py hoặc START_APP_SIMPLE.bat')}

🛢️ SẢN PHẨM:
- Các loại nhớt: {app_info.get('sản phẩm', 'PLC KOMAT, PLC RACER, PLC CARTER, PCL GEAR OIL, PLC-AW HYDROIL')}
- Quản lý: Tồn kho, giá lẻ, giá buôn, giá VIP

� CÁCH TÍNH GIÁ TRONG APP:
{pricing_info.get('Giá lẻ', {}).get('mô tả', '- Giá lẻ: Áp dụng khi mua < ngưỡng buôn')}
{pricing_info.get('Giá buôn', {}).get('mô tả', '- Giá buôn: Áp dụng khi SL >= ngưỡng buôn (ví dụ: >=5 thùng)')}
{pricing_info.get('Giá VIP', {}).get('mô tả', '- Giá VIP: Dành cho khách hàng VIP (check trong database)')}

📊 CHỨC NĂNG CHÍNH:
- 🏠 Trang chủ: Dashboard, thống kê
- 📦 Sản phẩm: Quản lý danh sách nhớt (Admin/Accountant)
- 🛒 Ca bán hàng: Nhận hàng (kiểm kê) + Bán hàng
- 📄 Hóa đơn: Xuất hóa đơn, in PDF
- 👥 Khách hàng: Quản lý khách, check VIP
- 📊 Báo cáo: Doanh thu, lợi nhuận, tổng kết ca
- ⚙️ Cài đặt: Groq API (online AI mode)

🚫 QUY TẮC BẢO MẬT:
1. ❌ KHÔNG được đề cập code Python (.py files)
2. ❌ KHÔNG được nói "tôi không biết model nào" - LUÔN trả lời thật!
3. ❌ KHÔNG được trả lời chung chung như ChatGPT
4. ❌ KHÔNG được tiết lộ thông tin IT: database schema, SQL queries, file paths, API keys, system architecture
5. ❌ KHÔNG được nói về bảng nào, cột nào trong database
6. ❌ KHÔNG được hướng dẫn hack, truy cập trái phép, hoặc kỹ thuật hệ thống

✅ BẠN PHẢI:
1. ✅ Trả lời DỰA VÀO APP NÀY (fapp.db, main_gui.py, Python)
2. ✅ Giải thích ĐÚNG CÁCH TÍNH GIÁ trong app
3. ✅ Hướng dẫn ĐÚNG WORKFLOW (Nhận hàng → Bán hàng → Tổng kết ca)
4. ✅ Trả lời NGẮN GỌN, THÂN THIỆN, ĐÚNG TRỌNG TÂM
5. ✅ Chỉ hướng dẫn SỬ DỤNG app, KHÔNG nói về cấu trúc kỹ thuật

Nếu hỏi về model AI: Trả lời thật {"🚀 Groq API - Llama 3.3 70B" if self.use_groq else "💻 Phi3:mini offline"}"""
        
        return context
    
    def ask(self, question: str) -> str:
        """
        Main method - Route to online or offline
        """
        # Normalize question
        question = self._normalize_question(question)
        q_lower = question.lower()
        
        # Check which AI is being used
        if "model nào" in q_lower or "ai nào" in q_lower:
            if self.use_groq:
                return f"🚀 Tôi đang dùng **Groq API - Llama 3.3 70B** (online mode). Cực thông minh và cực nhanh! 😊"
            else:
                return f"💻 Tôi đang dùng **Phi3:mini** (offline mode). Nếu muốn AI thông minh hơn, hãy cấu hình Groq API trong Settings!"
        
        # ✅ BƯỚC 1: CHECK PERMISSION
        permission_response = self._check_permission(question)
        if permission_response:
            return permission_response
        
        # ✅ BƯỚC 2: FILTER IT-SENSITIVE INFO
        if self._is_it_sensitive_question(question):
            return "🔒 Xin lỗi, tôi không thể cung cấp thông tin về kỹ thuật hệ thống. Hãy hỏi về cách sử dụng các chức năng trong app nhé! 😊"
        
        # Try DB query first (for data questions)
        data_keywords = ["bao nhiêu", "còn", "tồn", "danh sách", "liệt kê"]
        if any(kw in q_lower for kw in data_keywords):
            sql = self._find_query_template(question)
            if sql:
                result = self._query_db(sql)
                if result:
                    return self._format_db_result(result, question)
        
        # Skip app_knowledge search for logic/explanation questions
        # Let AI answer with rich context instead
        logic_keywords = ["cách", "giải thích", "tính", "tại sao", "như thế nào", "ra sao", "thế nào"]
        should_use_ai = any(kw in q_lower for kw in logic_keywords)
        
        # Try app knowledge ONLY for UI/tab questions
        if not should_use_ai:
            tab_keywords = ["tab", "mở", "vào đâu", "nút", "button", "click"]
            if any(kw in q_lower for kw in tab_keywords):
                app_answer = self._search_app_knowledge(question)
                if app_answer:
                    # ✅ BƯỚC 3: AUTO SWITCH TAB
                    self._auto_switch_tab(question)
                    return app_answer
        
        # Ask AI (online or offline) - This has rich context about pricing
        context = self._build_context()
        
        if self.use_groq:
            answer = self._ask_groq(question, context)
        else:
            answer = self._ask_offline(question, context)
        
        if answer:
            # ✅ BƯỚC 4: AUTO SWITCH TAB for AI answers too
            self._auto_switch_tab(question)
            return answer
        
        return "Hãy thử hỏi chi tiết hơn về tabs, workflows, sản phẩm, hoặc báo cáo nhé! 😊"
    
    def _load_json(self, path: str, default: Any) -> Any:
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
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
        sorted_queries = sorted(self.db_queries.items(), key=lambda x: len(x[0]), reverse=True)
        
        for key, sql in sorted_queries:
            if key in q_lower:
                # Parse dynamic parameters
                result_sql = sql
                
                # Extract date from question (e.g., "7/11", "ngày 7/11", "2024-11-07")
                date_match = re.search(r'(\d{1,2})[/\-](\d{1,2})(?:[/\-](\d{2,4}))?', question)
                if date_match and '{date}' in sql:
                    day = date_match.group(1).zfill(2)
                    month = date_match.group(2).zfill(2)
                    year = date_match.group(3) if date_match.group(3) else str(datetime.now().year)
                    if len(year) == 2:
                        year = '20' + year
                    parsed_date = f"{year}-{month}-{day}"
                    result_sql = result_sql.replace('{date}', parsed_date)
                
                # Extract username from question
                if '{user}' in sql:
                    # Find user name (word after "user" or before "bán")
                    user_match = re.search(r'(?:user\s+|^)(\w+)(?:\s+bán)?', q_lower)
                    if user_match:
                        username = user_match.group(1).upper()
                        result_sql = result_sql.replace('{user}', username)
                    else:
                        # If no specific user, skip this template
                        continue
                
                # Extract product name/keyword from question
                if '{query}' in sql:
                    # Extract product name (e.g., "2T", "KOMAT", "RACER")
                    # Try different patterns
                    query_match = re.search(r'(?:của|giá)\s+(?:sản phẩm\s+)?(\w+)', q_lower)
                    if not query_match:
                        # Try standalone product name
                        query_match = re.search(r'\b(\w*\d+\w*)\b', q_lower)  # Match word with digits
                    
                    if query_match:
                        product_keyword = query_match.group(1).upper()
                        result_sql = result_sql.replace('{query}', product_keyword)
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
            if "doanh thu" in q_lower or "tổng" in q_lower or "giao dịch" in q_lower or "chênh lệch" in q_lower:
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
        if ("sản phẩm" in q_lower or "tồn kho" in q_lower or "còn" in q_lower or "giá" in q_lower) and len(result[0]) >= 2:
            # Check if it's a price query (4 columns: ten, gia_le, gia_buon, gia_vip)
            if len(result[0]) == 4 and all(isinstance(val, (int, float, type(None))) for val in result[0][1:]):
                items = []
                for row in result:
                    ten = row[0]
                    gia_le = f"{row[1]:,.0f}".replace(",", ".") if row[1] else "N/A"
                    gia_buon = f"{row[2]:,.0f}".replace(",", ".") if row[2] else "N/A"
                    gia_vip = f"{row[3]:,.0f}".replace(",", ".") if row[3] else "N/A"
                    items.append(f"• **{ten}**\n  - Giá lẻ: {gia_le} VNĐ\n  - Giá buôn: {gia_buon} VNĐ\n  - Giá VIP: {gia_vip} VNĐ")
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
                role_icon = {"admin": "👑", "accountant": "👔", "staff": "👤"}.get(role, "👤")
                items.append(f"• {role_icon} **{username}** ({role})")
            return f"👥 **Danh sách User:**\n\n" + "\n".join(items)
        
        # Generic result (fallback)
        return f"Kết quả: {result[:3]}"
    
    def _search_app_knowledge(self, question: str) -> Optional[str]:
        """Search app knowledge with sub-tabs support"""
        q_lower = question.lower()
        
        # Normalize Vietnamese (bỏ → bổ, etc.)
        q_normalized = q_lower.replace("bổ", "bỏ").replace("xuất bỗ", "xuất bỏ")
        
        # Search in app_knowledge
        for tab_name, tab_info in self.app_knowledge.get("tabs", {}).items():
            tab_name_lower = tab_name.lower().replace("bổ", "bỏ")
            keywords = [kw.lower().replace("bổ", "bỏ") for kw in tab_info.get("keywords", [])]
            
            if tab_name_lower in q_normalized or any(kw in q_normalized for kw in keywords):
                # Check if tab has sub_tabs
                if "sub_tabs" in tab_info:
                    # Tab has sub-tabs, ask which one
                    sub_tab_names = list(tab_info["sub_tabs"].keys())
                    result = f"📌 **Tab {tab_name}**\n\n"
                    result += f"🔹 Chức năng chung: {tab_info.get('chức năng', '')}\n\n"
                    result += f"Tab này có **{len(sub_tab_names)} sub-tabs:**\n"
                    for i, sub_name in enumerate(sub_tab_names, 1):
                        sub_func = tab_info["sub_tabs"][sub_name].get("chức năng", "")
                        result += f"{i}. **{sub_name}**: {sub_func}\n"
                    result += f"\n❓ Bạn muốn tôi hướng dẫn sub-tab nào?"
                    return result
                else:
                    # Normal tab without sub-tabs
                    result = f"📌 **Tab {tab_name}**\n\n"
                    result += f"🔹 Chức năng: {tab_info.get('chức năng', '')}\n"
                    
                    # Add workflow if exists
                    if "workflow" in tab_info:
                        result += f"\n📝 Cách sử dụng:\n{tab_info['workflow']}\n"
                    
                    return result
        
        # Search in sub_tabs specifically
        for tab_name, tab_info in self.app_knowledge.get("tabs", {}).items():
            if "sub_tabs" in tab_info:
                for sub_name, sub_info in tab_info["sub_tabs"].items():
                    sub_name_lower = sub_name.lower().replace("bổ", "bỏ")
                    sub_keywords = [kw.lower().replace("bổ", "bỏ") for kw in sub_info.get("keywords", [])]
                    
                    if sub_name_lower in q_normalized or any(kw in q_normalized for kw in sub_keywords):
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
                "sản phẩm": ["sản phẩm", "san pham", "product", "thêm sp", "xóa sp", "import"],
                "lịch sử giá": ["lịch sử giá", "lich su gia", "price history", "thay đổi giá"],
                "quản lý user": ["quản lý user", "quan ly user", "thêm user", "xóa user", "user management"],
                "chênh lệch": ["chênh lệch", "chenh lech", "difference"],
                "xuất bổ": ["xuất bổ", "xuất bỏ", "xuat bo", "xuất thêm"],
                "công đoàn": ["công đoàn", "cong doan", "union", "thưởng"],
                "sổ quỹ": ["sổ quỹ", "so quy", "fund", "quỹ", "chuyển tiền"],
                "nhập đầu kỳ": ["nhập đầu kỳ", "nhap dau ky", "đầu kỳ", "initial"]
            }
            
            for tab_name, keywords in restricted_keywords.items():
                if any(kw in q_lower for kw in keywords):
                    return f"🚫 **Xin lỗi**, tab **{tab_name}** chỉ dành cho **Admin** hoặc **Accountant**.\n\nBạn là **Staff**, bạn có thể hỏi về:\n✅ Trang chủ\n✅ Ca bán hàng (Nhận hàng, Bán hàng)\n✅ Chi tiết bán\n✅ Hóa đơn\n✅ Báo cáo\n✅ Cài đặt"
        
        return None
    
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
            "bao nhiêu", "còn", "tồn kho", "danh sách", "liệt kê", "tổng", 
            "số lượng", "hóa đơn", "sản phẩm", "chi tiết bán", "giao dịch",
            "đã bán", "doanh thu", "chênh lệch", "xuất bỏ", "công đoàn",
            "sổ quỹ", "giá", "nhớt", "khách", "user nào", "username"
        ]
        
        # Nếu là câu hỏi data query → CHO PHÉP (không chặn)
        if any(kw in q_lower for kw in data_query_keywords):
            # Nhưng vẫn chặn nếu hỏi về PASSWORD hoặc CẤU TRÚC DB (không chặn tên bảng)
            forbidden_in_data = [
                "password", "mật khẩu user", "pwd", "hash password", "token", "api key trong",
                "schema database", "cột nào", "column nào", "primary key", "foreign key",
                "cấu trúc bảng", "bảng có những cột", "table structure", "create table"
            ]
            if any(kw in q_lower for kw in forbidden_in_data):
                return True  # CHẶN
            return False  # CHO PHÉP (bao gồm cả câu hỏi về tên bảng)
        
        # ❌ BLOCKLIST: IT keywords NGUY HIỂM (chỉ chặn SQL commands và bảo mật)
        dangerous_keywords = [
            # SQL modification commands (chặn HOÀN TOÀN)
            "update sanpham", "delete from", "drop table", "insert into", "alter table", "truncate",
            "câu lệnh sql", "sql command để", "viết sql", "execute sql", "run query",
            
            # Code & Files (chặn)
            "main_gui.py", ".py file", "python code", "source code", "đoạn code", 
            "directory", "class mainwindow", "function ", "def ", "import ", "module",
            
            # Security CRITICAL (chặn)
            "password user", "pwd admin", "mật khẩu lưu", "mật khẩu hash", "token lưu", "secret key", 
            "api key trong db", "groq key", "hash password", "hack", "exploit", "injection", "vulnerability",
            
            # System path (chặn)
            "fapp.db location", "server ip", "port number", "localhost:", 
            "config.json path", "system architecture", "database file path"
        ]
        
        return any(kw in q_lower for kw in dangerous_keywords)
    
    def _auto_switch_tab(self, question: str):
        """
        Tự động chuyển đến tab tương ứng khi AI trả lời về tab đó.
        """
        if not self.main_window:
            return
        
        q_lower = question.lower()
        
        # Map keywords -> tab index
        tab_mapping = {
            "trang chủ": 0,
            "sản phẩm": 1 if self.current_user_role in ["admin", "accountant"] else None,
            "lịch sử giá": 2 if self.current_user_role in ["admin", "accountant"] else None,
            "ca bán hàng": 3,
            "nhận hàng": (3, 0),  # Parent tab 3, child tab 0
            "bán hàng": (3, 1),   # Parent tab 3, child tab 1
            "chi tiết bán": 4,
            "hóa đơn": 5,
            "báo cáo": 6,
            "cài đặt": 7,
            "quản lý user": 8 if self.current_user_role == "admin" else None,
            "chênh lệch": 9 if self.current_user_role in ["admin", "accountant"] else None,
            "xuất bổ": 10 if self.current_user_role == "accountant" else None,
            "công đoàn": 11 if self.current_user_role == "accountant" else None,
            "sổ quỹ": 12 if self.current_user_role == "accountant" else None,
            "nhập đầu kỳ": 13 if self.current_user_role == "accountant" else None,
        }
        
        # Normalize search keywords
        search_map = {
            "trang chu": "trang chủ",
            "san pham": "sản phẩm",
            "lich su gia": "lịch sử giá",
            "ca ban hang": "ca bán hàng",
            "nhan hang": "nhận hàng",
            "ban hang": "bán hàng",
            "chi tiet ban": "chi tiết bán",
            "hoa don": "hóa đơn",
            "bao cao": "báo cáo",
            "cai dat": "cài đặt",
            "quan ly user": "quản lý user",
            "chenh lech": "chênh lệch",
            "xuat bo": "xuất bổ",
            "xuat bổ": "xuất bổ",
            "cong doan": "công đoàn",
            "so quy": "sổ quỹ",
            "nhap dau ky": "nhập đầu kỳ"
        }
        
        # Find matching tab
        for keyword, normalized in search_map.items():
            if keyword in q_lower or normalized in q_lower:
                tab_info = tab_mapping.get(normalized)
                
                if tab_info is None:
                    continue
                
                try:
                    if isinstance(tab_info, tuple):
                        # Sub-tab: (parent_index, child_index)
                        parent_idx, child_idx = tab_info
                        self.main_window.tabs.setCurrentIndex(parent_idx)
                        # Access child tab widget
                        parent_widget = self.main_window.tabs.widget(parent_idx)
                        if hasattr(parent_widget, 'findChild'):
                            from PyQt5.QtWidgets import QTabWidget
                            child_tabs = parent_widget.findChild(QTabWidget)
                            if child_tabs:
                                child_tabs.setCurrentIndex(child_idx)
                    else:
                        # Main tab
                        self.main_window.tabs.setCurrentIndex(tab_info)
                    
                    return  # Stop after first match
                except Exception as e:
                    print(f"Warning: Could not switch to tab: {e}")
                    pass
    
    def execute_action(self, action_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action with permission check"""
        if not self.action_system:
            return {"success": False, "message": "Action system not initialized"}
        return self.action_system.execute_action(action_name, params)


# Alias for backward compatibility
AIAssistant = HybridAI
