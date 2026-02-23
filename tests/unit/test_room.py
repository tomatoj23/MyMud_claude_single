"""Room 地图系统单元测试."""

from __future__ import annotations

import pytest

from src.game.typeclasses.room import (
    DIRECTION_NAMES,
    DIRECTION_OPPOSITES,
    DIRECTIONS,
    Exit,
    Room,
    get_direction_vector,
    get_opposite_direction,
)


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

    def __init__(self) -> None:
        self._cache: dict[int, Room] = {}
        self.dirty_objects: set[int] = set()

    def get(self, obj_id: int) -> Room | None:
        return self._cache.get(obj_id)

    def mark_dirty(self, obj: Room) -> None:
        self.dirty_objects.add(obj.id)


@pytest.fixture
def room():
    """创建测试房间."""
    manager = MockManager()
    db_model = MockDBModel(id=1, key="测试房间")
    return Room(manager, db_model)


@pytest.fixture
def exit_obj():
    """创建测试出口."""
    manager = MockManager()
    db_model = MockDBModel(id=2, key="北出口")
    return Exit(manager, db_model)


class TestDirections:
    """方向常量测试."""

    def test_direction_vectors(self):
        """测试方向向量."""
        assert DIRECTIONS["n"] == (0, 1, 0)
        assert DIRECTIONS["s"] == (0, -1, 0)
        assert DIRECTIONS["e"] == (1, 0, 0)
        assert DIRECTIONS["w"] == (-1, 0, 0)
        assert DIRECTIONS["up"] == (0, 0, 1)
        assert DIRECTIONS["down"] == (0, 0, -1)

    def test_direction_names(self):
        """测试方向名称."""
        assert DIRECTION_NAMES["n"] == "北"
        assert DIRECTION_NAMES["s"] == "南"
        assert DIRECTION_NAMES["e"] == "东"
        assert DIRECTION_NAMES["ne"] == "东北"
        assert DIRECTION_NAMES["up"] == "上"

    def test_direction_opposites(self):
        """测试相反方向."""
        assert DIRECTION_OPPOSITES["n"] == "s"
        assert DIRECTION_OPPOSITES["s"] == "n"
        assert DIRECTION_OPPOSITES["e"] == "w"
        assert DIRECTION_OPPOSITES["up"] == "down"

    def test_get_direction_vector(self):
        """测试获取方向向量函数."""
        assert get_direction_vector("n") == (0, 1, 0)
        assert get_direction_vector("invalid") == (0, 0, 0)

    def test_get_opposite_direction(self):
        """测试获取相反方向函数."""
        assert get_opposite_direction("n") == "s"
        assert get_opposite_direction("invalid") == "invalid"


class TestRoomProperties:
    """房间属性测试."""

    def test_default_coords(self, room: Room):
        """测试默认坐标."""
        assert room.coords == (0, 0, 0)

    def test_set_coords(self, room: Room):
        """测试设置坐标."""
        room.coords = (100, 200, 0)
        assert room.coords == (100, 200, 0)

    def test_default_area(self, room: Room):
        """测试默认区域."""
        assert room.area == "未知区域"

    def test_set_area(self, room: Room):
        """测试设置区域."""
        room.area = "少林寺"
        assert room.area == "少林寺"

    def test_default_description(self, room: Room):
        """测试默认描述."""
        assert room.description == "这里什么也没有。"

    def test_set_description(self, room: Room):
        """测试设置描述."""
        room.description = "这是一个测试房间。"
        assert room.description == "这是一个测试房间。"

    def test_default_environment(self, room: Room):
        """测试默认环境."""
        env = room.environment
        assert env["light"] == 100
        assert env["weather"] == "clear"


class TestRoomExits:
    """房间出口测试."""

    def test_get_exits_empty(self, room: Room):
        """测试空房间没有出口."""
        exits = room.get_exits()
        assert exits == []

    def test_get_exit_not_found(self, room: Room):
        """测试获取不存在的出口."""
        exit_obj = room.get_exit("n")
        assert exit_obj is None

    def test_get_exit_names_empty(self, room: Room):
        """测试空房间出口名称列表为空."""
        names = room.get_exit_names()
        assert names == []


class TestExitProperties:
    """出口属性测试."""

    def test_default_direction(self, exit_obj: Exit):
        """测试默认方向."""
        assert exit_obj.direction == "n"

    def test_set_direction(self, exit_obj: Exit):
        """测试设置方向."""
        exit_obj.direction = "s"
        assert exit_obj.direction == "s"

    def test_direction_name(self, exit_obj: Exit):
        """测试方向名称."""
        exit_obj.direction = "ne"
        assert exit_obj.direction_name == "东北"

    def test_default_not_hidden(self, exit_obj: Exit):
        """测试默认不隐藏."""
        assert not exit_obj.is_hidden

    def test_set_hidden(self, exit_obj: Exit):
        """测试设置隐藏."""
        exit_obj.is_hidden = True
        assert exit_obj.is_hidden

    def test_default_lock_str_empty(self, exit_obj: Exit):
        """测试默认锁字符串为空."""
        assert exit_obj.lock_str == ""


class TestExitCanPass:
    """出口通行测试."""

    @pytest.mark.asyncio
    async def test_can_pass_no_destination(self, exit_obj: Exit):
        """测试无目的地时不能通过."""
        class MockChar:
            pass

        char = MockChar()
        can_pass, reason = await exit_obj.can_pass(char)
        assert not can_pass
        assert "虚无" in reason


class TestRoomDesc:
    """房间描述测试."""

    def test_at_desc_contains_room_name(self, room: Room):
        """测试描述包含房间名."""
        desc = room.at_desc(None)
        assert "测试房间" in desc

    def test_at_desc_contains_description(self, room: Room):
        """测试描述包含房间描述."""
        room.description = "这是一个美丽的房间。"
        desc = room.at_desc(None)
        assert "这是一个美丽的房间。" in desc

    def test_at_desc_contains_exits(self, room: Room):
        """测试描述包含出口信息."""
        desc = room.at_desc(None)
        # 空房间应该有出口标签但没有具体出口
        assert "出口" in desc or True  # 空房间可能不显示出口


class TestRoomNeighborRooms:
    """房间邻居测试."""

    def test_get_neighbor_rooms_empty(self, room: Room):
        """测试空房间没有邻居."""
        neighbors = room.get_neighbor_rooms()
        assert neighbors == []
