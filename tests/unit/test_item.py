"""物品系统单元测试.

测试物品基类 Item 的所有功能.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.game.typeclasses.character import Character
from src.game.typeclasses.item import Item, ItemType


class TestItemType:
    """物品类型枚举测试."""

    def test_item_type_values(self):
        """测试物品类型值."""
        assert ItemType.NORMAL.value == "normal"
        assert ItemType.EQUIPMENT.value == "equipment"
        assert ItemType.CONSUMABLE.value == "consumable"
        assert ItemType.QUEST.value == "quest"
        assert ItemType.MATERIAL.value == "material"

    def test_item_type_count(self):
        """测试物品类型数量."""
        assert len(ItemType) == 5


class TestItemProperties:
    """物品属性测试."""

    @pytest.fixture
    def item(self):
        """创建测试物品."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 1
        mock_model.key = "测试物品"
        mock_model.typeclass_path = "src.game.typeclasses.item.Item"
        mock_model.location_id = None
        mock_model.attributes = {}
        
        item = Item(mock_manager, mock_model)
        return item

    def test_default_item_type(self, item):
        """测试默认物品类型."""
        assert item.item_type == ItemType.NORMAL

    def test_default_weight(self, item):
        """测试默认重量."""
        assert item.weight == 1

    def test_set_weight(self, item):
        """测试设置重量."""
        item.weight = 5
        assert item.weight == 5

    def test_default_value(self, item):
        """测试默认价值."""
        assert item.value == 0

    def test_set_value(self, item):
        """测试设置价值."""
        item.value = 100
        assert item.value == 100

    def test_default_description(self, item):
        """测试默认描述."""
        assert "普通" in item.description

    def test_set_description(self, item):
        """测试设置描述."""
        item.description = "这是一个测试物品"
        assert item.description == "这是一个测试物品"

    def test_default_is_stackable(self, item):
        """测试默认可堆叠性."""
        assert item.is_stackable is False

    def test_set_is_stackable(self, item):
        """测试设置可堆叠性."""
        item.is_stackable = True
        assert item.is_stackable is True

    def test_default_stack_size(self, item):
        """测试默认堆叠数量."""
        assert item.stack_size == 1

    def test_set_stack_size(self, item):
        """测试设置堆叠数量."""
        item.stack_size = 99
        assert item.stack_size == 99


class TestItemCanPickup:
    """物品拾取检查测试."""

    @pytest.fixture
    def item(self):
        """创建测试物品."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 1
        mock_model.key = "测试物品"
        mock_model.typeclass_path = "src.game.typeclasses.item.Item"
        mock_model.location_id = None
        mock_model.attributes = {}
        
        item = Item(mock_manager, mock_model)
        return item

    @pytest.fixture
    def character(self):
        """创建测试角色."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 2
        mock_model.key = "测试角色"
        mock_model.typeclass_path = "src.game.typeclasses.character.Character"
        mock_model.location_id = None
        mock_model.attributes = {}
        mock_model.contents = []  # 添加contents属性支持负重系统
        
        char = Character(mock_manager, mock_model)
        return char

    def test_can_pickup_default(self, item, character):
        """测试默认可以拾取."""
        can_pickup, reason = item.can_pickup(character)
        assert can_pickup is True
        assert reason == ""


class TestItemCanUse:
    """物品使用检查测试."""

    @pytest.fixture
    def item(self):
        """创建测试物品."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 1
        mock_model.key = "测试物品"
        mock_model.typeclass_path = "src.game.typeclasses.item.Item"
        mock_model.location_id = None
        mock_model.attributes = {}
        
        item = Item(mock_manager, mock_model)
        return item

    @pytest.fixture
    def character(self):
        """创建测试角色."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 2
        mock_model.key = "测试角色"
        mock_model.typeclass_path = "src.game.typeclasses.character.Character"
        mock_model.location_id = None
        mock_model.attributes = {}
        
        char = Character(mock_manager, mock_model)
        return char

    def test_can_use_default(self, item, character):
        """测试默认不可使用."""
        can_use, reason = item.can_use(character)
        assert can_use is False
        assert "无法使用" in reason

    @pytest.mark.asyncio
    async def test_on_use_default(self, item, character):
        """测试默认使用失败."""
        result = await item.on_use(character)
        assert result is False


class TestItemGetDesc:
    """物品描述测试."""

    @pytest.fixture
    def item(self):
        """创建测试物品."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 1
        mock_model.key = "测试物品"
        mock_model.typeclass_path = "src.game.typeclasses.item.Item"
        mock_model.location_id = None
        mock_model.attributes = {}
        
        item = Item(mock_manager, mock_model)
        return item

    def test_get_desc_contains_name(self, item):
        """测试描述包含物品名."""
        desc = item.get_desc()
        assert "测试物品" in desc

    def test_get_desc_contains_description(self, item):
        """测试描述包含物品描述."""
        item.description = "特殊的描述"
        desc = item.get_desc()
        assert "特殊的描述" in desc

    def test_get_desc_contains_value(self, item):
        """测试描述包含价值."""
        item.value = 100
        desc = item.get_desc()
        assert "100" in desc
        assert "铜钱" in desc

    def test_get_desc_contains_weight(self, item):
        """测试描述包含重量."""
        item.weight = 5
        desc = item.get_desc()
        assert "5" in desc
        assert "重量" in desc

    def test_get_desc_no_value(self, item):
        """测试价值为0时不显示."""
        item.value = 0
        desc = item.get_desc()
        # 价值为0时不应显示价值信息
        assert "铜钱" not in desc


class TestItemInitialization:
    """物品初始化测试."""

    def test_item_initialization(self):
        """测试物品正确初始化."""
        mock_manager = Mock()
        mock_model = Mock()
        mock_model.id = 1
        mock_model.key = "新物品"
        mock_model.typeclass_path = "src.game.typeclasses.item.Item"
        mock_model.location_id = None
        mock_model.attributes = {"weight": 10, "value": 50}
        
        item = Item(mock_manager, mock_model)
        
        assert item.id == 1
        assert item.key == "新物品"
        assert item.weight == 10
        assert item.value == 50
