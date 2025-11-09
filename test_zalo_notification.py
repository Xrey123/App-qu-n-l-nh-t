"""
Test Zalo Notification System
"""

from utils.zalo_notification import ZaloNotifier, SimpleZaloNotifier, notify_user_balance

print("=" * 60)
print("🧪 TEST ZALO NOTIFICATION SYSTEM")
print("=" * 60)

# Test 1: Check configuration
print("\n✅ Test 1: Configuration")
notifier = ZaloNotifier()
if notifier.access_token:
    print(f"   ✓ Access token: {notifier.access_token[:20]}...")
else:
    print("   ✗ Access token NOT configured")
    print("   → Add ZALO_ACCESS_TOKEN to .env file")

if notifier.oa_id:
    print(f"   ✓ OA ID: {notifier.oa_id}")
else:
    print("   ✗ OA ID NOT configured")
    print("   → Add ZALO_OA_ID to .env file")

# Test 2: Send test notification (if configured)
print("\n✅ Test 2: Send Test Notification")
if notifier.access_token and notifier.oa_id:
    # TODO: Replace with real phone number
    test_phone = "84987654321"  # THAY SỐ PHONE THẬT Ở ĐÂY
    test_username = "Test User"
    test_balance = -500000
    
    print(f"   Sending to: {test_phone}")
    print(f"   Username: {test_username}")
    print(f"   Balance: {test_balance:,} VNĐ")
    
    success = notifier.send_balance_notification(
        user_phone=test_phone,
        username=test_username,
        balance=test_balance
    )
    
    if success:
        print("   ✅ Notification sent successfully!")
        print("   → Check Zalo app to verify message received")
    else:
        print("   ❌ Failed to send notification")
        print("   → Check logs/shopflow_*.log for details")
else:
    print("   ⚠️ Skipped - Not configured")
    print("   → Configure Zalo OA first (see HUONG_DAN_ZALO_NOTIFICATION.md)")

# Test 3: Webhook method
print("\n✅ Test 3: Webhook Method")
webhook_notifier = SimpleZaloNotifier()
if webhook_notifier.webhook_url:
    print(f"   ✓ Webhook URL: {webhook_notifier.webhook_url[:40]}...")
    
    success = webhook_notifier.send_balance_notification(
        username="Test User",
        balance=-300000
    )
    
    if success:
        print("   ✅ Webhook notification sent!")
    else:
        print("   ❌ Webhook failed")
else:
    print("   ✗ Webhook NOT configured")
    print("   → Add ZALO_WEBHOOK_URL to .env file")

# Test 4: Database integration
print("\n✅ Test 4: Database Integration")
try:
    from users import lay_tat_ca_user
    
    users = lay_tat_ca_user()
    print(f"   ✓ Found {len(users)} users in database")
    
    # Show users with negative balance
    users_with_debt = []
    for user_id, username, role, so_du in users:
        if so_du < 0:
            users_with_debt.append((username, so_du))
    
    if users_with_debt:
        print(f"   ⚠️ {len(users_with_debt)} users with negative balance:")
        for username, balance in users_with_debt[:5]:  # Show first 5
            print(f"      - {username}: {balance:,.0f} VNĐ")
    else:
        print("   ✅ No users with negative balance")
        
except Exception as e:
    print(f"   ❌ Database error: {e}")

# Summary
print("\n" + "=" * 60)
print("📊 TEST SUMMARY")
print("=" * 60)
print("\nSetup checklist:")
print("□ Đăng ký Zalo OA tại: https://oa.zalo.me/")
print("□ Tạo app tại: https://developers.zalo.me/")
print("□ Thêm ZALO_ACCESS_TOKEN vào .env")
print("□ Thêm ZALO_OA_ID vào .env")
print("□ Thêm cột phone vào bảng Users")
print("□ Users follow OA")
print("□ Test gửi thông báo thật")
print("\nNext steps:")
print("1. Read: HUONG_DAN_ZALO_NOTIFICATION.md")
print("2. Configure: .env file")
print("3. Integrate: main_gui.py")
print("4. Test: With real phone numbers")
print("\n" + "=" * 60)
