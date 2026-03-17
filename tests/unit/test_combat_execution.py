"""战斗系统单元测试 - 执行逻辑.

测试战斗动作执行、伤害计算等.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.game.combat.core import CombatAction, Combatant, CombatResult, CombatSession

class TestExecuteAction:
    """测试执行行动 _execute_action (342-349)."""

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
    async def test_execute_action_move(self, mock_engine, enemy_char):
        """测试执行招式行动 (342-343)."""
        session = CombatSession(mock_engine, [enemy_char])
        combatant = session.participants[2]
        
        action = CombatAction("move", target=enemy_char, data={"move": Mock()})
        
        with patch.object(session, '_execute_move_action', new_callable=AsyncMock) as mock_move:
            await session._execute_action(combatant, action)
            mock_move.assert_called_once_with(combatant, action)

    @pytest.mark.asyncio
    async def test_execute_action_item(self, mock_engine, enemy_char):
        """测试执行物品行动 (344-345)."""
        session = CombatSession(mock_engine, [enemy_char])
        combatant = session.participants[2]
        
        action = CombatAction("item")
        
        await session._execute_action(combatant, action)
        
        assert f"{enemy_char.name} 使用了物品" in session.log

    @pytest.mark.asyncio
    async def test_execute_action_flee(self, mock_engine, enemy_char):
        """测试执行逃跑行动 (346-347)."""
        session = CombatSession(mock_engine, [enemy_char])
        combatant = session.participants[2]
        
        action = CombatAction("flee")
        
        with patch.object(session, '_do_flee', new_callable=AsyncMock) as mock_flee:
            await session._execute_action(combatant, action)
            mock_flee.assert_called_once_with(combatant, {})

    @pytest.mark.asyncio
    async def test_execute_action_defend(self, mock_engine, enemy_char):
        """测试执行防御行动 (348-349)."""
        session = CombatSession(mock_engine, [enemy_char])
        combatant = session.participants[2]
        
        action = CombatAction("defend")
        
        with patch.object(session, '_do_defend', new_callable=AsyncMock) as mock_defend:
            await session._execute_action(combatant, action)
            mock_defend.assert_called_once_with(combatant, {})


class TestExecuteMoveAction:
    """测试执行招式攻击 _execute_move_action (355-373)."""

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
    async def test_execute_move_action_no_target(self, mock_engine, enemy_char):
        """测试执行招式但没有目标 (358-359)."""
        session = CombatSession(mock_engine, [enemy_char])
        combatant = session.participants[2]
        
        action = CombatAction("move", target=None, data={"move": Mock()})
        
        await session._execute_move_action(combatant, action)
        
        # 没有目标应该直接返回，不记录日志
        assert len(session.log) == 0

    @pytest.mark.asyncio
    async def test_execute_move_action_hit_with_crit(self, mock_engine, enemy_char):
        """测试执行招式命中并暴击 (364-368)."""
        session = CombatSession(mock_engine, [enemy_char])
        combatant = session.participants[2]
        
        move = Mock()
        move.name = "测试招式"
        move.cooldown = 2.0
        
        action = CombatAction("move", target=enemy_char, data={"move": move})
        
        result = Mock()
        result.is_hit = True
        result.damage = 100
        result.is_crit = True
        
        with patch.object(session, '_execute_move', new_callable=AsyncMock, return_value=result):
            with patch.object(session, '_calculate_cooldown', return_value=2.0):
                await session._execute_move_action(combatant, action)
                
                assert "暴击" in session.log[-1]
                assert "100" in session.log[-1]

    @pytest.mark.asyncio
    async def test_execute_move_action_miss(self, mock_engine, enemy_char):
        """测试执行招式未命中 (369-372)."""
        session = CombatSession(mock_engine, [enemy_char])
        combatant = session.participants[2]
        
        move = Mock()
        move.name = "测试招式"
        
        action = CombatAction("move", target=enemy_char, data={"move": move})
        
        result = Mock()
        result.is_hit = False
        result.damage = 0
        result.is_crit = False
        
        with patch.object(session, '_execute_move', new_callable=AsyncMock, return_value=result):
            with patch.object(session, '_calculate_cooldown', return_value=2.0):
                await session._execute_move_action(combatant, action)
                
                assert "闪开" in session.log[-1]


class TestExecuteMove:
    """测试执行招式 _execute_move (379-387)."""

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
    async def test_execute_move_hit(self, mock_engine, player_char, enemy_char):
        """测试执行招式命中并造成伤害 (379-387)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        
        move = Mock()
        
        # 使用真实的 calculator 但 mock calculate_damage 方法
        from src.game.combat.calculator import CombatCalculator, DamageResult
        
        result = DamageResult(damage=50, is_hit=True, is_crit=False)
        
        with patch.object(CombatCalculator, 'calculate_damage', return_value=result):
            returned_result = await session._execute_move(player_char, enemy_char, move)
            
            assert returned_result.damage == 50
            enemy_char.modify_hp.assert_called_once_with(-50)

    @pytest.mark.asyncio
    async def test_execute_move_no_damage(self, mock_engine, player_char, enemy_char):
        """测试执行招式命中但没有伤害 (384-387)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        
        move = Mock()
        
        from src.game.combat.calculator import CombatCalculator, DamageResult
        
        result = DamageResult(damage=0, is_hit=True, is_crit=False)  # 无伤害
        
        with patch.object(CombatCalculator, 'calculate_damage', return_value=result):
            returned_result = await session._execute_move(player_char, enemy_char, move)
            
            assert returned_result.damage == 0
            # 不应调用 modify_hp
            enemy_char.modify_hp.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_move_miss(self, mock_engine, player_char, enemy_char):
        """测试执行招式未命中 (384-387)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        
        move = Mock()
        
        from src.game.combat.calculator import CombatCalculator, DamageResult
        
        result = DamageResult(damage=0, is_hit=False, is_crit=False)  # 未命中
        
        with patch.object(CombatCalculator, 'calculate_damage', return_value=result):
            returned_result = await session._execute_move(player_char, enemy_char, move)
            
            assert returned_result.is_hit is False
            # 未命中不应调用 modify_hp
            enemy_char.modify_hp.assert_not_called()


class TestCalculateNormalDamage:
    """测试普通伤害计算 _calculate_normal_damage (393-398)."""

    @pytest.fixture
    def mock_engine(self):
        return Mock()

    def test_calculate_normal_damage(self, mock_engine):
        """测试普通伤害计算 (393-398)."""
        attacker = Mock()
        attacker.get_attack.return_value = 100
        
        defender = Mock()
        defender.get_defense.return_value = 30
        
        session = CombatSession(mock_engine, [attacker])
        
        with patch('random.uniform', return_value=1.0):  # 固定随机因子
            damage = session._calculate_normal_damage(attacker, defender)
            
            # 基础伤害 = max(1, 100 - 30 * 0.3) = max(1, 91) = 91
            # 应用随机因子 1.0 -> 91
            assert damage == 91

    def test_calculate_normal_damage_random_range(self, mock_engine):
        """测试普通伤害计算的随机范围 (393-398)."""
        attacker = Mock()
        attacker.get_attack.return_value = 100
        
        defender = Mock()
        defender.get_defense.return_value = 30
        
        session = CombatSession(mock_engine, [attacker])
        
        # 测试多次，确保随机性
        damages = []
        for _ in range(10):
            damages.append(session._calculate_normal_damage(attacker, defender))
        
        # 所有伤害都应该是正数
        assert all(d > 0 for d in damages)
        # 伤害应该在合理范围内
        assert all(80 <= d <= 100 for d in damages)


class TestCheckEndLose:
    """测试战斗结束检查 - 失败情况 (432)."""

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
    async def test_check_end_lose(self, mock_engine, player_char, enemy_char):
        """测试战斗失败判定 (432)."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        
        # 玩家死亡，敌人存活
        player_char.get_hp.return_value = (0, 100)
        enemy_char.get_hp.return_value = (80, 80)
        
        result = await session._check_end()
        
        assert result == CombatResult.LOSE
        assert session.winner == enemy_char


class TestCombatSessionAdditionalCoverage:
    """额外覆盖率测试."""

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
    async def test_combat_loop_ai_calls_check_end(self, mock_engine, player_char, enemy_char):
        """测试战斗循环中 AI 处理调用检查结束."""
        session = CombatSession(mock_engine, [player_char, enemy_char])
        session.active = True
        
        call_count = [0]
        async def mock_process_ai():
            call_count[0] += 1
            if call_count[0] >= 1:
                session.active = False  # 停止循环
        
        with patch.object(session, '_process_ai_turns', side_effect=mock_process_ai):
            with patch.object(session, '_check_end', new_callable=AsyncMock, return_value=None):
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    await session._combat_loop()
                    
                    assert call_count[0] >= 1

    @pytest.mark.asyncio
    async def test_handle_player_command_default_args(self, mock_engine, player_char, enemy_char):
        """测试 handle_player_command 使用默认 args."""
        session = CombatSession(mock_engine, [player_char, enemy_char], player_char)
        session.participants[1].in_combat = True
        session.participants[1].next_action_time = time.time() + 100
        
        # 不传 args 参数
        success, msg = await session.handle_player_command(player_char, "kill")
        
        assert success is False
        assert "你还不能行动" in msg

    @pytest.mark.asyncio
    async def test_process_ai_turns_can_fight_false(self, mock_engine, enemy_char):
        """测试 AI 回合处理当 _can_fight 返回 False (181-182)."""
        session = CombatSession(mock_engine, [enemy_char])
        session.participants[2].is_player = False
        session.participants[2].in_combat = True
        session.participants[2].next_action_time = 0
        
        with patch.object(session, '_can_fight', return_value=False):
            with patch.object(session, '_ai_decide', new_callable=AsyncMock) as mock_decide:
                await session._process_ai_turns()
                
                # 不应该调用 AI 决策，因为 _can_fight 返回 False
                mock_decide.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_move_action_normal_attack(self, mock_engine, enemy_char):
        """测试执行普通攻击（move 为 None）(365-368)."""
        session = CombatSession(mock_engine, [enemy_char])
        combatant = session.participants[2]
        
        # move 为 None 表示普通攻击
        action = CombatAction("move", target=enemy_char, data={"move": None})
        
        result = Mock()
        result.is_hit = True
        result.damage = 30
        result.is_crit = False
        
        with patch.object(session, '_execute_move', new_callable=AsyncMock, return_value=result):
            with patch.object(session, '_calculate_cooldown', return_value=2.0):
                await session._execute_move_action(combatant, action)
                
                assert "普通攻击" in session.log[-1]
                assert "30" in session.log[-1]
