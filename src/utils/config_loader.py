"""配置加载器.

支持从YAML文件加载游戏配置。
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# 尝试导入yaml
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    logger.warning("PyYAML not installed, using default config")


class BalanceConfig:
    """游戏平衡配置."""
    
    _instance: BalanceConfig | None = None
    _config: dict[str, Any] | None = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """加载配置文件."""
        if self._config is not None:
            return
        
        # 默认配置
        self._config = self._get_default_config()
        
        if not HAS_YAML:
            logger.info("Using default balance config")
            return
        
        # 尝试加载配置文件
        config_paths = [
            Path("data/balance.yml"),
            Path(__file__).parent.parent.parent / "data" / "balance.yml",
        ]
        
        for path in config_paths:
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        user_config = yaml.safe_load(f)
                        if user_config:
                            self._deep_merge(self._config, user_config)
                            logger.info(f"Loaded balance config from {path}")
                            return
                except Exception as e:
                    logger.warning(f"Failed to load config from {path}: {e}")
        
        logger.info("Using default balance config (no config file found)")
    
    def _get_default_config(self) -> dict[str, Any]:
        """获取默认配置."""
        return {
            "combat": {
                "damage": {
                    "base": 10,
                    "variance": 0.1,
                    "crit_chance": 0.05,
                    "crit_multiplier": 1.5,
                    "counter_bonus": 0.2,
                    "countered_penalty": -0.15,
                },
                "cooldown": {
                    "base": 3.0,
                    "min": 1.0,
                    "agility_factor": 0.02,
                },
                "hit_rate": {
                    "base": 0.90,
                    "min": 0.30,
                    "max": 0.95,
                    "agility_mod_per_point": 0.005,
                },
                "flee": {
                    "base_chance": 0.5,
                    "min_chance": 0.2,
                    "max_chance": 0.9,
                    "agility_factor": 0.02,
                },
            },
            "leveling": {
                "exp_curve": [100, 200, 400, 800, 1600],
                "hp_per_level": 25,
                "mp_per_level": 15,
                "ep_per_level": 5,
            },
            "attributes": {
                "hp": {"base": 100, "per_constitution": 10, "per_gengu": 5},
                "mp": {"base": 50, "per_spirit": 8, "per_gengu": 3},
                "ep": {"base": 100},
                "attack": {"per_strength": 2},
                "defense": {"per_constitution": 1},
                "agility": {"per_agility": 1},
                "max_weight": {"base": 50, "per_strength": 5},
            },
            "wuxue": {
                "practice": {"base_gain": 10, "per_wuxing": 3},
                "level_up": {"exp_required_multiplier": 100},
                "mastery": {"max_level": 10},
            },
            "equipment": {
                "durability": {"default_max": 100},
                "quality_multiplier": {
                    "common": 1.0,
                    "uncommon": 1.2,
                    "rare": 1.5,
                    "epic": 2.0,
                    "legendary": 3.0,
                },
            },
            "pet": {
                "max_loyalty": 100,
                "min_loyalty": 0,
                "level_up_exp_multiplier": 100,
            },
        }
    
    def _deep_merge(self, base: dict, override: dict):
        """深度合并两个字典."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """获取配置值.
        
        Args:
            *keys: 配置键路径
            default: 默认值
            
        Returns:
            配置值或默认值
            
        Example:
            config.get("combat", "damage", "base")  # 返回 10
        """
        current = self._config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def reload(self):
        """重新加载配置."""
        self._config = None
        self._load_config()
        logger.info("Balance config reloaded")
    
    def get_all(self) -> dict[str, Any]:
        """获取完整配置."""
        return self._config.copy()


# 全局配置实例
balance_config = BalanceConfig()


def get_balance_config() -> BalanceConfig:
    """获取游戏平衡配置实例.
    
    Returns:
        BalanceConfig 单例
    """
    return balance_config
