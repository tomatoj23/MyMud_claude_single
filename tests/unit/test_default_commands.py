"""默认命令单元测试.

测试commands/default.py中各命令的执行。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.engine.commands.command import CommandResult
from src.engine.commands.default import (
    CmdCreate,
    CmdDestroy,
    CmdHelp,
    CmdInventory,
    CmdLook,
    CmdMove,
)


class TestCmdLook:
    """查看命令测试."""

    @pytest.mark.asyncio
    async def test_look_no_caller(self):
        """测试无调用者."""
        cmd = CmdLook()
        result = await cmd.execute()
        assert result.success is False
        assert "调用者未设置" in result.message

    @pytest.mark.asyncio
    async def test_look_no_args_with_location(self):
        """测试查看当前位置."""
        cmd = CmdLook()
        cmd.caller = Mock()
        cmd.args = ""
        
        location = Mock()
        location.at_desc.return_value = "这是一个房间。"
        location.contents = []
        cmd.caller.location = location
        
        result = await cmd.execute()
        assert result.success is True

    @pytest.mark.asyncio
    async def test_look_no_args_without_location(self):
        """测试无位置时的查看."""
        cmd = CmdLook()
        cmd.caller = Mock()
        cmd.args = ""
        cmd.caller.location = None
        
        result = await cmd.execute()
        assert result.success is True

    @pytest.mark.asyncio
    async def test_look_with_contents(self):
        """测试查看有内容的房间."""
        cmd = CmdLook()
        cmd.caller = Mock()
        cmd.args = ""
        
        obj1 = Mock()
        obj1.key = "箱子"
        obj2 = Mock()
        obj2.key = "桌子"
        
        location = Mock()
        location.at_desc.return_value = "房间里。"
        location.contents = [obj1, obj2]
        cmd.caller.location = location
        
        result = await cmd.execute()
        assert result.success is True

    @pytest.mark.asyncio
    async def test_look_with_target_found(self):
        """测试查看指定目标（找到）."""
        cmd = CmdLook()
        cmd.caller = Mock()
        cmd.args = "箱子"
        
        target = Mock()
        target.at_desc.return_value = "一个木箱。"
        cmd.search = Mock(return_value=target)
        
        result = await cmd.execute()
        assert result.success is True
        cmd.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_look_with_target_not_found(self):
        """测试查看指定目标（未找到）."""
        cmd = CmdLook()
        cmd.caller = Mock()
        cmd.args = "不存在的物品"
        cmd.search = Mock(return_value=None)
        
        result = await cmd.execute()
        assert result.success is False


class TestCmdMove:
    """移动命令测试."""

    @pytest.mark.asyncio
    async def test_move_no_caller(self):
        """测试无调用者."""
        cmd = CmdMove()
        result = await cmd.execute()
        assert result.success is False

    @pytest.mark.asyncio
    async def test_move_no_args(self):
        """测试无参数."""
        cmd = CmdMove()
        cmd.caller = Mock()
        cmd.args = ""
        
        result = await cmd.execute()
        assert result.success is False

    @pytest.mark.asyncio
    async def test_move_target_not_found(self):
        """测试目标未找到."""
        cmd = CmdMove()
        cmd.caller = Mock()
        cmd.args = "不存在的地点"
        cmd.search = Mock(return_value=None)
        
        result = await cmd.execute()
        assert result.success is False

    @pytest.mark.asyncio
    async def test_move_success(self):
        """测试成功移动."""
        cmd = CmdMove()
        cmd.caller = Mock()
        cmd.caller.location = Mock()
        cmd.caller.location.key = "旧房间"
        cmd.args = "新房间"
        
        target = Mock()
        target.key = "新房间"
        target.contents = []
        target.at_desc = Mock(return_value="新房间描述")
        cmd.search = Mock(return_value=target)
        
        result = await cmd.execute()
        assert result.success is True
        assert cmd.caller.location == target


class TestCmdInventory:
    """背包命令测试."""

    @pytest.mark.asyncio
    async def test_inventory_no_caller(self):
        """测试无调用者."""
        cmd = CmdInventory()
        result = await cmd.execute()
        assert result.success is False

    @pytest.mark.asyncio
    async def test_inventory_empty(self):
        """测试空背包."""
        cmd = CmdInventory()
        cmd.caller = Mock()
        cmd.caller.contents = []
        
        result = await cmd.execute()
        assert result.success is True

    @pytest.mark.asyncio
    async def test_inventory_with_items(self):
        """测试有物品的背包."""
        cmd = CmdInventory()
        cmd.caller = Mock()
        
        item1 = Mock()
        item1.key = "剑"
        item2 = Mock()
        item2.key = "药水"
        cmd.caller.contents = [item1, item2]
        
        result = await cmd.execute()
        assert result.success is True


class TestCmdCreate:
    """创建命令测试."""

    @pytest.mark.asyncio
    async def test_create_no_caller(self):
        """测试无调用者."""
        cmd = CmdCreate()
        result = await cmd.execute()
        assert result.success is False

    @pytest.mark.asyncio
    async def test_create_no_args(self):
        """测试无参数."""
        cmd = CmdCreate()
        cmd.caller = Mock()
        cmd.args = ""
        
        result = await cmd.execute()
        assert result.success is False

    @pytest.mark.asyncio
    async def test_create_success(self):
        """测试成功创建."""
        cmd = CmdCreate()
        cmd.caller = Mock()
        cmd.caller._manager = AsyncMock()
        cmd.caller.location = Mock()
        cmd.args = "测试对象"
        
        new_obj = Mock()
        new_obj.key = "测试对象"
        new_obj.id = 123
        cmd.caller._manager.create.return_value = new_obj
        
        result = await cmd.execute()
        assert result.success is True

    @pytest.mark.asyncio
    async def test_create_with_typeclass(self):
        """测试指定类型创建."""
        cmd = CmdCreate()
        cmd.caller = Mock()
        cmd.caller._manager = AsyncMock()
        cmd.caller.location = Mock()
        cmd.args = "测试对象 src.engine.core.typeclass.TypeclassBase"
        
        new_obj = Mock()
        new_obj.key = "测试对象"
        new_obj.id = 123
        cmd.caller._manager.create.return_value = new_obj
        
        result = await cmd.execute()
        assert result.success is True

    @pytest.mark.asyncio
    async def test_create_exception(self):
        """测试创建异常."""
        cmd = CmdCreate()
        cmd.caller = Mock()
        cmd.caller._manager = AsyncMock()
        cmd.args = "测试对象"
        
        cmd.caller._manager.create.side_effect = Exception("创建失败")
        
        result = await cmd.execute()
        assert result.success is False


class TestCmdDestroy:
    """删除命令测试."""

    @pytest.mark.asyncio
    async def test_destroy_no_caller(self):
        """测试无调用者."""
        cmd = CmdDestroy()
        result = await cmd.execute()
        assert result.success is False

    @pytest.mark.asyncio
    async def test_destroy_no_args(self):
        """测试无参数."""
        cmd = CmdDestroy()
        cmd.caller = Mock()
        cmd.args = ""
        
        result = await cmd.execute()
        assert result.success is False

    @pytest.mark.asyncio
    async def test_destroy_target_not_found(self):
        """测试目标未找到."""
        cmd = CmdDestroy()
        cmd.caller = Mock()
        cmd.args = "不存在的对象"
        cmd.search = Mock(return_value=None)
        
        result = await cmd.execute()
        assert result.success is False

    @pytest.mark.asyncio
    async def test_destroy_success(self):
        """测试成功删除."""
        cmd = CmdDestroy()
        cmd.caller = Mock()
        cmd.caller._manager = AsyncMock()
        cmd.args = "测试对象"
        
        target = Mock()
        target.key = "测试对象"
        cmd.search = Mock(return_value=target)
        cmd.caller._manager.delete.return_value = True
        
        result = await cmd.execute()
        assert result.success is True

    @pytest.mark.asyncio
    async def test_destroy_failure(self):
        """测试删除失败."""
        cmd = CmdDestroy()
        cmd.caller = Mock()
        cmd.caller._manager = AsyncMock()
        cmd.args = "测试对象"
        
        target = Mock()
        target.key = "测试对象"
        cmd.search = Mock(return_value=target)
        cmd.caller._manager.delete.return_value = False
        
        result = await cmd.execute()
        assert result.success is False


class TestCmdHelp:
    """帮助命令测试."""

    @pytest.mark.asyncio
    async def test_help_no_caller(self):
        """测试无调用者."""
        cmd = CmdHelp()
        result = await cmd.execute()
        assert result.success is False

    @pytest.mark.asyncio
    async def test_help_no_args(self):
        """测试无参数（显示概览）."""
        cmd = CmdHelp()
        cmd.caller = Mock()
        cmd.args = ""
        
        result = await cmd.execute()
        assert result.success is True

    @pytest.mark.asyncio
    async def test_help_with_command(self):
        """测试查看指定命令帮助."""
        cmd = CmdHelp()
        cmd.caller = Mock()
        cmd.args = "look"
        
        result = await cmd.execute()
        assert result.success is True
