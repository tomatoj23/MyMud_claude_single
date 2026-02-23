"""A*寻路算法.

使用三维曼哈顿距离作为启发函数.
"""

from __future__ import annotations

import heapq
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..typeclasses.room import Room


class PathFinder:
    """A*寻路."""

    def __init__(self, object_manager: "ObjectManager"):
        """初始化寻路器.

        Args:
            object_manager: 对象管理器
        """
        self.obj_mgr = object_manager

    async def find_path(
        self, start: Room, goal: Room
    ) -> Optional[list[tuple[str, Room]]]:
        """寻找路径.

        Args:
            start: 起始房间
            goal: 目标房间

        Returns:
            路径列表 [(方向, 房间), ...]，无路径返回None
        """
        # A*算法
        open_set: list[tuple[float, int]] = [(0, start.id)]  # (f_score, room_id)
        came_from: dict[int, tuple[str, int]] = {}  # room_id -> (direction, prev_room_id)

        g_score: dict[int, float] = {start.id: 0}
        f_score: dict[int, float] = {start.id: self._heuristic(start, goal)}

        open_set_hash = {start.id}

        while open_set:
            _, current_id = heapq.heappop(open_set)
            open_set_hash.remove(current_id)

            if current_id == goal.id:
                # 找到路径，重建
                return await self._reconstruct_path(came_from, current_id)

            current_room = self.obj_mgr.get(current_id)
            if not current_room:
                continue

            # 遍历邻居
            for exit_obj in current_room.get_exits():
                if not exit_obj.destination:
                    continue

                neighbor_id = exit_obj.destination_id

                # 计算 tentative_g_score
                tentative_g_score = g_score[current_id] + 1

                if neighbor_id not in g_score or tentative_g_score < g_score.get(
                    neighbor_id, float("inf")
                ):
                    came_from[neighbor_id] = (exit_obj.direction, current_id)
                    g_score[neighbor_id] = tentative_g_score
                    neighbor_room = exit_obj.destination
                    if neighbor_room:
                        f_score[neighbor_id] = tentative_g_score + self._heuristic(
                            neighbor_room, goal
                        )

                        if neighbor_id not in open_set_hash:
                            heapq.heappush(open_set, (f_score[neighbor_id], neighbor_id))
                            open_set_hash.add(neighbor_id)

        # 无路径
        return None

    def _heuristic(self, a: Room, b: Room) -> float:
        """启发函数 - 三维曼哈顿距离.

        Z轴权重更高（上下移动通常更难）
        """
        ax, ay, az = a.coords
        bx, by, bz = b.coords
        return abs(ax - bx) + abs(ay - by) + abs(az - bz) * 2

    async def _reconstruct_path(
        self, came_from: dict, current_id: int
    ) -> list[tuple[str, Room]]:
        """重建路径."""
        path: list[tuple[str, Room]] = []

        while current_id in came_from:
            direction, prev_id = came_from[current_id]
            room = self.obj_mgr.get(current_id)
            if room:
                path.append((direction, room))
            current_id = prev_id

        path.reverse()
        return path

    async def find_path_to_key(
        self, start: Room, goal_key: str
    ) -> Optional[list[tuple[str, Room]]]:
        """根据房间key寻路.

        Args:
            start: 起始房间
            goal_key: 目标房间key

        Returns:
            路径列表，无路径返回None
        """
        # 通过key查找房间
        rooms = await self.obj_mgr.find(key_contains=goal_key)
        if not rooms:
            return None

        # 找到key完全匹配的房间，或者使用第一个
        for room in rooms:
            if room.key == goal_key:
                return await self.find_path(start, room)

        return await self.find_path(start, rooms[0])

    async def find_path_to_coords(
        self, start: Room, goal_coords: tuple[int, int, int]
    ) -> Optional[list[tuple[str, Room]]]:
        """根据坐标寻路.

        Args:
            start: 起始房间
            goal_coords: 目标坐标 (x, y, z)

        Returns:
            路径列表，无路径返回None
        """
        # 查找该坐标的房间
        rooms = await self.obj_mgr.find(typeclass_path="src.game.typeclasses.room.Room")
        for room in rooms:
            if room.coords == goal_coords:
                return await self.find_path(start, room)

        return None

    def get_distance(self, room1: Room, room2: Room) -> float:
        """计算两个房间之间的距离.

        Args:
            room1: 房间1
            room2: 房间2

        Returns:
            距离值
        """
        return self._heuristic(room1, room2)
