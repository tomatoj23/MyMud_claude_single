"""Name属性边界情况和潜在问题排查测试.

排查可能存在的边界问题和潜在bug。
"""

from __future__ import annotations

import pytest

from src.game.typeclasses.character import Character
from src.game.typeclasses.room import Room
from src.game.typeclasses.item import Item
from src.game.typeclasses.equipment import Equipment


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
    def __init__(self) -> None:
        self._cache: dict[int, object] = {}
        self.dirty_objects: set[int] = set()

    def mark_dirty(self, obj: object) -> None:
        if hasattr(obj, 'id'):
            self.dirty_objects.add(obj.id)


@pytest.fixture
def mock_manager():
    return MockManager()


class TestNameFallbackEdgeCases:
    """name回退逻辑边界测试."""

    def test_empty_string_name_fallback(self, mock_manager):
        """测试空字符串name回退到key."""
        db = MockDBModel(id=1, key="test_key")
        char = Character(mock_manager, db)
        
        # 设置空字符串
        char.name = ""
        
        # 应回退到key
        assert char.name == "test_key"

    def test_whitespace_only_name_not_fallback(self, mock_manager):
        """测试纯空白name不回退（保留空格）."""
        db = MockDBModel(id=2, key="test_key")
        char = Character(mock_manager, db)
        
        # 设置纯空格
        char.name = "   "
        
        # 空格是有效字符串，不回退
        assert char.name == "   "

    def test_none_name_fallback(self, mock_manager):
        """测试None值回退到key."""
        db = MockDBModel(id=3, key="fallback_key")
        char = Character(mock_manager, db)
        
        # 直接设置None到db
        char.db.set("name", None)
        
        # 应回退到key
        assert char.name == "fallback_key"

    def test_zero_name_fallback(self, mock_manager):
        """测试数字0回退到key."""
        db = MockDBModel(id=4, key="numeric_key")
        char = Character(mock_manager, db)
        
        # 设置数字0（Python中0为假值）
        char.db.set("name", 0)
        
        # 0应为假值，回退到key
        assert char.name == "numeric_key"

    def test_false_name_fallback(self, mock_manager):
        """测试False回退到key."""
        db = MockDBModel(id=5, key="bool_key")
        char = Character(mock_manager, db)
        
        # 设置False
        char.db.set("name", False)
        
        # False为假值，回退到key
        assert char.name == "bool_key"


class TestNameKeyInteraction:
    """name与key交互测试."""

    def test_change_key_does_not_affect_name(self, mock_manager):
        """测试修改key不影响已设置的name."""
        db = MockDBModel(id=10, key="old_key")
        char = Character(mock_manager, db)
        char.name = "固定名字"
        
        # 修改key
        char.key = "new_key"
        
        # name应保持不变
        assert char.name == "固定名字"
        assert char.key == "new_key"

    def test_name_same_as_key_behavior(self, mock_manager):
        """测试name与key相同时的行为."""
        db = MockDBModel(id=11, key="same_value")
        char = Character(mock_manager, db)
        
        # 设置name与key相同
        char.name = "same_value"
        
        # 两者相同
        assert char.name == char.key
        assert char.name == "same_value"

    def test_name_then_unset_fallback(self, mock_manager):
        """测试设置name后取消设置回退到key."""
        db = MockDBModel(id=12, key="original_key")
        char = Character(mock_manager, db)
        
        # 先设置name
        char.name = "临时名字"
        assert char.name == "临时名字"
        
        # 取消设置（设置为空）
        char.name = ""
        
        # 应回退到key
        assert char.name == "original_key"


class TestNameWithSpecialCharacters:
    """特殊字符name测试."""

    def test_name_with_newline(self, mock_manager):
        """测试含换行符的name."""
        db = MockDBModel(id=20, key="test_key")
        char = Character(mock_manager, db)
        
        char.name = "第一行\n第二行"
        
        # 应保留换行符
        assert char.name == "第一行\n第二行"
        assert "\n" in char.name

    def test_name_with_tabs(self, mock_manager):
        """测试含制表符的name."""
        db = MockDBModel(id=21, key="test_key")
        char = Character(mock_manager, db)
        
        char.name = "列1\t列2\t列3"
        
        assert "\t" in char.name

    def test_name_with_html_tags(self, mock_manager):
        """测试含HTML标签的name."""
        db = MockDBModel(id=22, key="test_key")
        char = Character(mock_manager, db)
        
        char.name = "<b>加粗名字</b>"
        
        # 应原样保留
        assert char.name == "<b>加粗名字</b>"
        assert "<b>" in char.name

    def test_name_with_quotes(self, mock_manager):
        """测试含引号的name."""
        db = MockDBModel(id=23, key="test_key")
        char = Character(mock_manager, db)
        
        char.name = '名字有"双引号"和\'单引号\''
        
        assert '"双引号"' in char.name
        assert "'单引号'" in char.name

    def test_name_with_backslash(self, mock_manager):
        """测试含反斜杠的name."""
        db = MockDBModel(id=24, key="test_key")
        char = Character(mock_manager, db)
        
        char.name = "路径\\名称"
        
        assert "\\" in char.name


class TestNameMaxLength:
    """name长度边界测试."""

    def test_very_long_name(self, mock_manager):
        """测试超长name."""
        db = MockDBModel(id=30, key="test_key")
        char = Character(mock_manager, db)
        
        # 1000字符的name
        long_name = "A" * 1000
        char.name = long_name
        
        assert len(char.name) == 1000
        assert char.name == long_name

    def test_single_character_name(self, mock_manager):
        """测试单字符name."""
        db = MockDBModel(id=31, key="test_key")
        char = Character(mock_manager, db)
        
        char.name = "X"
        
        assert char.name == "X"

    def test_two_character_name(self, mock_manager):
        """测试双字符name（中文常见）."""
        db = MockDBModel(id=32, key="test_key")
        char = Character(mock_manager, db)
        
        char.name = "李白"
        
        assert char.name == "李白"


class TestNameTypeSafety:
    """name类型安全测试."""

    def test_name_as_integer(self, mock_manager):
        """测试整数作为name（应转换为字符串）."""
        db = MockDBModel(id=40, key="test_key")
        char = Character(mock_manager, db)
        
        # 直接设置整数到db
        char.db.set("name", 123)
        
        # 取出的值是整数，但逻辑上name应该是字符串
        # 实际行为取决于db.get的实现
        value = char.db.get("name")
        assert value == 123

    def test_name_as_list(self, mock_manager):
        """测试列表作为name."""
        db = MockDBModel(id=41, key="test_key")
        char = Character(mock_manager, db)
        
        # 设置列表（异常情况）
        char.db.set("name", ["a", "b"])
        
        # 列表为真值，不会回退
        value = char.db.get("name")
        assert value == ["a", "b"]
        # 但name属性返回的是列表，可能不是预期行为

    def test_name_as_dict(self, mock_manager):
        """测试字典作为name."""
        db = MockDBModel(id=42, key="test_key")
        char = Character(mock_manager, db)
        
        char.db.set("name", {"cn": "中文名", "en": "English"})
        
        value = char.db.get("name")
        assert value == {"cn": "中文名", "en": "English"}


class TestNamePersistenceConsistency:
    """name持久化一致性测试."""

    def test_name_persists_in_attributes(self, mock_manager):
        """测试name正确存储在attributes中."""
        db = MockDBModel(id=50, key="test_key")
        char = Character(mock_manager, db)
        
        char.name = "持久名字"
        
        # 验证存储
        assert char.db.get("name") == "持久名字"
        
        # 验证读取一致
        assert char.name == char.db.get("name")

    def test_multiple_name_changes(self, mock_manager):
        """测试多次修改name."""
        db = MockDBModel(id=51, key="test_key")
        char = Character(mock_manager, db)
        
        names = ["名字1", "名字2", "名字3", "最终名字"]
        for name in names:
            char.name = name
            assert char.name == name
        
        # 最终值正确
        assert char.name == "最终名字"

    def test_name_after_direct_attributes_modify(self, mock_manager):
        """测试直接修改attributes后name属性正确."""
        db = MockDBModel(id=52, key="test_key")
        char = Character(mock_manager, db)
        
        # 直接修改attributes
        char.db.set("name", "直接设置")
        
        # name属性应读取到
        assert char.name == "直接设置"


class TestNameMemorySharing:
    """name内存共享测试（排查潜在bug）."""

    def test_name_not_shared_between_objects(self, mock_manager):
        """测试不同对象的name不共享."""
        db1 = MockDBModel(id=60, key="key1")
        db2 = MockDBModel(id=61, key="key2")
        
        char1 = Character(mock_manager, db1)
        char2 = Character(mock_manager, db2)
        
        char1.name = "角色A"
        char2.name = "角色B"
        
        # 互不影响
        assert char1.name == "角色A"
        assert char2.name == "角色B"
        
        # 修改一个不影响另一个
        char1.name = "新名字"
        assert char2.name == "角色B"

    def test_name_independence_after_copy_reference(self, mock_manager):
        """测试复制引用后name独立性."""
        db = MockDBModel(id=62, key="test_key")
        char = Character(mock_manager, db)
        char.name = "原名字"
        
        # 模拟可能的问题：如果attributes被共享
        name_ref = char.db.get("name")
        name_ref = "修改引用"  # 这不应影响原值
        
        # 原对象name应不变
        assert char.name == "原名字"
