"""
🤖 AI ACTIONS SYSTEM
Cho phép AI thực hiện thao tác trên app (click button, nhập data)
NHƯNG không cho phép truy cập code hoặc sửa đổi
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime


class AIActionSystem:
    """
    Hệ thống cho phép AI thực hiện actions trên app
    - AI có thể: Click button, nhập data, điều hướng tab, export báo cáo
    - AI KHÔNG THỂ: Xem code, sửa code, truy cập file system
    - AI TÔN TRỌNG: Quyền hạn của user đang đăng nhập
    """
    
    def __init__(self, main_window=None, current_user_role=None):
        self.main_window = main_window
        self.current_user_role = current_user_role or "staff"  # Default: staff (ít quyền nhất)
        self.action_log = []  # Log tất cả actions
        
        # Define PERMISSIONS per role
        self.role_permissions = {
            "admin": {
                "tabs": ["Trang chủ", "Sản phẩm", "Lịch sử giá", "Ca bán hàng", 
                        "Chi tiết bán", "Hóa đơn", "Báo cáo", "AI Agent", "User",
                        "Chênh lệch", "Xuất bỏ", "Công đoàn", "Sổ quỹ", "Nhập đầu kỳ"],
                "actions": ["navigate_to_tab", "add_product", "create_invoice", 
                           "get_product_info", "get_inventory", "export_report",
                           "calculate_price", "calculate_profit", "manage_users",
                           "edit_product", "delete_product", "view_all_reports"],
                "description": "Toàn quyền - Quản lý sản phẩm, user, báo cáo, tất cả tabs"
            },
            
            "accountant": {
                "tabs": ["Trang chủ", "Ca bán hàng", "Chi tiết bán", "Hóa đơn", 
                        "Báo cáo", "AI Agent", "Chênh lệch", "Xuất bỏ", "Công đoàn", 
                        "Sổ quỹ", "Nhập đầu kỳ"],
                "actions": ["navigate_to_tab", "create_invoice", "get_product_info",
                           "get_inventory", "export_report", "calculate_price",
                           "calculate_profit", "view_reports"],
                "description": "Kế toán - Xem báo cáo, xuất bỏ, công đoàn, sổ quỹ"
            },
            
            "staff": {
                "tabs": ["Trang chủ", "Ca bán hàng", "Chi tiết bán", "Hóa đơn", "AI Agent"],
                "actions": ["navigate_to_tab", "create_invoice", "get_product_info",
                           "calculate_price"],
                "description": "Nhân viên - CHỈ bán hàng, không xem báo cáo/quản lý"
            }
        }
        
        # Define available actions (WHITE LIST - chỉ cho phép những gì liệt kê)
        self.available_actions = {
            # Navigation actions
            "navigate_to_tab": {
                "description": "Chuyển đến tab cụ thể",
                "params": ["tab_name"],
                "example": "navigate_to_tab('Sản phẩm')"
            },
            
            # Data entry actions
            "add_product": {
                "description": "Thêm sản phẩm mới",
                "params": ["ten", "don_vi", "gia_le", "gia_buon", "gia_vip"],
                "example": "add_product('PLC KOMAT 2T', 'thùng', 350000, 320000, 300000)"
            },
            
            "create_invoice": {
                "description": "Tạo hóa đơn bán hàng",
                "params": ["khach_hang", "items", "loai_gia"],
                "example": "create_invoice('Khách A', [{'ten': 'PLC KOMAT 2T', 'so_luong': 10}], 'buon')"
            },
            
            # Query actions (read-only)
            "get_product_info": {
                "description": "Lấy thông tin sản phẩm",
                "params": ["ten_san_pham"],
                "example": "get_product_info('PLC KOMAT 2T')"
            },
            
            "get_inventory": {
                "description": "Xem tồn kho",
                "params": [],
                "example": "get_inventory()"
            },
            
            # Report actions
            "export_report": {
                "description": "Xuất báo cáo",
                "params": ["report_type", "start_date", "end_date"],
                "example": "export_report('tong_ket_ca', '2024-01-01', '2024-01-31')"
            },
            
            # Calculation actions (business logic)
            "calculate_price": {
                "description": "Tính giá bán (có thể giải thích công thức)",
                "params": ["so_luong", "loai_gia", "ten_san_pham"],
                "example": "calculate_price(10, 'buon', 'PLC KOMAT 2T')"
            },
            
            "calculate_profit": {
                "description": "Tính lợi nhuận (có thể giải thích cách tính)",
                "params": ["start_date", "end_date"],
                "example": "calculate_profit('2024-01-01', '2024-01-31')"
            }
        }
        
        # Business rules (AI có thể đọc để hiểu logic)
        self.business_rules = {
            "pricing": {
                "description": "Quy tắc tính giá",
                "rules": [
                    "Giá lẻ: Khách mua ít (< ngưỡng buôn)",
                    "Giá buôn: Khách mua >= ngưỡng (VD: >=10 thùng)",
                    "Giá VIP: Khách thân thiết (được set thủ công)"
                ],
                "formula": "Tổng tiền = Số lượng × Giá (theo loại) - Giảm giá"
            },
            
            "workflow": {
                "description": "Quy trình nghiệp vụ",
                "steps": [
                    "1. Kiểm kê kho: Tab 'Nhận hàng' → Nhập số lượng đếm → Xác nhận",
                    "2. Bán hàng: Tab 'Bán hàng' → Chọn SP → Nhập SL → Chọn giá → Thanh toán",
                    "3. Đóng ca: Tab 'Báo cáo' → 'Tổng kết ca' → Xuất báo cáo"
                ]
            },
            
            "permissions": {
                "description": "Quyền hạn user",
                "roles": {
                    "admin": "Toàn quyền (quản lý sản phẩm, user, báo cáo)",
                    "accountant": "Xem báo cáo, xuất bỏ, công đoàn",
                    "staff": "Chỉ bán hàng"
                }
            },
            
            "calculations": {
                "description": "Các công thức tính toán",
                "formulas": {
                    "tong_tien_hoa_don": "SUM(so_luong × gia) - giam_gia + phat_sinh",
                    "ton_kho": "ton_dau_ky + nhap - xuat",
                    "loi_nhuan": "doanh_thu - (gia_nhap × so_luong_ban)",
                    "chenh_lech": "ton_thuc_te - ton_he_thong"
                }
            }
        }
    
    def execute_action(self, action_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Thực hiện action (WHITE LIST + PERMISSION CHECK)
        
        Returns:
            {
                "success": bool,
                "message": str,
                "data": Any (optional)
            }
        """
        # Step 1: Check if action is allowed (WHITE LIST)
        if action_name not in self.available_actions:
            return {
                "success": False,
                "message": f"❌ Action '{action_name}' không được phép. Chỉ cho phép: {list(self.available_actions.keys())}"
            }
        
        # Step 2: Check PERMISSION based on current user role
        permission_check = self._check_permission(action_name, params)
        if not permission_check["allowed"]:
            return {
                "success": False,
                "message": f"🚫 {permission_check['message']}"
            }
        
        # Step 3: Log action
        self.action_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action_name,
            "params": params,
            "user_role": self.current_user_role
        })
        
        # Step 4: Execute action (delegate to main_window)
        try:
            if action_name == "navigate_to_tab":
                return self._navigate_to_tab(params.get("tab_name"))
            
            elif action_name == "add_product":
                return self._add_product(params)
            
            elif action_name == "create_invoice":
                return self._create_invoice(params)
            
            elif action_name == "get_product_info":
                return self._get_product_info(params.get("ten_san_pham"))
            
            elif action_name == "get_inventory":
                return self._get_inventory()
            
            elif action_name == "export_report":
                return self._export_report(params)
            
            elif action_name == "calculate_price":
                return self._calculate_price(params)
            
            elif action_name == "calculate_profit":
                return self._calculate_profit(params)
            
            else:
                return {
                    "success": False,
                    "message": f"Action '{action_name}' chưa được implement"
                }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Lỗi khi thực hiện action: {str(e)}"
            }
    
    def _check_permission(self, action_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kiểm tra quyền hạn của user hiện tại
        
        Returns:
            {
                "allowed": bool,
                "message": str (if not allowed)
            }
        """
        # Get permissions for current role
        role_perms = self.role_permissions.get(self.current_user_role, {})
        allowed_actions = role_perms.get("actions", [])
        allowed_tabs = role_perms.get("tabs", [])
        
        # Check 1: Action allowed for this role?
        if action_name not in allowed_actions:
            return {
                "allowed": False,
                "message": f"Quyền '{self.current_user_role}' KHÔNG được phép thực hiện action '{action_name}'. Chỉ Admin mới làm được!"
            }
        
        # Check 2: Tab navigation - check if tab allowed
        if action_name == "navigate_to_tab":
            tab_name = params.get("tab_name", "")
            if tab_name not in allowed_tabs:
                return {
                    "allowed": False,
                    "message": f"Quyền '{self.current_user_role}' KHÔNG được phép truy cập tab '{tab_name}'.\n\n" +
                              f"Bạn chỉ có thể vào: {', '.join(allowed_tabs)}"
                }
        
        # Check 3: Report export - only admin & accountant
        if action_name == "export_report":
            if self.current_user_role not in ["admin", "accountant"]:
                return {
                    "allowed": False,
                    "message": f"Quyền '{self.current_user_role}' KHÔNG được phép xuất báo cáo. Chỉ Admin hoặc Kế toán mới làm được!"
                }
        
        # Check 4: Add/Edit/Delete product - only admin
        if action_name in ["add_product", "edit_product", "delete_product"]:
            if self.current_user_role != "admin":
                return {
                    "allowed": False,
                    "message": f"Quyền '{self.current_user_role}' KHÔNG được phép quản lý sản phẩm. Chỉ Admin mới làm được!"
                }
        
        # Check 5: View inventory - staff cannot see full inventory
        if action_name == "get_inventory":
            if self.current_user_role == "staff":
                return {
                    "allowed": False,
                    "message": f"Quyền Staff KHÔNG được phép xem tồn kho toàn bộ. Chỉ có thể xem thông tin từng sản phẩm khi bán hàng."
                }
        
        # All checks passed
        return {"allowed": True}
    
    def _navigate_to_tab(self, tab_name: str) -> Dict[str, Any]:
        """Chuyển đến tab"""
        if not self.main_window:
            return {"success": False, "message": "Không có main_window"}
        
        # Call main_window's navigate method (không truy cập code)
        if hasattr(self.main_window, 'navigate_to_tab'):
            success, msg = self.main_window.navigate_to_tab(tab_name)
            return {"success": success, "message": msg}
        
        return {"success": False, "message": "Navigate method không tồn tại"}
    
    def _add_product(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Thêm sản phẩm (call main_window method)"""
        if not self.main_window:
            return {"success": False, "message": "Không có main_window"}
        
        # Validate params
        required = ["ten", "don_vi", "gia_le", "gia_buon"]
        for field in required:
            if field not in params:
                return {"success": False, "message": f"Thiếu field '{field}'"}
        
        # Call main_window's add_product method
        if hasattr(self.main_window, 'add_product'):
            result = self.main_window.add_product(
                ten=params["ten"],
                don_vi=params["don_vi"],
                gia_le=params["gia_le"],
                gia_buon=params["gia_buon"],
                gia_vip=params.get("gia_vip", params["gia_buon"])
            )
            return {"success": True, "message": "✅ Đã thêm sản phẩm", "data": result}
        
        return {"success": False, "message": "add_product method không tồn tại"}
    
    def _create_invoice(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo hóa đơn"""
        # Similar implementation
        return {"success": False, "message": "Chức năng đang phát triển"}
    
    def _get_product_info(self, ten_san_pham: str) -> Dict[str, Any]:
        """Lấy thông tin sản phẩm từ DB"""
        import sqlite3
        try:
            conn = sqlite3.connect('fapp.db')
            c = conn.cursor()
            
            sql = "SELECT ten, don_vi, ton_kho, gia_le, gia_buon, gia_vip FROM SanPham WHERE ten LIKE ?"
            rows = c.execute(sql, (f"%{ten_san_pham}%",)).fetchall()
            conn.close()
            
            if rows:
                product = rows[0]
                return {
                    "success": True,
                    "message": "✅ Tìm thấy sản phẩm",
                    "data": {
                        "ten": product[0],
                        "don_vi": product[1],
                        "ton_kho": product[2],
                        "gia_le": product[3],
                        "gia_buon": product[4],
                        "gia_vip": product[5]
                    }
                }
            else:
                return {"success": False, "message": "❌ Không tìm thấy sản phẩm"}
        
        except Exception as e:
            return {"success": False, "message": f"Lỗi DB: {str(e)}"}
    
    def _get_inventory(self) -> Dict[str, Any]:
        """Xem tồn kho"""
        import sqlite3
        try:
            conn = sqlite3.connect('fapp.db')
            c = conn.cursor()
            
            sql = "SELECT ten, ton_kho, don_vi FROM SanPham ORDER BY ten"
            rows = c.execute(sql).fetchall()
            conn.close()
            
            inventory = [{"ten": r[0], "ton_kho": r[1], "don_vi": r[2]} for r in rows]
            
            return {
                "success": True,
                "message": "✅ Đã lấy tồn kho",
                "data": inventory
            }
        
        except Exception as e:
            return {"success": False, "message": f"Lỗi DB: {str(e)}"}
    
    def _export_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Xuất báo cáo"""
        return {"success": False, "message": "Chức năng đang phát triển"}
    
    def _calculate_price(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tính giá bán - CÓ THỂ GIẢI THÍCH CÔNG THỨC
        AI có thể đọc business_rules để hiểu cách tính
        """
        so_luong = params.get("so_luong", 0)
        loai_gia = params.get("loai_gia", "le")
        ten_san_pham = params.get("ten_san_pham")
        
        # Get product info
        product_info = self._get_product_info(ten_san_pham)
        if not product_info["success"]:
            return product_info
        
        product = product_info["data"]
        
        # Determine price
        if loai_gia == "le":
            gia = product["gia_le"]
        elif loai_gia == "buon":
            gia = product["gia_buon"]
        elif loai_gia == "vip":
            gia = product["gia_vip"]
        else:
            return {"success": False, "message": "Loại giá không hợp lệ"}
        
        tong_tien = so_luong * gia
        
        return {
            "success": True,
            "message": "✅ Đã tính giá",
            "data": {
                "san_pham": product["ten"],
                "so_luong": so_luong,
                "loai_gia": loai_gia,
                "don_gia": gia,
                "tong_tien": tong_tien
            },
            "explanation": f"Công thức: {so_luong} × {gia:,.0f} = {tong_tien:,.0f} VNĐ"
        }
    
    def _calculate_profit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Tính lợi nhuận - CÓ THỂ GIẢI THÍCH CÁCH TÍNH"""
        return {"success": False, "message": "Chức năng đang phát triển"}
    
    def get_available_actions(self) -> List[str]:
        """Trả về danh sách actions AI có thể dùng"""
        return list(self.available_actions.keys())
    
    def get_action_help(self, action_name: str) -> Optional[Dict[str, Any]]:
        """Trả về hướng dẫn sử dụng action"""
        return self.available_actions.get(action_name)
    
    def get_business_rules(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Trả về quy tắc nghiệp vụ (AI có thể đọc để hiểu logic)
        KHÔNG trả về code implementation!
        """
        if category:
            return self.business_rules.get(category, {})
        return self.business_rules
    
    def explain_calculation(self, calc_type: str) -> str:
        """Giải thích cách tính (dựa vào business_rules, KHÔNG xem code)"""
        calcs = self.business_rules.get("calculations", {}).get("formulas", {})
        
        if calc_type in calcs:
            formula = calcs[calc_type]
            return f"📊 Công thức tính {calc_type}:\n{formula}"
        
        return f"Không tìm thấy công thức cho '{calc_type}'"
    
    def get_action_log(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Xem lịch sử actions (để audit)"""
        return self.action_log[-limit:]
    
    def is_action_safe(self, action_name: str) -> bool:
        """
        Check xem action có an toàn không
        Ngăn chặn các actions nguy hiểm như:
        - Truy cập file system
        - Chạy arbitrary code
        - Sửa đổi DB trực tiếp (chỉ cho phép qua methods đã định nghĩa)
        """
        dangerous_keywords = [
            "exec", "eval", "open", "write", "delete", "drop",
            "__import__", "compile", "os.", "sys.", "subprocess"
        ]
        
        action_lower = action_name.lower()
        for keyword in dangerous_keywords:
            if keyword in action_lower:
                return False
        
        return True
    
    def set_current_user_role(self, role: str):
        """
        Cập nhật quyền user hiện tại (gọi khi user login/logout)
        
        Args:
            role: "admin", "accountant", hoặc "staff"
        """
        if role not in self.role_permissions:
            raise ValueError(f"Invalid role: {role}. Must be: admin, accountant, or staff")
        
        self.current_user_role = role
        print(f"✅ AI Actions: Đã cập nhật quyền user → '{role}'")
    
    def get_current_user_role(self) -> str:
        """Trả về quyền user hiện tại"""
        return self.current_user_role
    
    def get_allowed_tabs_for_role(self, role: Optional[str] = None) -> List[str]:
        """Trả về danh sách tabs user được phép truy cập"""
        role = role or self.current_user_role
        return self.role_permissions.get(role, {}).get("tabs", [])
    
    def get_allowed_actions_for_role(self, role: Optional[str] = None) -> List[str]:
        """Trả về danh sách actions user được phép thực hiện"""
        role = role or self.current_user_role
        return self.role_permissions.get(role, {}).get("actions", [])
    
    def can_access_tab(self, tab_name: str, role: Optional[str] = None) -> bool:
        """Kiểm tra xem user có thể truy cập tab không"""
        role = role or self.current_user_role
        allowed_tabs = self.get_allowed_tabs_for_role(role)
        return tab_name in allowed_tabs


# Example usage
if __name__ == "__main__":
    action_system = AIActionSystem()
    
    # AI asks: "Sản phẩm PLC KOMAT 2T còn bao nhiêu?"
    result = action_system.execute_action("get_product_info", {
        "ten_san_pham": "PLC KOMAT 2T"
    })
    print(result)
    
    # AI asks: "Tính giá cho 10 thùng PLC KOMAT 2T giá buôn"
    result = action_system.execute_action("calculate_price", {
        "ten_san_pham": "PLC KOMAT 2T",
        "so_luong": 10,
        "loai_gia": "buon"
    })
    print(result)
    
    # AI asks: "Giải thích cách tính tổng tiền hóa đơn"
    explanation = action_system.explain_calculation("tong_tien_hoa_don")
    print(explanation)
