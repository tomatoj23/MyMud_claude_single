"""战斗核心 - 即时制.

玩家可随时输入命令，各行动有独立的冷却时间。
"""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import contextmanager
from enum import Enum
from typing import TYPE_CHECKING, Optional

from .transaction import CombatTransaction, TransactionManager

if TYPE_CHECKING:
    from src.engine.core.engine import GameEngine
    from src.game.typeclasses.character import Character
    from src.game.typeclasses.wuxue import Move


class CombatResult(Enum):
    """战斗结果."""

    WIN = "win"
    LOSE = "lose"
    DRAW = "draw"
    FLEE = "flee"


class Combatant:
    """战斗参与者封装.

    管理参与者的冷却时间和状态。
    """

    def __init__(self, character: Character, is_player: bool = False):
        self.character = character
        self.is_player = is_player
        self.next_action_time: float = 0.0
        self.in_combat: bool = False

    def is_ready(self, now: float | None = None) -> bool:
        """检查是否可以行动."""
        if now is None:
            now = time.time()
        return now >= self.next_action_time

    def set_cooldown(self, cooldown: float) -> None:
        """设置下次可行动时间."""
        self.next_action_time = time.time() + cooldown

    def get_remaining_cooldown(self) -> float:
        """获取剩余冷却时间（秒）."""
        remaining = self.next_action_time - time.time()
        return max(0.0, remaining)


class CombatAction:
    """战斗行动."""

    def __init__(
        self,
        action_type: str,  # "move", "item", "flee", "defend"
        target: Optional[Character] = None,
        data: dict | None = None,
    ):
        self.type = action_type
        self.target = target
        self.data = data or {}


logger = logging.getLogger(__name__)

# 策略注册表（延迟导入避免循环依赖）
_ACTION_STRATEGIES: dict[str, "CombatActionStrategy"] | None = None


def _get_strategies() -> dict[str, "CombatActionStrategy"]:
    """获取策略注册表（延迟初始化）."""
    global _ACTION_STRATEGIES
    if _ACTION_STRATEGIES is None:
        from .strategy import AttackStrategy, CastStrategy, FleeStrategy, DefendStrategy
        _ACTION_STRATEGIES = {
            "kill": AttackStrategy(),
            "cast": CastStrategy(),
            "flee": FleeStrategy(),
            "defend": DefendStrategy(),
        }
    return _ACTION_STRATEGIES


class CombatSession:
    """即时制战斗会话.

    管理一场战斗的完整流程：
    - 参与者管理（玩家和NPC）
    - 实时行动冷却
    - 伤害结算
    - 胜负判定

    Example:
        session = CombatSession(engine, [player, enemy])
        await session.start()
        # 玩家输入命令时
        await session.handle_player_command(player, "kill", {"target": enemy})
    """

    # 基础冷却时间（秒）
    BASE_COOLDOWN = 3.0
    # 敏捷对冷却的影响系数
    AGILITY_FACTOR = 0.02
    # 最小冷却时间
    MIN_COOLDOWN = 1.0
    # 逃跑冷却时间
    FLEE_COOLDOWN = 5.0

    def __init__(
        self,
        engine: GameEngine,
        participants: list[Character],
        player_character: Character | None = None,
    ):
        self.engine = engine
        self.participants: dict[int, Combatant] = {}
        self.active = False
        self._loop_task: asyncio.Task | None = None
        self.result: CombatResult | None = None
        self.winner: Character | None = None
        self.log: list[str] = []
        self._last_update_time = time.time()  # 用于实时战斗结算 (TD-022)
        self._txn_manager = TransactionManager()  # 事务管理器

        # 初始化参与者
        for char in participants:
            is_player = player_character is not None and char.id == player_character.id
            self.participants[char.id] = Combatant(char, is_player)

    @contextmanager
    def transaction(self):
        """提供事务保护上下文.
        
        使用示例:
            with self.transaction() as txn:
                txn.snapshot(target, ['hp'])
                target.hp -= damage
                txn.commit()
        """
        with self._txn_manager.begin() as txn:
            yield txn

    async def start(self) -> None:
        """开始战斗."""
        self.active = True

        # 触发战斗开始事件
        for combatant in self.participants.values():
            combatant.in_combat = True
            char = combatant.character
            if hasattr(char, "at_combat_start"):
                char.at_combat_start(self)

        # 启动战斗循环
        self._loop_task = asyncio.create_task(self._combat_loop())

        self._log("战斗开始！")

    async def stop(self, result: CombatResult | None = None) -> None:
        """停止战斗."""
        self.active = False
        self.result = result

        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass

        # 触发战斗结束事件
        for combatant in self.participants.values():
            combatant.in_combat = False
            char = combatant.character
            if hasattr(char, "at_combat_end"):
                char.at_combat_end(self)

        if result == CombatResult.WIN:
            self._log("战斗胜利！")
        elif result == CombatResult.LOSE:
            self._log("战斗失败！")
        elif result == CombatResult.FLEE:
            self._log("成功逃跑！")
        elif result == CombatResult.DRAW:
            self._log("战斗平局！")

    async def _combat_loop(self) -> None:
        """战斗主循环（100ms tick）."""
        while self.active:
            await self._process_ai_turns()

            # 检查战斗结束
            if result := await self._check_end():
                await self.stop(result)
                return

            # BUFF结算（按实际时间）(TD-022)
            current_time = time.time()
            elapsed = current_time - self._last_update_time
            if elapsed >= 1.0:  # 每秒结算一次
                await self._process_buffs(elapsed)
                self._last_update_time = current_time

            await asyncio.sleep(0.1)

    async def _process_ai_turns(self) -> None:
        """处理AI角色的行动."""
        now = time.time()

        for combatant in self.participants.values():
            if combatant.is_player:
                continue  # 玩家由外部输入驱动

            if not combatant.in_combat or not self._can_fight(combatant.character):
                continue

            if combatant.is_ready(now):
                action = await self._ai_decide(combatant)
                if action:
                    await self._execute_action(combatant, action)

    async def _ai_decide(self, combatant: Combatant) -> CombatAction | None:
        """AI决策行动."""
        from .ai import CombatAI

        ai = CombatAI()
        return await ai.decide(combatant.character, self)

    def _can_fight(self, character: Character) -> bool:
        """检查角色是否还能战斗."""
        hp, _ = character.get_hp()
        return hp > 0

    async def handle_player_command(
        self,
        character: Character,
        cmd: str,
        args: dict | None = None,
    ) -> tuple[bool, str]:
        """处理玩家战斗命令（使用策略模式）.

        Args:
            character: 玩家角色
            cmd: 命令（"kill", "cast", "flee", "defend"）
            args: 命令参数

        Returns:
            (是否成功, 消息)
        """
        args = args or {}
        combatant = self.participants.get(character.id)

        if not combatant or not combatant.in_combat:
            return False, "你不在战斗中"

        if not combatant.is_ready():
            remaining = combatant.get_remaining_cooldown()
            return False, f"你还不能行动（还需{remaining:.1f}秒）"

        # 获取策略
        strategies = _get_strategies()
        strategy = strategies.get(cmd)
        
        if not strategy:
            return False, f"未知的战斗命令: {cmd}"
        
        # 验证
        valid, msg = strategy.validate(self, combatant, args)
        if not valid:
            return False, msg
        
        # 执行
        result = await strategy.execute(self, combatant, args)
        
        # 设置冷却
        if result.success:
            cooldown = strategy.get_cooldown(args)
            combatant.set_cooldown(cooldown)
        
        return result.success, result.message

    async def _do_attack(
        self, combatant: Combatant, args: dict
    ) -> tuple[bool, str]:
        """执行普通攻击或招式攻击."""
        target = args.get("target")
        move = args.get("move")  # 可选，None表示普通攻击

        if not target:
            return False, "请指定攻击目标"

        # 检查目标是否在战斗中
        target_combatant = self.participants.get(target.id)
        if not target_combatant or not target_combatant.in_combat:
            return False, "目标不在战斗中"

        # 计算冷却时间
        cooldown = self._calculate_cooldown(combatant.character, move)

        # 执行攻击
        if move:
            # 使用招式
            result = await self._execute_move(combatant.character, target, move)
            msg = f"你对{target.name}使用「{move.name}」，" if result.is_hit else "你使用招式但未命中，"
            if result.damage > 0:
                msg += f"造成 {int(result.damage)} 点伤害！"
            if result.is_crit:
                msg += " 暴击！"
        else:
            # 普通攻击
            damage = self._calculate_normal_damage(combatant.character, target)
            target.modify_hp(-damage)
            result = type("obj", (object,), {"is_hit": True, "damage": damage, "is_crit": False})()
            msg = f"你攻击{target.name}，造成 {damage} 点伤害！"

        # 设置冷却
        combatant.set_cooldown(cooldown)

        self._log(msg)
        return True, msg

    async def _do_cast(
        self, combatant: Combatant, args: dict
    ) -> tuple[bool, str]:
        """执行施法（内功/特殊技能）(TD-023)（带事务保护）."""
        char = combatant.character
        
        # 获取要施放的内功
        neigong_key = args.get("neigong")
        if not neigong_key:
            return False, "未指定内功"
        
        # 检查是否学会该内功
        if not char.wuxue_has_learned(neigong_key):
            return False, "你尚未学会此内功"
        
        # 获取内功信息
        from src.game.data.wuxue_registry import get_kungfu
        neigong = get_kungfu(neigong_key)
        if not neigong:
            return False, "内功数据错误"
        
        # 检查内力消耗
        mp_cost = args.get("mp_cost", 20)
        if hasattr(char, 'mp') and char.mp < mp_cost:
            return False, "内力不足"
        
        # 获取内功效果
        effect = args.get("effect", "heal")
        power = args.get("power", 50)
        
        # 应用内功效果（带事务保护）
        try:
            with self.transaction() as txn:
                # 记录快照
                if hasattr(char, 'mp'):
                    txn.snapshot(char, ['mp'])
                
                # 消耗内力
                if hasattr(char, 'mp'):
                    char.mp -= mp_cost
                
                if effect == "heal":
                    # 治疗
                    if hasattr(char, 'hp'):
                        txn.snapshot(char, ['hp'])
                        old_hp = char.hp
                        char.hp = min(char.max_hp, char.hp + power)
                        healed = char.hp - old_hp
                        combatant.set_cooldown(3.0)
                        txn.commit()
                        return True, f"运功疗伤，恢复 {healed} 点气血"
                
                elif effect == "buff":
                    # 增益效果
                    buff_type = args.get("buff_type", "attack")
                    duration = args.get("duration", 10)
                    combatant.set_cooldown(2.0)
                    txn.commit()
                    return True, f"运起{neigong.name}，{buff_type}提升"
                
                elif effect == "attack":
                    # 内功攻击
                    target = self._get_target(combatant, args.get("target_id"))
                    if not target:
                        txn.rollback()
                        return False, "目标不存在"
                    
                    damage = power
                    if hasattr(target.character, 'hp'):
                        txn.snapshot(target.character, ['hp'])
                        target.character.hp -= damage
                    combatant.set_cooldown(4.0)
                    txn.commit()
                    return True, f"以{neigong.name}攻击，造成{damage}点伤害"
                
                txn.commit()
                return False, "未知内功效果"
                
        except Exception as e:
            logger.exception(f"内功施放失败: {e}")
            return False, f"施法失败: {e}"

    async def _do_flee(
        self, combatant: Combatant, args: dict
    ) -> tuple[bool, str]:
        """执行逃跑."""
        # 逃跑成功率基于敏捷差
        char = combatant.character
        enemies = [
            c.character
            for c in self.participants.values()
            if c.character.id != char.id and self._can_fight(c.character)
        ]

        if not enemies:
            return False, "没有敌人"

        avg_enemy_agility = sum(e.get_agility() for e in enemies) / len(enemies)
        agility_diff = char.get_agility() - avg_enemy_agility

        import random

        flee_chance = 0.5 + agility_diff * 0.02
        flee_chance = max(0.2, min(0.9, flee_chance))

        if random.random() < flee_chance:
            combatant.set_cooldown(self.FLEE_COOLDOWN)
            await self.stop(CombatResult.FLEE)
            return True, "你成功逃跑了！"
        else:
            combatant.set_cooldown(self.FLEE_COOLDOWN)
            return True, "逃跑失败！"

    async def _do_defend(
        self, combatant: Combatant, args: dict
    ) -> tuple[bool, str]:
        """执行防御."""
        # 添加防御BUFF
        from .buff import Buff, BuffType

        buff = Buff(
            key="defending",
            name="防御姿态",
            duration=1,
            buff_type=BuffType.BUFF,
            stats_mod={"defense": 20},
        )

        if hasattr(combatant.character, "buff_manager"):
            await combatant.character.buff_manager.add(buff)

        combatant.set_cooldown(1.5)  # 防御冷却较短
        return True, "你摆出防御姿态，准备抵挡攻击。"

    async def _process_buffs(self, elapsed: float) -> None:
        """处理BUFF效果（按实际时间结算）(TD-022).
        
        Args:
            elapsed: 经过的时间（秒）
        """
        for combatant in self.participants.values():
            if not combatant.in_combat:
                continue
            
            char = combatant.character
            if hasattr(char, 'buff_manager'):
                # 更新BUFF持续时间
                await char.buff_manager.update(elapsed)
                
                # 处理持续效果（如中毒、回血）
                for buff in char.buff_manager.active_buffs:
                    if hasattr(buff, 'dot_damage') and buff.dot_damage:
                        # 持续伤害
                        if hasattr(char, 'hp'):
                            char.hp -= buff.dot_damage * elapsed
                    if hasattr(buff, 'hot_heal') and buff.hot_heal:
                        # 持续治疗
                        if hasattr(char, 'hp'):
                            char.hp = min(char.max_hp, char.hp + buff.hot_heal * elapsed)

    async def _execute_action(
        self, combatant: Combatant, action: CombatAction
    ) -> None:
        """执行战斗行动（AI调用）."""
        if action.type == "move":
            await self._execute_move_action(combatant, action)
        elif action.type == "item":
            self._log(f"{combatant.character.name} 使用了物品")
        elif action.type == "flee":
            await self._do_flee(combatant, {})
        elif action.type == "defend":
            await self._do_defend(combatant, {})

    async def _execute_move_action(
        self, combatant: Combatant, action: CombatAction
    ) -> None:
        """执行招式攻击（AI调用）."""
        move = action.data.get("move")
        target = action.target

        if not target:
            return

        cooldown = self._calculate_cooldown(combatant.character, move)
        result = await self._execute_move(combatant.character, target, move)

        if result.is_hit and result.damage > 0:
            msg = f"{combatant.character.name} 使用「{move.name if move else '普通攻击'}」"
            if result.is_crit:
                msg += " 暴击！"
            msg += f" 对 {target.name} 造成 {int(result.damage)} 点伤害！"
        else:
            msg = f"{combatant.character.name} 的攻击被 {target.name} 闪开了！"

        self._log(msg)
        combatant.set_cooldown(cooldown)

    async def _execute_move(
        self, attacker: Character, defender: Character, move: Move | None
    ) -> DamageResult:
        """执行招式并计算伤害（带事务保护）."""
        from .calculator import CombatCalculator

        calculator = CombatCalculator()
        result = calculator.calculate_damage(attacker, defender, move, None)

        if result.is_hit and result.damage > 0:
            try:
                with self.transaction() as txn:
                    # 记录快照
                    txn.snapshot(defender, ['hp'])
                    
                    # 执行伤害
                    defender.modify_hp(-int(result.damage))
                    
                    # 提交事务
                    txn.commit()
            except Exception as e:
                logger.exception(f"战斗伤害结算失败: {e}")
                # 事务会自动回滚，返回未命中的结果
                result = type(
                    'DamageResult',
                    (),
                    {'damage': 0, 'is_hit': False, 'is_crit': False, 'messages': ['结算失败']}
                )()

        return result

    def _calculate_normal_damage(
        self, attacker: Character, defender: Character
    ) -> int:
        """计算普通攻击伤害."""
        import random

        attack = attacker.get_attack()
        defense = defender.get_defense()
        base_damage = max(1, attack - defense * 0.3)
        return int(base_damage * random.uniform(0.9, 1.1))

    def _calculate_cooldown(
        self, character: Character, move: Move | None
    ) -> float:
        """计算行动冷却时间.

        公式: 基础冷却 * (1 - 敏捷 * 系数)
        最小冷却: 1秒
        """
        if move and move.cooldown > 0:
            base = move.cooldown
        else:
            base = self.BASE_COOLDOWN

        agility = character.get_agility()
        reduction = agility * self.AGILITY_FACTOR
        cooldown = base * max(0.3, 1.0 - reduction)

        return max(self.MIN_COOLDOWN, cooldown)

    async def _check_end(self) -> CombatResult | None:
        """检查战斗是否结束."""
        alive_fighters = [
            c for c in self.participants.values() if self._can_fight(c.character)
        ]

        if len(alive_fighters) <= 1:
            if alive_fighters:
                self.winner = alive_fighters[0].character
                # 判断是玩家胜利还是失败
                if alive_fighters[0].is_player:
                    return CombatResult.WIN
                else:
                    return CombatResult.LOSE
            else:
                return CombatResult.DRAW

        return None

    def _log(self, message: str) -> None:
        """记录战斗日志."""
        self.log.append(message)

    def get_alive_enemies(self, character: Character) -> list[Character]:
        """获取存活的敌人列表."""
        return [
            c.character
            for c in self.participants.values()
            if c.character.id != character.id and self._can_fight(c.character)
        ]

    def is_in_combat(self, character: Character) -> bool:
        """检查角色是否在战斗中."""
        combatant = self.participants.get(character.id)
        return combatant is not None and combatant.in_combat
