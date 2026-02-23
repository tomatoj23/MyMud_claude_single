"""战斗AI."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game.typeclasses.character import Character
    from src.game.combat.core import CombatSession, CombatAction


class CombatAI:
    """基础战斗AI.

    简单的随机选择策略：
    - 随机选择可用招式
    - 随机选择目标
    - 低血量时可能逃跑或防御
    """

    def __init__(self, ai_type: str = "normal"):
        self.ai_type = ai_type

    async def decide(
        self, character: Character, combat: CombatSession
    ) -> CombatAction:
        """AI决策行动.

        Args:
            character: AI控制的角色
            combat: 战斗会话

        Returns:
            战斗行动
        """
        # 获取可用招式
        moves = character.get_available_moves()

        # 获取存活的目标（敌方）
        targets = combat.get_alive_enemies(character)

        if not targets:
            # 没有目标，防御
            from .core import CombatAction

            return CombatAction("defend")

        # 简单策略：80%概率攻击，20%概率防御
        if random.random() < 0.8:
            target = random.choice(targets)

            if moves:
                # 随机选择招式
                kungfu, move = random.choice(moves)
                from .core import CombatAction

                return CombatAction(
                    action_type="move",
                    target=target,
                    data={"move": move, "kungfu": kungfu},
                )
            else:
                # 无招式，普通攻击
                from .core import CombatAction

                return CombatAction("move", target, {"move": None})
        else:
            # 防御
            from .core import CombatAction

            return CombatAction("defend")


class SmartAI(CombatAI):
    """智能AI.

    更智能的战斗策略：
    - 血量低时优先逃跑或防御
    - 尝试选择克制对手的招式
    - 保留强力招式的冷却
    """

    # 低血量阈值
    LOW_HP_THRESHOLD = 0.3
    # 逃跑概率
    FLEE_CHANCE = 0.4
    # 防御概率
    DEFEND_CHANCE = 0.3

    async def decide(
        self, character: Character, combat: CombatSession
    ) -> CombatAction:
        """智能决策."""
        hp, max_hp = character.get_hp()
        hp_ratio = hp / max_hp if max_hp > 0 else 0

        # 低血量时的决策
        if hp_ratio < self.LOW_HP_THRESHOLD:
            roll = random.random()
            if roll < self.FLEE_CHANCE:
                from .core import CombatAction

                return CombatAction("flee")
            elif roll < self.FLEE_CHANCE + self.DEFEND_CHANCE:
                from .core import CombatAction

                return CombatAction("defend")

        # 获取目标
        targets = combat.get_alive_enemies(character)
        if not targets:
            from .core import CombatAction

            return CombatAction("defend")

        target = self._select_target(targets)

        # 获取可用招式
        moves = character.get_available_moves()

        if moves:
            # 尝试选择最优招式
            move_pair = self._select_best_move(moves, target)
            if move_pair:
                kungfu, move = move_pair
                from .core import CombatAction

                return CombatAction(
                    action_type="move",
                    target=target,
                    data={"move": move, "kungfu": kungfu},
                )

        # 默认使用父类逻辑
        return await super().decide(character, combat)

    def _select_target(self, targets: list[Character]) -> Character:
        """选择最优目标.

        策略：优先选择血量最低的敌人
        """
        if not targets:
            raise ValueError("No targets available")

        # 70%概率选血量最低的，30%随机
        if random.random() < 0.7:
            return min(targets, key=lambda t: t.get_hp()[0])
        else:
            return random.choice(targets)

    def _select_best_move(
        self, moves: list[tuple], target: Character
    ) -> tuple | None:
        """选择最优招式.

        策略：
        - 优先选择高伤害的招式
        - 考虑克制关系（待实现）
        """
        if not moves:
            return None

        # 简单策略：随机选择
        # TODO: 实现基于克制关系的智能选择
        return random.choice(moves)


class AggressiveAI(CombatAI):
    """激进AI.

    特点：
    - 总是优先攻击
    - 选择伤害最高的招式
    - 从不逃跑
    """

    async def decide(
        self, character: Character, combat: CombatSession
    ) -> CombatAction:
        """激进决策."""
        targets = combat.get_alive_enemies(character)

        if not targets:
            from .core import CombatAction

            return CombatAction("defend")

        target = random.choice(targets)
        moves = character.get_available_moves()

        if moves:
            # 选择伤害最高的招式（假设move有damage属性）
            # TODO: 根据实际招式属性选择
            kungfu, move = random.choice(moves)
            from .core import CombatAction

            return CombatAction(
                action_type="move",
                target=target,
                data={"move": move, "kungfu": kungfu},
            )

        from .core import CombatAction

        return CombatAction("move", target, {"move": None})


class DefensiveAI(CombatAI):
    """防御型AI.

    特点：
    - 经常使用防御
    - 血量低于50%时必防御
    - 很少主动攻击
    """

    async def decide(
        self, character: Character, combat: CombatSession
    ) -> CombatAction:
        """防御型决策."""
        hp, max_hp = character.get_hp()
        hp_ratio = hp / max_hp if max_hp > 0 else 0

        # 低血量必防御
        if hp_ratio < 0.5:
            from .core import CombatAction

            return CombatAction("defend")

        # 50%概率防御
        if random.random() < 0.5:
            from .core import CombatAction

            return CombatAction("defend")

        # 其他情况使用父类逻辑
        return await super().decide(character, combat)
