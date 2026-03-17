# 金庸武侠文字MUD单机版 - 详细开发计划

> 基于Evennia 6.0架构思想的单机化改造方案

---

## 📊 项目总览

### 当前状态（2026-03-17更新）

| 阶段 | 名称 | 时间 | 状态 | 完成度 |
|:---:|:---|:---:|:---:|:---:|
| 阶段一 | 引擎核心搭建 | 第1-3周 | ✅ 已完成 | 100% |
| 阶段二 | 武侠世界构建 | 第4-5周 | ✅ 已完成 | 100% |
| 阶段三 | 玩法系统实现 | 第6-8周 | ✅ 已完成 | 100% |
| 架构改进 | 债务清偿 | - | ✅ 已完成 | 51/51 |
| **里程碑** | **master合并** | **2026-02-26** | **✅ 已完成** | **-** |
| 阶段四 | GUI客户端 | 第9-12周 | 🔄 进行中 | 60% |
| 阶段五 | 内容制作 | 第13-15周 | ⏳ 待开始 | 0% |
| 阶段六 | 存档与系统功能 | 第16-17周 | ⏳ 待开始 | 0% |

### 关键指标

| 指标 | 数值 | 说明 |
|:---|:---:|:---|
| **测试总数** | 1,812 | 单元测试 + 集成测试 |
| **测试通过率** | 100% | 全部通过 |
| **技术债务** | 0 | 51项全部清偿 |
| **代码覆盖率** | ~90% | 核心模块 |
| **GUI测试** | 29 | 新增GUI专项测试 |

### 最近里程碑

**2026-03-17: Phase 4 GUI Backlog 完成 4/8**
- 完成任务:
  - B4-GUI-001: 右侧信息面板（地图/任务/装备/背包）
  - B4-GUI-002: 主题系统（dark/light QSS主题）
  - B4-GUI-003: 快捷键支持（6个快捷键）
  - B4-GUI-004: 存档/读档 GUI（MessagePack + Gzip）
- 新增文件: 11个（~2,200行代码）
- 新增测试: 29个（全部通过）
- GUI可正常启动运行

**2026-02-26: 架构改进分支合并完成**
- 合并分支: `refactor/phase1-combat-transaction` → `master`
- 合并提交: `83c8a33`
- 主要交付:
  - 战斗事务保护机制
  - 策略模式重构
  - 混沌测试套件
  - 技术债务全部清偿
  - contents同步属性修复

---

## 项目概述

### 核心目标
开发一款单机版金庸武侠文字MUD游戏，融合经典MUD的深度玩法与现代GUI的交互体验。

### 技术栈
| 层级 | 技术选型 |
|:---|:---|
| 游戏引擎 | Python 3.11+, asyncio, SQLAlchemy 2.0 |
| 数据库 | SQLite (WAL模式) |
| GUI框架 | PySide6 + qasync |
| 打包工具 | PyInstaller |

---

## 阶段一：引擎核心搭建（第1-3周）

### 阶段目标
建立单机版MUD引擎的基础框架，实现对象管理、命令处理、事件调度三大核心系统。本阶段结束时，应能通过命令行与引擎进行基本的对象创建、移动、查看等交互。

---

### 1.1 项目骨架搭建（第1周）

#### 1.1.1 目录结构与基础配置

**任务清单：**
- [ ] 创建完整项目目录结构
- [ ] 初始化Git仓库，配置`.gitignore`
- [ ] 创建`pyproject.toml`或`requirements.txt`
- [ ] 配置开发工具：Black、Ruff、Mypy
- [ ] 编写`Makefile`或`task.py`开发脚本

**目录结构详情：**
```
jinyong_mud/
├── src/
│   ├── engine/              # 游戏引擎核心
│   │   ├── __init__.py
│   │   ├── core/            # 核心基类
│   │   ├── objects/         # 游戏对象
│   │   ├── commands/        # 命令系统
│   │   ├── events/          # 事件调度
│   │   └── database/        # 数据库层
│   ├── gui/                 # PySide6图形界面
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── panels/          # 各功能面板
│   │   └── themes/          # QSS样式主题
│   ├── game/                # 游戏具体实现
│   │   ├── typeclasses/     # 武侠特色类型类
│   │   ├── commands/        # 游戏命令
│   │   └── world/           # 世界数据
│   └── utils/               # 工具函数
├── tests/                   # 单元测试
│   ├── unit/               # 单元测试
│   └── integration/        # 集成测试
├── docs/                    # 文档
├── tools/                   # 开发工具
├── resources/               # 资源文件
│   ├── images/
│   ├── sounds/
│   └── data/               # 初始数据
└── scripts/                 # 辅助脚本
```

**依赖配置（pyproject.toml）：**
```toml
[tool.poetry.dependencies]
python = "^3.11"
SQLAlchemy = {version = "^2.0", extras = ["asyncio"]}
aiosqlite = "^0.19"
PySide6 = "^6.6"
qasync = "^0.27"
msgpack = "^1.0"
jieba = "^0.42"
alembic = "^1.13"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4"
pytest-asyncio = "^0.21"
black = "^23.0"
ruff = "^0.1"
mypy = "^1.7"
```

**验收标准：**
- 运行`pip install -e .`可成功安装
- 运行`ruff check .`无错误
- 运行`black --check .`无格式问题
- Git提交规范检查通过

---

#### 1.1.2 日志与配置系统

**任务清单：**
- [ ] 设计日志配置（按模块分离，文件+控制台双输出）
- [ ] 实现游戏配置管理类（YAML/JSON配置加载）
- [ ] 配置热重载机制（开发模式）
- [ ] 异常捕获与错误报告机制

**核心接口设计：**
```python
# src/utils/logging.py
import logging
from pathlib import Path

def setup_logging(
    level: str = "INFO",
    log_dir: Path = Path("logs"),
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """配置日志系统"""

# src/utils/config.py
from pathlib import Path
from typing import Any

class ConfigManager:
    """游戏配置管理器"""
    
    def __init__(self, config_path: Path)
    def load(self) -> dict[str, Any]
    def get(self, key: str, default: Any = None) -> Any
    def set(self, key: str, value: Any) -> None
    def save(self) -> None
    def watch(self, callback: callable) -> None  # 热重载监听
```

**验收标准：**
- 日志按日期和模块分类存储
- 配置变更后开发模式自动重载
- 未捕获异常自动记录堆栈并保存现场

---

### 1.2 数据库与对象系统（第2周）

#### 1.2.1 SQLite数据库基础设施

**任务清单：**
- [ ] 数据库连接池管理（aiosqlite）
- [ ] WAL模式配置与优化参数
- [ ] 数据库初始化脚本（schema创建）
- [ ] 连接健康检查与自动重连

**核心接口设计：**
```python
# src/engine/database/connection.py
import aiosqlite
from contextlib import asynccontextmanager

class DatabaseManager:
    """异步SQLite连接管理器"""
    
    def __init__(self, db_path: Path)
    async def initialize(self) -> None
    async def close(self) -> None
    
    @asynccontextmanager
    async def session(self) -> AsyncIterator[aiosqlite.Connection]
    
    async def execute(self, sql: str, parameters: tuple = ()) -> aiosqlite.Cursor
    async def executemany(self, sql: str, parameters: list) -> aiosqlite.Cursor
```

**SQLite优化配置：**
```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;  -- 64MB
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456;  -- 256MB
```

**验收标准：**
- 并发读写测试通过（1000次/秒写入）
- 数据库文件损坏时自动恢复或重建
- 连接异常时自动重连

---

#### 1.2.2 ORM模型与实体基类

**任务清单：**
- [ ] SQLAlchemy 2.0 DeclarativeBase配置
- [ ] ObjectModel实体基类表设计
- [ ] 关联关系配置（location/contained）
- [ ] JSON字段索引优化

**数据库模型设计：**
```python
# src/engine/database/models.py
from sqlalchemy import ForeignKey, String, DateTime, JSON, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, Dict, Any

class Base(DeclarativeBase):
    pass

class ObjectModel(Base):
    """游戏对象数据库模型"""
    __tablename__ = "objects"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    typeclass_path: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    
    # 容器关系
    location_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("objects.id", ondelete="SET NULL"), 
        nullable=True, 
        index=True
    )
    
    # 扩展属性（JSON存储）
    attributes: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # 关系
    location: Mapped[Optional["ObjectModel"]] = relationship(
        "ObjectModel", 
        remote_side=[id],
        back_populates="contents"
    )
    contents: Mapped[list["ObjectModel"]] = relationship(
        "ObjectModel",
        back_populates="location"
    )
    
    __table_args__ = (
        Index('idx_typeclass_key', 'typeclass_path', 'key'),
        Index('idx_attributes_gin', 'attributes'),  # SQLite JSON1扩展
    )
```

**验收标准：**
- 所有模型可通过Alembic正确迁移
- JSON查询性能测试（10000条数据<100ms）
- 级联删除行为符合预期

---

#### 1.2.3 Typeclass动态类系统

**任务清单：**
- [ ] Typeclass元类设计（自动注册）
- [ ] AttributeHandler属性代理（db属性访问）
- [ ] 动态类加载机制（importlib）
- [ ] 对象生命周期钩子（at_init, at_delete等）

**核心实现：**
```python
# src/engine/core/typeclass.py
from typing import Any, Type, TYPE_CHECKING
import importlib

if TYPE_CHECKING:
    from src.engine.core.objects import ObjectManager

class AttributeHandler:
    """JSON属性代理处理器"""
    
    def __init__(self, obj: "TypeclassBase")
    def __getattr__(self, name: str) -> Any
    def __setattr__(self, name: str, value: Any) -> None
    def __delattr__(self, name: str) -> None
    def get(self, name: str, default: Any = None) -> Any
    def set(self, name: str, value: Any) -> None
    def all(self) -> dict[str, Any]

class TypeclassBase:
    """游戏对象类型基类"""
    
    typeclass_path: str = "src.engine.core.typeclass.TypeclassBase"
    
    def __init__(self, manager: "ObjectManager", db_model: ObjectModel):
        self.manager = manager
        self._db_model = db_model
        self.db = AttributeHandler(self)
        self._is_dirty = False
    
    # 属性代理
    @property
    def id(self) -> int: return self._db_model.id
    
    @property
    def key(self) -> str: return self._db_model.key
    @key.setter
    def key(self, value: str): 
        self._db_model.key = value
        self._is_dirty = True
    
    # 容器关系
    @property
    def location(self) -> Optional["TypeclassBase"]:
        if self._db_model.location_id:
            return self.manager.get(self._db_model.location_id)
        return None
    
    @location.setter
    def location(self, value: Optional["TypeclassBase"]):
        self._db_model.location_id = value.id if value else None
        self._is_dirty = True
    
    @property
    def contents(self) -> list["TypeclassBase"]:
        return [self.manager.get(c.id) for c in self._db_model.contents]
    
    # 生命周期钩子（子类可重写）
    def at_init(self) -> None: pass
    def at_delete(self) -> None: pass
    def at_move(self, destination: "TypeclassBase") -> bool: return True
    def at_moved(self, source: "TypeclassBase") -> None: pass
    def at_desc(self, looker: "TypeclassBase") -> str: return ""
    
    def mark_dirty(self) -> None: self._is_dirty = True
    def is_dirty(self) -> bool: return self._is_dirty
    def clean_dirty(self) -> None: self._is_dirty = False

class TypeclassMeta(type):
    """Typeclass元类，自动注册类型路径"""
    registry: dict[str, Type[TypeclassBase]] = {}
    
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if hasattr(cls, 'typeclass_path'):
            mcs.registry[cls.typeclass_path] = cls
        return cls

# 动态加载器
class TypeclassLoader:
    """动态类型加载器"""
    
    @staticmethod
    def load(typeclass_path: str) -> Type[TypeclassBase]:
        """从路径加载类型类"""
        # 优先从注册表获取
        if typeclass_path in TypeclassMeta.registry:
            return TypeclassMeta.registry[typeclass_path]
        
        # 动态导入
        module_path, class_name = typeclass_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
```

**验收标准：**
- 动态加载1000个对象<500ms
- db属性修改自动标记dirty
- 新Typeclass无需重启即可加载

---

#### 1.2.4 ObjectManager对象管理器

**任务清单：**
- [ ] L1缓存实现（活跃对象字典）
- [ ] L2缓存实现（LRU缓存查询结果）
- [ ] 批量保存与写时复制
- [ ] 对象创建、删除、查询接口

**核心接口：**
```python
# src/engine/core/objects.py
from functools import lru_cache
from typing import Optional, Type, List
import weakref

class ObjectManager:
    """游戏对象管理器 - L1/L2缓存 + 持久化"""
    
    def __init__(self, db_manager: DatabaseManager)
    
    # L1缓存 - 活跃对象（直接引用）
    _l1_cache: dict[int, weakref.ref[TypeclassBase]]  # id -> weakref
    
    # L2缓存 - 数据库查询结果
    @lru_cache(maxsize=1000)
    async def _get_db_model(self, obj_id: int) -> Optional[ObjectModel]
    
    async def get(self, obj_id: int) -> Optional[TypeclassBase]:
        """获取对象（优先L1缓存）"""
    
    async def create(
        self, 
        typeclass_path: str, 
        key: str, 
        location: Optional[TypeclassBase] = None,
        attributes: Optional[dict] = None
    ) -> TypeclassBase:
        """创建新对象"""
    
    async def delete(self, obj: TypeclassBase) -> None:
        """删除对象"""
    
    async def find(
        self, 
        typeclass_path: Optional[str] = None,
        location: Optional[TypeclassBase] = None,
        key_contains: Optional[str] = None
    ) -> List[TypeclassBase]:
        """条件查询"""
    
    async def save(self, obj: TypeclassBase, force: bool = False) -> None:
        """保存对象状态"""
    
    async def save_all(self) -> int:
        """批量保存所有dirty对象"""
    
    def clear_cache(self) -> None:
        """清理缓存（内存紧张时调用）"""
```

**验收标准：**
- L1缓存命中率>90%
- 1000个对象批量保存<1秒
- 内存占用超过阈值时自动释放非活跃对象

---

### 1.3 命令与事件系统（第3周）

#### 1.3.1 CmdSet命令集合系统

**任务清单：**
- [ ] Command基类设计（权限、别名、冷却）
- [ ] CmdSet集合类（添加、删除、合并）
- [ ] 命令Trie树索引（前缀快速匹配）
- [ ] 权限锁系统（LockFunc）

**核心实现：**
```python
# src/engine/commands/command.py
from typing import Optional, List, Callable
from dataclasses import dataclass

@dataclass
class CommandResult:
    success: bool
    message: str
    data: Optional[dict] = None

class Command:
    """命令基类"""
    
    key: str = ""
    aliases: List[str] = []
    locks: str = ""  # 权限表达式
    help_category: str = "general"
    help_text: str = ""
    
    # 运行时属性
    caller: TypeclassBase
    args: str = ""
    cmdset_source: Optional[str] = None
    
    async def check_locks(self) -> bool:
        """检查权限"""
    
    async def parse(self) -> bool:
        """解析参数，返回是否解析成功"""
        return True
    
    async def execute(self) -> CommandResult:
        """执行命令"""
        raise NotImplementedError
    
    async def run(self) -> CommandResult:
        """完整执行流程"""
        if not await self.check_locks():
            return CommandResult(False, "你没有权限执行此命令。")
        if not await self.parse():
            return CommandResult(False, "参数解析失败。")
        return await self.execute()

# src/engine/commands/cmdset.py
from typing import Set
from collections import OrderedDict

class CmdSet:
    """命令集合"""
    
    key: str = "default"
    priority: int = 0
    
    def __init__(self):
        self.commands: OrderedDict[str, Command] = OrderedDict()
    
    def add(self, cmd_class: Type[Command]) -> None:
        """添加命令类"""
    
    def remove(self, cmd_key: str) -> None:
        """移除命令"""
    
    def merge(self, other: "CmdSet") -> "CmdSet":
        """合并两个命令集（优先级处理冲突）"""
    
    def get_match(self, cmdline: str) -> Optional[Command]:
        """根据输入匹配命令（Trie树前缀匹配）"""
    
    def all(self) -> List[Command]:
        """获取所有命令"""
```

---

#### 1.3.2 命令解析流水线

**任务清单：**
- [ ] 输入预处理（标准化、别名展开）
- [ ] Trie树前缀匹配算法
- [ ] 歧义处理与智能提示
- [ ] 命令执行上下文管理

**核心接口：**
```python
# src/engine/commands/handler.py
class CommandHandler:
    """命令处理器"""
    
    def __init__(self, engine: "GameEngine")
    
    def build_trie(self, cmdset: CmdSet) -> None:
        """构建命令前缀树"""
    
    async def match(
        self, 
        cmdline: str, 
        available_cmdsets: List[CmdSet]
    ) -> Optional[Command]:
        """匹配命令"""
    
    async def execute(
        self, 
        caller: TypeclassBase, 
        cmdline: str,
        context_cmdsets: Optional[List[CmdSet]] = None
    ) -> CommandResult:
        """
        完整执行流程：
        1. 获取调用者当前cmdset（对象+位置+状态叠加）
        2. 构建合并后的命令集
        3. Trie树匹配命令
        4. 实例化命令并执行
        """
    
    def get_suggestions(self, partial: str) -> List[str]:
        """获取命令补全建议"""
```

**命令匹配示例：**
```
输入: "look at sword"
→ 分词: ["look", "at", "sword"]
→ 匹配: "look"命令
→ 参数: "at sword"
```

---

#### 1.3.3 事件调度中心

**任务清单：**
- [ ] 延迟事件（callLater等效）
- [ ] 周期事件（Tick等效）
- [ ] 条件事件（状态监听）
- [ ] 优先级队列（heapq）
- [ ] 时间膨胀控制

**核心实现：**
```python
# src/engine/events/scheduler.py
import asyncio
import heapq
from dataclasses import dataclass, field
from typing import Callable, Any, Optional
from enum import Enum, auto

class EventType(Enum):
    DELAY = auto()      # 延迟执行
    REPEAT = auto()     # 周期执行
    CONDITION = auto()  # 条件触发
    FRAME = auto()      # 每帧执行

@dataclass(order=True)
class ScheduledEvent:
    """调度事件"""
    trigger_time: float
    event_type: EventType = field(compare=False)
    callback: Callable = field(compare=False)
    args: tuple = field(default_factory=tuple, compare=False)
    kwargs: dict = field(default_factory=dict, compare=False)
    interval: Optional[float] = field(default=None, compare=False)
    event_id: str = field(default="", compare=False)
    priority: int = field(default=0, compare=False)  # 优先级（越小越优先）

class EventScheduler:
    """事件调度中心 - asyncio实现"""
    
    def __init__(self, time_scale: float = 1.0):
        self._event_queue: list[ScheduledEvent] = []
        self._running = False
        self._time_scale = time_scale
        self._task: Optional[asyncio.Task] = None
        self._frame_callbacks: list[Callable] = []
    
    async def start(self) -> None:
        """启动调度循环"""
    
    async def stop(self) -> None:
        """停止调度循环"""
    
    def schedule_delay(
        self, 
        delay: float, 
        callback: Callable, 
        *args, 
        **kwargs
    ) -> str:
        """延迟执行（单位：秒）"""
    
    def schedule_repeat(
        self, 
        interval: float, 
        callback: Callable, 
        *args, 
        **kwargs
    ) -> str:
        """周期执行"""
    
    def schedule_condition(
        self, 
        condition: Callable[[], bool],
        callback: Callable,
        check_interval: float = 1.0
    ) -> str:
        """条件满足时执行"""
    
    def register_frame(self, callback: Callable) -> None:
        """注册每帧回调"""
    
    def unregister_frame(self, callback: Callable) -> None:
        """取消帧回调"""
    
    def cancel(self, event_id: str) -> bool:
        """取消指定事件"""
    
    def set_time_scale(self, scale: float) -> None:
        """设置时间流速（0.5x - 2.0x）"""
    
    async def _loop(self) -> None:
        """主调度循环"""
```

**Script/Ticker等价实现：**
```python
# src/engine/events/script.py
class Script(TypeclassBase):
    """Evennia风格Script - 持久化任务对象"""
    
    desc: str = ""
    interval: float = 0  # 0表示不重复
    repeats: int = 0     # 0表示无限
    start_delay: float = 0
    persistent: bool = True
    
    async def at_start(self) -> None:
        """首次启动时调用"""
    
    async def at_repeat(self) -> None:
        """每次触发时调用"""
    
    async def at_stop(self) -> None:
        """停止时调用"""
    
    def is_valid(self) -> bool:
        """检查是否应继续运行"""
```

---

#### 1.3.4 引擎核心整合

**任务清单：**
- [ ] GameEngine主类整合
- [ ] 启动/关闭流程
- [ ] 命令行测试模式
- [ ] 基础命令实现（look, go, say等）

**GameEngine设计：**
```python
# src/engine/core/engine.py
class GameEngine:
    """游戏引擎核心"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.db: DatabaseManager
        self.objects: ObjectManager
        self.commands: CommandHandler
        self.events: EventScheduler
        self.running = False
    
    async def initialize(self) -> None:
        """初始化引擎"""
        # 1. 初始化数据库
        # 2. 初始化对象管理器
        # 3. 初始化命令处理器
        # 4. 初始化事件调度器
        # 5. 加载世界数据
    
    async def start(self) -> None:
        """启动引擎"""
    
    async def stop(self) -> None:
        """停止引擎（优雅关闭）"""
        # 1. 保存所有dirty对象
        # 2. 停止事件调度器
        # 3. 关闭数据库连接
    
    async def process_input(
        self, 
        caller: TypeclassBase, 
        text: str
    ) -> CommandResult:
        """处理玩家输入"""
```

**基础命令实现：**
```python
# src/game/commands/basic.py
class CmdLook(Command):
    key = "look"
    aliases = ["l", "查看"]
    locks = "cmd:all()"
    
    async def execute(self) -> CommandResult:
        location = self.caller.location
        if not location:
            return CommandResult(True, "你漂浮在虚空中，四周一片黑暗。")
        
        desc = location.at_desc(self.caller)
        contents = [obj.key for obj in location.contents if obj != self.caller]
        
        message = f"\n{location.key}\n{desc}\n"
        if contents:
            message += f"\n这里还有：{', '.join(contents)}"
        
        return CommandResult(True, message)

class CmdGo(Command):
    key = "go"
    aliases = ["move", "goto", "走", "去"]
    
    async def parse(self) -> bool:
        self.direction = self.args.strip()
        return bool(self.direction)
    
    async def execute(self) -> CommandResult:
        # 查找出口
        exit_obj = self._find_exit(self.direction)
        if not exit_obj:
            return CommandResult(False, f"你无法向{self.direction}走。")
        
        destination = exit_obj.destination
        if not self.caller.at_move(destination):
            return CommandResult(False, "你无法离开这里。")
        
        # 执行移动
        source = self.caller.location
        self.caller.location = destination
        await self.manager.save(self.caller)
        
        self.caller.at_moved(source)
        
        # 触发look
        return CommandResult(True, f"你来到了{destination.key}。")
```

**阶段一验收标准：**
- 可通过命令行与引擎交互
- 支持创建对象、移动、查看等基本操作
- 事件调度器可正确处理延迟/周期任务
- 对象修改后正确标记dirty并持久化

---

## 阶段二：游戏数据模型（第4-5周）

### 阶段目标
建立完整的武侠游戏数据模型，包括角色属性、门派系统、内力系统、物品装备、武学系统、地图系统六大模块。本阶段结束时，应能创建完整的武侠角色并装备武器、学习武功。

---

### 2.1 武侠角色系统（第4周上半周）

#### 2.1.1 角色属性模型

**任务清单：**
- [ ] Character类型类（继承TypeclassBase）
- [ ] 先天资质系统（根骨、悟性、福缘、容貌）
- [ ] 后天属性系统（力量、敏捷、体质、精神）
- [ ] 动态状态系统（气血、内力、精力）
- [ ] 属性成长公式

**角色数据结构：**
```python
# src/game/typeclasses/character.py
class Character(TypeclassBase):
    """武侠角色类型"""
    
    typeclass_path = "src.game.typeclasses.character.Character"
    
    # ===== 先天资质（创建时随机，1-30，几乎不变） =====
    @property
    def birth_talents(self) -> dict[str, int]:
        """先天资质"""
        return self.db.get("birth_talents", {
            "gengu": 15,      # 根骨 - 影响体质、气血上限
            "wuxing": 15,     # 悟性 - 影响武学领悟速度
            "fuyuan": 15,     # 福缘 - 影响奇遇概率
            "rongmao": 15,    # 容貌 - 影响NPC态度
        })
    
    # ===== 后天属性（可通过修炼提升） =====
    @property
    def attributes(self) -> dict[str, int]:
        """后天属性"""
        return self.db.get("attributes", {
            "strength": 10,   # 力量 - 影响外功伤害
            "agility": 10,    # 敏捷 - 影响闪避、命中
            "constitution": 10,  # 体质 - 影响气血上限
            "spirit": 10,     # 精神 - 影响内力上限、抗性
        })
    
    # ===== 动态状态（战斗中实时变化） =====
    @property
    def status(self) -> dict[str, tuple[int, int]]:
        """
        动态状态 - (当前值, 最大值)
        """
        return self.db.get("status", {
            "hp": (100, 100),     # 气血
            "mp": (50, 50),       # 内力
            "ep": (100, 100),     # 精力（日常活动消耗）
        })
    
    def get_hp(self) -> tuple[int, int]:
        """获取当前/最大气血"""
    
    def modify_hp(self, delta: int) -> int:
        """修改气血，返回实际变化值"""
    
    def get_mp(self) -> tuple[int, int]:
        """获取当前/最大内力"""
    
    def modify_mp(self, delta: int) -> int:
        """修改内力"""
    
    # ===== 属性计算 =====
    def get_max_hp(self) -> int:
        """计算最大气血 = 基础值 + 体质*10 + 根骨*5"""
    
    def get_max_mp(self) -> int:
        """计算最大内力 = 基础值 + 精神*8 + 根骨*3"""
    
    def get_attack(self) -> int:
        """计算攻击力（基础 + 装备 + BUFF）"""
    
    def get_defense(self) -> int:
        """计算防御力"""
```

---

#### 2.1.2 门派系统

**任务清单：**
- [ ] Menpai门派数据模型
- [ ] 门派入门条件检查
- [ ] 门派贡献系统
- [ ] 门派职位系统

**实现：**
```python
# src/game/typeclasses/menpai.py
class Menpai:
    """门派定义"""
    
    key: str              # 门派名
    desc: str             # 门派描述
    location_id: int      # 门派驻地房间ID
    
    # 入门条件
    requirements: dict    # {min_gengu: 15, max_good_evil: -100, ...}
    
    # 武学路线
    wuxue_list: list[str]  # 可学武功列表
    
    # 门派特色
    special_bonus: dict   # 属性加成

class CharacterMenpaiMixin:
    """角色的门派相关方法"""
    
    @property
    def menpai(self) -> Optional[str]:
        """当前门派"""
        return self.db.get("menpai")
    
    @property
    def menpai_contrib(self) -> int:
        """门派贡献"""
        return self.db.get("menpai_contrib", 0)
    
    @property
    def menpai_position(self) -> str:
        """门派职位"""
        return self.db.get("menpai_position", "弟子")
    
    async def join_menpai(self, menpai: Menpai) -> bool:
        """加入门派（检查条件）"""
    
    async def leave_menpai(self) -> bool:
        """离开/叛师（可能有惩罚）"""
```

---

#### 2.1.3 内力系统

**任务清单：**
- [ ] 丹田容量计算
- [ ] 经脉系统模型（图结构）
- [ ] 内力属性（阴阳刚柔）
- [ ] 走火入魔风险机制

**经脉系统设计：**
```python
# src/game/typeclasses/internal_power.py
class Meridian:
    """经脉节点"""
    
    key: str              # 经脉名（如"手太阴肺经"）
    xuewei: list[str]     # 穴位列表
    is_opened: bool = False
    
    # 冲穴条件
    requirements: dict    # {min_mp: 100, min_level: 30}
    
    # 效果
    effects: dict         # 冲开后属性加成

class InternalPowerSystem:
    """内力系统"""
    
    def __init__(self, character: Character):
        self.character = character
    
    @property
    def internal_type(self) -> str:
        """内力属性 - 阴/阳/刚/柔"""
        return self.character.db.get("internal_type", "neutral")
    
    @property
    def dantian_capacity(self) -> int:
        """丹田容量"""
    
    @property
    def meridians(self) -> dict[str, Meridian]:
        """经脉状态"""
    
    async def open_meridian(self, meridian_key: str) -> bool:
        """冲开穴位（可能失败）"""
    
    def get_deviation_risk(self) -> float:
        """计算走火入魔风险"""
```

---

### 2.2 物品与装备系统（第4周下半周）

#### 2.2.1 物品基类与分类

**任务清单：**
- [ ] Item物品基类
- [ ] 物品类型枚举
- [ ] 物品叠加规则
- [ ] 物品耐久度系统

```python
# src/game/typeclasses/item.py
class ItemType(Enum):
    WEAPON = "weapon"       # 武器
    ARMOR = "armor"         # 防具
    ACCESSORY = "accessory" # 饰品
    MEDICINE = "medicine"   # 药品
    MATERIAL = "material"   # 材料
    BOOK = "book"          # 秘籍
    QUEST = "quest"        # 任务物品

class Item(TypeclassBase):
    """物品基类"""
    
    typeclass_path = "src.game.typeclasses.item.Item"
    
    @property
    def item_type(self) -> ItemType:
    
    @property
    def quality(self) -> int:
        """品质 1-5（普通/优秀/精良/史诗/传说）"""
    
    @property
    def durability(self) -> tuple[int, int]:
        """(当前, 最大)耐久"""
    
    @property
    def is_bound(self) -> bool:
        """是否绑定"""
    
    @property
    def stack_limit(self) -> int:
        """叠加上限"""
    
    @property
    def stack_count(self) -> int:
        """当前堆叠数量"""
```

---

#### 2.2.2 装备系统

**任务清单：**
- [ ] 装备槽位定义（12+槽位）
- [ ] 装备属性加成计算
- [ ] 套装效果
- [ ] 装备对比功能

```python
# src/game/typeclasses/equipment.py
class EquipmentSlot(Enum):
    MAIN_HAND = "main_hand"    # 主手
    OFF_HAND = "off_hand"      # 副手
    HEAD = "head"              # 头
    BODY = "body"              # 身
    WAIST = "waist"            # 腰
    LEGS = "legs"              # 腿
    FEET = "feet"              # 足
    NECK = "neck"              # 项链
    RING1 = "ring1"            # 戒指1
    RING2 = "ring2"            # 戒指2
    JADE = "jade"              # 玉佩

class Equipment(Item):
    """装备类"""
    
    @property
    def slot(self) -> EquipmentSlot:
    
    @property
    def stats_bonus(self) -> dict[str, int]:
        """属性加成"""
    
    @property
    def set_name(self) -> Optional[str]:
        """所属套装"""

class EquipmentMixin:
    """角色的装备管理"""
    
    def get_equipped(self, slot: EquipmentSlot) -> Optional[Equipment]:
        """获取指定槽位装备"""
    
    async def equip(self, item: Equipment) -> bool:
        """装备物品"""
    
    async def unequip(self, slot: EquipmentSlot) -> Optional[Equipment]:
        """卸下装备"""
    
    def get_total_stats(self) -> dict[str, int]:
        """计算所有装备属性总和"""
    
    def get_set_bonuses(self) -> dict[str, Any]:
        """计算套装效果"""
```

---

### 2.3 武学系统（第5周上半周）

#### 2.3.1 武学数据模型

**任务清单：**
- [ ] Kungfu武功定义
- [ ] Move招式定义
- [ ] Neigong内功定义
- [ ] Qinggong轻功定义

```python
# src/game/typeclasses/wuxue.py
class WuxueType(Enum):
    QUAN = "quan"      # 拳
    ZHANG = "zhang"    # 掌
    ZHI = "zhi"        # 指
    JIAN = "jian"      # 剑
    DAO = "dao"        # 刀
    GUN = "gun"        # 棍/杖
    NEIGONG = "neigong"  # 内功
    QINGGONG = "qinggong" # 轻功

class Move:
    """招式定义"""
    
    key: str
    name: str           # 招式名
    wuxue_type: WuxueType
    
    # 消耗
    mp_cost: int
    ep_cost: int
    cooldown: float     # 冷却时间
    
    # 效果脚本
    effect_script: str  # Python代码字符串
    
    # 克制关系
    counters: list[WuxueType]
    countered_by: list[WuxueType]

class Kungfu:
    """武功"""
    
    key: str
    name: str
    menpai: str         # 所属门派
    wuxue_type: WuxueType
    
    moves: list[Move]   # 包含招式
    
    # 学习条件
    requirements: dict

class CharacterWuxueMixin:
    """角色的武学管理"""
    
    @property
    def learned_wuxue(self) -> dict[str, dict]:
        """
        已学武功: {
            "kungfu_key": {
                "level": 1,           # 层数
                "exp": 0,             # 熟练度
                "moves": {            # 招式熟练度
                    "move_key": exp
                }
            }
        }
        """
    
    async def learn_wuxue(self, kungfu: Kungfu) -> bool:
        """学习武功"""
    
    async def practice_move(self, move: Move) -> bool:
        """练习招式，增加熟练度"""
    
    def get_move_effect(self, move: Move) -> Callable:
        """获取招式效果函数"""
```

---

#### 2.3.2 招式效果脚本系统

**任务清单：**
- [ ] 招式效果函数接口定义
- [ ] 沙箱执行环境
- [ ] 常用效果函数库

```python
# src/game/combat/move_effects.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class MoveEffectResult:
    damage: float = 0
    heal: float = 0
    effects: list[str] = None  # stun, poison, buff等
    messages: list[str] = None
    mp_cost: int = 0

class CombatContext:
    """战斗上下文"""
    caster: "Character"
    target: "Character"
    environment: "Room"
    # 战斗上下文信息

def execute_move_script(
    script: str, 
    context: CombatContext
) -> MoveEffectResult:
    """
    沙箱执行招式脚本
    可用变量: caster, target, context, random, dice
    """
    sandbox_globals = {
        "caster": context.caster,
        "target": context.target,
        "context": context,
        "random": __import__("random").random,
        "dice": lambda n, d: sum(__import__("random").randint(1, d) for _ in range(n)),
        "MoveEffectResult": MoveEffectResult,
    }
    
    exec(script, sandbox_globals, {})
    return sandbox_globals.get("result", MoveEffectResult())

# 示例招式脚本
MOVE_SCRIPT_EXAMPLE = """
# 降龙十八掌 - 亢龙有悔
base_damage = caster.get_attack() * 2

# 内力匹配加成
if caster.internal_type == "yang_gang":
    base_damage *= 1.3

# 命中率判定
hit_chance = 0.9 + (caster.get_agility() - target.get_agility()) * 0.01
if random() < hit_chance:
    damage = base_damage * (0.9 + random() * 0.2)  # 伤害浮动
    result = MoveEffectResult(
        damage=damage,
        mp_cost=50,
        messages=[f"{caster.name}拍出亢龙有悔，掌风呼啸！造成{damage:.0f}点伤害！"]
    )
else:
    result = MoveEffectResult(
        mp_cost=50,
        messages=[f"{caster.name}拍出亢龙有悔，但被{target.name}闪开了！"]
    )
"""
```

---

### 2.4 地图系统（第5周下半周）

#### 2.4.1 地图数据模型

**任务清单：**
- [ ] Room房间类（三维坐标）
- [ ] Exit出口类
- [ ] Area区域类
- [ ] 动态加载策略

```python
# src/game/typeclasses/room.py
class Room(TypeclassBase):
    """房间类型"""
    
    typeclass_path = "src.game.typeclasses.room.Room"
    
    @property
    def coords(self) -> tuple[int, int, int]:
        """三维坐标 (x, y, z)"""
        return self.db.get("coords", (0, 0, 0))
    
    @property
    def area(self) -> str:
        """所属区域"""
        return self.db.get("area", "未知区域")
    
    @property
    def description(self) -> str:
        """房间描述"""
    
    @property
    def environment(self) -> dict:
        """环境属性（光照、天气等）"""
    
    def get_exits(self) -> list["Exit"]:
        """获取所有出口"""
    
    def get_exit(self, direction: str) -> Optional["Exit"]:
        """获取指定方向出口"""

class Exit(TypeclassBase):
    """出口类型"""
    
    typeclass_path = "src.game.typeclasses.room.Exit"
    
    @property
    def direction(self) -> str:
        """方向（n/ne/e/se/s/sw/w/nw/up/down）"""
    
    @property
    def destination(self) -> Room:
        """目标房间"""
    
    @property
    def is_hidden(self) -> bool:
        """是否隐藏"""
    
    @property
    def lock_str(self) -> str:
        """通行条件"""
    
    async def can_pass(self, character: Character) -> tuple[bool, str]:
        """检查是否可以通过"""

class Area:
    """区域定义"""
    
    key: str
    name: str
    rooms: list[int]  # 房间ID列表
    
    # 加载策略
    load_range: int = 3      # 预加载范围
    unload_delay: int = 60   # 卸载延迟（秒）
```

---

#### 2.4.2 动态加载与寻路

**任务清单：**
- [ ] 区域动态加载管理器
- [ ] A*寻路算法
- [ ] 自动导航功能

```python
# src/game/world/loader.py
class WorldLoader:
    """世界动态加载管理器"""
    
    def __init__(self, object_manager: ObjectManager):
        self.obj_mgr = object_manager
        self._loaded_areas: set[str] = set()
        self._active_rooms: dict[int, float] = {}  # room_id -> last_access_time
    
    async def on_player_move(self, from_room: Room, to_room: Room):
        """玩家移动时触发加载/卸载"""
    
    async def _load_area(self, area: Area):
        """加载区域"""
    
    async def _unload_area(self, area: Area):
        """卸载区域"""
    
    def get_active_rooms(self) -> list[int]:
        """获取当前活跃房间"""

# src/game/world/pathfinding.py
class PathFinder:
    """A*寻路"""
    
    def __init__(self, world_loader: WorldLoader):
        self.world = world_loader
    
    async def find_path(
        self, 
        start: Room, 
        goal: Room
    ) -> Optional[list[tuple[str, Room]]]:
        """
        返回路径: [("n", room1), ("ne", room2), ...]
        """
    
    def heuristic(self, a: Room, b: Room) -> float:
        """启发函数 - 三维曼哈顿距离"""
        ax, ay, az = a.coords
        bx, by, bz = b.coords
        return abs(ax-bx) + abs(ay-by) + abs(az-bz) * 2  # Z轴权重更高
```

**阶段二验收标准：**
- 可创建完整武侠角色（含先天/后天属性）
- 角色可装备/卸下武器、防具
- 角色可学习武功并使用招式
- 地图系统支持三维移动和寻路

---

## 阶段三：游戏玩法系统（第6-8周）

### 阶段目标
实现核心游戏玩法：探索、战斗、任务、NPC交互。本阶段结束时，应能完成从角色创建到参与战斗、完成任务的全流程。

---

### 3.1 探索与移动系统（第6周上半周）

#### 3.1.1 场景描述渲染

**任务清单：**
- [ ] 房间描述动态生成
- [ ] 关键词高亮与点击交互
- [ ] 环境状态（昼夜、天气）影响描述

```python
# src/game/exploration/desc_renderer.py
class DescriptionRenderer:
    """场景描述渲染器"""
    
    def __init__(self, engine: GameEngine):
        self.engine = engine
    
    async def render_room(
        self, 
        room: Room, 
        looker: Character,
        format: str = "text"
    ) -> str:
        """
        渲染房间描述
        包含：名称、描述、出口、物品、NPC、环境
        """
    
    def _apply_environment_modifiers(
        self, 
        desc: str, 
        room: Room
    ) -> str:
        """根据环境（昼夜、天气）修改描述"""
    
    def _extract_keywords(self, text: str) -> list[tuple[str, str]]:
        """提取关键词（用于GUI点击交互）"""
```

---

#### 3.1.2 自然语言命令

**任务清单：**
- [ ] jieba分词集成
- [ ] 动词同义词库
- [ ] 模糊匹配与纠错
- [ ] 上下文补全

```python
# src/game/commands/nlp.py
import jieba

class NLPCommandParser:
    """自然语言命令解析器"""
    
    # 动词同义词映射
    VERB_SYNONYMS = {
        "去": "go", "走": "go", "移动": "go", "前往": "go",
        "看": "look", "观察": "look", "查看": "look",
        "拿": "get", "拾取": "get", "捡起": "get",
        # ...
    }
    
    def __init__(self, engine: GameEngine):
        # 加载自定义词典
        jieba.load_userdict("resources/dict/wuxie_dict.txt")
    
    def parse(self, text: str) -> Optional[tuple[str, str]]:
        """
        解析自然语言为(命令, 参数)
        "向东北走" -> ("go", "northeast")
        "查看背包" -> ("inventory", "")
        """
        words = list(jieba.cut(text))
        # 解析逻辑...
    
    def get_similar_commands(self, typo: str) -> list[str]:
        """输入纠错建议"""
```

---

### 3.2 战斗系统（第6周下半周-第7周）

#### 3.2.1 战斗核心（即时制）

**设计原则：** MUD采用即时制战斗，玩家可随时输入命令，无需等待回合。

**任务清单：**
- [x] CombatSession战斗会话
- [x] 行动冷却系统
- [x] 战斗AI

```python
# src/game/combat/core.py
class CombatSession:
    """即时制战斗会话
    
    玩家可随时输入命令，各行动有独立冷却时间。
    冷却时间受角色敏捷属性影响。
    """
    
    def __init__(
        self, 
        engine: GameEngine,
        participants: list[Character],
        player_character: Character | None = None,
    ):
        self.engine = engine
        self.participants: dict[int, Combatant] = {}
        self.active = False
    
    async def start(self) -> None:
        """开始战斗，启动战斗循环"""
    
    async def _combat_loop(self) -> None:
        """战斗主循环（100ms tick）"""
    
    async def handle_player_command(
        self, character: Character, cmd: str, args: dict
    ) -> tuple[bool, str]:
        """处理玩家战斗命令
        
        检查冷却时间，执行命令，设置新冷却。
        """
    
    def _calculate_cooldown(
        self, character: Character, move: Move | None
    ) -> float:
        """计算行动冷却时间
        
        公式: base_cooldown * (1 - agility * factor)
        最小冷却: 1秒
        """

class Combatant:
    """战斗参与者封装"""
    
    def __init__(self, character: Character, is_player: bool = False):
        self.character = character
        self.is_player = is_player
        self.next_action_time: float = 0.0
    
    def is_ready(self) -> bool:
        """检查是否可以行动"""
    
    def set_cooldown(self, cooldown: float) -> None:
        """设置下次可行动时间"""

class CombatAction:
    """战斗行动"""
    type: str  # "move", "item", "flee", "defend"
    target: Optional[Character]
    data: dict

class CombatAI:
    """战斗AI - 多策略支持"""
    
    async def decide(
        self, character: Character, combat: CombatSession
    ) -> CombatAction:
        """AI决策"""

class SmartAI(CombatAI):
    """智能AI - 血量低时优先防御/逃跑"""

class AggressiveAI(CombatAI):
    """激进AI - 总是优先攻击"""

class DefensiveAI(CombatAI):
    """防御型AI - 经常使用防御"""
```

---

#### 3.2.2 战斗数值计算

**任务清单：**
- [ ] 伤害计算公式
- [ ] 命中率/闪避率计算
- [ ] 招式相克修正
- [ ] 环境加成

```python
# src/game/combat/calculator.py
class CombatCalculator:
    """战斗数值计算器"""
    
    @staticmethod
    def calculate_damage(
        attacker: Character,
        defender: Character,
        move: Move,
        context: CombatContext
    ) -> DamageResult:
        """
        伤害计算流程：
        1. 基础伤害 = 攻击力 * 招式倍率
        2. 防御减免 = 基础伤害 - 防御力
        3. 招式克制加成
        4. 环境加成
        5. 随机浮动 (0.9-1.1)
        """
    
    @staticmethod
    def calculate_hit_rate(
        attacker: Character,
        defender: Character,
        move: Move
    ) -> float:
        """
        命中率 = 基础命中 + (敏捷差 * 0.5%) + 招式修正
        """
    
    @staticmethod
    def get_environment_bonus(
        context: CombatContext
    ) -> dict[str, float]:
        """
        环境加成：
        - 高地 -> +10%命中
        - 雨天 -> 火系-20%，水系+20%
        - 夜间 -> -20%命中（无照明）
        """
```

---

#### 3.2.3 BUFF/DEBUFF系统

```python
# src/game/combat/buff.py
class Buff:
    """状态效果"""
    
    key: str
    name: str
    duration: float  # 持续时间（秒）
    buff_type: BuffType  # BUFF/DEBUFF/NEUTRAL
    stack_limit: int = 1
    
    # 效果
    stats_mod: dict[str, int]  # 属性修正
    on_apply: Callable | None  # 应用时回调
    on_tick: Callable | None   # 每tick回调
    on_remove: Callable | None # 移除时回调

class BuffManager:
    """角色BUFF管理"""
    
    def __init__(self, character: Character):
        self.character = character
        self._buffs: dict[str, Buff] = {}
    
    async def add(self, buff: Buff) -> bool:
        """添加BUFF"""
    
    async def remove(self, buff_key: str) -> bool:
        """移除BUFF"""
    
    async def tick(self) -> list[str]:
        """BUFF结算，清理过期BUFF，返回消息"""
    
    def get_stats_modifier(self) -> dict[str, int]:
        """获取所有BUFF的属性修正总和"""
    
    def has_buff(self, buff_key: str) -> bool:
        """检查是否有指定BUFF"""
```

---

### 3.3 任务与剧情系统（第8周）

#### 3.3.1 任务数据模型

**任务清单：**
- [ ] Task任务定义
- [ ] 任务目标类型（收集/击杀/对话/探索）
- [ ] 任务奖励
- [ ] 任务链

```python
# src/game/quest/core.py
class QuestObjectiveType(Enum):
    COLLECT = "collect"    # 收集物品
    KILL = "kill"          # 击杀NPC
    TALK = "talk"          # 对话
    EXPLORE = "explore"    # 探索地点
    CUSTOM = "custom"      # 自定义条件

class QuestObjective:
    """任务目标"""
    type: QuestObjectiveType
    target: str           # 目标ID
    count: int = 1
    current: int = 0
    description: str

class Quest:
    """任务定义"""
    
    key: str
    name: str
    description: str
    type: str  # "main" | "side" | "daily" | "menpai"
    
    objectives: list[QuestObjective]
    rewards: dict  # exp, item, wuxue, reputation
    
    # 前置条件
    prerequisites: dict  # level, menpai, quest_completed等
    
    # 任务链
    next_quest: Optional[str]
    
    # 时间限制
    time_limit: Optional[int]  # 秒，None表示无限制

class CharacterQuestMixin:
    """角色的任务管理"""
    
    @property
    def active_quests(self) -> dict[str, dict]:
        """进行中任务"""
    
    @property
    def completed_quests(self) -> list[str]:
        """已完成任务"""
    
    async def accept_quest(self, quest: Quest) -> bool:
        """接受任务"""
    
    async def update_objective(
        self, 
        quest_key: str, 
        objective_idx: int, 
        progress: int
    ) -> bool:
        """更新任务进度"""
    
    async def complete_quest(self, quest_key: str) -> bool:
        """完成任务"""
```

---

#### 3.3.2 因果点与世界状态

```python
# src/game/quest/karma.py
class KarmaSystem:
    """因果点系统"""
    
    KARMA_TYPES = ["good", "evil", "love", "loyalty", "wisdom", "courage"]
    
    def __init__(self, character: Character):
        self.character = character
    
    def add_karma(self, karma_type: str, points: int, reason: str):
        """添加因果点"""
    
    def get_karma_summary(self) -> dict[str, int]:
        """获取因果点汇总"""
    
    def check_requirement(self, requirement: dict) -> bool:
        """检查因果点是否满足条件"""
        # 例如：{"good": ">=10", "evil": "<=5", "love+wisdom": ">=15"}

class WorldStateManager:
    """世界状态管理"""
    
    def __init__(self, engine: GameEngine):
        self.engine = engine
        self._states: dict[str, Any] = {}
    
    def get(self, key: str, default=None):
        """获取世界状态"""
    
    def set(self, key: str, value: Any):
        """设置世界状态"""
    
    def on_player_choice(
        self, 
        character: Character, 
        choice_id: str, 
        choice: str
    ):
        """记录玩家选择"""
```

---

### 3.4 NPC系统（第8周）

#### 3.4.1 NPC行为系统

**任务清单：**
- [ ] NPC类型类
- [ ] 行为树基础框架
- [ ] 日常行程系统
- [ ] 对话系统

```python
# src/game/npc/core.py
class NPC(Character):
    """NPC类型"""
    
    typeclass_path = "src.game.npc.core.NPC"
    
    @property
    def ai_enabled(self) -> bool:
    
    @property
    def schedule(self) -> list[ScheduleItem]:
        """日常行程安排"""
    
    async def update_ai(self, delta_time: float):
        """AI更新"""

# src/game/npc/behavior_tree.py
class BehaviorNode:
    """行为树节点"""
    async def tick(self, npc: NPC, context: dict) -> NodeStatus:
        """返回 SUCCESS | FAILURE | RUNNING """

class SelectorNode(BehaviorNode): pass  # 顺序执行直到成功
class SequenceNode(BehaviorNode): pass  # 顺序执行直到失败
class ActionNode(BehaviorNode): pass    # 执行动作

class NPCBehaviorTree:
    """NPC行为树"""
    
    def __init__(self, root: BehaviorNode):
        self.root = root
    
    async def tick(self, npc: NPC):
        await self.root.tick(npc, {})
```

---

#### 3.4.2 好感度与对话

```python
# src/game/npc/reputation.py
class NPCRelationship:
    """NPC关系管理"""
    
    def __init__(self, character: Character):
        self.character = character
    
    def get_favor(self, npc_id: str) -> int:
        """获取对特定NPC的好感度"""
    
    def modify_favor(self, npc_id: str, delta: int, reason: str):
        """修改好感度"""
    
    def get_relationship_level(self, npc_id: str) -> str:
        """
        关系等级：
        - 仇敌（-100以下）
        - 冷淡（-50~-100）
        - 陌生（-50~50）
        - 友善（50~100）
        - 尊敬（100~200）
        - 至交（200以上）
        """

# src/game/npc/dialogue.py
class DialogueNode:
    """对话节点"""
    
    text: str                    # NPC说的话
    responses: list[Response]    # 玩家回应选项
    conditions: dict             # 显示条件
    effects: dict                # 选择后的效果

class Response:
    text: str
    next_node: Optional[str]
    conditions: dict
    effects: dict

class DialogueSystem:
    """对话系统"""
    
    async def start_dialogue(
        self, 
        character: Character, 
        npc: NPC
    ) -> DialogueNode:
        """开始对话"""
    
    async def select_response(
        self, 
        character: Character, 
        response_idx: int
    ) -> DialogueNode:
        """选择回应"""
```

**阶段三验收标准：**
- 完整的战斗流程（开始→行动→结算→结束）
- 可接受、进行、完成任务
- NPC有日常行为并与玩家对话
- 支持自然语言命令

---

## 阶段四：GUI客户端开发（第9-12周）

### 阶段目标
使用PySide6构建现代化图形界面，实现沉浸式武侠体验。本阶段结束时，应能通过GUI完成所有游戏操作。

---

### 4.1 GUI基础框架（第9周）

#### 4.1.1 PySide6主窗口架构

**任务清单：**
- [ ] MainWindow主窗口类
- [ ] 面板布局管理系统
- [ ] 信号-槽状态绑定
- [ ] 主题样式加载

```python
# src/gui/main_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QSplitter
from PySide6.QtCore import Signal, QObject
import qasync

class GameState(QObject):
    """游戏状态信号中心"""
    
    # 角色状态
    player_hp_changed = Signal(int, int)      # 当前, 最大
    player_mp_changed = Signal(int, int)
    player_exp_changed = Signal(int, int)
    
    # 位置变化
    player_moved = Signal(object)  # Room对象
    
    # 战斗
    combat_started = Signal(object)
    combat_ended = Signal(object)
    combat_round = Signal(int)
    
    # 物品
    inventory_changed = Signal()
    equipment_changed = Signal()
    
    # 任务
    quest_updated = Signal(str)   # quest_key

class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, engine: GameEngine):
        super().__init__()
        self.engine = engine
        self.game_state = GameState()
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """初始化UI组件"""
        # 中央分割器
        self.main_splitter = QSplitter()
        
        # 左侧面板
        self.left_panel = LeftPanel(self.game_state)
        
        # 中央主视窗
        self.main_view = MainViewPanel(self.game_state)
        
        # 右侧面板
        self.right_panel = RightPanel(self.game_state)
        
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.main_view)
        self.main_splitter.addWidget(self.right_panel)
        
        self.setCentralWidget(self.main_splitter)
    
    def _connect_signals(self):
        """连接引擎事件到GUI信号"""
        # 由引擎回调触发GUI更新
        pass
    
    def closeEvent(self, event):
        """关闭时保存并停止引擎"""
        # 异步停止引擎
        asyncio.create_task(self._shutdown())
        event.accept()
    
    async def _shutdown(self):
        await self.engine.stop()
```

---

#### 4.1.2 qasync桥接

```python
# src/gui/async_bridge.py
import asyncio
from qasync import QEventLoop
from PySide6.QtCore import QCoreApplication

class AsyncBridge:
    """asyncio与PySide6桥接"""
    
    def __init__(self, app: QCoreApplication):
        self.app = app
        self.loop = QEventLoop(app)
        asyncio.set_event_loop(self.loop)
    
    def run(self, coro):
        """运行协程"""
        return self.loop.run_until_complete(coro)
    
    def create_task(self, coro):
        """创建任务"""
        return self.loop.create_task(coro)
```

---

### 4.2 核心面板开发（第10-11周）

#### 4.2.1 主视窗面板（P0）

```python
# src/gui/panels/main_view.py
from PySide6.QtWidgets import (
    QTextBrowser, QLineEdit, QVBoxLayout, QWidget
)

class MainViewPanel(QWidget):
    """主视窗 - 场景描述、事件流、命令输入"""
    
    def __init__(self, game_state: GameState):
        super().__init__()
        self.game_state = game_state
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 场景描述区
        self.scene_view = QTextBrowser()
        self.scene_view.setOpenLinks(False)
        self.scene_view.anchorClicked.connect(self._on_link_clicked)
        
        # 事件流
        self.event_log = QTextBrowser()
        self.event_log.setMaximumBlockCount(100)  # 限制行数
        
        # 命令输入
        self.cmd_input = CommandLineEdit()
        self.cmd_input.returnPressed.connect(self._on_command)
        
        layout.addWidget(self.scene_view, 2)
        layout.addWidget(self.event_log, 1)
        layout.addWidget(self.cmd_input)
    
    def update_scene(self, room: Room):
        """更新场景显示"""
        html = self._render_room_html(room)
        self.scene_view.setHtml(html)
    
    def append_event(self, text: str, style: str = "normal"):
        """添加事件到流"""
        formatted = self._format_event(text, style)
        self.event_log.append(formatted)
    
    def _on_command(self):
        text = self.cmd_input.text()
        self.cmd_input.clear()
        self.cmd_input.addToHistory(text)
        # 发送给引擎处理
        asyncio.create_task(self._send_command(text))
    
    def _render_room_html(self, room: Room) -> str:
        """渲染房间为富文本"""
        return f"""
        <h2>{room.key}</h2>
        <p>{room.description}</p>
        <p>出口: {' '.join(f'<a href="go {ex.direction}">{ex.direction}</a>' 
                           for ex in room.get_exits())}</p>
        """

class CommandLineEdit(QLineEdit):
    """支持历史记录和自动补全的命令输入"""
    
    def __init__(self):
        super().__init__()
        self.history: list[str] = []
        self.history_idx = 0
    
    def addToHistory(self, text: str):
        self.history.append(text)
        self.history_idx = len(self.history)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            # 上一条历史
            pass
        elif event.key() == Qt.Key_Down:
            # 下一条历史
            pass
        elif event.key() == Qt.Key_Tab:
            # 自动补全
            pass
        super().keyPressEvent(event)
```

---

#### 4.2.2 角色状态面板（P0）

```python
# src/gui/panels/status.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QProgressBar, QLabel, QGridLayout
)
from PySide6.QtCore import Slot

class StatusPanel(QWidget):
    """角色状态面板 - 气血/内力/精力"""
    
    def __init__(self, game_state: GameState):
        super().__init__()
        self.game_state = game_state
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 气血
        self.hp_layout = self._create_bar(
            "气血", "#c0392b", "#e74c3c"
        )
        layout.addLayout(self.hp_layout)
        
        # 内力
        self.mp_layout = self._create_bar(
            "内力", "#8e44ad", "#9b59b6"
        )
        layout.addLayout(self.mp_layout)
        
        # 精力
        self.ep_layout = self._create_bar(
            "精力", "#27ae60", "#2ecc71"
        )
        layout.addLayout(self.ep_layout)
        
        # BUFF图标区
        self.buff_area = BuffArea()
        layout.addWidget(self.buff_area)
        
        # 战斗姿态
        self.stance_selector = StanceSelector()
        layout.addWidget(self.stance_selector)
    
    def _connect_signals(self):
        self.game_state.player_hp_changed.connect(self._update_hp)
        self.game_state.player_mp_changed.connect(self._update_mp)
    
    @Slot(int, int)
    def _update_hp(self, current: int, max_hp: int):
        bar = self.hp_layout.itemAt(1).widget()
        bar.setMaximum(max_hp)
        bar.setValue(current)
        bar.setFormat(f"%v / %m ({current/max_hp*100:.1f}%)")
        
        # 低血量警告
        if current / max_hp < 0.2:
            bar.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
    
    def _create_bar(self, label: str, bg_color: str, fg_color: str) -> QGridLayout:
        layout = QGridLayout()
        label_widget = QLabel(label)
        bar = QProgressBar()
        bar.setTextVisible(True)
        bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {bg_color};
                border-radius: 3px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {fg_color};
            }}
        """)
        layout.addWidget(label_widget, 0, 0)
        layout.addWidget(bar, 0, 1)
        return layout
```

---

#### 4.2.3 移动罗盘（P0）

```python
# src/gui/panels/compass.py
from PySide6.QtWidgets import QWidget, QGridLayout, QPushButton
from PySide6.QtCore import Qt, Slot

class CompassWidget(QWidget):
    """八方向罗盘"""
    
    DIRECTIONS = {
        "nw": (0, 0), "n": (0, 1), "ne": (0, 2),
        "w":  (1, 0), "look": (1, 1), "e": (1, 2),
        "sw": (2, 0), "s": (2, 1), "se": (2, 2),
        "up": (0, 3), "down": (2, 3)
    }
    
    DIRECTION_NAMES = {
        "nw": "西北", "n": "北", "ne": "东北",
        "w": "西", "look": "环顾", "e": "东",
        "sw": "西南", "s": "南", "se": "东南",
        "up": "上", "down": "下"
    }
    
    def __init__(self, game_state: GameState):
        super().__init__()
        self.game_state = game_state
        self._buttons: dict[str, QPushButton] = {}
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(2)
        
        for dir_key, (row, col) in self.DIRECTIONS.items():
            btn = QPushButton(self.DIRECTION_NAMES[dir_key])
            btn.setFixedSize(50, 50)
            btn.setEnabled(False)  # 默认禁用，根据当前位置可用出口启用
            btn.clicked.connect(lambda d=dir_key: self._on_direction(d))
            self._buttons[dir_key] = btn
            layout.addWidget(btn, row, col)
    
    def update_available_exits(self, room: Room):
        """根据当前房间更新可用出口"""
        exits = {ex.direction for ex in room.get_exits()}
        for dir_key, btn in self._buttons.items():
            btn.setEnabled(dir_key in exits or dir_key == "look")
    
    def _on_direction(self, direction: str):
        if direction == "look":
            cmd = "look"
        else:
            cmd = f"go {direction}"
        # 发送命令
        asyncio.create_task(self._send_command(cmd))
```

---

#### 4.2.4 背包与装备面板（P1）

```python
# src/gui/panels/inventory.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QTabWidget,
    QPushButton, QMenu
)

class InventoryPanel(QWidget):
    """背包面板"""
    
    CATEGORIES = ["全部", "武器", "防具", "饰品", "药品", "材料", "其他"]
    
    def __init__(self, game_state: GameState):
        super().__init__()
        self.game_state = game_state
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 分类标签
        self.tabs = QTabWidget()
        for cat in self.CATEGORIES:
            list_widget = ItemListWidget()
            self.tabs.addTab(list_widget, cat)
        layout.addWidget(self.tabs)
        
        # 批量操作按钮
        btn_layout = QHBoxLayout()
        self.btn_sort = QPushButton("整理")
        self.btn_drop = QPushButton("丢弃")
        btn_layout.addWidget(self.btn_sort)
        btn_layout.addWidget(self.btn_drop)
        layout.addLayout(btn_layout)
    
    def update_inventory(self, items: list[Item]):
        """刷新背包显示"""

class EquipmentPanel(QWidget):
    """装备面板 - 纸娃娃"""
    
    def __init__(self, game_state: GameState):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        # 12+装备槽位的可视化布局
        # 支持拖拽装备
        pass
```

---

#### 4.2.5 武学面板（P1）

```python
# src/gui/panels/wuxue.py
class WuxuePanel(QWidget):
    """武学面板"""
    
    def __init__(self, game_state: GameState):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        # 已学武功列表
        self.kungfu_list = QListWidget()
        
        # 招式详情
        self.move_detail = MoveDetailWidget()
        
        # 快捷配置
        self.hotkey_config = HotkeyConfigWidget()
        
        # 经脉图
        self.meridian_map = MeridianMapWidget()
```

---

#### 4.2.6 地图系统（P1）

```python
# src/gui/panels/map.py
class MapPanel(QWidget):
    """地图面板"""
    
    def __init__(self, game_state: GameState):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        # 世界地图（区域节点）
        self.world_map = WorldMapView()
        
        # 区域地图（房间拓扑）
        self.area_map = AreaMapView()
        
        # 迷雾系统
        self.fog_of_war = FogOfWar()
```

---

### 4.3 主题与美化（第12周）

#### 4.3.1 QSS主题系统

```python
# src/gui/themes/manager.py
from pathlib import Path

class ThemeManager:
    """主题管理器"""
    
    THEMES = {
        "ink": "水墨",      # 默认
        "metal": "金属",
        "classic": "经典",
        "dark": "夜间"
    }
    
    def __init__(self):
        self.current_theme = "ink"
    
    def load_theme(self, theme_name: str) -> str:
        """加载QSS样式"""
        qss_path = Path(f"resources/themes/{theme_name}.qss")
        return qss_path.read_text(encoding="utf-8")
    
    def apply_theme(self, app: QApplication, theme_name: str):
        """应用主题"""
        qss = self.load_theme(theme_name)
        app.setStyleSheet(qss)
        self.current_theme = theme_name
```

**水墨主题示例（ink.qss）：**
```css
/* 水墨风格 */
QMainWindow {
    background-color: #f5f5f0;
}

QTextBrowser {
    background-color: #fafaf5;
    color: #2c2c2c;
    border: 1px solid #d0d0c8;
    font-family: "Noto Serif CJK SC", "SimSun", serif;
    font-size: 14px;
    line-height: 1.6;
}

QProgressBar {
    border: 1px solid #8b4513;
    background-color: #f5f5f0;
}

QPushButton {
    background-color: #e8e4dc;
    border: 1px solid #8b4513;
    padding: 5px 15px;
    border-radius: 3px;
}

QPushButton:hover {
    background-color: #d8d4cc;
}

QPushButton:pressed {
    background-color: #c8c4bc;
}
```

**阶段四验收标准：**
- 所有游戏功能可通过GUI操作
- 主题切换即时生效
- 响应式UI，状态变更实时反映
- 支持快捷键操作

---

## 阶段五：内容制作与集成（第13-15周）

### 阶段目标
填充游戏内容：地图、任务、武学、NPC数据。本阶段结束时，应有一个可游玩的Demo版本。

---

### 5.1 世界构建（第13周）

#### 5.1.1 金庸经典场景

**场景清单：**
| 区域 | 房间数 | 特色 |
|:---|:---|:---|
| 襄阳城 | 30+ | 主城，客栈、武馆、集市 |
| 洛阳 | 25+ | 古都，皇城、书院 |
| 少林寺 | 40+ | 门派驻地，藏经阁、罗汉堂 |
| 武当山 | 35+ | 门派驻地，金顶、紫霄宫 |
| 华山 | 30+ | 门派驻地，思过崖、玉女峰 |
| 峨眉山 | 25+ | 门派驻地 |
| 桃花岛 | 20+ | 门派驻地，奇门遁甲 |
| 绝情谷 | 15+ | 秘境，情花毒 |
| 终南山 | 20+ | 古墓派，活死人墓 |

**任务清单：**
- [ ] 房间描述文案编写（每房间100-300字）
- [ ] 出口连接配置
- [ ] 环境属性设置（昼夜、天气影响）

---

### 5.2 武学数据（第14周上半周）

#### 5.2.1 十大门派基础武学

**武学清单：**
| 门派 | 外功 | 内功 | 轻功 |
|:---|:---|:---|:---|
| 少林 | 罗汉拳、般若掌、龙爪手 | 易筋经、洗髓经 | 一苇渡江 |
| 武当 | 太极拳、太极剑 | 纯阳无极功 | 梯云纵 |
| 峨眉 | 峨眉剑法、金顶绵掌 | 峨眉心法 | 金顶轻功 |
| 华山 | 华山剑法、紫霞神功 | 紫霞神功 | 华山身法 |
| 丐帮 | 降龙十八掌、打狗棒法 | 降龙伏虎功 | 逍遥游 |
| 明教 | 乾坤大挪移、圣火令 | 明教心法 | 圣火轻功 |
| 日月神教 | 葵花宝典、吸星大法 | 葵花宝典 | 鬼魅身法 |
| 桃花岛 | 落英神剑掌、玉箫剑法 | 桃花心法 | 桃花影落 |
| 白驼山 | 蛤蟆功、神驼雪山掌 | 蛤蟆功 | 白驼轻功 |
| 星宿派 | 化功大法、三阴蜈蚣爪 | 化功大法 | 星宿身法 |

**任务清单：**
- [ ] 每种武功定义招式列表
- [ ] 招式效果脚本编写
- [ ] 克制关系配置
- [ ] 学习条件设置

---

### 5.3 任务与剧情（第14周下半周）

#### 5.3.1 主线任务链

**主线章节：**
1. **初入江湖**（1-10级）
   - 创建角色，选择门派
   - 学习基础武学
   - 首次下山历练

2. **崭露头角**（11-30级）
   - 门派大比
   - 江湖奇遇
   - 首次与魔教交手

3. **名动江湖**（31-60级）
   - 追查阴谋
   - 结识侠侣
   - 大战四大恶人

4. **一代宗师**（61-100级）
   - 正邪决战
   - 武林盟主/魔教教主
   - 多结局分支

**任务清单：**
- [ ] 编写30+主线任务
- [ ] 编写50+支线任务
- [ ] 随机遭遇事件库（20+事件）

---

### 5.4 NPC数据（第15周）

#### 5.4.1 门派NPC

**NPC清单：**
| 门派 | 师父 | 特色NPC |
|:---|:---|:---|
| 少林 | 方丈玄慈 | 扫地僧、觉远 |
| 武当 | 张三丰 | 宋远桥、张翠山 |
| 丐帮 | 帮主 | 传功长老、执法长老 |

**任务清单：**
- [ ] 50+有完整对话的NPC
- [ ] 20+可战斗的NPC
- [ ] 10+商人NPC

**阶段五验收标准：**
- 可创建角色并选择门派
- 可完成至少3条主线任务
- 可学习门派基础武学
- 可进行NPC对话和战斗

---

## 阶段六：存档与系统功能（第16-17周）

### 阶段目标
实现完善的存档系统和后台管理功能。

---

### 6.1 存档系统（第16周）

#### 6.1.1 存档管理器

```python
# src/engine/save/manager.py
import msgpack
import gzip
from pathlib import Path
from datetime import datetime

class SaveManager:
    """存档管理器"""
    
    SAVE_DIR = Path("saves")
    AUTO_SAVE_SLOTS = 10
    QUICK_SAVE_SLOT = "quick"
    
    def __init__(self, engine: GameEngine):
        self.engine = engine
    
    async def save(
        self, 
        slot: str, 
        name: str = "", 
        screenshot: Optional[bytes] = None
    ) -> Path:
        """
        保存游戏
        序列化内容：
        - 玩家角色完整状态
        - 世界状态
        - 任务进度
        - 时间戳和元数据
        """
    
    async def load(self, slot: str) -> bool:
        """加载存档"""
    
    async def auto_save(self) -> Path:
        """自动存档（轮转）"""
    
    def get_save_list(self) -> list[SaveInfo]:
        """获取所有存档信息"""
    
    def delete_save(self, slot: str) -> bool:
        """删除存档"""
    
    def _serialize(self) -> bytes:
        """序列化游戏状态"""
        data = {
            "version": GAME_VERSION,
            "timestamp": datetime.now().isoformat(),
            "player": self._serialize_character(),
            "world_state": self._serialize_world(),
            "quests": self._serialize_quests(),
        }
        return msgpack.packb(data, use_bin_type=True)
```

**任务清单：**
- [ ] MessagePack序列化
- [ ] 存档压缩与加密
- [ ] 自动存档触发（关键节点）
- [ ] 存档兼容性检查

---

### 6.2 后台管理系统（第17周）

#### 6.2.1 开发者模式（F12）

```python
# src/gui/dev/manager.py
class DeveloperMode(QWidget):
    """开发者模式面板"""
    
    def __init__(self, engine: GameEngine):
        super().__init__()
        self.setWindowTitle("开发者模式")
    
    def _setup_panels(self):
        self.tabs = QTabWidget()
        
        # 对象浏览器
        self.obj_browser = ObjectBrowser(self.engine)
        self.tabs.addTab(self.obj_browser, "对象")
        
        # 日志查看器
        self.log_viewer = LogViewer()
        self.tabs.addTab(self.log_viewer, "日志")
        
        # 性能监控
        self.perf_monitor = PerformanceMonitor()
        self.tabs.addTab(self.perf_monitor, "性能")
        
        # 平衡性测试
        self.balance_tester = BalanceTester(self.engine)
        self.tabs.addTab(self.balance_tester, "平衡测试")
```

#### 6.2.2 平衡性测试台

```python
# src/gui/dev/balance.py
class BalanceTester(QWidget):
    """平衡性测试工具"""
    
    async def run_combat_simulation(
        self,
        char_a_template: dict,
        char_b_template: dict,
        rounds: int = 1000
    ) -> CombatStats:
        """
        批量战斗模拟
        统计：胜率、平均战斗时长、伤害分布
        """
    
    def generate_report(self, stats: CombatStats) -> str:
        """生成平衡性报告"""
```

**阶段六验收标准：**
- 存档/读档功能完整
- 自动存档正常触发
- 开发者模式可实时查看/修改数据
- 战斗模拟器可批量测试

---

## 阶段七：测试与优化（第18-19周）

### 7.1 功能测试

**任务清单：**
- [ ] 编写单元测试（pytest，覆盖率>80%）
- [ ] 集成测试（引擎-GUI交互）
- [ ] 存档兼容性测试（跨版本）

### 7.2 性能优化

**任务清单：**
- [ ] 对象缓存优化（命中率>95%）
- [ ] 数据库查询优化（<10ms）
- [ ] GUI渲染优化（60FPS）

### 7.3 平衡性调整

**任务清单：**
- [ ] 战斗数值曲线验证
- [ ] 成长节奏测试（1-100级时间分配）
- [ ] 经济系统平衡

**阶段七验收标准：**
- 所有测试通过
- 内存占用<500MB
- 无明显卡顿

---

## 阶段八：打包与发布（第20周）

### 8.1 打包配置

**PyInstaller配置（jinyong_mud.spec）：**
```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('src/game/world/data', 'game/world/data'),
    ],
    hiddenimports=[
        'src.game.typeclasses.character',
        'src.game.typeclasses.room',
        'src.game.typeclasses.item',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='金庸武侠MUD',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI模式
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',
)
```

### 8.2 首次运行向导

**任务清单：**
- [ ] 环境检测脚本
- [ ] 角色创建界面
- [ ] 新手教程

### 8.3 发布准备

**任务清单：**
- [ ] 安装程序（Inno Setup / NSIS）
- [ ] 用户手册
- [ ] 版本管理（语义化版本）

**阶段八验收标准：**
- 单文件可执行程序
- 首次运行向导完整
- 无依赖安装即可运行

---

## 里程碑时间表

```
第3周  [M1] 引擎核心就绪
       - 对象、命令、事件系统可运行
       - 通过命令行可进行基本交互

第5周  [M2] 数据模型完成
       - 武侠角色/物品/武学/地图模型就绪
       - 可创建完整角色

第8周  [M3] 玩法系统就绪
       - 探索/战斗/任务可完整体验
       - 可通过命令行完成游戏流程

第12周 [M4] GUI客户端就绪
       - 10个核心面板全部可用
       - 响应式UI正常工作

第15周 [M5] 内容填充完成
       - 可游玩Demo版本
       - 至少3小时游戏内容

第17周 [M6] 系统功能完整
       - 存档/后台管理可用
       - 开发者工具完备

第19周 [M7] 测试优化完成
       - Beta测试版本
       - 性能达标

第20周 [M8] 正式发布
       - v1.0可执行文件
       - 完整安装包
```

---

## 技术风险与应对

| 风险 | 影响 | 概率 | 应对策略 |
|:---|:---|:---|:---|
| Typeclass动态加载性能 | 高 | 中 | L1缓存 + 延迟加载，实测调优 |
| SQLite并发写入瓶颈 | 中 | 低 | WAL模式 + 批量写入 + 写时复制 |
| GUI渲染卡顿 | 中 | 中 | qasync桥接，耗时操作异步化 |
| 存档兼容性问题 | 高 | 中 | 版本化schema，惰性升级策略 |
| 战斗数值不平衡 | 中 | 高 | 自动化测试台，大量模拟验证 |
| PyInstaller打包失败 | 高 | 中 | 早期开始测试打包，hook文件 |
| PySide6与asyncio冲突 | 高 | 低 | qasync成熟方案，预留缓冲时间 |

---

## 开发工具与规范

### 代码规范
- Python 3.11+ 类型注解（mypy检查）
- Black代码格式化（行宽100）
- Ruff静态检查（启用所有规则）
- 异步函数统一`async/await`语法，禁用`asyncio.coroutine`

### 版本控制
- Git分支模型：main / develop / feature/* / release/*
- Commit规范：Conventional Commits
- PR代码审查（至少1人）

### 文档规范
- API文档：Google Style Docstrings
- 架构文档：PlantUML图表
- 更新日志：Keep a Changelog

---

## 后续迭代规划

### v1.1 内容扩展（2个月）
- 增加门派（星宿派完善、慕容世家、大理段氏）
- 更多主线剧情（分支+50%）
- 随机副本系统

### v1.2 系统增强（1个月）
- MOD支持（Python脚本扩展）
- 多语言本地化（英文版）
- 云存档同步

### v2.0 重大更新（4个月）
- 多周目继承系统
- LLM驱动的动态对话（本地模型）
- 沙盒式江湖世界（ procedurally generated）

---

*计划制定日期：2026-02-21*
*预计开发周期：20周*
*文档版本：v1.0*
