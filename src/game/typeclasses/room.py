"""地图系统 - 房间和出口.

提供房间（Room）、出口（Exit）定义，支持三维坐标.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.engine.core.typeclass import TypeclassBase

if TYPE_CHECKING:
    from .character import Character


# 方向常量
DIRECTIONS = {
    "n": (0, 1, 0),
    "ne": (1, 1, 0),
    "e": (1, 0, 0),
    "se": (1, -1, 0),
    "s": (0, -1, 0),
    "sw": (-1, -1, 0),
    "w": (-1, 0, 0),
    "nw": (-1, 1, 0),
    "up": (0, 0, 1),
    "down": (0, 0, -1),
}

DIRECTION_NAMES = {
    "n": "北",
    "ne": "东北",
    "e": "东",
    "se": "东南",
    "s": "南",
    "sw": "西南",
    "w": "西",
    "nw": "西北",
    "up": "上",
    "down": "下",
}

DIRECTION_OPPOSITES = {
    "n": "s",
    "ne": "sw",
    "e": "w",
    "se": "nw",
    "s": "n",
    "sw": "ne",
    "w": "e",
    "nw": "se",
    "up": "down",
    "down": "up",
}


class Room(TypeclassBase):
    """房间类型.

    属性：
    - coords: 三维坐标 (x, y, z)
    - area: 所属区域
    - description: 房间描述
    - environment: 环境属性（光照、天气等）

    Attributes:
        typeclass_path: 类型路径
    """

    typeclass_path = "src.game.typeclasses.room.Room"

    @property
    def coords(self) -> tuple[int, int, int]:
        """三维坐标 (x, y, z)."""
        return self.db.get("coords", (0, 0, 0))

    @coords.setter
    def coords(self, value: tuple[int, int, int]) -> None:
        self.db.set("coords", value)

    @property
    def area(self) -> str:
        """所属区域."""
        return self.db.get("area", "未知区域")

    @area.setter
    def area(self, value: str) -> None:
        self.db.set("area", value)

    @property
    def description(self) -> str:
        """房间描述."""
        return self.db.get("description", "这里什么也没有。")

    @description.setter
    def description(self, value: str) -> None:
        self.db.set("description", value)

    @property
    def environment(self) -> dict:
        """环境属性（光照、天气等）."""
        return self.db.get(
            "environment",
            {
                "light": 100,  # 光照度 0-100
                "weather": "clear",  # 天气
                "terrain": "normal",  # 地形
            },
        )

    @environment.setter
    def environment(self, value: dict) -> None:
        self.db.set("environment", value)

    @property
    def name(self) -> str:
        """房间显示名称.

        人类可读的显示名称。如果未设置，则回退到 key。
        存储在 attributes 中，无需数据库迁移。

        Returns:
            显示名称，或 key（如果 name 未设置）
        """
        return self.db.get("name") or self.key

    @name.setter
    def name(self, value: str) -> None:
        """设置房间显示名称."""
        self.db.set("name", value)

    # ===== 出口相关 =====
    def get_exits(self) -> list["Exit"]:
        """获取所有出口."""
        exits: list[Exit] = []
        for obj in self.contents:
            if isinstance(obj, Exit):
                exits.append(obj)
        return exits

    def get_exit(self, direction: str) -> Optional["Exit"]:
        """获取指定方向出口.

        Args:
            direction: 方向（n/ne/e/se/s/sw/w/nw/up/down）

        Returns:
            出口对象，不存在返回None
        """
        for exit_obj in self.get_exits():
            if exit_obj.direction == direction:
                return exit_obj
        return None

    def get_exit_names(self) -> list[str]:
        """获取所有出口方向名称."""
        return [exit_obj.direction_name for exit_obj in self.get_exits()]

    # ===== 内容物相关 =====
    async def get_contents_async(
        self,
        typeclass_filter: type | None = None,
    ) -> list["TypeclassBase"]:
        """异步获取房间内容物（批量加载优化）.

        相比同步访问 self.contents，此方法使用批量查询减少数据库访问。

        Args:
            typeclass_filter: 可选的类型过滤器

        Returns:
            内容物对象列表
        """
        if not hasattr(self, "_manager"):
            return []

        # 批量查询所有 location_id = self.id 的对象
        rows = await self._manager.db.fetchall(
            "SELECT id FROM objects WHERE location_id = ?",
            (self.id,),
        )

        if not rows:
            return []

        obj_ids = [row["id"] for row in rows]
        contents = await self._manager.load_many(obj_ids)

        if typeclass_filter:
            contents = [obj for obj in contents if isinstance(obj, typeclass_filter)]

        return contents

    def get_characters(self) -> list["Character"]:
        """获取房间内的角色（不包括玩家自己）."""
        from .character import Character

        return [obj for obj in self.contents if isinstance(obj, Character)]

    def get_items(self) -> list["Item"]:
        """获取房间内的物品."""
        from .item import Item

        return [obj for obj in self.contents if isinstance(obj, Item)]

    # ===== 描述渲染 =====
    def at_desc(self, looker: Optional["Character"]) -> str:
        """渲染房间描述（可被子类重写）.

        Args:
            looker: 观察者

        Returns:
            描述文本
        """
        desc = f"\n{self.name}\n"
        desc += "=" * 40 + "\n"
        desc += self.description + "\n"

        # 出口
        exits = self.get_exits()
        if exits:
            exit_names = [ex.direction_name for ex in exits]
            desc += f"\n[出口] {' '.join(exit_names)}"

        # 物品
        items = self.get_items()
        if items:
            item_names = [item.name for item in items]
            desc += f"\n[物品] {', '.join(item_names)}"

        # 其他角色
        characters = self.get_characters()
        others = [c for c in characters if c != looker]
        if others:
            char_names = [c.name for c in others]
            desc += f"\n[人物] {', '.join(char_names)}"

        return desc

    # ===== 寻路相关 =====
    def get_neighbor_rooms(self) -> list[tuple[str, "Room"]]:
        """获取相邻房间列表.

        Returns:
            [(方向, 房间), ...]
        """
        neighbors: list[tuple[str, Room]] = []
        for exit_obj in self.get_exits():
            dest = exit_obj.destination
            if dest and isinstance(dest, Room):
                neighbors.append((exit_obj.direction, dest))
        return neighbors


class Exit(TypeclassBase):
    """出口类型.

    Attributes:
        typeclass_path: 类型路径
    """

    typeclass_path = "src.game.typeclasses.room.Exit"

    @property
    def direction(self) -> str:
        """方向（n/ne/e/se/s/sw/w/nw/up/down）."""
        return self.db.get("direction", "n")

    @direction.setter
    def direction(self, value: str) -> None:
        self.db.set("direction", value)

    @property
    def direction_name(self) -> str:
        """方向中文名."""
        return DIRECTION_NAMES.get(self.direction, "未知")

    @property
    def destination_id(self) -> Optional[int]:
        """目标房间ID."""
        return self.db.get("destination_id")

    @destination_id.setter
    def destination_id(self, value: Optional[int]) -> None:
        self.db.set("destination_id", value)

    @property
    def destination(self) -> Optional[Room]:
        """目标房间对象."""
        dest_id = self.destination_id
        if dest_id and hasattr(self, "_manager"):
            obj = self._manager.get(dest_id)
            if isinstance(obj, Room):
                return obj
        return None

    @destination.setter
    def destination(self, room: Optional[Room]) -> None:
        self.destination_id = room.id if room else None

    @property
    def is_hidden(self) -> bool:
        """是否隐藏."""
        return self.db.get("is_hidden", False)

    @is_hidden.setter
    def is_hidden(self, value: bool) -> None:
        self.db.set("is_hidden", value)

    @property
    def lock_str(self) -> str:
        """通行条件（锁字符串）."""
        return self.db.get("lock_str", "")

    @lock_str.setter
    def lock_str(self, value: str) -> None:
        self.db.set("lock_str", value)

    @property
    def name(self) -> str:
        """出口显示名称.

        人类可读的显示名称。如果未设置，则回退到 key。
        存储在 attributes 中，无需数据库迁移。

        Returns:
            显示名称，或 key（如果 name 未设置）
        """
        return self.db.get("name") or self.key

    @name.setter
    def name(self, value: str) -> None:
        """设置出口显示名称."""
        self.db.set("name", value)

    async def can_pass(self, character: "Character") -> tuple[bool, str]:
        """检查是否可以通过.

        Args:
            character: 角色

        Returns:
            (是否可以通过, 原因)
        """
        # 检查锁
        if self.lock_str:
            # TODO: 解析锁字符串，检查条件
            pass

        # 检查目的地
        if not self.destination:
            return False, "出口似乎通向虚无..."

        return True, ""

    def get_desc(self) -> str:
        """获取出口描述."""
        if self.is_hidden:
            return ""

        desc = f"{self.direction_name}"
        if self.destination:
            desc += f" - {self.destination.name}"
        return desc


def get_direction_vector(direction: str) -> tuple[int, int, int]:
    """获取方向的坐标向量.

    Args:
        direction: 方向代码

    Returns:
        (dx, dy, dz)
    """
    return DIRECTIONS.get(direction, (0, 0, 0))


def get_opposite_direction(direction: str) -> str:
    """获取相反方向.

    Args:
        direction: 方向代码

    Returns:
        相反方向代码
    """
    return DIRECTION_OPPOSITES.get(direction, direction)
