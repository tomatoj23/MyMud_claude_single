"""跨阶段集成测试 - 简化版本.

测试场景：玩家创建角色 → 接受任务 → 与NPC对话 → 进入战斗 → 完成任务
"""
import asyncio
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from src.utils.config import Config
from src.engine.core import GameEngine
from src.game.typeclasses.character import Character
from src.game.npc.core import NPC, NPCType
from src.game.quest.core import (
    Quest, QuestObjective, QuestObjectiveType, QuestType, 
    CharacterQuestMixin, QuestObjective
)
from src.game.combat.core import CombatSession
from src.game.typeclasses.equipment import Equipment, EquipmentSlot


class TestPlayerJourneySimplified:
    """简化版玩家流程集成测试."""
    
    @pytest.mark.asyncio
    async def test_character_and_equipment_integration(self):
        """测试角色创建与装备系统集成."""
        # 创建临时引擎
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir) / 'test.db'}"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        try:
            # ========== 阶段1: 创建角色 ==========
            player = await engine.objects.create(
                "src.game.typeclasses.character.Character",
                key="player_test",
                attributes={"name": "测试侠客"}
            )
            
            # 设置属性
            player.level = 10
            player.menpai = "少林"
            player.attributes = {"strength": 15, "agility": 12, "constitution": 14, "spirit": 10}
            
            # 验证角色创建
            assert player is not None
            assert player.key == "player_test"
            assert player.level == 10
            assert player.attributes['strength'] == 15
            
            # ========== 阶段2: 装备系统 ==========
            sword = await engine.objects.create(
                "src.game.typeclasses.equipment.Equipment",
                key="iron_sword",
                attributes={"name": "铁剑"}
            )
            sword.slot = EquipmentSlot.MAIN_HAND
            sword.quality = 1
            sword.stats_bonus = {"attack": 20}
            
            # 将剑放入玩家背包（通过 location）
            sword.location = player
            
            # 装备武器
            result, msg = await player.equip(sword)
            assert result is True, f"装备失败: {msg}"
            
            # 验证装备成功
            equipped = player.get_equipped(EquipmentSlot.MAIN_HAND)
            assert equipped is not None
            assert equipped.key == "iron_sword"
            
            print("✅ 角色与装备集成测试通过！")
            
        finally:
            await engine.stop()
    
    @pytest.mark.asyncio
    async def test_quest_system_standalone(self):
        """测试任务系统独立功能."""
        # 创建模拟角色
        character = Mock()
        character._active_quests = {}
        character._completed_quests = []
        character.db = MagicMock()
        character.db.get = MagicMock(side_effect=lambda key, default=None: 
            character._active_quests if key == "active_quests" else
            character._completed_quests if key == "completed_quests" else default)
        character.db.set = MagicMock(side_effect=lambda key, value: 
            character._active_quests.__setitem__(key, value) if key == "active_quests" else None)
        character.level = 10
        character.menpai = "少林"
        
        # 手动添加 CharacterQuestMixin 方法
        mixin = CharacterQuestMixin()
        mixin.__dict__['db'] = character.db
        
        # 创建任务
        quest = Quest(
            key="kill_wolves",
            name="除狼任务",
            description="帮助村民除掉3只野狼",
            quest_type=QuestType.MAIN,
            objectives=[
                QuestObjective(QuestObjectiveType.KILL, "wolf", count=3)
            ],
            rewards={"exp": 100}
        )
        
        # 测试任务接受条件
        can_accept, msg = quest.can_accept(mixin)
        assert can_accept is True
        
        print("✅ 任务系统测试通过！")
    
    @pytest.mark.asyncio
    async def test_npc_system_standalone(self):
        """测试NPC系统独立功能."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir) / 'test.db'}"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        try:
            # 创建商人NPC
            merchant = await engine.objects.create(
                "src.game.npc.core.NPC",
                key="shopkeeper",
                attributes={"name": "掌柜"}
            )
            merchant.npc_type = NPCType.MERCHANT
            
            # 验证商人属性
            assert merchant.is_merchant is True
            assert merchant.can_trade() is True
            
            # 创建训练师NPC
            trainer = await engine.objects.create(
                "src.game.npc.core.NPC",
                key="master",
                attributes={"name": "师父"}
            )
            trainer.npc_type = NPCType.TRAINER
            
            # 验证训练师属性
            assert trainer.is_trainer is True
            assert trainer.can_train() is True
            
            # 创建任务NPC
            quest_npc = await engine.objects.create(
                "src.game.npc.core.NPC",
                key="quest_giver",
                attributes={"name": "任务发布人"}
            )
            quest_npc.npc_type = NPCType.QUEST
            
            # 验证任务NPC属性
            assert quest_npc.is_quest_giver is True
            
            print("✅ NPC系统测试通过！")
            
        finally:
            await engine.stop()
    
    @pytest.mark.asyncio
    async def test_combat_system_standalone(self):
        """测试战斗系统独立功能（简化版）."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir) / 'test.db'}"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        try:
            # 创建真实玩家
            player = await engine.objects.create(
                "src.game.typeclasses.character.Character",
                key="player_combat",
                attributes={"name": "战斗测试玩家"}
            )
            player.attributes = {"strength": 20, "agility": 15, "constitution": 18, "spirit": 12}
            
            # 创建敌人NPC
            enemy = await engine.objects.create(
                "src.game.npc.core.NPC",
                key="wolf",
                attributes={"name": "野狼"}
            )
            enemy.npc_type = NPCType.ENEMY
            enemy.is_hostile = True
            
            # 创建战斗会话（不启动战斗循环，只测试初始化）
            combat = CombatSession(engine, [player, enemy], player_character=player)
            
            # 验证参与者已添加
            assert player.id in combat.participants
            assert enemy.id in combat.participants
            assert combat.participants[player.id].is_player is True
            assert combat.participants[enemy.id].is_player is False
            
            print("✅ 战斗系统测试通过！")
            
        finally:
            await engine.stop()
    
    @pytest.mark.asyncio
    async def test_reputation_system_standalone(self):
        """测试声望/好感度系统."""
        from src.game.npc.reputation import NPCRelationship
        
        # 创建模拟角色
        character = Mock()
        character._npc_relations = {}
        character.db = MagicMock()
        character.db.get = MagicMock(return_value={})
        character.db.set = MagicMock()
        
        # 创建关系管理器
        relations = NPCRelationship(character)
        
        # 修改好感度
        relations.modify_favor("npc_1", 20, "帮助任务")
        relations.modify_favor("npc_1", 30, "赠送礼物")
        
        # 验证好感度
        favor = relations.get_favor("npc_1")
        assert favor == 50
        
        # 验证关系等级
        level = relations.get_relationship_level("npc_1")
        assert level == "友善"
        
        # 测试友好检查
        assert relations.is_friendly("npc_1") is True
        assert relations.can_learn("npc_1") is True
        
        print("✅ 声望系统测试通过！")
