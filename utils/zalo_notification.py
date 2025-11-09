"""
Zalo Notification System - Gửi thông báo số dư qua Zalo

Có 2 phương pháp:
1. Zalo Official Account (OA) API - Chuyên nghiệp, cần đăng ký
2. Zalo Web Hook - Đơn giản hơn nhưng giới hạn

Documentation: https://developers.zalo.me/docs/official-account/
"""

import requests
import json
from datetime import datetime
from utils.logging_config import get_logger
from utils.money import format_price

logger = get_logger(__name__)


class ZaloNotificationError(Exception):
    """Custom exception for Zalo notification errors"""
    pass


class ZaloNotifier:
    """
    Zalo Official Account Notifier
    
    Setup:
    1. Đăng ký Zalo OA tại: https://oa.zalo.me/
    2. Tạo app tại: https://developers.zalo.me/
    3. Lấy access_token và OA ID
    4. Lưu vào .env file
    """
    
    def __init__(self, access_token: str = None, oa_id: str = None):
        """
        Initialize Zalo notifier
        
        Args:
            access_token: Zalo OA access token (get from https://developers.zalo.me/)
            oa_id: Zalo Official Account ID
        """
        self.access_token = access_token or self._get_token_from_env()
        self.oa_id = oa_id or self._get_oa_id_from_env()
        self.api_base = "https://openapi.zalo.me/v2.0/oa"
        
        if not self.access_token:
            logger.warning("Zalo access token not configured")
        if not self.oa_id:
            logger.warning("Zalo OA ID not configured")
    
    def _get_token_from_env(self):
        """Get access token from .env file"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv('ZALO_ACCESS_TOKEN')
    
    def _get_oa_id_from_env(self):
        """Get OA ID from .env file"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv('ZALO_OA_ID')
    
    def send_balance_notification(self, user_phone: str, username: str, balance: float, 
                                  balance_type: str = "nợ") -> bool:
        """
        Gửi thông báo số dư qua Zalo
        
        Args:
            user_phone: Số điện thoại user (format: 84xxxxxxxxx)
            username: Tên user
            balance: Số dư (âm = nợ, dương = thừa)
            balance_type: "nợ" hoặc "thừa"
        
        Returns:
            True nếu gửi thành công
        
        Example:
            notifier = ZaloNotifier()
            notifier.send_balance_notification(
                user_phone="84987654321",
                username="Nguyễn Văn A",
                balance=-500000,
                balance_type="nợ"
            )
        """
        if not self.access_token or not self.oa_id:
            logger.error("Zalo not configured. Please setup access_token and oa_id")
            return False
        
        try:
            # Format message
            balance_str = format_price(abs(balance))
            status_emoji = "⚠️" if balance < 0 else "✅"
            
            message = f"""
{status_emoji} THÔNG BÁO SỐ DƯ - SHOPFLOW

👤 User: {username}
💰 Số dư: {balance_str} VNĐ
📊 Trạng thái: {"NỢ" if balance < 0 else "THỪA"}
📅 Ngày: {datetime.now().strftime("%d/%m/%Y %H:%M")}

{"⚠️ Vui lòng nộp tiền sớm nhất có thể!" if balance < 0 else "✅ Đã thanh toán đủ"}

---
🏪 ShopFlow - Hệ thống quản lý bán hàng
"""
            
            # Send via Zalo OA API
            return self._send_text_message(user_phone, message.strip())
            
        except Exception as e:
            logger.error(f"Failed to send Zalo notification: {e}", exc_info=True)
            return False
    
    def _send_text_message(self, phone: str, message: str) -> bool:
        """
        Gửi tin nhắn text qua Zalo OA API
        
        Args:
            phone: Số điện thoại (format: 84xxxxxxxxx)
            message: Nội dung tin nhắn
        
        Returns:
            True nếu thành công
        """
        url = f"{self.api_base}/message"
        
        headers = {
            "Content-Type": "application/json",
            "access_token": self.access_token
        }
        
        payload = {
            "recipient": {
                "user_id": phone  # hoặc "phone_number" tùy API version
            },
            "message": {
                "text": message
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("error") == 0:
                logger.info(f"Sent Zalo notification to {phone}")
                return True
            else:
                logger.error(f"Zalo API error: {result}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Zalo message: {e}", exc_info=True)
            return False
    
    def send_bulk_balance_notifications(self, users_data: list) -> dict:
        """
        Gửi thông báo số dư cho nhiều users
        
        Args:
            users_data: List of dict với keys: phone, username, balance
            
        Example:
            users = [
                {"phone": "84987654321", "username": "User A", "balance": -500000},
                {"phone": "84912345678", "username": "User B", "balance": 200000},
            ]
            results = notifier.send_bulk_balance_notifications(users)
        
        Returns:
            {"success": 2, "failed": 0, "details": [...]}
        """
        results = {"success": 0, "failed": 0, "details": []}
        
        for user in users_data:
            phone = user.get("phone")
            username = user.get("username")
            balance = user.get("balance", 0)
            
            if not phone or not username:
                logger.warning(f"Missing phone or username for user: {user}")
                results["failed"] += 1
                continue
            
            success = self.send_balance_notification(
                user_phone=phone,
                username=username,
                balance=balance
            )
            
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append({
                "phone": phone,
                "username": username,
                "success": success
            })
        
        logger.info(f"Bulk notification: {results['success']} success, {results['failed']} failed")
        return results


class SimpleZaloNotifier:
    """
    Simple Zalo Notifier - Không cần OA, dùng webhook đơn giản
    
    Phương pháp:
    1. Tạo Zalo group với tất cả nhân viên
    2. Thêm bot vào group
    3. Bot gửi message vào group
    4. Tag user cụ thể
    
    Hạn chế: Cần Zalo group, message công khai
    """
    
    def __init__(self, webhook_url: str = None):
        """
        Args:
            webhook_url: Webhook URL của Zalo bot/group
        """
        self.webhook_url = webhook_url or self._get_webhook_from_env()
        
        if not self.webhook_url:
            logger.warning("Zalo webhook URL not configured")
    
    def _get_webhook_from_env(self):
        """Get webhook URL from .env"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv('ZALO_WEBHOOK_URL')
    
    def send_balance_notification(self, username: str, balance: float) -> bool:
        """
        Gửi thông báo đơn giản qua webhook
        
        Args:
            username: Tên user
            balance: Số dư
        
        Returns:
            True nếu thành công
        """
        if not self.webhook_url:
            logger.error("Webhook URL not configured")
            return False
        
        try:
            balance_str = format_price(abs(balance))
            status_emoji = "⚠️" if balance < 0 else "✅"
            
            message = f"{status_emoji} @{username}: Số dư {balance_str} VNĐ"
            
            response = requests.post(
                self.webhook_url,
                json={"text": message},
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Sent simple Zalo notification for {username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False


# Helper functions
def notify_user_balance(user_id: int, username: str, balance: float, 
                       phone: str = None, method: str = "oa") -> bool:
    """
    Gửi thông báo số dư cho user
    
    Args:
        user_id: ID của user trong DB
        username: Tên user
        balance: Số dư
        phone: Số điện thoại (nếu dùng OA method)
        method: "oa" (Official Account) hoặc "webhook" (Simple)
    
    Returns:
        True nếu gửi thành công
    
    Example:
        # Trong main_gui.py
        from utils.zalo_notification import notify_user_balance
        
        # Gửi thông báo khi load tab Sổ quỹ
        notify_user_balance(
            user_id=5,
            username="Nguyễn Văn A",
            balance=-500000,
            phone="84987654321",
            method="oa"
        )
    """
    try:
        if method == "oa":
            if not phone:
                logger.warning(f"No phone number for user {username}")
                return False
            
            notifier = ZaloNotifier()
            return notifier.send_balance_notification(
                user_phone=phone,
                username=username,
                balance=balance
            )
        
        elif method == "webhook":
            notifier = SimpleZaloNotifier()
            return notifier.send_balance_notification(
                username=username,
                balance=balance
            )
        
        else:
            logger.error(f"Unknown notification method: {method}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to notify user balance: {e}", exc_info=True)
        return False


def notify_all_negative_balances(threshold: float = -100000) -> dict:
    """
    Gửi thông báo cho tất cả users có số dư âm (nợ)
    
    Args:
        threshold: Ngưỡng nợ tối thiểu để gửi thông báo (VD: -100,000 = nợ > 100k)
    
    Returns:
        {"success": int, "failed": int}
    
    Example:
        # Chạy hàng ngày lúc 9h sáng
        from utils.zalo_notification import notify_all_negative_balances
        
        results = notify_all_negative_balances(threshold=-100000)
        print(f"Đã gửi {results['success']} thông báo")
    """
    from users import lay_tat_ca_user
    
    users = lay_tat_ca_user()
    notifier = ZaloNotifier()
    
    users_to_notify = []
    for user_id, username, role, so_du in users:
        if so_du < threshold:
            # TODO: Lấy phone từ DB (cần thêm cột phone vào bảng Users)
            users_to_notify.append({
                "phone": f"84{user_id:09d}",  # Placeholder - cần phone thật
                "username": username,
                "balance": so_du
            })
    
    if not users_to_notify:
        logger.info("No users with negative balance to notify")
        return {"success": 0, "failed": 0}
    
    return notifier.send_bulk_balance_notifications(users_to_notify)
