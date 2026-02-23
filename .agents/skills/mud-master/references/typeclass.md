# Typeclass系统实现指南

## 核心概念

Typeclass系统是MUD引擎的核心，提供：

1. **动态类加载** - 通过字符串路径动态加载类
2. **属性代理** - 透明访问数据库JSON字段
3. **生命周期管理** - 初始化、删除、移动的钩子
4. **脏数据追踪** - 自动标记修改的对象

## 实现要点

### 1. AttributeHandler

- 使用 `__getattr__` 和 `__setattr__` 实现属性代理
- 本地缓存减少数据库访问
- 设置属性时自动调用 `mark_dirty()`

### 2. 动态类加载

```python
import importlib

def load_typeclass(path: str) -> Type[TypeclassBase]:
    """从路径加载Typeclass类。
    
    Args:
        path: 模块路径，如 "src.objects.characters.Character"
        
    Returns:
        Typeclass类
    """
    module_path, class_name = path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)
```

### 3. 生命周期钩子

子类可以重写以下方法：

- `at_init()` - 对象初始化后调用
- `at_delete()` - 对象删除前调用
- `at_move(destination)` - 对象移动到新位置时调用

### 4. 脏数据机制

- 每次属性修改调用 `mark_dirty()`
- ObjectManager定期保存脏数据对象
- 支持批量保存优化性能

## 注意事项

1. 避免循环引用，使用 `weakref` 做缓存
2. 属性名不要以下划线开头（内部保留）
3. 数据库模型需要包含 `attributes` JSON字段
