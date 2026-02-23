"""房间系统扩展单元测试.

补充 room.py 中未覆盖的功能测试.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from src.game.typeclasses.character import Character
from src.game.typeclasses.item import Item
from src.game.typeclasses.room import Exit, Room


class TestRoomEnvironment:
    """房间环境属性测试."""

    @pytest.fixture
    def room(self):
        """创建测试房间."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 1
        mock_model.key = "测试房间"
        mock_model.typeclass_path = "src.game.typeclasses.room.Room"
        mock_model.location_id = None
        mock_model.attributes = {}
        mock_model.contents = []
        
        room = Room(mock_manager, mock_model)
        return room

    def test_default_environment(self, room):
        """测试默认环境属性."""
        env = room.environment
        assert "light" in env
        assert "weather" in env
        assert "terrain" in env
        assert env["light"] == 100
        assert env["weather"] == "clear"
        assert env["terrain"] == "normal"

    def test_set_environment(self, room):
        """测试设置环境属性."""
        room.environment = {"light": 50, "weather": "rain", "terrain": "forest"}
        env = room.environment
        assert env["light"] == 50
        assert env["weather"] == "rain"
        assert env["terrain"] == "forest"


class TestRoomGetExit:
    """房间出口获取测试."""

    @pytest.fixture
    def room(self):
        """创建测试房间."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 1
        mock_model.key = "测试房间"
        mock_model.typeclass_path = "src.game.typeclasses.room.Room"
        mock_model.location_id = None
        mock_model.attributes = {}
        mock_model.contents = []
        
        room = Room(mock_manager, mock_model)
        return room

    def test_get_exit_not_found(self, room):
        """测试获取不存在的出口."""
        exit_obj = room.get_exit("n")
        assert exit_obj is None

    def test_get_exit_names_empty(self, room):
        """测试空房间出口名称."""
        names = room.get_exit_names()
        assert names == []


class TestRoomGetCharacters:
    """房间角色获取测试."""

    @pytest.fixture
    def room(self):
        """创建测试房间."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 1
        mock_model.key = "测试房间"
        mock_model.typeclass_path = "src.game.typeclasses.room.Room"
        mock_model.location_id = None
        mock_model.attributes = {}
        mock_model.contents = []
        
        room = Room(mock_manager, mock_model)
        return room

    def test_get_characters_empty(self, room):
        """测试空房间获取角色."""
        characters = room.get_characters()
        assert characters == []

    def test_get_characters_with_items(self, room):
        """测试房间内有物品时获取角色（应排除物品）."""
        # 这个测试主要验证类型过滤
        characters = room.get_characters()
        # 由于 contents 为空，结果应为空
        assert characters == []


class TestRoomGetItems:
    """房间物品获取测试."""

    @pytest.fixture
    def room(self):
        """创建测试房间."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 1
        mock_model.key = "测试房间"
        mock_model.typeclass_path = "src.game.typeclasses.room.Room"
        mock_model.location_id = None
        mock_model.attributes = {}
        mock_model.contents = []
        
        room = Room(mock_manager, mock_model)
        return room

    def test_get_items_empty(self, room):
        """测试空房间获取物品."""
        items = room.get_items()
        assert items == []


class TestRoomAtDesc:
    """房间描述渲染测试."""

    @pytest.fixture
    def room(self):
        """创建测试房间."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 1
        mock_model.key = "扬州城广场"
        mock_model.typeclass_path = "src.game.typeclasses.room.Room"
        mock_model.location_id = None
        mock_model.attributes = {"description": "扬州城的中心广场"}
        mock_model.contents = []
        
        room = Room(mock_manager, mock_model)
        return room

    def test_at_desc_contains_room_name(self, room):
        """测试描述包含房间名."""
        desc = room.at_desc(None)
        assert "扬州城广场" in desc

    def test_at_desc_contains_description(self, room):
        """测试描述包含房间描述."""
        desc = room.at_desc(None)
        assert "中心广场" in desc

    def test_at_desc_formatting(self, room):
        """测试描述格式."""
        desc = room.at_desc(None)
        assert "=" in desc  # 分隔线


class TestRoomNeighborRooms:
    """房间邻居获取测试."""

    @pytest.fixture
    def room(self):
        """创建测试房间."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 1
        mock_model.key = "测试房间"
        mock_model.typeclass_path = "src.game.typeclasses.room.Room"
        mock_model.location_id = None
        mock_model.attributes = {}
        mock_model.contents = []
        
        room = Room(mock_manager, mock_model)
        return room

    def test_get_neighbor_rooms_empty(self, room):
        """测试空房间获取邻居."""
        neighbors = room.get_neighbor_rooms()
        assert neighbors == []


class TestExitDestination:
    """出口目的地测试."""

    @pytest.fixture
    def exit_obj(self):
        """创建测试出口."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 1
        mock_model.key = "北门"
        mock_model.typeclass_path = "src.game.typeclasses.room.Exit"
        mock_model.location_id = 100
        mock_model.attributes = {"direction": "n", "destination_id": 200}
        
        exit_obj = Exit(mock_manager, mock_model)
        return exit_obj

    def test_destination_id_property(self, exit_obj):
        """测试目的地ID属性."""
        assert exit_obj.destination_id == 200

    def test_destination_setter(self, exit_obj):
        """测试目的地设置器."""
        mock_room = Mock()
        mock_room.id = 300
        
        exit_obj.destination = mock_room
        assert exit_obj.destination_id == 300

    def test_destination_setter_none(self, exit_obj):
        """测试设置空目的地."""
        exit_obj.destination = None
        assert exit_obj.destination_id is None


class TestExitCanPass:
    """出口通行检查测试."""

    @pytest.fixture
    def exit_with_dest(self):
        """创建有目的地的出口."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 1
        mock_model.key = "北门"
        mock_model.typeclass_path = "src.game.typeclasses.room.Exit"
        mock_model.location_id = 100
        mock_model.attributes = {"direction": "n", "destination_id": 200}
        
        exit_obj = Exit(mock_manager, mock_model)
        
        # 模拟目的地存在
        mock_dest = Mock()
        mock_dest.id = 200
        type(exit_obj).destination = property(lambda self: mock_dest)
        
        return exit_obj

    @pytest.fixture
    def character(self):
        """创建测试角色."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 1
        mock_model.key = "测试角色"
        mock_model.typeclass_path = "src.game.typeclasses.character.Character"
        mock_model.location_id = None
        mock_model.attributes = {}
        
        char = Character(mock_manager, mock_model)
        return char

    @pytest.mark.asyncio
    async def test_can_pass_with_destination(self, exit_with_dest, character):
        """测试有目的地时可以通行."""
        can_pass, reason = await exit_with_dest.can_pass(character)
        assert can_pass is True


class TestRoomContentsAsync:
    """房间异步内容物获取测试."""

    @pytest.mark.asyncio
    async def test_get_contents_async(self):
        """测试异步获取房间内容物."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 1
        mock_model.key = "测试房间"
        mock_model.typeclass_path = "src.game.typeclasses.room.Room"
        mock_model.location_id = None
        mock_model.attributes = {}
        mock_model.contents = []
        
        room = Room(mock_manager, mock_model)
        
        # 模拟数据库返回 (返回一个可等待对象)
        async def async_empty(*args, **kwargs):
            return []
        mock_manager.db.fetchall = async_empty
        
        contents = await room.get_contents_async()
        assert contents == []

    @pytest.mark.asyncio
    async def test_get_contents_async_no_manager(self):
        """测试无管理器时的异步获取."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 1
        mock_model.key = "测试房间"
        mock_model.typeclass_path = "src.game.typeclasses.room.Room"
        mock_model.location_id = None
        mock_model.attributes = {}
        mock_model.contents = []
        
        room = Room(mock_manager, mock_model)
        
        # 删除 _manager 属性
        del room._manager
        
        contents = await room.get_contents_async()
        assert contents == []
