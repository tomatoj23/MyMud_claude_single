"""NPC系统.

包含：
- NPC: NPC类型类
- NPCBehaviorTree: 行为树AI
- NPCRelationship: 好感度系统
- DialogueSystem: 对话系统
"""

from .core import NPCType, NPC
from .behavior_tree import (
    NodeStatus,
    BehaviorNode,
    SelectorNode,
    SequenceNode,
    ActionNode,
    ConditionNode,
    InverterNode,
    NPCBehaviorTree,
)
from .reputation import NPCRelationship
from .dialogue import Response, DialogueNode, DialogueSystem

__all__ = [
    "NPCType",
    "NPC",
    "NodeStatus",
    "BehaviorNode",
    "SelectorNode",
    "SequenceNode",
    "ActionNode",
    "ConditionNode",
    "InverterNode",
    "NPCBehaviorTree",
    "NPCRelationship",
    "Response",
    "DialogueNode",
    "DialogueSystem",
]
