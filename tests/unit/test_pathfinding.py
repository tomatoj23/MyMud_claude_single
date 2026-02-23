"""Pathfinding 寻路算法单元测试."""

from __future__ import annotations

import pytest

from src.game.typeclasses.room import Room
from src.game.world.pathfinding import PathFinder


class MockDBModel:
    """模拟数据库模型."""

    def __init__(self, **kwargs) -> None:
        self.id = kwargs.get("id", 1)
        self.key = kwargs.get("key", "test_room")
        self.typeclass_path = kwargs.get(
            "typeclass_path", "src.game.typeclasses.room.Room"
        )
        self.location_id = kwargs.get("location_id", None)
        self.attributes = kwargs.get("attributes", {})
        self.contents = []


class MockManager:
    """模拟对象管理器."""

    def __init__(self):
        self._cache: dict[int, Room] = {}
        self._rooms_by_coords: dict[tuple[int, int, int], Room] = {}

    def get(self, obj_id: int) -> Room | None:
        return self._cache.get(obj_id)

    def add_room(self, room: Room):
        self._cache[room.id] = room
        self._rooms_by_coords[room.coords] = room

    async def find(self, **kwargs):
        """模拟查找房间."""
        typeclass_path = kwargs.get("typeclass_path")
        if typeclass_path == "src.game.typeclasses.room.Room":
            return list(self._cache.values())
        return []


class MockExit:
    """模拟出口."""

    def __init__(self, direction: str, destination_id: int, destination=None):
        self.direction = direction
        self.destination_id = destination_id
        self._destination = destination

    @property
    def destination(self):
        return self._destination


class MockRoom:
    """简化版模拟房间."""

    def __init__(self, room_id: int, coords: tuple[int, int, int], key: str = ""):
        self.id = room_id
        self.coords = coords
        self.key = key or f"room_{room_id}"
        self._exits: list[MockExit] = []
        self.area = "test"

    def get_exits(self):
        return self._exits

    def add_exit(self, exit_obj: MockExit):
        self._exits.append(exit_obj)


@pytest.fixture
def pathfinder():
    """创建寻路器."""
    manager = MockManager()
    return PathFinder(manager), manager


class TestPathFinder:
    """寻路器测试."""

    @pytest.mark.asyncio
    async def test_find_path_same_room(self, pathfinder):
        """测试起点终点相同时返回空路径."""
        finder, manager = pathfinder

        room1 = MockRoom(1, (0, 0, 0))
        manager.add_room(room1)

        path = await finder.find_path(room1, room1)
        assert path == []

    @pytest.mark.asyncio
    async def test_find_path_direct_connection(self, pathfinder):
        """测试直接相连的房间."""
        finder, manager = pathfinder

        room1 = MockRoom(1, (0, 0, 0))
        room2 = MockRoom(2, (0, 1, 0))

        # 房间1北通房间2
        exit_n = MockExit("n", 2, room2)
        room1.add_exit(exit_n)

        manager.add_room(room1)
        manager.add_room(room2)

        path = await finder.find_path(room1, room2)
        assert len(path) == 1
        assert path[0][0] == "n"

    @pytest.mark.asyncio
    async def test_find_path_two_steps(self, pathfinder):
        """测试两步路径."""
        finder, manager = pathfinder

        room1 = MockRoom(1, (0, 0, 0))
        room2 = MockRoom(2, (0, 1, 0))
        room3 = MockRoom(3, (0, 2, 0))

        # 1->2->3
        room1.add_exit(MockExit("n", 2, room2))
        room2.add_exit(MockExit("n", 3, room3))

        manager.add_room(room1)
        manager.add_room(room2)
        manager.add_room(room3)

        path = await finder.find_path(room1, room3)
        assert len(path) == 2
        assert path[0][0] == "n"
        assert path[1][0] == "n"

    @pytest.mark.asyncio
    async def test_find_path_no_path(self, pathfinder):
        """测试无路径时返回None."""
        finder, manager = pathfinder

        room1 = MockRoom(1, (0, 0, 0))
        room2 = MockRoom(2, (10, 10, 0))

        # 没有连接
        manager.add_room(room1)
        manager.add_room(room2)

        path = await finder.find_path(room1, room2)
        assert path is None

    @pytest.mark.asyncio
    async def test_find_path_avoids_detours(self, pathfinder):
        """测试寻路选择最短路径."""
        finder, manager = pathfinder

        # 创建网格: 1-2-3
        #          |
        #          4
        room1 = MockRoom(1, (0, 0, 0))
        room2 = MockRoom(2, (0, 1, 0))
        room3 = MockRoom(3, (0, 2, 0))
        room4 = MockRoom(4, (1, 0, 0))

        # 1->2->3 (长路径)
        room1.add_exit(MockExit("n", 2, room2))
        room2.add_exit(MockExit("n", 3, room3))

        # 1->4 (短路径，但不是目标)
        room1.add_exit(MockExit("e", 4, room4))

        manager.add_room(room1)
        manager.add_room(room2)
        manager.add_room(room3)
        manager.add_room(room4)

        path = await finder.find_path(room1, room3)
        assert len(path) == 2  # 应该走 1->2->3

    def test_heuristic_manhattan_distance(self, pathfinder):
        """测试启发函数使用曼哈顿距离."""
        finder, manager = pathfinder

        room1 = MockRoom(1, (0, 0, 0))
        room2 = MockRoom(2, (3, 4, 0))

        # 曼哈顿距离: |3-0| + |4-0| + |0-0|*2 = 3 + 4 + 0 = 7
        distance = finder._heuristic(room1, room2)
        assert distance == 7

    def test_heuristic_z_weighted(self, pathfinder):
        """测试Z轴权重更高."""
        finder, manager = pathfinder

        room1 = MockRoom(1, (0, 0, 0))
        room2 = MockRoom(2, (0, 0, 3))

        # Z轴权重为2: 3 * 2 = 6
        distance = finder._heuristic(room1, room2)
        assert distance == 6

    def test_get_distance(self, pathfinder):
        """测试距离计算."""
        finder, manager = pathfinder

        room1 = MockRoom(1, (0, 0, 0))
        room2 = MockRoom(2, (1, 2, 3))

        # 1 + 2 + 3*2 = 9
        distance = finder.get_distance(room1, room2)
        assert distance == 9
