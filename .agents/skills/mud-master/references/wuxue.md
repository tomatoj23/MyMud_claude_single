# 武学系统

## 概述

武学系统包括武功定义、招式系统、学习进度、克制关系和招式效果脚本沙箱。

## 武学类型定义

```python
# src/game/typeclasses/wuxue.py
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable


class WuxueType(Enum):
    """武学类型"""
    QUAN = "quan"           # 拳
    ZHANG = "zhang"         # 掌
    ZHI = "zhi"             # 指
    JIAN = "jian"           # 剑
    DAO = "dao"             # 刀
    GUN = "gun"             # 棍/杖
    NEIGONG = "neigong"     # 内功
    QINGGONG = "qinggong"   # 轻功


WUXUE_TYPE_NAMES = {
    WuxueType.QUAN: "拳法",
    WuxueType.ZHANG: "掌法",
    WuxueType.ZHI: "指法",
    WuxueType.JIAN: "剑法",
    WuxueType.DAO: "刀法",
    WuxueType.GUN: "棍法",
    WuxueType.NEIGONG: "内功",
    WuxueType.QINGGONG: "轻功",
}
```

## Move 招式定义

```python
# src/game/typeclasses/wuxue.py
from dataclasses import dataclass
from typing import Any


@dataclass
class Move:
    """招式定义
    
    Attributes:
        key: 唯一标识
        name: 显示名
        wuxue_type: 武学类型
        mp_cost: 内力消耗
        ep_cost: 精力消耗
        cooldown: 冷却时间（秒）
        effect_script: 效果脚本（Python代码）
        counters: 克制的武学类型
        countered_by: 被克制的武学类型
    """
    key: str
    name: str
    wuxue_type: WuxueType
    mp_cost: int = 10
    ep_cost: int = 5
    cooldown: float = 0.0
    effect_script: str = ""
    counters: list[WuxueType] = None
    countered_by: list[WuxueType] = None
    
    def __post_init__(self):
        if self.counters is None:
            self.counters = []
        if self.countered_by is None:
            self.countered_by = []


# 招式效果结果
@dataclass
class MoveEffectResult:
    """招式效果结果"""
    damage: float = 0
    heal: float = 0
    effects: list[str] = None  # stun, poison, buff等
    messages: list[str] = None
    mp_cost: int = 0
    ep_cost: int = 0
    
    def __post_init__(self):
        if self.effects is None:
            self.effects = []
        if self.messages is None:
            self.messages = []
```

## Kungfu 武功定义

```python
# src/game/typeclasses/wuxue.py
class Kungfu:
    """武功定义
    
    Attributes:
        key: 唯一标识
        name: 显示名
        menpai: 所属门派
        wuxue_type: 武学类型
        moves: 包含招式列表
        requirements: 学习条件
    """
    
    def __init__(
        self,
        key: str,
        name: str,
        menpai: str,
        wuxue_type: WuxueType,
        moves: list[Move] = None,
        requirements: dict = None,
        description: str = "",
    ):
        self.key = key
        self.name = name
        self.menpai = menpai
        self.wuxue_type = wuxue_type
        self.moves = moves or []
        self.requirements = requirements or {}
        self.description = description
    
    def get_move(self, move_key: str) -> Optional[Move]:
        """获取指定招式"""
        for move in self.moves:
            if move.key == move_key:
                return move
        return None
    
    def can_learn(self, character: "Character") -> tuple[bool, str]:
        """检查角色是否可以学习
        
        Args:
            character: 角色
            
        Returns:
            (是否可以, 原因)
        """
        # 门派检查
        if self.menpai and character.menpai != self.menpai:
            return False, f"仅限{self.menpai}弟子学习"
        
        # 等级检查
        min_level = self.requirements.get("level", 1)
        if character.level < min_level:
            return False, f"等级不足（需要{min_level}级）"
        
        # 前置武功检查
        prereq = self.requirements.get("prerequisite")
        if prereq:
            learned = character.learned_wuxue
            if prereq not in learned:
                return False, f"需要先学习{prereq}"
        
        # 悟性检查
        min_wuxing = self.requirements.get("wuxing", 10)
        if character.wuxing < min_wuxing:
            return False, f"悟性不足（需要{min_wuxing}）"
        
        return True, ""
```

## 招式效果脚本沙箱

```python
# src/game/combat/move_effects.py
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.game.typeclasses.character import Character
    from src.game.typeclasses.room import Room
    from src.game.typeclasses.wuxue import MoveEffectResult


@dataclass
class CombatContext:
    """战斗上下文"""
    caster: "Character"
    target: "Character"
    environment: "Room"
    round_num: int


def execute_move_script(
    move: "Move",
    context: CombatContext
) -> MoveEffectResult:
    """沙箱执行招式脚本
    
    可用变量:
    - caster: 攻击者
    - target: 目标
    - context: 战斗上下文
    - random: 随机数函数
    - dice: 骰子函数 dice(n, d) = n个d面骰子
    - MoveEffectResult: 结果类
    
    Args:
        move: 招式
        context: 战斗上下文
        
    Returns:
        招式效果结果
    """
    # 构建沙箱环境
    sandbox_globals = {
        "__builtins__": {},  # 禁用所有内置函数（安全）
        "caster": context.caster,
        "target": context.target,
        "context": context,
        "random": random.random,
        "randint": random.randint,
        "uniform": random.uniform,
        "dice": lambda n, d: sum(random.randint(1, d) for _ in range(n)),
        "MoveEffectResult": MoveEffectResult,
        "result": None,
    }
    
    # 安全执行脚本
    try:
        exec(move.effect_script, sandbox_globals, {})
        return sandbox_globals.get("result", MoveEffectResult())
    except Exception as e:
        # 执行失败，返回默认结果
        return MoveEffectResult(
            messages=[f"{move.name}执行失败：{e}"]
        )


# ===== 常用招式脚本模板 =====

# 基础伤害招式
MOVE_SCRIPT_DAMAGE = """
# 基础伤害招式
base_damage = caster.get_attack() * 1.5

# 命中率判定
hit_chance = 0.9 + (caster.get_agility() - target.get_agility()) * 0.005
hit_chance = max(0.3, min(0.95, hit_chance))

if random() < hit_chance:
    # 命中
    damage = base_damage * uniform(0.9, 1.1)
    damage = max(1, damage - target.get_defense() * 0.5)
    
    result = MoveEffectResult(
        damage=damage,
        mp_cost=move.mp_cost,
        messages=[f"{caster.name}使出{move.name}，命中！造成{damage:.0f}点伤害！"]
    )
else:
    # 未命中
    result = MoveEffectResult(
        mp_cost=move.mp_cost,
        messages=[f"{caster.name}使出{move.name}，但被{target.name}闪开了！"]
    )
"""

# 暴击招式（高伤害低命中）
MOVE_SCRIPT_CRIT = """
# 暴击招式
base_damage = caster.get_attack() * 2.5

# 较低命中率
hit_chance = 0.6 + (caster.get_agility() - target.get_agility()) * 0.003
hit_chance = max(0.2, min(0.8, hit_chance))

if random() < hit_chance:
    # 命中，必定暴击
    damage = base_damage * uniform(1.2, 1.5)
    damage = max(1, damage - target.get_defense() * 0.3)
    
    result = MoveEffectResult(
        damage=damage,
        mp_cost=move.mp_cost,
        messages=[f"{caster.name}使出{move.name}，暴击！造成{damage:.0f}点伤害！"]
    )
else:
    result = MoveEffectResult(
        mp_cost=move.mp_cost,
        messages=[f"{caster.name}使出{move.name}，被{target.name}轻松躲开！"]
    )
"""

# 连击招式（多次低伤害）
MOVE_SCRIPT_COMBO = """
# 连击招式
total_damage = 0
messages = []

for i in range(3):
    base_damage = caster.get_attack() * 0.8
    hit_chance = 0.85
    
    if random() < hit_chance:
        damage = base_damage * uniform(0.8, 1.2)
        damage = max(1, damage - target.get_defense() * 0.5)
        total_damage += damage
        messages.append(f"第{i+1}击命中，造成{damage:.0f}点伤害！")
    else:
        messages.append(f"第{i+1}击落空！")

result = MoveEffectResult(
    damage=total_damage,
    mp_cost=move.mp_cost,
    messages=[f"{caster.name}使出{move.name}！"] + messages
)
"""

# 内力招式（消耗大量内力造成高额伤害）
MOVE_SCRIPT_INTERNAL = """
# 内力招式
internal_bonus = 1 + caster.get_mp()[0] / caster.get_max_mp()
base_damage = caster.get_attack() * 2.0 * internal_bonus

hit_chance = 0.8
if random() < hit_chance:
    damage = base_damage * uniform(0.95, 1.05)
    result = MoveEffectResult(
        damage=damage,
        mp_cost=move.mp_cost,
        messages=[f"{caster.name}运起内力，使出{move.name}！造成{damage:.0f}点伤害！"]
    )
else:
    result = MoveEffectResult(
        mp_cost=move.mp_cost,
        messages=[f"{caster.name}使出{move.name}，被{target.name}闪避！"]
    )
"""
```

## 角色武学管理 Mixin

```python
# src/game/typeclasses/wuxue.py
class CharacterWuxueMixin:
    """角色的武学管理"""
    
    @property
    def learned_wuxue(self) -> dict[str, dict]:
        """已学武功
        
        Returns:
            {
                "kungfu_key": {
                    "level": 1,           # 层数/等级
                    "exp": 0,             # 熟练度经验
                    "moves": {            # 招式熟练度
                        "move_key": exp
                    }
                }
            }
        """
        return self.db.get("learned_wuxue", {})
    
    async def learn_wuxue(self, kungfu: Kungfu) -> tuple[bool, str]:
        """学习武功
        
        Args:
            kungfu: 武功对象
            
        Returns:
            (是否成功, 消息)
        """
        # 检查是否可以学习
        can_learn, reason = kungfu.can_learn(self)
        if not can_learn:
            return False, reason
        
        # 添加到已学武功
        learned = self.learned_wuxue
        learned[kungfu.key] = {
            "level": 1,
            "exp": 0,
            "moves": {move.key: 0 for move in kungfu.moves},
            "learned_at": "timestamp",
        }
        self.db.set("learned_wuxue", learned)
        
        return True, f"你学会了「{kungfu.name}」！"
    
    def has_learned(self, kungfu_key: str) -> bool:
        """是否已学某武功"""
        return kungfu_key in self.learned_wuxue
    
    def get_wuxue_level(self, kungfu_key: str) -> int:
        """获取武功层数"""
        wuxue = self.learned_wuxue.get(kungfu_key, {})
        return wuxue.get("level", 0)
    
    async def practice_move(
        self, 
        kungfu: Kungfu, 
        move: Move
    ) -> tuple[bool, str]:
        """练习招式，增加熟练度
        
        Args:
            kungfu: 武功
            move: 招式
            
        Returns:
            (是否成功, 消息)
        """
        if not self.has_learned(kungfu.key):
            return False, "你尚未学会这门武功"
        
        learned = self.learned_wuxue
        kungfu_data = learned[kungfu.key]
        
        # 增加熟练度
        current_exp = kungfu_data["moves"].get(move.key, 0)
        gain = self._calculate_practice_gain()
        kungfu_data["moves"][move.key] = current_exp + gain
        
        # 检查武功升级
        if self._check_wuxue_level_up(kungfu_data):
            kungfu_data["level"] += 1
            msg = f「{kungfu.name}」提升至第{kungfu_data['level']}层！""
        else:
            msg = f"你练习了「{move.name}」，熟练度+{gain}"
        
        self.db.set("learned_wuxue", learned)
        return True, msg
    
    def _calculate_practice_gain(self) -> int:
        """计算练习收益（受悟性影响）"""
        base = 10
        from_wuxing = self.wuxing // 3
        return base + from_wuxing
    
    def _check_wuxue_level_up(self, kungfu_data: dict) -> bool:
        """检查是否满足升级条件"""
        current_level = kungfu_data["level"]
        total_move_exp = sum(kungfu_data["moves"].values())
        
        # 需要总熟练度达到层数*100
        required = current_level * 100
        return total_move_exp >= required
    
    def get_move_effect(
        self, 
        kungfu: Kungfu, 
        move: Move
    ) -> MoveEffectResult:
        """执行招式效果
        
        Args:
            kungfu: 武功
            move: 招式
            
        Returns:
            招式效果结果
        """
        from ..combat.move_effects import CombatContext, execute_move_script
        
        # 构建战斗上下文
        context = CombatContext(
            caster=self,
            target=None,  # 需要在实际战斗中设置
            environment=None,
            round_num=1,
        )
        
        return execute_move_script(move, context)
    
    def get_available_moves(self) -> list[tuple[Kungfu, Move]]:
        """获取所有可用招式"""
        available = []
        
        for kungfu_key, data in self.learned_wuxue.items():
            # TODO: 通过kungfu_key获取Kungfu对象
            # kungfu = get_kungfu_by_key(kungfu_key)
            # for move in kungfu.moves:
            #     available.append((kungfu, move))
            pass
        
        return available
```

## 克制关系系统

```python
# src/game/combat/counter.py
from ..typeclasses.wuxue import WuxueType


# 克制关系矩阵
# 行克制列
COUNTER_MATRIX = {
    WuxueType.QUAN: [WuxueType.ZHANG, WuxueType.ZHI],
    WuxueType.ZHANG: [WuxueType.ZHI, WuxueType.JIAN],
    WuxueType.ZHI: [WuxueType.JIAN, WuxueType.DAO],
    WuxueType.JIAN: [WuxueType.DAO, WuxueType.GUN],
    WuxueType.DAO: [WuxueType.GUN, WuxueType.QUAN],
    WuxueType.GUN: [WuxueType.QUAN, WuxueType.ZHANG],
    WuxueType.NEIGONG: [],
    WuxueType.QINGGONG: [],
}

COUNTER_BONUS = 0.2  # 克制伤害加成
COUNTERED_PENALTY = -0.15  # 被克制伤害减成


def get_counter_modifier(
    attacker_type: WuxueType,
    defender_type: WuxueType
) -> float:
    """获取克制关系修正系数
    
    Args:
        attacker_type: 攻击者武学类型
        defender_type: 防御者武学类型
        
    Returns:
        伤害修正系数
    """
    if defender_type in COUNTER_MATRIX.get(attacker_type, []):
        return 1 + COUNTER_BONUS
    
    # 检查是否被克制
    for wtype, counters in COUNTER_MATRIX.items():
        if attacker_type in counters and defender_type == wtype:
            return 1 + COUNTERED_PENALTY
    
    return 1.0
```

## 使用示例

```python
# 定义武功招式
move1 = Move(
    key="luohan_kai_shan",
    name="罗汉开山",
    wuxue_type=WuxueType.QUAN,
    mp_cost=10,
    cooldown=0,
    effect_script=MOVE_SCRIPT_DAMAGE,
    counters=[WuxueType.JIAN],
)

move2 = Move(
    key="luohan_xi_shou",
    name="罗汉献寿",
    wuxue_type=WuxueType.QUAN,
    mp_cost=20,
    cooldown=3,
    effect_script=MOVE_SCRIPT_CRIT,
)

# 创建武功
luohanquan = Kungfu(
    key="luohanquan",
    name="罗汉拳",
    menpai="少林",
    wuxue_type=WuxueType.QUAN,
    moves=[move1, move2],
    requirements={"level": 1, "menpai": "少林"},
)

# 角色学习武功
success, msg = await character.learn_wuxue(luohanquan)
print(msg)  # 你学会了「罗汉拳」！

# 练习招式
success, msg = await character.practice_move(luohanquan, move1)
print(msg)  # 你练习了「罗汉开山」，熟练度+15

# 执行招式
result = character.get_move_effect(luohanquan, move1)
print(result.damage)
print(result.messages)
```
