"""游戏引擎核心模块.

提供MUD游戏的基础引擎功能，包括:
- 核心基类(BaseObject, BaseRoom等)
- 游戏对象管理
- 命令系统
- 事件调度
- 数据库层
"""

from src.engine.core.engine import GameEngine, create_engine, get_engine

__all__ = [
    "GameEngine",
    "create_engine",
    "get_engine",
]
