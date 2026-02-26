"""战斗策略模式.

提供可扩展的战斗行动策略系统。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .core import CombatSession, Combatant
    from src.game.typeclasses.character import Character
    from src.game.typeclasses.wuxue import Move


@dataclass
class ActionResult:
    """行动结果."""
    success: bool = False
    message: str = ""
    damage: int = 0
    side_effects: list[dict] = field(default_factory=list)
    
    def add_side_effect(self, effect_type: str, data: dict):
        """添加副作用记录，用于回滚."""
        self.side_effects.append({"type": effect_type, "data": data})


class CombatActionStrategy(ABC):
    """战斗行动策略基类."""
    
    @abstractmethod
    async def execute(
        self, 
        session: CombatSession, 
        combatant: Combatant, 
        args: dict
    ) -> ActionResult:
        """执行行动.
        
        Args:
            session: 战斗会话
            combatant: 行动者
            args: 行动参数
            
        Returns:
            行动结果
        """
        pass
    
    @abstractmethod
    def validate(
        self, 
        session: CombatSession, 
        combatant: Combatant, 
        args: dict
    ) -> tuple[bool, str]:
        """验证行动是否可行.
        
        Args:
            session: 战斗会话
            combatant: 行动者
            args: 行动参数
            
        Returns:
            (是否可行, 错误信息)
        """
        pass
    
    def get_cooldown(self, args: dict) -> float:
        """获取行动冷却时间.
        
        Args:
            args: 行动参数
            
        Returns:
            冷却时间（秒）
        """
        return 3.0  # 默认3秒
    
    def get_mp_cost(self, args: dict) -> int:
        """获取内力消耗.
        
        Args:
            args: 行动参数
            
        Returns:
            内力消耗
        """
        return 0  # 默认不消耗


class AttackStrategy(CombatActionStrategy):
    """攻击策略."""
    
    def validate(
        self, 
        session: CombatSession, 
        combatant: Combatant, 
        args: dict
    ) -> tuple[bool, str]:
        """验证攻击."""
        target = args.get("target")
        if not target:
            return False, "请指定攻击目标"
        
        # 检查目标是否在战斗中
        target_combatant = session.participants.get(target.id)
        if not target_combatant or not target_combatant.in_combat:
            return False, "目标不在战斗中"
        
        return True, ""
    
    async def execute(
        self, 
        session: CombatSession, 
        combatant: Combatant, 
        args: dict
    ) -> ActionResult:
        """执行攻击."""
        target = args.get("target")
        move = args.get("move")
        
        char = combatant.character
        
        # 计算伤害
        if move:
            # 使用招式
            from .calculator import CombatCalculator
            calculator = CombatCalculator()
            damage_result = calculator.calculate_damage(char, target, move, None)
            
            if damage_result.is_hit and damage_result.damage > 0:
                # 使用事务保护
                with session.transaction() as txn:
                    txn.snapshot(target, ['hp'])
                    target.modify_hp(-int(damage_result.damage))
                    txn.commit()
                
                msg = f"你对{target.name}使用「{move.name}」，造成 {int(damage_result.damage)} 点伤害！"
                if damage_result.is_crit:
                    msg += " 暴击！"
                
                return ActionResult(
                    success=True,
                    message=msg,
                    damage=int(damage_result.damage)
                )
            else:
                return ActionResult(
                    success=True,
                    message=f"你使用招式但未命中。"
                )
        else:
            # 普通攻击
            damage = session._calculate_normal_damage(char, target)
            
            with session.transaction() as txn:
                txn.snapshot(target, ['hp'])
                target.modify_hp(-damage)
                txn.commit()
            
            return ActionResult(
                success=True,
                message=f"你攻击{target.name}，造成 {damage} 点伤害！",
                damage=damage
            )
    
    def get_cooldown(self, args: dict) -> float:
        """获取冷却时间."""
        move = args.get("move")
        if move and move.cooldown > 0:
            return move.cooldown
        return 3.0


class CastStrategy(CombatActionStrategy):
    """内功施放策略."""
    
    def validate(
        self, 
        session: CombatSession, 
        combatant: Combatant, 
        args: dict
    ) -> tuple[bool, str]:
        """验证施法."""
        neigong_key = args.get("neigong")
        if not neigong_key:
            return False, "未指定内功"
        
        char = combatant.character
        if not char.wuxue_has_learned(neigong_key):
            return False, "你尚未学会此内功"
        
        mp_cost = args.get("mp_cost", 20)
        if hasattr(char, 'mp') and char.mp < mp_cost:
            return False, "内力不足"
        
        return True, ""
    
    async def execute(
        self, 
        session: CombatSession, 
        combatant: Combatant, 
        args: dict
    ) -> ActionResult:
        """执行施法."""
        char = combatant.character
        neigong_key = args.get("neigong")
        effect = args.get("effect", "heal")
        power = args.get("power", 50)
        mp_cost = args.get("mp_cost", 20)
        
        try:
            with session.transaction() as txn:
                # 消耗内力
                if hasattr(char, 'mp'):
                    txn.snapshot(char, ['mp'])
                    char.mp -= mp_cost
                
                if effect == "heal":
                    # 治疗
                    if hasattr(char, 'hp'):
                        txn.snapshot(char, ['hp'])
                        old_hp = char.hp
                        char.hp = min(char.max_hp, char.hp + power)
                        healed = char.hp - old_hp
                        txn.commit()
                        return ActionResult(
                            success=True,
                            message=f"运功疗伤，恢复 {healed} 点气血"
                        )
                
                elif effect == "buff":
                    txn.commit()
                    buff_type = args.get("buff_type", "attack")
                    return ActionResult(
                        success=True,
                        message=f"运起内功，{buff_type}提升"
                    )
                
                elif effect == "attack":
                    target_id = args.get("target_id")
                    target = None
                    if target_id:
                        for pid, p in session.participants.items():
                            if p.character.id == target_id:
                                target = p.character
                                break
                    
                    if target and hasattr(target, 'hp'):
                        txn.snapshot(target, ['hp'])
                        target.hp -= power
                        txn.commit()
                        return ActionResult(
                            success=True,
                            message=f"以内功攻击，造成{power}点伤害",
                            damage=power
                        )
                    else:
                        txn.rollback()
                        return ActionResult(
                            success=False,
                            message="目标不存在"
                        )
                
                txn.commit()
                return ActionResult(
                    success=False,
                    message="未知内功效果"
                )
                
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"施法失败: {e}"
            )
    
    def get_cooldown(self, args: dict) -> float:
        """获取冷却时间."""
        effect = args.get("effect", "heal")
        cooldowns = {
            "heal": 3.0,
            "buff": 2.0,
            "attack": 4.0
        }
        return cooldowns.get(effect, 3.0)
    
    def get_mp_cost(self, args: dict) -> int:
        """获取内力消耗."""
        return args.get("mp_cost", 20)


class FleeStrategy(CombatActionStrategy):
    """逃跑策略."""
    
    def validate(
        self, 
        session: CombatSession, 
        combatant: Combatant, 
        args: dict
    ) -> tuple[bool, str]:
        """验证逃跑."""
        char = combatant.character
        enemies = [
            c.character
            for c in session.participants.values()
            if c.character.id != char.id and session._can_fight(c.character)
        ]
        
        if not enemies:
            return False, "没有敌人"
        
        return True, ""
    
    async def execute(
        self, 
        session: CombatSession, 
        combatant: Combatant, 
        args: dict
    ) -> ActionResult:
        """执行逃跑."""
        import random
        
        char = combatant.character
        enemies = [
            c.character
            for c in session.participants.values()
            if c.character.id != char.id and session._can_fight(c.character)
        ]
        
        avg_enemy_agility = sum(e.get_agility() for e in enemies) / len(enemies)
        agility_diff = char.get_agility() - avg_enemy_agility
        
        flee_chance = 0.5 + agility_diff * 0.02
        flee_chance = max(0.2, min(0.9, flee_chance))
        
        if random.random() < flee_chance:
            from .core import CombatResult
            await session.stop(CombatResult.FLEE)
            return ActionResult(
                success=True,
                message="你成功逃跑了！"
            )
        else:
            return ActionResult(
                success=True,
                message="逃跑失败！"
            )
    
    def get_cooldown(self, args: dict) -> float:
        """逃跑冷却时间."""
        return 5.0


class DefendStrategy(CombatActionStrategy):
    """防御策略."""
    
    def validate(
        self, 
        session: CombatSession, 
        combatant: Combatant, 
        args: dict
    ) -> tuple[bool, str]:
        """验证防御."""
        return True, ""
    
    async def execute(
        self, 
        session: CombatSession, 
        combatant: Combatant, 
        args: dict
    ) -> ActionResult:
        """执行防御."""
        from .buff import Buff, BuffType
        
        buff = Buff(
            key="defending",
            name="防御姿态",
            duration=3.0,
            buff_type=BuffType.BUFF,
            stats_mod={"defense": 20},
        )
        
        char = combatant.character
        if hasattr(char, "buff_manager"):
            await char.buff_manager.add(buff)
        
        return ActionResult(
            success=True,
            message="你摆出防御姿态，准备抵挡攻击。"
        )
    
    def get_cooldown(self, args: dict) -> float:
        """防御冷却时间."""
        return 1.5
