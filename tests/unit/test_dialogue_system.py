"""对话系统单元测试.

测试TD-010~013: 对话系统功能
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.game.npc.dialogue import DialogueSystem, Response, DialogueNode


class TestDialogueConditions:
    """测试对话条件 (TD-010)."""
    
    @pytest.fixture
    def dialogue_system(self):
        """创建对话系统."""
        return DialogueSystem()
    
    @pytest.fixture
    def mock_character(self):
        """创建模拟角色."""
        char = MagicMock()
        char.contents = []
        char.db = MagicMock()
        char.db.get.return_value = []
        return char
    
    @pytest.fixture
    def mock_npc(self):
        """创建模拟NPC."""
        npc = MagicMock()
        npc.key = "test_npc"
        npc.name = "测试NPC"
        return mock_npc
    
    def test_check_inventory_empty(self, dialogue_system, mock_character):
        """测试空背包检查."""
        mock_character.contents = []
        
        result = dialogue_system._check_inventory(mock_character, "sword", 1)
        assert result is False
    
    def test_check_inventory_has_item(self, dialogue_system, mock_character):
        """测试有物品."""
        item = MagicMock()
        item.key = "sword"
        mock_character.contents = [item]
        
        result = dialogue_system._check_inventory(mock_character, "sword", 1)
        assert result is True
    
    def test_check_inventory_quantity(self, dialogue_system, mock_character):
        """测试数量检查."""
        item1 = MagicMock()
        item1.key = "potion"
        item2 = MagicMock()
        item2.key = "potion"
        mock_character.contents = [item1, item2]
        
        result = dialogue_system._check_inventory(mock_character, "potion", 2)
        assert result is True
        
        result = dialogue_system._check_inventory(mock_character, "potion", 3)
        assert result is False


class TestDialogueEffects:
    """测试对话效果 (TD-011~013)."""
    
    @pytest.fixture
    def dialogue_system(self):
        """创建对话系统."""
        return DialogueSystem()
    
    @pytest.fixture
    def mock_character(self):
        """创建模拟角色."""
        char = MagicMock()
        char.contents = []
        char.db = MagicMock()
        char.db.get.return_value = {}
        char.db.set = MagicMock()
        return char
    
    @pytest.fixture
    def mock_npc(self):
        """创建模拟NPC."""
        npc = MagicMock()
        npc.key = "test_npc"
        return npc
    
    @pytest.mark.asyncio
    async def test_give_item(self, dialogue_system, mock_character):
        """测试给予物品 (TD-011)."""
        with patch('src.engine.objects.manager.ObjectManager') as MockManager:
            mock_manager = MagicMock()
            mock_manager.create = AsyncMock(return_value=MagicMock())
            MockManager.return_value = mock_manager
            
            result = await dialogue_system._give_item_to_character(
                mock_character, "sword", 1
            )
            
            assert result is True
            mock_manager.create.assert_called_once()
    
    def test_unlock_quest(self, dialogue_system, mock_character):
        """测试解锁任务 (TD-012)."""
        # 测试使用unlock_quest方法
        mock_character.unlock_quest = MagicMock()
        
        result = dialogue_system._unlock_quest_for_character(
            mock_character, "test_quest"
        )
        
        assert result is True
        mock_character.unlock_quest.assert_called_once_with("test_quest")
    
    def test_unlock_quest_fallback(self, dialogue_system, mock_character):
        """测试解锁任务回退."""
        # 创建没有unlock_quest的角色
        char = MagicMock()
        char.db = MagicMock()
        char.db.get.return_value = []
        char.db.set = MagicMock()
        # 确保没有unlock_quest
        if hasattr(char, 'unlock_quest'):
            delattr(char, 'unlock_quest')
        
        result = dialogue_system._unlock_quest_for_character(
            char, "test_quest"
        )
        
        assert result is True
        # 验证添加到available_quests
        char.db.set.assert_called()
    
    def test_record_world_state(self, dialogue_system, mock_character):
        """测试记录世界状态 (TD-013)."""
        dialogue_system._record_world_state(
            mock_character, "choice_1", "option_a"
        )
        
        # 验证db.set被调用
        mock_character.db.set.assert_called_once()
        call_args = mock_character.db.set.call_args
        assert call_args[0][0] == "world_state"
        
        world_state = call_args[0][1]
        assert "choices" in world_state
        assert "choice_1" in world_state["choices"]
        assert world_state["choices"]["choice_1"]["value"] == "option_a"


class TestDialogueIntegration:
    """测试对话系统集成."""
    
    @pytest.fixture
    def dialogue_system(self):
        """创建对话系统."""
        return DialogueSystem()
    
    @pytest.fixture
    def mock_character(self):
        """创建模拟角色."""
        char = MagicMock()
        char.contents = []
        char.db = MagicMock()
        char.db.get.return_value = {}
        char.db.set = MagicMock()
        char.npc_relations = MagicMock()
        char.is_quest_active = MagicMock(return_value=True)
        char.is_quest_completed = MagicMock(return_value=False)
        return char
    
    @pytest.fixture
    def mock_npc(self):
        """创建模拟NPC."""
        npc = MagicMock()
        npc.key = "test_npc"
        npc.name = "测试NPC"
        return npc
    
    def test_check_conditions_item(self, dialogue_system, mock_character, mock_npc):
        """测试物品条件检查集成."""
        item = MagicMock()
        item.key = "golden_key"
        mock_character.contents = [item]
        
        conditions = {"has_item": {"key": "golden_key", "quantity": 1}}
        result = dialogue_system._check_conditions(mock_character, mock_npc, conditions)
        
        assert result is True
    
    def test_check_conditions_item_not_enough(self, dialogue_system, mock_character, mock_npc):
        """测试物品不足."""
        mock_character.contents = []
        
        conditions = {"has_item": {"key": "golden_key", "quantity": 1}}
        result = dialogue_system._check_conditions(mock_character, mock_npc, conditions)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_apply_effects_give_item(self, dialogue_system, mock_character, mock_npc):
        """测试应用物品效果."""
        with patch.object(dialogue_system, '_give_item_to_character', new_callable=AsyncMock) as mock_give:
            effects = {"give_item": "sword", "item_count": 1}
            await dialogue_system._apply_effects(mock_character, mock_npc, effects)
            
            mock_give.assert_called_once_with(mock_character, "sword", 1)
    
    @pytest.mark.asyncio
    async def test_apply_effects_unlock_quest(self, dialogue_system, mock_character, mock_npc):
        """测试应用解锁任务效果."""
        with patch.object(dialogue_system, '_unlock_quest_for_character') as mock_unlock:
            effects = {"unlock_quest": "new_quest"}
            await dialogue_system._apply_effects(mock_character, mock_npc, effects)
            
            mock_unlock.assert_called_once_with(mock_character, "new_quest")
    
    @pytest.mark.asyncio
    async def test_apply_effects_record_choice(self, dialogue_system, mock_character, mock_npc):
        """测试应用记录选择效果."""
        with patch.object(dialogue_system, '_record_world_state') as mock_record:
            effects = {"record_choice": "choice_1", "choice_value": "a"}
            await dialogue_system._apply_effects(mock_character, mock_npc, effects)
            
            mock_record.assert_called_once_with(mock_character, "choice_1", "a")
