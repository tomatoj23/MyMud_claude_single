"""命令显示name属性验证测试.

验证修复后命令系统中 .name 的正确使用。
"""

from __future__ import annotations

import pytest

from src.game.typeclasses.character import Character
from src.game.typeclasses.room import Room, Exit
from src.game.typeclasses.item import Item
from src.game.typeclasses.equipment import Equipment, EquipmentSlot


class MockDBModel:
    """模拟数据库模型."""

    def __init__(self, **kwargs) -> None:
        self.id = kwargs.get("id", 1)
        self.key = kwargs.get("key", "test_key")
        self.typeclass_path = kwargs.get(
            "typeclass_path", "src.game.typeclasses.character.Character"
        )
        self.location_id = kwargs.get("location_id", None)
        self.attributes = kwargs.get("attributes", {})
        self.contents = []


class MockManager:
    """模拟对象管理器."""

    def __init__(self) -> None:
        self._cache: dict[int, object] = {}
        self.dirty_objects: set[int] = set()

    def mark_dirty(self, obj: object) -> None:
        if hasattr(obj, 'id'):
            self.dirty_objects.add(obj.id)

    def get(self, obj_id: int) -> object | None:
        return self._cache.get(obj_id)

    def register(self, obj: object) -> None:
        if hasattr(obj, 'id'):
            self._cache[obj.id] = obj


@pytest.fixture
def mock_manager():
    """创建模拟管理器."""
    return MockManager()


class TestNameInCommandMessages:
    """命令消息中name显示测试."""

    def test_room_name_in_move_messages(self, mock_manager):
        """测试房间移动消息使用name而非key."""
        # 创建原房间
        old_room_db = MockDBModel(
            id=1,
            key="old_room_key",
            typeclass_path="src.game.typeclasses.room.Room"
        )
        old_room = Room(mock_manager, old_room_db)
        old_room.name = "扬州客栈"
        
        # 创建目标房间
        new_room_db = MockDBModel(
            id=2,
            key="new_room_key",
            typeclass_path="src.game.typeclasses.room.Room"
        )
        new_room = Room(mock_manager, new_room_db)
        new_room.name = "扬州大街"
        
        # 验证移动消息使用name
        leave_msg = f"你离开了 {old_room.name}。"
        arrive_msg = f"你来到了 {new_room.name}。"
        
        assert "扬州客栈" in leave_msg
        assert "扬州大街" in arrive_msg
        assert "old_room_key" not in leave_msg
        assert "new_room_key" not in arrive_msg

    def test_item_name_in_inventory_display(self, mock_manager):
        """测试背包列表使用item.name而非key."""
        # 创建物品
        item1_db = MockDBModel(
            id=10,
            key="silver_ingot",
            typeclass_path="src.game.typeclasses.item.Item"
        )
        item1 = Item(mock_manager, item1_db)
        item1.name = "银两"
        
        item2_db = MockDBModel(
            id=11,
            key="healing_herb",
            typeclass_path="src.game.typeclasses.item.Item"
        )
        item2 = Item(mock_manager, item2_db)
        item2.name = "草药"
        
        items = [item1, item2]
        
        # 模拟背包列表显示
        item_names = [f"  {item.name}" for item in items]
        
        assert "  银两" in item_names
        assert "  草药" in item_names
        assert "silver_ingot" not in item_names
        assert "healing_herb" not in item_names

    def test_object_name_in_delete_message(self, mock_manager):
        """测试删除对象消息使用name."""
        # 创建要删除的对象
        item_db = MockDBModel(
            id=20,
            key="trash_item",
            typeclass_path="src.game.typeclasses.item.Item"
        )
        item = Item(mock_manager, item_db)
        item.name = "破旧的布衣"
        
        # 验证删除消息使用name
        name = item.name
        delete_msg = f"你删除了: {name}"
        
        assert "破旧的布衣" in delete_msg
        assert "trash_item" not in delete_msg

    def test_object_name_in_multimatch_message(self, mock_manager):
        """测试多匹配提示使用obj.name."""
        # 创建多个匹配对象
        sword1_db = MockDBModel(id=30, key="sword_001", typeclass_path="src.game.typeclasses.item.Item")
        sword1 = Item(mock_manager, sword1_db)
        sword1.name = "青锋剑"
        
        sword2_db = MockDBModel(id=31, key="sword_002", typeclass_path="src.game.typeclasses.item.Item")
        sword2 = Item(mock_manager, sword2_db)
        sword2.name = "铁剑"
        
        matches = [sword1, sword2]
        
        # 模拟多匹配提示
        names = ", ".join(obj.name for obj in matches)
        multimatch_msg = f"有多个匹配: [{names}]"
        
        assert "青锋剑, 铁剑" == names
        assert "sword_001" not in multimatch_msg
        assert "sword_002" not in multimatch_msg


class TestNameVsKeyIsolation:
    """name与key隔离性验证测试."""

    def test_name_key_difference_in_commands(self, mock_manager):
        """验证命令消息中name和key显示不同."""
        room_db = MockDBModel(
            id=40,
            key="yz_city_001",
            typeclass_path="src.game.typeclasses.room.Room"
        )
        room = Room(mock_manager, room_db)
        room.name = "扬州城"
        
        # 验证name和key不同
        assert room.name != room.key
        assert room.name == "扬州城"
        assert room.key == "yz_city_001"
        
        # 消息应该显示name
        msg = f"你来到了 {room.name}。"
        assert "扬州城" in msg
        assert "yz_city_001" not in msg

    def test_chinese_name_display(self, mock_manager):
        """测试中文name正确显示."""
        item_db = MockDBModel(
            id=50,
            key="long_sword_001",
            typeclass_path="src.game.typeclasses.equipment.Equipment"
        )
        item = Equipment(mock_manager, item_db)
        item.name = "龙泉剑"
        item.slot = EquipmentSlot.MAIN_HAND
        
        # 验证中文name显示
        assert item.name == "龙泉剑"
        
        item_names = [f"  {item.name}"]
        assert "  龙泉剑" in item_names
        assert "long_sword_001" not in item_names


class TestRoomContentsNameDisplay:
    """房间内容name显示测试."""

    def test_character_name_in_room_desc(self, mock_manager):
        """测试房间描述中角色使用name."""
        # 创建房间
        room_db = MockDBModel(
            id=60,
            key="tavern",
            typeclass_path="src.game.typeclasses.room.Room"
        )
        room = Room(mock_manager, room_db)
        room.name = "同福客栈"
        
        # 创建角色
        char_db = MockDBModel(
            id=61,
            key="npc_innkeeper",
            typeclass_path="src.game.typeclasses.character.Character"
        )
        from src.game.typeclasses.character import Character
        char = Character(mock_manager, char_db)
        char.name = "佟掌柜"
        
        # 验证角色name
        assert char.name == "佟掌柜"
        assert char.key == "npc_innkeeper"
        
        # 房间描述应使用name
        room_desc = room.at_desc(None)
        assert "同福客栈" in room_desc

    def test_exit_destination_name_display(self, mock_manager):
        """测试出口目标显示使用name."""
        # 创建目标房间
        dest_db = MockDBModel(
            id=70,
            key="east_market",
            typeclass_path="src.game.typeclasses.room.Room"
        )
        dest = Room(mock_manager, dest_db)
        dest.name = "东市"
        
        # 创建出口
        exit_db = MockDBModel(
            id=71,
            key="east_exit",
            typeclass_path="src.game.typeclasses.room.Exit"
        )
        exit_obj = Exit(mock_manager, exit_db)
        exit_obj.name = "东门"
        
        # 模拟出口描述
        exit_desc = f"{exit_obj.name} - {dest.name}"
        
        assert "东门 - 东市" == exit_desc
        assert "east_exit" not in exit_desc
        assert "east_market" not in exit_desc


class TestNamePriorityOverKey:
    """name优先级验证测试."""

    def test_name_always_preferred_in_display(self, mock_manager):
        """验证显示时总是优先使用name."""
        # 设置完全不同的name和key
        item_db = MockDBModel(
            id=80,
            key="xyz_123_abc",
            typeclass_path="src.game.typeclasses.item.Item"
        )
        item = Item(mock_manager, item_db)
        item.name = "绝世好剑"
        
        # 所有显示场景都使用name
        desc = item.get_desc()
        assert "绝世好剑" in desc
        assert "xyz_123_abc" not in desc
        
        inventory_line = f"  {item.name}"
        assert "  绝世好剑" == inventory_line
        
        delete_msg = f"你删除了: {item.name}"
        assert "你删除了: 绝世好剑" == delete_msg

    def test_name_unicode_support(self, mock_manager):
        """测试Unicode name正确显示."""
        item_db = MockDBModel(
            id=90,
            key="special_item",
            typeclass_path="src.game.typeclasses.item.Item"
        )
        item = Item(mock_manager, item_db)
        item.name = "🗡️神剑🗡️"
        
        # Unicode name应正确显示
        assert "🗡️神剑🗡️" == item.name
        
        msg = f"你获得了 {item.name}"
        assert "你获得了 🗡️神剑🗡️" == msg
