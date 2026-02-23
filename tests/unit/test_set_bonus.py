"""套装效果系统单元测试.

测试TD-016: 套装效果计算
"""

import pytest
from unittest.mock import MagicMock, patch

from src.game.data.set_bonuses import (
    SetBonusConfig,
    SetBonusLevel,
    get_set_bonus_config,
    register_set_bonus,
    SET_BONUS_REGISTRY,
)


class TestSetBonusLevel:
    """测试套装效果等级."""
    
    def test_creation(self):
        """测试创建效果等级."""
        level = SetBonusLevel(
            required_count=2,
            description="2件：攻击+10",
            stats_bonus={"attack": 10}
        )
        assert level.required_count == 2
        assert level.description == "2件：攻击+10"
        assert level.stats_bonus == {"attack": 10}
        assert level.special_effect is None


class TestSetBonusConfig:
    """测试套装效果配置."""
    
    @pytest.fixture
    def sample_config(self):
        """创建示例配置."""
        return SetBonusConfig(
            set_name="测试套装",
            max_pieces=4,
            bonus_levels=[
                SetBonusLevel(2, "2件：攻击+10", {"attack": 10}),
                SetBonusLevel(4, "4件：攻击+25，防御+15", {"attack": 25, "defense": 15}),
            ]
        )
    
    def test_get_bonus_for_count_no_match(self, sample_config):
        """测试件数不足时返回None."""
        assert sample_config.get_bonus_for_count(1) is None
    
    def test_get_bonus_for_count_first_level(self, sample_config):
        """测试触发第一级效果."""
        bonus = sample_config.get_bonus_for_count(2)
        assert bonus is not None
        assert bonus.required_count == 2
        assert bonus.stats_bonus["attack"] == 10
    
    def test_get_bonus_for_count_second_level(self, sample_config):
        """测试触发第二级效果."""
        bonus = sample_config.get_bonus_for_count(4)
        assert bonus is not None
        assert bonus.required_count == 4
        assert bonus.stats_bonus["attack"] == 25
        assert bonus.stats_bonus["defense"] == 15
    
    def test_get_bonus_for_count_intermediate(self, sample_config):
        """测试中间件数触发最高可用等级."""
        bonus = sample_config.get_bonus_for_count(3)
        assert bonus is not None
        assert bonus.required_count == 2  # 3件触发2件效果


class TestSetBonusRegistry:
    """测试套装注册表."""
    
    def test_get_existing_set(self):
        """测试获取已存在的套装."""
        config = get_set_bonus_config("少林僧衣")
        assert config is not None
        assert config.set_name == "少林僧衣"
        assert config.max_pieces == 4
    
    def test_get_non_existing_set(self):
        """测试获取不存在的套装返回None."""
        config = get_set_bonus_config("不存在的套装")
        assert config is None
    
    def test_register_new_set(self):
        """测试注册新套装."""
        new_config = SetBonusConfig(
            set_name="测试新套装",
            max_pieces=2,
            bonus_levels=[
                SetBonusLevel(2, "2件：全属性+5", {"all_stats": 5})
            ]
        )
        register_set_bonus(new_config)
        
        # 验证注册成功
        retrieved = get_set_bonus_config("测试新套装")
        assert retrieved is not None
        assert retrieved.max_pieces == 2
        
        # 清理
        del SET_BONUS_REGISTRY["测试新套装"]


class TestPredefinedSets:
    """测试预定义套装配置."""
    
    @pytest.mark.parametrize("set_name,expected_pieces", [
        ("少林僧衣", 4),
        ("武当道袍", 4),
        ("华山剑袍", 4),
        ("丐帮破衣", 4),
        ("全真心法袍", 4),
        ("玉女素心袍", 4),
        ("逍遥羽衣", 4),
        ("峨眉禅衣", 4),
        ("日月神教服", 4),
        ("星宿毒袍", 4),
        ("江湖轻甲", 4),
    ])
    def test_all_sets_exist(self, set_name, expected_pieces):
        """测试所有套装都存在."""
        config = get_set_bonus_config(set_name)
        assert config is not None, f"套装 {set_name} 不存在"
        assert config.max_pieces == expected_pieces
    
    def test_shaolin_set_bonuses(self):
        """测试少林套装效果."""
        config = get_set_bonus_config("少林僧衣")
        
        # 2件效果
        bonus_2 = config.get_bonus_for_count(2)
        assert bonus_2 is not None
        assert "根骨" in bonus_2.description
        assert bonus_2.stats_bonus.get("constitution") == 10
        
        # 4件效果
        bonus_4 = config.get_bonus_for_count(4)
        assert bonus_4 is not None
        assert bonus_4.stats_bonus.get("constitution") == 20
        assert "defense_percent" in bonus_4.stats_bonus
        assert "金钟罩" in bonus_4.special_effect
    
    def test_wudang_set_bonuses(self):
        """测试武当套装效果."""
        config = get_set_bonus_config("武当道袍")
        
        bonus_4 = config.get_bonus_for_count(4)
        assert bonus_4 is not None
        assert bonus_4.stats_bonus.get("intelligence") == 20
        assert "太极劲" in bonus_4.special_effect
    
    def test_huashan_set_bonuses(self):
        """测试华山套装效果."""
        config = get_set_bonus_config("华山剑袍")
        
        bonus_4 = config.get_bonus_for_count(4)
        assert bonus_4 is not None
        assert "华山剑气" in bonus_4.special_effect


class TestEquipmentMixinSetBonus:
    """测试EquipmentMixin的套装效果方法."""
    
    @pytest.fixture
    def mock_equipment(self):
        """创建模拟装备."""
        items = []
        
        def create_item(set_name, slot):
            item = MagicMock()
            item.set_name = set_name
            item.slot = slot
            item.stats_bonus = {"attack": 5}
            item.is_broken = False
            return item
        
        return create_item
    
    @pytest.fixture
    def mixin_with_sets(self, mock_equipment):
        """创建带套装的mixin."""
        from src.game.typeclasses.equipment import CharacterEquipmentMixin, EquipmentSlot
        
        mixin = MagicMock(spec=CharacterEquipmentMixin)
        
        # 模拟装备：少林僧衣 3件 (头部、身体、手部)
        equipped = {
            EquipmentSlot.HEAD: mock_equipment("少林僧衣", EquipmentSlot.HEAD),
            EquipmentSlot.BODY: mock_equipment("少林僧衣", EquipmentSlot.BODY),
            EquipmentSlot.HANDS: mock_equipment("少林僧衣", EquipmentSlot.HANDS),
            EquipmentSlot.FEET: mock_equipment("江湖轻甲", EquipmentSlot.FEET),
        }
        
        def mock_get_equipped(slot):
            return equipped.get(slot)
        
        mixin.get_equipped = mock_get_equipped
        
        # 绑定真实方法
        from src.game.typeclasses.equipment import CharacterEquipmentMixin
        mixin.get_set_bonuses = lambda: CharacterEquipmentMixin.get_set_bonuses(mixin)
        mixin.get_total_set_stats = lambda: CharacterEquipmentMixin.get_total_set_stats(mixin)
        mixin.get_set_info = lambda: CharacterEquipmentMixin.get_set_info(mixin)
        
        return mixin
    
    def test_get_set_bonuses_counts(self, mixin_with_sets):
        """测试套装件数统计."""
        bonuses = mixin_with_sets.get_set_bonuses()
        
        # 应该有少林僧衣的统计
        assert "少林僧衣" in bonuses
        assert bonuses["少林僧衣"]["count"] == 3
    
    def test_get_set_bonuses_stats(self, mixin_with_sets):
        """测试套装属性加成."""
        bonuses = mixin_with_sets.get_set_bonuses()
        
        shaolin_bonus = bonuses.get("少林僧衣", {})
        stats = shaolin_bonus.get("stats", {})
        # 3件应该触发2件效果
        assert stats.get("constitution") == 10
    
    def test_get_total_set_stats(self, mixin_with_sets):
        """测试总属性计算."""
        total = mixin_with_sets.get_total_set_stats()
        
        # 少林2件效果 + 根骨
        assert "constitution" in total
        assert total["constitution"] == 10
    
    def test_get_set_info(self, mixin_with_sets):
        """测试套装信息显示."""
        info = mixin_with_sets.get_set_info()
        
        # 应该返回两个套装的信息
        assert len(info) == 2
        
        # 少林僧衣信息
        shaolin = next((i for i in info if i["name"] == "少林僧衣"), None)
        assert shaolin is not None
        assert shaolin["count"] == 3
        assert shaolin["active_bonus"] is not None
        assert shaolin["next_bonus"] is not None  # 应该有4件效果的提示
