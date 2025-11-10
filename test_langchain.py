"""
Test script cho LangChain integration
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_system.hybrid import HybridAI


def test_langchain_integration():
    """Test LangChain memory & smart prompts"""

    print("="*60)
    print("🧪 TEST LANGCHAIN INTEGRATION")
    print("="*60)

    # Test 1: Khởi tạo AI với LangChain
    print("\n[TEST 1] Khởi tạo HybridAI với LangChain...")
    ai = HybridAI(
        db_path="fapp.db",
        main_window=None,
        current_user_role="admin",
        current_user_id=1
    )
    print("✅ Khởi tạo thành công!")
    print(f"   - AI Mode: {ai.ai_mode}")
    print(f"   - Model: {ai.model_name}")
    print(f"   - LangChain Memory: {'✅ Active' if ai.enhanced_memory else '❌ Disabled'}")
    print(f"   - Smart Prompts: {'✅ Active' if ai.prompt_manager else '❌ Disabled'}")

    # Test 2: Hỏi đáp và lưu vào memory
    print("\n[TEST 2] Test conversation với memory...")
    questions = [
        "có bao nhiêu tab trong app",
        "tab chi tiết bán làm gì",
        "cách tính giá trong app"
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n   Q{i}: {question}")
        answer, conv_id = ai.ask(question)
        print(f"   A{i}: {answer[:100]}...")  # First 100 chars
        print(f"   Conv ID: {conv_id}")

    # Test 3: Kiểm tra memory statistics
    if ai.enhanced_memory:
        print("\n[TEST 3] Memory Statistics...")
        stats = ai.enhanced_memory.get_statistics()
        print(f"   - Total Conversations: {stats['total_conversations']}")
        print(f"   - Experience Level: {stats['experience_level']}")
        print(f"   - Last Active: {stats['last_active']}")

    # Test 4: Test smart prompts
    if ai.prompt_manager:
        print("\n[TEST 4] Smart Prompts...")
        prompts = ai.prompt_manager.get_all_prompts()
        for prompt_type in ['newbie', 'expert', 'accountant']:
            if prompt_type in prompts:
                print(f"   ✅ {prompt_type.upper()} prompt loaded ({len(prompts[prompt_type])} chars)")

    # Test 5: Test feedback system
    print("\n[TEST 5] Test Feedback System...")
    print("   Sending 👍 feedback for last conversation...")
    ai.feedback(conv_id, True)
    print("   ✅ Feedback saved!")

    print("\n" + "="*60)
    print("✅ TẤT CẢ TESTS HOÀN TẤT!")
    print("="*60)


if __name__ == "__main__":
    test_langchain_integration()
