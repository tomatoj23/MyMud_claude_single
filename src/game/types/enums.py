"""游戏系统枚举定义.

将魔法字符串替换为类型安全的枚举.
"""

from enum import Enum, auto


class MoveType(str, Enum):
    """招式类型."""
    ATTACK = "attack"
    DEFEND = "defend"
    CAST = "cast"
    USE_ITEM = "item"
    FLEE = "flee"
    SPECIAL = "special"


class BuffType(str, Enum):
    """BUFF/DEBUFF类型."""
    POISON = "poison"
    STUN = "stun"
    SILENCE = "silence"
    BUFF = "buff"
    DEBUFF = "debuff"
    HEAL_OVER_TIME = "hot"
    DAMAGE_OVER_TIME = "dot"


class DamageType(str, Enum):
    """伤害类型."""
    PHYSICAL = "physical"
    INTERNAL = "internal"  # 内功伤害
    POISON = "poison"
    FIRE = "fire"
    COLD = "cold"
    LIGHTNING = "lightning"


class NPCState(str, Enum):
    """NPC状态."""
    IDLE = "idle"
    PATROL = "patrol"
    COMBAT = "combat"
    DEAD = "dead"
    FLEE = "flee"


class QuestStatus(str, Enum):
    """任务状态."""
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    TURNED_IN = "turned_in"
