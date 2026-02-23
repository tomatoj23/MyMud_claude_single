"""世界动态加载管理器.

负责：
- 按需加载区域
- 根据玩家位置预加载相邻区域
- 卸载长时间未访问的区域
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ...engine.objects.manager import ObjectManager
    from ..typeclasses.room import Room


@dataclass
class Area:
    """区域定义.

    Attributes:
        key: 唯一标识
        name: 显示名
        description: 区域描述
        rooms: 房间ID列表
        load_range: 预加载范围
        unload_delay: 卸载延迟（秒）
    """

    key: str
    name: str
    description: str = ""
    rooms: list[int] = field(default_factory=list)
    load_range: int = 3  # 预加载范围
    unload_delay: int = 60  # 卸载延迟（秒）


class WorldLoader:
    """世界动态加载管理器."""

    def __init__(self, object_manager: ObjectManager):
        """初始化世界加载器.

        Args:
            object_manager: 对象管理器
        """
        self.obj_mgr = object_manager
        self._loaded_areas: dict[str, Area] = {}
        self._active_rooms: dict[int, float] = {}  # room_id -> last_access_time
        self._unload_task: Optional[asyncio.Task] = None
        self._running = False

    async def initialize(self) -> None:
        """初始化世界加载器."""
        if self._running:
            return
        self._running = True
        # 启动后台卸载任务
        self._unload_task = asyncio.create_task(self._unload_loop())

    async def shutdown(self) -> None:
        """关闭世界加载器."""
        self._running = False
        if self._unload_task:
            self._unload_task.cancel()
            try:
                await self._unload_task
            except asyncio.CancelledError:
                pass

    async def on_player_move(self, from_room: Room, to_room: Room) -> None:
        """玩家移动时触发加载/卸载.

        Args:
            from_room: 起始房间
            to_room: 目标房间
        """
        # 更新活跃时间
        now = time.time()
        self._active_rooms[to_room.id] = now

        # 加载新区域
        await self._load_area(to_room.area)

        # 预加载相邻区域
        await self._preload_adjacent_areas(to_room)

    async def _load_area(self, area_key: str) -> None:
        """加载区域.

        Args:
            area_key: 区域key
        """
        if area_key in self._loaded_areas:
            return

        # 从文件加载区域数据
        area_data = self._load_area_from_file(area_key)
        if not area_data:
            # 创建一个空区域
            area = Area(key=area_key, name=area_key)
        else:
            area = Area(**area_data)

        self._loaded_areas[area_key] = area

    def _load_area_from_file(self, area_key: str) -> Optional[dict]:
        """从文件加载区域数据.

        Args:
            area_key: 区域key

        Returns:
            区域数据字典
        """
        file_path = Path(f"resources/world/{area_key}.yaml")
        if not file_path.exists():
            return None

        try:
            import yaml

            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data.get("area") if data else None
        except Exception:
            return None

    async def _preload_adjacent_areas(self, room: Room) -> None:
        """预加载相邻区域.

        Args:
            room: 当前房间
        """
        # 获取相邻房间的区域
        for _direction, neighbor in room.get_neighbor_rooms():
            if neighbor.area != room.area:
                await self._load_area(neighbor.area)

    async def _unload_loop(self) -> None:
        """后台卸载循环."""
        while self._running:
            await asyncio.sleep(60)  # 每分钟检查一次
            await self._check_and_unload()

    async def _check_and_unload(self) -> None:
        """检查并卸载不活跃区域."""
        now = time.time()

        # 找出长时间未访问的房间
        to_unload = []
        for room_id, last_access in list(self._active_rooms.items()):
            if now - last_access > 300:  # 5分钟未访问
                to_unload.append(room_id)

        # 卸载房间
        for room_id in to_unload:
            del self._active_rooms[room_id]

    def get_active_rooms(self) -> list[int]:
        """获取当前活跃房间."""
        return list(self._active_rooms.keys())

    def is_room_active(self, room_id: int) -> bool:
        """检查房间是否活跃."""
        return room_id in self._active_rooms

    def get_loaded_areas(self) -> list[str]:
        """获取已加载的区域列表."""
        return list(self._loaded_areas.keys())

    def get_area(self, area_key: str) -> Optional[Area]:
        """获取区域信息.

        Args:
            area_key: 区域key

        Returns:
            区域对象
        """
        return self._loaded_areas.get(area_key)

    async def mark_room_active(self, room_id: int) -> None:
        """标记房间为活跃.

        Args:
            room_id: 房间ID
        """
        self._active_rooms[room_id] = time.time()
