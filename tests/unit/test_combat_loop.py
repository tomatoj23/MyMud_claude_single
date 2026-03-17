"""战斗系统单元测试 - 战斗循环.

测试战斗循环、AI处理等功能.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.game.combat.core import CombatAction, Combatant, CombatResult, CombatSession

class TestCombatLoop:
    """测试战斗主循环 _combat_loop (160-171)."""

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
    async def test_combat_loop_processes_ai_and_checks_end(self, mock_engine, player_char, enemy_char):
        """测试战斗循环处理AI回合并检查结束 (160-171)."""
        session = CombatSession(mock_engine, [player_char, enemy_char])
        session.active = True  # 需要设置为 True 才能进入循环
        
        # 第一次循环 _process_ai_turns 被调用，第二次循环 _check_end 返回结果
        ai_call_count = [0]
        async def mock_process_ai():
            ai_call_count[0] += 1
        
        check_count = [0]
        async def mock_check_end():
            check_count[0] += 1
            if check_count[0] >= 2:  # 第二次检查时结束战斗
                return CombatResult.WIN
            return None
        
        with patch.object(session, '_process_ai_turns', side_effect=mock_process_ai):
            with patch.object(session, '_check_end', side_effect=mock_check_end):
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    # 运行战斗循环，应该很快结束
                    await session._combat_loop()
                    
                    assert session.active is False
                    # _check_end 被调用两次以上
                    assert check_count[0] >= 2


class TestProcessAiTurns:
    """测试 AI 回合处理 _process_ai_turns (175-187)."""

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
    async def test_process_ai_turns_skips_player(self, mock_engine, enemy_char):
        """测试 AI 回合处理跳过玩家 (178-179)."""
        # 创建一个没有玩家的战斗
        session = CombatSession(mock_engine, [enemy_char])
        session.participants[2].is_player = False
        session.participants[2].in_combat = True
        
        # 模拟 AI 已经准备好行动
        session.participants[2].next_action_time = 0
        
        with patch.object(session, '_ai_decide', new_callable=AsyncMock) as mock_decide:
            with patch.object(session, '_execute_action', new_callable=AsyncMock) as mock_execute:
                with patch.object(session, '_can_fight', return_value=True):
                    await session._process_ai_turns()
                    
                    # 非玩家应该被处理
                    mock_decide.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_ai_turns_skips_not_in_combat(self, mock_engine, enemy_char):
        """测试 AI 回合处理跳过不在战斗中的角色 (181-182)."""
        session = CombatSession(mock_engine, [enemy_char])
        session.participants[2].is_player = False
        session.participants[2].in_combat = False  # 不在战斗中
        
        with patch.object(session, '_ai_decide', new_callable=AsyncMock) as mock_decide:
            await session._process_ai_turns()
            
            # 不应该调用 AI 决策
            mock_decide.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_ai_turns_skips_not_ready(self, mock_engine, enemy_char):
        """测试 AI 回合处理跳过未准备好的角色 (184-187)."""
        session = CombatSession(mock_engine, [enemy_char])
        session.participants[2].is_player = False
        session.participants[2].in_combat = True
        # 设置冷却时间到未来
        session.participants[2].next_action_time = time.time() + 100
        
        with patch.object(session, '_ai_decide', new_callable=AsyncMock) as mock_decide:
            with patch.object(session, '_can_fight', return_value=True):
                await session._process_ai_turns()
                
                # 不应该调用 AI 决策，因为还没准备好
                mock_decide.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_ai_turns_when_ready(self, mock_engine, enemy_char):
        """测试 AI 回合处理当角色准备好时执行行动 (184-187)."""
        session = CombatSession(mock_engine, [enemy_char])
        session.participants[2].is_player = False
        session.participants[2].in_combat = True
        session.participants[2].next_action_time = 0  # 已经准备好
        
        action = CombatAction("defend")
        
        with patch.object(session, '_ai_decide', new_callable=AsyncMock, return_value=action) as mock_decide:
            with patch.object(session, '_execute_action', new_callable=AsyncMock) as mock_execute:
                with patch.object(session, '_can_fight', return_value=True):
                    await session._process_ai_turns()
                    
                    # 应该调用 AI 决策和执行行动
                    mock_decide.assert_called_once()
                    mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_ai_turns_skips_player_continue(self, mock_engine, player_char, enemy_char):
        """测试 AI 回合处理跳过玩家（覆盖第 179 行 continue）."""
        # 创建包含玩家和敌人的会话
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        session.participants[1].is_player = True  # 玩家
        session.participants[1].in_combat = True
        session.participants[1].next_action_time = 0  # 已准备好
        
        session.participants[2].is_player = False  # 敌人
        session.participants[2].in_combat = True
        session.participants[2].next_action_time = time.time() + 100  # 未准备好
        
        with patch.object(session, '_ai_decide', new_callable=AsyncMock) as mock_decide:
            with patch.object(session, '_can_fight', return_value=True):
                await session._process_ai_turns()
                
                # 玩家被跳过，敌人未准备好，所以不应该调用 _ai_decide
                mock_decide.assert_not_called()


class TestAiDecide:
    """测试 AI 决策方法 _ai_decide (191-194)."""

    @pytest.fixture
    def mock_engine(self):
        return Mock()

    @pytest.fixture
    def enemy_char(self):
        char = Mock()
        char.id = 2
        char.name = "敌人"
        char.get_hp.return_value = (80, 80)
        return char

    @pytest.mark.asyncio
    async def test_ai_decide_returns_action(self, mock_engine, enemy_char):
        """测试 AI 决策返回行动 (191-194)."""
        from src.game.combat.ai import CombatAI
        
        session = CombatSession(mock_engine, [enemy_char])
        combatant = session.participants[2]
        
        # 模拟 CombatAI.decide 返回一个动作
        mock_action = CombatAction("defend")
        
        with patch('src.game.combat.ai.CombatAI.decide', new_callable=AsyncMock, return_value=mock_action):
            result = await session._ai_decide(combatant)
            
            assert result == mock_action


