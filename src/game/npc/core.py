"""NPC核心类型."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game.combat.core import CombatSession

from src.game.typeclasses.character import Character


class NPCType(Enum):
    """NPC类型."""

    NORMAL = "normal"  # 普通
    MERCHANT = "merchant"  # 商人
    TRAINER = "trainer"  # 训练师
    QUEST = "quest"  # 任务NPC
    BOSS = "boss"  # Boss
    ENEMY = "enemy"  # 敌人


class NPC(Character):
    """NPC类型.

    扩展Character，添加AI和行为树支持。
    """

    typeclass_path = "src.game.npc.core.NPC"

    @property
    def npc_type(self) -> NPCType:
        """NPC类型."""
        return NPCType(self.db.get("npc_type", "normal"))

    @npc_type.setter
    def npc_type(self, value: NPCType) -> None:
        self.db.set("npc_type", value.value)

    @property
    def ai_enabled(self) -> bool:
        """是否启用AI."""
        return self.db.get("ai_enabled", True)

    @ai_enabled.setter
    def ai_enabled(self, value: bool) -> None:
        self.db.set("ai_enabled", value)

    @property
    def schedule(self) -> list[dict]:
        """日常行程安排.

        Returns:
            [{"time": "08:00", "location": "room_key", "action": "action_name"}]
        """
        return self.db.get("schedule", [])

    @schedule.setter
    def schedule(self, value: list[dict]) -> None:
        self.db.set("schedule", value)

    @property
    def home_location(self) -> str | None:
        """出生点/回家位置."""
        return self.db.get("home_location")

    @home_location.setter
    def home_location(self, value: str | None) -> None:
        self.db.set("home_location", value)

    @property
    def is_hostile(self) -> bool:
        """是否为敌对NPC."""
        return self.db.get("is_hostile", False)

    @is_hostile.setter
    def is_hostile(self, value: bool) -> None:
        self.db.set("is_hostile", value)

    @property
    def dialogue_key(self) -> str | None:
        """对话配置key."""
        return self.db.get("dialogue_key")

    @dialogue_key.setter
    def dialogue_key(self, value: str | None) -> None:
        self.db.set("dialogue_key", value)

    # ===== AI相关 =====

    async def update_ai(self, delta_time: float) -> None:
        """AI更新.

        Args:
            delta_time: 经过的时间（秒）
        """
        if not self.ai_enabled:
            return

        # 执行行为树
        if self.behavior_tree:
            from .behavior_tree import NPCBehaviorTree
            await self.behavior_tree.tick(self, {})

    def set_behavior_tree(self, behavior_tree) -> None:
        """设置行为树."""
        self._behavior_tree = behavior_tree
        
    @property
    def behavior_tree(self):
        """获取行为树."""
        return getattr(self, '_behavior_tree', None)

    # ===== 战斗相关 =====

    def at_combat_start(self, combat: CombatSession) -> None:
        """战斗开始."""
        super().at_combat_start(combat) if hasattr(super(), "at_combat_start") else None
        # NPC进入战斗模式时禁用日常AI
        self.ai_enabled = False

    def at_combat_end(self, combat: CombatSession) -> None:
        """战斗结束."""
        super().at_combat_end(combat) if hasattr(super(), "at_combat_end") else None
        # 恢复日常AI
        self.ai_enabled = True

    # ===== 便捷方法 =====

    @property
    def is_merchant(self) -> bool:
        """是否为商人."""
        return self.npc_type == NPCType.MERCHANT

    @property
    def is_trainer(self) -> bool:
        """是否为训练师."""
        return self.npc_type == NPCType.TRAINER

    @property
    def is_quest_giver(self) -> bool:
        """是否为任务NPC."""
        return self.npc_type == NPCType.QUEST

    def can_trade(self) -> bool:
        """是否可以交易."""
        return self.npc_type == NPCType.MERCHANT

    def can_train(self) -> bool:
        """是否可以传授武功."""
        return self.npc_type == NPCType.TRAINER

    def get_dialogue_key(self) -> str:
        """获取对话key（默认使用NPC的key）."""
        return self.dialogue_key or self.key

    # ===== 工厂方法 =====

    @classmethod
    def create_merchant(cls, key: str, name: str, shop_items: list | None = None) -> "NPC":
        """创建商人NPC."""
        npc = cls()
        npc.key = key
        npc.name = name
        npc.npc_type = NPCType.MERCHANT
        npc.db.set("shop_items", shop_items or [])
        return npc

    @classmethod
    def create_trainer(cls, key: str, name: str, teachable_wuxue: list | None = None) -> "NPC":
        """创建训练师NPC."""
        npc = cls()
        npc.key = key
        npc.name = name
        npc.npc_type = NPCType.TRAINER
        npc.db.set("teachable_wuxue", teachable_wuxue or [])
        return npc

    @classmethod
    def create_enemy(cls, key: str, name: str, level: int = 1) -> "NPC":
        """创建敌人NPC."""
        npc = cls()
        npc.key = key
        npc.name = name
        npc.npc_type = NPCType.ENEMY
        npc.is_hostile = True
        npc.level = level
        return npc


# 在Character上添加NPC关系管理属性

def _get_npc_relations(self):
    """获取NPC关系管理器（延迟初始化）."""
    if not hasattr(self, "_npc_relations"):
        from .reputation import NPCRelationship

        self._npc_relations = NPCRelationship(self)
    return self._npc_relations


# 将方法添加到Character类
Character.npc_relations = property(_get_npc_relations)
