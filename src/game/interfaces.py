"""游戏对象协议接口.

定义核心抽象，避免循环导入问题.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from src.game.typeclasses.room import Room


@runtime_checkable
class Position(Protocol):
    """位置协议."""
    x: int
    y: int
    z: int


@runtime_checkable
class Combatant(Protocol):
    """战斗参与者协议."""
    
    @property
    def name(self) -> str: ...
    
    @property
    def key(self) -> str: ...
    
    @property
    def hp(self) -> tuple[int, int]: ...
    
    @property
    def mp(self) -> tuple[int, int]: ...
    
    def modify_hp(self, delta: int) -> int: ...
    
    def modify_mp(self, delta: int) -> int: ...
    
    def get_attack(self) -> int: ...
    
    def get_defense(self) -> int: ...


@runtime_checkable
class ItemHolder(Protocol):
    """物品持有者协议."""
    
    def get_current_weight(self) -> int: ...
    
    def get_max_weight(self) -> int: ...
    
    def can_carry(self, item) -> tuple[bool, str]: ...


@runtime_checkable
class Movable(Protocol):
    """可移动对象协议."""
    
    async def move_to(self, destination: Room) -> bool: ...
    
    @property
    def location(self) -> Room | None: ...
