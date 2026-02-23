# 战斗系统

## 概述

战斗系统支持回合制和即时制双模式，包含战斗AI、数值计算和BUFF/DEBUFF系统。

## 战斗实例

```python
# src/game/combat/core.py
from enum import Enum
from typing import Optional, TYPE_CHECKING
import asyncio

if TYPE_CHECKING:
    from ..typeclasses.character import Character


class CombatMode(Enum):
    """战斗模式"""
    TURN = "turn"      # 回合制
    TIME = "time"      # 即时制（时间条）


class CombatResult(Enum):
    """战斗结果"""
    WIN = "win"
    LOSE = "lose"
    DRAW = "draw"
    FLEE = "flee"


class CombatInstance:
    """战斗实例
    
    管理一场战斗的完整流程：
    - 参与者管理
    - 回合/时间条控制
    - 行动执行
    - 胜负判定
    """
    
    def __init__(
        self, 
        engine: "GameEngine",
        participants: list["Character"],
        mode: CombatMode = CombatMode.TURN
    ):
        self.engine = engine
        self.participants = participants
        self.mode = mode
        self.round_num = 0
        self.active = False
        
        # 回合制
        self.current_turn_idx = 0
        self.turn_queue: asyncio.Queue = asyncio.Queue()
        
        # 即时制
        self.time_queue: list[tuple[float, "Character"]] = []  # (time_ready, character)
        
        # 结果
        self.result: Optional[CombatResult] = None
        self.winner: Optional["Character"] = None
        
        # 日志
        self.log: list[str] = []
    
    async def start(self) -> None:
        """开始战斗"""
        self.active = True
        self.round_num = 1
        
        # 触发战斗开始事件
        for p in self.participants:
            p.at_combat_start(self)
        
        # 启动战斗循环
        if self.mode == CombatMode.TURN:
            await self._turn_loop()
        else:
            await self._time_loop()
    
    async def stop(self) -> None:
        """停止战斗"""
        self.active = False
        
        # 触发战斗结束事件
        for p in self.participants:
            p.at_combat_end(self)
    
    async def _turn_loop(self) -> None:
        """回合制主循环"""
        while self.active:
            turn_order = self._get_turn_order()
            
            for character in turn_order:
                if not self.active:
                    break
                
                # 检查角色是否还能战斗
                if not self._can_fight(character):
                    continue
                
                # 等待玩家输入或AI决策
                action = await self._get_action(character)
                
                if action:
                    await self._execute_action(character, action)
                
                # 检查战斗结束
                if result := await self._check_end():
                    self.result = result
                    await self.stop()
                    return
            
            # 回合结束处理
            await self._on_round_end()
            self.round_num += 1
    
    async def _time_loop(self) -> None:
        """即时制主循环（时间条）"""
        # 初始化时间队列
        for p in self.participants:
            self._update_time_queue(p, 0)
        
        while self.active:
            if not self.time_queue:
                await asyncio.sleep(0.1)
                continue
            
            # 获取时间最短的参与者
            self.time_queue.sort(key=lambda x: x[0])
            ready_time, character = self.time_queue.pop(0)
            
            # 等待到该角色行动
            wait_time = max(0, ready_time - self._get_current_time())
            if wait_time > 0:
                await asyncio.sleep(wait_time / 10)  # 加速时间
            
            if not self.active:
                break
            
            # 执行行动
            action = await self._get_action(character)
            if action:
                await self._execute_action(character, action)
            
            # 重新加入队列
            self._update_time_queue(character, ready_time)
            
            # 检查战斗结束
            if result := await self._check_end():
                self.result = result
                await self.stop()
                return
    
    def _get_turn_order(self) -> list["Character"]:
        """根据速度决定行动顺序"""
        fighters = [p for p in self.participants if self._can_fight(p)]
        return sorted(fighters, key=lambda c: c.get_agility(), reverse=True)
    
    def _update_time_queue(self, character: "Character", base_time: float) -> None:
        """更新角色在时间队列中的位置"""
        speed = character.get_agility()
        ready_time = base_time + (100 / max(1, speed))  # 速度越快，等待时间越短
        self.time_queue.append((ready_time, character))
    
    def _get_current_time(self) -> float:
        """获取当前时间"""
        # 使用最小时间作为当前时间
        if self.time_queue:
            return min(t for t, _ in self.time_queue)
        return 0
    
    def _can_fight(self, character: "Character") -> bool:
        """检查角色是否还能战斗"""
        hp, _ = character.get_hp()
        return hp > 0
    
    async def _get_action(self, character: "Character") -> Optional["CombatAction"]:
        """获取角色行动"""
        # TODO: 判断是玩家还是AI
        # if character.is_player:
        #     return await self._wait_player_input(character)
        # else:
        #     return await self._ai_decide(character)
        return None
    
    async def _execute_action(
        self, 
        character: "Character", 
        action: "CombatAction"
    ) -> None:
        """执行战斗行动"""
        if action.type == "move":
            # 执行招式
            await self._execute_move(character, action)
        elif action.type == "item":
            # 使用物品
            await self._execute_item(character, action)
        elif action.type == "flee":
            # 逃跑
            await self._execute_flee(character, action)
        elif action.type == "defend":
            # 防御
            await self._execute_defend(character, action)
    
    async def _execute_move(self, character: "Character", action: "CombatAction") -> None:
        """执行招式"""
        from ..typeclasses.wuxue import CombatContext, execute_move_script
        
        move = action.data.get("move")
        target = action.target
        
        if not move or not target:
            return
        
        # 构建战斗上下文
        context = CombatContext(
            caster=character,
            target=target,
            environment=character.location,
            round_num=self.round_num,
        )
        
        # 执行招式效果脚本
        result = execute_move_script(move, context)
        
        # 应用伤害
        if result.damage > 0:
            actual_damage = target.modify_hp(-int(result.damage))
            self.log.append(f"{target.name}受到{abs(actual_damage)}点伤害")
        
        # 应用治疗
        if result.heal > 0:
            character.modify_hp(int(result.heal))
        
        # 记录日志
        self.log.extend(result.messages)
    
    async def _check_end(self) -> Optional[CombatResult]:
        """检查战斗是否结束
        
        Returns:
            战斗结果，未结束返回None
        """
        alive = [p for p in self.participants if self._can_fight(p)]
        
        if len(alive) <= 1:
            if alive:
                self.winner = alive[0]
                return CombatResult.WIN
            else:
                return CombatResult.DRAW
        
        # 检查是否逃跑成功
        # TODO
        
        return None
    
    async def _on_round_end(self) -> None:
        """回合结束处理"""
        for p in self.participants:
            # BUFF/DEBUFF结算
            if hasattr(p, "buff_manager"):
                await p.buff_manager.tick()
            
            # 每回合恢复少量内力
            p.modify_mp(1)
    
    async def player_input(
        self, 
        character: "Character", 
        command: str
    ) -> None:
        """接收玩家战斗指令"""
        # TODO: 解析命令并放入队列
        pass


class CombatAction:
    """战斗行动"""
    
    def __init__(
        self,
        type: str,  # "move", "item", "flee", "defend"
        target: Optional["Character"] = None,
        data: dict = None
    ):
        self.type = type
        self.target = target
        self.data = data or {}
```

## 战斗数值计算

```python
# src/game/combat/calculator.py
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..typeclasses.character import Character
    from ..typeclasses.wuxue import Move


@dataclass
class DamageResult:
    """伤害结果"""
    damage: float
    is_crit: bool
    is_hit: bool
    messages: list[str]


class CombatCalculator:
    """战斗数值计算器"""
    
    @staticmethod
    def calculate_damage(
        attacker: "Character",
        defender: "Character",
        move: "Move",
        context: "CombatContext"
    ) -> DamageResult:
        """
        伤害计算流程：
        1. 基础伤害 = 攻击力 * 招式倍率
        2. 防御减免 = 基础伤害 - 防御力
        3. 招式克制加成
        4. 环境加成
        5. 随机浮动 (0.9-1.1)
        """
        messages = []
        
        # 1. 基础伤害
        base_damage = attacker.get_attack() * 1.5  # 招式倍率
        
        # 2. 防御减免
        defense = defender.get_defense()
        damage_after_def = max(1, base_damage - defense * 0.5)
        
        # 3. 招式克制
        from .counter import get_counter_modifier
        counter_mod = get_counter_modifier(move.wuxue_type, None)  # TODO: 防御者招式类型
        damage_after_counter = damage_after_def * counter_mod
        
        if counter_mod > 1:
            messages.append("招式克制！伤害增加！")
        elif counter_mod < 1:
            messages.append("招式被克！伤害减少！")
        
        # 4. 环境加成
        env_mod = CombatCalculator.get_environment_bonus(context)
        damage_after_env = damage_after_counter * env_mod.get("damage", 1.0)
        
        # 5. 随机浮动
        import random
        final_damage = damage_after_env * random.uniform(0.9, 1.1)
        
        # 暴击判定
        is_crit = random.random() < 0.1  # 10%暴击率
        if is_crit:
            final_damage *= 1.5
            messages.append("暴击！")
        
        return DamageResult(
            damage=max(1, final_damage),
            is_crit=is_crit,
            is_hit=True,
            messages=messages
        )
    
    @staticmethod
    def calculate_hit_rate(
        attacker: "Character",
        defender: "Character",
        move: "Move"
    ) -> float:
        """
        命中率 = 基础命中 + (敏捷差 * 0.5%) + 招式修正
        """
        base_hit = 0.9
        agility_diff = attacker.get_agility() - defender.get_agility()
        hit_mod = agility_diff * 0.005
        
        return max(0.3, min(0.95, base_hit + hit_mod))
    
    @staticmethod
    def get_environment_bonus(context: "CombatContext") -> dict[str, float]:
        """
        环境加成：
        - 高地 -> +10%命中
        - 雨天 -> 火系-20%，水系+20%
        - 夜间 -> -20%命中（无照明）
        """
        bonus = {"damage": 1.0, "hit": 1.0}
        
        room = context.environment
        if not room:
            return bonus
        
        env = room.environment
        
        # 天气影响
        weather = env.get("weather", "clear")
        if weather == "rain":
            # TODO: 根据招式属性调整
            pass
        
        # 光照影响
        light = env.get("light", 100)
        if light < 30:
            bonus["hit"] *= 0.8
        
        return bonus
```

## BUFF/DEBUFF系统

```python
# src/game/combat/buff.py
from enum import Enum
from typing import Optional, Callable
import time


class BuffType(Enum):
    """BUFF类型"""
    BUFF = "buff"      # 增益
    DEBUFF = "debuff"  # 减益
    NEUTRAL = "neutral"  # 中性


class Buff:
    """状态效果"""
    
    def __init__(
        self,
        key: str,
        name: str,
        duration: int,  # 持续回合数
        buff_type: BuffType = BuffType.NEUTRAL,
        stack_limit: int = 1,
        stats_mod: dict = None,
        on_apply: Optional[str] = None,
        on_tick: Optional[str] = None,
        on_remove: Optional[str] = None,
    ):
        self.key = key
        self.name = name
        self.duration = duration
        self.buff_type = buff_type
        self.stack_limit = stack_limit
        self.stats_mod = stats_mod or {}
        self.on_apply_script = on_apply
        self.on_tick_script = on_tick
        self.on_remove_script = on_remove
        
        self.stacks = 1
        self.applied_at = time.time()
    
    def is_expired(self) -> bool:
        """是否已过期"""
        return self.duration <= 0


class BuffManager:
    """角色BUFF管理"""
    
    def __init__(self, character: "Character"):
        self.character = character
        self._buffs: dict[str, Buff] = {}
    
    async def add(self, buff: Buff) -> bool:
        """添加BUFF
        
        Args:
            buff: BUFF对象
            
        Returns:
            是否成功添加
        """
        existing = self._buffs.get(buff.key)
        
        if existing:
            # 叠加
            if existing.stacks < existing.stack_limit:
                existing.stacks += 1
                existing.duration = max(existing.duration, buff.duration)
                return True
            else:
                # 已达叠加上限，刷新持续时间
                existing.duration = buff.duration
                return True
        else:
            # 新BUFF
            self._buffs[buff.key] = buff
            # 执行应用脚本
            await self._execute_script(buff.on_apply_script)
            return True
    
    async def remove(self, buff_key: str) -> bool:
        """移除BUFF"""
        buff = self._buffs.pop(buff_key, None)
        if buff:
            await self._execute_script(buff.on_remove_script)
            return True
        return False
    
    async def tick(self) -> None:
        """回合结束时的BUFF结算"""
        expired = []
        
        for key, buff in self._buffs.items():
            # 执行每回合脚本
            if buff.on_tick_script:
                await self._execute_script(buff.on_tick_script)
            
            # 减少持续时间
            buff.duration -= 1
            
            if buff.is_expired():
                expired.append(key)
        
        # 移除过期BUFF
        for key in expired:
            await self.remove(key)
    
    def get_stats_modifier(self) -> dict[str, int]:
        """获取所有BUFF的属性修正总和"""
        total = {}
        
        for buff in self._buffs.values():
            for stat, value in buff.stats_mod.items():
                total[stat] = total.get(stat, 0) + value * buff.stacks
        
        return total
    
    def has_buff(self, buff_key: str) -> bool:
        """检查是否有指定BUFF"""
        return buff_key in self._buffs
    
    def get_buffs(self, buff_type: BuffType = None) -> list[Buff]:
        """获取BUFF列表"""
        if buff_type:
            return [b for b in self._buffs.values() if b.buff_type == buff_type]
        return list(self._buffs.values())
    
    async def _execute_script(self, script: Optional[str]) -> None:
        """执行BUFF脚本"""
        if not script:
            return
        
        # TODO: 安全执行脚本
        pass
    
    def clear(self) -> None:
        """清除所有BUFF"""
        self._buffs.clear()


# 常用BUFF定义
BUFF_STUN = Buff(
    key="stun",
    name="眩晕",
    duration=1,
    buff_type=BuffType.DEBUFF,
    stats_mod={"agility": -50},
)

BUFF_POISON = Buff(
    key="poison",
    name="中毒",
    duration=5,
    buff_type=BuffType.DEBUFF,
    on_tick="target.modify_hp(-5)",
)

BUFF_DEFENSE_UP = Buff(
    key="defense_up",
    name="防御提升",
    duration=3,
    buff_type=BuffType.BUFF,
    stats_mod={"defense": 20},
)
```

## 战斗AI

```python
# src/game/combat/ai.py
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..typeclasses.character import Character
    from .core import CombatInstance, CombatAction


class CombatAI:
    """战斗AI"""
    
    def __init__(self, ai_type: str = "normal"):
        self.ai_type = ai_type
    
    async def decide(
        self, 
        character: "Character", 
        combat: CombatInstance
    ) -> "CombatAction":
        """AI决策
        
        Args:
            character: AI控制的角色
            combat: 战斗实例
            
        Returns:
            战斗行动
        """
        # 获取可用招式
        moves = character.get_available_moves()
        
        # 获取目标（敌方）
        targets = [p for p in combat.participants 
                   if p != character and combat._can_fight(p)]
        
        if not targets:
            return CombatAction("defend")
        
        target = random.choice(targets)
        
        # 简单AI：随机选择招式
        if moves:
            kungfu, move = random.choice(moves)
            return CombatAction(
                type="move",
                target=target,
                data={"move": move, "kungfu": kungfu}
            )
        
        # 无招式，普通攻击
        return CombatAction("move", target, {"move": None})


class SmartAI(CombatAI):
    """智能AI"""
    
    async def decide(
        self, 
        character: "Character", 
        combat: CombatInstance
    ) -> "CombatAction":
        """智能决策
        
        策略：
        - 血量低时优先防御或治疗
        - 选择克制对手的招式
        - 保留强力招式的冷却
        """
        hp, max_hp = character.get_hp()
        hp_ratio = hp / max_hp
        
        # 血量低时可能逃跑或防御
        if hp_ratio < 0.2:
            if random.random() < 0.3:
                return CombatAction("flee")
            return CombatAction("defend")
        
        # 否则使用父类逻辑
        return await super().decide(character, combat)
```
