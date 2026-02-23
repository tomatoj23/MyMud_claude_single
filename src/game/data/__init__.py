"""游戏数据配置模块."""

from src.game.data.set_bonuses import (
    SetBonusConfig,
    SetBonusLevel,
    get_set_bonus_config,
    register_set_bonus,
    SET_BONUS_REGISTRY,
)

__all__ = [
    "SetBonusConfig",
    "SetBonusLevel",
    "get_set_bonus_config",
    "register_set_bonus",
    "SET_BONUS_REGISTRY",
]
