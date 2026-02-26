"""调试命令测试."""

import pytest
from unittest.mock import MagicMock, patch

from src.game.commands.debug import (
    CmdValidateCharacter,
    CmdInspectCharacter,
    CmdValidateAll,
    CmdBalanceConfig,
    CmdReloadConfig,
)


class TestCmdValidateCharacter:
    """测试角色验证命令."""
    
    @pytest.mark.asyncio
    async def test_no_args(self):
        """测试无参数."""
        cmd = CmdValidateCharacter()
        cmd.args = ""
        cmd.caller = MagicMock()
        
        await cmd.execute()
        
        cmd.caller.msg.assert_called_once()
        assert "用法" in cmd.caller.msg.call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_invalid_id(self):
        """测试无效ID."""
        cmd = CmdValidateCharacter()
        cmd.args = "abc"
        cmd.caller = MagicMock()
        
        await cmd.execute()
        
        cmd.caller.msg.assert_called_with("角色ID必须是数字")
    
    @pytest.mark.asyncio
    async def test_character_not_found(self):
        """测试角色不存在."""
        cmd = CmdValidateCharacter()
        cmd.args = "999"
        cmd.caller = MagicMock()
        
        with patch('src.engine.objects.manager.ObjectManager') as mock_mgr:
            mock_mgr.return_value.get.return_value = None
            await cmd.execute()
        
        cmd.caller.msg.assert_called_with("找不到角色: 999")
    
    @pytest.mark.asyncio
    async def test_valid_character(self):
        """测试有效角色."""
        cmd = CmdValidateCharacter()
        cmd.args = "1"
        cmd.caller = MagicMock()
        
        char = MagicMock()
        char.name = "测试角色"
        char.validate_state.return_value = []
        
        with patch('src.engine.objects.manager.ObjectManager') as mock_mgr:
            mock_mgr.return_value.get.return_value = char
            await cmd.execute()
        
        cmd.caller.msg.assert_called_with("角色 测试角色 状态正常")


class TestCmdInspectCharacter:
    """测试角色查看命令."""
    
    @pytest.mark.asyncio
    async def test_inspect_character(self):
        """测试查看角色."""
        cmd = CmdInspectCharacter()
        cmd.args = "1"
        cmd.caller = MagicMock()
        
        char = MagicMock()
        char.name = "测试角色"
        char.id = 1
        char.key = "test_char"
        char.hp = 100
        char.max_hp = 100
        char.level = 10
        char.birth_talents = {"gengu": 15, "wuxing": 18}
        char.attributes = {"strength": 20}
        char.get_attack.return_value = 50
        char.is_state_valid.return_value = True
        
        with patch('src.engine.objects.manager.ObjectManager') as mock_mgr:
            mock_mgr.return_value.get.return_value = char
            await cmd.execute()
        
        # 应该输出多行信息
        assert cmd.caller.msg.call_count > 5


class TestCmdValidateAll:
    """测试验证所有角色命令."""
    
    @pytest.mark.asyncio
    async def test_validate_all(self):
        """测试验证所有."""
        cmd = CmdValidateAll()
        cmd.args = ""
        cmd.caller = MagicMock()
        
        char1 = MagicMock()
        char1.validate_state.return_value = []
        char2 = MagicMock()
        char2.validate_state.return_value = ["error"]
        char2.fix_state.return_value = ["fixed"]
        
        with patch('src.engine.objects.manager.ObjectManager') as mock_mgr:
            mock_mgr.return_value._cache.values.return_value = [char1, char2]
            await cmd.execute()
        
        cmd.caller.msg.assert_called()


class TestCmdBalanceConfig:
    """测试配置查看命令."""
    
    @pytest.mark.asyncio
    async def test_show_all_config(self):
        """测试显示所有配置."""
        cmd = CmdBalanceConfig()
        cmd.args = ""
        cmd.caller = MagicMock()
        
        with patch('src.utils.config_loader.get_balance_config') as mock_config:
            mock_config.return_value.get_all.return_value = {
                "test": {"value": 100}
            }
            cmd._show_config = MagicMock()
            await cmd.execute()
        
        cmd._show_config.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_show_specific_config(self):
        """测试显示特定配置."""
        cmd = CmdBalanceConfig()
        cmd.args = "combat damage base"
        cmd.caller = MagicMock()
        
        with patch('src.utils.config_loader.get_balance_config') as mock_config:
            mock_config.return_value.get.return_value = 10
            await cmd.execute()
        
        cmd.caller.msg.assert_called_with("combat.damage.base = 10")


class TestCmdReloadConfig:
    """测试重新加载配置命令."""
    
    @pytest.mark.asyncio
    async def test_reload(self):
        """测试重新加载."""
        cmd = CmdReloadConfig()
        cmd.args = ""
        cmd.caller = MagicMock()
        
        mock_config = MagicMock()
        
        with patch('src.utils.config_loader.get_balance_config', return_value=mock_config):
            await cmd.execute()
        
        mock_config.reload.assert_called_once()
        cmd.caller.msg.assert_called_with("配置文件已重新加载")
