# 项目骨架

## 目录结构

```
jinyong_mud/
├── src/
│   ├── engine/              # 游戏引擎核心
│   │   ├── __init__.py
│   │   ├── core/            # 核心基类
│   │   │   ├── __init__.py
│   │   │   ├── typeclass.py     # Typeclass系统
│   │   │   ├── objects.py       # ObjectManager
│   │   │   ├── engine.py        # GameEngine
│   │   │   └── ...
│   │   ├── database/        # 数据库层
│   │   │   ├── __init__.py
│   │   │   ├── connection.py    # 连接管理
│   │   │   └── models.py        # ORM模型
│   │   ├── commands/        # 命令系统
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Command基类
│   │   │   ├── cmdset.py        # CmdSet
│   │   │   └── handler.py       # 命令处理器
│   │   ├── events/          # 事件调度
│   │   │   ├── __init__.py
│   │   │   └── scheduler.py     # EventScheduler
│   │   └── save/            # 存档系统
│   │       ├── __init__.py
│   │       └── manager.py       # SaveManager
│   │
│   ├── gui/                 # PySide6图形界面
│   │   ├── __init__.py
│   │   ├── main_window.py       # 主窗口
│   │   ├── async_bridge.py      # asyncio桥接
│   │   ├── panels/          # 各功能面板
│   │   │   ├── __init__.py
│   │   │   ├── main_view.py
│   │   │   ├── status.py
│   │   │   ├── compass.py
│   │   │   ├── inventory.py
│   │   │   └── ...
│   │   └── themes/          # QSS样式主题
│   │       └── manager.py
│   │
│   ├── game/                # 游戏具体实现
│   │   ├── __init__.py
│   │   ├── typeclasses/     # 武侠特色类型类
│   │   │   ├── __init__.py
│   │   │   ├── character.py     # 角色
│   │   │   ├── equipment.py     # 装备
│   │   │   ├── item.py          # 物品
│   │   │   ├── room.py          # 房间
│   │   │   └── wuxue.py         # 武学
│   │   ├── commands/        # 游戏命令
│   │   │   ├── __init__.py
│   │   │   └── basic.py         # 基础命令
│   │   ├── combat/          # 战斗系统
│   │   │   ├── __init__.py
│   │   │   ├── core.py          # CombatInstance
│   │   │   ├── calculator.py    # 数值计算
│   │   │   └── buff.py          # BUFF系统
│   │   ├── quest/           # 任务系统
│   │   │   ├── __init__.py
│   │   │   └── core.py
│   │   ├── npc/             # NPC系统
│   │   │   ├── __init__.py
│   │   │   ├── core.py
│   │   │   └── behavior_tree.py
│   │   └── world/           # 世界数据
│   │       ├── __init__.py
│   │       ├── loader.py        # 动态加载
│   │       └── pathfinding.py   # 寻路
│   │
│   └── utils/               # 工具函数
│       ├── __init__.py
│       ├── config.py            # 配置管理
│       └── logging.py           # 日志配置
│
├── tests/                   # 单元测试
│   ├── __init__.py
│   ├── unit/               # 单元测试
│   └── integration/        # 集成测试
│
├── docs/                    # 文档
├── tools/                   # 开发工具
├── resources/               # 资源文件
│   ├── images/
│   ├── sounds/
│   ├── themes/             # QSS主题
│   ├── world/              # 世界数据YAML
│   └── wuxue/              # 武学数据YAML
│
├── scripts/                 # 辅助脚本
├── pyproject.toml          # 项目配置
├── README.md
└── .gitignore
```

## pyproject.toml

```toml
[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.poetry]
name = "jinyong-mud"
version = "0.1.0"
description = "金庸武侠文字MUD单机版"
authors = ["Your Name <you@example.com>"]
readme = "README.md"
packages = [{include = "src"}]

[tool.poetry.dependencies]
python = "^3.11"
SQLAlchemy = {version = "^2.0", extras = ["asyncio"]}
aiosqlite = "^0.19"
PySide6 = "^6.6"
qasync = "^0.27"
msgpack = "^1.0"
jieba = "^0.42"
alembic = "^1.13"
pyyaml = "^6.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4"
pytest-asyncio = "^0.21"
pytest-cov = "^4.1"
black = "^23.0"
ruff = "^0.1"
mypy = "^1.7"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N", "D", "UP", "B", "C4", "SIM"]
ignore = ["D100", "D104", "D105"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

## 配置文件

```yaml
# config/game.yaml
# 游戏配置

game:
  name: "金庸武侠MUD"
  version: "0.1.0"
  time_scale: 1.0  # 时间流速

database:
  path: "data/game.db"
  wal_mode: true
  cache_size: 64000  # 64MB

logging:
  level: "INFO"
  log_dir: "logs"
  max_bytes: 10485760  # 10MB
  backup_count: 5

world:
  data_path: "resources/world"
  load_range: 3
  unload_delay: 60
```

## 日志配置

```python
# src/utils/logging.py
import logging
import logging.handlers
from pathlib import Path


def setup_logging(
    level: str = "INFO",
    log_dir: Path = Path("logs"),
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """配置日志系统
    
    Args:
        level: 日志级别
        log_dir: 日志目录
        max_bytes: 单个日志文件最大大小
        backup_count: 备份文件数量
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # 格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 文件处理器（按模块分离）
    modules = ["engine", "game", "gui"]
    for module in modules:
        handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{module}.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        handler.setFormatter(formatter)
        
        module_logger = logging.getLogger(f"src.{module}")
        module_logger.addHandler(handler)
        module_logger.setLevel(logging.DEBUG)
    
    # 控制台处理器
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root_logger.addHandler(console)
```

## 配置管理

```python
# src/utils/config.py
import yaml
import json
from pathlib import Path
from typing import Any, Optional


class ConfigManager:
    """游戏配置管理器
    
    支持YAML/JSON配置加载和热重载
    """
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._data: dict[str, Any] = {}
        self._callbacks: list[callable] = []
    
    def load(self) -> dict[str, Any]:
        """加载配置"""
        if not self.config_path.exists():
            self._data = {}
            return self._data
        
        suffix = self.config_path.suffix.lower()
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            if suffix in (".yaml", ".yml"):
                self._data = yaml.safe_load(f) or {}
            elif suffix == ".json":
                self._data = json.load(f)
            else:
                raise ValueError(f"不支持的配置文件格式: {suffix}")
        
        return self._data
    
    def save(self) -> None:
        """保存配置"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        suffix = self.config_path.suffix.lower()
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            if suffix in (".yaml", ".yml"):
                yaml.dump(self._data, f, allow_unicode=True, default_flow_style=False)
            elif suffix == ".json":
                json.dump(self._data, f, ensure_ascii=False, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号路径）"""
        keys = key.split(".")
        value = self._data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split(".")
        data = self._data
        
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        
        data[keys[-1]] = value
    
    def watch(self, callback: callable) -> None:
        """注册配置变更回调"""
        self._callbacks.append(callback)
    
    def _notify_change(self) -> None:
        """通知配置变更"""
        for callback in self._callbacks:
            try:
                callback(self._data)
            except Exception:
                pass
```

## .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
.venv/
ENV/
env/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Logs
logs/
*.log

# Data
data/
saves/
*.db
*.db-journal
*.db-wal
*.db-shm

# OS
.DS_Store
Thumbs.db

# Test
.coverage
htmlcov/
.pytest_cache/
```
