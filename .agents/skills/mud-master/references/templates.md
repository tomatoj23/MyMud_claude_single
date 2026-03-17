> 使用说明：
> - 模板只作为脚手架参考；优先对齐当前仓库已有文件名和模块布局。
> - 例如命令基类当前实际在 `src/engine/commands/command.py`，不是独立的 `base.py`。

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

当前仓库已经有 `src/engine/commands/command.py` 基类。新增命令时优先写子类，不要重新实现基础命令框架：

```python
# src/game/commands/cmd_look.py
from src.engine.commands.command import Command, CommandResult
from src.engine.core.messages import MessageType


class CmdLook(Command):
    """查看当前环境。"""

    key = "look"
    aliases = ["l"]
    help_category = "general"
    help_text = "查看当前房间和周围对象。"

    def parse(self) -> bool:
        self.target_name = self.args.strip()
        return True

    async def execute(self) -> CommandResult:
        if self.caller is None:
            return CommandResult(False, "调用者未设置")

        self.msg("你环顾四周。", MessageType.INFO)
        return CommandResult(True, "查看完成")
```

运行时字段 `caller`、`args`、`cmdstring`、`session` 由命令处理器或测试在实例化后填充。

## CmdSet 模板

```python
# src/engine/commands/cmdset.py
from typing import Type
from .command import Command


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


