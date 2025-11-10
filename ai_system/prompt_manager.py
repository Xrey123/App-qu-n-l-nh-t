"""
Prompt Template Manager - Smart prompt selection
"""

import os
from typing import Dict


class PromptManager:
    """
    Quản lý prompt templates và chọn prompt phù hợp
    """

    def __init__(self):
        self.prompts_dir = "ai/prompts"
        self.prompts = self._load_all_prompts()

    def _load_all_prompts(self) -> Dict[str, str]:
        """Load tất cả prompt templates"""
        prompts = {}
        templates = ["newbie.txt", "expert.txt", "accountant.txt"]

        for template in templates:
            path = os.path.join(self.prompts_dir, template)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    key = template.replace(".txt", "")
                    prompts[key] = f.read()

        return prompts

    def get_prompt(
        self, user_role: str, experience_level: str = "newbie"
    ) -> str:
        """
        Chọn prompt template phù hợp

        Args:
            user_role: "admin" / "accountant" / "staff"
            experience_level: "newbie" / "intermediate" / "expert"

        Returns:
            Prompt string
        """
        # Accountant có prompt riêng
        if user_role.lower() == "accountant":
            return self.prompts.get("accountant", self.prompts.get("newbie", ""))

        # Các role khác chọn theo experience level
        if experience_level == "expert":
            return self.prompts.get("expert", self.prompts.get("newbie", ""))
        else:
            # Newbie và Intermediate đều dùng newbie prompt
            return self.prompts.get("newbie", "")

    def get_all_prompts(self) -> Dict[str, str]:
        """Lấy tất cả prompts (for debugging)"""
        return self.prompts
