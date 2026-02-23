"""任务系统.

包含：
- Quest: 任务定义
- CharacterQuestMixin: 角色任务管理
- KarmaSystem: 因果点系统
- WorldStateManager: 世界状态管理
"""

from .core import (
    QuestType,
    QuestObjectiveType,
    QuestObjective,
    Quest,
    CharacterQuestMixin,
)
from .karma import KarmaSystem
from .world_state import WorldStateManager

__all__ = [
    "QuestType",
    "QuestObjectiveType",
    "QuestObjective",
    "Quest",
    "CharacterQuestMixin",
    "KarmaSystem",
    "WorldStateManager",
]
