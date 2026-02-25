"""配置加载器测试."""

import pytest
from unittest.mock import mock_open, patch

from src.utils.config_loader import BalanceConfig, get_balance_config


class TestBalanceConfig:
    """测试游戏平衡配置."""
    
    def test_singleton(self):
        """测试单例模式."""
        config1 = BalanceConfig()
        config2 = BalanceConfig()
        assert config1 is config2
    
    def test_get_nested_value(self):
        """测试获取嵌套值."""
        config = BalanceConfig()
        
        value = config.get("combat", "damage", "base")
        assert value == 10
    
    def test_get_with_default(self):
        """测试获取带默认值."""
        config = BalanceConfig()
        
        value = config.get("nonexistent", "key", default=100)
        assert value == 100
    
    def test_get_partial_path(self):
        """测试获取部分路径."""
        config = BalanceConfig()
        
        value = config.get("combat", "damage")
        assert isinstance(value, dict)
        assert "base" in value
    
    def test_combat_damage_config(self):
        """测试战斗伤害配置."""
        config = BalanceConfig()
        
        assert config.get("combat", "damage", "crit_chance") == 0.05
        assert config.get("combat", "damage", "crit_multiplier") == 1.5
        assert config.get("combat", "damage", "counter_bonus") == 0.2
    
    def test_combat_cooldown_config(self):
        """测试战斗冷却配置."""
        config = BalanceConfig()
        
        assert config.get("combat", "cooldown", "base") == 3.0
        assert config.get("combat", "cooldown", "min") == 1.0
    
    def test_leveling_config(self):
        """测试升级配置."""
        config = BalanceConfig()
        
        exp_curve = config.get("leveling", "exp_curve")
        assert isinstance(exp_curve, list)
        assert exp_curve[0] == 100
        assert config.get("leveling", "hp_per_level") == 25
    
    def test_attributes_config(self):
        """测试属性配置."""
        config = BalanceConfig()
        
        assert config.get("attributes", "hp", "base") == 100
        assert config.get("attributes", "attack", "per_strength") == 2
        assert config.get("attributes", "defense", "per_constitution") == 1
    
    def test_equipment_quality_config(self):
        """测试装备品质配置."""
        config = BalanceConfig()
        
        multipliers = config.get("equipment", "quality_multiplier")
        assert multipliers["common"] == 1.0
        assert multipliers["legendary"] == 3.0
    
    def test_get_all(self):
        """测试获取完整配置."""
        config = BalanceConfig()
        
        all_config = config.get_all()
        assert isinstance(all_config, dict)
        assert "combat" in all_config
        assert "leveling" in all_config
    
    def test_reload(self):
        """测试重新加载."""
        config = BalanceConfig()
        
        # 重新加载不应报错
        config.reload()
        
        # 配置应该仍然有效
        assert config.get("combat", "damage", "base") == 10


class TestGetBalanceConfig:
    """测试获取配置函数."""
    
    def test_get_balance_config(self):
        """测试获取全局配置."""
        config1 = get_balance_config()
        config2 = get_balance_config()
        
        assert config1 is config2
        assert isinstance(config1, BalanceConfig)


class TestConfigMerge:
    """测试配置合并."""
    
    def test_deep_merge(self):
        """测试深度合并."""
        config = BalanceConfig()
        
        base = {"a": 1, "b": {"c": 2, "d": 3}}
        override = {"b": {"c": 99}}
        
        config._deep_merge(base, override)
        
        assert base["a"] == 1
        assert base["b"]["c"] == 99
        assert base["b"]["d"] == 3
