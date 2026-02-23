"""武学注册表.

提供武功缓存和查找功能.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.game.typeclasses.wuxue import Kungfu, WuxueType


class WuxueRegistry:
    """武学注册表.
    
    单例模式，提供武功缓存和查找功能.
    """
    
    _instance: Optional["WuxueRegistry"] = None
    _initialized: bool = False
    
    def __new__(cls) -> "WuxueRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if WuxueRegistry._initialized:
            return
        
        self._kungfu_cache: dict[str, "Kungfu"] = {}
        self._by_menpai: dict[str, list[str]] = {}
        self._by_type: dict[str, list[str]] = {}
        WuxueRegistry._initialized = True
    
    @classmethod
    def reset(cls) -> None:
        """重置注册表（用于测试）."""
        if cls._instance:
            cls._instance._kungfu_cache.clear()
            cls._instance._by_menpai.clear()
            cls._instance._by_type.clear()
        cls._instance = None
        cls._initialized = False
    
    def register(self, kungfu: "Kungfu") -> None:
        """注册武功.
        
        Args:
            kungfu: 武功对象
        """
        self._kungfu_cache[kungfu.key] = kungfu
        
        # 按门派索引
        menpai = kungfu.menpai or "none"
        if menpai not in self._by_menpai:
            self._by_menpai[menpai] = []
        if kungfu.key not in self._by_menpai[menpai]:
            self._by_menpai[menpai].append(kungfu.key)
        
        # 按类型索引
        wuxue_type = kungfu.wuxue_type.value
        if wuxue_type not in self._by_type:
            self._by_type[wuxue_type] = []
        if kungfu.key not in self._by_type[wuxue_type]:
            self._by_type[wuxue_type].append(kungfu.key)
    
    def get(self, key: str) -> Optional["Kungfu"]:
        """通过key获取武功.
        
        Args:
            key: 武功key
            
        Returns:
            Kungfu对象或None
        """
        return self._kungfu_cache.get(key)
    
    def get_by_menpai(self, menpai: str) -> list["Kungfu"]:
        """获取门派所有武功.
        
        Args:
            menpai: 门派名
            
        Returns:
            武功列表
        """
        keys = self._by_menpai.get(menpai, [])
        return [self._kungfu_cache[k] for k in keys if k in self._kungfu_cache]
    
    def get_by_type(self, wuxue_type: "WuxueType") -> list["Kungfu"]:
        """获取类型所有武功.
        
        Args:
            wuxue_type: 武学类型
            
        Returns:
            武功列表
        """
        keys = self._by_type.get(wuxue_type.value, [])
        return [self._kungfu_cache[k] for k in keys if k in self._kungfu_cache]
    
    def get_all(self) -> list["Kungfu"]:
        """获取所有武功.
        
        Returns:
            武功列表
        """
        return list(self._kungfu_cache.values())
    
    def has(self, key: str) -> bool:
        """检查是否存在.
        
        Args:
            key: 武功key
            
        Returns:
            是否存在
        """
        return key in self._kungfu_cache
    
    def clear(self) -> None:
        """清空缓存."""
        self._kungfu_cache.clear()
        self._by_menpai.clear()
        self._by_type.clear()


# 全局访问点
_registry: Optional[WuxueRegistry] = None


def get_wuxue_registry() -> WuxueRegistry:
    """获取武学注册表实例."""
    global _registry
    if _registry is None:
        _registry = WuxueRegistry()
    return _registry


def register_kungfu(kungfu: "Kungfu") -> None:
    """注册武功（便捷函数）."""
    get_wuxue_registry().register(kungfu)


def get_kungfu(key: str) -> Optional["Kungfu"]:
    """获取武功（便捷函数）."""
    return get_wuxue_registry().get(key)


def reset_wuxue_registry() -> None:
    """重置注册表（测试用）."""
    global _registry
    WuxueRegistry.reset()
    _registry = None
