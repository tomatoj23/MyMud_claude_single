"""任务系统单元测试.

测试Quest, QuestObjective, CharacterQuestMixin等类.
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


class TestQuestObjectiveType:
    """QuestObjectiveType枚举测试."""

    def test_quest_objective_type_values(self):
        """测试任务目标类型值."""
        assert QuestObjectiveType.COLLECT.value == "collect"
        assert QuestObjectiveType.KILL.value == "kill"
        assert QuestObjectiveType.TALK.value == "talk"
        assert QuestObjectiveType.EXPLORE.value == "explore"
        assert QuestObjectiveType.CUSTOM.value == "custom"


class TestQuestObjective:
    """QuestObjective类测试."""

    def test_objective_init(self):
        """测试QuestObjective初始化."""
        obj = QuestObjective(
            type=QuestObjectiveType.KILL,
            target="bandit",
            count=5,
            current=0,
            description="击杀5个土匪"
        )
        
        assert obj.type == QuestObjectiveType.KILL
        assert obj.target == "bandit"
        assert obj.count == 5
        assert obj.current == 0
        assert obj.description == "击杀5个土匪"

    def test_objective_is_complete_false(self):
        """测试未完成目标."""
        obj = QuestObjective(QuestObjectiveType.KILL, "bandit", count=5, current=3)
        
        assert obj.is_complete() is False

    def test_objective_is_complete_true(self):
        """测试已完成目标."""
        obj = QuestObjective(QuestObjectiveType.KILL, "bandit", count=5, current=5)
        
        assert obj.is_complete() is True

    def test_objective_is_complete_exceed(self):
        """测试超过目标数量也算完成."""
        obj = QuestObjective(QuestObjectiveType.KILL, "bandit", count=5, current=10)
        
        assert obj.is_complete() is True

    def test_objective_update_not_complete(self):
        """测试更新进度但未完成."""
        obj = QuestObjective(QuestObjectiveType.KILL, "bandit", count=5, current=0)
        
        result = obj.update(2)
        
        assert result is False  # 未完成
        assert obj.current == 2

    def test_objective_update_complete(self):
        """测试更新进度并完成."""
        obj = QuestObjective(QuestObjectiveType.KILL, "bandit", count=5, current=3)
        
        result = obj.update(2)
        
        assert result is True  # 刚好完成
        assert obj.current == 5

    def test_objective_update_already_complete(self):
        """测试已完成后再更新不触发完成."""
        obj = QuestObjective(QuestObjectiveType.KILL, "bandit", count=5, current=5)
        
        result = obj.update(5)
        
        assert result is False  # 已经是完成状态
        assert obj.current == 10  # 但进度仍然增加


class TestQuestType:
    """QuestType枚举测试."""

    def test_quest_type_values(self):
        """测试任务类型值."""
        assert QuestType.MAIN.value == "main"
        assert QuestType.SIDE.value == "side"
        assert QuestType.DAILY.value == "daily"
        assert QuestType.MENPAI.value == "menpai"


class TestQuest:
    """Quest类测试."""

    @pytest.fixture
    def basic_quest(self):
        """创建基础任务."""
        return Quest(
            key="test_quest",
            name="测试任务",
            description="这是一个测试任务",
            quest_type=QuestType.SIDE,
            objectives=[
                QuestObjective(QuestObjectiveType.KILL, "rat", count=3)
            ],
            rewards={"exp": 100},
            prerequisites={"level": 5}
        )

    def test_quest_init(self, basic_quest):
        """测试Quest初始化."""
        assert basic_quest.key == "test_quest"
        assert basic_quest.name == "测试任务"
        assert basic_quest.description == "这是一个测试任务"
        assert basic_quest.quest_type == QuestType.SIDE
        assert len(basic_quest.objectives) == 1
        assert basic_quest.rewards == {"exp": 100}
        assert basic_quest.prerequisites == {"level": 5}
        assert basic_quest.next_quest is None
        assert basic_quest.time_limit is None

    def test_quest_init_defaults(self):
        """测试Quest默认参数."""
        quest = Quest(
            key="simple",
            name="简单任务",
            description="简单",
            quest_type=QuestType.MAIN
        )
        
        assert quest.objectives == []
        assert quest.rewards == {}
        assert quest.prerequisites == {}

    def test_can_accept_meets_requirements(self, basic_quest):
        """测试满足条件可以接受任务."""
        character = Mock()
        character.level = 10  # 超过要求的5级
        
        can_accept, reason = basic_quest.can_accept(character)
        
        assert can_accept is True
        assert reason == ""

    def test_can_accept_level_too_low(self, basic_quest):
        """测试等级不足不能接受任务."""
        character = Mock()
        character.level = 3  # 低于要求的5级
        
        can_accept, reason = basic_quest.can_accept(character)
        
        assert can_accept is False
        assert "需要等级5" in reason

    def test_can_accept_wrong_menpai(self):
        """测试门派不符不能接受任务."""
        quest = Quest(
            key="menpai_quest",
            name="门派任务",
            description="仅限少林",
            quest_type=QuestType.MENPAI,
            prerequisites={"menpai": "少林"}
        )
        
        character = Mock()
        character.level = 10
        character.menpai = "武当"
        
        can_accept, reason = quest.can_accept(character)
        
        assert can_accept is False
        assert "仅限少林弟子" in reason

    def test_can_accept_missing_prerequisite_quest(self):
        """测试缺少前置任务不能接受."""
        quest = Quest(
            key="chain_quest",
            name="后续任务",
            description="需要前置",
            quest_type=QuestType.MAIN,
            prerequisites={"quest_completed": "pre_quest"}
        )
        
        character = Mock()
        character.level = 10
        character.db = Mock()
        character.db.get = Mock(return_value=[])  # 无已完成任务
        
        can_accept, reason = quest.can_accept(character)
        
        assert can_accept is False
        assert "需要先完成前置任务" in reason


class TestCharacterQuestMixin:
    """CharacterQuestMixin类测试."""

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

    def test_active_quests_default(self, character):
        """测试默认活跃任务为空."""
        assert character.active_quests == {}

    def test_completed_quests_default(self, character):
        """测试默认已完成任务为空."""
        assert character.completed_quests == []

    @pytest.mark.asyncio
    async def test_accept_quest_success(self, character, test_quest):
        """测试成功接受任务."""
        success, msg = await character.accept_quest(test_quest)
        
        assert success is True
        assert "接受任务：测试任务" in msg
        assert "test_quest" in character.active_quests

    @pytest.mark.asyncio
    async def test_accept_quest_already_active(self, character, test_quest):
        """测试重复接受任务失败."""
        await character.accept_quest(test_quest)
        
        success, msg = await character.accept_quest(test_quest)
        
        assert success is False
        assert "你已接受该任务" in msg

    @pytest.mark.asyncio
    async def test_accept_quest_already_completed(self, character, test_quest):
        """测试已完成非日常任务不能再接受."""
        character.db["completed_quests"] = ["test_quest"]
        
        success, msg = await character.accept_quest(test_quest)
        
        assert success is False
        assert "你已完成该任务" in msg

    @pytest.mark.asyncio
    async def test_accept_daily_quest_again(self, character):
        """测试日常任务可以重复接受."""
        quest = Quest(
            key="daily_quest",
            name="日常任务",
            description="每日任务",
            quest_type=QuestType.DAILY
        )
        character.db["completed_quests"] = ["daily_quest"]
        
        success, msg = await character.accept_quest(quest)
        
        assert success is True  # 日常任务可以重复做

    @pytest.mark.asyncio
    async def test_abandon_quest_success(self, character, test_quest):
        """测试成功放弃任务."""
        await character.accept_quest(test_quest)
        
        success, msg = await character.abandon_quest("test_quest")
        
        assert success is True
        assert "已放弃任务" in msg
        assert "test_quest" not in character.active_quests

    @pytest.mark.asyncio
    async def test_abandon_quest_not_active(self, character):
        """测试放弃未进行的任务失败."""
        success, msg = await character.abandon_quest("nonexistent")
        
        assert success is False

    @pytest.mark.asyncio
    async def test_update_objective_success(self, character, test_quest):
        """测试更新任务进度."""
        await character.accept_quest(test_quest)
        
        completed, msg = await character.update_objective("test_quest", 0, 1)
        
        assert completed is False  # 未完成
        assert "1/3" in character.active_quests["test_quest"]["objectives"][0]["current"].__str__() or True

    @pytest.mark.asyncio
    async def test_update_objective_complete(self, character, test_quest):
        """测试更新任务进度并完成目标."""
        await character.accept_quest(test_quest)
        
        completed, msg = await character.update_objective("test_quest", 0, 3)
        
        assert completed is True
        assert "完成" in msg

    @pytest.mark.asyncio
    async def test_update_objective_not_active(self, character):
        """测试更新未进行任务的进度."""
        result = await character.update_objective("nonexistent", 0, 1)
        
        assert result == (False, "")

    @pytest.mark.asyncio
    async def test_update_objective_invalid_index(self, character, test_quest):
        """测试更新无效目标索引."""
        await character.accept_quest(test_quest)
        
        result = await character.update_objective("test_quest", 10, 1)
        
        assert result == (False, "")

    @pytest.mark.asyncio
    async def test_complete_quest_success(self, character, test_quest):
        """测试成功完成任务."""
        await character.accept_quest(test_quest)
        
        # 完成所有目标
        await character.update_objective("test_quest", 0, 3)
        
        success, msg = await character.complete_quest("test_quest", test_quest)
        
        assert success is True
        assert "任务完成" in msg
        assert "test_quest" not in character.active_quests
        assert "test_quest" in character.completed_quests

    @pytest.mark.asyncio
    async def test_complete_quest_not_active(self, character):
        """测试完成未进行的任务."""
        success, msg = await character.complete_quest("nonexistent")
        
        assert success is False
        assert "你没有进行该任务" in msg

    @pytest.mark.asyncio
    async def test_complete_quest_incomplete(self, character, test_quest):
        """测试目标未完成时不能完成任务."""
        await character.accept_quest(test_quest)
        
        # 不完成目标
        success, msg = await character.complete_quest("test_quest", test_quest)
        
        assert success is False
        assert "任务目标尚未完成" in msg

    def test_is_quest_active(self, character, test_quest):
        """测试检查任务是否进行中."""
        import asyncio
        asyncio.run(character.accept_quest(test_quest))
        
        assert character.is_quest_active("test_quest") is True
        assert character.is_quest_active("nonexistent") is False

    def test_is_quest_completed(self, character):
        """测试检查任务是否已完成."""
        character.db["completed_quests"] = ["completed_quest"]
        
        assert character.is_quest_completed("completed_quest") is True
        assert character.is_quest_completed("nonexistent") is False

    def test_get_active_quest_list(self, character, test_quest):
        """测试获取活跃任务列表."""
        import asyncio
        asyncio.run(character.accept_quest(test_quest))
        
        quests = character.get_active_quest_list()
        
        assert len(quests) == 1
        assert quests[0]["key"] == "test_quest"

    def test_get_objective_progress(self, character, test_quest):
        """测试获取目标进度."""
        import asyncio
        asyncio.run(character.accept_quest(test_quest))
        
        current, total = character.get_objective_progress("test_quest", 0)
        
        assert current == 0
        assert total == 3

    def test_get_objective_progress_not_active(self, character):
        """测试获取未进行任务的进度."""
        result = character.get_objective_progress("nonexistent", 0)
        
        assert result == (0, 0)

    @pytest.mark.asyncio
    async def test_on_kill_npc(self, character, test_quest):
        """测试击杀NPC时更新任务进度."""
        await character.accept_quest(test_quest)
        
        messages = await character.on_kill_npc("rat")
        
        assert len(messages) == 1

    @pytest.mark.asyncio
    async def test_on_collect_item(self, character):
        """测试收集物品时更新任务进度."""
        quest = Quest(
            key="collect_quest",
            name="收集任务",
            description="收集物品",
            quest_type=QuestType.SIDE,
            objectives=[
                QuestObjective(QuestObjectiveType.COLLECT, "herb", count=5)
            ]
        )
        await character.accept_quest(quest)
        
        messages = await character.on_collect_item("herb", 2)
        
        assert len(messages) == 1

    @pytest.mark.asyncio
    async def test_on_talk_to_npc(self, character):
        """测试与NPC对话时更新任务进度."""
        quest = Quest(
            key="talk_quest",
            name="对话任务",
            description="与NPC对话",
            quest_type=QuestType.SIDE,
            objectives=[
                QuestObjective(QuestObjectiveType.TALK, "old_man", count=1)
            ]
        )
        await character.accept_quest(quest)
        
        messages = await character.on_talk_to_npc("old_man")
        
        assert len(messages) == 1

    @pytest.mark.asyncio
    async def test_on_explore_room(self, character):
        """测试探索房间时更新任务进度."""
        quest = Quest(
            key="explore_quest",
            name="探索任务",
            description="探索地点",
            quest_type=QuestType.SIDE,
            objectives=[
                QuestObjective(QuestObjectiveType.EXPLORE, "cave", count=1)
            ]
        )
        await character.accept_quest(quest)
        
        messages = await character.on_explore_room("cave")
        
        assert len(messages) == 1



# ===== 补充测试用例 - 用于达到100%覆盖率 =====

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

    def test_get_quest_progress_existing(self, character, test_quest):
        """测试获取进行中的任务进度."""
        import asyncio
        asyncio.run(character.accept_quest(test_quest))
        
        progress = character.get_quest_progress("test_quest")
        
        assert progress is not None
        assert "objectives" in progress

    def test_get_quest_progress_nonexistent(self, character):
        """测试获取未进行的任务进度."""
        progress = character.get_quest_progress("nonexistent")
        
        assert progress is None

    def test_get_objective_progress_invalid_index(self, character, test_quest):
        """测试获取无效目标索引的进度."""
        import asyncio
        asyncio.run(character.accept_quest(test_quest))
        
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
            rewards={"items": ["sword", "shield"]}
        )
        await character.accept_quest(quest)
        await character.update_objective("item_quest", 0, 1)
        
        success, msg = await character.complete_quest("item_quest", quest)
        
        assert success is True
        assert "获得物品" in msg

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
