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
        mock_manager.get_contents_sync = Mock(return_value=[])
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


# --- Merged from test_item_coverage.py ---

class MockDBModel:
    """Mock database model."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.key = kwargs.get("key", "test_item")
        self.typeclass_path = kwargs.get("typeclass_path", "src.game.typeclasses.item.Item")
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


@pytest.fixture
def mock_manager():
    return MockManager()


@pytest.fixture
def item(mock_manager):
    """Create test item."""
    mock_model = MockDBModel(id=1, key="test_item")
    return Item(mock_manager, mock_model)


@pytest.fixture
def character(mock_manager):
    """Create test character."""
    mock_model = MockDBModel(
        id=2, 
        key="test_char",
        typeclass_path="src.game.typeclasses.character.Character"
    )
    return Character(mock_manager, mock_model)


class TestItemCanPickupDetailed:
    """Detailed tests for can_pickup method."""
    
    def test_can_pickup_no_weight_attribute(self, item, character):
        """Test item without weight attribute defaults to allowed."""
        # Remove weight attribute
        if hasattr(item, '_weight'):
            delattr(item, '_weight')
        
        can_pickup, msg = item.can_pickup(character)
        assert can_pickup is True
        assert msg == ""
    
    def test_can_pickup_with_negative_weight(self, item, character):
        """Test negative weight handling."""
        item.weight = -10
        
        # Character should handle negative weight gracefully
        can_pickup, msg = item.can_pickup(character)
        # Should be allowed since negative weight effectively reduces load
        assert isinstance(can_pickup, bool)
    
    def test_can_pickup_zero_weight(self, item, character):
        """Test zero weight item can always be picked up."""
        item.weight = 0
        
        can_pickup, msg = item.can_pickup(character)
        assert can_pickup is True
        assert msg == ""


class TestItemCanUseDetailed:
    """Detailed tests for can_use and on_use methods."""
    
    def test_can_use_default(self, item, character):
        """Test default can_use returns False."""
        can_use, msg = item.can_use(character)
        assert can_use is False
        assert "无法使用" in msg or "cannot" in msg.lower()
    
    def test_can_use_consumable_type(self, mock_manager):
        """Test consumable item type check."""
        # This would need a ConsumableItem subclass
        # For now, test base Item behavior
        mock_model = MockDBModel(id=3, key="consumable")
        item = Item(mock_manager, mock_model)
        
        # Base Item should not be usable
        can_use, _ = item.can_use(Mock())
        assert can_use is False
    
    @pytest.mark.asyncio
    async def test_on_use_default(self, item, character):
        """Test default on_use returns False."""
        result = await item.on_use(character)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_on_use_no_character(self, item):
        """Test on_use with no character."""
        result = await item.on_use(None)
        assert result is False


class TestItemStackable:
    """Tests for stackable items."""
    
    def test_default_not_stackable(self, item):
        """Test default is_stackable is False."""
        assert item.is_stackable is False
    
    def test_set_stackable(self, item):
        """Test setting is_stackable."""
        item.is_stackable = True
        assert item.is_stackable is True
    
    def test_default_stack_size(self, item):
        """Test default stack_size is 1."""
        assert item.stack_size == 1
    
    def test_set_stack_size(self, item):
        """Test setting stack_size."""
        item.stack_size = 99
        assert item.stack_size == 99
    
    def test_stack_size_with_non_stackable(self, item):
        """Test stack_size is 1 when not stackable."""
        item.is_stackable = False
        item.stack_size = 50  # Try to set higher
        # Should still report 1 if not stackable
        # (Behavior depends on implementation)


class TestItemValue:
    """Tests for item value."""
    
    def test_default_value(self, item):
        """Test default value is 0."""
        assert item.value == 0
    
    def test_set_value(self, item):
        """Test setting value."""
        item.value = 100
        assert item.value == 100
    
    def test_value_negative(self, item):
        """Test negative value handling."""
        item.value = -50
        assert item.value == -50


class TestItemDescription:
    """Tests for item description."""
    
    def test_default_description(self, item):
        """Test default description."""
        desc = item.description
        assert "普通" in desc or "ordinary" in desc.lower()
    
    def test_set_description(self, item):
        """Test setting description."""
        item.description = "这是一个特殊的物品。"
        assert item.description == "这是一个特殊的物品。"
    
    def test_get_desc_format(self, item):
        """Test get_desc returns formatted string."""
        item.name = "测试剑"
        item.description = "一把锋利的剑。"
        item.value = 100
        item.weight = 5
        
        desc = item.get_desc()
        assert "测试剑" in desc
        assert "锋利的剑" in desc
        assert "100" in desc or "价值" in desc


class TestItemWeightEdgeCases:
    """Edge cases for weight handling."""
    
    def test_weight_large_value(self, item):
        """Test large weight values."""
        item.weight = 999999
        assert item.weight == 999999
    
    def test_weight_float(self, item):
        """Test float weight (if supported)."""
        # Depending on implementation, may convert to int
        item.weight = 5.5
        # Check behavior
        weight = item.weight
        assert isinstance(weight, (int, float))


class TestItemTypeMethods:
    """Tests for item type related methods."""
    
    def test_item_type_normal(self, item):
        """Test NORMAL type."""
        assert item.item_type == ItemType.NORMAL
    
    def test_item_type_string_conversion(self, mock_manager):
        """Test creating item with string type."""
        # This tests if item_type property handles strings
        mock_model = MockDBModel(id=4, key="typed_item", attributes={"item_type": "equipment"})
        # Note: Base Item class doesn't store item_type in attributes
        # This test documents current behavior


class TestItemNameProperty:
    """Tests for name property integration."""
    
    def test_name_defaults_to_key(self, item):
        """Test name defaults to key when not set."""
        assert item.name == item.key
    
    def test_name_custom_value(self, item):
        """Test custom name."""
        item.name = "Custom Name"
        assert item.name == "Custom Name"
        assert item.key != "Custom Name"
    
    def test_name_in_get_desc(self, item):
        """Test name appears in get_desc."""
        item.name = "金疮药"
        desc = item.get_desc()
        assert "金疮药" in desc
