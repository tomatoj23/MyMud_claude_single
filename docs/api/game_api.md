# 游戏系统 API 文档

> 本文档描述金庸武侠MUD的游戏系统API。

---

## 目录

- [Character](#character) - 角色系统
- [Equipment](#equipment) - 装备系统
- [Wuxue](#wuxue) - 武学系统
- [Combat](#combat) - 战斗系统
- [Quest](#quest) - 任务系统
- [NPC](#npc) - NPC系统

---

## Character

武侠角色类型，包含属性、成长、门派等系统。

### 位置

`src/game/typeclasses/character.py`

### 类定义

```python
class Character(CharacterEquipmentMixin, CharacterWuxueMixin, TypeclassBase):
    """武侠角色类型。"""
    typeclass_path = "src.game.typeclasses.character.Character"
```

### 属性

#### 先天资质

| 属性 | 类型 | 说明 |
|:---|:---|:---|
| `gengu` | `int` | 根骨 - 影响体质、气血上限 |
| `wuxing` | `int` | 悟性 - 影响武学领悟速度 |
| `fuyuan` | `int` | 福缘 - 影响奇遇概率 |
| `rongmao` | `int` | 容貌 - 影响NPC态度 |

#### 后天属性

| 属性 | 类型 | 说明 |
|:---|:---|:---|
| `strength` | `int` | 力量 - 影响外功伤害 |
| `agility` | `int` | 敏捷 - 影响闪避、命中 |
| `constitution` | `int` | 体质 - 影响气血上限 |
| `spirit` | `int` | 精神 - 影响内力上限、抗性 |

#### 动态状态

| 属性 | 类型 | 说明 |
|:---|:---|:---|
| `hp` | `tuple[int, int]` | 当前/最大气血 |
| `mp` | `tuple[int, int]` | 当前/最大内力 |
| `ep` | `tuple[int, int]` | 当前/最大精力 |

#### 成长属性

| 属性 | 类型 | 说明 |
|:---|:---|:---|
| `level` | `int` | 等级 |
| `exp` | `int` | 经验值 |
| `menpai` | `str \| None` | 所属门派 |
| `menpai_contrib` | `int` | 门派贡献 |

### 方法

#### modify_hp

```python
def modify_hp(self, delta: int) -> int
```

修改气血，返回实际变化值。

| 参数 | 类型 | 说明 |
|:---|:---|:---|
| `delta` | `int` | 变化值（正为治疗，负为伤害） |

| 返回 | 说明 |
|:---|:---|
| `int` | 实际变化值 |

---

#### add_exp

```python
def add_exp(self, amount: int) -> bool
```

增加经验，返回是否升级。

---

#### get_attack

```python
def get_attack(self) -> int
```

计算攻击力（基础 + 装备 + BUFF）。

---

## Equipment

装备系统，包含装备槽位、品质、耐久度等。

### 位置

`src/game/typeclasses/equipment.py`

### 装备槽位

```python
class EquipmentSlot(Enum):
    WEAPON = "weapon"           # 武器
    HEAD = "head"              # 头部
    BODY = "body"              # 身体
    HAND_LEFT = "hand_left"    # 左手
    HAND_RIGHT = "hand_right"  # 右手
    LEGS = "legs"              # 腿部
    FEET = "feet"              # 脚部
    RING_LEFT = "ring_left"    # 左戒指
    RING_RIGHT = "ring_right"  # 右戒指
    NECK = "neck"              # 项链
    CLOAK = "cloak"            # 披风
    BELT = "belt"              # 腰带
```

### 装备品质

```python
class EquipmentQuality(Enum):
    NORMAL = 1      # 普通
    MAGIC = 2       # 魔法
    RARE = 3        # 稀有
    EPIC = 4        # 史诗
    LEGENDARY = 5   # 传说
```

### 方法

#### equip

```python
def equip(self, item: Equipment) -> bool
```

装备物品。

---

#### unequip

```python
def unequip(self, slot: EquipmentSlot) -> Equipment | None
```

卸下装备。

---

## Combat

战斗系统，包含回合制战斗、AI、伤害计算等。

### 位置

`src/game/combat/core.py`

### 类定义

```python
class CombatSession:
    """战斗会话。"""
```

### 构造函数

```python
def __init__(
    self,
    engine: GameEngine,
    enemies: list[Character],
    player: Character | None = None
)
```

### 方法

#### start

```python
async def start(self) -> None
```

开始战斗。

---

#### stop

```python
async def stop(self, result: CombatResult) -> None
```

结束战斗。

---

#### handle_player_command

```python
async def handle_player_command(
    self,
    combatant: Combatant,
    command: str,
    **kwargs
) -> tuple[bool, str]
```

处理玩家战斗命令。

| 参数 | 类型 | 说明 |
|:---|:---|:---|
| `command` | `str` | 命令（kill/cast/flee/defend） |

---

### 伤害计算

位置：`src/game/combat/calculator.py`

```python
class CombatCalculator:
    """战斗计算器。"""
    
    @staticmethod
    def calculate_damage(
        attacker: Character,
        defender: Character,
        move: Move | None = None,
        context: dict | None = None
    ) -> DamageResult
```

---

## Quest

任务系统，支持多种目标类型和任务链。

### 位置

`src/game/quest/core.py`

### 任务目标类型

```python
class QuestObjectiveType(Enum):
    KILL = "kill"           # 击杀目标
    COLLECT = "collect"     # 收集物品
    TALK = "talk"           # 对话NPC
    REACH = "reach"         # 到达地点
    COMBAT = "combat"       # 完成战斗
```

### 类定义

```python
class Quest:
    """任务。"""
```

### 方法

#### start

```python
def start(self, character: Character) -> bool
```

开始任务。

---

#### update_progress

```python
def update_progress(
    self,
    objective_type: QuestObjectiveType,
    target: str,
    amount: int = 1
) -> bool
```

更新任务进度。

---

#### complete

```python
async def complete(self, character: Character) -> bool
```

完成任务并发放奖励。

---

## NPC

NPC系统，包含类型、行为树、对话等。

### 位置

`src/game/npc/core.py`

### NPC类型

```python
class NPCType(Enum):
    NORMAL = "normal"       # 普通NPC
    MERCHANT = "merchant"   # 商人
    TRAINER = "trainer"     # 训练师
    QUEST = "quest"         # 任务NPC
    ENEMY = "enemy"         # 敌人
```

### 类定义

```python
class NPC(Character):
    """NPC类型。"""
    typeclass_path = "src.game.npc.core.NPC"
```

### 属性

| 属性 | 类型 | 说明 |
|:---|:---|:---|
| `npc_type` | `NPCType` | NPC类型 |
| `ai_enabled` | `bool` | 是否启用AI |
| `schedule` | `dict` | 日常行程表 |
| `home_location` | `int \| None` | 家位置ID |
| `dialogue_key` | `str` | 对话键 |

### 方法

#### can_trade

```python
def can_trade(self) -> bool
```

是否可以交易。

---

#### can_train

```python
def can_train(self) -> bool
```

是否可以训练。

---

#### update_ai

```python
async def update_ai(self, dt: float) -> None
```

更新AI行为。

---

## 行为树

位置：`src/game/npc/behavior_tree.py`

### 节点类型

| 节点 | 说明 |
|:---|:---|
| `SelectorNode` | 选择器（有一个成功则成功） |
| `SequenceNode` | 序列器（全部成功才成功） |
| `ParallelNode` | 并行节点 |
| `ActionNode` | 动作节点 |
| `ConditionNode` | 条件节点 |
| `InverterNode` | 反转节点 |
| `RepeatNode` | 重复节点 |

### 使用示例

```python
from src.game.npc.behavior_tree import SelectorNode, SequenceNode, ActionNode

# 创建行为树
root = SelectorNode([
    SequenceNode([
        ConditionNode(is_in_combat),
        ActionNode(attack_player)
    ]),
    ActionNode(patrol)
])

# 执行行为树
status = await root.tick(npc)
```

---

## 对话系统

位置：`src/game/npc/dialogue.py`

### 类定义

```python
class DialogueSystem:
    """对话系统。"""
```

### 方法

#### register_dialogue

```python
def register_dialogue(
    self,
    key: str,
    nodes: dict[str, DialogueNode]
) -> None
```

注册对话树。

---

#### start_dialogue

```python
def start_dialogue(
    self,
    character: Character,
    npc: NPC,
    dialogue_key: str
) -> DialogueNode | None
```

开始对话。

---

#### select_response

```python
async def select_response(
    self,
    character: Character,
    npc: NPC,
    response_index: int
) -> DialogueNode | None
```

选择对话选项。
