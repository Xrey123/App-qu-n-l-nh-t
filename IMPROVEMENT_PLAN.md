# 🔐 KẾ HOẠCH CẢI TIẾN BẢO MẬT APP

## 📋 PHÂN TÍCH HIỆN TRẠNG

### ✅ Tốt:

- [x] User tự nhập Groq API key
- [x] Hybrid system (online + offline)
- [x] Fallback mechanism
- [x] UI để thay đổi key

### ⚠️ Cần cải tiến:

- [ ] API key lưu plaintext (ai/config.json)
- [ ] Không có license system
- [ ] Code chưa obfuscate
- [ ] Không có anti-debug protection

---

## 🎯 GIẢI PHÁP 3 LỚP BẢO VỆ

### **LỚP 1: ENCRYPT API KEY (Quan trọng!)**

**Vấn đề:** API key của user lưu dạng plaintext

```json
// ai/config.json
{ "groq_api_key": "YOUR_API_KEY_HERE" }
```

**Giải pháp:** Encrypt key bằng HWID-based encryption

```python
# File: utils/secure_config.py (MỚI)

from cryptography.fernet import Fernet
import json
import hashlib
import base64
import os

def get_encryption_key():
    """Tạo key mã hóa từ HWID"""
    from utils.hwid import get_hardware_id
    hwid = get_hardware_id()
    key_material = hashlib.sha256(f"{hwid}|SHOPFLOW".encode()).digest()
    return base64.urlsafe_b64encode(key_material)

def save_encrypted_config(api_key):
    """Lưu API key đã mã hóa"""
    fernet = Fernet(get_encryption_key())
    encrypted = fernet.encrypt(api_key.encode())

    config = {
        "api_key_encrypted": encrypted.decode(),
        "ollama_url": "http://localhost:11434",
        "offline_model": "phi3:mini"
    }

    with open("ai/config.json", "w") as f:
        json.dump(config, f, indent=2)

def load_encrypted_config():
    """Đọc và decrypt API key"""
    try:
        with open("ai/config.json", "r") as f:
            config = json.load(f)

        encrypted = config["api_key_encrypted"].encode()
        fernet = Fernet(get_encryption_key())
        api_key = fernet.decrypt(encrypted).decode()

        return api_key
    except:
        return None
```

**Cách tích hợp:**

```python
# File: ai_system/hybrid.py (SỬA)

# Line 41: Thay đổi cách load key
# TỪ:
self.groq_api_key = self.config.get("groq_api_key", "")

# THÀNH:
from utils.secure_config import load_encrypted_config
self.groq_api_key = load_encrypted_config() or ""

# Line 89: Thay đổi cách save key
# TỪ:
self.config["groq_api_key"] = api_key
self._save_config()

# THÀNH:
from utils.secure_config import save_encrypted_config
save_encrypted_config(api_key)
```

**Kết quả:**

```json
// ai/config.json (SAU KHI ENCRYPT)
{
  "api_key_encrypted": "gAAAAABl3x2...", // ✅ Encrypted!
  "ollama_url": "http://localhost:11434",
  "offline_model": "phi3:mini"
}
```

---

### **LỚP 2: LICENSE SYSTEM (Bắt buộc!)**

**Vấn đề:** Không có license → Ai cũng dùng free

**Giải pháp:** HWID-based license

```python
# File: utils/hwid.py (MỚI)

import hashlib
import platform
import subprocess
import uuid

def get_hardware_id():
    """Lấy HWID của máy"""
    components = []

    # CPU
    try:
        cpu = subprocess.check_output("wmic cpu get processorid", shell=True)
        components.append(cpu.decode().strip())
    except:
        pass

    # Motherboard
    try:
        mb = subprocess.check_output("wmic baseboard get serialnumber", shell=True)
        components.append(mb.decode().strip())
    except:
        pass

    # MAC
    components.append(str(uuid.getnode()))

    # Disk
    try:
        disk = subprocess.check_output("wmic diskdrive get serialnumber", shell=True)
        components.append(disk.decode().strip())
    except:
        pass

    hwid = hashlib.sha256("|".join(components).encode()).hexdigest()
    return hwid
```

```python
# File: utils/license.py (MỚI)

from cryptography.fernet import Fernet
import json
from datetime import datetime
import os
import sys

class LicenseValidator:
    """Validate license"""

    # ⚠️ Key này sẽ được obfuscate
    SECRET_KEY = b'YOUR_32_BYTE_KEY_HERE_CHANGE_IT_'

    @staticmethod
    def validate():
        """Kiểm tra license"""

        # 1. Check file license.key
        if not os.path.exists("license.key"):
            return False, "Không tìm thấy license key", None

        # 2. Decrypt license
        try:
            fernet = Fernet(LicenseValidator.SECRET_KEY)

            with open("license.key", "rb") as f:
                encrypted = f.read()

            decrypted = fernet.decrypt(encrypted)
            license_data = json.loads(decrypted.decode())

        except:
            return False, "License không hợp lệ", None

        # 3. Check HWID
        from utils.hwid import get_hardware_id
        current_hwid = get_hardware_id()

        if license_data["hwid"] != current_hwid:
            return False, "License không khớp với máy này", None

        # 4. Check expiry
        expire = datetime.fromisoformat(license_data["expire"])
        if datetime.now() > expire:
            return False, f"License đã hết hạn ({expire.strftime('%d/%m/%Y')})", None

        # ✅ Valid
        return True, None, license_data
```

**Tích hợp vào main_gui.py:**

```python
# File: main_gui.py (THÊM VÀO ĐẦU __init__)

class MainWindow(QMainWindow):
    def __init__(self, user_id, login_window=None):

        # ✅ KIỂM TRA LICENSE TRƯỚC KHI CHẠY
        from utils.license import LicenseValidator

        valid, error, license_info = LicenseValidator.validate()

        if not valid:
            QMessageBox.critical(
                None,
                "🔒 License Error",
                f"{error}\n\nVui lòng liên hệ để kích hoạt app."
            )
            sys.exit(1)

        self.license_info = license_info

        # ... existing code ...
```

---

### **LỚP 3: CODE OBFUSCATION (Rất quan trọng!)**

**Vấn đề:** Code Python đọc được → Cracker dễ patch

**Giải pháp:** PyArmor obfuscation

```bash
# Cài PyArmor
pip install pyarmor

# Obfuscate app
pyarmor gen --enable-jit --mix-str --assert-call --output dist main_gui.py
pyarmor gen --enable-jit --mix-str --output dist/ai_system ai_system/
pyarmor gen --enable-jit --mix-str --output dist/utils utils/

# Build EXE
cd dist
pyinstaller --onefile --windowed --name ShopFlow main_gui.py
```

**Kết quả:** Code biến thành bytecode mã hóa → AI không đọc được!

---

## 📊 ROADMAP IMPLEMENTATION

### **GIAI ĐOẠN 1: CƠ BẢN (2-3 giờ)**

- [ ] Tạo utils/hwid.py
- [ ] Tạo utils/secure_config.py
- [ ] Sửa ai_system/hybrid.py (encrypt key)
- [ ] Test encrypt/decrypt API key

### **GIAI ĐOẠN 2: LICENSE (1 ngày)**

- [ ] Tạo utils/license.py
- [ ] Tạo tool generate license (trên máy bạn)
- [ ] Tích hợp vào main_gui.py
- [ ] Test với license giả

### **GIAI ĐOẠN 3: OBFUSCATE (30 phút)**

- [ ] Cài PyArmor
- [ ] Obfuscate code
- [ ] Build EXE
- [ ] Test EXE

### **GIAI ĐOẠN 4: DEPLOY (1-2 giờ)**

- [ ] Tạo installer (Inno Setup)
- [ ] Test trên máy sạch
- [ ] Document hướng dẫn cho khách

---

## 🎯 KẾT QUẢ MONG ĐỢI

### **Trước:**

```
❌ API key plaintext → Cracker lấy được
❌ Không license → Ai cũng dùng free
❌ Code .py → Đọc được logic
❌ Dễ crack trong 2-3 giờ
```

### **Sau:**

```
✅ API key encrypted → Chỉ máy đó đọc được
✅ License HWID → Chỉ 1 máy dùng được
✅ Code obfuscated → AI không đọc được
✅ Khó crack 40-70 giờ → Không đáng công
```

---

## 💰 CHI PHÍ & THỜI GIAN

| Công việc       | Thời gian  | Chi phí |
| --------------- | ---------- | ------- |
| Encrypt API key | 2 giờ      | $0      |
| License system  | 8 giờ      | $0      |
| Obfuscation     | 1 giờ      | $0      |
| Test & Deploy   | 3 giờ      | $0      |
| **TỔNG**        | **14 giờ** | **$0**  |

**Độ bảo mật:** ⭐⭐⭐⭐ (85-90%)

---

## ✅ CHECKLIST CUỐI CÙNG

- [ ] API key của user được encrypt
- [ ] License check khi khởi động
- [ ] Code obfuscate với PyArmor
- [ ] Test trên máy sạch
- [ ] Document cho khách hàng
- [ ] Tool generate license (cho bạn)
- [ ] Backup code gốc (trước obfuscate)

---

**Cập nhật:** 09/11/2025  
**Status:** Ready to implement
