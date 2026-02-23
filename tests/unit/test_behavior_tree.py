"""NPC行为树单元测试.

测试BehaviorNode及其子类.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from src.game.npc.behavior_tree import (
    ActionNode,
    BehaviorNode,
    ConditionNode,
    create_guard_behavior,
    create_merchant_behavior,
    create_patrol_behavior,
    HasPlayerNearbyNode,
    InverterNode,
    IsInCombatNode,
    IsNightNode,
    NodeStatus,
    NPCBehaviorTree,
    ParallelNode,
    PatrolNode,
    RandomMoveNode,
    RepeatNode,
    ReturnHomeNode,
    SelectorNode,
    SequenceNode,
)


class TestNodeStatus:
    """NodeStatus枚举测试."""

    def test_node_status_values(self):
        """测试节点状态值."""
        assert NodeStatus.SUCCESS.value == "success"
        assert NodeStatus.FAILURE.value == "failure"
        assert NodeStatus.RUNNING.value == "running"


class TestBehaviorNode:
    """BehaviorNode基类测试."""

    def test_behavior_node_is_abstract(self):
        """测试BehaviorNode是抽象基类."""
        from src.game.npc.behavior_tree import BehaviorNode
        
        # 不能直接实例化抽象基类
        with pytest.raises(TypeError):
            BehaviorNode()


class TestSelectorNode:
    """SelectorNode选择节点测试."""

    @pytest.fixture
    def npc(self):
        """创建测试NPC."""
        return Mock()

    @pytest.mark.asyncio
    async def test_selector_all_success(self, npc):
        """测试所有子节点成功."""
        child1 = Mock()
        child1.tick = AsyncMock(return_value=NodeStatus.SUCCESS)
        child2 = Mock()
        child2.tick = AsyncMock(return_value=NodeStatus.SUCCESS)
        
        selector = SelectorNode([child1, child2])
        result = await selector.tick(npc, {})
        
        assert result == NodeStatus.SUCCESS
        child1.tick.assert_called_once()
        child2.tick.assert_not_called()  # 第一个成功就不执行后面的

    @pytest.mark.asyncio
    async def test_selector_first_failure(self, npc):
        """测试第一个失败执行第二个."""
        child1 = Mock()
        child1.tick = AsyncMock(return_value=NodeStatus.FAILURE)
        child2 = Mock()
        child2.tick = AsyncMock(return_value=NodeStatus.SUCCESS)
        
        selector = SelectorNode([child1, child2])
        result = await selector.tick(npc, {})
        
        assert result == NodeStatus.SUCCESS
        child1.tick.assert_called_once()
        child2.tick.assert_called_once()

    @pytest.mark.asyncio
    async def test_selector_all_failure(self, npc):
        """测试所有子节点失败."""
        child1 = Mock()
        child1.tick = AsyncMock(return_value=NodeStatus.FAILURE)
        child2 = Mock()
        child2.tick = AsyncMock(return_value=NodeStatus.FAILURE)
        
        selector = SelectorNode([child1, child2])
        result = await selector.tick(npc, {})
        
        assert result == NodeStatus.FAILURE

    @pytest.mark.asyncio
    async def test_selector_running(self, npc):
        """测试RUNNING状态."""
        child1 = Mock()
        child1.tick = AsyncMock(return_value=NodeStatus.RUNNING)
        
        selector = SelectorNode([child1])
        result = await selector.tick(npc, {})
        
        assert result == NodeStatus.RUNNING


class TestSequenceNode:
    """SequenceNode序列节点测试."""

    @pytest.fixture
    def npc(self):
        """创建测试NPC."""
        return Mock()

    @pytest.mark.asyncio
    async def test_sequence_all_success(self, npc):
        """测试所有子节点成功."""
        child1 = Mock()
        child1.tick = AsyncMock(return_value=NodeStatus.SUCCESS)
        child2 = Mock()
        child2.tick = AsyncMock(return_value=NodeStatus.SUCCESS)
        
        sequence = SequenceNode([child1, child2])
        result = await sequence.tick(npc, {})
        
        assert result == NodeStatus.SUCCESS
        child1.tick.assert_called_once()
        child2.tick.assert_called_once()

    @pytest.mark.asyncio
    async def test_sequence_first_failure(self, npc):
        """测试第一个失败停止执行."""
        child1 = Mock()
        child1.tick = AsyncMock(return_value=NodeStatus.FAILURE)
        child2 = Mock()
        child2.tick = AsyncMock(return_value=NodeStatus.SUCCESS)
        
        sequence = SequenceNode([child1, child2])
        result = await sequence.tick(npc, {})
        
        assert result == NodeStatus.FAILURE
        child1.tick.assert_called_once()
        child2.tick.assert_not_called()  # 不执行后面的

    @pytest.mark.asyncio
    async def test_sequence_running(self, npc):
        """测试RUNNING状态."""
        child1 = Mock()
        child1.tick = AsyncMock(return_value=NodeStatus.RUNNING)
        
        sequence = SequenceNode([child1])
        result = await sequence.tick(npc, {})
        
        assert result == NodeStatus.RUNNING


class TestParallelNode:
    """ParallelNode并行节点测试."""

    @pytest.fixture
    def npc(self):
        """创建测试NPC."""
        return Mock()

    @pytest.mark.asyncio
    async def test_parallel_meets_threshold(self, npc):
        """测试达到成功阈值."""
        child1 = Mock()
        child1.tick = AsyncMock(return_value=NodeStatus.SUCCESS)
        child2 = Mock()
        child2.tick = AsyncMock(return_value=NodeStatus.SUCCESS)
        child3 = Mock()
        child3.tick = AsyncMock(return_value=NodeStatus.FAILURE)
        
        # 阈值为2，至少2个成功
        parallel = ParallelNode([child1, child2, child3], success_threshold=2)
        result = await parallel.tick(npc, {})
        
        assert result == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_parallel_not_meets_threshold(self, npc):
        """测试未达到成功阈值."""
        child1 = Mock()
        child1.tick = AsyncMock(return_value=NodeStatus.SUCCESS)
        child2 = Mock()
        child2.tick = AsyncMock(return_value=NodeStatus.FAILURE)
        child3 = Mock()
        child3.tick = AsyncMock(return_value=NodeStatus.FAILURE)
        
        # 阈值为2，只有1个成功
        parallel = ParallelNode([child1, child2, child3], success_threshold=2)
        result = await parallel.tick(npc, {})
        
        assert result == NodeStatus.FAILURE


class TestActionNode:
    """ActionNode动作节点测试."""

    @pytest.fixture
    def npc(self):
        """创建测试NPC."""
        return Mock()

    @pytest.mark.asyncio
    async def test_action_success(self, npc):
        """测试成功的动作."""
        action = Mock(return_value=True)
        
        node = ActionNode(action)
        result = await node.tick(npc, {})
        
        assert result == NodeStatus.SUCCESS
        action.assert_called_once_with(npc, {})

    @pytest.mark.asyncio
    async def test_action_failure(self, npc):
        """测试失败的动作."""
        action = Mock(return_value=False)
        
        node = ActionNode(action)
        result = await node.tick(npc, {})
        
        assert result == NodeStatus.FAILURE

    @pytest.mark.asyncio
    async def test_action_async(self, npc):
        """测试异步动作."""
        async def async_action(npc, context):
            return True
        
        node = ActionNode(async_action)
        result = await node.tick(npc, {})
        
        assert result == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_action_exception(self, npc):
        """测试动作抛出异常."""
        action = Mock(side_effect=Exception("Error"))
        
        node = ActionNode(action)
        result = await node.tick(npc, {})
        
        assert result == NodeStatus.FAILURE


class TestConditionNode:
    """ConditionNode条件节点测试."""

    @pytest.fixture
    def npc(self):
        """创建测试NPC."""
        return Mock()

    @pytest.mark.asyncio
    async def test_condition_true(self, npc):
        """测试条件为真."""
        condition = Mock(return_value=True)
        
        node = ConditionNode(condition)
        result = await node.tick(npc, {})
        
        assert result == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_condition_false(self, npc):
        """测试条件为假."""
        condition = Mock(return_value=False)
        
        node = ConditionNode(condition)
        result = await node.tick(npc, {})
        
        assert result == NodeStatus.FAILURE

    @pytest.mark.asyncio
    async def test_condition_exception(self, npc):
        """测试条件抛出异常."""
        condition = Mock(side_effect=Exception("Error"))
        
        node = ConditionNode(condition)
        result = await node.tick(npc, {})
        
        assert result == NodeStatus.FAILURE


class TestInverterNode:
    """InverterNode反转节点测试."""

    @pytest.fixture
    def npc(self):
        """创建测试NPC."""
        return Mock()

    @pytest.mark.asyncio
    async def test_inverter_success_to_failure(self, npc):
        """测试成功反转为失败."""
        child = Mock()
        child.tick = AsyncMock(return_value=NodeStatus.SUCCESS)
        
        inverter = InverterNode(child)
        result = await inverter.tick(npc, {})
        
        assert result == NodeStatus.FAILURE

    @pytest.mark.asyncio
    async def test_inverter_failure_to_success(self, npc):
        """测试失败反转为成功."""
        child = Mock()
        child.tick = AsyncMock(return_value=NodeStatus.FAILURE)
        
        inverter = InverterNode(child)
        result = await inverter.tick(npc, {})
        
        assert result == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_inverter_running_unchanged(self, npc):
        """测试RUNNING状态不变."""
        child = Mock()
        child.tick = AsyncMock(return_value=NodeStatus.RUNNING)
        
        inverter = InverterNode(child)
        result = await inverter.tick(npc, {})
        
        assert result == NodeStatus.RUNNING


class TestRepeatNode:
    """RepeatNode重复节点测试."""

    @pytest.fixture
    def npc(self):
        """创建测试NPC."""
        return Mock()

    @pytest.mark.asyncio
    async def test_repeat_success(self, npc):
        """测试重复执行成功."""
        child = Mock()
        child.tick = AsyncMock(return_value=NodeStatus.SUCCESS)
        
        repeat = RepeatNode(child, times=3)
        result = await repeat.tick(npc, {})
        
        assert result == NodeStatus.SUCCESS
        assert child.tick.call_count == 3

    @pytest.mark.asyncio
    async def test_repeat_failure_stops(self, npc):
        """测试失败时停止重复."""
        child = Mock()
        child.tick = AsyncMock(return_value=NodeStatus.FAILURE)
        
        repeat = RepeatNode(child, times=5)
        result = await repeat.tick(npc, {})
        
        assert result == NodeStatus.FAILURE
        assert child.tick.call_count == 1  # 第一次就失败


class TestNPCBehaviorTree:
    """NPCBehaviorTree行为树测试."""

    @pytest.fixture
    def npc(self):
        """创建测试NPC."""
        return Mock()

    @pytest.mark.asyncio
    async def test_behavior_tree_tick(self, npc):
        """测试行为树执行."""
        root = Mock()
        root.tick = AsyncMock(return_value=NodeStatus.SUCCESS)
        
        tree = NPCBehaviorTree(root)
        result = await tree.tick(npc)
        
        assert result == NodeStatus.SUCCESS
        root.tick.assert_called_once_with(npc, {})

    @pytest.mark.asyncio
    async def test_behavior_tree_no_root(self, npc):
        """测试无根节点时执行."""
        tree = NPCBehaviorTree()
        result = await tree.tick(npc)
        
        assert result == NodeStatus.FAILURE

    def test_behavior_tree_set_root(self):
        """测试设置根节点."""
        tree = NPCBehaviorTree()
        root = Mock()
        
        tree.set_root(root)
        
        assert tree.root == root


class TestReturnHomeNode:
    """ReturnHomeNode回家节点测试."""

    @pytest.fixture
    def npc(self):
        """创建测试NPC."""
        npc = Mock()
        npc.home_location = "home_room"
        npc.db = Mock()
        npc.db.get = Mock(return_value="home_room")
        return npc

    @pytest.mark.asyncio
    async def test_return_home_with_home(self, npc):
        """测试有出生点时回家."""
        node = ReturnHomeNode()
        
        context = {}
        result = await node.tick(npc, context)
        
        assert result == NodeStatus.SUCCESS
        assert context.get("home_target") == "home_room"

    @pytest.mark.asyncio
    async def test_return_home_no_home(self, npc):
        """测试无出生点时失败."""
        npc.home_location = None
        npc.db.get = Mock(return_value=None)
        
        node = ReturnHomeNode()
        
        result = await node.tick(npc, {})
        
        assert result == NodeStatus.FAILURE


class TestPatrolNode:
    """PatrolNode巡逻节点测试."""

    @pytest.mark.asyncio
    async def test_patrol_with_points(self):
        """测试有巡逻点时巡逻."""
        npc = Mock()
        node = PatrolNode(patrol_points=["room1", "room2", "room3"])
        
        context = {}
        result = await node.tick(npc, context)
        
        assert result == NodeStatus.SUCCESS
        assert context.get("patrol_target") == "room1"
    
    @pytest.mark.asyncio
    async def test_patrol_empty_points(self):
        """测试无巡逻点时失败."""
        npc = Mock()
        node = PatrolNode(patrol_points=[])
        
        context = {}
        result = await node.tick(npc, context)
        
        assert result == NodeStatus.FAILURE
    
    @pytest.mark.asyncio
    async def test_patrol_default_points(self):
        """测试默认空巡逻点."""
        npc = Mock()
        node = PatrolNode()  # 不传入巡逻点
        
        context = {}
        result = await node.tick(npc, context)
        
        assert result == NodeStatus.FAILURE
    
    @pytest.mark.asyncio
    async def test_patrol_cycles_through_points(self):
        """测试巡逻点循环."""
        npc = Mock()
        node = PatrolNode(patrol_points=["room1", "room2"])
        
        context1 = {}
        await node.tick(npc, context1)
        assert context1.get("patrol_target") == "room1"
        
        context2 = {}
        await node.tick(npc, context2)
        assert context2.get("patrol_target") == "room2"
        
        context3 = {}
        await node.tick(npc, context3)
        # 应该回到第一个点
        assert context3.get("patrol_target") == "room1"


class TestReturnHomeNodeExtended:
    """ReturnHomeNode回家节点扩展测试."""

    @pytest.mark.asyncio
    async def test_return_home_default_max_distance(self):
        """测试默认最大距离."""
        node = ReturnHomeNode()  # 使用默认max_distance
        
        assert node.max_distance == 50.0
    
    @pytest.mark.asyncio
    async def test_return_home_custom_max_distance(self):
        """测试自定义最大距离."""
        node = ReturnHomeNode(max_distance=100.0)
        
        assert node.max_distance == 100.0


class TestRandomMoveNode:
    """RandomMoveNode随机移动节点测试."""

    @pytest.mark.asyncio
    async def test_random_move_probability_pass(self):
        """测试随机移动成功（概率通过）."""
        import random
        
        npc = Mock()
        node = RandomMoveNode(probability=1.0)  # 100%概率
        
        result = await node.tick(npc, {})
        
        assert result == NodeStatus.SUCCESS
    
    @pytest.mark.asyncio
    async def test_random_move_probability_fail(self):
        """测试随机移动失败（概率未通过）."""
        import random
        
        npc = Mock()
        node = RandomMoveNode(probability=0.0)  # 0%概率
        
        result = await node.tick(npc, {})
        
        assert result == NodeStatus.FAILURE
    
    def test_random_move_default_probability(self):
        """测试默认概率值."""
        node = RandomMoveNode()
        
        assert node.probability == 0.3


class TestConditionNodes:
    """条件节点测试."""

    @pytest.mark.asyncio
    async def test_is_in_combat_node(self):
        """测试战斗中检查节点."""
        npc = Mock()
        node = IsInCombatNode()
        
        result = await node.tick(npc, {})
        
        # 当前实现返回False
        assert result == NodeStatus.FAILURE
    
    @pytest.mark.asyncio
    async def test_is_night_node(self):
        """测试夜晚检查节点."""
        npc = Mock()
        node = IsNightNode()
        
        result = await node.tick(npc, {})
        
        # 当前实现返回False
        assert result == NodeStatus.FAILURE
    
    @pytest.mark.asyncio
    async def test_has_player_nearby_node(self):
        """测试附近玩家检查节点."""
        npc = Mock()
        node = HasPlayerNearbyNode()
        
        result = await node.tick(npc, {})
        
        # 当前实现返回False
        assert result == NodeStatus.FAILURE
    
    @pytest.mark.asyncio
    async def test_has_player_nearby_custom_range(self):
        """测试附近玩家检查节点自定义范围."""
        npc = Mock()
        node = HasPlayerNearbyNode(range_distance=20.0)
        
        assert node.range_distance == 20.0


class TestBehaviorTreeFactories:
    """行为树工厂函数测试."""

    def test_create_patrol_behavior(self):
        """测试创建巡逻行为树."""
        tree = create_patrol_behavior(["room1", "room2", "room3"])
        
        assert tree is not None
        assert tree.root is not None
    
    def test_create_guard_behavior(self):
        """测试创建守卫行为树."""
        tree = create_guard_behavior()
        
        assert tree is not None
        assert tree.root is not None
    
    def test_create_merchant_behavior(self):
        """测试创建商人行为树."""
        tree = create_merchant_behavior()
        
        assert tree is not None
        assert tree.root is not None
