# 代码模板

## AttributeHandler 模板

```python
# src/engine/core/typeclass.py
from typing import Any, Type, Optional, TYPE_CHECKING
import importlib

if TYPE_CHECKING:
    from src.engine.core.objects import ObjectManager


class AttributeHandler:
    """JSON属性代理处理器。
    
    提供对数据库JSON attributes字段的透明访问，
    自动处理序列化和脏数据标记。
    
    Attributes:
        _obj: 关联的TypeclassBase实例
        _cache: 本地属性缓存
    """
    
    def __init__(self, obj: "TypeclassBase") -> None:
        self._obj = obj
        self._cache: dict[str, Any] = {}
    
    def __getattr__(self, name: str) -> Any:
        """获取属性值。
        
        优先从缓存获取，否则从数据库模型获取。
        
        Args:
            name: 属性名
            
        Returns:
            属性值，不存在返回None
        """
        if name in self._cache:
            return self._cache[name]
        
        attrs = self._obj._db_model.attributes or {}
        value = attrs.get(name)
        self._cache[name] = value
        return value
    
    def __setattr__(self, name: str, value: Any) -> None:
        """设置属性值，自动标记脏数据。"""
        if name.startswith("_"):
            super().__setattr__(name, value)
            return
        
        self._cache[name] = value
        self._obj.mark_dirty()
        
        # 同步到数据库模型
        if self._obj._db_model.attributes is None:
            self._obj._db_model.attributes = {}
        self._obj._db_model.attributes[name] = value
```

## TypeclassBase 模板

```python
# src/engine/core/typeclass.py
from typing import Any, ClassVar
from abc import ABC


class TypeclassBase(ABC):
    """MUD对象基类。
    
    提供Typeclass系统的核心功能：
    - 动态类加载
    - 属性代理访问
    - 生命周期钩子
    - 脏数据标记
    
    Attributes:
        typeclass_path: 类路径，用于动态加载
    """
    
    typeclass_path: ClassVar[str] = ""
    
    def __init__(self, db_model: Any) -> None:
        """初始化Typeclass实例。
        
        Args:
            db_model: 数据库模型实例
        """
        self._db_model = db_model
        self._is_dirty = False
        self.db = AttributeHandler(self)
        self.at_init()
    
    def mark_dirty(self) -> None:
        """标记对象为脏数据，需要保存。"""
        self._is_dirty = True
    
    def is_dirty(self) -> bool:
        """检查对象是否被修改。"""
        return self._is_dirty
    
    def save(self) -> None:
        """保存对象到数据库。"""
        # 实现保存逻辑
        self._is_dirty = False
    
    # 生命周期钩子
    def at_init(self) -> None:
        """初始化时调用。"""
        pass
    
    def at_delete(self) -> None:
        """删除前调用。"""
        pass
    
    def at_move(self, destination: Any) -> None:
        """移动到新位置时调用。
        
        Args:
            destination: 目标位置
        """
        pass
```

## Command 模板

```python
# src/engine/commands/base.py
from typing import Any, ClassVar
from abc import ABC, abstractmethod


class Command(ABC):
    """命令基类。
    
    所有MUD命令的基类，定义命令的基本结构和执行流程。
    
    Attributes:
        key: 命令主键
        aliases: 命令别名列表
        locks: 权限锁字符串
        help_text: 帮助文本
    """
    
    key: ClassVar[str] = ""
    aliases: ClassVar[list[str]] = []
    locks: ClassVar[str] = ""
    help_text: ClassVar[str] = ""
    
    def __init__(self, caller: Any, cmd_string: str, args: str) -> None:
        """初始化命令实例。
        
        Args:
            caller: 命令执行者
            cmd_string: 输入的命令字符串
            args: 命令参数
        """
        self.caller = caller
        self.cmd_string = cmd_string
        self.args = args
    
    @abstractmethod
    def execute(self) -> None:
        """执行命令。子类必须实现。"""
        pass
    
    def check_access(self) -> bool:
        """检查执行权限。"""
        # 实现权限检查逻辑
        return True
```

## CmdSet 模板

```python
# src/engine/commands/cmdset.py
from typing import Type
from .base import Command


class CmdSet:
    """命令集合。
    
    管理一组命令，支持优先级合并。
    """
    
    def __init__(self) -> None:
        self.commands: dict[str, Type[Command]] = {}
        self.priority = 0
    
    def add(self, cmd_class: Type[Command]) -> None:
        """添加命令类。
        
        Args:
            cmd_class: 命令类
        """
        self.commands[cmd_class.key] = cmd_class
        for alias in cmd_class.aliases:
            self.commands[alias] = cmd_class
    
    def remove(self, key: str) -> None:
        """移除命令。"""
        if key in self.commands:
            del self.commands[key]
    
    def merge(self, other: "CmdSet") -> "CmdSet":
        """合并另一个CmdSet，高优先级覆盖低优先级。
        
        Args:
            other: 另一个命令集合
            
        Returns:
            合并后的新集合
        """
        result = CmdSet()
        if self.priority >= other.priority:
            result.commands.update(other.commands)
            result.commands.update(self.commands)
        else:
            result.commands.update(self.commands)
            result.commands.update(other.commands)
        return result
```
