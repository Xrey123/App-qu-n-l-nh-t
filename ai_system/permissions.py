"""
Permissions - Role-based Permission Management
Định nghĩa quyền cho Admin, Accountant, Staff
"""

from typing import Dict, List, Optional


class RolePermissions:
    """
    Quản lý quyền hạn theo role
    - Admin: Full access
    - Accountant: Read + Reports (no User/Product management)
    - Staff: Sales only (5 tabs)
    """
    
    # Role hierarchy
    ROLE_HIERARCHY = {
        "admin": 3,       # Highest
        "accountant": 2,
        "staff": 1        # Lowest
    }
    
    # All tabs in app
    ALL_TABS = [
        "🏠 Trang chủ",
        "📦 Sản phẩm",
        "💰 Lịch sử giá",
        "🛒 Ca bán hàng",
        "📝 Chi tiết bán",
        "📄 Hóa đơn",
        "📊 Báo cáo",
        "🤖 AI Agent",
        "👤 User",
        "⚖️ Chênh lệch",
        "📤 Xuất bỏ",
        "🏭 Công đoàn",
        "💵 Sổ quỹ",
        "📥 Nhập đầu kỳ"
    ]
    
    # Permission mapping
    PERMISSIONS = {
        "admin": {
            "tabs": ALL_TABS,  # All tabs
            "actions": [
                "navigate_to_tab",
                "create_invoice",
                "get_product_info",
                "get_inventory",
                "search_product",
                "calculate_price",
                "add_product",
                "edit_product",
                "delete_product",
                "manage_users",
                "add_user",
                "edit_user",
                "delete_user",
                "export_report",
                "view_cash_fund",
                "manage_stock",
                "process_discrepancy",
                "export_excess",
            ],
            "description": "Toàn quyền - Quản trị viên"
        },
        
        "accountant": {
            "tabs": [
                "🏠 Trang chủ",
                "🛒 Ca bán hàng",
                "📝 Chi tiết bán",
                "📄 Hóa đơn",
                "📊 Báo cáo",
                "🤖 AI Agent",
                "⚖️ Chênh lệch",
                "📤 Xuất bỏ",
                "🏭 Công đoàn",
                "💵 Sổ quỹ",
                "📥 Nhập đầu kỳ"
            ],  # No Sản phẩm, Lịch sử giá, User
            "actions": [
                "navigate_to_tab",
                "create_invoice",
                "get_product_info",
                "get_inventory",
                "search_product",
                "calculate_price",
                "export_report",
                "view_cash_fund",
                "process_discrepancy",
                "export_excess",
            ],
            "description": "Kế toán - Xem báo cáo, xuất bỏ, quỹ"
        },
        
        "staff": {
            "tabs": [
                "🏠 Trang chủ",
                "🛒 Ca bán hàng",
                "📝 Chi tiết bán",
                "📄 Hóa đơn",
                "🤖 AI Agent"
            ],  # Only sales-related tabs
            "actions": [
                "navigate_to_tab",
                "create_invoice",
                "get_product_info",
                "calculate_price",
            ],
            "description": "Nhân viên - CHỈ bán hàng"
        }
    }
    
    @classmethod
    def get_allowed_tabs(cls, role: str) -> List[str]:
        """Get tabs that role can access"""
        return cls.PERMISSIONS.get(role, {}).get("tabs", [])
    
    @classmethod
    def get_allowed_actions(cls, role: str) -> List[str]:
        """Get actions that role can perform"""
        return cls.PERMISSIONS.get(role, {}).get("actions", [])
    
    @classmethod
    def can_access_tab(cls, role: str, tab_name: str) -> bool:
        """Check if role can access specific tab"""
        allowed_tabs = cls.get_allowed_tabs(role)
        
        # Normalize tab name (remove emoji, strip whitespace)
        tab_normalized = tab_name.strip()
        
        for allowed_tab in allowed_tabs:
            # Match by name (with or without emoji)
            if tab_normalized in allowed_tab or allowed_tab in tab_normalized:
                return True
        
        return False
    
    @classmethod
    def can_perform_action(cls, role: str, action_name: str) -> bool:
        """Check if role can perform specific action"""
        allowed_actions = cls.get_allowed_actions(role)
        return action_name in allowed_actions
    
    @classmethod
    def get_role_level(cls, role: str) -> int:
        """Get role level (higher = more privilege)"""
        return cls.ROLE_HIERARCHY.get(role, 0)
    
    @classmethod
    def is_higher_role(cls, role1: str, role2: str) -> bool:
        """Check if role1 has higher privilege than role2"""
        return cls.get_role_level(role1) > cls.get_role_level(role2)
    
    @classmethod
    def get_role_description(cls, role: str) -> str:
        """Get role description"""
        return cls.PERMISSIONS.get(role, {}).get("description", "Unknown role")
    
    @classmethod
    def validate_role(cls, role: str) -> bool:
        """Check if role is valid"""
        return role in cls.PERMISSIONS


# Export helper functions for easy use
def can_access_tab(role: str, tab_name: str) -> bool:
    """Helper: Check if role can access tab"""
    return RolePermissions.can_access_tab(role, tab_name)


def can_perform_action(role: str, action_name: str) -> bool:
    """Helper: Check if role can perform action"""
    return RolePermissions.can_perform_action(role, action_name)


def get_allowed_tabs(role: str) -> List[str]:
    """Helper: Get allowed tabs for role"""
    return RolePermissions.get_allowed_tabs(role)
