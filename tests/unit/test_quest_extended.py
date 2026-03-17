"""任务系统单元测试 - 扩展功能.

测试因果点前置条件、扩展功能、任务奖励等.
"""

from __future__ import annotations

from unittest.mock import MagicMock, Mock

import pytest

from src.game.quest.core import (
    CharacterQuestMixin,
    Quest,
    QuestObjective,
    QuestObjectiveType,
    QuestType,
)

class TestQuestKarmaPrerequisites:
    """测试任务因果点前置条件."""

    def test_can_accept_karma_prerequisite_pass(self):
        """测试因果点前置条件满足."""
        quest = Quest(
            key="karma_quest",
            name="因果点任务",
            description="需要善良因果点",
            quest_type=QuestType.MAIN,
            prerequisites={"karma": {"good": ">=10"}}
        )
        
        character = Mock()
        character.level = 10
        character.db = Mock()
        character.db.get = Mock(return_value={"good": 20})
        
        can_accept, reason = quest.can_accept(character)
        
        assert can_accept is True
        assert reason == ""

    def test_can_accept_karma_prerequisite_fail(self):
        """测试因果点前置条件不满足."""
        quest = Quest(
            key="karma_quest",
            name="因果点任务",
            description="需要善良因果点",
            quest_type=QuestType.MAIN,
            prerequisites={"karma": {"good": ">=10"}}
        )
        
        character = Mock()
        character.level = 10
        character.db = Mock()
        character.db.get = Mock(return_value={"good": 5})
        
        can_accept, reason = quest.can_accept(character)
        
        assert can_accept is False
        assert "因果点不满足条件" in reason


class TestCharacterQuestMixinExtended:
    """CharacterQuestMixin 扩展测试."""

    @pytest.fixture
    def character(self):
        """创建带任务Mixin的角色."""
        class TestCharacter(CharacterQuestMixin):
            def __init__(self):
                self._active_quests = {}
                self._completed_quests = []
                # 创建Mock db，同时支持get/set和__getitem__/__setitem__
                self._db = MagicMock()
                self._db.get = MagicMock(side_effect=self._get_db)
                self._db.set = MagicMock(side_effect=self._set_db)
                self._db.__getitem__ = MagicMock(side_effect=self._get_db)
                self._db.__setitem__ = MagicMock(side_effect=self._set_item)
            
            def _get_db(self, key, default=None):
                if key == "active_quests":
                    return self._active_quests
                if key == "completed_quests":
                    return self._completed_quests
                return default
            
            def _set_db(self, key, value):
                if key == "active_quests":
                    self._active_quests = value
                elif key == "completed_quests":
                    self._completed_quests = value
            
            def _set_item(self, key, value):
                self._set_db(key, value)
            
            @property
            def db(self):
                return self._db
            
            @db.setter
            def db(self, value):
                self._db = value
            
            @property
            def level(self):
                return 10
            
            @property
            def menpai(self):
                return "少林"
        
        return TestCharacter()

    @pytest.fixture
    def test_quest(self):
        """创建测试任务."""
        return Quest(
            key="test_quest",
            name="测试任务",
            description="测试",
            quest_type=QuestType.SIDE,
            objectives=[
                QuestObjective(QuestObjectiveType.KILL, "rat", count=3)
            ],
            rewards={"exp": 100}
        )

    @pytest.mark.asyncio
    async def test_accept_quest_can_accept_false(self, character):
        """测试无法接受不满足条件的任务."""
        quest = Quest(
            key="level_quest",
            name="等级任务",
            description="需要高等级",
            quest_type=QuestType.MAIN,
            prerequisites={"level": 100}
        )
        
        success, msg = await character.accept_quest(quest)
        
        assert success is False
        assert "需要等级100" in msg

    @pytest.mark.asyncio
    async def test_update_objective_already_complete(self, character):
        """测试更新已完成目标的进度."""
        quest = Quest(
            key="collect_quest",
            name="收集任务",
            description="收集物品",
            quest_type=QuestType.SIDE,
            objectives=[
                QuestObjective(QuestObjectiveType.COLLECT, "herb", count=1)
            ]
        )
        await character.accept_quest(quest)
        
        # 先完成目标
        await character.update_objective("collect_quest", 0, 1)
        
        # 再次更新已完成的目标
        completed, msg = await character.update_objective("collect_quest", 0, 1)
        
        # 已经完成的不再更新
        assert completed is False
        assert msg == ""

    @pytest.mark.asyncio
    async def test_get_quest_progress_existing(self, character, test_quest):
        """测试获取进行中的任务进度."""
        await character.accept_quest(test_quest)
        
        progress = character.get_quest_progress("test_quest")
        
        assert progress is not None
        assert "objectives" in progress

    def test_get_quest_progress_nonexistent(self, character):
        """测试获取未进行的任务进度."""
        progress = character.get_quest_progress("nonexistent")
        
        assert progress is None

    @pytest.mark.asyncio
    async def test_get_objective_progress_invalid_index(self, character, test_quest):
        """测试获取无效目标索引的进度."""
        await character.accept_quest(test_quest)
        
        result = character.get_objective_progress("test_quest", 10)
        
        assert result == (0, 0)


class TestQuestRewards:
    """测试任务奖励发放."""

    @pytest.fixture
    def character(self):
        """创建带任务Mixin的角色."""
        class TestCharacter(CharacterQuestMixin):
            def __init__(self):
                self._active_quests = {}
                self._completed_quests = []
                self._exp = 0
                self._potential = 0
                self._silver = 0
                self._reputation = 0
                self._db = MagicMock()
                self._db.get = MagicMock(side_effect=self._get_db)
                self._db.set = MagicMock(side_effect=self._set_db)
                self._db.__getitem__ = MagicMock(side_effect=self._get_db)
                self._db.__setitem__ = MagicMock(side_effect=self._set_item)
            
            def _get_db(self, key, default=None):
                if key == "active_quests":
                    return self._active_quests
                if key == "completed_quests":
                    return self._completed_quests
                if key == "potential":
                    return self._potential
                if key == "silver":
                    return self._silver
                if key == "reputation":
                    return self._reputation
                return default
            
            def _set_db(self, key, value):
                if key == "active_quests":
                    self._active_quests = value
                elif key == "completed_quests":
                    self._completed_quests = value
                elif key == "potential":
                    self._potential = value
                elif key == "silver":
                    self._silver = value
                elif key == "reputation":
                    self._reputation = value
            
            def _set_item(self, key, value):
                self._set_db(key, value)
            
            def add_exp(self, amount):
                self._exp += amount
            
            @property
            def db(self):
                return self._db
            
            @db.setter
            def db(self, value):
                self._db = value
            
            @property
            def level(self):
                return 10
            
            @property
            def menpai(self):
                return "少林"
        
        return TestCharacter()

    @pytest.mark.asyncio
    async def test_give_rewards_exp_with_add_exp(self, character):
        """测试发放经验奖励（角色有add_exp方法）."""
        quest = Quest(
            key="exp_quest",
            name="经验任务",
            description="奖励经验",
            quest_type=QuestType.SIDE,
            objectives=[
                QuestObjective(QuestObjectiveType.KILL, "rat", count=1)
            ],
            rewards={"exp": 100}
        )
        await character.accept_quest(quest)
        await character.update_objective("exp_quest", 0, 1)
        
        success, msg = await character.complete_quest("exp_quest", quest)
        
        assert success is True
        assert "经验 +100" in msg
        assert character._exp == 100

    @pytest.mark.asyncio
    async def test_give_rewards_no_add_exp_method(self, character):
        """测试发放经验奖励（角色无add_exp方法）."""
        # 移除add_exp方法
        delattr(type(character), 'add_exp')
        
        quest = Quest(
            key="exp_quest",
            name="经验任务",
            description="奖励经验",
            quest_type=QuestType.SIDE,
            objectives=[
                QuestObjective(QuestObjectiveType.KILL, "rat", count=1)
            ],
            rewards={"exp": 100}
        )
        await character.accept_quest(quest)
        await character.update_objective("exp_quest", 0, 1)
        
        success, msg = await character.complete_quest("exp_quest", quest)
        
        assert success is True
        assert "经验 +100" in msg

    @pytest.mark.asyncio
    async def test_give_rewards_potential(self, character):
        """测试发放潜能奖励."""
        quest = Quest(
            key="potential_quest",
            name="潜能任务",
            description="奖励潜能",
            quest_type=QuestType.SIDE,
            objectives=[
                QuestObjective(QuestObjectiveType.KILL, "rat", count=1)
            ],
            rewards={"potential": 50}
        )
        await character.accept_quest(quest)
        await character.update_objective("potential_quest", 0, 1)
        
        success, msg = await character.complete_quest("potential_quest", quest)
        
        assert success is True
        assert "潜能 +50" in msg

    @pytest.mark.asyncio
    async def test_give_rewards_silver(self, character):
        """测试发放银两奖励."""
        quest = Quest(
            key="silver_quest",
            name="银两任务",
            description="奖励银两",
            quest_type=QuestType.SIDE,
            objectives=[
                QuestObjective(QuestObjectiveType.KILL, "rat", count=1)
            ],
            rewards={"silver": 1000}
        )
        await character.accept_quest(quest)
        await character.update_objective("silver_quest", 0, 1)
        
        success, msg = await character.complete_quest("silver_quest", quest)
        
        assert success is True
        assert "银两 +1000" in msg
        assert character._silver == 1000

    @pytest.mark.asyncio
    async def test_give_rewards_items(self, character):
        """测试发放物品奖励."""
        quest = Quest(
            key="item_quest",
            name="物品任务",
            description="奖励物品",
            quest_type=QuestType.SIDE,
            objectives=[
                QuestObjective(QuestObjectiveType.KILL, "rat", count=1)
            ],
            rewards={"items": [{"key": "sword", "name": "剑"}, {"key": "shield", "name": "盾"}]}
        )
        await character.accept_quest(quest)
        await character.update_objective("item_quest", 0, 1)
        
        success, msg = await character.complete_quest("item_quest", quest)
        
        assert success is True
        assert "获得" in msg

    @pytest.mark.asyncio
    async def test_give_rewards_wuxue(self, character):
        """测试发放武学奖励."""
        quest = Quest(
            key="wuxue_quest",
            name="武学任务",
            description="奖励武学",
            quest_type=QuestType.SIDE,
            objectives=[
                QuestObjective(QuestObjectiveType.KILL, "rat", count=1)
            ],
            rewards={"wuxue": "taichi"}
        )
        await character.accept_quest(quest)
        await character.update_objective("wuxue_quest", 0, 1)
        
        success, msg = await character.complete_quest("wuxue_quest", quest)
        
        assert success is True
        assert "领悟武学" in msg

    @pytest.mark.asyncio
    async def test_give_rewards_reputation(self, character):
        """测试发放声望奖励."""
        quest = Quest(
            key="reputation_quest",
            name="声望任务",
            description="奖励声望",
            quest_type=QuestType.SIDE,
            objectives=[
                QuestObjective(QuestObjectiveType.KILL, "rat", count=1)
            ],
            rewards={"reputation": 50}
        )
        await character.accept_quest(quest)
        await character.update_objective("reputation_quest", 0, 1)
        
        success, msg = await character.complete_quest("reputation_quest", quest)
        
        assert success is True
        assert "声望 +50" in msg
        assert character._reputation == 50

    @pytest.mark.asyncio
    async def test_give_rewards_multiple(self, character):
        """测试发放多种奖励."""
        quest = Quest(
            key="multi_quest",
            name="多重奖励任务",
            description="奖励多种",
            quest_type=QuestType.SIDE,
            objectives=[
                QuestObjective(QuestObjectiveType.KILL, "rat", count=1)
            ],
            rewards={
                "exp": 100,
                "potential": 50,
                "silver": 1000,
                "reputation": 25
            }
        )
        await character.accept_quest(quest)
        await character.update_objective("multi_quest", 0, 1)
        
        success, msg = await character.complete_quest("multi_quest", quest)
        
        assert success is True
        assert "经验 +100" in msg
        assert "潜能 +50" in msg
        assert "银两 +1000" in msg
        assert "声望 +25" in msg

    @pytest.mark.asyncio
    async def test_give_rewards_empty(self, character):
        """测试无奖励时返回空字符串."""
        quest = Quest(
            key="no_reward_quest",
            name="无奖励任务",
            description="没有奖励",
            quest_type=QuestType.SIDE,
            objectives=[
                QuestObjective(QuestObjectiveType.KILL, "rat", count=1)
            ],
            rewards={}
        )
        await character.accept_quest(quest)
        await character.update_objective("no_reward_quest", 0, 1)
        
        success, msg = await character.complete_quest("no_reward_quest", quest)
        
        assert success is True
        assert "任务完成！" in msg
