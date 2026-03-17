"""配置管理模块.

提供统一的配置管理功能，支持:
- YAML/JSON格式
- 支持环境检测
- 配置热重载(开发模式)
- 类型安全的配置访问
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal, TypeVar, cast, overload

import yaml
from watchdog.events import DirModifiedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src.utils.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class ConfigError(Exception):
    """配置错误异常."""

    pass


class ConfigNotFoundError(ConfigError):
    """配置项未找到异常."""

    pass


class ConfigTypeError(ConfigError):
    """配置类型错误异常."""

    pass


@dataclass
class DatabaseConfig:
    """数据库配置."""

    url: str = "sqlite+aiosqlite:///data/jinyong_mud.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_pre_ping: bool = True


@dataclass
class GameConfig:
    """游戏核心配置."""

    name: str = "金庸武侠MUD"
    version: str = "0.1.0"
    tick_rate: float = 0.1  # 游戏主循环tick间隔(秒)
    auto_save_interval: int = 300  # 自动保存间隔(秒)
    max_players: int = 1  # 单机版固定为1


@dataclass
class GuiConfig:
    """GUI界面配置."""

    theme: str = "default"
    font_family: str = "Microsoft YaHei"
    font_size: int = 14
    window_width: int = 1200
    window_height: int = 800
    fullscreen: bool = False
    locale: str = "zh_CN"


@dataclass
class LoggingConfig:
    """日志配置."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_dir: str = "logs"
    console_output: bool = True
    file_output: bool = True
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class Config:
    """应用主配置类.

    包含所有模块的配置项，支持序列化和反序列化。
    """

    # 环境设置
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = True

    # 各模块配置
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    game: GameConfig = field(default_factory=GameConfig)
    gui: GuiConfig = field(default_factory=GuiConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # 扩展配置(用于动态配置项)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典.

        Returns:
            配置的字典表示
        """
        result: dict[str, Any] = {
            "environment": self.environment,
            "debug": self.debug,
            "database": asdict(self.database),
            "game": asdict(self.game),
            "gui": asdict(self.gui),
            "logging": asdict(self.logging),
            "extra": self.extra,
        }
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """从字典创建配置.

        Args:
            data: 配置字典

        Returns:
            配置对象
        """
        config = cls()

        if "environment" in data:
            config.environment = cast(
                Literal["development", "testing", "production"],
                data["environment"],
            )
        if "debug" in data:
            config.debug = data["debug"]

        if "database" in data:
            config.database = DatabaseConfig(**data["database"])
        if "game" in data:
            config.game = GameConfig(**data["game"])
        if "gui" in data:
            config.gui = GuiConfig(**data["gui"])
        if "logging" in data:
            config.logging = LoggingConfig(**data["logging"])
        if "extra" in data:
            config.extra = data["extra"]

        return config


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变更处理器."""

    def __init__(self, config_path: Path, callback: Callable[[], Any]) -> None:
        """初始化处理器.

        Args:
            config_path: 配置文件路径
            callback: 配置变更回调函数
        """
        self.config_path = config_path
        self.callback = callback

    def on_modified(self, event: FileModifiedEvent | DirModifiedEvent) -> None:
        """处理文件修改事件.

        Args:
            event: 文件系统事件
        """
        src_path = event.src_path.decode() if isinstance(event.src_path, bytes) else event.src_path
        if not event.is_directory and Path(src_path) == self.config_path:
            logger.info(f"Config file changed: {self.config_path}")
            self.callback()


import threading


class ConfigManager:
    """配置管理器.

    管理配置的加载、保存和热重载。
    单例模式确保全局配置一致性。
    """

    _instance: ConfigManager | None = None
    _initialized: bool = False
    _lock = threading.Lock()

    CONFIG_FILES = [
        "config.yaml",
        "config.json",
        "config.local.yaml",
        "config.local.json",
    ]

    @classmethod
    def reset(cls) -> None:
        """重置单例实例（仅用于测试）.
        
        警告: 不要在生产代码中调用此方法！
        此方法用于测试隔离，确保每个测试有干净的单例状态。
        """
        with cls._lock:
            cls._instance = None
            cls._initialized = False

    @classmethod
    def get_instance(cls) -> ConfigManager:
        """获取单例实例（线程安全）.
        
        Returns:
            ConfigManager单例实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __new__(cls) -> ConfigManager:
        """创建单例实例."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化配置管理器."""
        if self._initialized:
            return

        self._config = Config()
        self._config_path: Path | None = None
        self._observer: Any = None
        self._callbacks: list[Callable[..., Any]] = []
        self._initialized = True

    @property
    def config(self) -> Config:
        """获取当前配置.

        Returns:
            当前配置对象
        """
        return self._config

    def _detect_environment(self) -> Literal["development", "testing", "production"]:
        """检测运行环境.

        Returns:
            检测到的环境名称
        """
        env = os.environ.get("JINYONG_MUD_ENV", "").lower()
        if env in ("dev", "development"):
            return "development"
        elif env in ("test", "testing"):
            return "testing"
        elif env in ("prod", "production"):
            return "production"

        # 根据sys.frozen检测
        if getattr(__import__("sys"), "frozen", False):
            return "production"

        return "development"

    def _find_config_file(self, config_dir: Path | str | None = None) -> Path | None:
        """查找配置文件.

        Args:
            config_dir: 配置目录，默认为当前工作目录

        Returns:
            找到的配置文件路径，未找到返回None
        """
        search_dir = Path(config_dir) if config_dir else Path.cwd()

        # 环境特定配置文件优先
        env = self._detect_environment()
        env_files = [
            f"config.{env}.yaml",
            f"config.{env}.json",
            f"config.{env}.local.yaml",
            f"config.{env}.local.json",
        ]

        for filename in env_files + self.CONFIG_FILES:
            config_path = search_dir / filename
            if config_path.exists():
                return config_path

        return None

    def _load_from_file(self, path: Path) -> dict[str, Any]:
        """从文件加载配置数据.

        Args:
            path: 配置文件路径

        Returns:
            配置字典

        Raises:
            ConfigError: 文件格式不支持或解析失败
        """
        suffix = path.suffix.lower()

        try:
            with open(path, encoding="utf-8") as f:
                if suffix in (".yaml", ".yml"):
                    return cast(dict[str, Any], yaml.safe_load(f) or {})
                elif suffix == ".json":
                    return cast(dict[str, Any], json.load(f))
                else:
                    raise ConfigError(f"Unsupported config file format: {suffix}")
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse YAML config: {e}") from e
        except json.JSONDecodeError as e:
            raise ConfigError(f"Failed to parse JSON config: {e}") from e
        except Exception as e:
            raise ConfigError(f"Failed to load config file: {e}") from e

    def _save_to_file(self, path: Path, data: dict[str, Any]) -> None:
        """保存配置到文件.

        Args:
            path: 目标文件路径
            data: 配置字典

        Raises:
            ConfigError: 保存失败
        """
        suffix = path.suffix.lower()

        try:
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                if suffix in (".yaml", ".yml"):
                    yaml.dump(data, f, allow_unicode=True, sort_keys=False, indent=2)
                elif suffix == ".json":
                    json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    raise ConfigError(f"Unsupported config file format: {suffix}")
        except Exception as e:
            raise ConfigError(f"Failed to save config file: {e}") from e

    def load(
        self,
        config_path: Path | str | None = None,
        auto_reload: bool = False,
    ) -> Config:
        """加载配置.

        Args:
            config_path: 配置文件路径，None则自动查找
            auto_reload: 是否启用热重载

        Returns:
            加载的配置对象
        """
        if config_path:
            self._config_path = Path(config_path)
            if not self._config_path.exists():
                raise ConfigNotFoundError(f"Config file not found: {config_path}")
        else:
            self._config_path = self._find_config_file()

        if self._config_path:
            logger.info(f"Loading config from: {self._config_path}")
            data = self._load_from_file(self._config_path)
            self._config = Config.from_dict(data)
        else:
            logger.info("No config file found, using default configuration")
            self._config = Config()
            self._config.environment = self._detect_environment()
            self._config.debug = self._config.environment == "development"

        # 设置环境变量
        os.environ["JINYONG_MUD_ENV"] = self._config.environment

        # 启用热重载
        if auto_reload and self._config_path:
            self._enable_hot_reload()

        return self._config

    def save(self, config_path: Path | str | None = None) -> None:
        """保存配置.

        Args:
            config_path: 目标文件路径，None则使用当前路径
        """
        path = Path(config_path) if config_path else self._config_path
        if not path:
            path = Path.cwd() / "config.yaml"

        logger.info(f"Saving config to: {path}")
        data = self._config.to_dict()
        self._save_to_file(path, data)
        self._config_path = path

    def _enable_hot_reload(self) -> None:
        """启用配置热重载."""
        if not self._config_path or self._observer:
            return

        self._observer = Observer()
        handler = ConfigFileHandler(self._config_path, self._reload_callback)
        self._observer.schedule(handler, str(self._config_path.parent), recursive=False)
        self._observer.start()
        logger.info(f"Hot reload enabled for: {self._config_path}")

    def _reload_callback(self) -> None:
        """配置重载回调."""
        try:
            if self._config_path:
                data = self._load_from_file(self._config_path)
                self._config = Config.from_dict(data)
                logger.info("Config reloaded successfully")

                # 触发注册的回调
                for callback in self._callbacks:
                    try:
                        callback(self._config)
                    except Exception as e:
                        logger.error(f"Config reload callback error: {e}")
        except Exception as e:
            logger.error(f"Failed to reload config: {e}")

    def reload(self) -> Config:
        """手动重新加载配置.

        Returns:
            重新加载后的配置对象
        """
        if self._config_path:
            data = self._load_from_file(self._config_path)
            self._config = Config.from_dict(data)
            logger.info("Config reloaded manually")
        return self._config

    def on_reload(self, callback: Callable[..., Any]) -> Callable[..., Any]:
        """注册配置重载回调.

        Args:
            callback: 配置变更时调用的回调函数

        Returns:
            装饰器函数
        """
        self._callbacks.append(callback)
        return callback

    def get(self, key: str, default: T | None = None) -> Any | T | None:
        """获取配置项.

        支持点号分隔的路径，如"database.url"。

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值或默认值
        """
        keys = key.split(".")
        value: Any = self._config.to_dict()

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    @overload
    def get_typed(self, key: str, type_: type[T]) -> T | None: ...

    @overload
    def get_typed(self, key: str, type_: type[T], default: T) -> T: ...

    def get_typed(
        self,
        key: str,
        type_: type[T],
        default: T | None = None,
    ) -> T | None:
        """获取指定类型的配置项.

        Args:
            key: 配置键
            type_: 期望的类型
            default: 默认值

        Returns:
            配置值或默认值

        Raises:
            ConfigTypeError: 类型不匹配
        """
        value = self.get(key, default)
        if value is None:
            return default

        if not isinstance(value, type_):
            raise ConfigTypeError(
                f"Config value for '{key}' expected {type_.__name__}, got {type(value).__name__}"
            )

        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置项.

        注意: 此方法仅修改内存中的配置，不会自动保存到文件。

        Args:
            key: 配置键，支持点号分隔的路径，如"game.name"
            value: 配置值
        """
        keys = key.split(".")
        data = self._config.to_dict()

        target = data
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        target[keys[-1]] = value
        self._config = Config.from_dict(data)

    def update(self, **kwargs: Any) -> None:
        """批量更新配置项.

        Args:
            **kwargs: 配置键值对
        """
        data = self._config.to_dict()
        data.update(kwargs)
        self._config = Config.from_dict(data)

    def stop(self) -> None:
        """停止配置管理器."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("Config manager stopped")


# 全局配置管理器实例
_manager = ConfigManager()


def load_config(
    config_path: Path | str | None = None,
    auto_reload: bool = False,
) -> Config:
    """加载配置.

    便捷函数，使用全局配置管理器。

    Args:
        config_path: 配置文件路径
        auto_reload: 是否启用热重载

    Returns:
        配置对象
    """
    return _manager.load(config_path, auto_reload)


def get_config() -> Config:
    """获取当前配置.

    Returns:
        当前配置对象
    """
    return _manager.config


def save_config(config_path: Path | str | None = None) -> None:
    """保存配置.

    Args:
        config_path: 目标文件路径
    """
    _manager.save(config_path)


def reload_config() -> Config:
    """重新加载配置.

    Returns:
        重新加载后的配置对象
    """
    return _manager.reload()
