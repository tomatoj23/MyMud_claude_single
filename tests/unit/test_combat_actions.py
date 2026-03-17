"""战斗系统单元测试 - 战斗动作.

测试战斗动作处理：攻击、施法、逃跑、防御等.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.game.combat.core import CombatAction, Combatant, CombatResult, CombatSession

class TestHandlePlayerCommand:
    """测试玩家命令处理 handle_player_command (217-237)."""

    @pytest.fixture
    def mock_engine(self):
        return Mock()

    @pytest.fixture
    def player_char(self):
        char = Mock()
        char.id = 1
        char.name = "玩家"
        char.get_hp.return_value = (100, 100)
        return char

    @pytest.fixture
    def enemy_char(self):
        char = Mock()
        char.id = 2
        char.name = "敌人"
        char.get_hp.return_value = (80, 80)
        return char

    @pytest.mark.asyncio
    async def test_handle_command_not_in_combat(self, mock_engine, player_char, enemy_char):
        """测试处理不在战斗中的角色的命令 (220-221)."""
        session = CombatSession(mock_engine, [player_char, enemy_char])
        # participant 不在战斗中
        session.participants[1].in_combat = False
        
        success, msg = await session.handle_player_command(player_char, "kill", {})
        
        assert success is False
        assert "你不在战斗中" in msg

    @pytest.mark.asyncio
    async def test_handle_command_not_ready(self, mock_engine, player_char, enemy_char):
        """测试处理未准备好的角色的命令 (223-225)."""
        session = CombatSession(mock_engine, [player_char, enemy_char])
        session.participants[1].in_combat = True
        # 设置冷却
        session.participants[1].next_action_time = time.time() + 100
        
        success, msg = await session.handle_player_command(player_char, "kill", {})
        
        assert success is False
        assert "你还不能行动" in msg

    @pytest.mark.asyncio
    async def test_handle_command_kill(self, mock_engine, player_char, enemy_char):
        """测试处理 kill 命令 (228-229) - 使用策略模式."""
        from src.game.combat.core import _get_strategies
        
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        session.participants[1].in_combat = True
        session.participants[1].next_action_time = 0
        
        # Mock策略 - validate不是异步的，返回普通值
        mock_strategy = MagicMock()
        mock_strategy.validate.return_value = (True, "")
        mock_strategy.execute = AsyncMock(return_value=MagicMock(success=True, message="攻击成功"))
        
        with patch.dict(_get_strategies(), {"kill": mock_strategy}, clear=False):
            success, msg = await session.handle_player_command(player_char, "kill", {"target": enemy_char})
            
            mock_strategy.validate.assert_called_once()
            mock_strategy.execute.assert_called_once()
            assert success is True

    @pytest.mark.asyncio
    async def test_handle_command_cast(self, mock_engine, player_char, enemy_char):
        """测试处理 cast 命令 (230-231) - 使用策略模式."""
        from src.game.combat.core import _get_strategies
        
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        session.participants[1].in_combat = True
        session.participants[1].next_action_time = 0
        
        # Mock策略 - validate不是异步的，返回普通值
        mock_strategy = MagicMock()
        mock_strategy.validate.return_value = (True, "")
        mock_strategy.execute = AsyncMock(return_value=MagicMock(success=True, message="施法成功"))
        
        with patch.dict(_get_strategies(), {"cast": mock_strategy}, clear=False):
            success, msg = await session.handle_player_command(player_char, "cast", {})
            
            mock_strategy.validate.assert_called_once()
            mock_strategy.execute.assert_called_once()
            assert success is True

    @pytest.mark.asyncio
    async def test_handle_command_flee(self, mock_engine, player_char, enemy_char):
        """测试处理 flee 命令 (232-233) - 使用策略模式."""
        from src.game.combat.core import _get_strategies
        
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        session.participants[1].in_combat = True
        session.participants[1].next_action_time = 0
        
        # Mock策略 - validate不是异步的，返回普通值
        mock_strategy = MagicMock()
        mock_strategy.validate.return_value = (True, "")
        mock_strategy.execute = AsyncMock(return_value=MagicMock(success=True, message="逃跑成功"))
        
        with patch.dict(_get_strategies(), {"flee": mock_strategy}, clear=False):
            success, msg = await session.handle_player_command(player_char, "flee", {})
            
            mock_strategy.validate.assert_called_once()
            mock_strategy.execute.assert_called_once()
            assert success is True

    @pytest.mark.asyncio
    async def test_handle_command_defend(self, mock_engine, player_char, enemy_char):
        """测试处理 defend 命令 (234-235) - 使用策略模式."""
        from src.game.combat.core import _get_strategies
        
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        session.participants[1].in_combat = True
        session.participants[1].next_action_time = 0
        
        # Mock策略 - validate不是异步的，返回普通值
        mock_strategy = MagicMock()
        mock_strategy.validate.return_value = (True, "")
        mock_strategy.execute = AsyncMock(return_value=MagicMock(success=True, message="防御成功"))
        
        with patch.dict(_get_strategies(), {"defend": mock_strategy}, clear=False):
            success, msg = await session.handle_player_command(player_char, "defend", {})
            
            mock_strategy.validate.assert_called_once()
            mock_strategy.execute.assert_called_once()
            assert success is True

    @pytest.mark.asyncio
    async def test_handle_command_unknown(self, mock_engine, player_char, enemy_char):
        """测试处理未知命令 (237)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        session.participants[1].in_combat = True
        session.participants[1].next_action_time = 0
        
        success, msg = await session.handle_player_command(player_char, "unknown_cmd", {})
        
        assert success is False
        assert "未知的战斗命令" in msg


class TestDoAttack:
    """测试攻击处理 _do_attack (243-277)."""

    @pytest.fixture
    def mock_engine(self):
        return Mock()

    @pytest.fixture
    def player_char(self):
        char = Mock()
        char.id = 1
        char.name = "玩家"
        char.get_hp.return_value = (100, 100)
        char.get_agility.return_value = 20
        char.get_attack.return_value = 50
        return char

    @pytest.fixture
    def enemy_char(self):
        char = Mock()
        char.id = 2
        char.name = "敌人"
        char.get_hp.return_value = (80, 80)
        char.get_defense.return_value = 30
        return char

    @pytest.mark.asyncio
    async def test_do_attack_no_target(self, mock_engine, player_char):
        """测试攻击但没有指定目标 (246-247)."""
        session = CombatSession(mock_engine, [player_char], player_char)
        combatant = session.participants[1]
        
        success, msg = await session._do_attack(combatant, {})
        
        assert success is False
        assert "请指定攻击目标" in msg

    @pytest.mark.asyncio
    async def test_do_attack_target_not_in_combat(self, mock_engine, player_char, enemy_char):
        """测试攻击不在战斗中的目标 (250-252)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        combatant = session.participants[1]
        session.participants[2].in_combat = False
        
        success, msg = await session._do_attack(combatant, {"target": enemy_char})
        
        assert success is False
        assert "目标不在战斗中" in msg

    @pytest.mark.asyncio
    async def test_do_attack_with_move_hit(self, mock_engine, player_char, enemy_char):
        """测试使用招式攻击命中 (258-265)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        combatant = session.participants[1]
        session.participants[2].in_combat = True
        
        move = Mock()
        move.name = "测试招式"
        move.cooldown = 2.0
        
        result = Mock()
        result.is_hit = True
        result.damage = 50
        result.is_crit = True
        
        with patch.object(session, '_execute_move', new_callable=AsyncMock, return_value=result):
            success, msg = await session._do_attack(combatant, {"target": enemy_char, "move": move})
            
            assert success is True
            assert "测试招式" in msg
            assert "50" in msg
            assert "暴击" in msg

    @pytest.mark.asyncio
    async def test_do_attack_with_move_miss(self, mock_engine, player_char, enemy_char):
        """测试使用招式攻击未命中 (258-265)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        combatant = session.participants[1]
        session.participants[2].in_combat = True
        
        move = Mock()
        move.name = "测试招式"
        move.cooldown = 2.0
        
        result = Mock()
        result.is_hit = False
        result.damage = 0
        result.is_crit = False
        
        with patch.object(session, '_execute_move', new_callable=AsyncMock, return_value=result):
            success, msg = await session._do_attack(combatant, {"target": enemy_char, "move": move})
            
            assert success is True
            assert "未命中" in msg

    @pytest.mark.asyncio
    async def test_do_attack_normal(self, mock_engine, player_char, enemy_char):
        """测试普通攻击 (266-271)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        combatant = session.participants[1]
        session.participants[2].in_combat = True
        
        with patch.object(session, '_calculate_normal_damage', return_value=25):
            success, msg = await session._do_attack(combatant, {"target": enemy_char})
            
            assert success is True
            assert "攻击" in msg
            assert "25" in msg
            enemy_char.modify_hp.assert_called_once()


class TestDoCast:
    """测试施法处理 _do_cast (284)."""

    @pytest.fixture
    def mock_engine(self):
        return Mock()

    @pytest.fixture
    def player_char(self):
        char = Mock()
        char.id = 1
        char.name = "玩家"
        char.get_hp.return_value = (100, 100)
        return char

    @pytest.mark.asyncio
    async def test_do_cast_no_neigong_specified(self, mock_engine, player_char):
        """测试施法时未指定内功 (284)."""
        session = CombatSession(mock_engine, [player_char], player_char)
        combatant = session.participants[1]
        
        success, msg = await session._do_cast(combatant, {})
        
        assert success is False
        assert "未指定内功" in msg


class TestDoFlee:
    """测试逃跑处理 _do_flee (291-315)."""

    @pytest.fixture
    def mock_engine(self):
        return Mock()

    @pytest.fixture
    def player_char(self):
        char = Mock()
        char.id = 1
        char.name = "玩家"
        char.get_hp.return_value = (100, 100)
        char.get_agility.return_value = 20
        return char

    @pytest.fixture
    def enemy_char(self):
        char = Mock()
        char.id = 2
        char.name = "敌人"
        char.get_hp.return_value = (80, 80)
        char.get_agility.return_value = 15
        return char

    @pytest.mark.asyncio
    async def test_do_flee_no_enemies(self, mock_engine, player_char):
        """测试逃跑但没有敌人 (296-299)."""
        # 只创建玩家，没有敌人
        session = CombatSession(mock_engine, [player_char], player_char)
        combatant = session.participants[1]
        
        success, msg = await session._do_flee(combatant, {})
        
        assert success is False
        assert "没有敌人" in msg

    @pytest.mark.asyncio
    async def test_do_flee_success(self, mock_engine, player_char, enemy_char):
        """测试逃跑成功 (309-312)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        combatant = session.participants[1]
        session.participants[2].in_combat = True
        
        with patch('random.random', return_value=0.1):  # 低随机值确保成功
            success, msg = await session._do_flee(combatant, {})
            
            assert success is True
            assert "成功逃跑" in msg
            assert session.result == CombatResult.FLEE

    @pytest.mark.asyncio
    async def test_do_flee_failure(self, mock_engine, player_char, enemy_char):
        """测试逃跑失败 (313-315)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        combatant = session.participants[1]
        session.participants[2].in_combat = True
        
        with patch('random.random', return_value=0.9):  # 高随机值确保失败
            success, msg = await session._do_flee(combatant, {})
            
            assert success is True  # 命令执行成功，只是逃跑失败
            assert "逃跑失败" in msg


class TestDoDefend:
    """测试防御处理 _do_defend (322-336)."""

    @pytest.fixture
    def mock_engine(self):
        return Mock()

    @pytest.fixture
    def player_char(self):
        char = Mock()
        char.id = 1
        char.name = "玩家"
        char.get_hp.return_value = (100, 100)
        char.buff_manager = AsyncMock()
        return char

    @pytest.mark.asyncio
    async def test_do_defend_with_buff_manager(self, mock_engine, player_char):
        """测试防御添加BUFF (322-336)."""
        session = CombatSession(mock_engine, [player_char], player_char)
        combatant = session.participants[1]
        
        success, msg = await session._do_defend(combatant, {})
        
        assert success is True
        assert "防御姿态" in msg
        # 验证 buff_manager.add 被调用
        player_char.buff_manager.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_do_defend_without_buff_manager(self, mock_engine, player_char):
        """测试防御但角色没有buff_manager (332-334)."""
        player_char_no_buff = Mock()
        player_char_no_buff.id = 1
        player_char_no_buff.name = "玩家"
        player_char_no_buff.get_hp.return_value = (100, 100)
        # 没有 buff_manager 属性
        del player_char_no_buff.buff_manager
        
        session = CombatSession(mock_engine, [player_char_no_buff], player_char_no_buff)
        combatant = session.participants[1]
        
        success, msg = await session._do_defend(combatant, {})
        
        assert success is True
        assert "防御姿态" in msg


class TestHandlePlayerCommand:
    """测试玩家命令处理 handle_player_command (217-237)."""

    @pytest.fixture
    def mock_engine(self):
        return Mock()

    @pytest.fixture
    def player_char(self):
        char = Mock()
        char.id = 1
        char.name = "玩家"
        char.get_hp.return_value = (100, 100)
        return char

    @pytest.fixture
    def enemy_char(self):
        char = Mock()
        char.id = 2
        char.name = "敌人"
        char.get_hp.return_value = (80, 80)
        return char

    @pytest.mark.asyncio
    async def test_handle_command_not_in_combat(self, mock_engine, player_char, enemy_char):
        """测试处理不在战斗中的角色的命令 (220-221)."""
        session = CombatSession(mock_engine, [player_char, enemy_char])
        # participant 不在战斗中
        session.participants[1].in_combat = False
        
        success, msg = await session.handle_player_command(player_char, "kill", {})
        
        assert success is False
        assert "你不在战斗中" in msg

    @pytest.mark.asyncio
    async def test_handle_command_not_ready(self, mock_engine, player_char, enemy_char):
        """测试处理未准备好的角色的命令 (223-225)."""
        session = CombatSession(mock_engine, [player_char, enemy_char])
        session.participants[1].in_combat = True
        # 设置冷却
        session.participants[1].next_action_time = time.time() + 100
        
        success, msg = await session.handle_player_command(player_char, "kill", {})
        
        assert success is False
        assert "你还不能行动" in msg

    @pytest.mark.asyncio
    async def test_handle_command_kill(self, mock_engine, player_char, enemy_char):
        """测试处理 kill 命令 (228-229) - 使用策略模式."""
        from src.game.combat.core import _get_strategies
        
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        session.participants[1].in_combat = True
        session.participants[1].next_action_time = 0
        
        # Mock策略 - validate不是异步的，返回普通值
        mock_strategy = MagicMock()
        mock_strategy.validate.return_value = (True, "")
        mock_strategy.execute = AsyncMock(return_value=MagicMock(success=True, message="攻击成功"))
        
        with patch.dict(_get_strategies(), {"kill": mock_strategy}, clear=False):
            success, msg = await session.handle_player_command(player_char, "kill", {"target": enemy_char})
            
            mock_strategy.validate.assert_called_once()
            mock_strategy.execute.assert_called_once()
            assert success is True

    @pytest.mark.asyncio
    async def test_handle_command_cast(self, mock_engine, player_char, enemy_char):
        """测试处理 cast 命令 (230-231) - 使用策略模式."""
        from src.game.combat.core import _get_strategies
        
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        session.participants[1].in_combat = True
        session.participants[1].next_action_time = 0
        
        # Mock策略 - validate不是异步的，返回普通值
        mock_strategy = MagicMock()
        mock_strategy.validate.return_value = (True, "")
        mock_strategy.execute = AsyncMock(return_value=MagicMock(success=True, message="施法成功"))
        
        with patch.dict(_get_strategies(), {"cast": mock_strategy}, clear=False):
            success, msg = await session.handle_player_command(player_char, "cast", {})
            
            mock_strategy.validate.assert_called_once()
            mock_strategy.execute.assert_called_once()
            assert success is True

    @pytest.mark.asyncio
    async def test_handle_command_flee(self, mock_engine, player_char, enemy_char):
        """测试处理 flee 命令 (232-233) - 使用策略模式."""
        from src.game.combat.core import _get_strategies
        
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        session.participants[1].in_combat = True
        session.participants[1].next_action_time = 0
        
        # Mock策略 - validate不是异步的，返回普通值
        mock_strategy = MagicMock()
        mock_strategy.validate.return_value = (True, "")
        mock_strategy.execute = AsyncMock(return_value=MagicMock(success=True, message="逃跑成功"))
        
        with patch.dict(_get_strategies(), {"flee": mock_strategy}, clear=False):
            success, msg = await session.handle_player_command(player_char, "flee", {})
            
            mock_strategy.validate.assert_called_once()
            mock_strategy.execute.assert_called_once()
            assert success is True

    @pytest.mark.asyncio
    async def test_handle_command_defend(self, mock_engine, player_char, enemy_char):
        """测试处理 defend 命令 (234-235) - 使用策略模式."""
        from src.game.combat.core import _get_strategies
        
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        session.participants[1].in_combat = True
        session.participants[1].next_action_time = 0
        
        # Mock策略 - validate不是异步的，返回普通值
        mock_strategy = MagicMock()
        mock_strategy.validate.return_value = (True, "")
        mock_strategy.execute = AsyncMock(return_value=MagicMock(success=True, message="防御成功"))
        
        with patch.dict(_get_strategies(), {"defend": mock_strategy}, clear=False):
            success, msg = await session.handle_player_command(player_char, "defend", {})
            
            mock_strategy.validate.assert_called_once()
            mock_strategy.execute.assert_called_once()
            assert success is True

    @pytest.mark.asyncio
    async def test_handle_command_unknown(self, mock_engine, player_char, enemy_char):
        """测试处理未知命令 (237)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        session.participants[1].in_combat = True
        session.participants[1].next_action_time = 0
        
        success, msg = await session.handle_player_command(player_char, "unknown_cmd", {})
        
        assert success is False
        assert "未知的战斗命令" in msg


class TestDoAttack:
    """测试攻击处理 _do_attack (243-277)."""

    @pytest.fixture
    def mock_engine(self):
        return Mock()

    @pytest.fixture
    def player_char(self):
        char = Mock()
        char.id = 1
        char.name = "玩家"
        char.get_hp.return_value = (100, 100)
        char.get_agility.return_value = 20
        char.get_attack.return_value = 50
        return char

    @pytest.fixture
    def enemy_char(self):
        char = Mock()
        char.id = 2
        char.name = "敌人"
        char.get_hp.return_value = (80, 80)
        char.get_defense.return_value = 30
        return char

    @pytest.mark.asyncio
    async def test_do_attack_no_target(self, mock_engine, player_char):
        """测试攻击但没有指定目标 (246-247)."""
        session = CombatSession(mock_engine, [player_char], player_char)
        combatant = session.participants[1]
        
        success, msg = await session._do_attack(combatant, {})
        
        assert success is False
        assert "请指定攻击目标" in msg

    @pytest.mark.asyncio
    async def test_do_attack_target_not_in_combat(self, mock_engine, player_char, enemy_char):
        """测试攻击不在战斗中的目标 (250-252)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        combatant = session.participants[1]
        session.participants[2].in_combat = False
        
        success, msg = await session._do_attack(combatant, {"target": enemy_char})
        
        assert success is False
        assert "目标不在战斗中" in msg

    @pytest.mark.asyncio
    async def test_do_attack_with_move_hit(self, mock_engine, player_char, enemy_char):
        """测试使用招式攻击命中 (258-265)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        combatant = session.participants[1]
        session.participants[2].in_combat = True
        
        move = Mock()
        move.name = "测试招式"
        move.cooldown = 2.0
        
        result = Mock()
        result.is_hit = True
        result.damage = 50
        result.is_crit = True
        
        with patch.object(session, '_execute_move', new_callable=AsyncMock, return_value=result):
            success, msg = await session._do_attack(combatant, {"target": enemy_char, "move": move})
            
            assert success is True
            assert "测试招式" in msg
            assert "50" in msg
            assert "暴击" in msg

    @pytest.mark.asyncio
    async def test_do_attack_with_move_miss(self, mock_engine, player_char, enemy_char):
        """测试使用招式攻击未命中 (258-265)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        combatant = session.participants[1]
        session.participants[2].in_combat = True
        
        move = Mock()
        move.name = "测试招式"
        move.cooldown = 2.0
        
        result = Mock()
        result.is_hit = False
        result.damage = 0
        result.is_crit = False
        
        with patch.object(session, '_execute_move', new_callable=AsyncMock, return_value=result):
            success, msg = await session._do_attack(combatant, {"target": enemy_char, "move": move})
            
            assert success is True
            assert "未命中" in msg

    @pytest.mark.asyncio
    async def test_do_attack_normal(self, mock_engine, player_char, enemy_char):
        """测试普通攻击 (266-271)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        combatant = session.participants[1]
        session.participants[2].in_combat = True
        
        with patch.object(session, '_calculate_normal_damage', return_value=25):
            success, msg = await session._do_attack(combatant, {"target": enemy_char})
            
            assert success is True
            assert "攻击" in msg
            assert "25" in msg
            enemy_char.modify_hp.assert_called_once()


class TestDoCast:
    """测试施法处理 _do_cast (284)."""

    @pytest.fixture
    def mock_engine(self):
        return Mock()

    @pytest.fixture
    def player_char(self):
        char = Mock()
        char.id = 1
        char.name = "玩家"
        char.get_hp.return_value = (100, 100)
        return char

    @pytest.mark.asyncio
    async def test_do_cast_no_neigong_specified(self, mock_engine, player_char):
        """测试施法时未指定内功 (284)."""
        session = CombatSession(mock_engine, [player_char], player_char)
        combatant = session.participants[1]
        
        success, msg = await session._do_cast(combatant, {})
        
        assert success is False
        assert "未指定内功" in msg


class TestDoFlee:
    """测试逃跑处理 _do_flee (291-315)."""

    @pytest.fixture
    def mock_engine(self):
        return Mock()

    @pytest.fixture
    def player_char(self):
        char = Mock()
        char.id = 1
        char.name = "玩家"
        char.get_hp.return_value = (100, 100)
        char.get_agility.return_value = 20
        return char

    @pytest.fixture
    def enemy_char(self):
        char = Mock()
        char.id = 2
        char.name = "敌人"
        char.get_hp.return_value = (80, 80)
        char.get_agility.return_value = 15
        return char

    @pytest.mark.asyncio
    async def test_do_flee_no_enemies(self, mock_engine, player_char):
        """测试逃跑但没有敌人 (296-299)."""
        # 只创建玩家，没有敌人
        session = CombatSession(mock_engine, [player_char], player_char)
        combatant = session.participants[1]
        
        success, msg = await session._do_flee(combatant, {})
        
        assert success is False
        assert "没有敌人" in msg

    @pytest.mark.asyncio
    async def test_do_flee_success(self, mock_engine, player_char, enemy_char):
        """测试逃跑成功 (309-312)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        combatant = session.participants[1]
        session.participants[2].in_combat = True
        
        with patch('random.random', return_value=0.1):  # 低随机值确保成功
            success, msg = await session._do_flee(combatant, {})
            
            assert success is True
            assert "成功逃跑" in msg
            assert session.result == CombatResult.FLEE

    @pytest.mark.asyncio
    async def test_do_flee_failure(self, mock_engine, player_char, enemy_char):
        """测试逃跑失败 (313-315)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        combatant = session.participants[1]
        session.participants[2].in_combat = True
        
        with patch('random.random', return_value=0.9):  # 高随机值确保失败
            success, msg = await session._do_flee(combatant, {})
            
            assert success is True  # 命令执行成功，只是逃跑失败
            assert "逃跑失败" in msg


class TestDoDefend:
    """测试防御处理 _do_defend (322-336)."""

    @pytest.fixture
    def mock_engine(self):
        return Mock()

    @pytest.fixture
    def player_char(self):
        char = Mock()
        char.id = 1
        char.name = "玩家"
        char.get_hp.return_value = (100, 100)
        char.buff_manager = AsyncMock()
        return char

    @pytest.mark.asyncio
    async def test_do_defend_with_buff_manager(self, mock_engine, player_char):
        """测试防御添加BUFF (322-336)."""
        session = CombatSession(mock_engine, [player_char], player_char)
        combatant = session.participants[1]
        
        success, msg = await session._do_defend(combatant, {})
        
        assert success is True
        assert "防御姿态" in msg
        # 验证 buff_manager.add 被调用
        player_char.buff_manager.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_do_defend_without_buff_manager(self, mock_engine, player_char):
        """测试防御但角色没有buff_manager (332-334)."""
        player_char_no_buff = Mock()
        player_char_no_buff.id = 1
        player_char_no_buff.name = "玩家"
        player_char_no_buff.get_hp.return_value = (100, 100)
        # 没有 buff_manager 属性
        del player_char_no_buff.buff_manager
        
        session = CombatSession(mock_engine, [player_char_no_buff], player_char_no_buff)
        combatant = session.participants[1]
        
        success, msg = await session._do_defend(combatant, {})
        
        assert success is True
        assert "防御姿态" in msg


