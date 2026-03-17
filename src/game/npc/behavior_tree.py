"""NPC行为树系统."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Callable

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .core import NPC


class NodeStatus(Enum):
    """行为树节点状态."""

    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


class BehaviorNode(ABC):
    """行为树节点基类."""

    @abstractmethod
    async def tick(self, npc: NPC, context: dict) -> NodeStatus:
        """执行节点.

        Args:
            npc: NPC对象
            context: 上下文数据

        Returns:
            执行结果状态
        """
        pass


class SelectorNode(BehaviorNode):
    """选择节点 - 顺序执行子节点，直到有一个成功.

    类似于逻辑或(OR)：子节点有一个成功就返回成功
    """

    def __init__(self, children: list[BehaviorNode] | None = None):
        self.children = children or []

    async def tick(self, npc: NPC, context: dict) -> NodeStatus:
        for child in self.children:
            status = await child.tick(npc, context)
            if status == NodeStatus.SUCCESS:
                return NodeStatus.SUCCESS
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        return NodeStatus.FAILURE


class SequenceNode(BehaviorNode):
    """序列节点 - 顺序执行子节点，直到有一个失败.

    类似于逻辑与(AND)：所有子节点都成功才返回成功
    """

    def __init__(self, children: list[BehaviorNode] | None = None):
        self.children = children or []

    async def tick(self, npc: NPC, context: dict) -> NodeStatus:
        for child in self.children:
            status = await child.tick(npc, context)
            if status == NodeStatus.FAILURE:
                return NodeStatus.FAILURE
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        return NodeStatus.SUCCESS


class ParallelNode(BehaviorNode):
    """并行节点 - 执行所有子节点.

    根据成功阈值决定返回结果
    """

    def __init__(self, children: list[BehaviorNode] | None = None, success_threshold: int = 1):
        self.children = children or []
        self.success_threshold = success_threshold

    async def tick(self, npc: NPC, context: dict) -> NodeStatus:
        success_count = 0
        for child in self.children:
            status = await child.tick(npc, context)
            if status == NodeStatus.SUCCESS:
                success_count += 1

        if success_count >= self.success_threshold:
            return NodeStatus.SUCCESS
        return NodeStatus.FAILURE


class ActionNode(BehaviorNode):
    """动作节点 - 执行具体动作."""

    def __init__(self, action: Callable[[NPC, dict], bool | None]):
        self.action = action

    async def tick(self, npc: NPC, context: dict) -> NodeStatus:
        try:
            result = self.action(npc, context)
            # 支持异步和同步函数
            if hasattr(result, "__await__"):
                result = await result

            if result:
                return NodeStatus.SUCCESS
            return NodeStatus.FAILURE
        except Exception as e:
            # 可以在这里添加日志记录
            logger.exception(f"ActionNode error: {e}")
            return NodeStatus.FAILURE


class ConditionNode(BehaviorNode):
    """条件节点 - 检查条件."""

    def __init__(self, condition: Callable[[NPC, dict], bool]):
        self.condition = condition

    async def tick(self, npc: NPC, context: dict) -> NodeStatus:
        try:
            result = self.condition(npc, context)
            if hasattr(result, "__await__"):
                result = await result

            if result:
                return NodeStatus.SUCCESS
            return NodeStatus.FAILURE
        except Exception:
            logger.exception(f"ConditionNode执行失败: {self.condition}")
            return NodeStatus.FAILURE


class InverterNode(BehaviorNode):
    """反转节点 - 反转子节点结果."""

    def __init__(self, child: BehaviorNode):
        self.child = child

    async def tick(self, npc: NPC, context: dict) -> NodeStatus:
        status = await self.child.tick(npc, context)
        if status == NodeStatus.SUCCESS:
            return NodeStatus.FAILURE
        if status == NodeStatus.FAILURE:
            return NodeStatus.SUCCESS
        return status


class RepeatNode(BehaviorNode):
    """重复节点 - 重复执行子节点指定次数."""

    def __init__(self, child: BehaviorNode, times: int):
        self.child = child
        self.times = times
        self._count = 0

    async def tick(self, npc: NPC, context: dict) -> NodeStatus:
        while self._count < self.times:
            status = await self.child.tick(npc, context)
            if status == NodeStatus.FAILURE:
                return NodeStatus.FAILURE
            self._count += 1

        self._count = 0  # 重置计数
        return NodeStatus.SUCCESS


class NPCBehaviorTree:
    """NPC行为树."""

    def __init__(self, root: BehaviorNode | None = None):
        self.root = root

    async def tick(self, npc: NPC, context: dict | None = None) -> NodeStatus:
        """执行一次行为树.

        Args:
            npc: NPC对象
            context: 上下文数据

        Returns:
            执行结果
        """
        if not self.root:
            return NodeStatus.FAILURE

        context = context or {}
        return await self.root.tick(npc, context)

    def set_root(self, root: BehaviorNode) -> None:
        """设置根节点."""
        self.root = root


# ===== 常用行为节点 =====

class PatrolNode(ActionNode):
    """巡逻节点."""

    def __init__(self, patrol_points: list[str] | None = None):
        self.patrol_points = patrol_points or []
        self._current_index = 0
        super().__init__(self._patrol)

    async def _patrol(self, npc: NPC, context: dict) -> bool:
        """执行巡逻."""
        if not self.patrol_points:
            return False

        # 获取下一个巡逻点
        point = self.patrol_points[self._current_index]
        self._current_index = (self._current_index + 1) % len(self.patrol_points)

        # TD-002: 实现移动到巡逻点的逻辑
        from .behavior_nodes import MovementController
        success = await MovementController.move_to(npc, point)
        
        if success:
            context["patrol_target"] = point
            return True
        return False


class ReturnHomeNode(ActionNode):
    """返回出生点节点."""

    def __init__(self, max_distance: float = 50.0):
        self.max_distance = max_distance
        super().__init__(self._return_home)

    async def _return_home(self, npc: NPC, context: dict) -> bool:
        """返回出生点."""
        home = npc.home_location
        if not home:
            return False

        # TD-003: 检查当前位置与出生点的距离
        from .behavior_nodes import MovementController
        distance = MovementController.get_distance_to_home(npc)
        
        # 如果超出max_distance，则移动回家
        if distance > self.max_distance:
            success = await MovementController.move_to(npc, home)
            if success:
                context["home_target"] = home
                context["distance_returned"] = distance
                return True
            return False
        
        # 距离范围内，不需要回家
        return True


class RandomMoveNode(ActionNode):
    """随机移动节点."""

    def __init__(self, probability: float = 0.3):
        self.probability = probability
        super().__init__(self._random_move)

    async def _random_move(self, npc: NPC, context: dict) -> bool:
        """随机移动."""
        import random

        if random.random() > self.probability:
            return False

        # TD-004: 实现随机移动逻辑
        from .behavior_nodes import MovementController
        success = await MovementController.move_randomly(npc)
        
        if success:
            context["random_moved"] = True
            return True
        return False


class IsInCombatNode(ConditionNode):
    """检查是否在战斗中."""

    def __init__(self):
        super().__init__(self._check_combat)

    async def _check_combat(self, npc: NPC, context: dict) -> bool:
        # TD-005: 检查NPC是否在战斗中
        from .behavior_nodes import CombatChecker
        in_combat = CombatChecker.is_in_combat(npc)
        context["in_combat"] = in_combat
        return in_combat


class IsNightNode(ConditionNode):
    """检查是否是夜晚."""

    def __init__(self):
        super().__init__(self._check_night)

    async def _check_night(self, npc: NPC, context: dict) -> bool:
        # TD-006: 从游戏时间系统获取当前时间
        from .behavior_nodes import GameTime
        is_night = GameTime.is_night()
        context["is_night"] = is_night
        context["current_hour"] = GameTime.get_current_hour()
        return is_night


class HasPlayerNearbyNode(ConditionNode):
    """检查附近是否有玩家."""

    def __init__(self, range_distance: float = 10.0):
        self.range_distance = range_distance
        super().__init__(self._check_player)

    async def _check_player(self, npc: NPC, context: dict) -> bool:
        # TD-007: 检查范围内是否有玩家
        from .behavior_nodes import NPCUtils
        players = NPCUtils.get_nearby_players(npc, self.range_distance)
        has_player = len(players) > 0
        context["nearby_players"] = players
        context["player_count"] = len(players)
        return has_player


class IsTooFarFromHomeNode(ConditionNode):
    """检查是否离家太远."""

    def __init__(self, max_distance: float = 50.0):
        self.max_distance = max_distance
        super().__init__(self._check_distance)

    async def _check_distance(self, npc: NPC, context: dict) -> bool:
        # TD-008: 检查是否离家太远
        from .behavior_nodes import MovementController
        distance = MovementController.get_distance_to_home(npc)
        too_far = distance > self.max_distance
        context["distance_to_home"] = distance
        context["max_distance"] = self.max_distance
        context["too_far_from_home"] = too_far
        return too_far


# ===== 预设行为树 =====

def create_patrol_behavior(patrol_points: list[str]) -> NPCBehaviorTree:
    """创建巡逻行为树.

    Args:
        patrol_points: 巡逻点列表（房间key）

    Returns:
        行为树实例
    """
    # 根节点：选择节点
    # 1. 如果离家太远，回家
    # 2. 否则巡逻
    root = SelectorNode([
        SequenceNode([
            IsTooFarFromHomeNode(max_distance=50.0),  # TD-008: 检查是否离家太远
            ReturnHomeNode(),
        ]),
        PatrolNode(patrol_points),
    ])

    return NPCBehaviorTree(root)


def create_guard_behavior() -> NPCBehaviorTree:
    """创建守卫行为树.

    守卫特点：
    - 主要在固定位置警戒
    - 发现敌人时攻击
    - 夜间保持警觉
    """
    root = SelectorNode([
        # 如果在战斗中，继续战斗
        SequenceNode([
            IsInCombatNode(),
            ActionNode(lambda n, c: True),  # 保持战斗状态
        ]),
        # 夜晚时更加警觉
        SequenceNode([
            IsNightNode(),
            ActionNode(lambda n, c: True),  # 保持警戒
        ]),
        # 平时随机走动
        RandomMoveNode(probability=0.1),
    ])

    return NPCBehaviorTree(root)


def create_merchant_behavior() -> NPCBehaviorTree:
    """创建商人行为树.

    商人特点：
    - 主要在固定位置
    - 白天营业
    - 夜间休息
    """
    root = SelectorNode([
        # 夜晚回家/休息
        SequenceNode([
            IsNightNode(),
            ReturnHomeNode(),
        ]),
        # 白天营业
        SequenceNode([
            HasPlayerNearbyNode(),
            ActionNode(lambda n, c: True),  # 与玩家互动
        ]),
        # 平时待在原地
        ActionNode(lambda n, c: True),
    ])

    return NPCBehaviorTree(root)
