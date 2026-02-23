"""NPC集成测试.

使用真实引擎创建NPC对象，测试完整功能.
"""

from __future__ import annotations

import pytest

from src.game.npc.behavior_tree import SelectorNode, SequenceNode, ActionNode, NodeStatus
from src.game.npc.core import NPC, NPCType
from src.engine.core.typeclass import TypeclassBase


@pytest.mark.asyncio
class TestNPCCreation:
    """NPC创建测试."""

    async def test_create_merchant(self, engine):
        """测试创建商人NPC."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="merchant_npc",
            attributes={
                "npc_type": "merchant",
                "dialogue_key": "merchant_dialogue",
            }
        )
        
        assert npc is not None
        assert npc.key == "merchant_npc"
        assert npc.npc_type == NPCType.MERCHANT
        assert npc.dialogue_key == "merchant_dialogue"

    async def test_create_trainer(self, engine):
        """测试创建训练师NPC."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="trainer_npc",
            attributes={
                "npc_type": NPCType.TRAINER.value,
            }
        )
        
        assert npc.npc_type == NPCType.TRAINER
        assert npc.is_trainer is True

    async def test_create_enemy(self, engine):
        """测试创建敌人NPC."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="enemy_npc",
            attributes={
                "npc_type": "enemy",
                "is_hostile": True,
            }
        )
        
        assert npc.npc_type == NPCType.ENEMY
        assert npc.is_hostile is True


@pytest.mark.asyncio
class TestNPCProperties:
    """NPC属性测试."""

    async def test_npc_type_default(self, engine):
        """测试默认NPC类型."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="normal_npc",
        )
        assert npc.npc_type == NPCType.NORMAL

    async def test_npc_type_setter(self, npc):
        """测试设置NPC类型."""
        npc.npc_type = NPCType.MERCHANT
        assert npc.npc_type == NPCType.MERCHANT

    async def test_ai_enabled_default(self, npc):
        """测试默认AI启用状态."""
        assert npc.ai_enabled is True

    async def test_ai_enabled_setter(self, npc):
        """测试设置AI启用状态."""
        npc.ai_enabled = False
        assert npc.ai_enabled is False

    async def test_schedule_default(self, npc):
        """测试默认日程."""
        assert npc.schedule == []

    async def test_schedule_setter(self, npc):
        """测试设置日程."""
        schedule = {"08:00": "open_shop", "20:00": "close_shop"}
        npc.schedule = schedule
        assert npc.schedule == schedule

    async def test_home_location_default(self, npc):
        """测试默认家位置."""
        assert npc.home_location is None

    async def test_home_location_setter(self, npc):
        """测试设置家位置."""
        # 创建另一个NPC作为位置
        location = await npc._manager.create(
            typeclass_path="src.engine.core.typeclass.TypeclassBase",
            key="home_room",
        )
        npc.home_location = location.id
        assert npc.home_location == location.id

    async def test_is_hostile_default(self, npc):
        """测试默认敌对状态."""
        assert npc.is_hostile is False

    async def test_is_hostile_setter(self, npc):
        """测试设置敌对状态."""
        npc.is_hostile = True
        assert npc.is_hostile is True

    async def test_dialogue_key_default(self, npc):
        """测试默认对话键."""
        assert npc.dialogue_key is None

    async def test_dialogue_key_setter(self, npc):
        """测试设置对话键."""
        npc.dialogue_key = "test_dialogue"
        assert npc.dialogue_key == "test_dialogue"


@pytest.mark.asyncio
class TestNPCTypeChecks:
    """NPC类型检查测试."""

    async def test_is_merchant_true(self, engine):
        """测试商人类型检查（是商人）."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="merchant",
            attributes={"npc_type": NPCType.MERCHANT.value},
        )
        assert npc.is_merchant is True

    async def test_is_merchant_false(self, engine):
        """测试商人类型检查（不是商人）."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="normal_npc",
            attributes={"npc_type": NPCType.NORMAL.value},
        )
        assert npc.is_merchant is False

    async def test_is_trainer_true(self, engine):
        """测试训练师类型检查（是训练师）."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="trainer",
            attributes={"npc_type": "trainer"},
        )
        assert npc.is_trainer is True

    async def test_is_trainer_false(self, npc):
        """测试训练师类型检查（不是训练师）."""
        assert npc.is_trainer is False

    async def test_is_quest_giver_true(self, engine):
        """测试任务给予者类型检查（是）."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="quest_giver",
            attributes={"npc_type": NPCType.QUEST.value},
        )
        assert npc.is_quest_giver is True

    async def test_is_quest_giver_false(self, npc):
        """测试任务给予者类型检查（不是）."""
        assert npc.is_quest_giver is False


@pytest.mark.asyncio
class TestNPCInteraction:
    """NPC交互测试."""

    async def test_can_trade_as_merchant(self, engine):
        """测试商人可以交易."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="merchant",
            attributes={"npc_type": NPCType.MERCHANT.value},
        )
        assert npc.can_trade() is True

    async def test_can_trade_as_normal(self, engine):
        """测试普通NPC不能交易."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="normal_npc",
            attributes={"npc_type": NPCType.NORMAL.value},
        )
        assert npc.can_trade() is False

    async def test_can_trade_as_enemy(self, engine):
        """测试敌对NPC不能交易."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="enemy",
            attributes={"npc_type": NPCType.ENEMY.value, "is_hostile": True},
        )
        assert npc.can_trade() is False

    async def test_can_train_as_trainer(self, engine):
        """测试训练师可以教学."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="trainer",
            attributes={"npc_type": "trainer"},
        )
        assert npc.can_train() is True

    async def test_can_train_as_normal(self, npc):
        """测试普通NPC不能教学."""
        assert npc.can_train() is False


@pytest.mark.asyncio
class TestNPCDialogue:
    """NPC对话测试."""

    async def test_get_dialogue_key_custom(self, engine):
        """测试获取自定义对话键."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="npc_with_dialogue",
            attributes={"dialogue_key": "custom_dialogue"},
        )
        assert npc.get_dialogue_key() == "custom_dialogue"

    async def test_get_dialogue_key_default(self, npc):
        """测试获取默认对话键."""
        # 默认使用NPC的key
        assert npc.get_dialogue_key() == npc.key


@pytest.mark.asyncio
class TestNPCBehaviorTree:
    """NPC行为树测试."""

    async def test_set_behavior_tree(self, npc):
        """测试设置行为树."""
        # 创建一个简单的选择节点
        action = ActionNode(lambda n, c: True)
        selector = SelectorNode([action])
        
        npc.set_behavior_tree(selector)
        assert npc._behavior_tree is not None

    async def test_update_ai_disabled(self, npc):
        """测试AI禁用时更新."""
        npc.ai_enabled = False
        # 不应该抛出异常
        await npc.update_ai(0.1)

    async def test_update_ai_no_behavior_tree(self, npc):
        """测试无行为树时更新."""
        npc._behavior_tree = None
        # 不应该抛出异常
        await npc.update_ai(0.1)

    async def test_update_ai_with_behavior_tree(self, npc):
        """测试有行为树时更新."""
        action = ActionNode(lambda n, c: True)
        selector = SelectorNode([action])
        npc.set_behavior_tree(selector)
        
        # 不应该抛出异常
        await npc.update_ai(0.1)
