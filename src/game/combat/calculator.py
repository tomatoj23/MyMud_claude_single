"""战斗数值计算器."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game.typeclasses.character import Character
    from src.game.typeclasses.wuxue import Move, WuxueType


@dataclass
class DamageResult:
    """伤害结果."""

    damage: float = 0
    is_crit: bool = False
    is_hit: bool = True
    messages: list[str] | None = None

    def __post_init__(self):
        if self.messages is None:
            self.messages = []


class CombatCalculator:
    """战斗数值计算器.

    负责所有战斗相关数值的计算：
    - 伤害计算
    - 命中率
    - 环境加成
    """

    # 暴击率基础值
    BASE_CRIT_RATE = 0.05
    # 暴击伤害倍率
    CRIT_DAMAGE = 1.5
    # 基础命中率
    BASE_HIT_RATE = 0.90
    # 伤害随机浮动范围
    DAMAGE_VARIANCE = 0.1

    def calculate_damage(
        self,
        attacker: Character,
        defender: Character,
        move: Move | None,
        context: CombatContext | None,
    ) -> DamageResult:
        """计算伤害.

        计算流程：
        1. 命中率判定
        2. 基础伤害 = 攻击力 * 招式倍率
        3. 防御减免
        4. 招式克制加成
        5. 随机浮动
        6. 暴击判定

        Args:
            attacker: 攻击者
            defender: 防御者
            move: 使用的招式（None表示普通攻击）
            context: 战斗上下文

        Returns:
            伤害结果
        """
        messages = []

        # 1. 命中率判定
        hit_rate = self.calculate_hit_rate(attacker, defender, move)
        if random.random() > hit_rate:
            return DamageResult(damage=0, is_crit=False, is_hit=False, messages=["未命中！"])

        # 2. 基础伤害
        attack_power = attacker.get_attack()
        if move:
            move_multiplier = 1.5  # 招式倍率
        else:
            move_multiplier = 1.0
        base_damage = attack_power * move_multiplier

        # 3. 防御减免
        defense = defender.get_defense()
        damage_after_def = max(1, base_damage - defense * 0.5)

        # 4. 招式克制加成 (TD-024)
        if move:
            from src.game.typeclasses.wuxue import get_counter_modifier, WuxueType

            # 获取防御者当前使用的武学类型
            defender_type = self._get_defender_wuxue_type(defender)
            counter_mod = get_counter_modifier(move.wuxue_type, defender_type)
            damage_after_counter = damage_after_def * counter_mod

            if counter_mod > 1.0:
                messages.append("招式克制！伤害增加！")
            elif counter_mod < 1.0:
                messages.append("招式被克！伤害减少！")
        else:
            damage_after_counter = damage_after_def

        # 5. 环境加成
        env_mod = self.get_environment_bonus(context)
        damage_after_env = damage_after_counter * env_mod.get("damage", 1.0)

        # 6. 随机浮动
        variance = random.uniform(
            1.0 - self.DAMAGE_VARIANCE, 1.0 + self.DAMAGE_VARIANCE
        )
        final_damage = damage_after_env * variance

        # 7. 暴击判定
        from src.utils.config_loader import get_balance_config
        crit_rate = get_balance_config().get("combat", "damage", "crit_chance", default=0.05)
        is_crit = random.random() < crit_rate
        if is_crit:
            final_damage *= self.CRIT_DAMAGE
            messages.append("暴击！")

        return DamageResult(
            damage=max(1, final_damage),
            is_crit=is_crit,
            is_hit=True,
            messages=messages,
        )

    def calculate_hit_rate(
        self, attacker: Character, defender: Character, move: Move | None
    ) -> float:
        """计算命中率.

        公式: 基础命中 + (敏捷差 * 0.5%) + 招式修正

        Args:
            attacker: 攻击者
            defender: 防御者
            move: 使用的招式

        Returns:
            命中率 (0-1)
        """
        base_hit = self.BASE_HIT_RATE

        # 敏捷差影响
        from src.utils.config_loader import get_balance_config
        agility_mod_factor = get_balance_config().get(
            "combat", "hit_rate", "agility_mod_per_point", default=0.005
        )
        agility_diff = attacker.get_agility() - defender.get_agility()
        agility_mod = agility_diff * agility_mod_factor

        # 招式修正（某些招式可能有命中加成）(TD-025)
        move_mod = 0.0
        if move:
            move_mod = self._get_move_hit_modifier(move)

        hit_rate = base_hit + agility_mod + move_mod

        # 限制在合理范围
        return max(0.3, min(0.95, hit_rate))

    def get_environment_bonus(
        self, context: CombatContext | None
    ) -> dict[str, float]:
        """获取环境加成.

        可能的加成：
        - 高地 -> +10%命中
        - 雨天 -> 火系-20%，水系+20%
        - 夜间 -> -20%命中（无照明）

        Args:
            context: 战斗上下文

        Returns:
            加成字典 {"damage": x, "hit": y}
        """
        bonus = {"damage": 1.0, "hit": 1.0}

        if not context or not context.environment:
            return bonus

        room = context.environment
        env = getattr(room, "environment", {})

        if not isinstance(env, dict):
            return bonus

        # 天气影响
        weather = env.get("weather", "clear")
        if weather == "rain":
            # 雨天影响（待实现属性系统）
            pass
        elif weather == "fog":
            bonus["hit"] *= 0.9

        # 光照影响
        light = env.get("light", 100)
        if light < 30:
            bonus["hit"] *= 0.8

        # 地形影响
        terrain = env.get("terrain", "normal")
        if terrain == "high_ground":
            bonus["damage"] *= 1.1

        return bonus

    def _get_defender_wuxue_type(self, defender) -> WuxueType | None:
        """获取防御者当前使用的武学类型 (TD-024).
        
        Args:
            defender: 防御者
            
        Returns:
            武学类型或None
        """
        # 检查防御者是否有当前使用的武功
        if hasattr(defender, 'current_wuxue'):
            wuxue = defender.current_wuxue
            if wuxue:
                return wuxue.wuxue_type
        
        # 检查是否有默认武学类型
        if hasattr(defender, 'default_wuxue_type'):
            return defender.default_wuxue_type
        
        return None

    def _get_move_hit_modifier(self, move) -> float:
        """获取招式命中修正 (TD-025).
        
        Args:
            move: 招式
            
        Returns:
            命中修正值
        """
        if not move:
            return 0.0
        
        # 从招式数据读取命中修正
        if hasattr(move, 'hit_modifier'):
            return move.hit_modifier
        
        # 根据武学类型默认修正
        from src.game.typeclasses.wuxue import WuxueType
        type_hit_bonus = {
            WuxueType.ZHANG: 0.05,  # 掌法+5%命中
            WuxueType.ZHI: 0.10,    # 指法+10%命中
            WuxueType.QINGGONG: 0.15,  # 轻功+15%命中
        }
        
        return type_hit_bonus.get(move.wuxue_type, 0.0)


class CombatContext:
    """战斗上下文.

    封装战斗时的环境信息，用于计算环境加成。
    """

    def __init__(
        self,
        caster: Character,
        target: Character,
        environment: Room | None,
        round_num: int = 0,
    ):
        self.caster = caster
        self.target = target
        self.environment = environment
        self.round_num = round_num


# 避免循环导入的延迟导入
from src.game.typeclasses.room import Room  # noqa: E402
