# 战斗系统（即时制）

## 概述

即时制战斗系统，玩家可随时输入命令，各行动有独立的冷却时间。

## 设计原则

- **无回合等待**：玩家无需等待"回合"，随时可输入命令
- **行动冷却**：每个招式/动作有独立冷却时间（受敏捷影响）
- **实时输出**：战斗消息实时推送到所有参与者
- **自由命令**：战斗中可以使用任何命令（逃跑、吃药、切换武器等）

## 战斗会话

```python
# src/game/combat/core.py
from enum import Enum
from typing import Optional, TYPE_CHECKING
import asyncio
import time

if TYPE_CHECKING:
    from ..typeclasses.character import Character


class CombatResult(Enum):
    """战斗结果"""
    WIN = "win"
    LOSE = "lose"
    DRAW = "draw"
    FLEE = "flee"


class Combatant:
    """战斗参与者封装
    
    管理参与者的冷却时间和状态。
    """
    
    def __init__(self, character: Character, is_player: bool = False):
        self.character = character
        self.is_player = is_player
        self.next_action_time: float = 0.0
        self.in_combat: bool = False
    
    def is_ready(self, now: float | None = None) -> bool:
        """检查是否可以行动"""
        if now is None:
            now = time.time()
        return now >= self.next_action_time
    
    def set_cooldown(self, cooldown: float) -> None:
        """设置下次可行动时间"""
        self.next_action_time = time.time() + cooldown
    
    def get_remaining_cooldown(self) -> float:
        """获取剩余冷却时间（秒）"""
        remaining = self.next_action_time - time.time()
        return max(0.0, remaining)


class CombatSession:
    """即时制战斗会话
    
    管理一场战斗的完整流程：
    - 参与者管理（玩家和NPC）
    - 实时行动冷却
    - 伤害结算
    - 胜负判定
    """
    
    # 基础冷却时间（秒）
    BASE_COOLDOWN = 3.0
    # 敏捷对冷却的影响系数
    AGILITY_FACTOR = 0.02
    # 最小冷却时间
    MIN_COOLDOWN = 1.0
    
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
        
        # 初始化参与者
        for char in participants:
            is_player = player_character is not None and char.id == player_character.id
            self.participants[char.id] = Combatant(char, is_player)
    
    async def start(self) -> None:
        """开始战斗"""
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
        """停止战斗"""
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
    
    async def _combat_loop(self) -> None:
        """战斗主循环（100ms tick）"""
        while self.active:
            await self._process_ai_turns()
            
            # 检查战斗结束
            if result := await self._check_end():
                await self.stop(result)
                return
            
            await asyncio.sleep(0.1)
    
    async def _process_ai_turns(self) -> None:
        """处理AI角色的行动"""
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
    
    async def handle_player_command(
        self, character: Character, cmd: str, args: dict | None = None
    ) -> tuple[bool, str]:
        """处理玩家战斗命令
        
        Args:
            character: 玩家角色
            cmd: 命令（"kill", "cast", "flee", "defend"）
            args: 命令参数
        
        Returns:
            (是否成功, 消息)
        """
        # 检查角色是否准备好行动
        combatant = self.participants.get(character.id)
        if not combatant or not combatant.in_combat:
            return False, "你不在战斗中"
        
        if not combatant.is_ready():
            remaining = combatant.get_remaining_cooldown()
            return False, f"你还不能行动（还需{remaining:.1f}秒）"
        
        # 执行命令...
    
    def _calculate_cooldown(
        self, character: Character, move: Move | None
    ) -> float:
        """计算行动冷却时间
        
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
```

## 战斗数值计算

```python
# src/game/combat/calculator.py
@dataclass
class DamageResult:
    """伤害结果"""
    damage: float = 0
    is_crit: bool = False
    is_hit: bool = True
    messages: list[str] | None = None


class CombatCalculator:
    """战斗数值计算器"""
    
    BASE_CRIT_RATE = 0.05
    CRIT_DAMAGE = 1.5
    BASE_HIT_RATE = 0.90
    DAMAGE_VARIANCE = 0.1
    
    @staticmethod
    def calculate_damage(
        attacker: Character,
        defender: Character,
        move: Move | None,
        context: CombatContext | None,
    ) -> DamageResult:
        """计算伤害
        
        流程：
        1. 命中率判定
        2. 基础伤害 = 攻击力 * 招式倍率
        3. 防御减免
        4. 招式克制加成
        5. 随机浮动
        6. 暴击判定
        """
        # ...
    
    @staticmethod
    def calculate_hit_rate(
        attacker: Character, defender: Character, move: Move | None
    ) -> float:
        """命中率 = 基础命中 + (敏捷差 * 0.5%) + 招式修正"""
        base_hit = 0.90
        agility_diff = attacker.get_agility() - defender.get_agility()
        hit_mod = agility_diff * 0.005
        return max(0.3, min(0.95, base_hit + hit_mod))
```

## BUFF/DEBUFF系统

```python
# src/game/combat/buff.py
class BuffType(Enum):
    BUFF = "buff"
    DEBUFF = "debuff"
    NEUTRAL = "neutral"


class Buff:
    """状态效果
    
    Attributes:
        key: 唯一标识
        name: 显示名
        duration: 持续时间（秒）
        buff_type: BUFF类型
        stack_limit: 叠加上限
        stats_mod: 属性修正
    """
    
    def __init__(
        self,
        key: str,
        name: str,
        duration: float,  # 持续时间（秒）
        buff_type: BuffType = BuffType.NEUTRAL,
        stack_limit: int = 1,
        stats_mod: dict[str, int] | None = None,
        on_apply: Callable | None = None,
        on_tick: Callable | None = None,
        on_remove: Callable | None = None,
    ):
        self.key = key
        self.name = name
        self.duration = duration
        self.buff_type = buff_type
        self.stack_limit = stack_limit
        self.stats_mod = stats_mod or {}
        
        self._on_apply = on_apply
        self._on_tick = on_tick
        self._on_remove = on_remove
        
        self.stacks = 1
        self.applied_at = time.time()
        self.expires_at = self.applied_at + duration
    
    def is_expired(self, now: float | None = None) -> bool:
        """检查是否已过期"""
        if now is None:
            now = time.time()
        return now >= self.expires_at


class BuffManager:
    """角色BUFF管理"""
    
    def __init__(self, character: Character):
        self.character = character
        self._buffs: dict[str, Buff] = {}
    
    async def add(self, buff: Buff) -> bool:
        """添加BUFF"""
        # ...
    
    async def tick(self) -> list[str]:
        """执行BUFF结算，清理过期BUFF"""
        # ...
    
    def get_stats_modifier(self) -> dict[str, int]:
        """获取所有BUFF的属性修正总和"""
        # ...
```

## 战斗AI

```python
# src/game/combat/ai.py
class CombatAI:
    """基础战斗AI"""
    
    async def decide(
        self, character: Character, combat: CombatSession
    ) -> CombatAction:
        """AI决策"""
        # 获取可用招式
        moves = character.get_available_moves()
        
        # 获取存活的目标
        targets = combat.get_alive_enemies(character)
        
        if not targets:
            return CombatAction("defend")
        
        target = random.choice(targets)
        
        # 简单AI：80%攻击，20%防御
        if random.random() < 0.8 and moves:
            kungfu, move = random.choice(moves)
            return CombatAction("move", target, {"move": move})
        
        return CombatAction("defend")


class SmartAI(CombatAI):
    """智能AI
    
    策略：
    - 血量低时优先逃跑或防御
    - 选择克制对手的招式
    """
    
    async def decide(self, character, combat) -> CombatAction:
        hp, max_hp = character.get_hp()
        hp_ratio = hp / max_hp
        
        # 低血量时的决策
        if hp_ratio < 0.3:
            if random.random() < 0.4:
                return CombatAction("flee")
            return CombatAction("defend")
        
        return await super().decide(character, combat)


class AggressiveAI(CombatAI):
    """激进AI - 总是优先攻击"""
    pass


class DefensiveAI(CombatAI):
    """防御型AI - 经常使用防御"""
    pass
```

## 冷却时间公式

```
冷却时间 = 基础冷却 * (1 - 敏捷 * 0.02)
最小冷却 = 1.0秒

示例：
- 基础冷却3秒，敏捷20点
- 冷却 = 3 * (1 - 20 * 0.02) = 3 * 0.6 = 1.8秒

- 基础冷却5秒，敏捷30点
- 冷却 = 5 * (1 - 30 * 0.02) = 5 * 0.4 = 2.0秒
```

## 玩家体验示例

```
[战斗中]
你对土匪使用了「亢龙有悔」，造成 156 点伤害！
土匪还剩 45/200 气血。

【2.5秒后可以再次行动】

> kill bandit
你还不能行动（还需1.2秒）

> 
土匪对你使用「黑风刀法」，造成 34 点伤害！

> kill bandit
你攻击土匪，造成 78 点伤害！
土匪倒下了！

战斗胜利！
```
