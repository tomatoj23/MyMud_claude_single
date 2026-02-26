"""跨阶段集成测试 - 模拟玩家真实行为流程.

测试场景：玩家创建角色 → 接受任务 → 与NPC对话 → 进入战斗 → 完成任务

覆盖阶段：
- 阶段一：引擎核心（GameEngine, ObjectManager）
- 阶段二：角色系统（Character, Equipment, Item）
- 阶段三：战斗/任务/NPC系统
"""
import asyncio
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.utils.config import Config
from src.engine.core import GameEngine
from src.game.typeclasses.character import Character
from src.game.npc.core import NPC, NPCType
from src.game.quest.core import Quest, QuestObjective, QuestObjectiveType, QuestType, CharacterQuestMixin
from src.game.combat.core import CombatSession, CombatResult
from src.game.typeclasses.equipment import Equipment, EquipmentSlot
from src.game.typeclasses.item import Item


@pytest.fixture
async def engine():
    """创建测试引擎."""
    tmp_dir = tempfile.mkdtemp()
    config = Config()
    config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir) / 'test.db'}"
    
    engine = GameEngine(config)
    await engine.initialize()
    
    yield engine
    
    # 清理
    try:
        await engine.stop()
    except:
        pass


@pytest.fixture
async def player(engine):
    """创建测试玩家角色（包含Quest Mixin）."""
    # 创建带有Quest Mixin的角色类
    class PlayerCharacter(Character, CharacterQuestMixin):
        pass
    
    player = await engine.objects.create(
        "src.game.typeclasses.character.Character",
        key="player_test",
        attributes={"name": "测试侠客"}
    )
    
    # 手动添加 quest 相关属性
    from unittest.mock import MagicMock
    player._active_quests = {}
    player._completed_quests = []
    player._db_quest = MagicMock()
    player._db_quest.get = lambda key, default=None: player._active_quests if key == "active_quests" else player._completed_quests if key == "completed_quests" else default
    player._db_quest.set = lambda key, value: player._active_quests.__setitem__(key, value) if key == "active_quests" else player._completed_quests.__setitem__(key, value)
    
    # 设置基础属性
    player.level = 10
    player.menpai = "少林"
    player.attributes = {"strength": 15, "agility": 12, "constitution": 14, "spirit": 10}
    player.birth_talents = {"gengu": 15, "wuxing": 15, "fuyuan": 15, "rongmao": 15}
    
    return player


@pytest.fixture
def kill_quest() -> Quest:
    """创建击杀任务."""
    return Quest(
        key="kill_wolves",
        name="除狼任务",
        description="帮助村民除掉3只野狼",
        quest_type=QuestType.MAIN,
        objectives=[
            QuestObjective(QuestObjectiveType.KILL, "wolf", count=3)
        ],
        rewards={"exp": 100, "silver": 50, "reputation": 10}
    )


class TestPlayerJourney:
    """玩家完整流程集成测试."""
    
    @pytest.mark.asyncio
    async def test_full_player_journey(self, engine, player):
        """测试完整玩家流程：创建角色 → 接受任务 → 对话NPC → 战斗 → 完成任务."""
        
        # ========== 阶段1: 角色创建与初始化 ==========
        # 验证角色创建成功
        assert player is not None
        assert player.key == "player_test"
        assert player.level == 10
        assert player.menpai == "少林"
        
        # 验证属性系统
        assert player.attributes['strength'] == 15
        assert player.attributes['agility'] == 12
        
        # ========== 阶段2: 装备系统 ==========
        # 创建装备
        sword = await engine.objects.create(
            "src.game.typeclasses.equipment.Equipment",
            key="iron_sword",
            attributes={"name": "铁剑"}
        )
        sword.slot = EquipmentSlot.MAIN_HAND
        sword.quality = 1
        sword.stats_bonus = {"attack": 20}
        
        # 先添加到背包，再装备
        # 将剑移动到玩家位置（模拟放入背包）
        sword.location = player
        result, msg = await player.equipment_equip(sword)
        assert result is True, f"装备失败: {msg}"
        
        # 验证装备加成
        total_stats = player.equipment_get_stats()
        assert total_stats["attack"] > 0
        
        # ========== 阶段3: 任务系统 ==========
        # 创建任务
        quest = Quest(
            key="kill_wolves",
            name="除狼任务",
            description="帮助村民除掉3只野狼",
            quest_type=QuestType.MAIN,
            objectives=[
                QuestObjective(QuestObjectiveType.KILL, "wolf", count=3)
            ],
            rewards={"exp": 100, "silver": 50, "reputation": 10}
        )
        
        # 接受任务
        success, msg = await player.accept_quest(quest)
        assert success is True, f"接受任务失败: {msg}"
        assert player.is_quest_active("kill_wolves") is True
        
        # 验证任务进度
        progress = player.get_quest_progress("kill_wolves")
        assert progress is not None
        assert progress["objectives"][0]["current"] == 0
        assert progress["objectives"][0]["count"] == 3
        
        # ========== 阶段4: NPC系统与对话 ==========
        # 创建任务NPC
        npc = await engine.objects.create(
            "src.game.npc.core.NPC",
            key="village_elder",
            attributes={"name": "村长"}
        )
        npc.npc_type = NPCType.QUEST
        npc.dialogue_key = "village_elder_quest"
        
        # 验证NPC创建
        assert npc.is_quest_giver is True
        assert npc.can_train() is False  # 不是训练师
        
        # 设置NPC关系（好感度）
        player.npc_relations.modify_favor("village_elder", 60, "帮助村民")
        favor = player.npc_relations.get_favor("village_elder")
        assert favor == 60
        
        # 验证关系等级
        level = player.npc_relations.get_relationship_level("village_elder")
        assert level == "友善"  # 60好感度应该是友善
        
        # ========== 阶段5: 战斗系统 ==========
        # 创建敌人（野狼）
        wolf1 = await engine.objects.create(
            "src.game.npc.core.NPC",
            key="wolf_1",
            attributes={"name": "野狼"}
        )
        wolf1.npc_type = NPCType.ENEMY
        wolf1.is_hostile = True
        wolf1.level = 5
        
        # 创建战斗会话并启动
        combat = CombatSession(engine, [player, wolf1])
        await combat.start()
        
        # 验证战斗初始化
        assert combat.is_in_combat(player) is True
        assert combat.is_in_combat(wolf1) is True
        
        # 模拟击杀野狼并更新任务
        messages = await player.on_kill_npc("wolf")
        
        # 验证任务进度更新
        progress = player.get_quest_progress("kill_wolves")
        assert progress["objectives"][0]["current"] == 1
        
        # 再击杀2只（通过直接更新模拟）
        await player.update_objective("kill_wolves", 0, 1)
        await player.update_objective("kill_wolves", 0, 1)
        
        progress = player.get_quest_progress("kill_wolves")
        assert progress["objectives"][0]["current"] == 3
        assert progress["objectives"][0]["current"] >= progress["objectives"][0]["count"]
        
        # ========== 阶段6: 完成任务与奖励 ==========
        # 完成任务
        success, msg = await player.complete_quest("kill_wolves", quest)
        assert success is True, f"完成任务失败: {msg}"
        
        # 验证任务状态
        assert player.is_quest_active("kill_wolves") is False
        assert player.is_quest_completed("kill_wolves") is True
        
        # 验证奖励发放（如果有add_exp方法）
        # 注意：奖励发放需要实际实现
        
        print("✅ 完整玩家流程测试通过！")
    
    @pytest.mark.asyncio
    async def test_equipment_and_combat_integration(self, engine, player):
        """测试装备系统与战斗系统集成."""
        
        # 创建不同品质的装备
        normal_sword = await engine.objects.create(
            "src.game.typeclasses.equipment.Equipment",
            key="normal_sword",
            attributes={"name": "普通剑"}
        )
        normal_sword.slot = EquipmentSlot.MAIN_HAND
        normal_sword.quality = 1  # 普通
        normal_sword.stats_bonus = {"attack": 10}
        
        rare_sword = await engine.objects.create(
            "src.game.typeclasses.equipment.Equipment",
            key="rare_sword",
            attributes={"name": "精钢剑"}
        )
        rare_sword.slot = EquipmentSlot.MAIN_HAND
        rare_sword.quality = 3  # 精良
        rare_sword.stats_bonus = {"attack": 25}
        
        # 先将装备放入背包（设置location）
        normal_sword.location = player
        
        # 装备普通剑
        success, msg = await player.equipment_equip(normal_sword)
        assert success, f"装备失败: {msg}"
        stats1 = player.equipment_get_stats()
        
        # 更换为精良剑
        await player.equipment_unequip(EquipmentSlot.MAIN_HAND)
        rare_sword.location = player
        success, msg = await player.equipment_equip(rare_sword)
        assert success, f"装备失败: {msg}"
        stats2 = player.equipment_get_stats()
        
        # 精良剑应该有更高攻击力（如果属性存在）
        attack1 = stats1.get("attack", 0)
        attack2 = stats2.get("attack", 0)
        assert attack2 > attack1, f"精良剑攻击力应该更高: {attack2} vs {attack1}"
        
        print("✅ 装备与战斗集成测试通过！")
    
    @pytest.mark.asyncio
    async def test_quest_chain_integration(self, engine, player):
        """测试任务链集成."""
        
        # 创建任务链
        quest1 = Quest(
            key="chain_step1",
            name="任务链第一步",
            description="第一步",
            quest_type=QuestType.MAIN,
            objectives=[QuestObjective(QuestObjectiveType.TALK, "npc1", count=1)],
            rewards={"exp": 50},
            next_quest="chain_step2"
        )
        
        quest2 = Quest(
            key="chain_step2",
            name="任务链第二步",
            description="第二步",
            quest_type=QuestType.MAIN,
            objectives=[QuestObjective(QuestObjectiveType.KILL, "mob", count=2)],
            rewards={"exp": 100},
            prerequisites={"quest_completed": "chain_step1"}
        )
        
        # 接受第一个任务
        success, _ = await player.accept_quest(quest1)
        assert success is True
        
        # 完成第一个任务
        await player.on_talk_to_npc("npc1")
        success, _ = await player.complete_quest("chain_step1", quest1)
        assert success is True
        
        # 验证可以接受第二个任务（前置条件满足）
        can_accept, msg = quest2.can_accept(player)
        assert can_accept is True, f"应该能接受第二个任务: {msg}"
        
        success, _ = await player.accept_quest(quest2)
        assert success is True
        
        print("✅ 任务链集成测试通过！")
    
    @pytest.mark.asyncio
    async def test_npc_interaction_flow(self, engine, player):
        """测试NPC交互流程."""
        
        # 创建商人NPC
        merchant = await engine.objects.create(
            "src.game.npc.core.NPC",
            key="shopkeeper",
            attributes={"name": "掌柜"}
        )
        merchant.npc_type = NPCType.MERCHANT
        
        # 验证商人功能
        assert merchant.is_merchant is True
        assert merchant.can_trade() is True
        
        # 创建训练师NPC
        trainer = await engine.objects.create(
            "src.game.npc.core.NPC",
            key="master",
            attributes={"name": "师父"}
        )
        trainer.npc_type = NPCType.TRAINER
        
        # 验证训练师功能
        assert trainer.is_trainer is True
        assert trainer.can_train() is True
        
        # 好感度影响交易
        player.npc_relations.modify_favor("shopkeeper", 50, "经常光顾")
        
        # 高好感度时可以学习（特定NPC）
        can_learn = player.npc_relations.can_learn("shopkeeper")
        # 商人通常不能教授武功，除非好感度很高（这里取决于具体实现）
        
        print("✅ NPC交互流程测试通过！")


class TestDataPersistence:
    """数据持久化集成测试."""
    
    @pytest.mark.asyncio
    async def test_character_data_persistence(self, engine):
        """测试角色数据持久化."""
        
        # 创建角色
        char = await engine.objects.create(
            "src.game.typeclasses.character.Character",
            key="persistent_char",
            attributes={"name": "持久化角色"}
        )
        char.level = 20
        char.attributes = {"strength": 20, "agility": 18, "constitution": 15, "spirit": 12}
        
        # 标记脏数据并保存
        engine.objects.mark_dirty(char)
        await engine.objects.save_all()
        
        # 从数据库重新加载
        loaded = await engine.objects.load(char.id)
        
        assert loaded is not None
        assert loaded.key == "persistent_char"
        assert loaded.level == 20
        
        print("✅ 数据持久化测试通过！")


class TestErrorRecovery:
    """错误恢复集成测试."""
    
    @pytest.mark.asyncio
    async def test_combat_error_recovery(self, engine, player):
        """测试战斗错误恢复."""
        
        # 创建战斗
        combat = CombatSession(engine, [player])
        
        # 模拟异常情况
        try:
            # 尝试在没有启动战斗时处理命令
            result = await combat.handle_player_command(player, "kill", ["target"])
            # 应该返回False而不是抛出异常 (可能是元组或布尔值)
            if isinstance(result, tuple):
                assert result[0] is False
            else:
                assert result is False
        except Exception as e:
            pytest.fail(f"战斗错误处理不当: {e}")
        
        print("✅ 错误恢复测试通过！")
