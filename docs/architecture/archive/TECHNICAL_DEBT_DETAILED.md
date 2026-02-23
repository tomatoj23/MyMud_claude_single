# 技术债务详细分析与清偿计划

> 排除GUI的完整技术债务分析

**分析日期**: 2026-02-23  
**债务总数**: 29项  
**预计清偿时间**: 6-8周

---

## 📊 债务总览

### 按严重程度分类

| 级别 | 数量 | 描述 | 示例 |
|:---:|:---:|:---|:---|
| 🔴 阻塞 | 1 | 影响系统运行 | NotImplementedError |
| 🟠 严重 | 8 | 核心功能缺失 | AI/战斗计算 |
| 🟡 中等 | 12 | 功能不完整 | 锁检查/负重 |
| 🟢 轻微 | 8 | 优化项 | 实时战斗/内功施法 |

### 按模块分布

```
npc/           ████████████████████ 48% (14项)
combat/        ██████████░░░░░░░░░░ 28% (8项)
typeclasses/   ██████░░░░░░░░░░░░░░ 17% (5项)
commands/      ███░░░░░░░░░░░░░░░░░ 10% (3项)
quest/         ██░░░░░░░░░░░░░░░░░░ 7% (2项)
```

---

## 🔴 阻塞级债务 (1项)

### TD-001: Command.execute() 抽象方法

**位置**: `src/engine/commands/command.py:110`  
**代码**:
```python
def execute(self) -> CommandResult:
    raise NotImplementedError(f"命令 {self.key} 未实现 execute 方法")
```

**分析**:
- **类型**: 设计模式债务（模板方法模式）
- **风险**: 低 - 这是预期的抽象方法
- **现状**: 所有具体命令已实现该方法，无运行时问题
- **处理建议**: ✅ **无需处理** - 这是正确的抽象基类设计

---

## 🟠 严重级债务 (8项)

### NPC系统 (8项)

#### TD-002: 实现移动到巡逻点逻辑
**位置**: `npc/behavior_tree.py:219`  
**功能**: PatrolAction 节点的执行逻辑  
**依赖**: 
- 需要地图坐标系统
- 需要寻路算法 (A*)
- 需要移动动画/时间

**工作量**: 8-12小时  
**实现方案**:
```python
class PatrolAction(ActionNode):
    async def execute(self, npc: NPC, context: Context) -> NodeStatus:
        # 1. 获取当前巡逻点
        patrol_point = self.data.get("point")
        
        # 2. 计算路径（使用A*）
        path = await context.pathfinding.find_path(
            npc.location, patrol_point
        )
        
        # 3. 逐点移动
        for waypoint in path:
            await npc.move_to(waypoint)
            await asyncio.sleep(MOVE_DELAY)
        
        return NodeStatus.SUCCESS
```

---

#### TD-003: 检查与出生点距离
**位置**: `npc/behavior_tree.py:238`  
**功能**: ReturnHomeAction 距离检查  
**依赖**: TD-002（坐标计算）

**工作量**: 2-3小时  
**实现方案**:
```python
async def execute(self, npc: NPC, context: Context) -> NodeStatus:
    current_pos = npc.location.coords
    home_pos = npc.home_location.coords
    
    distance = calculate_3d_distance(current_pos, home_pos)
    max_distance = self.data.get("max_distance", 50)
    
    if distance > max_distance:
        return NodeStatus.SUCCESS  # 需要回家
    return NodeStatus.FAILURE
```

---

#### TD-004: 实现随机移动逻辑
**位置**: `npc/behavior_tree.py:259`  
**功能**: WanderAction 随机移动  
**依赖**: TD-002

**工作量**: 4-6小时  
**实现方案**:
```python
async def execute(self, npc: NPC, context: Context) -> NodeStatus:
    # 1. 获取周围可移动位置
    neighbors = npc.location.get_neighbor_rooms()
    
    # 2. 随机选择（考虑权重）
    weights = [self._get_move_weight(n) for n in neighbors]
    chosen = random.choices(neighbors, weights=weights, k=1)[0]
    
    # 3. 执行移动
    await npc.move_to(chosen)
    
    return NodeStatus.SUCCESS

def _get_move_weight(self, room: Room) -> float:
    """根据房间类型给移动权重"""
    if room.is_dangerous:
        return 0.1  # 危险区域低权重
    if room.has_players:
        return 2.0  # 有玩家高权重
    return 1.0
```

---

#### TD-005: 检查NPC是否在战斗中
**位置**: `npc/behavior_tree.py:270`  
**功能**: IsInCombat 条件节点  
**依赖**: 战斗系统状态接口

**工作量**: 2-3小时  
**实现方案**:
```python
class IsInCombat(ConditionNode):
    def check(self, npc: NPC, context: Context) -> bool:
        # 方式1: 检查战斗会话管理器
        return CombatSessionManager.is_in_combat(npc)
        
        # 或方式2: 检查角色状态
        return npc.has_status("in_combat")
```

---

#### TD-006: 获取游戏时间
**位置**: `npc/behavior_tree.py:281`  
**功能**: IsTimeInRange 时间检查  
**依赖**: 需要游戏时间系统

**工作量**: 4-6小时（含时间系统设计）

**实现方案**:
```python
class GameTime:
    """游戏内时间系统"""
    def __init__(self):
        self._real_start = time.time()
        self._game_time_multiplier = 12  # 1现实小时=12游戏小时
    
    def get_game_time(self) -> datetime:
        elapsed_real = time.time() - self._real_start
        elapsed_game = elapsed_real * self._game_time_multiplier
        return self._start_time + timedelta(seconds=elapsed_game)

class IsTimeInRange(ConditionNode):
    def check(self, npc: NPC, context: Context) -> bool:
        game_time = context.world.time.get_game_time()
        start_time = parse_time(self.data["start"])  # "08:00"
        end_time = parse_time(self.data["end"])      # "18:00"
        return start_time <= game_time.time() <= end_time
```

---

#### TD-007: 检查范围内是否有玩家
**位置**: `npc/behavior_tree.py:293`  
**功能**: IsPlayerNearby 感知检查  
**依赖**: 房间/位置系统

**工作量**: 3-4小时  
**实现方案**:
```python
class IsPlayerNearby(ConditionNode):
    def check(self, npc: NPC, context: Context) -> bool:
        radius = self.data.get("radius", 3)  # 检测半径（房间数）
        
        # BFS搜索周围房间
        visited = set()
        queue = [(npc.location, 0)]
        
        while queue:
            room, distance = queue.pop(0)
            if distance > radius:
                continue
                
            # 检查房间内的玩家
            if any(isinstance(obj, Player) for obj in room.contents):
                return True
                
            # 继续搜索相邻房间
            for exit_obj in room.get_exits():
                if exit_obj.destination not in visited:
                    visited.add(exit_obj.destination)
                    queue.append((exit_obj.destination, distance + 1))
        
        return False
```

---

#### TD-008: 检查是否离家太远
**位置**: `npc/behavior_tree.py:313`  
**功能**: 巡逻范围限制  
**依赖**: TD-003

**工作量**: 2小时（复用TD-003）  
**实现方案**: 调用TD-003的距离计算逻辑

---

#### TD-009: 派系关系系统
**位置**: `npc/reputation.py:257-262`  
**功能**: get_faction_reputation / modify_faction_reputation  
**工作量**: 8-12小时

**实现方案**:
```python
class FactionReputation:
    """派系关系管理"""
    
    FACTIONS = ["少林", "武当", "峨眉", "丐帮", "魔教", ...]
    
    def get_faction_reputation(self, faction: str) -> int:
        """获取对某派系的好感度 -10000~10000"""
        relations = self.character.db.get("faction_relations", {})
        return relations.get(faction, 0)
    
    def modify_faction_reputation(self, faction: str, delta: int) -> None:
        """修改派系好感度"""
        current = self.get_faction_reputation(faction)
        new_value = max(-10000, min(10000, current + delta))
        
        # 存储修改
        relations = self.character.db.get("faction_relations", {})
        relations[faction] = new_value
        self.character.db.set("faction_relations", relations)
        
        # 触发声望变化事件
        self._on_faction_change(faction, current, new_value)
    
    def _on_faction_change(self, faction: str, old: int, new: int) -> None:
        """处理声望变化副作用"""
        # 1. 检查是否跨越关键阈值（敌对/中立/友好）
        # 2. 触发相关任务/对话
        # 3. 影响关联派系（如少林好感↑，魔教好感↓）
```

---

## 🟡 中等级债务 (12项)

### 对话系统 (4项)

#### TD-010: 检查背包
**位置**: `npc/dialogue.py:281`  
**功能**: 对话中检查玩家是否有特定物品  
**工作量**: 2-3小时

**实现方案**:
```python
async def _handle_check_inventory(self, character, condition: dict) -> bool:
    """检查背包条件"""
    item_key = condition.get("item")
    quantity = condition.get("quantity", 1)
    
    # 搜索背包
    inventory = character.get_items()
    found = sum(1 for item in inventory if item.key == item_key)
    
    return found >= quantity
```

---

#### TD-011: 给予物品
**位置**: `npc/dialogue.py:318`  
**功能**: NPC给予玩家物品  
**工作量**: 3-4小时（含背包满检查）

**实现方案**:
```python
async def _handle_give_item(self, character, action: dict) -> bool:
    """NPC给予物品"""
    item_key = action.get("item")
    quantity = action.get("quantity", 1)
    
    # 1. 检查NPC是否有该物品
    npc_inventory = self.npc.get_items()
    item = next((i for i in npc_inventory if i.key == item_key), None)
    
    if not item:
        return False
    
    # 2. 检查玩家背包空间
    if not character.can_carry(item):
        await self.msg("你的背包已满，无法接收物品。")
        return False
    
    # 3. 转移物品
    item.location = character
    await self.msg(f"{self.npc.name}给了你{item.name}。")
    return True
```

---

#### TD-012: 解锁任务
**位置**: `npc/dialogue.py:341`  
**功能**: 对话触发任务  
**依赖**: 任务系统接口

**工作量**: 4-6小时  
**实现方案**:
```python
async def _handle_unlock_quest(self, character, action: dict) -> bool:
    """解锁新任务"""
    quest_key = action.get("quest")
    
    # 获取任务模板
    quest_template = QuestRegistry.get(quest_key)
    if not quest_template:
        return False
    
    # 检查前置条件
    if not quest_template.check_prerequisites(character):
        return False
    
    # 创建任务实例
    quest = Quest.create_from_template(quest_template, character)
    character.quest_manager.accept(quest)
    
    await self.msg(f"获得新任务：{quest.name}")
    return True
```

---

#### TD-013: 记录到世界状态
**位置**: `npc/dialogue.py:356`  
**功能**: 对话影响世界状态（如标记某事件已发生）  
**工作量**: 4-6小时

**实现方案**:
```python
async def _handle_set_world_state(self, character, action: dict) -> bool:
    """设置世界状态"""
    key = action.get("key")
    value = action.get("value")
    
    # 获取世界状态管理器
    world_state = character.engine.world_state
    
    # 设置状态（支持作用域）
    scope = action.get("scope", "global")  # global/region/player
    
    if scope == "global":
        world_state.set_global(key, value)
    elif scope == "region":
        world_state.set_region(character.location.area, key, value)
    elif scope == "player":
        character.db.set(f"state_{key}", value)
    
    # 触发状态变化事件
    await world_state.on_state_changed(key, value, scope)
    return True
```

---

### 核心功能 (8项)

#### TD-014: 负重检查
**位置**: `typeclasses/item.py:113`  
**功能**: 实现物品拾取时的负重检查  
**工作量**: 3-4小时

**实现方案**:
```python
def can_pickup(self, character: "Character") -> tuple[bool, str]:
    """检查是否可以拾取"""
    # 1. 计算物品重量
    item_weight = self.weight
    
    # 2. 获取角色当前负重
    current_weight = character.get_current_weight()
    max_weight = character.get_max_weight()  # 基于臂力计算
    
    # 3. 检查是否超重
    if current_weight + item_weight > max_weight:
        return False, f"太沉了，你拿不动（还需{item_weight}负重空间）"
    
    return True, ""

# Character中的相关方法
def get_current_weight(self) -> int:
    """获取当前负重"""
    return sum(item.weight for item in self.contents)

def get_max_weight(self) -> int:
    """获取最大负重（基于臂力）"""
    base = self.strength * 5  # 每点臂力5单位负重
    # 加上装备加成
    bonus = self.get_equipment_bonus("max_weight")
    return base + bonus
```

---

#### TD-015: 出口锁系统
**位置**: `typeclasses/room.py:348`  
**功能**: 解析锁字符串，检查通行条件  
**工作量**: 8-12小时

**实现方案**:
```python
class ExitLockParser:
    """出口锁字符串解析器"""
    
    # 锁字符串格式: "condition1;condition2;..."
    # 条件类型:
    #   - has_item:key:需要物品
    #   - has_skill:key:level:需要技能等级
    #   - has_quest:key:stage:需要任务进度
    #   - attr:attr_name:op:value:属性比较
    #   - time:start:end:时间限制
    
    def __init__(self, lock_str: str):
        self.conditions = self._parse(lock_str)
    
    def _parse(self, lock_str: str) -> list[Condition]:
        if not lock_str:
            return []
        
        conditions = []
        for cond_str in lock_str.split(";"):
            parts = cond_str.split(":")
            cond_type = parts[0]
            
            if cond_type == "has_item":
                conditions.append(HasItemCondition(parts[1]))
            elif cond_type == "has_skill":
                conditions.append(HasSkillCondition(parts[1], int(parts[2])))
            elif cond_type == "attr":
                conditions.append(AttrCondition(parts[1], parts[2], parts[3]))
            # ...
        
        return conditions
    
    async def check(self, character: Character) -> tuple[bool, str]:
        """检查角色是否满足所有条件"""
        for condition in self.conditions:
            passed, msg = await condition.check(character)
            if not passed:
                return False, msg
        return True, ""

# 在Exit.can_pass中使用
async def can_pass(self, character: "Character") -> tuple[bool, str]:
    if self.lock_str:
        parser = ExitLockParser(self.lock_str)
        return await parser.check(character)
    return True, ""
```

---

#### TD-016: 套装效果计算
**位置**: `typeclasses/equipment.py:417`  
**功能**: 根据套装件数计算属性加成  
**工作量**: 6-8小时

**实现方案**:
```python
def _calculate_set_bonus(self, equipped_items: list[Equipment]) -> dict[str, int]:
    """计算套装加成"""
    # 1. 统计套装件数
    set_counts: dict[str, int] = {}
    for item in equipped_items:
        if item.set_name:
            set_counts[item.set_name] = set_counts.get(item.set_name, 0) + 1
    
    # 2. 计算加成
    total_bonus: dict[str, int] = {}
    
    for set_name, count in set_counts.items():
        # 获取套装配置
        set_config = SET_BONUSES.get(set_name, {})
        
        # 应用件数对应的加成
        for threshold, bonuses in set_config.items():
            if count >= threshold:
                for attr, value in bonuses.items():
                    total_bonus[attr] = total_bonus.get(attr, 0) + value
    
    return total_bonus

# 套装配置示例
SET_BONUSES = {
    "天蚕套装": {
        2: {"defense": 50},      # 2件：防御+50
        4: {"max_hp": 500},       # 4件：生命+500
        6: {"damage_reduction": 0.1},  # 6件：减伤10%
    },
    # ...
}
```

---

#### TD-017: 武学查找缓存
**位置**: `typeclasses/wuxue.py:298`  
**功能**: 通过kungfu_key获取Kungfu对象  
**工作量**: 4-6小时

**实现方案**:
```python
class KungfuRegistry:
    """武学注册表（单例）"""
    _instance = None
    _cache: dict[str, Kungfu] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, kungfu: Kungfu) -> None:
        """注册武学"""
        self._cache[kungfu.key] = kungfu
    
    def get(self, key: str) -> Kungfu | None:
        """获取武学（带缓存）"""
        return self._cache.get(key)
    
    def load_all(self) -> None:
        """从配置文件加载所有武学"""
        # 加载data/kungfu/下的所有武学定义
        pass

# 使用
registry = KungfuRegistry()
kungfu = registry.get(kungfu_key)
```

---

#### TD-018: 命令锁检查
**位置**: `commands/command.py:85`  
**功能**: 实现完整的锁检查逻辑  
**工作量**: 6-8小时（类似TD-015）

**实现方案**: 复用TD-015的ExitLockParser，改为命令锁检查

---

#### TD-019: 动态命令集合
**位置**: `commands/handler.py:85-86`  
**功能**: 
- 从调用者位置获取可用命令
- 从调用者自身获取可用命令

**工作量**: 4-6小时  
**实现方案**:
```python
async def _get_available_commands(self, caller) -> CommandSet:
    """获取调用者可用的命令集合"""
    base_cmdset = self.cmdset  # 基础命令
    
    # 1. 从位置获取命令（房间特定命令）
    location = caller.location
    if location:
        location_cmdset = location.get_cmdset()
        base_cmdset = base_cmdset + location_cmdset
    
    # 2. 从自身获取命令（角色技能/状态命令）
    character_cmdset = caller.get_cmdset()  # 如战斗中的特殊命令
    base_cmdset = base_cmdset + character_cmdset
    
    return base_cmdset
```

---

#### TD-020: 任务物品发放
**位置**: `quest/core.py:346`  
**功能**: 任务完成时给予物品奖励  
**工作量**: 3-4小时

**实现方案**:
```python
async def _give_item_reward(self, character: Character, reward: dict) -> None:
    """发放物品奖励"""
    item_key = reward["item"]
    quantity = reward.get("quantity", 1)
    
    # 1. 创建物品
    for _ in range(quantity):
        item = await character.engine.objects.create(
            typeclass_path="src.game.typeclasses.item.Item",
            key=item_key,
            attributes={"name": reward.get("name", item_key)}
        )
        
        # 2. 放入玩家背包
        item.location = character
    
    # 3. 通知玩家
    character.msg(f"获得物品：{reward.get('name', item_key)} x{quantity}")
```

---

#### TD-021: 武学奖励
**位置**: `quest/core.py:351`  
**功能**: 任务完成时教授武学  
**工作量**: 4-6小时

**实现方案**:
```python
async def _give_kungfu_reward(self, character: Character, reward: dict) -> None:
    """发放武学奖励"""
    kungfu_key = reward["kungfu"]
    
    # 1. 检查是否已学会
    if character.wuxue.has_learned(kungfu_key):
        character.msg(f"你已经学会了{reward.get('name', kungfu_key)}")
        return
    
    # 2. 检查学习条件
    kungfu = KungfuRegistry.get(kungfu_key)
    if not kungfu.meets_requirements(character):
        character.msg("你还达不到学习这门武学的条件")
        return
    
    # 3. 教授武学
    await character.wuxue.learn(kungfu)
    character.msg(f"习得武学：{kungfu.name}！")
```

---

## 🟢 轻微级债务 (8项)

### 战斗系统优化 (4项)

#### TD-022: 实时战斗结算
**位置**: `combat/core.py:169`  
**功能**: 优化为按实际时间结算（目前是回合制）  
**工作量**: 16-24小时（较大改动）  
**优先级**: 低（回合制已可用）

**说明**: 当前回合制战斗已完整可用，实时战斗是增强功能，非必需。

---

#### TD-023: 内功施法
**位置**: `combat/core.py:283`  
**功能**: 实现内功/特殊技能施法  
**工作量**: 8-12小时  
**说明**: 需设计内功系统架构

---

#### TD-024: 防御者武学类型获取
**位置**: `combat/calculator.py:95`  
**功能**: 获取防御者当前使用的武学类型（用于克制计算）  
**工作量**: 2-3小时

**实现方案**:
```python
def _get_defender_kungfu_type(self, defender: Character) -> str:
    """获取防御者当前使用的武学类型"""
    # 1. 检查当前装备的主手武器对应的武学
    weapon = defender.get_equipped_item(EquipmentSlot.MAIN_HAND)
    if weapon and hasattr(weapon, "associated_kungfu"):
        return weapon.associated_kungfu.type
    
    # 2. 检查当前激活的武学
    active_kungfu = defender.wuxue.get_active()
    if active_kungfu:
        return active_kungfu.type
    
    # 3. 默认类型
    return "unarmed"
```

---

#### TD-025: 招式命中修正
**位置**: `combat/calculator.py:154`  
**功能**: 从招式数据读取命中修正  
**工作量**: 2-3小时

**实现方案**:
```python
def _get_move_hit_modifier(self, move: Move) -> float:
    """获取招式命中修正"""
    # 从招式数据读取
    return move.data.get("hit_modifier", 1.0)  # 默认1.0（无修正）
```

---

### 战斗AI优化 (2项)

#### TD-026: 基于克制关系的智能选择
**位置**: `combat/ai.py:165`  
**功能**: AI根据克制关系选择招式  
**工作量**: 4-6小时

**实现方案**:
```python
def _select_counter_move(self, combatant: Combatant, target: Character) -> Move:
    """选择克制目标的招式"""
    available_moves = combatant.get_available_moves()
    
    # 获取目标当前武学类型
    target_type = self._get_target_kungfu_type(target)
    
    # 评分选择
    best_move = None
    best_score = -float('inf')
    
    for move in available_moves:
        score = move.base_damage
        
        # 检查克制关系
        if move.counter_type == target_type:
            score *= 1.5  # 克制加成
        elif move.is_countered_by(target_type):
            score *= 0.7  # 被克减成
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
```

---

#### TD-027: 根据招式属性选择
**位置**: `combat/ai.py:194`  
**功能**: AI根据招式属性（内力消耗/冷却等）选择  
**工作量**: 3-4小时

---

---

## 📋 清偿计划

### 阶段1: 核心基础 (第1-2周)

**目标**: 清偿阻塞和中等级债务，建立基础功能

| 周次 | 债务项 | 工作量 | 负责人 |
|:---:|:---|:---:|:---:|
| W1 | TD-014 负重检查 | 4h | 开发组A |
| W1 | TD-015 出口锁系统 | 12h | 开发组A |
| W1 | TD-016 套装效果 | 8h | 开发组B |
| W2 | TD-017 武学缓存 | 6h | 开发组B |
| W2 | TD-018 命令锁检查 | 8h | 开发组A |
| W2 | TD-019 动态命令 | 6h | 开发组B |
| W2 | TD-020/021 任务奖励 | 8h | 开发组C |

**阶段产出**:
- 完整的物品/装备系统
- 灵活的任务系统
- 安全的命令系统

---

### 阶段2: NPC智能 (第3-5周)

**目标**: 实现完整的NPC AI系统

| 周次 | 债务项 | 工作量 | 依赖 |
|:---:|:---|:---:|:---|
| W3 | TD-006 游戏时间系统 | 6h | 无 |
| W3 | TD-005 战斗状态检查 | 3h | 战斗系统 |
| W3 | TD-003 距离检查 | 3h | 坐标系统 |
| W3 | TD-008 离家检查 | 2h | TD-003 |
| W4 | TD-002 移动逻辑 | 12h | 寻路系统 |
| W4 | TD-004 随机移动 | 6h | TD-002 |
| W5 | TD-007 玩家感知 | 4h | TD-004 |
| W5 | TD-009 派系关系 | 12h | 声望系统 |

**阶段产出**:
- 智能的NPC行为
- 生动的江湖世界
- 复杂的势力关系

---

### 阶段3: 对话与交互 (第5-6周)

**目标**: 完成对话系统和交互功能

| 周次 | 债务项 | 工作量 | 依赖 |
|:---:|:---|:---:|:---|
| W5 | TD-010 背包检查 | 3h | 无 |
| W5 | TD-011 给予物品 | 4h | TD-010 |
| W6 | TD-012 解锁任务 | 6h | 任务系统 |
| W6 | TD-013 世界状态 | 6h | 全局状态 |

---

### 阶段4: 战斗完善 (第6-7周)

**目标**: 完善战斗系统

| 周次 | 债务项 | 工作量 | 优先级 |
|:---:|:---|:---:|:---:|
| W6 | TD-024 武学类型获取 | 3h | 高 |
| W6 | TD-025 命中修正 | 3h | 高 |
| W7 | TD-026 AI克制选择 | 6h | 中 |
| W7 | TD-027 AI属性选择 | 4h | 中 |

---

### 阶段5: 高级功能 (第7-8周，可选)

**目标**: 实现增强功能

| 周次 | 债务项 | 工作量 | 说明 |
|:---:|:---|:---:|:---|
| W7 | TD-023 内功施法 | 12h | 新系统 |
| W8 | TD-022 实时战斗 | 24h | 架构改动大 |

---

## 📈 清偿进度追踪

```
Week 1: [████████░░░░░░░░░░] 40%  核心基础
Week 2: [████████████████░░] 80%  核心完成
Week 3: [████░░░░░░░░░░░░░░] 20%  NPC开始
Week 4: [████████░░░░░░░░░░] 40%  NPC移动
Week 5: [████████████░░░░░░] 60%  NPC完成+对话
Week 6: [██████████████░░░░] 70%  对话完成+战斗
Week 7: [████████████████░░] 80%  战斗完成
Week 8: [██████████████████] 90%  高级功能（可选）
```

---

## ✅ 验收标准

每项债务清偿后需满足：

1. **功能完整**: 实现TODO描述的全部功能
2. **测试覆盖**: 新增单元测试，覆盖率>80%
3. **文档更新**: 更新相关API文档
4. **混沌测试**: 通过对应的混沌测试
5. **代码审查**: 通过团队代码审查

---

*最后更新: 2026-02-23*
