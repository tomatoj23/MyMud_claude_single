"""NPC对话系统单元测试.

测试DialogueSystem, DialogueNode, Response类.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from src.game.npc.dialogue import DialogueNode, DialogueSystem, Response


class TestResponse:
    """Response类测试."""

    def test_response_init(self):
        """测试Response初始化."""
        response = Response(
            text="选项1",
            next_node="node2",
            conditions={"min_favor": 10},
            effects={"favor_delta": 5}
        )
        
        assert response.text == "选项1"
        assert response.next_node == "node2"
        assert response.conditions == {"min_favor": 10}
        assert response.effects == {"favor_delta": 5}

    def test_response_defaults(self):
        """测试Response默认值."""
        response = Response(text="简单选项")
        
        assert response.text == "简单选项"
        assert response.next_node is None
        assert response.conditions == {}
        assert response.effects == {}


class TestDialogueNode:
    """DialogueNode类测试."""

    def test_dialogue_node_init(self):
        """测试DialogueNode初始化."""
        responses = [Response("选项1"), Response("选项2")]
        node = DialogueNode(
            text="NPC说的话",
            responses=responses,
            conditions={"quest_active": "quest1"},
            effects={"favor_delta": 5}
        )
        
        assert node.text == "NPC说的话"
        assert node.responses == responses
        assert node.conditions == {"quest_active": "quest1"}
        assert node.effects == {"favor_delta": 5}

    def test_dialogue_node_defaults(self):
        """测试DialogueNode默认值."""
        node = DialogueNode(text="简单对话")
        
        assert node.text == "简单对话"
        assert node.responses == []
        assert node.conditions == {}
        assert node.effects == {}


class TestDialogueSystem:
    """DialogueSystem类测试."""

    @pytest.fixture
    def dialogue_system(self):
        """创建DialogueSystem实例."""
        return DialogueSystem()

    @pytest.fixture
    def character(self):
        """创建测试角色."""
        char = Mock()
        char.npc_relations = Mock()
        char.npc_relations.get_favor = Mock(return_value=0)
        char.level = 10
        char.menpai = "少林"
        char.is_quest_active = Mock(return_value=False)
        char.is_quest_completed = Mock(return_value=False)
        char.contents = []  # 添加可迭代的 contents
        # 设置 db.get 返回字典
        char.db = Mock()
        char.db.get = Mock(return_value={})
        return char

    @pytest.fixture
    def npc(self):
        """创建测试NPC."""
        npc = Mock()
        npc.key = "test_npc"
        npc.get_dialogue_key.return_value = "test_npc"
        return npc

    def test_dialogue_system_init(self, dialogue_system):
        """测试DialogueSystem初始化."""
        assert dialogue_system.dialogues == {}

    def test_register_dialogue(self, dialogue_system):
        """测试注册对话节点."""
        node = DialogueNode(text="测试对话")
        
        dialogue_system.register_dialogue("npc1", "default", node)
        
        assert "npc1" in dialogue_system.dialogues
        assert "default" in dialogue_system.dialogues["npc1"]
        assert dialogue_system.dialogues["npc1"]["default"] == node

    def test_register_dialogue_tree(self, dialogue_system):
        """测试批量注册对话树."""
        nodes = {
            "default": DialogueNode(text="默认"),
            "friendly": DialogueNode(text="友好")
        }
        
        dialogue_system.register_dialogue_tree("npc1", nodes)
        
        assert dialogue_system.dialogues["npc1"] == nodes

    def test_get_node_exists(self, dialogue_system):
        """测试获取存在的对话节点."""
        node = DialogueNode(text="测试")
        dialogue_system.register_dialogue("npc1", "default", node)
        
        result = dialogue_system.get_node("npc1", "default")
        
        assert result == node

    def test_get_node_nonexistent(self, dialogue_system):
        """测试获取不存在的对话节点."""
        result = dialogue_system.get_node("npc1", "default")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_start_dialogue_default(self, dialogue_system, character, npc):
        """测试开始默认对话."""
        default_node = DialogueNode(text="默认对话")
        dialogue_system.register_dialogue("test_npc", "default", default_node)
        
        result = await dialogue_system.start_dialogue(character, npc)
        
        assert result == default_node

    @pytest.mark.asyncio
    async def test_start_dialogue_hostile(self, dialogue_system, character, npc):
        """测试敌对状态下的对话."""
        character.npc_relations.get_favor.return_value = -100
        
        hostile_node = DialogueNode(text="敌对对话")
        default_node = DialogueNode(text="默认对话")
        
        dialogue_system.register_dialogue("test_npc", "hostile", hostile_node)
        dialogue_system.register_dialogue("test_npc", "default", default_node)
        
        result = await dialogue_system.start_dialogue(character, npc)
        
        assert result == hostile_node

    @pytest.mark.asyncio
    async def test_start_dialogue_friendly(self, dialogue_system, character, npc):
        """测试友好状态下的对话."""
        character.npc_relations.get_favor.return_value = 150
        
        friendly_node = DialogueNode(text="友好对话")
        default_node = DialogueNode(text="默认对话")
        
        dialogue_system.register_dialogue("test_npc", "friendly", friendly_node)
        dialogue_system.register_dialogue("test_npc", "default", default_node)
        
        result = await dialogue_system.start_dialogue(character, npc)
        
        assert result == friendly_node

    @pytest.mark.asyncio
    async def test_start_dialogue_know(self, dialogue_system, character, npc):
        """测试认识状态下的对话."""
        character.npc_relations.get_favor.return_value = 75  # >=50 但 <100
        
        know_node = DialogueNode(text="认识对话")
        default_node = DialogueNode(text="默认对话")
        
        dialogue_system.register_dialogue("test_npc", "know", know_node)
        dialogue_system.register_dialogue("test_npc", "default", default_node)
        
        result = await dialogue_system.start_dialogue(character, npc)
        
        assert result == know_node

    @pytest.mark.asyncio
    async def test_start_dialogue_first_available(self, dialogue_system, character, npc):
        """测试使用第一个可用节点（无default节点）."""
        character.npc_relations.get_favor.return_value = 0
        
        custom_node = DialogueNode(text="自定义对话")
        
        dialogue_system.register_dialogue("test_npc", "custom", custom_node)
        
        result = await dialogue_system.start_dialogue(character, npc)
        
        assert result == custom_node

    @pytest.mark.asyncio
    async def test_start_dialogue_no_dialogue(self, dialogue_system, character, npc):
        """测试无对话配置."""
        result = await dialogue_system.start_dialogue(character, npc)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_start_dialogue_condition_not_met(self, dialogue_system, character, npc):
        """测试条件不满足的对话."""
        node = DialogueNode(
            text="有条件对话",
            conditions={"min_level": 20}  # 要求20级
        )
        dialogue_system.register_dialogue("test_npc", "default", node)
        
        character.level = 10  # 只有10级
        
        result = await dialogue_system.start_dialogue(character, npc)
        
        assert result is None

    def test_get_available_responses_all(self, dialogue_system, character, npc):
        """测试获取所有可用回应选项."""
        responses = [
            Response("选项1"),
            Response("选项2"),
        ]
        node = DialogueNode(text="对话", responses=responses)
        
        available = dialogue_system.get_available_responses(character, npc, node)
        
        assert len(available) == 2
        assert available[0] == (0, responses[0])
        assert available[1] == (1, responses[1])

    def test_get_available_responses_with_condition(self, dialogue_system, character, npc):
        """测试条件过滤的回应选项."""
        responses = [
            Response("无条件选项"),
            Response("有条件选项", conditions={"min_level": 20}),
        ]
        node = DialogueNode(text="对话", responses=responses)
        
        character.level = 10
        
        available = dialogue_system.get_available_responses(character, npc, node)
        
        assert len(available) == 1
        assert available[0] == (0, responses[0])

    def test_get_available_responses_min_favor(self, dialogue_system, character, npc):
        """测试最小好感度条件."""
        responses = [
            Response("选项1", conditions={"min_favor": 50}),
        ]
        node = DialogueNode(text="对话", responses=responses)
        
        character.npc_relations.get_favor.return_value = 30  # 低于50
        
        available = dialogue_system.get_available_responses(character, npc, node)
        
        assert len(available) == 0

    def test_get_available_responses_max_favor(self, dialogue_system, character, npc):
        """测试最大好感度条件."""
        responses = [
            Response("选项1", conditions={"max_favor": 50}),
        ]
        node = DialogueNode(text="对话", responses=responses)
        
        character.npc_relations.get_favor.return_value = 80  # 高于50
        
        available = dialogue_system.get_available_responses(character, npc, node)
        
        assert len(available) == 0

    def test_get_available_responses_menpai(self, dialogue_system, character, npc):
        """测试门派条件."""
        responses = [
            Response("选项1", conditions={"menpai": "少林"}),
        ]
        node = DialogueNode(text="对话", responses=responses)
        
        character.menpai = "武当"
        
        available = dialogue_system.get_available_responses(character, npc, node)
        
        assert len(available) == 0

    def test_get_available_responses_quest_active(self, dialogue_system, character, npc):
        """测试活跃任务条件."""
        responses = [
            Response("选项1", conditions={"quest_active": "quest1"}),
        ]
        node = DialogueNode(text="对话", responses=responses)
        
        character.is_quest_active.return_value = False
        
        available = dialogue_system.get_available_responses(character, npc, node)
        
        assert len(available) == 0

    def test_get_available_responses_quest_completed(self, dialogue_system, character, npc):
        """测试已完成任务条件."""
        responses = [
            Response("选项1", conditions={"quest_completed": "quest1"}),
        ]
        node = DialogueNode(text="对话", responses=responses)
        
        character.is_quest_completed.return_value = False
        
        available = dialogue_system.get_available_responses(character, npc, node)
        
        assert len(available) == 0

    def test_get_available_responses_quest_completed_pass(self, dialogue_system, character, npc):
        """测试已完成任务条件通过."""
        responses = [
            Response("选项1", conditions={"quest_completed": "quest1"}),
        ]
        node = DialogueNode(text="对话", responses=responses)
        
        character.is_quest_completed.return_value = True
        
        available = dialogue_system.get_available_responses(character, npc, node)
        
        assert len(available) == 1

    def test_check_conditions_has_item(self, dialogue_system, character, npc):
        """测试拥有物品条件."""
        responses = [
            Response("选项1", conditions={"has_item": "item1"}),
        ]
        node = DialogueNode(text="对话", responses=responses)
        
        # 没有物品时应该不可用
        available = dialogue_system.get_available_responses(character, npc, node)
        assert len(available) == 0
        
        # 添加物品后应该可用
        item = Mock()
        item.key = "item1"
        character.contents = [item]
        available = dialogue_system.get_available_responses(character, npc, node)
        assert len(available) == 1

    @pytest.mark.asyncio
    async def test_select_response_next_node(self, dialogue_system, character, npc):
        """测试选择回应后进入下一个节点."""
        node1 = DialogueNode(
            text="节点1",
            responses=[Response("去节点2", next_node="node2")]
        )
        node2 = DialogueNode(text="节点2")
        
        dialogue_system.register_dialogue_tree("test_npc", {
            "node1": node1,
            "node2": node2
        })
        
        result = await dialogue_system.select_response(character, npc, node1, 0)
        
        assert result == node2

    @pytest.mark.asyncio
    async def test_select_response_no_next(self, dialogue_system, character, npc):
        """测试选择回应后无下一个节点."""
        node = DialogueNode(
            text="节点",
            responses=[Response("结束")]
        )
        
        result = await dialogue_system.select_response(character, npc, node, 0)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_select_response_invalid_index(self, dialogue_system, character, npc):
        """测试无效回应索引."""
        node = DialogueNode(text="节点", responses=[])
        
        result = await dialogue_system.select_response(character, npc, node, 0)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_select_response_favor_effect(self, dialogue_system, character, npc):
        """测试选择回应的好感度效果."""
        node = DialogueNode(
            text="节点",
            responses=[Response("选项", effects={"favor_delta": 10})]
        )
        
        await dialogue_system.select_response(character, npc, node, 0)
        
        character.npc_relations.modify_favor.assert_called_once_with(
            "test_npc", 10, ""
        )

    @pytest.mark.asyncio
    async def test_select_response_favor_effect_with_reason(self, dialogue_system, character, npc):
        """测试选择回应的好感度效果带原因."""
        node = DialogueNode(
            text="节点",
            responses=[Response("选项", effects={"favor_delta": 10, "favor_reason": "感谢帮助"})]
        )
        
        await dialogue_system.select_response(character, npc, node, 0)
        
        character.npc_relations.modify_favor.assert_called_once_with(
            "test_npc", 10, "感谢帮助"
        )

    @pytest.mark.asyncio
    async def test_select_response_next_node_condition_fail(self, dialogue_system, character, npc):
        """测试选择回应后下一个节点条件不满足."""
        node1 = DialogueNode(
            text="节点1",
            responses=[Response("去节点2", next_node="node2")]
        )
        # 节点2有条件要求，但角色不满足
        node2 = DialogueNode(
            text="节点2",
            conditions={"min_level": 50}  # 角色只有10级
        )
        
        dialogue_system.register_dialogue_tree("test_npc", {
            "node1": node1,
            "node2": node2
        })
        
        result = await dialogue_system.select_response(character, npc, node1, 0)
        
        # 条件不满足，返回None
        assert result is None

    @pytest.mark.asyncio
    async def test_select_response_no_next_node_in_dialogue(self, dialogue_system, character, npc):
        """测试选择回应后下一个节点不存在于对话系统中."""
        node1 = DialogueNode(
            text="节点1",
            responses=[Response("去不存在节点", next_node="nonexistent")]
        )
        
        dialogue_system.register_dialogue_tree("test_npc", {
            "node1": node1
        })
        
        result = await dialogue_system.select_response(character, npc, node1, 0)
        
        # 节点不存在，返回None
        assert result is None

    @pytest.mark.asyncio
    async def test_select_response_silver_effect(self, dialogue_system, character, npc):
        """测试选择回应的银两效果."""
        node = DialogueNode(
            text="节点",
            responses=[Response("选项", effects={"give_silver": 100})]
        )
        
        character.db = Mock()
        character.db.get = Mock(return_value=50)
        character.db.set = Mock()
        
        await dialogue_system.select_response(character, npc, node, 0)
        
        character.db.set.assert_called_with("silver", 150)

    @pytest.mark.asyncio
    async def test_select_response_exp_effect(self, dialogue_system, character, npc):
        """测试选择回应的经验效果."""
        node = DialogueNode(
            text="节点",
            responses=[Response("选项", effects={"give_exp": 50})]
        )
        
        await dialogue_system.select_response(character, npc, node, 0)
        
        character.add_exp.assert_called_once_with(50)

    @pytest.mark.asyncio
    async def test_select_response_exp_effect_async(self, dialogue_system, character, npc):
        """测试选择回应的异步经验效果."""
        node = DialogueNode(
            text="节点",
            responses=[Response("选项", effects={"give_exp": 50})]
        )
        
        # 设置异步add_exp
        async def async_add_exp(exp):
            pass
        character.add_exp = async_add_exp
        
        # 不应抛出异常
        await dialogue_system.select_response(character, npc, node, 0)

    @pytest.mark.asyncio
    async def test_select_response_give_item_effect(self, dialogue_system, character, npc):
        """测试选择回应的给予物品效果（当前实现为pass）."""
        node = DialogueNode(
            text="节点",
            responses=[Response("选项", effects={"give_item": "sword", "item_count": 2})]
        )
        
        # 当前实现为空pass，不应抛出异常
        await dialogue_system.select_response(character, npc, node, 0)

    @pytest.mark.asyncio
    async def test_select_response_unlock_quest_effect(self, dialogue_system, character, npc):
        """测试选择回应的解锁任务效果（当前实现为pass）."""
        node = DialogueNode(
            text="节点",
            responses=[Response("选项", effects={"unlock_quest": "quest1"})]
        )
        
        # 当前实现为空pass，不应抛出异常
        await dialogue_system.select_response(character, npc, node, 0)

    @pytest.mark.asyncio
    async def test_select_response_karma_effect(self, dialogue_system, character, npc):
        """测试选择回应的因果点效果."""
        node = DialogueNode(
            text="节点",
            responses=[Response("选项", effects={"karma": {"good": 10, "evil": -5}})]
        )
        
        with patch('src.game.quest.karma.KarmaSystem') as MockKarmaSystem:
            karma_sys = Mock()
            karma_sys.add_karma = Mock()
            MockKarmaSystem.return_value = karma_sys
            
            await dialogue_system.select_response(character, npc, node, 0)
            
            # 验证 KarmaSystem 被创建并调用了add_karma
            MockKarmaSystem.assert_called_once_with(character)
            karma_sys.add_karma.assert_any_call("good", 10)
            karma_sys.add_karma.assert_any_call("evil", -5)

    @pytest.mark.asyncio
    async def test_select_response_record_choice_effect(self, dialogue_system, character, npc):
        """测试选择回应的记录选择效果（当前实现为pass）."""
        node = DialogueNode(
            text="节点",
            responses=[Response("选项", effects={"record_choice": "choice1", "choice_value": "value1"})]
        )
        
        # 当前实现为空pass，不应抛出异常
        await dialogue_system.select_response(character, npc, node, 0)

    @pytest.mark.asyncio
    async def test_start_dialogue_with_async_on_enter(self, dialogue_system, character, npc):
        """测试开始对话时on_enter回调是协程的情况."""
        async_calls = []
        
        async def async_on_enter(char, npc_obj):
            async_calls.append("called")
        
        node = DialogueNode(
            text="对话",
            responses=[Response("选项")],
            on_enter=async_on_enter
        )
        dialogue_system.register_dialogue("test_npc", "default", node)
        
        result = await dialogue_system.start_dialogue(character, npc)
        
        assert result == node
        assert async_calls == ["called"]

    @pytest.mark.asyncio
    async def test_select_response_with_async_on_enter(self, dialogue_system, character, npc):
        """测试选择回应后下一节点on_enter是协程的情况."""
        async_calls = []
        
        async def async_on_enter(char, npc_obj):
            async_calls.append("called")
        
        node1 = DialogueNode(
            text="节点1",
            responses=[Response("去节点2", next_node="node2")]
        )
        node2 = DialogueNode(
            text="节点2",
            on_enter=async_on_enter
        )
        
        dialogue_system.register_dialogue_tree("test_npc", {
            "node1": node1,
            "node2": node2
        })
        
        result = await dialogue_system.select_response(character, npc, node1, 0)
        
        assert result == node2
        assert async_calls == ["called"]

    def test_check_conditions_empty(self, dialogue_system, character, npc):
        """测试空条件始终通过."""
        result = dialogue_system._check_conditions(character, npc, {})
        
        assert result is True

    def test_check_conditions_min_level_pass(self, dialogue_system, character, npc):
        """测试等级条件通过."""
        character.level = 20
        
        result = dialogue_system._check_conditions(character, npc, {"min_level": 10})
        
        assert result is True

    def test_check_conditions_min_level_fail(self, dialogue_system, character, npc):
        """测试等级条件失败."""
        character.level = 5
        
        result = dialogue_system._check_conditions(character, npc, {"min_level": 10})
        
        assert result is False

    def test_check_conditions_karma(self, dialogue_system, character, npc):
        """测试因果点条件."""
        # Mock KarmaSystem 来测试 karma 条件检查
        with patch('src.game.quest.karma.KarmaSystem') as MockKarmaSystem:
            karma_sys = Mock()
            karma_sys.check_single_requirement = Mock(return_value=True)
            MockKarmaSystem.return_value = karma_sys
            
            result = dialogue_system._check_conditions(
                character, npc, {"karma": {"good": ">=10"}}
            )
            
            # 验证 KarmaSystem 被创建并调用了检查方法
            MockKarmaSystem.assert_called_once_with(character)
            karma_sys.check_single_requirement.assert_called_once_with("good", ">=10")
            assert result is True

    def test_check_conditions_karma_fail(self, dialogue_system, character, npc):
        """测试因果点条件失败."""
        # Mock KarmaSystem 来测试 karma 条件检查失败的情况
        with patch('src.game.quest.karma.KarmaSystem') as MockKarmaSystem:
            karma_sys = Mock()
            karma_sys.check_single_requirement = Mock(return_value=False)
            MockKarmaSystem.return_value = karma_sys
            
            result = dialogue_system._check_conditions(
                character, npc, {"karma": {"evil": ">=10"}}
            )
            
            # 条件不满足，返回False
            assert result is False

    def test_format_dialogue(self, dialogue_system, character, npc):
        """测试对话格式化."""
        node = DialogueNode(
            text="NPC说的话",
            responses=[
                Response("回应1"),
                Response("回应2"),
            ]
        )
        
        formatted = dialogue_system.format_dialogue(character, npc, node)
        
        assert formatted["npc_name"] == npc.name
        assert formatted["text"] == "NPC说的话"
        assert len(formatted["responses"]) == 2
        assert formatted["responses"][0]["index"] == 0
        assert formatted["responses"][0]["text"] == "回应1"


class TestDialogueHelpers:
    """对话便捷函数测试."""

    def test_create_simple_dialogue(self):
        """测试创建简单对话."""
        from src.game.npc.dialogue import create_simple_dialogue
        
        node = create_simple_dialogue("NPC的话", ["选项1", "选项2"])
        
        assert node.text == "NPC的话"
        assert len(node.responses) == 2
        assert node.responses[0].text == "选项1"
        assert node.responses[1].text == "选项2"

    def test_create_trade_dialogue(self):
        """测试创建商人对话."""
        from src.game.npc.dialogue import create_trade_dialogue
        
        nodes = create_trade_dialogue("店主")
        
        assert "default" in nodes
        assert "shop" in nodes
        assert "sell" in nodes

    def test_create_quest_dialogue(self):
        """测试创建任务对话."""
        from src.game.npc.dialogue import create_quest_dialogue
        
        nodes = create_quest_dialogue("NPC", "寻找物品")
        
        assert "default" in nodes
        assert "quest_desc" in nodes
        assert "accept" in nodes
