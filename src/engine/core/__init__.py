"""引擎核心模块."""

from src.engine.core.engine import GameEngine, create_engine, get_engine
from src.engine.core.typeclass import (
    AttributeHandler,
    TypeclassBase,
    TypeclassLoader,
    TypeclassMeta,
)

__all__ = [
    "GameEngine",
    "create_engine",
    "get_engine",
    "AttributeHandler",
    "TypeclassBase",
    "TypeclassLoader",
    "TypeclassMeta",
]
"""引擎核心基类模块.

提供游戏引擎的基础类和接口。
"""
