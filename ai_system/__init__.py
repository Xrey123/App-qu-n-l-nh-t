"""
AI System - Unified AI Assistant with Permissions
Tích hợp: AI Chat + Actions + Role-Based Permissions + Hybrid Mode (Groq/Offline)
"""

from .hybrid import HybridAI as AIAssistant
from .actions import AIActionSystem
from .permissions import RolePermissions

__all__ = ['AIAssistant', 'AIActionSystem', 'RolePermissions']
