"""物品基类.

所有可携带物品的基础类型.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from src.engine.core.typeclass import TypeclassBase

if TYPE_CHECKING:
    from .character import Character


class ItemType(Enum):
    """物品类型."""

    NORMAL = "normal"  # 普通物品
    EQUIPMENT = "equipment"  # 装备
    CONSUMABLE = "consumable"  # 消耗品
    QUEST = "quest"  # 任务物品
    MATERIAL = "material"  # 材料


class Item(TypeclassBase):
    """物品基类.

    Attributes:
        typeclass_path: 类型路径
    """

    typeclass_path = "src.game.typeclasses.item.Item"

    @property
    def item_type(self) -> ItemType:
        """物品类型."""
        return ItemType.NORMAL

    @property
    def weight(self) -> int:
        """重量."""
        return self.db.get("weight", 1)

    @weight.setter
    def weight(self, value: int) -> None:
        self.db.set("weight", value)

    @property
    def value(self) -> int:
        """价值（铜钱）."""
        return self.db.get("value", 0)

    @value.setter
    def value(self, value: int) -> None:
        self.db.set("value", value)

    @property
    def description(self) -> str:
        """物品描述."""
        return self.db.get("description", "这是一件普通的物品。")

    @description.setter
    def description(self, value: str) -> None:
        self.db.set("description", value)

    @property
    def is_stackable(self) -> bool:
        """是否可堆叠."""
        return self.db.get("is_stackable", False)

    @is_stackable.setter
    def is_stackable(self, value: bool) -> None:
        self.db.set("is_stackable", value)

    @property
    def stack_size(self) -> int:
        """堆叠数量."""
        return self.db.get("stack_size", 1)

    @stack_size.setter
    def stack_size(self, value: int) -> None:
        self.db.set("stack_size", value)

    @property
    def name(self) -> str:
        """物品显示名称.

        人类可读的显示名称。如果未设置，则回退到 key。
        存储在 attributes 中，无需数据库迁移。

        Returns:
            显示名称，或 key（如果 name 未设置）
        """
        return self.db.get("name") or self.key

    @name.setter
    def name(self, value: str) -> None:
        """设置物品显示名称."""
        self.db.set("name", value)

    def can_pickup(self, character: "Character") -> tuple[bool, str]:
        """检查是否可以拾取.

        检查角色是否有足够的负重空间拾取该物品。

        Args:
            character: 角色

        Returns:
            (是否可以, 原因)
        """
        # 检查负重
        return character.can_carry(self)

    def can_use(self, character: "Character") -> tuple[bool, str]:
        """检查是否可以使用.

        Args:
            character: 角色

        Returns:
            (是否可以, 原因)
        """
        return False, "该物品无法使用"

    async def on_use(self, character: "Character") -> bool:
        """使用物品.

        Args:
            character: 使用者

        Returns:
            是否使用成功
        """
        return False

    def get_desc(self) -> str:
        """获取物品描述."""
        desc = f"{self.name}\n"
        desc += f"{self.description}\n"
        if self.value > 0:
            desc += f"价值: {self.value} 铜钱\n"
        if self.weight > 0:
            desc += f"重量: {self.weight}\n"
        return desc
