"""
Test trực tiếp Database Query - Không qua Groq API
"""

import sys

sys.path.append(".")

from ai_system.hybrid import HybridAI

print("=" * 60)
print("  TEST DATABASE QUERY TRỰC TIẾP")
print("=" * 60)

# Khởi tạo AI
ai = HybridAI(db_path="fapp.db", current_user_role="admin")

# Test các câu hỏi
test_questions = [
    "Còn bao nhiêu sản phẩm trong kho?",
    "Giá của sản phẩm 2T?",
    "Giá 2T",
    "Danh sách sản phẩm có chữ 2T",
    "Ngày 7/11 hung bán được bao nhiêu sản phẩm?",
    "User hung bán được gì ngày 7/11?",
    "Tổng doanh thu ngày 7/11",
    "Doanh thu ngày 8/11",
]

for i, question in enumerate(test_questions, 1):
    print(f"\n{'='*60}")
    print(f"📝 CÂU HỎI {i}: {question}")
    print(f"{'='*60}")

    # Tìm SQL template
    sql = ai._find_query_template(question)

    if sql:
        print(f"\n🔍 SQL: {sql}")

        # Query database
        result = ai._query_db(sql)

        if result:
            print(f"\n📊 RAW RESULT: {result[:3]}")  # Hiển thị 3 dòng đầu

            # Format result
            formatted = ai._format_db_result(result, question)
            print(f"\n💬 FORMATTED OUTPUT:")
            print(formatted)
        else:
            print("\n⚠️ Không có dữ liệu")
    else:
        print("\n❌ KHÔNG TÌM THẤY SQL TEMPLATE")
        print("   → AI sẽ dùng Groq/Phi3 để trả lời")

print("\n" + "=" * 60)
print("  KẾT THÚC TEST")
print("=" * 60)
