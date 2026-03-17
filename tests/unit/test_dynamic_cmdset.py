"""动态命令集合单元测试.

测试TD-019: 动态命令集合
"""

import pytest
from unittest.mock import MagicMock

from src.engine.commands.handler import CommandHandler
from src.engine.commands.command import Command


class MockCommand(Command):
    """模拟命令."""
    key = "mock_cmd"
    
    async def execute(self):
        return True


class TestDynamicCmdset:
    """测试动态命令集合."""
    
    @pytest.fixture
    def handler(self):
        """创建命令处理器."""
        mock_engine = MagicMock()
        return CommandHandler(mock_engine)
    
    @pytest.fixture
    def mock_caller_no_extras(self):
        """创建无额外命令的模拟调用者."""
        caller = MagicMock()
        caller.location = None
        # 确保cmdset属性不存在，避免被merge
        if hasattr(caller, 'cmdset'):
            del caller.cmdset
        return caller
    
    @pytest.fixture
    def mock_caller_with_location_cmds(self):
        """创建带位置命令的模拟调用者."""
        caller = MagicMock()
        
        # 模拟房间有本地命令
        room = MagicMock()
        room.get_local_cmds.return_value = [MockCommand]
        # 确保没有cmdset属性
        if hasattr(room, 'cmdset'):
            del room.cmdset
        caller.location = room
        
        # 确保没有cmdset属性
        if hasattr(caller, 'cmdset'):
            del caller.cmdset
        
        return caller
    
    @pytest.fixture
    def mock_caller_with_special_cmds(self):
        """创建带特殊命令的模拟调用者."""
        caller = MagicMock()
        caller.location = None
        caller.get_special_cmds.return_value = [MockCommand]
        
        # 确保没有cmdset属性
        if hasattr(caller, 'cmdset'):
            del caller.cmdset
        
        return caller
    
    def test_basic_cmdset(self, handler, mock_caller_no_extras):
        """测试基础命令集合."""
        cmdset = handler.get_cmdset(mock_caller_no_extras)

        assert cmdset is not None
        assert hasattr(cmdset, 'match')
    
    def test_location_local_cmds(self, handler, mock_caller_with_location_cmds):
        """测试位置本地命令."""
        cmdset = handler.get_cmdset(mock_caller_with_location_cmds)
        
        # 应该包含房间提供的命令
        assert cmdset.match("mock_cmd") is not None
    
    def test_caller_special_cmds(self, handler, mock_caller_with_special_cmds):
        """测试调用者特殊命令."""
        cmdset = handler.get_cmdset(mock_caller_with_special_cmds)
        
        # 应该包含调用者的特殊命令
        assert cmdset.match("mock_cmd") is not None
    
    def test_no_location(self, handler, mock_caller_no_extras):
        """测试无位置情况."""
        mock_caller_no_extras.location = None
        
        # 不应报错
        cmdset = handler.get_cmdset(mock_caller_no_extras)
        assert cmdset is not None
        assert hasattr(cmdset, 'match')
    
    def test_location_without_get_local_cmds(self, handler):
        """测试位置没有get_local_cmds方法."""
        caller = MagicMock()
        room = MagicMock()
        # 没有get_local_cmds方法
        if hasattr(room, 'get_local_cmds'):
            del room.get_local_cmds
        # 确保没有cmdset属性
        if hasattr(room, 'cmdset'):
            del room.cmdset
        caller.location = room
        
        # 确保caller也没有cmdset属性
        if hasattr(caller, 'cmdset'):
            del caller.cmdset
        
        # 不应报错
        cmdset = handler.get_cmdset(caller)
        assert cmdset is not None
        assert hasattr(cmdset, 'match')
