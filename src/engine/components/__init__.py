"""组件模式基础设施.

ECS架构的简化实现，用于新功能开发。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.engine.core.typeclass import TypeclassBase


class Component(ABC):
    """组件基类.
    
    所有组件必须继承此类。
    """
    
    def __init__(self, owner: TypeclassBase):
        self.owner = owner
    
    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """获取组件提供的属性.
        
        Returns:
            属性字典
        """
        pass
    
    def on_attach(self):
        """附加到实体时调用."""
        pass
    
    def on_detach(self):
        """从实体移除时调用."""
        pass


class ComponentMixin:
    """组件混入类.
    
    为 TypeclassBase 添加组件支持。
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._components: dict[str, Component] = {}
    
    def add_component(self, name: str, component: Component) -> None:
        """添加组件.
        
        Args:
            name: 组件名称
            component: 组件实例
        """
        self._components[name] = component
        component.on_attach()
    
    def get_component(self, name: str) -> Component | None:
        """获取组件.
        
        Args:
            name: 组件名称
            
        Returns:
            组件实例或None
        """
        return self._components.get(name)
    
    def remove_component(self, name: str) -> Component | None:
        """移除组件.
        
        Args:
            name: 组件名称
            
        Returns:
            被移除的组件或None
        """
        component = self._components.pop(name, None)
        if component:
            component.on_detach()
        return component
    
    def has_component(self, name: str) -> bool:
        """检查是否有指定组件.
        
        Args:
            name: 组件名称
            
        Returns:
            是否存在
        """
        return name in self._components
    
    def get_all_components(self) -> dict[str, Component]:
        """获取所有组件.
        
        Returns:
            组件字典
        """
        return self._components.copy()
    
    def aggregate_stats(self) -> dict[str, Any]:
        """聚合所有组件的属性.
        
        Returns:
            合并后的属性字典
        """
        stats = {}
        for component in self._components.values():
            stats.update(component.get_stats())
        return stats
