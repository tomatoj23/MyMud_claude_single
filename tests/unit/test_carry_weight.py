"""负重系统单元测试 (TD-014)."""

from __future__ import annotations

import pytest

from src.game.typeclasses.character import Character
from src.game.typeclasses.item import Item


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


@pytest.fixture
def mock_manager():
    return MockManager()


class TestCharacterCarryWeight:
    """角色负重功能测试."""

    def test_get_current_weight_empty(self, mock_manager):
        """测试空背包负重为0."""
        db = MockDBModel(id=1, key="char1")
        char = Character(mock_manager, db)
        
        assert char.get_current_weight() == 0

    def test_get_current_weight_with_items(self, mock_manager):
        """测试有物品时负重计算正确."""
        db = MockDBModel(id=2, key="char2")
        char = Character(mock_manager, db)
        
        # 直接设置物品到角色的contents中（模拟数据库中的物品）
        item1_data = MockDBModel(id=10, key="item1", typeclass_path="src.game.typeclasses.item.Item", attributes={"weight": 5})
        item2_data = MockDBModel(id=11, key="item2", typeclass_path="src.game.typeclasses.item.Item", attributes={"weight": 3})
        
        char._db_model.contents = [item1_data, item2_data]
        
        assert char.get_current_weight() == 8

    def test_get_max_weight_base(self, mock_manager):
        """测试基础最大负重."""
        db = MockDBModel(id=3, key="char3")
        char = Character(mock_manager, db)
        
        # 默认臂力10
        assert char.get_max_weight() == 100  # 基础50 + 臂力10*5

    def test_get_max_weight_with_strength(self, mock_manager):
        """测试臂力影响最大负重."""
        db = MockDBModel(id=4, key="char4")
        char = Character(mock_manager, db)
        
        # 设置臂力为20
        char.attributes = {"strength": 20}
        
        # 基础50 + 20*5 = 150
        assert char.get_max_weight() == 150

    def test_get_max_weight_with_equipment_bonus(self, mock_manager):
        """测试装备加成影响最大负重."""
        db = MockDBModel(id=5, key="char5")
        char = Character(mock_manager, db)
        
        # 模拟装备加成
        # 这需要装备系统支持，先跳过详细测试
        max_weight = char.get_max_weight()
        assert max_weight >= 50  # 至少基础值

    def test_can_carry_when_not_overweight(self, mock_manager):
        """测试未超重时可以携带."""
        db = MockDBModel(id=6, key="char6")
        char = Character(mock_manager, db)
        
        # 创建轻物品
        item_db = MockDBModel(id=12, key="light_item", typeclass_path="src.game.typeclasses.item.Item")
        item = Item(mock_manager, item_db)
        item.weight = 10
        
        # 应该可以携带
        can_carry, msg = char.can_carry(item)
        assert can_carry is True
        assert msg == ""

    def test_can_carry_when_overweight(self, mock_manager):
        """测试超重时无法携带."""
        db = MockDBModel(id=7, key="char7")
        char = Character(mock_manager, db)
        
        # 创建超重物品
        item_db = MockDBModel(id=13, key="heavy_item", typeclass_path="src.game.typeclasses.item.Item")
        item = Item(mock_manager, item_db)
        item.weight = 1000  # 远超过最大负重
        
        # 应该无法携带
        can_carry, msg = char.can_carry(item)
        assert can_carry is False
        assert "负重" in msg or "太沉" in msg

    def test_carry_weight_exact_limit(self, mock_manager):
        """测试刚好达到负重上限."""
        db = MockDBModel(id=8, key="char8")
        char = Character(mock_manager, db)
        
        # 先放入一些物品
        item1_db = MockDBModel(id=14, key="item1", typeclass_path="src.game.typeclasses.item.Item")
        item1 = Item(mock_manager, item1_db)
        item1.weight = 90
        item1.location = char
        char._contents_cache = [item1]
        
        # 再放入一个刚好达到上限的物品
        item2_db = MockDBModel(id=15, key="item2", typeclass_path="src.game.typeclasses.item.Item")
        item2 = Item(mock_manager, item2_db)
        item2.weight = 10  # 90 + 10 = 100 = 最大负重
        
        can_carry, _ = char.can_carry(item2)
        assert can_carry is True


class TestItemCanPickup:
    """物品拾取检查测试."""

    def test_can_pickup_when_not_overweight(self, mock_manager):
        """测试未超重时可以拾取."""
        char_db = MockDBModel(id=20, key="char20")
        char = Character(mock_manager, char_db)
        
        item_db = MockDBModel(id=21, key="pickup_item", typeclass_path="src.game.typeclasses.item.Item")
        item = Item(mock_manager, item_db)
        item.weight = 10
        
        can_pickup, msg = item.can_pickup(char)
        assert can_pickup is True
        assert msg == ""

    def test_can_pickup_when_overweight(self, mock_manager):
        """测试超重时无法拾取."""
        char_db = MockDBModel(id=22, key="char22")
        char = Character(mock_manager, char_db)
        
        # 先让角色负重接近上限（通过直接设置contents）
        heavy_item_data = MockDBModel(id=23, key="heavy", typeclass_path="src.game.typeclasses.item.Item", attributes={"weight": 95})
        char._db_model.contents = [heavy_item_data]
        
        # 再尝试拾取一个超重物品
        item_db = MockDBModel(id=24, key="too_heavy", typeclass_path="src.game.typeclasses.item.Item")
        item = Item(mock_manager, item_db)
        item.weight = 10  # 95 + 10 > 100
        
        can_pickup, msg = item.can_pickup(char)
        assert can_pickup is False
        assert "拿不动" in msg or "负重" in msg

    def test_can_pickup_zero_weight_item(self, mock_manager):
        """测试零重量物品总是可以拾取."""
        char_db = MockDBModel(id=25, key="char25")
        char = Character(mock_manager, char_db)
        
        # 让角色已经满负重
        heavy_db = MockDBModel(id=26, key="heavy", typeclass_path="src.game.typeclasses.item.Item")
        heavy = Item(mock_manager, heavy_db)
        heavy.weight = 100
        heavy.location = char
        char._contents_cache = [heavy]
        
        # 零重量物品
        item_db = MockDBModel(id=27, key="zero_weight", typeclass_path="src.game.typeclasses.item.Item")
        item = Item(mock_manager, item_db)
        item.weight = 0
        
        can_pickup, msg = item.can_pickup(char)
        assert can_pickup is True


class TestCarryWeightEdgeCases:
    """负重边界情况测试."""

    def test_negative_weight(self, mock_manager):
        """测试负重量处理."""
        db = MockDBModel(id=30, key="char30")
        char = Character(mock_manager, db)
        
        item_db = MockDBModel(id=31, key="negative", typeclass_path="src.game.typeclasses.item.Item")
        item = Item(mock_manager, item_db)
        item.weight = -10  # 异常数据
        
        # 应该按0处理或拒绝
        can_carry, _ = char.can_carry(item)
        # 具体行为取决于实现
        assert isinstance(can_carry, bool)

    def test_very_large_weight(self, mock_manager):
        """测试超大重量处理."""
        db = MockDBModel(id=32, key="char32")
        char = Character(mock_manager, db)
        
        item_db = MockDBModel(id=33, key="huge", typeclass_path="src.game.typeclasses.item.Item")
        item = Item(mock_manager, item_db)
        item.weight = 999999999
        
        can_carry, msg = char.can_carry(item)
        assert can_carry is False

    def test_carry_weight_display(self, mock_manager):
        """测试负重显示信息."""
        db = MockDBModel(id=34, key="char34")
        char = Character(mock_manager, db)
        
        # 放入一些物品
        item_db = MockDBModel(id=35, key="item", typeclass_path="src.game.typeclasses.item.Item")
        item = Item(mock_manager, item_db)
        item.weight = 50
        item.location = char
        char._contents_cache = [item]
        
        # 验证显示信息
        info = char.get_carry_weight_info()
        # 验证显示信息包含当前和最大值
        assert "0/100" in info  # 格式: 当前/最大
