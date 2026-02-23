# 核心引擎 API 文档

> 本文档描述金庸武侠MUD引擎的核心API接口。

---

## 目录

- [GameEngine](#gameengine) - 游戏引擎主类
- [TypeclassBase](#typeclassbase) - 类型类基类
- [ObjectManager](#objectmanager) - 对象管理器
- [CommandHandler](#commandhandler) - 命令处理器
- [EventScheduler](#eventscheduler) - 事件调度器
- [MessageBus](#messagebus) - 消息总线

---

## GameEngine

游戏引擎主类，负责协调所有子系统。

### 位置

`src/engine/core/engine.py`

### 类定义

```python
class GameEngine:
    """游戏引擎主类。"""
```

### 构造函数

```python
def __init__(self, config: Config | None = None)
```

| 参数 | 类型 | 说明 |
|:---|:---|:---|
| `config` | `Config \| None` | 配置对象，使用默认配置时为None |

### 属性

| 属性 | 类型 | 说明 |
|:---|:---|:---|
| `config` | `Config` | 引擎配置 |
| `db` | `DatabaseManager` | 数据库管理器 |
| `objects` | `ObjectManager` | 对象管理器 |
| `commands` | `CommandHandler` | 命令处理器 |
| `events` | `EventScheduler` | 事件调度器 |

### 方法

#### initialize

```python
async def initialize(self) -> None
```

初始化引擎，按顺序初始化数据库、对象管理器、命令处理器和事件调度器。

**Raises:**
- `RuntimeError`: 引擎已初始化时抛出

**示例:**
```python
engine = GameEngine(config)
await engine.initialize()
```

---

#### start

```python
async def start(self) -> None
```

启动引擎，开始事件循环和自动保存。

**Raises:**
- `RuntimeError`: 引擎未初始化或已运行时抛出

---

#### stop

```python
async def stop(self) -> None
```

停止引擎，保存所有数据并清理资源。

---

#### process_input

```python
async def process_input(self, session_id: str, text: str) -> str
```

处理玩家输入。

| 参数 | 类型 | 说明 |
|:---|:---|:---|
| `session_id` | `str` | 会话ID |
| `text` | `str` | 输入文本 |

| 返回 | 说明 |
|:---|:---|
| `str` | 处理结果消息 |

---

## TypeclassBase

类型类基类，所有游戏对象的基类。

### 位置

`src/engine/core/typeclass.py`

### 类定义

```python
class TypeclassBase:
    """类型类基类。"""
    typeclass_path: str = "src.engine.core.typeclass.TypeclassBase"
```

### 构造函数

```python
def __init__(self, manager: ObjectManager, db_model: ObjectModel)
```

| 参数 | 类型 | 说明 |
|:---|:---|:---|
| `manager` | `ObjectManager` | 对象管理器 |
| `db_model` | `ObjectModel` | 数据库模型 |

### 属性

| 属性 | 类型 | 说明 |
|:---|:---|:---|
| `id` | `int` | 对象唯一ID |
| `key` | `str` | 对象标识名 |
| `db` | `AttributeHandler` | 属性处理器 |
| `location` | `TypeclassBase \| None` | 所在位置 |
| `contents` | `list[TypeclassBase]` | 包含的对象列表 |

### 方法

#### at_init

```python
def at_init(self) -> None
```

对象初始化时调用（首次创建时）。子类可重写此方法。

---

#### at_before_move

```python
def at_before_move(self, destination: TypeclassBase | None) -> bool
```

移动前钩子，返回False可取消移动。

---

#### at_after_move

```python
def at_after_move(self, source: TypeclassBase | None) -> None
```

移动后钩子。

---

#### at_delete

```python
def at_delete(self) -> None
```

对象删除时调用。

---

#### msg

```python
def msg(self, text: str, **kwargs) -> None
```

向对象发送消息。

| 参数 | 类型 | 说明 |
|:---|:---|:---|
| `text` | `str` | 消息文本 |

---

## ObjectManager

对象管理器，负责游戏对象的创建、加载、缓存和保存。

### 位置

`src/engine/objects/manager.py`

### 类定义

```python
class ObjectManager:
    """对象管理器。"""
```

### 方法

#### create

```python
async def create(
    self,
    typeclass_path: str,
    key: str,
    location: TypeclassBase | None = None,
    attributes: dict[str, Any] | None = None,
    **kwargs
) -> TypeclassBase
```

创建新对象。

| 参数 | 类型 | 说明 |
|:---|:---|:---|
| `typeclass_path` | `str` | 类型类路径 |
| `key` | `str` | 对象标识名 |
| `location` | `TypeclassBase \| None` | 初始位置 |
| `attributes` | `dict[str, Any] \| None` | 初始属性 |

| 返回 | 说明 |
|:---|:---|
| `TypeclassBase` | 创建的对象实例 |

**示例:**
```python
room = await engine.objects.create(
    typeclass_path="src.game.typeclasses.room.Room",
    key="扬州城",
    attributes={"desc": "繁华的扬州城"}
)
```

---

#### get

```python
async def get(self, obj_id: int) -> TypeclassBase | None
```

通过ID获取对象（带缓存）。

---

#### find

```python
async def find(
    self,
    key: str | None = None,
    typeclass_path: str | None = None,
    location: TypeclassBase | None = None,
    **filters
) -> list[TypeclassBase]
```

条件查询对象。

---

#### save

```python
async def save(self, obj: TypeclassBase) -> None
```

保存单个对象。

---

#### delete

```python
async def delete(self, obj: TypeclassBase | int) -> None
```

删除对象。

---

## CommandHandler

命令处理器，负责解析和执行玩家命令。

### 位置

`src/engine/commands/handler.py`

### 类定义

```python
class CommandHandler:
    """命令处理器。"""
```

### 方法

#### handle

```python
async def handle(
    self,
    caller: TypeclassBase,
    text: str,
    cmdset: CmdSet | None = None
) -> CommandResult
```

处理命令输入。

| 参数 | 类型 | 说明 |
|:---|:---|:---|
| `caller` | `TypeclassBase` | 命令调用者 |
| `text` | `str` | 输入文本 |
| `cmdset` | `CmdSet \| None` | 可选的命令集 |

| 返回 | 说明 |
|:---|:---|
| `CommandResult` | 命令执行结果 |

---

## EventScheduler

事件调度器，管理延迟执行的事件。

### 位置

`src/engine/events/scheduler.py`

### 类定义

```python
class EventScheduler:
    """事件调度器。"""
```

### 方法

#### schedule

```python
def schedule(
    self,
    callback: Callable,
    delay: float,
    *args,
    **kwargs
) -> str
```

调度延迟事件。

| 参数 | 类型 | 说明 |
|:---|:---|:---|
| `callback` | `Callable` | 回调函数 |
| `delay` | `float` | 延迟时间（秒） |

| 返回 | 说明 |
|:---|:---|
| `str` | 事件ID |

---

#### schedule_recurring

```python
def schedule_recurring(
    self,
    callback: Callable,
    interval: float,
    *args,
    **kwargs
) -> str
```

调度周期事件。

---

#### cancel

```python
def cancel(self, event_id: str) -> bool
```

取消事件。

---

## MessageBus

消息总线，负责引擎与GUI之间的消息传递。

### 位置

`src/engine/core/messages.py`

### 类定义

```python
class MessageBus:
    """消息总线。"""
```

### 方法

#### subscribe

```python
def subscribe(
    self,
    msg_type: MessageType | str,
    handler: Callable
) -> str
```

订阅消息。

| 参数 | 类型 | 说明 |
|:---|:---|:---|
| `msg_type` | `MessageType \| str` | 消息类型 |
| `handler` | `Callable` | 消息处理器 |

| 返回 | 说明 |
|:---|:---|
| `str` | 订阅ID |

---

#### emit

```python
def emit(self, message: Message) -> None
```

发送消息。

---

#### emit_text

```python
def emit_text(
    self,
    msg_type: str,
    content: str,
    **kwargs
) -> None
```

发送文本消息（便捷方法）。

---

## 全局函数

### create_engine

```python
def create_engine(config: Config | None = None) -> GameEngine
```

创建全局引擎实例。

---

### get_engine

```python
def get_engine() -> GameEngine
```

获取全局引擎实例。

---

### get_message_bus

```python
def get_message_bus() -> MessageBus
```

获取全局消息总线实例。
