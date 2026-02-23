"""寻路系统扩展单元测试.

补充 pathfinding.py 中未覆盖的功能测试.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from src.game.typeclasses.room import Room
from src.game.world.pathfinding import PathFinder


class TestPathFinderFindPathToKey:
    """PathFinder.find_path_to_key 测试."""

    @pytest.mark.asyncio
    async def test_find_path_to_key_found(self):
        """测试根据key找到路径."""
        mock_loader = Mock()
        
        # 创建起始房间
        start_room = Mock(spec=Room)
        start_room.id = 1
        start_room.coords = (0, 0, 0)
        start_room.get_exits.return_value = []
        
        finder = PathFinder(mock_loader)
        
        # 模拟找到目标房间（与起始房间相同id，直接返回空路径）
        target_room = Mock(spec=Room)
        target_room.id = 1  # 相同id
        target_room.key = "目标房间"
        target_room.coords = (0, 0, 0)
        
        mock_loader.find = AsyncMock(return_value=[target_room])
        mock_loader.get = Mock(return_value=start_room)
        
        # 同一房间返回空路径
        result = await finder.find_path_to_key(start_room, "目标房间")
        assert result == []

    @pytest.mark.asyncio
    async def test_find_path_to_key_not_found(self):
        """测试根据key未找到房间."""
        mock_loader = Mock()
        
        start_room = Mock(spec=Room)
        start_room.id = 1
        start_room.coords = (0, 0, 0)
        
        finder = PathFinder(mock_loader)
        mock_loader.find = AsyncMock(return_value=[])
        
        result = await finder.find_path_to_key(start_room, "不存在的房间")
        assert result is None


class TestPathFinderFindPathToCoords:
    """PathFinder.find_path_to_coords 测试."""

    @pytest.mark.asyncio
    async def test_find_path_to_coords_found(self):
        """测试根据坐标找到路径."""
        mock_loader = Mock()
        
        # 创建起始房间
        start_room = Mock(spec=Room)
        start_room.id = 1
        start_room.coords = (0, 0, 0)
        start_room.get_exits.return_value = []
        
        finder = PathFinder(mock_loader)
        
        # 创建目标房间（相同坐标）
        target_room = Mock(spec=Room)
        target_room.id = 1  # 相同ID
        target_room.coords = (0, 0, 0)
        
        mock_loader.find = AsyncMock(return_value=[start_room])
        
        result = await finder.find_path_to_coords(start_room, (0, 0, 0))
        assert result == []

    @pytest.mark.asyncio
    async def test_find_path_to_coords_not_found(self):
        """测试根据坐标未找到房间."""
        mock_loader = Mock()
        
        start_room = Mock(spec=Room)
        start_room.id = 1
        start_room.coords = (0, 0, 0)
        
        finder = PathFinder(mock_loader)
        mock_loader.find = AsyncMock(return_value=[])
        
        result = await finder.find_path_to_coords(start_room, (999, 999, 999))
        assert result is None


class TestPathFinderEdgeCases:
    """寻路边界情况测试."""

    @pytest.mark.asyncio
    async def test_find_path_no_manager_for_neighbor(self):
        """测试邻居房间无manager时的路径查找."""
        mock_loader = Mock()
        mock_loader.get = Mock(return_value=None)
        
        # 创建起始房间
        start_room = Mock(spec=Room)
        start_room.id = 1
        start_room.coords = (0, 0, 0)
        
        # 创建出口指向不存在的房间
        mock_exit = Mock()
        mock_exit.direction = "n"
        mock_exit.destination_id = 999
        mock_exit.destination = None  # 无目的地
        
        start_room.get_exits.return_value = [mock_exit]
        
        finder = PathFinder(mock_loader)
        
        # 目标房间（需要移动才能到达）
        goal_room = Mock(spec=Room)
        goal_room.id = 2
        goal_room.coords = (1, 0, 0)
        
        # 由于无法到达目标，应该返回None
        result = await finder.find_path(start_room, goal_room)
        assert result is None
