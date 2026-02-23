# 任务与NPC系统

## 任务系统

### 任务数据模型

```python
# src/game/quest/core.py
from enum import Enum
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..typeclasses.character import Character


class QuestType(Enum):
    """任务类型"""
    MAIN = "main"      # 主线
    SIDE = "side"      # 支线
    DAILY = "daily"    # 日常
    MENPAI = "menpai"  # 门派


class QuestObjectiveType(Enum):
    """任务目标类型"""
    COLLECT = "collect"    # 收集物品
    KILL = "kill"          # 击杀NPC
    TALK = "talk"          # 对话
    EXPLORE = "explore"    # 探索地点
    CUSTOM = "custom"      # 自定义条件


@dataclass
class QuestObjective:
    """任务目标"""
    type: QuestObjectiveType
    target: str           # 目标ID
    count: int = 1
    current: int = 0
    description: str = ""


class Quest:
    """任务定义"""
    
    def __init__(
        self,
        key: str,
        name: str,
        description: str,
        quest_type: QuestType,
        objectives: list[QuestObjective] = None,
        rewards: dict = None,
        prerequisites: dict = None,
        next_quest: Optional[str] = None,
        time_limit: Optional[int] = None,  # 秒，None表示无限制
    ):
        self.key = key
        self.name = name
        self.description = description
        self.type = quest_type
        self.objectives = objectives or []
        self.rewards = rewards or {}
        self.prerequisites = prerequisites or {}
        self.next_quest = next_quest
        self.time_limit = time_limit


# 角色任务管理 Mixin
class CharacterQuestMixin:
    """角色的任务管理"""
    
    @property
    def active_quests(self) -> dict[str, dict]:
        """进行中任务
        
        Returns:
            {quest_key: progress_data}
        """
        return self.db.get("active_quests", {})
    
    @property
    def completed_quests(self) -> list[str]:
        """已完成任务"""
        return self.db.get("completed_quests", [])
    
    async def accept_quest(self, quest: Quest) -> tuple[bool, str]:
        """接受任务
        
        Args:
            quest: 任务对象
            
        Returns:
            (是否成功, 消息)
        """
        # 检查前置条件
        can_accept, reason = self._check_prerequisites(quest)
        if not can_accept:
            return False, reason
        
        # 检查是否已接受或已完成
        if quest.key in self.active_quests:
            return False, "你已接受该任务"
        
        if quest.key in self.completed_quests:
            return False, "你已完成该任务"
        
        # 添加到活跃任务
        active = self.active_quests
        active[quest.key] = {
            "accepted_at": "timestamp",
            "objectives": [
                {"type": obj.type.value, "target": obj.target, 
                 "count": obj.count, "current": 0}
                for obj in quest.objectives
            ],
            "time_limit": quest.time_limit,
        }
        self.db.set("active_quests", active)
        
        return True, f"接受任务：{quest.name}"
    
    def _check_prerequisites(self, quest: Quest) -> tuple[bool, str]:
        """检查任务前置条件"""
        prereqs = quest.prerequisites
        
        # 等级要求
        if "level" in prereqs:
            if self.level < prereqs["level"]:
                return False, f"需要等级{prereqs['level']}"
        
        # 门派要求
        if "menpai" in prereqs:
            if self.menpai != prereqs["menpai"]:
                return False, f"仅限{prereqs['menpai']}弟子"
        
        # 前置任务
        if "quest_completed" in prereqs:
            if prereqs["quest_completed"] not in self.completed_quests:
                return False, "需要先完成前置任务"
        
        return True, ""
    
    async def update_objective(
        self, 
        quest_key: str, 
        objective_idx: int, 
        progress: int
    ) -> bool:
        """更新任务进度
        
        Args:
            quest_key: 任务key
            objective_idx: 目标索引
            progress: 进度增量
            
        Returns:
            是否完成该目标
        """
        active = self.active_quests
        if quest_key not in active:
            return False
        
        quest_data = active[quest_key]
        objectives = quest_data.get("objectives", [])
        
        if objective_idx >= len(objectives):
            return False
        
        obj = objectives[objective_idx]
        obj["current"] = min(obj["count"], obj["current"] + progress)
        
        self.db.set("active_quests", active)
        
        # 检查是否完成
        return obj["current"] >= obj["count"]
    
    async def complete_quest(self, quest_key: str) -> tuple[bool, str]:
        """完成任务
        
        Args:
            quest_key: 任务key
            
        Returns:
            (是否成功, 消息)
        """
        active = self.active_quests
        if quest_key not in active:
            return False, "你没有进行该任务"
        
        # 检查所有目标是否完成
        quest_data = active[quest_key]
        objectives = quest_data.get("objectives", [])
        
        for obj in objectives:
            if obj["current"] < obj["count"]:
                return False, "任务目标尚未完成"
        
        # 发放奖励
        # TODO: 从任务定义获取奖励并发放
        
        # 移动到已完成
        del active[quest_key]
        self.db.set("active_quests", active)
        
        completed = self.completed_quests
        completed.append(quest_key)
        self.db.set("completed_quests", completed)
        
        return True, "任务完成！"
    
    def get_quest_progress(self, quest_key: str) -> Optional[dict]:
        """获取任务进度"""
        return self.active_quests.get(quest_key)


# 因果点系统
class KarmaSystem:
    """因果点系统"""
    
    KARMA_TYPES = ["good", "evil", "love", "loyalty", "wisdom", "courage"]
    
    def __init__(self, character: "Character"):
        self.character = character
    
    def add_karma(self, karma_type: str, points: int, reason: str = "") -> None:
        """添加因果点"""
        karma = self.character.db.get("karma", {})
        karma[karma_type] = karma.get(karma_type, 0) + points
        self.character.db.set("karma", karma)
    
    def get_karma(self, karma_type: str) -> int:
        """获取因果点"""
        karma = self.character.db.get("karma", {})
        return karma.get(karma_type, 0)
    
    def get_karma_summary(self) -> dict[str, int]:
        """获取因果点汇总"""
        return self.character.db.get("karma", {})
    
    def check_requirement(self, requirement: dict) -> bool:
        """检查因果点是否满足条件
        
        Args:
            requirement: {"good": ">=10", "evil": "<=5"}
            
        Returns:
            是否满足
        """
        for karma_type, condition in requirement.items():
            value = self.get_karma(karma_type)
            
            # 解析条件
            if ">=" in condition:
                threshold = int(condition.replace(">=", ""))
                if value < threshold:
                    return False
            elif "<=" in condition:
                threshold = int(condition.replace("<=", ""))
                if value > threshold:
                    return False
            # TODO: 更多条件类型
        
        return True


# 世界状态管理
class WorldStateManager:
    """世界状态管理"""
    
    def __init__(self, engine: "GameEngine"):
        self.engine = engine
        self._states: dict[str, any] = {}
    
    def get(self, key: str, default=None):
        """获取世界状态"""
        return self._states.get(key, default)
    
    def set(self, key: str, value: any) -> None:
        """设置世界状态"""
        self._states[key] = value
    
    def on_player_choice(
        self, 
        character: "Character", 
        choice_id: str, 
        choice: str
    ) -> None:
        """记录玩家选择"""
        key = f"choice_{character.id}_{choice_id}"
        self.set(key, choice)
```

## NPC系统

### NPC类型类

```python
# src/game/npc/core.py
from typing import Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..typeclasses.character import Character
    from ..typeclasses.room import Room


class NPCType(Enum):
    """NPC类型"""
    NORMAL = "normal"      # 普通
    MERCHANT = "merchant"  # 商人
    TRAINER = "trainer"    # 训练师
    QUEST = "quest"        # 任务NPC
    BOSS = "boss"          # Boss


class NPC(Character):
    """NPC类型
    
    扩展Character，添加AI和行为树支持
    """
    
    typeclass_path = "src.game.npc.core.NPC"
    
    @property
    def npc_type(self) -> NPCType:
        """NPC类型"""
        return NPCType(self.db.get("npc_type", "normal"))
    
    @property
    def ai_enabled(self) -> bool:
        """是否启用AI"""
        return self.db.get("ai_enabled", True)
    
    @property
    def schedule(self) -> list[dict]:
        """日常行程安排
        
        Returns:
            [{"time": "08:00", "location": "room_key", "action": "action_name"}]
        """
        return self.db.get("schedule", [])
    
    async def update_ai(self, delta_time: float) -> None:
        """AI更新
        
        Args:
            delta_time: 经过的时间
        """
        if not self.ai_enabled:
            return
        
        # 执行行为树
        if hasattr(self, "behavior_tree"):
            await self.behavior_tree.tick(self)
    
    def at_combat_start(self, combat) -> None:
        """战斗开始"""
        super().at_combat_start(combat)
        # NPC进入战斗模式
        self.ai_enabled = False  # 由战斗系统接管
    
    def at_combat_end(self, combat) -> None:
        """战斗结束"""
        super().at_combat_end(combat)
        self.ai_enabled = True
```

### 行为树基础框架

```python
# src/game/npc/behavior_tree.py
from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional


class NodeStatus(Enum):
    """行为树节点状态"""
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


class BehaviorNode(ABC):
    """行为树节点基类"""
    
    @abstractmethod
    async def tick(self, npc: "NPC", context: dict) -> NodeStatus:
        """执行节点
        
        Args:
            npc: NPC对象
            context: 上下文数据
            
        Returns:
            执行结果状态
        """
        pass


class SelectorNode(BehaviorNode):
    """选择节点 - 顺序执行子节点，直到有一个成功"""
    
    def __init__(self, children: list[BehaviorNode] = None):
        self.children = children or []
    
    async def tick(self, npc: "NPC", context: dict) -> NodeStatus:
        for child in self.children:
            status = await child.tick(npc, context)
            if status == NodeStatus.SUCCESS:
                return NodeStatus.SUCCESS
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        return NodeStatus.FAILURE


class SequenceNode(BehaviorNode):
    """序列节点 - 顺序执行子节点，直到有一个失败"""
    
    def __init__(self, children: list[BehaviorNode] = None):
        self.children = children or []
    
    async def tick(self, npc: "NPC", context: dict) -> NodeStatus:
        for child in self.children:
            status = await child.tick(npc, context)
            if status == NodeStatus.FAILURE:
                return NodeStatus.FAILURE
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        return NodeStatus.SUCCESS


class ActionNode(BehaviorNode):
    """动作节点 - 执行具体动作"""
    
    def __init__(self, action: callable):
        self.action = action
    
    async def tick(self, npc: "NPC", context: dict) -> NodeStatus:
        try:
            result = await self.action(npc, context)
            return NodeStatus.SUCCESS if result else NodeStatus.FAILURE
        except Exception:
            return NodeStatus.FAILURE


class ConditionNode(BehaviorNode):
    """条件节点 - 检查条件"""
    
    def __init__(self, condition: callable):
        self.condition = condition
    
    async def tick(self, npc: "NPC", context: dict) -> NodeStatus:
        try:
            result = await self.condition(npc, context)
            return NodeStatus.SUCCESS if result else NodeStatus.FAILURE
        except Exception:
            return NodeStatus.FAILURE


class InverterNode(BehaviorNode):
    """反转节点 - 反转子节点结果"""
    
    def __init__(self, child: BehaviorNode):
        self.child = child
    
    async def tick(self, npc: "NPC", context: dict) -> NodeStatus:
        status = await self.child.tick(npc, context)
        if status == NodeStatus.SUCCESS:
            return NodeStatus.FAILURE
        if status == NodeStatus.FAILURE:
            return NodeStatus.SUCCESS
        return status


class NPCBehaviorTree:
    """NPC行为树"""
    
    def __init__(self, root: BehaviorNode):
        self.root = root
    
    async def tick(self, npc: "NPC"):
        """执行一次行为树"""
        context = {}  # 可以在这里存储上下文数据
        await self.root.tick(npc, context)


# 常用行为节点

class PatrolNode(ActionNode):
    """巡逻节点"""
    
    def __init__(self):
        super().__init__(self._patrol)
    
    async def _patrol(self, npc: "NPC", context: dict) -> bool:
        # 移动到下一个巡逻点
        # TODO: 实现巡逻逻辑
        return True


class ReturnHomeNode(ActionNode):
    """返回节点"""
    
    def __init__(self):
        super().__init__(self._return_home)
    
    async def _return_home(self, npc: "NPC", context: dict) -> bool:
        # 返回出生点
        home = npc.db.get("home_location")
        if home:
            # TODO: 移动到home
            pass
        return True
```

### 好感度与对话系统

```python
# src/game/npc/reputation.py
class NPCRelationship:
    """NPC关系管理"""
    
    RELATIONSHIP_LEVELS = [
        (-100, "仇敌"),
        (-50, "冷淡"),
        (0, "陌生"),
        (50, "友善"),
        (100, "尊敬"),
        (200, "至交"),
    ]
    
    def __init__(self, character: "Character"):
        self.character = character
    
    def get_favor(self, npc_id: str) -> int:
        """获取对特定NPC的好感度"""
        relations = self.character.db.get("npc_relations", {})
        return relations.get(npc_id, {}).get("favor", 0)
    
    def modify_favor(self, npc_id: str, delta: int, reason: str = "") -> None:
        """修改好感度"""
        relations = self.character.db.get("npc_relations", {})
        if npc_id not in relations:
            relations[npc_id] = {}
        
        relations[npc_id]["favor"] = relations[npc_id].get("favor", 0) + delta
        
        # 记录原因
        if "history" not in relations[npc_id]:
            relations[npc_id]["history"] = []
        relations[npc_id]["history"].append({"delta": delta, "reason": reason})
        
        self.character.db.set("npc_relations", relations)
    
    def get_relationship_level(self, npc_id: str) -> str:
        """获取关系等级名称"""
        favor = self.get_favor(npc_id)
        
        for threshold, name in self.RELATIONSHIP_LEVELS:
            if favor < threshold:
                return name
        return "至交"


# src/game/npc/dialogue.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class Response:
    """对话回应选项"""
    text: str
    next_node: Optional[str] = None
    conditions: dict = None  # 显示条件
    effects: dict = None     # 选择后的效果


@dataclass
class DialogueNode:
    """对话节点"""
    text: str                    # NPC说的话
    responses: list[Response]    # 玩家回应选项
    conditions: dict = None      # 显示条件
    effects: dict = None         # 显示后的效果


class DialogueSystem:
    """对话系统"""
    
    def __init__(self):
        self.dialogues: dict[str, dict[str, DialogueNode]] = {}
        # {npc_key: {node_id: DialogueNode}}
    
    def register_dialogue(
        self, 
        npc_key: str, 
        node_id: str, 
        node: DialogueNode
    ) -> None:
        """注册对话节点"""
        if npc_key not in self.dialogues:
            self.dialogues[npc_key] = {}
        self.dialogues[npc_key][node_id] = node
    
    async def start_dialogue(
        self, 
        character: "Character", 
        npc: "NPC"
    ) -> Optional[DialogueNode]:
        """开始对话
        
        返回起始对话节点
        """
        npc_dialogues = self.dialogues.get(npc.key, {})
        
        # 根据好感度选择起始节点
        favor = character.npc_relations.get_favor(npc.key)
        
        if favor < -50:
            start_node = "hostile"
        elif favor > 100:
            start_node = "friendly"
        else:
            start_node = "default"
        
        return npc_dialogues.get(start_node)
    
    async def select_response(
        self, 
        character: "Character", 
        npc: "NPC",
        current_node: DialogueNode,
        response_idx: int
    ) -> Optional[DialogueNode]:
        """选择回应
        
        Args:
            character: 玩家角色
            npc: NPC
            current_node: 当前对话节点
            response_idx: 回应选项索引
            
        Returns:
            下一个对话节点
        """
        if response_idx >= len(current_node.responses):
            return None
        
        response = current_node.responses[response_idx]
        
        # 应用效果
        if response.effects:
            if "favor_delta" in response.effects:
                character.npc_relations.modify_favor(
                    npc.key, 
                    response.effects["favor_delta"]
                )
            
            if "give_item" in response.effects:
                # TODO: 给予物品
                pass
            
            if "unlock_quest" in response.effects:
                # TODO: 解锁任务
                pass
        
        # 返回下一个节点
        if response.next_node:
            npc_dialogues = self.dialogues.get(npc.key, {})
            return npc_dialogues.get(response.next_node)
        
        return None
```
