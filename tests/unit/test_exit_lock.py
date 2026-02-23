"""出口锁系统单元测试.

测试TD-015: 出口锁系统
"""

import pytest
from unittest.mock import MagicMock

from src.utils.lock_parser import (
    ExitLockParser,
    LockError,
    HasItemCondition,
    HasSkillCondition,
    AttrCondition,
    TimeCondition,
    QuestCondition,
    AndCondition,
    OrCondition,
)


class TestExitLockParser:
    """测试锁解析器."""
    
    def test_parse_empty_string(self):
        """测试空字符串返回None."""
        assert ExitLockParser.parse(None) is None
        assert ExitLockParser.parse("") is None
        assert ExitLockParser.parse("   ") is None
    
    def test_parse_has_item(self):
        """测试解析has_item条件."""
        condition = ExitLockParser.parse("has_item:golden_key:1")
        assert isinstance(condition, HasItemCondition)
        assert condition.item_key == "golden_key"
        assert condition.quantity == 1
    
    def test_parse_has_skill(self):
        """测试解析has_skill条件."""
        condition = ExitLockParser.parse("has_skill:qinggong:5")
        assert isinstance(condition, HasSkillCondition)
        assert condition.skill_key == "qinggong"
        assert condition.level == 5
    
    def test_parse_attr_int(self):
        """测试解析属性条件（整数）."""
        condition = ExitLockParser.parse("attr:strength:>=:50")
        assert isinstance(condition, AttrCondition)
        assert condition.attr_name == "strength"
        assert condition.operator == ">="
        assert condition.value == 50
        assert isinstance(condition.value, int)
    
    def test_parse_attr_float(self):
        """测试解析属性条件（浮点数）."""
        condition = ExitLockParser.parse("attr:health:>:50.5")
        assert isinstance(condition, AttrCondition)
        assert condition.attr_name == "health"
        assert condition.operator == ">"
        assert condition.value == 50.5
        assert isinstance(condition.value, float)
    
    def test_parse_attr_string(self):
        """测试解析属性条件（字符串）."""
        condition = ExitLockParser.parse("attr:name:==:hero")
        assert isinstance(condition, AttrCondition)
        assert condition.attr_name == "name"
        assert condition.operator == "=="
        assert condition.value == "hero"
    
    def test_parse_attr_all_operators(self):
        """测试解析所有属性操作符."""
        operators = ["==", "!=", "<", "<=", ">", ">="]
        for op in operators:
            condition = ExitLockParser.parse(f"attr:level:{op}:10")
            assert condition.operator == op
    
    def test_parse_time(self):
        """测试解析时间条件."""
        condition = ExitLockParser.parse("time:08:00:18:00")
        assert isinstance(condition, TimeCondition)
        assert condition.start_time == "08:00"
        assert condition.end_time == "18:00"
    
    def test_parse_quest(self):
        """测试解析任务条件."""
        condition = ExitLockParser.parse("quest:main_quest:completed")
        assert isinstance(condition, QuestCondition)
        assert condition.quest_key == "main_quest"
        assert condition.status == "completed"
    
    def test_parse_and_condition(self):
        """测试解析AND组合条件."""
        condition = ExitLockParser.parse("has_item:key:1;attr:level:>=:10")
        assert isinstance(condition, AndCondition)
        assert len(condition.conditions) == 2
        assert isinstance(condition.conditions[0], HasItemCondition)
        assert isinstance(condition.conditions[1], AttrCondition)
    
    def test_parse_or_condition(self):
        """测试解析OR组合条件."""
        condition = ExitLockParser.parse("has_item:key:1|has_skill:lockpicking:3")
        assert isinstance(condition, OrCondition)
        assert len(condition.conditions) == 2
    
    def test_parse_complex_condition(self):
        """测试解析复杂组合条件."""
        # AND和OR混合（先分OR，再处理各部分的AND）
        condition = ExitLockParser.parse(
            "has_item:pass:1;attr:level:>=:10|has_skill:stealth:5"
        )
        assert isinstance(condition, OrCondition)
        assert len(condition.conditions) == 2
        # 第二部分应该是单个条件，不是AndCondition
        assert isinstance(condition.conditions[1], HasSkillCondition)
    
    def test_parse_invalid_format(self):
        """测试解析无效格式抛出异常."""
        with pytest.raises(LockError):
            ExitLockParser.parse("invalid_format")
        
        with pytest.raises(LockError):
            ExitLockParser.parse("unknown:type:value")
    
    def test_parse_whitespace_handling(self):
        """测试空白字符处理."""
        condition = ExitLockParser.parse("  has_item:key:1  ")
        assert isinstance(condition, HasItemCondition)
        assert condition.item_key == "key"


class TestAttrCondition:
    """测试属性条件."""
    
    def create_mock_character(self, **attrs):
        """创建模拟角色."""
        char = MagicMock()
        char.attributes = attrs
        for key, value in attrs.items():
            setattr(char, key, value)
        return char
    
    def test_check_equal_int_pass(self):
        """测试整数相等检查通过."""
        char = self.create_mock_character(level=10)
        condition = AttrCondition("level", "==", 10)
        passed, reason = condition.check(char)
        assert passed is True
        assert reason == ""
    
    def test_check_equal_int_fail(self):
        """测试整数相等检查失败."""
        char = self.create_mock_character(level=5)
        condition = AttrCondition("level", "==", 10)
        passed, reason = condition.check(char)
        assert passed is False
        assert "level" in reason
    
    def test_check_greater_equal_pass(self):
        """测试大于等于检查通过."""
        char = self.create_mock_character(strength=50)
        condition = AttrCondition("strength", ">=", 30)
        passed, reason = condition.check(char)
        assert passed is True
    
    def test_check_greater_equal_exact(self):
        """测试大于等于检查边界值."""
        char = self.create_mock_character(strength=50)
        condition = AttrCondition("strength", ">=", 50)
        passed, reason = condition.check(char)
        assert passed is True
    
    def test_check_greater_pass(self):
        """测试大于检查通过."""
        char = self.create_mock_character(agility=20)
        condition = AttrCondition("agility", ">", 10)
        passed, reason = condition.check(char)
        assert passed is True
    
    def test_check_less_pass(self):
        """测试小于检查通过."""
        char = self.create_mock_character(weight=50)
        condition = AttrCondition("weight", "<", 100)
        passed, reason = condition.check(char)
        assert passed is True
    
    def test_check_not_equal_pass(self):
        """测试不等于检查通过."""
        char = self.create_mock_character(status="active")
        condition = AttrCondition("status", "!=", "dead")
        passed, reason = condition.check(char)
        assert passed is True
    
    def test_check_missing_attribute(self):
        """测试缺失属性."""
        char = self.create_mock_character()
        condition = AttrCondition("unknown_attr", ">=", 10)
        passed, reason = condition.check(char)
        # 缺失属性应该返回0，不满足>=10
        assert passed is False
    
    def test_check_float_comparison(self):
        """测试浮点数比较."""
        char = self.create_mock_character(health=75.5)
        condition = AttrCondition("health", ">=", 50.0)
        passed, reason = condition.check(char)
        assert passed is True
    
    def test_check_string_equality(self):
        """测试字符串相等."""
        char = self.create_mock_character(faction="shaolin")
        condition = AttrCondition("faction", "==", "shaolin")
        passed, reason = condition.check(char)
        assert passed is True
    
    def test_str_representation(self):
        """测试字符串表示."""
        condition = AttrCondition("level", ">=", 10)
        assert "level" in str(condition)
        assert ">=" in str(condition)
        assert "10" in str(condition)


class TestAndCondition:
    """测试AND组合条件."""
    
    def create_mock_character(self, **attrs):
        """创建模拟角色."""
        char = MagicMock()
        char.attributes = attrs
        for key, value in attrs.items():
            setattr(char, key, value)
        return char
    
    def test_all_pass(self):
        """测试所有条件通过."""
        char = self.create_mock_character(level=10, strength=50)
        condition = AndCondition([
            AttrCondition("level", ">=", 5),
            AttrCondition("strength", ">=", 30),
        ])
        passed, reason = condition.check(char)
        assert passed is True
        assert reason == ""
    
    def test_first_fail(self):
        """测试第一个条件失败."""
        char = self.create_mock_character(level=3, strength=50)
        condition = AndCondition([
            AttrCondition("level", ">=", 5),
            AttrCondition("strength", ">=", 30),
        ])
        passed, reason = condition.check(char)
        assert passed is False
        assert "level" in reason
    
    def test_second_fail(self):
        """测试第二个条件失败."""
        char = self.create_mock_character(level=10, strength=20)
        condition = AndCondition([
            AttrCondition("level", ">=", 5),
            AttrCondition("strength", ">=", 30),
        ])
        passed, reason = condition.check(char)
        assert passed is False
        assert "strength" in reason
    
    def test_str_representation(self):
        """测试字符串表示."""
        condition = AndCondition([
            AttrCondition("level", ">=", 10),
            AttrCondition("strength", ">=", 50),
        ])
        text = str(condition)
        assert "level" in text
        assert "strength" in text
        assert "且" in text


class TestOrCondition:
    """测试OR组合条件."""
    
    def create_mock_character(self, **attrs):
        """创建模拟角色."""
        char = MagicMock()
        char.attributes = attrs
        for key, value in attrs.items():
            setattr(char, key, value)
        return char
    
    def test_first_pass(self):
        """测试第一个条件通过."""
        char = self.create_mock_character(level=10, strength=20)
        condition = OrCondition([
            AttrCondition("level", ">=", 5),
            AttrCondition("strength", ">=", 30),
        ])
        passed, reason = condition.check(char)
        assert passed is True
        assert reason == ""
    
    def test_second_pass(self):
        """测试第二个条件通过."""
        char = self.create_mock_character(level=3, strength=50)
        condition = OrCondition([
            AttrCondition("level", ">=", 5),
            AttrCondition("strength", ">=", 30),
        ])
        passed, reason = condition.check(char)
        assert passed is True
        assert reason == ""
    
    def test_all_fail(self):
        """测试所有条件失败."""
        char = self.create_mock_character(level=3, strength=20)
        condition = OrCondition([
            AttrCondition("level", ">=", 5),
            AttrCondition("strength", ">=", 30),
        ])
        passed, reason = condition.check(char)
        assert passed is False
        assert "level" in reason
        assert "strength" in reason
        assert "或" in reason
    
    def test_str_representation(self):
        """测试字符串表示."""
        condition = OrCondition([
            AttrCondition("level", ">=", 10),
            AttrCondition("strength", ">=", 50),
        ])
        text = str(condition)
        assert "level" in text
        assert "strength" in text
        assert "或" in text


class TestConditionStr:
    """测试条件的字符串表示."""
    
    def test_has_item_str(self):
        """测试has_item字符串表示."""
        cond = HasItemCondition("golden_key", 1)
        assert "golden_key" in str(cond)
        assert "x1" in str(cond)
    
    def test_has_skill_str(self):
        """测试has_skill字符串表示."""
        cond = HasSkillCondition("qinggong", 5)
        assert "qinggong" in str(cond)
        assert "等级>=5" in str(cond)
    
    def test_time_str(self):
        """测试time字符串表示."""
        cond = TimeCondition("08:00", "18:00")
        assert "08:00" in str(cond)
        assert "18:00" in str(cond)
    
    def test_quest_str(self):
        """测试quest字符串表示."""
        cond = QuestCondition("main_quest", "completed")
        assert "main_quest" in str(cond)
        assert "已完成" in str(cond)
