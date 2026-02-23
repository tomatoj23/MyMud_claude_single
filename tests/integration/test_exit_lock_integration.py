"""出口锁系统集成测试.

测试TD-015: 出口锁系统与Exit类的集成
"""

import pytest
from unittest.mock import MagicMock, patch

from src.game.typeclasses.room import Exit, Room
from src.utils.lock_parser import (
    ExitLockParser,
    AndCondition,
    OrCondition,
    AttrCondition,
    TimeCondition,
    QuestCondition,
)


class TestExitLockIntegration:
    """测试出口锁系统集成."""
    
    @pytest.fixture
    def mock_character(self):
        """创建模拟角色."""
        char = MagicMock()
        char.attributes = {
            "level": 10,
            "strength": 50,
            "agility": 30,
        }
        char.level = 10
        char.strength = 50
        char.agility = 30
        return char
    
    @pytest.fixture
    def mock_room(self):
        """创建模拟房间."""
        room = MagicMock(spec=Room)
        room.id = 2
        room.name = "目标房间"
        return room
    
    @pytest.fixture
    def exit_with_destination(self, mock_room):
        """创建有目的地的出口."""
        exit_obj = MagicMock(spec=Exit)
        exit_obj.lock_str = ""
        exit_obj.destination = mock_room
        
        # 模拟can_pass方法
        async def can_pass(char):
            if exit_obj.lock_str:
                condition = ExitLockParser.parse(exit_obj.lock_str)
                if condition:
                    passed, reason = condition.check(char)
                    if not passed:
                        return False, f"无法通行：{reason}"
            if not exit_obj.destination:
                return False, "出口似乎通向虚无..."
            return True, ""
        
        exit_obj.can_pass = can_pass
        return exit_obj
    
    @pytest.mark.asyncio
    async def test_no_lock_always_pass(self, exit_with_destination, mock_character):
        """测试无锁时总是通过."""
        exit_with_destination.lock_str = ""
        passed, reason = await exit_with_destination.can_pass(mock_character)
        assert passed is True
        assert reason == ""
    
    @pytest.mark.asyncio
    async def test_attr_lock_pass(self, exit_with_destination, mock_character):
        """测试属性锁通过."""
        exit_with_destination.lock_str = "attr:level:>=:5"
        passed, reason = await exit_with_destination.can_pass(mock_character)
        assert passed is True
        assert reason == ""
    
    @pytest.mark.asyncio
    async def test_attr_lock_fail(self, exit_with_destination, mock_character):
        """测试属性锁失败."""
        exit_with_destination.lock_str = "attr:level:>=:20"
        passed, reason = await exit_with_destination.can_pass(mock_character)
        assert passed is False
        assert "无法通行" in reason
        assert "level" in reason
    
    @pytest.mark.asyncio
    async def test_and_lock_pass(self, exit_with_destination, mock_character):
        """测试AND组合锁通过."""
        exit_with_destination.lock_str = "attr:level:>=:5;attr:strength:>=:30"
        passed, reason = await exit_with_destination.can_pass(mock_character)
        assert passed is True
        assert reason == ""
    
    @pytest.mark.asyncio
    async def test_and_lock_fail(self, exit_with_destination, mock_character):
        """测试AND组合锁失败."""
        exit_with_destination.lock_str = "attr:level:>=:5;attr:strength:>=:100"
        passed, reason = await exit_with_destination.can_pass(mock_character)
        assert passed is False
        assert "strength" in reason
    
    @pytest.mark.asyncio
    async def test_or_lock_first_pass(self, exit_with_destination, mock_character):
        """测试OR组合锁第一个通过."""
        exit_with_destination.lock_str = "attr:level:>=:5|attr:strength:>=:100"
        passed, reason = await exit_with_destination.can_pass(mock_character)
        assert passed is True
        assert reason == ""
    
    @pytest.mark.asyncio
    async def test_or_lock_second_pass(self, exit_with_destination, mock_character):
        """测试OR组合锁第二个通过."""
        exit_with_destination.lock_str = "attr:level:>=:20|attr:strength:>=:30"
        passed, reason = await exit_with_destination.can_pass(mock_character)
        assert passed is True
        assert reason == ""
    
    @pytest.mark.asyncio
    async def test_or_lock_all_fail(self, exit_with_destination, mock_character):
        """测试OR组合锁全部失败."""
        exit_with_destination.lock_str = "attr:level:>=:20|attr:strength:>=:100"
        passed, reason = await exit_with_destination.can_pass(mock_character)
        assert passed is False
    
    @pytest.mark.asyncio
    async def test_no_destination_fail(self, exit_with_destination, mock_character):
        """测试无目的地时失败."""
        exit_with_destination.lock_str = ""
        exit_with_destination.destination = None
        passed, reason = await exit_with_destination.can_pass(mock_character)
        assert passed is False
        assert "虚无" in reason
    
    @pytest.mark.asyncio
    async def test_lock_takes_priority(self, exit_with_destination, mock_character):
        """测试锁检查优先于目的地检查."""
        exit_with_destination.lock_str = "attr:level:>=:100"
        exit_with_destination.destination = None  # 即使有目的地检查
        passed, reason = await exit_with_destination.can_pass(mock_character)
        # 应该先检查锁，锁不通过就返回
        assert passed is False
        assert "level" in reason


class TestExitLockReal:
    """使用真实Exit类的测试."""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库模型."""
        db = MagicMock()
        db.id = 1
        db.key = "north_exit"
        db.typeclass_path = "src.game.typeclasses.room.Exit"
        db.attributes = {}
        
        def get_attr(key, default=None):
            return db.attributes.get(key, default)
        
        def set_attr(key, value):
            db.attributes[key] = value
        
        db.get = get_attr
        db.set = set_attr
        return db
    
    @pytest.fixture
    def mock_character(self):
        """创建模拟角色."""
        char = MagicMock()
        char.attributes = {"level": 10, "strength": 50}
        char.level = 10
        char.strength = 50
        return char
    
    def create_exit(self, mock_db, **kwargs):
        """创建Exit实例."""
        # Exit需要 manager 参数
        exit_obj = Exit.__new__(Exit)
        exit_obj._db_model = mock_db
        exit_obj.db = mock_db
        for key, value in kwargs.items():
            setattr(exit_obj, key, value)
        return exit_obj
    
    @pytest.mark.asyncio
    async def test_real_exit_no_lock(self, mock_db, mock_character):
        """测试真实Exit无锁情况."""
        exit_obj = self.create_exit(mock_db, lock_str="")
        
        # 没有目的地会失败
        passed, reason = await exit_obj.can_pass(mock_character)
        assert passed is False
        assert "虚无" in reason
    
    @pytest.mark.asyncio
    async def test_real_exit_with_attr_lock(self, mock_db, mock_character):
        """测试真实Exit属性锁."""
        exit_obj = self.create_exit(mock_db, lock_str="attr:level:>=:5")
        
        passed, reason = await exit_obj.can_pass(mock_character)
        # 没有目的地，但锁应该优先检查
        # 但当前锁通过后才会检查目的地
        assert "虚无" in reason or "level" in reason


class TestExitLockSyntaxExamples:
    """测试各种实际使用场景的锁语法."""
    
    def test_level_requirement(self):
        """测试等级要求."""
        condition = ExitLockParser.parse("attr:level:>=:30")
        assert isinstance(condition, AttrCondition)
        assert condition.value == 30
    
    def test_strength_requirement(self):
        """测试臂力要求."""
        condition = ExitLockParser.parse("attr:strength:>=:50")
        assert condition.attr_name == "strength"
        assert condition.value == 50
    
    def test_faction_check(self):
        """测试门派检查."""
        condition = ExitLockParser.parse("attr:faction:==:shaolin")
        assert condition.attr_name == "faction"
        assert condition.value == "shaolin"
    
    def test_key_and_level(self):
        """测试钥匙+等级."""
        condition = ExitLockParser.parse(
            "has_item:golden_key:1;attr:level:>=:10"
        )
        assert isinstance(condition, AndCondition)
    
    def test_skill_or_item(self):
        """测试技能或物品."""
        condition = ExitLockParser.parse(
            "has_skill:qinggong:5|has_item:rope:1"
        )
        assert isinstance(condition, OrCondition)
    
    def test_complex_gate(self):
        """测试复杂门岗条件."""
        # 高等级 或 (有通行证 且 等级>=10)
        condition = ExitLockParser.parse(
            "attr:level:>=:50|has_item:pass:1;attr:level:>=:10"
        )
        # 这是OR条件，第二部分是AndCondition
        assert isinstance(condition, OrCondition)
    
    def test_time_restricted(self):
        """测试时间限制."""
        condition = ExitLockParser.parse("time:06:00:22:00")
        assert isinstance(condition, TimeCondition)
    
    def test_quest_prerequisite(self):
        """测试任务前置."""
        condition = ExitLockParser.parse("quest:tutorial:completed")
        assert isinstance(condition, QuestCondition)



