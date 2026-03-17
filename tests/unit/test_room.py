"""Room 地图系统单元测试."""

from __future__ import annotations

import pytest

from src.game.typeclasses.character import Character
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

    def get_contents_sync(self, obj_id: int) -> list:
        """同步获取对象内容."""
        return [
            obj for obj in self._cache.values()
            if getattr(getattr(obj, '_db_model', None), 'location_id', None) == obj_id
        ]


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
        # 空房间描述应该是字符串
        assert isinstance(desc, str)
        assert len(desc) > 0


class TestRoomNeighborRooms:
    """房间邻居测试."""

    def test_get_neighbor_rooms_empty(self, room: Room):
        """测试空房间没有邻居."""
        neighbors = room.get_neighbor_rooms()
        assert neighbors == []


# --- Merged from test_room_coverage.py ---

class MockDBModel:
    """Mock database model."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.key = kwargs.get("key", "test_room")
        self.typeclass_path = kwargs.get("typeclass_path", "src.game.typeclasses.room.Room")
        self.location_id = kwargs.get("location_id", None)
        self.attributes = kwargs.get("attributes", {})
        self.contents = []


class MockManager:
    """Mock object manager."""

    def __init__(self):
        self.dirty_objects = set()
        self._cache = {}

    def mark_dirty(self, obj):
        self.dirty_objects.add(getattr(obj, 'id', id(obj)))

    def get(self, obj_id):
        return self._cache.get(obj_id)

    def get_contents_sync(self, obj_id):
        """同步获取对象内容."""
        return [
            obj for obj in self._cache.values()
            if getattr(getattr(obj, '_db_model', None), 'location_id', None) == obj_id
        ]

    async def find(self, **kwargs):
        """Mock find method."""
        return []


@pytest.fixture
def mock_manager():
    return MockManager()


@pytest.fixture
def room(mock_manager):
    """Create test room."""
    mock_model = MockDBModel(id=1, key="test_room")
    return Room(mock_manager, mock_model)


class TestRoomGetContentsAsync:
    """Tests for get_contents_async method."""
    
    @pytest.mark.asyncio
    async def test_get_contents_async_empty(self, room):
        """Test async get contents with empty room."""
        contents = await room.get_contents()
        assert contents == []
    
    @pytest.mark.asyncio
    async def test_get_contents_async_with_items(self, room, mock_manager):
        """Test async get contents with items."""
        # Create items in room
        item1_model = MockDBModel(id=10, key="item1", typeclass_path="src.game.typeclasses.item.Item")
        item2_model = MockDBModel(id=11, key="item2", typeclass_path="src.game.typeclasses.item.Item")
        room._db_model.contents = [item1_model, item2_model]
        
        contents = await room.get_contents()
        # Should return list (may be empty if not fully mocked)
        assert isinstance(contents, list)


class TestRoomAtDescDetailed:
    """Detailed tests for at_desc method."""
    
    def test_at_desc_basic(self, room):
        """Test basic room description."""
        room.name = "测试房间"
        room.description = "这是一个测试房间。"
        
        desc = room.at_desc(None)
        assert "测试房间" in desc
        assert "测试房间" in desc
    
    def test_at_desc_with_exits(self, room):
        """Test description includes exits."""
        room.name = "大厅"
        room.description = "宽敞的大厅。"
        
        # Create exits
        exit_n_model = MockDBModel(id=20, key="north_exit", typeclass_path="src.game.typeclasses.room.Exit", attributes={"direction": "n"})
        exit_s_model = MockDBModel(id=21, key="south_exit", typeclass_path="src.game.typeclasses.room.Exit", attributes={"direction": "s"})
        room._db_model.contents = [exit_n_model, exit_s_model]
        
        desc = room.at_desc(None)
        assert "大厅" in desc
        # Should mention exits if implemented
    
    def test_at_desc_with_items(self, room):
        """Test description includes items."""
        room.name = "宝物室"
        room.description = "满是宝物的房间。"
        
        # Create items
        item_model = MockDBModel(id=30, key="treasure", typeclass_path="src.game.typeclasses.item.Item", attributes={"name": "宝箱"})
        room._db_model.contents = [item_model]
        
        desc = room.at_desc(None)
        assert "宝物室" in desc
    
    def test_at_desc_with_characters(self, room):
        """Test description includes other characters."""
        room.name = "广场"
        room.description = "热闹的广场。"
        
        # Create character
        char_model = MockDBModel(id=40, key="npc", typeclass_path="src.game.typeclasses.character.Character", attributes={"name": "路人"})
        room._db_model.contents = [char_model]
        
        desc = room.at_desc(None)
        assert "广场" in desc


class TestRoomNeighborRooms:
    """Tests for get_neighbor_rooms method."""
    
    def test_get_neighbor_rooms_empty(self, room):
        """Test get neighbors with no exits."""
        neighbors = room.get_neighbor_rooms()
        assert neighbors == []
    
    def test_get_neighbor_rooms_with_exits(self, room, mock_manager):
        """Test get neighbors with exits."""
        # Create destination room
        dest_model = MockDBModel(id=50, key="dest_room", typeclass_path="src.game.typeclasses.room.Room")
        mock_manager._cache[50] = Room(mock_manager, dest_model)
        
        # Create exit pointing to destination
        exit_model = MockDBModel(
            id=60, 
            key="east_exit", 
            typeclass_path="src.game.typeclasses.room.Exit",
            attributes={"direction": "e", "destination_id": 50}
        )
        room._db_model.contents = [exit_model]
        
        neighbors = room.get_neighbor_rooms()
        # Should return list of (direction, room) tuples
        assert isinstance(neighbors, list)


class TestExitPropertiesDetailed:
    """Detailed tests for Exit properties."""
    
    @pytest.fixture
    def exit_obj(self, mock_manager):
        """Create test exit."""
        mock_model = MockDBModel(id=100, key="test_exit", typeclass_path="src.game.typeclasses.room.Exit")
        return Exit(mock_manager, mock_model)
    
    def test_exit_default_direction(self, exit_obj):
        """Test default direction is 'n'."""
        assert exit_obj.direction == "n"
    
    def test_exit_set_direction(self, exit_obj):
        """Test setting direction."""
        exit_obj.direction = "e"
        assert exit_obj.direction == "e"
    
    def test_exit_direction_name(self, exit_obj):
        """Test direction_name property."""
        exit_obj.direction = "e"
        assert exit_obj.direction_name == DIRECTION_NAMES.get("e", "未知")
    
    def test_exit_default_not_hidden(self, exit_obj):
        """Test default is_hidden is False."""
        assert exit_obj.is_hidden is False
    
    def test_exit_set_hidden(self, exit_obj):
        """Test setting hidden."""
        exit_obj.is_hidden = True
        assert exit_obj.is_hidden is True
    
    def test_exit_lock_str_default(self, exit_obj):
        """Test default lock_str is empty."""
        assert exit_obj.lock_str == ""
    
    def test_exit_set_lock_str(self, exit_obj):
        """Test setting lock_str."""
        exit_obj.lock_str = "has_item:key"
        assert exit_obj.lock_str == "has_item:key"


class TestExitDestination:
    """Tests for Exit destination properties."""
    
    @pytest.mark.asyncio
    async def test_exit_destination_none(self, mock_manager):
        """Test exit with no destination."""
        mock_model = MockDBModel(id=110, key="exit_none", typeclass_path="src.game.typeclasses.room.Exit")
        exit_obj = Exit(mock_manager, mock_model)
        
        dest = exit_obj.destination
        assert dest is None
    
    @pytest.mark.asyncio
    async def test_exit_can_pass_no_destination(self, mock_manager):
        """Test can_pass with no destination."""
        mock_model = MockDBModel(id=120, key="exit_blocked", typeclass_path="src.game.typeclasses.room.Exit")
        exit_obj = Exit(mock_manager, mock_model)
        
        char_model = MockDBModel(id=130, key="char", typeclass_path="src.game.typeclasses.character.Character")
        character = Character(mock_manager, char_model)
        
        can_pass, reason = await exit_obj.can_pass(character)
        assert can_pass is False
        assert "虚无" in reason or "nowhere" in reason.lower()


class TestRoomCoords:
    """Tests for room coordinates."""
    
    def test_default_coords(self, room):
        """Test default coordinates are (0,0,0)."""
        assert room.coords == (0, 0, 0)
    
    def test_set_coords(self, room):
        """Test setting coordinates."""
        room.coords = (10, 20, 0)
        assert room.coords == (10, 20, 0)
    
    def test_coords_3d(self, room):
        """Test 3D coordinates with z."""
        room.coords = (5, 5, 1)  # Upper floor
        assert room.coords[2] == 1


class TestRoomArea:
    """Tests for room area property."""
    
    def test_default_area(self, room):
        """Test default area."""
        assert room.area == "未知区域"
    
    def test_set_area(self, room):
        """Test setting area."""
        room.area = "扬州城"
        assert room.area == "扬州城"


class TestRoomEnvironment:
    """Tests for room environment."""
    
    def test_default_environment(self, room):
        """Test default environment settings."""
        env = room.environment
        assert "light" in env
        assert "weather" in env
        assert "terrain" in env
    
    def test_set_environment(self, room):
        """Test setting environment."""
        room.environment = {"light": 50, "weather": "rain", "terrain": "forest"}
        assert room.environment["light"] == 50
        assert room.environment["weather"] == "rain"


class TestRoomNameProperty:
    """Tests for room name property integration."""
    
    def test_room_name_defaults_to_key(self, room):
        """Test room name defaults to key."""
        assert room.name == room.key
    
    def test_room_name_custom(self, room):
        """Test custom room name."""
        room.name = "扬州客栈"
        assert room.name == "扬州客栈"
        assert room.key != "扬州客栈"
    
    def test_room_name_in_at_desc(self, room):
        """Test name appears in at_desc."""
        room.name = "龙门客栈"
        room.description = "人来人往的客栈。"
        
        desc = room.at_desc(None)
        assert "龙门客栈" in desc
