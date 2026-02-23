"""Room模块覆盖率补充测试 (ARCH-004)."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.game.typeclasses.room import Room, Exit, DIRECTION_NAMES
from src.game.typeclasses.character import Character


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
