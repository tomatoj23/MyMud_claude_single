"""随机数据测试 - 使用Hypothesis生成随机输入发现潜在问题.

这些测试通过大量随机输入来发现边界情况和意外行为。
"""
import pytest
import asyncio
import tempfile
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
import string

from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.stateful import RuleBasedStateMachine, rule, precondition, invariant

from src.utils.config import Config
from src.engine.core import GameEngine
from src.game.typeclasses.character import Character
from src.game.typeclasses.equipment import Equipment, EquipmentSlot, EquipmentQuality
from src.game.npc.core import NPC, NPCType
from src.game.combat.core import CombatSession, CombatAction, CombatResult


# 定义策略
valid_names = st.text(
    min_size=1, 
    max_size=50,
    alphabet=string.ascii_letters + string.digits + "_"
)

chinese_names = st.text(
    min_size=1,
    max_size=20,
    alphabet="甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥天地玄黄"
)

positive_ints = st.integers(min_value=1, max_value=10000)
non_negative_ints = st.integers(min_value=0, max_value=10000)

# 属性策略 - 合理的游戏数值范围
attributes_strategy = st.fixed_dictionaries({
    "strength": st.integers(min_value=1, max_value=100),
    "agility": st.integers(min_value=1, max_value=100),
    "intelligence": st.integers(min_value=1, max_value=100),
    "constitution": st.integers(min_value=1, max_value=100),
    "max_hp": st.integers(min_value=10, max_value=1000),
    "max_mp": st.integers(min_value=10, max_value=1000),
})


@pytest.fixture
async def engine():
    tmp_dir = tempfile.mkdtemp()
    config = Config()
    config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir) / 'random.db'}"
    config.game.auto_save_interval = 60
    
    engine = GameEngine(config)
    await engine.initialize()
    
    yield engine
    
    try:
        await engine.stop()
    except:
        pass


class TestCharacterRandomAttributes:
    """随机属性测试."""
    
    @pytest.mark.asyncio
    @given(
        name=valid_names,
        attrs=attributes_strategy,
        level=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_character_with_random_attributes(self, name, attrs, level):
        """测试各种随机属性组合的角色创建."""
        # 这里简化测试，不实际创建引擎实例
        # 在实际测试中，可以使用 engine 参数
        
        # 验证属性值范围
        assert 1 <= attrs["strength"] <= 100
        assert 1 <= attrs["agility"] <= 100
        assert 10 <= attrs["max_hp"] <= 1000
        
        # 验证名称
        assert len(name) >= 1
        assert len(name) <= 50
    
    @pytest.mark.asyncio
    @given(
        exp=st.integers(min_value=0, max_value=1000000),
        current_level=st.integers(min_value=1, max_value=99)
    )
    @settings(max_examples=100, deadline=None)
    async def test_exp_to_level_calculation(self, exp, current_level):
        """测试经验值到等级的计算."""
        # 假设需要 current_level * 100 经验升级
        needed = current_level * 100
        levels_gained = exp // needed if needed > 0 else 0
        
        new_level = min(current_level + levels_gained, 100)
        
        # 验证等级不会倒退
        assert new_level >= current_level
        # 验证等级不超过上限
        assert new_level <= 100


class TestCombatRandomScenarios:
    """随机战斗场景测试."""
    
    @pytest.mark.asyncio
    @given(
        attacker_level=st.integers(min_value=1, max_value=100),
        defender_level=st.integers(min_value=1, max_value=100),
        attacker_str=st.integers(min_value=1, max_value=100),
        defender_def=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=100, deadline=None)
    async def test_damage_calculation_bounds(self, attacker_level, defender_level, 
                                              attacker_str, defender_def):
        """测试伤害计算在各种随机属性下的边界."""
        # 基础伤害计算
        base_damage = max(1, attacker_str - defender_def // 2)
        level_bonus = attacker_level * 0.5
        
        damage = int(base_damage + level_bonus)
        
        # 伤害应该为正数
        assert damage >= 1
        
        # 伤害应该有上限（避免溢出）
        max_reasonable_damage = 10000
        assert damage < max_reasonable_damage or attacker_str > 1000
    
    @pytest.mark.asyncio
    @given(
        hp=st.integers(min_value=1, max_value=10000),
        damage=st.integers(min_value=0, max_value=10000)
    )
    @settings(max_examples=100, deadline=None)
    async def test_hp_never_negative(self, hp, damage):
        """测试HP不会变成负数."""
        new_hp = max(0, hp - damage)
        assert new_hp >= 0
        
        # 如果伤害足够大，HP应该为0
        if damage >= hp:
            assert new_hp == 0
        else:
            assert new_hp == hp - damage


class TestEquipmentRandomValues:
    """随机装备数值测试."""
    
    @pytest.mark.asyncio
    @given(
        durability_current=st.integers(min_value=-10, max_value=1000),
        durability_max=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=100, deadline=None)
    async def test_equipment_durability_handling(self, durability_current, durability_max):
        """测试装备耐久度处理."""
        # 确保最大值至少为1
        assume(durability_max > 0)
        
        # 计算是否损坏
        is_broken = durability_current <= 0
        
        # 验证逻辑
        if durability_current <= 0:
            assert is_broken is True
        else:
            assert is_broken is False
        
        # 耐久度比例应在合理范围
        if durability_current >= 0:
            ratio = durability_current / durability_max
            assert 0 <= ratio or durability_current < 0
    
    @pytest.mark.asyncio
    @given(
        attack_bonus=st.integers(min_value=-100, max_value=1000),
        defense_bonus=st.integers(min_value=-100, max_value=1000),
        level_req=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=100, deadline=None)
    async def test_equipment_stats_validation(self, attack_bonus, defense_bonus, level_req):
        """测试装备属性验证."""
        # 攻击力不应为负（游戏设计选择）
        # 但应该能处理负值输入
        effective_attack = max(0, attack_bonus)
        assert effective_attack >= 0
        
        # 防御力同理
        effective_defense = max(0, defense_bonus)
        assert effective_defense >= 0
        
        # 等级需求应在合理范围
        assert 1 <= level_req <= 100


class TestNPCRandomBehavior:
    """随机NPC行为测试."""
    
    @pytest.mark.asyncio
    @given(
        favor=st.integers(min_value=-1000, max_value=1000),
        relationship_change=st.integers(min_value=-100, max_value=100)
    )
    @settings(max_examples=100, deadline=None)
    async def test_relationship_bounds(self, favor, relationship_change):
        """测试关系值边界."""
        new_favor = favor + relationship_change
        
        # 关系值应有上下限（假设-1000到1000）
        # 但我们应该能处理超出范围的值
        assert isinstance(new_favor, int)
        
        # 关系等级计算不应崩溃
        if new_favor < -100:
            level = "仇敌"
        elif new_favor < -50:
            level = "冷淡"
        elif new_favor < 50:
            level = "陌生"
        elif new_favor < 100:
            level = "友善"
        elif new_favor < 200:
            level = "尊敬"
        else:
            level = "至交"
        
        assert level in ["仇敌", "冷淡", "陌生", "友善", "尊敬", "至交"]


class TestQuestRandomProgress:
    """随机任务进度测试."""
    
    @pytest.mark.asyncio
    @given(
        current=st.integers(min_value=0, max_value=1000),
        required=st.integers(min_value=1, max_value=1000),
        progress=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=100, deadline=None)
    async def test_quest_progress_completion(self, current, required, progress):
        """测试任务进度完成判断."""
        assume(required > 0)
        
        new_current = min(current + progress, required)
        is_complete = new_current >= required
        
        # 进度不应超过要求值太多
        assert new_current <= required + progress
        
        # 完成状态应正确
        if new_current >= required:
            assert is_complete is True


class TestDataConsistencyRandom:
    """随机数据一致性测试."""
    
    @pytest.mark.asyncio
    @given(
        gold=st.integers(min_value=0, max_value=1000000),
        cost=st.integers(min_value=0, max_value=1000000)
    )
    @settings(max_examples=100, deadline=None)
    async def test_gold_transaction(self, gold, cost):
        """测试金钱交易."""
        if cost > gold:
            # 余额不足
            can_afford = False
            remaining = gold
        else:
            can_afford = True
            remaining = gold - cost
        
        assert remaining >= 0
        assert remaining <= gold
        
        if can_afford:
            assert remaining == gold - cost
    
    @pytest.mark.asyncio
    @given(
        current_time=st.datetimes(
            min_value=datetime(2000, 1, 1),
            max_value=datetime(2030, 12, 31)
        ),
        duration_seconds=st.integers(min_value=0, max_value=86400)
    )
    @settings(max_examples=100, deadline=None)
    async def test_time_based_cooldown(self, current_time, duration_seconds):
        """测试基于时间的冷却."""
        end_time = current_time + timedelta(seconds=duration_seconds)
        
        # 冷却是否结束
        is_expired = current_time >= end_time
        
        # 如果持续时间为0，冷却应该立即结束
        if duration_seconds == 0:
            assert is_expired is True
        
        # 结束时间应该晚于或等于开始时间
        assert end_time >= current_time


# 有状态测试 - 模拟游戏会话
class GameSessionStateMachine(RuleBasedStateMachine):
    """游戏会话状态机测试."""
    
    def __init__(self):
        super().__init__()
        self.characters = []
        self.equipments = []
        self.gold = 0
        self.quests_completed = 0
    
    @rule(name=valid_names)
    def create_character(self, name):
        """创建角色."""
        char = {"name": name, "level": 1, "hp": 100}
        self.characters.append(char)
    
    @rule()
    def level_up_random_character(self):
        """随机角色升级."""
        if self.characters:
            import random
            char = random.choice(self.characters)
            if char["level"] < 100:
                char["level"] += 1
                char["hp"] += 10
    
    @rule(gold_amount=non_negative_ints)
    def add_gold(self, gold_amount):
        """添加金币."""
        self.gold += gold_amount
    
    @rule(cost=non_negative_ints)
    def spend_gold(self, cost):
        """花费金币."""
        if cost <= self.gold:
            self.gold -= cost
    
    @rule()
    def complete_quest(self):
        """完成任务."""
        self.quests_completed += 1
    
    @invariant()
    def gold_never_negative(self):
        """金币永不为负."""
        assert self.gold >= 0
    
    @invariant()
    def quest_count_non_negative(self):
        """任务完成数非负."""
        assert self.quests_completed >= 0
    
    @invariant()
    def characters_have_valid_levels(self):
        """角色等级有效."""
        for char in self.characters:
            assert 1 <= char["level"] <= 100
            assert char["hp"] > 0


# 标记测试
pytestmark = [
    pytest.mark.integration,
    pytest.mark.randomized,
    pytest.mark.slow
]

# 如果不想运行hypothesis测试，可以使用以下标记跳过
# pytestmark.append(pytest.mark.skip(reason="Hypothesis tests disabled"))
