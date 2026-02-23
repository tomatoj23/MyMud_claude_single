"""NPC系统单元测试.

使用集成fixture测试NPC功能.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from src.game.npc.core import NPC, NPCType


class TestNPCType:
    """NPCType枚举测试."""

    def test_npc_type_values(self):
        """测试NPC类型值."""
        assert NPCType.NORMAL.value == "normal"
        assert NPCType.MERCHANT.value == "merchant"
        assert NPCType.TRAINER.value == "trainer"
        assert NPCType.QUEST.value == "quest"
        assert NPCType.BOSS.value == "boss"
        assert NPCType.ENEMY.value == "enemy"


@pytest.mark.asyncio
class TestNPC:
    """NPC类测试."""

    async def test_npc_type_default(self, engine):
        """测试默认NPC类型."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        assert npc.npc_type == NPCType.NORMAL

    async def test_npc_type_setter(self, engine):
        """测试设置NPC类型."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        npc.npc_type = NPCType.MERCHANT
        assert npc.npc_type == NPCType.MERCHANT

    async def test_ai_enabled_default(self, engine):
        """测试默认AI启用状态."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        assert npc.ai_enabled is True

    async def test_ai_enabled_setter(self, engine):
        """测试设置AI启用状态."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        npc.ai_enabled = False
        assert npc.ai_enabled is False

    async def test_schedule_default(self, engine):
        """测试默认行程."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        # schedule默认可能是dict或list
        assert npc.schedule == {} or npc.schedule == []

    async def test_schedule_setter(self, engine):
        """测试设置行程."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        schedule = {"08:00": "open", "20:00": "close"}
        npc.schedule = schedule
        assert npc.schedule == schedule

    async def test_home_location_default(self, engine):
        """测试默认家位置."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        assert npc.home_location is None

    async def test_home_location_setter(self, engine):
        """测试设置家位置."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        npc.home_location = 123
        assert npc.home_location == 123

    async def test_is_hostile_default(self, engine):
        """测试默认敌对状态."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        assert npc.is_hostile is False

    async def test_is_hostile_setter(self, engine):
        """测试设置敌对状态."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        npc.is_hostile = True
        assert npc.is_hostile is True

    async def test_dialogue_key_default(self, engine):
        """测试默认对话键."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        assert npc.dialogue_key is None

    async def test_dialogue_key_setter(self, engine):
        """测试设置对话键."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        npc.dialogue_key = "test_dialogue"
        assert npc.dialogue_key == "test_dialogue"


@pytest.mark.asyncio
class TestNPCTypes:
    """NPC类型检查测试."""

    async def test_is_merchant_true(self, engine):
        """测试商人类型检查（是商人）."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="merchant",
            attributes={"npc_type": "merchant"},
        )
        assert npc.is_merchant is True

    async def test_is_merchant_false(self, engine):
        """测试商人类型检查（不是商人）."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="normal_npc",
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

    async def test_is_trainer_false(self, engine):
        """测试训练师类型检查（不是训练师）."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="normal_npc",
        )
        assert npc.is_trainer is False

    async def test_is_quest_giver_true(self, engine):
        """测试任务NPC类型检查（是）."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="quest_npc",
            attributes={"npc_type": "quest"},
        )
        assert npc.is_quest_giver is True

    async def test_is_quest_giver_false(self, engine):
        """测试任务NPC类型检查（不是）."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="normal_npc",
        )
        assert npc.is_quest_giver is False


@pytest.mark.asyncio
class TestNPCInteraction:
    """NPC交互测试."""

    async def test_can_trade_as_merchant(self, engine):
        """测试商人可以交易."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="merchant",
            attributes={"npc_type": "merchant"},
        )
        assert npc.can_trade() is True

    async def test_can_trade_as_normal(self, engine):
        """测试普通NPC不能交易."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="normal_npc",
        )
        assert npc.can_trade() is False

    async def test_can_trade_as_enemy(self, engine):
        """测试敌对NPC不能交易."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="enemy",
            attributes={
                "npc_type": "enemy",
                "is_hostile": True,
            },
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

    async def test_can_train_as_normal(self, engine):
        """测试普通NPC不能教学."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="normal_npc",
        )
        assert npc.can_train() is False


@pytest.mark.asyncio
class TestNPCDialogue:
    """NPC对话测试."""

    async def test_get_dialogue_key_custom(self, engine):
        """测试获取自定义对话键."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="npc",
            attributes={"dialogue_key": "custom_dialogue"},
        )
        assert npc.get_dialogue_key() == "custom_dialogue"

    async def test_get_dialogue_key_default(self, engine):
        """测试获取默认对话键."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        assert npc.get_dialogue_key() == "test_npc"


@pytest.mark.asyncio
class TestNPCBehaviorTree:
    """NPC行为树测试."""

    async def test_update_ai_disabled(self, engine):
        """测试AI禁用时更新."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        npc.ai_enabled = False
        # 不应抛出异常
        await npc.update_ai(0.1)

    async def test_update_ai_no_behavior_tree(self, engine):
        """测试无行为树时更新."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        npc._behavior_tree = None
        # 不应抛出异常
        await npc.update_ai(0.1)

    async def test_set_behavior_tree(self, engine):
        """测试设置行为树."""
        from src.game.npc.behavior_tree import SelectorNode, ActionNode
        
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        action = ActionNode(lambda n, c: True)
        selector = SelectorNode([action])
        
        npc.set_behavior_tree(selector)
        assert npc._behavior_tree is not None

    async def test_update_ai_with_behavior_tree(self, engine):
        """测试有行为树时更新."""
        from src.game.npc.behavior_tree import SelectorNode, ActionNode
        
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        action = ActionNode(lambda n, c: True)
        selector = SelectorNode([action])
        npc.set_behavior_tree(selector)
        
        # 不应抛出异常
        await npc.update_ai(0.1)

    async def test_behavior_tree_property(self, engine):
        """测试behavior_tree属性getter."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        # 测试默认返回None
        assert npc.behavior_tree is None
        
        from src.game.npc.behavior_tree import SelectorNode, ActionNode
        action = ActionNode(lambda n, c: True)
        selector = SelectorNode([action])
        npc.set_behavior_tree(selector)
        
        # 测试能获取设置的行为树
        assert npc.behavior_tree is selector


@pytest.mark.asyncio
class TestNPCCombat:
    """NPC战斗相关测试."""

    async def test_at_combat_start(self, engine):
        """测试战斗开始时禁用AI."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        npc.ai_enabled = True
        
        # 模拟战斗开始
        mock_combat = Mock()
        npc.at_combat_start(mock_combat)
        
        # AI应该被禁用
        assert npc.ai_enabled is False

    async def test_at_combat_end(self, engine):
        """测试战斗结束时恢复AI."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="test_npc",
        )
        npc.ai_enabled = False
        
        # 模拟战斗结束
        mock_combat = Mock()
        npc.at_combat_end(mock_combat)
        
        # AI应该被恢复
        assert npc.ai_enabled is True


class TestNPCTypesAdditional:
    """额外的NPC类型检查测试."""

    @pytest.mark.asyncio
    async def test_is_merchant_property(self, engine):
        """测试is_merchant属性（通过behavior_tree属性getter触发db访问）."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="merchant",
            attributes={"npc_type": "merchant"},
        )
        # 访问属性触发代码覆盖
        assert npc.is_merchant is True

    @pytest.mark.asyncio
    async def test_is_trainer_property(self, engine):
        """测试is_trainer属性（通过behavior_tree属性getter触发db访问）."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="trainer",
            attributes={"npc_type": "trainer"},
        )
        assert npc.is_trainer is True

    @pytest.mark.asyncio
    async def test_is_quest_giver_property(self, engine):
        """测试is_quest_giver属性."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="quest_npc",
            attributes={"npc_type": "quest"},
        )
        assert npc.is_quest_giver is True


class TestNPCFactory:
    """NPC工厂方法测试."""

    @pytest.mark.asyncio
    async def test_create_merchant(self, engine):
        """测试创建商人NPC."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="merchant_1",
            attributes={
                "npc_type": "merchant",
                "shop_items": ["sword", "shield"]
            }
        )
        
        assert npc.key == "merchant_1"
        assert npc.npc_type == NPCType.MERCHANT
        assert npc.db.get("shop_items") == ["sword", "shield"]

    @pytest.mark.asyncio
    async def test_create_trainer(self, engine):
        """测试创建训练师NPC."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="trainer_1",
            attributes={
                "npc_type": "trainer",
                "teachable_wuxue": ["taijiquan", "wudangjian"]
            }
        )
        
        assert npc.key == "trainer_1"
        assert npc.npc_type == NPCType.TRAINER
        assert npc.db.get("teachable_wuxue") == ["taijiquan", "wudangjian"]

    @pytest.mark.asyncio
    async def test_create_enemy(self, engine):
        """测试创建敌人NPC."""
        npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="enemy_1",
            attributes={
                "npc_type": "enemy",
                "is_hostile": True,
                "level": 5
            }
        )
        
        assert npc.key == "enemy_1"
        assert npc.npc_type == NPCType.ENEMY
        assert npc.is_hostile is True
        assert npc.level == 5


class TestNPCCharacterIntegration:
    """NPC与Character集成测试."""

    @pytest.mark.asyncio
    async def test_character_npc_relations_property(self, engine):
        """测试Character的npc_relations属性."""
        from src.game.typeclasses.character import Character
        from src.game.npc.reputation import NPCRelationship
        
        character = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="test_char",
        )
        
        # 访问npc_relations属性应返回NPCRelationship实例
        relations = character.npc_relations
        assert isinstance(relations, NPCRelationship)
        assert relations.character == character

    @pytest.mark.asyncio
    async def test_character_npc_relations_lazy_init(self, engine):
        """测试npc_relations延迟初始化."""
        from src.game.typeclasses.character import Character
        from src.game.npc.reputation import NPCRelationship
        
        character = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="test_char2",
        )
        
        # 首次访问创建实例
        relations1 = character.npc_relations
        # 再次访问返回同一实例
        relations2 = character.npc_relations
        
        assert relations1 is relations2


class TestNPCFactoryMethods:
    """NPC工厂方法单元测试（使用Mock）."""

    def test_create_merchant_factory(self):
        """测试create_merchant工厂方法."""
        mock_npc = Mock(spec=NPC)
        mock_npc.db = Mock()
        mock_npc.db.set = Mock()
        
        with patch.object(NPC, '__new__', return_value=mock_npc):
            result = NPC.create_merchant("merchant_1", "王老板", shop_items=["sword"])
        
        assert result.npc_type == NPCType.MERCHANT
        result.db.set.assert_called_once_with("shop_items", ["sword"])

    def test_create_trainer_factory(self):
        """测试create_trainer工厂方法."""
        mock_npc = Mock(spec=NPC)
        mock_npc.db = Mock()
        mock_npc.db.set = Mock()
        
        with patch.object(NPC, '__new__', return_value=mock_npc):
            result = NPC.create_trainer("trainer_1", "张师傅", teachable_wuxue=["taiji"])
        
        assert result.npc_type == NPCType.TRAINER
        result.db.set.assert_called_once_with("teachable_wuxue", ["taiji"])

    def test_create_enemy_factory(self):
        """测试create_enemy工厂方法."""
        mock_npc = Mock(spec=NPC)
        mock_npc.db = Mock()
        
        with patch.object(NPC, '__new__', return_value=mock_npc):
            result = NPC.create_enemy("enemy_1", "山贼", level=5)
        
        assert result.npc_type == NPCType.ENEMY
        assert result.is_hostile is True
        assert result.level == 5
