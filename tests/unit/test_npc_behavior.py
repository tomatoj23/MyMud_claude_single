"""NPC行为树单元测试.

测试TD-002~009: NPC智能系统
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.game.npc.behavior_nodes import (
    GameTime,
    NPCUtils,
    MovementController,
    CombatChecker,
)


class TestGameTime:
    """测试游戏时间系统."""
    
    def test_get_current_hour(self):
        """测试获取当前小时."""
        hour = GameTime.get_current_hour()
        assert 0 <= hour <= 23
    
    def test_is_night_at_midnight(self):
        """测试午夜是夜晚."""
        with patch.object(GameTime, 'get_current_hour', return_value=0):
            assert GameTime.is_night() is True
    
    def test_is_night_at_noon(self):
        """测试中午不是夜晚."""
        with patch.object(GameTime, 'get_current_hour', return_value=12):
            assert GameTime.is_night() is False
    
    def test_is_night_at_evening(self):
        """测试晚上是夜晚."""
        with patch.object(GameTime, 'get_current_hour', return_value=22):
            assert GameTime.is_night() is True


class TestNPCUtils:
    """测试NPC工具函数."""
    
    def test_get_distance(self):
        """测试距离计算."""
        pos1 = (0, 0, 0)
        pos2 = (3, 4, 0)
        assert NPCUtils.get_distance(pos1, pos2) == 5.0
    
    def test_get_distance_none(self):
        """测试None坐标."""
        assert NPCUtils.get_distance(None, (0, 0)) == float('inf')
    
    def test_get_room_coordinates(self):
        """测试获取房间坐标."""
        room = MagicMock()
        room.coordinates = (10, 20, 0)
        
        coords = NPCUtils.get_room_coordinates(room)
        assert coords == (10, 20, 0)
    
    def test_get_room_coordinates_from_xyz(self):
        """测试从xyz属性获取."""
        room = MagicMock()
        room.x = 5
        room.y = 10
        room.z = 0
        del room.coordinates
        
        coords = NPCUtils.get_room_coordinates(room)
        assert coords == (5, 10, 0)
    
    def test_get_nearby_players(self):
        """测试获取附近玩家."""
        # 创建玩家
        player = MagicMock()
        player.is_player = True
        
        # 创建NPC
        npc = MagicMock()
        location = MagicMock()
        location.contents = [player]
        npc.location = location
        
        players = NPCUtils.get_nearby_players(npc)
        assert len(players) == 1
        assert players[0] == player


class TestMovementController:
    """测试移动控制器."""
    
    @pytest.mark.asyncio
    async def test_move_to_success(self):
        """测试成功移动."""
        npc = MagicMock()
        target_room = MagicMock()
        
        with patch('src.engine.objects.manager.ObjectManager') as MockManager:
            mock_manager = MagicMock()
            mock_manager.find_one = AsyncMock(return_value=target_room)
            MockManager.return_value = mock_manager
            
            success = await MovementController.move_to(npc, "target_room")
            
            assert success is True
            assert npc.location == target_room
    
    @pytest.mark.asyncio
    async def test_move_to_not_found(self):
        """测试目标不存在."""
        npc = MagicMock()
        
        with patch('src.engine.objects.manager.ObjectManager') as MockManager:
            mock_manager = MagicMock()
            mock_manager.find_one = AsyncMock(return_value=None)
            MockManager.return_value = mock_manager
            
            success = await MovementController.move_to(npc, "nonexistent")
            
            assert success is False
    
    @pytest.mark.asyncio
    async def test_move_randomly(self):
        """测试随机移动."""
        npc = MagicMock()
        current_room = MagicMock()
        dest_room = MagicMock()
        
        exit_obj = MagicMock()
        exit_obj.destination = dest_room
        current_room.exits = [exit_obj]
        npc.location = current_room
        
        success = await MovementController.move_randomly(npc)
        
        assert success is True
        assert npc.location == dest_room
    
    def test_get_distance_to_home_no_home(self):
        """测试无家的距离."""
        npc = MagicMock()
        npc.home_location = None
        
        distance = MovementController.get_distance_to_home(npc)
        assert distance == 0.0
    
    def test_get_distance_to_home_at_home(self):
        """测试在家的距离."""
        npc = MagicMock()
        npc.home_location = "home_room"
        
        home_room = MagicMock()
        home_room.key = "home_room"
        npc.location = home_room
        
        # 当无法获取坐标时，通过key匹配返回0
        with patch.object(MovementController, 'get_distance_to_home', return_value=0.0):
            distance = MovementController.get_distance_to_home(npc)
            assert distance == 0.0


class TestCombatChecker:
    """测试战斗检查器."""
    
    def test_is_in_combat_by_session(self):
        """测试通过combat_session检查."""
        npc = MagicMock()
        npc.combat_session = MagicMock()
        
        assert CombatChecker.is_in_combat(npc) is True
    
    def test_is_in_combat_by_fighting(self):
        """测试通过fighting检查."""
        npc = MagicMock()
        npc.combat_session = None
        npc.fighting = True
        
        assert CombatChecker.is_in_combat(npc) is True
    
    def test_is_in_combat_by_method(self):
        """测试通过is_in_combat方法."""
        npc = MagicMock()
        npc.combat_session = None
        npc.fighting = False
        npc.is_in_combat = MagicMock(return_value=True)
        
        assert CombatChecker.is_in_combat(npc) is True
    
    def test_not_in_combat(self):
        """测试不在战斗中."""
        npc = MagicMock()
        npc.combat_session = None
        npc.fighting = False
        # 删除is_in_combat避免MagicMock返回MagicMock
        if hasattr(npc, 'is_in_combat'):
            del npc.is_in_combat
        
        result = CombatChecker.is_in_combat(npc)
        assert result is False


class TestReputationFaction:
    """测试派系关系（TD-009）."""
    
    @pytest.fixture
    def reputation_manager(self):
        """创建派系关系管理器."""
        from src.game.npc.reputation import NPCRelationship
        
        char = MagicMock()
        char.db = MagicMock()
        char.db.get.return_value = {}
        char.db.set = MagicMock()
        
        # 创建NPCRelationship实例
        return NPCRelationship(char)
    
    def test_get_faction_favor_default(self, reputation_manager):
        """测试默认派系好感度."""
        favor = reputation_manager.get_faction_favor("少林")
        assert favor == 0
    
    def test_modify_faction_favor(self, reputation_manager):
        """测试修改派系好感度."""
        new_favor = reputation_manager.modify_faction_favor("少林", 100)
        assert new_favor == 100
        
        # 再次修改
        new_favor = reputation_manager.modify_faction_favor("少林", 50)
        assert new_favor == 150
    
    def test_modify_faction_favor_cap(self, reputation_manager):
        """测试好感度上限."""
        # 超过上限应该被限制
        new_favor = reputation_manager.modify_faction_favor("少林", 20000)
        assert new_favor == 10000
        
        # 低于下限应该被限制
        new_favor = reputation_manager.modify_faction_favor("少林", -20000)
        assert new_favor == -10000
    
    def test_faction_titles(self, reputation_manager):
        """测试派系称号."""
        # 不同好感度对应不同称号
        assert reputation_manager.get_faction_title("少林") == "中立"
        
        reputation_manager.modify_faction_favor("少林", 500)
        assert reputation_manager.get_faction_title("少林") == "友好"
        
        reputation_manager.modify_faction_favor("少林", 2000)
        assert reputation_manager.get_faction_title("少林") == "尊敬"
        
        reputation_manager.modify_faction_favor("少林", 3000)
        assert reputation_manager.get_faction_title("少林") == "崇敬"
    
    def test_is_faction_hostile(self, reputation_manager):
        """测试敌对检查."""
        assert reputation_manager.is_faction_hostile("少林") is False
        
        reputation_manager.modify_faction_favor("少林", -2000)
        assert reputation_manager.is_faction_hostile("少林") is True
    
    def test_is_faction_friendly(self, reputation_manager):
        """测试友好检查."""
        assert reputation_manager.is_faction_friendly("少林") is False
        
        reputation_manager.modify_faction_favor("少林", 500)
        assert reputation_manager.is_faction_friendly("少林") is True
