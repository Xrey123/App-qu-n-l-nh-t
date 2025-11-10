"""
QUICK START - Auto Trainer
"""

print(
    """
╔══════════════════════════════════════════════════════════════════╗
║          🤖 AUTO TRAINER - TỰ ĐỘNG DẠY AI                       ║
╚══════════════════════════════════════════════════════════════════╝

📌 2 CHỨC NĂNG:

   1️⃣ SMART ASK (KHUYẾN NGHỊ ⭐)
      → Copilot đọc DATABASE THẬT
      → Trả lời dựa trên logic app
      → Dạy AI tự động
      
   2️⃣ Auto Trainer (Cũ)
      → Trả lời từ knowledge base
      → Ví dụ mẫu

─────────────────────────────────────────────────────────────────

🚀 CÁCH DÙNG:

   ╭─ SMART ASK (Gõ không dấu) ─────────────────────╮
   │ python q.py cau hoi cua ban                    │
   │                                                 │
   │ Ví dụ:                                         │
   │  python q.py gia PLC RACER bao nhieu?          │
   │  python q.py con PLC KOMAT khong?              │
   │  python q.py co san pham gi?                   │
   ╰─────────────────────────────────────────────────╯

   ╭─ Auto Trainer (Cần tiếng Việt) ───────────────╮
   │ python hoi.py "câu hỏi tiếng Việt"            │
   ╰─────────────────────────────────────────────────╯

─────────────────────────────────────────────────────────────────

💡 VÍ DỤ THỰC TẾ:

   python q.py gia PLC RACER PLUS bao nhieu?
   python q.py lam sao de nhap kho?
   python q.py co san pham gi?

─────────────────────────────────────────────────────────────────

📊 AI LEVEL:
"""
)

# Load và hiển thị level
import json
from pathlib import Path

level_file = Path("src/ai_offline_pro/ai_level.json")
if level_file.exists():
    with open(level_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        print(f"   🎮 Level: {data['level']}")
        print(f"   📚 Đã học: {data['total_questions_learned']} câu")
        print(f"   📅 Cập nhật: {data['last_updated'][:19]}")
else:
    print("   🎮 Level: 1 (Mới bắt đầu)")
    print("   📚 Đã học: 0 câu")

print(
    """
─────────────────────────────────────────────────────────────────

📖 Xem hướng dẫn:
   - SMART_ASK_README.md (Khuyến nghị)
   - AUTO_TRAINER_README.md

╔══════════════════════════════════════════════════════════════════╗
║  🎉 BẮT ĐẦU HỎI: python q.py cau hoi cua ban 🚀                 ║
╚══════════════════════════════════════════════════════════════════╝
"""
)
