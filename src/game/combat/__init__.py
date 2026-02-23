"""战斗系统.

即时制战斗核心，包含：
- CombatSession: 战斗会话管理
- CombatCalculator: 伤害计算
- BuffManager: BUFF/DEBUFF管理
- CombatAI: 战斗AI
"""

from .core import CombatSession, CombatAction, CombatResult
from .calculator import CombatCalculator, DamageResult
from .buff import Buff, BuffType, BuffManager
from .ai import CombatAI, SmartAI

__all__ = [
    "CombatSession",
    "CombatAction",
    "CombatResult",
    "CombatCalculator",
    "DamageResult",
    "Buff",
    "BuffType",
    "BuffManager",
    "CombatAI",
    "SmartAI",
]
