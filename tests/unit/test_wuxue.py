"""Wuxue 武学系统单元测试."""

from __future__ import annotations

import pytest

from src.game.typeclasses.character import Character
from src.game.typeclasses.wuxue import (
    COUNTER_BONUS,
    COUNTERED_PENALTY,
    Kungfu,
    Move,
    MoveEffectResult,
    WuxueType,
    get_counter_modifier,
)


class TestWuxueType:
    """武学类型测试."""

    def test_wuxue_type_values(self):
        """测试武学类型值."""
        assert WuxueType.QUAN.value == "quan"
        assert WuxueType.JIAN.value == "jian"
        assert WuxueType.NEIGONG.value == "neigong"

    def test_wuxue_type_names(self):
        """测试武学类型名称."""
        from src.game.typeclasses.wuxue import WUXUE_TYPE_NAMES

        assert WUXUE_TYPE_NAMES[WuxueType.QUAN] == "拳法"
        assert WUXUE_TYPE_NAMES[WuxueType.JIAN] == "剑法"


class TestMove:
    """招式测试."""

    def test_move_creation(self):
        """测试创建招式."""
        move = Move(
            key="test_move",
            name="测试招式",
            wuxue_type=WuxueType.QUAN,
            mp_cost=10,
            ep_cost=5,
        )
        assert move.key == "test_move"
        assert move.name == "测试招式"
        assert move.wuxue_type == WuxueType.QUAN
        assert move.mp_cost == 10
        assert move.ep_cost == 5

    def test_move_default_values(self):
        """测试招式默认值."""
        move = Move(key="test", name="测试", wuxue_type=WuxueType.QUAN)
        assert move.mp_cost == 10
        assert move.ep_cost == 5
        assert move.cooldown == 0.0
        assert move.counters == []

    def test_move_counters(self):
        """测试招式克制关系."""
        move = Move(
            key="test",
            name="测试",
            wuxue_type=WuxueType.QUAN,
            counters=[WuxueType.ZHANG, WuxueType.ZHI],
        )
        assert WuxueType.ZHANG in move.counters
        assert WuxueType.ZHI in move.counters


class TestMoveEffectResult:
    """招式效果结果测试."""

    def test_default_values(self):
        """测试默认值."""
        result = MoveEffectResult()
        assert result.damage == 0
        assert result.heal == 0
        assert result.effects == []
        assert result.messages == []

    def test_custom_values(self):
        """测试自定义值."""
        result = MoveEffectResult(
            damage=100, heal=20, effects=["stun"], messages=["命中！"], mp_cost=10
        )
        assert result.damage == 100
        assert result.heal == 20
        assert "stun" in result.effects
        assert "命中！" in result.messages


class TestKungfu:
    """武功测试."""

    def test_kungfu_creation(self):
        """测试创建武功."""
        move1 = Move(key="m1", name="招式1", wuxue_type=WuxueType.QUAN)
        move2 = Move(key="m2", name="招式2", wuxue_type=WuxueType.QUAN)

        kungfu = Kungfu(
            key="luohanquan",
            name="罗汉拳",
            menpai="少林",
            wuxue_type=WuxueType.QUAN,
            moves=[move1, move2],
            requirements={"level": 5, "wuxing": 15},
        )

        assert kungfu.key == "luohanquan"
        assert kungfu.name == "罗汉拳"
        assert kungfu.menpai == "少林"
        assert len(kungfu.moves) == 2

    def test_get_move(self):
        """测试获取招式."""
        move1 = Move(key="m1", name="招式1", wuxue_type=WuxueType.QUAN)
        move2 = Move(key="m2", name="招式2", wuxue_type=WuxueType.QUAN)

        kungfu = Kungfu(
            key="test",
            name="测试武功",
            menpai="少林",
            wuxue_type=WuxueType.QUAN,
            moves=[move1, move2],
        )

        found = kungfu.get_move("m1")
        assert found == move1

        not_found = kungfu.get_move("nonexistent")
        assert not_found is None


from src.game.typeclasses.wuxue import CharacterWuxueMixin


class MockCharacter(CharacterWuxueMixin):
    """模拟角色."""

    def __init__(self):
        self.level = 1
        self.menpai = None
        self.wuxing = 15
        self._learned_wuxue = {}
        self._db_model = type('DBModel', (), {'attributes': {}})()
        self._is_dirty = False

    @property
    def learned_wuxue(self):
        return self._learned_wuxue

    @learned_wuxue.setter
    def learned_wuxue(self, value):
        self._learned_wuxue = value

    def db_get(self, key, default=None):
        return getattr(self._db_model, 'attributes', {}).get(key, default)

    def db_set(self, key, value):
        if not hasattr(self._db_model, 'attributes'):
            self._db_model.attributes = {}
        self._db_model.attributes[key] = value

    # 模拟 db 属性
    class MockDB:
        def __init__(self, parent):
            self._parent = parent

        def get(self, key, default=None):
            return self._parent.db_get(key, default)

        def set(self, key, value):
            self._parent.db_set(key, value)

    @property
    def db(self):
        return self.MockDB(self)


class TestKungfuCanLearn:
    """武功学习条件测试."""

    def test_can_learn_meets_all_requirements(self):
        """测试满足所有条件可以学习."""
        kungfu = Kungfu(
            key="test",
            name="测试",
            menpai="少林",
            wuxue_type=WuxueType.QUAN,
            requirements={"level": 5},
        )

        char = MockCharacter()
        char.level = 10
        char.menpai = "少林"

        can_learn, reason = kungfu.can_learn(char)
        assert can_learn
        assert reason == ""

    def test_cannot_learn_wrong_menpai(self):
        """测试门派不符不能学习."""
        kungfu = Kungfu(
            key="test",
            name="测试",
            menpai="少林",
            wuxue_type=WuxueType.QUAN,
        )

        char = MockCharacter()
        char.menpai = "武当"

        can_learn, reason = kungfu.can_learn(char)
        assert not can_learn
        assert "仅限" in reason

    def test_cannot_learn_level_too_low(self):
        """测试等级不足不能学习."""
        kungfu = Kungfu(
            key="test",
            name="测试",
            menpai="少林",
            wuxue_type=WuxueType.QUAN,
            requirements={"level": 10},
        )

        char = MockCharacter()
        char.level = 5
        char.menpai = "少林"

        can_learn, reason = kungfu.can_learn(char)
        assert not can_learn
        assert "等级不足" in reason

    def test_cannot_learn_wuxing_too_low(self):
        """测试悟性不足不能学习."""
        kungfu = Kungfu(
            key="test",
            name="测试",
            menpai="少林",
            wuxue_type=WuxueType.QUAN,
            requirements={"wuxing": 20},
        )

        char = MockCharacter()
        char.wuxing = 15
        char.menpai = "少林"

        can_learn, reason = kungfu.can_learn(char)
        assert not can_learn
        assert "悟性不足" in reason


class TestCounterMatrix:
    """克制关系测试."""

    def test_counter_bonus(self):
        """测试克制加成."""
        modifier = get_counter_modifier(WuxueType.QUAN, WuxueType.ZHANG)
        assert modifier == 1 + COUNTER_BONUS

    def test_countered_penalty(self):
        """测试被克制减成."""
        modifier = get_counter_modifier(WuxueType.ZHANG, WuxueType.QUAN)
        assert modifier == 1 + COUNTERED_PENALTY

    def test_no_counter_no_modifier(self):
        """测试无克制关系时无修正."""
        modifier = get_counter_modifier(WuxueType.QUAN, WuxueType.JIAN)
        assert modifier == 1.0

    def test_neigong_no_counter(self):
        """测试内功无克制关系."""
        modifier = get_counter_modifier(WuxueType.NEIGONG, WuxueType.QUAN)
        assert modifier == 1.0


class TestCharacterWuxueMixin:
    """角色武学管理测试."""

    def test_default_learned_wuxue_empty(self):
        """测试默认没有学过武功."""
        char = MockCharacter()
        assert char.wuxue_learned == {}

    def test_has_learned(self):
        """测试检查是否学过武功."""
        char = MockCharacter()
        char.wuxue_learned = {"luohanquan": {"level": 1}}
        assert char.wuxue_has_learned("luohanquan")
        assert not char.wuxue_has_learned("nonexistent")

    def test_get_wuxue_level(self):
        """测试获取武功层数."""
        char = MockCharacter()
        char.wuxue_learned = {"luohanquan": {"level": 3}}
        assert char.wuxue_get_level("luohanquan") == 3
        assert char.wuxue_get_level("nonexistent") == 0

    def test_get_move_mastery(self):
        """测试获取招式熟练度."""
        char = MockCharacter()
        char.wuxue_learned = {
            "luohanquan": {"moves": {"move1": 50, "move2": 30}}
        }
        assert char.wuxue_get_move_mastery("luohanquan", "move1") == 50
        assert char.wuxue_get_move_mastery("luohanquan", "nonexistent") == 0

    def test_get_total_mastery(self):
        """测试获取武功总熟练度."""
        char = MockCharacter()
        char.wuxue_learned = {
            "luohanquan": {"moves": {"move1": 50, "move2": 30}}
        }
        assert char.wuxue_get_total_mastery("luohanquan") == 80

    def test_calculate_practice_gain(self):
        """测试计算练习收益."""
        from src.game.typeclasses.wuxue import CharacterWuxueMixin

        char = MockCharacter()
        char.wuxing = 18
        # 基础10 + 悟性/3 = 10 + 6 = 16
        gain = CharacterWuxueMixin._wuxue_calc_practice_gain(char)
        assert gain == 16

    def test_check_wuxue_level_up(self):
        """测试检查武功升级条件."""
        from src.game.typeclasses.wuxue import CharacterWuxueMixin

        char = MockCharacter()
        # 当前1层，需要100熟练度才能升到2层
        kungfu_data = {"level": 1, "moves": {"m1": 60, "m2": 40}}
        should_level_up = CharacterWuxueMixin._wuxue_check_level_up(char, kungfu_data)
        assert should_level_up  # 总熟练度100，刚好达到

    def test_check_wuxue_not_level_up(self):
        """测试不满足升级条件."""
        from src.game.typeclasses.wuxue import CharacterWuxueMixin

        char = MockCharacter()
        kungfu_data = {"level": 1, "moves": {"m1": 30, "m2": 40}}
        should_level_up = CharacterWuxueMixin._wuxue_check_level_up(char, kungfu_data)
        assert not should_level_up  # 总熟练度70，不够100
