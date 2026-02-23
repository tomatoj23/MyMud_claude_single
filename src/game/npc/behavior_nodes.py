"""NPC行为树节点实现.

实现TD-002~008的NPC智能功能.
"""

from __future__ import annotations

import random
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import NPC
    from src.game.typeclasses.character import Character


class GameTime:
    """游戏时间系统（简化版）."""
    
    @staticmethod
    def get_current_hour() -> int:
        """获取当前小时（0-23）."""
        # 简化实现：使用现实时间
        return datetime.now().hour
    
    @staticmethod
    def is_night() -> bool:
        """检查是否是夜晚（20:00 - 06:00）."""
        hour = GameTime.get_current_hour()
        return hour >= 20 or hour < 6


class NPCUtils:
    """NPC工具函数."""
    
    @staticmethod
    def get_distance(pos1: tuple, pos2: tuple) -> float:
        """计算两点距离."""
        if not pos1 or not pos2:
            return float('inf')
        return sum((a - b) ** 2 for a, b in zip(pos1, pos2)) ** 0.5
    
    @staticmethod
    def get_room_coordinates(room) -> tuple | None:
        """获取房间坐标."""
        if not room:
            return None
        # 从房间key解析坐标，或使用房间属性
        if hasattr(room, 'coordinates'):
            return room.coordinates
        if hasattr(room, 'x') and hasattr(room, 'y'):
            return (room.x, room.y, getattr(room, 'z', 0))
        return None
    
    @staticmethod
    def get_nearby_players(npc: "NPC", range_distance: float = 10.0) -> list["Character"]:
        """获取附近的玩家.
        
        Args:
            npc: NPC对象
            range_distance: 范围距离
            
        Returns:
            玩家列表
        """
        players = []
        
        # 检查当前位置
        location = npc.location
        if not location:
            return players
        
        # 获取位置中的内容
        if hasattr(location, 'contents'):
            for obj in location.contents:
                # 检查是否是玩家（有is_player属性或者是Character类型）
                if hasattr(obj, 'is_player') and obj.is_player:
                    players.append(obj)
                elif isinstance(obj, Character):
                    players.append(obj)
        
        # 检查相邻房间（简化实现，只检查当前房间）
        npc_coords = NPCUtils.get_room_coordinates(location)
        if npc_coords:
            # 检查相邻房间的玩家
            if hasattr(location, 'exits'):
                for exit_obj in location.exits:
                    if exit_obj.destination:
                        dest_coords = NPCUtils.get_room_coordinates(exit_obj.destination)
                        if dest_coords:
                            dist = NPCUtils.get_distance(npc_coords, dest_coords)
                            if dist <= range_distance:
                                # 检查目的地中的玩家
                                if hasattr(exit_obj.destination, 'contents'):
                                    for obj in exit_obj.destination.contents:
                                        if hasattr(obj, 'is_player') and obj.is_player:
                                            players.append(obj)
        
        return players


class MovementController:
    """移动控制器."""
    
    @staticmethod
    async def move_to(npc: "NPC", target_key: str) -> bool:
        """移动到目标房间.
        
        Args:
            npc: NPC对象
            target_key: 目标房间key
            
        Returns:
            是否成功移动
        """
        try:
            # 获取对象管理器
            from src.engine.objects.manager import ObjectManager
            manager = ObjectManager()
            
            # 查找目标房间
            target_room = await manager.find_one(key=target_key)
            if not target_room:
                return False
            
            # 设置新位置
            npc.location = target_room
            return True
            
        except Exception:
            return False
    
    @staticmethod
    async def move_randomly(npc: "NPC") -> bool:
        """随机移动到相邻房间.
        
        Args:
            npc: NPC对象
            
        Returns:
            是否成功移动
        """
        location = npc.location
        if not location:
            return False
        
        # 获取可用出口
        if not hasattr(location, 'exits'):
            return False
        
        exits = [e for e in location.exits if e.destination]
        if not exits:
            return False
        
        # 随机选择出口
        chosen_exit = random.choice(exits)
        
        # 移动
        npc.location = chosen_exit.destination
        return True
    
    @staticmethod
    def get_distance_to_home(npc: "NPC") -> float:
        """获取与出生点的距离.
        
        Args:
            npc: NPC对象
            
        Returns:
            距离（如果没有坐标返回无穷大）
        """
        home_key = npc.home_location
        if not home_key:
            return 0.0  # 没有家，视为在家
        
        current_location = npc.location
        if not current_location:
            return float('inf')
        
        # 获取当前坐标
        current_coords = NPCUtils.get_room_coordinates(current_location)
        if not current_coords:
            # 无法获取坐标，检查是否在同一房间
            if hasattr(current_location, 'key') and current_location.key == home_key:
                return 0.0
            return float('inf')
        
        # 获取家的坐标
        try:
            from src.engine.objects.manager import ObjectManager
            manager = ObjectManager()
            home_room = manager.get_by_key(home_key)
            if not home_room:
                return float('inf')
            
            home_coords = NPCUtils.get_room_coordinates(home_room)
            if not home_coords:
                return float('inf')
            
            return NPCUtils.get_distance(current_coords, home_coords)
            
        except Exception:
            return float('inf')


class CombatChecker:
    """战斗状态检查器."""
    
    @staticmethod
    def is_in_combat(npc: "NPC") -> bool:
        """检查NPC是否在战斗中.
        
        Args:
            npc: NPC对象
            
        Returns:
            是否在战斗中
        """
        # 检查combat_session属性
        if hasattr(npc, 'combat_session') and npc.combat_session:
            return True
        
        # 检查fighting属性
        if hasattr(npc, 'fighting') and npc.fighting:
            return True
        
        # 检查is_in_combat方法
        if hasattr(npc, 'is_in_combat') and callable(npc.is_in_combat):
            try:
                return npc.is_in_combat()
            except Exception:
                pass
        
        return False
