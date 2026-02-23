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

    def _get_main_opponent(self, character: Character) -> Character | None:
        """获取主要对手（当前战斗中的敌人）."""
        # 简化实现：从角色获取当前战斗会话
        if hasattr(character, 'combat_session') and character.combat_session:
            combat = character.combat_session
            if hasattr(combat, 'get_alive_enemies'):
                enemies = combat.get_alive_enemies(character)
                if enemies:
                    return enemies[0]
        return None
    
    def _get_opponent_wuxue_type(self, opponent: Character):
        """获取对手的武学类型."""
        if hasattr(opponent, 'current_wuxue') and opponent.current_wuxue:
            return opponent.current_wuxue.wuxue_type
        if hasattr(opponent, 'default_wuxue_type'):
            return opponent.default_wuxue_type
        return None
    
    def _select_counter_move(self, moves: list[tuple], opponent_type) -> tuple | None:
        """基于克制关系选择招式 (TD-026).
        
        Args:
            moves: 可用招式列表 [(kungfu, move), ...]
            opponent_type: 对手的武学类型
            
        Returns:
            克制的招式或None
        """
        if not opponent_type or not moves:
            return None
        
        from src.game.typeclasses.wuxue import COUNTER_MATRIX
        
        # 寻找能克制对手武学类型的招式
        # COUNTER_MATRIX[attack_type] = [被克制的类型列表]
        # 所以我们要找：opponent_type in COUNTER_MATRIX[move_type]
        for kungfu, move in moves:
            counters = COUNTER_MATRIX.get(move.wuxue_type, [])
            if opponent_type in counters:
                return (kungfu, move)
        
        return None
    
    def _select_highest_damage_move(self, moves: list[tuple]) -> tuple | None:
        """选择伤害最高的招式 (TD-027).
        
        Args:
            moves: 可用招式列表 [(kungfu, move), ...]
            
        Returns:
            伤害最高的招式或None
        """
        if not moves:
            return None
        
        def get_move_damage(item):
            kungfu, move = item
            # 优先使用招式的damage属性
            if hasattr(move, 'damage'):
                return move.damage
            # 回退到基础伤害+武学加成
            base = 10
            level_bonus = kungfu.level if hasattr(kungfu, 'level') else 1
            return base * level_bonus
        
        return max(moves, key=get_move_damage)

    def _select_best_move(
        self, moves: list[tuple], target: Character
    ) -> tuple | None:
        """选择最优招式.

        策略：
        - 优先选择高伤害的招式
        - 考虑克制关系 (TD-026)
        """
        if not moves:
            return None

        # 获取对手信息
        opponent = self._get_main_opponent(character)
        if opponent:
            opponent_type = self._get_opponent_wuxue_type(opponent)
            
            # 基于克制关系选择
            counter_move = self._select_counter_move(moves, opponent_type)
            if counter_move:
                return counter_move
        
        # 回退：选择伤害最高的招式 (TD-027)
        return self._select_highest_damage_move(moves)


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
