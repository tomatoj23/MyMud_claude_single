"""日志系统模块.

提供统一的日志配置和管理功能，支持:
- 按模块分离日志
- 文件+控制台双输出
- 日志轮转(10MB，保留5份)
- 开发模式热重载
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Literal


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器.

    为控制台输出添加ANSI颜色代码，提高可读性。
    """

    # ANSI颜色代码
    COLORS = {
        "DEBUG": "\033[36m",      # 青色
        "INFO": "\033[32m",       # 绿色
        "WARNING": "\033[33m",    # 黄色
        "ERROR": "\033[31m",      # 红色
        "CRITICAL": "\033[35m",   # 洋红
        "RESET": "\033[0m",       # 重置
    }

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        use_colors: bool = True,
    ) -> None:
        """初始化彩色格式化器.

        Args:
            fmt: 日志格式字符串
            datefmt: 日期格式字符串
            use_colors: 是否使用颜色
        """
        super().__init__(fmt, datefmt)
        self._use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录.

        Args:
            record: 日志记录对象

        Returns:
            格式化后的日志字符串
        """
        if self._use_colors:
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        return super().format(record)


class LogConfig:
    """日志配置类.

    管理日志系统的配置参数。
    """

    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    DEFAULT_BACKUP_COUNT = 5

    def __init__(
        self,
        level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
        log_dir: Path | str = "logs",
        console_output: bool = True,
        file_output: bool = True,
        max_bytes: int = DEFAULT_MAX_BYTES,
        backup_count: int = DEFAULT_BACKUP_COUNT,
        format_str: str = DEFAULT_FORMAT,
        date_format: str = DEFAULT_DATE_FORMAT,
    ) -> None:
        """初始化日志配置.

        Args:
            level: 日志级别
            log_dir: 日志目录路径
            console_output: 是否输出到控制台
            file_output: 是否输出到文件
            max_bytes: 单个日志文件最大字节数
            backup_count: 保留的备份文件数量
            format_str: 日志格式字符串
            date_format: 日期格式字符串
        """
        self.level = getattr(logging, level)
        self.log_dir = Path(log_dir)
        self.console_output = console_output
        self.file_output = file_output
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.format_str = format_str
        self.date_format = date_format


class LoggingManager:
    """日志管理器.

    单例模式管理整个应用的日志配置。
    支持按模块分离日志输出。
    """

    _instance: LoggingManager | None = None
    _initialized: bool = False

    def __new__(cls) -> LoggingManager:
        """创建单例实例."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """初始化日志管理器."""
        if self._initialized:
            return
        self._config: LogConfig = LogConfig()
        self._loggers: dict[str, logging.Logger] = {}
        self._handlers: list[logging.Handler] = []
        self._initialized = True

    def configure(self, config: LogConfig) -> None:
        """配置日志系统.

        Args:
            config: 日志配置对象
        """
        self._config = config
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """设置日志处理器."""
        self._handlers = []

        # 创建日志目录
        if self._config.file_output:
            self._config.log_dir.mkdir(parents=True, exist_ok=True)

        # 创建格式化器
        console_formatter = ColoredFormatter(
            self._config.format_str,
            self._config.date_format,
            use_colors=True,
        )
        file_formatter = ColoredFormatter(
            self._config.format_str,
            self._config.date_format,
            use_colors=False,
        )

        # 控制台处理器
        if self._config.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self._config.level)
            console_handler.setFormatter(console_formatter)
            self._handlers.append(console_handler)

        # 文件处理器(根日志)
        if self._config.file_output:
            root_log_file = self._config.log_dir / "jinyong_mud.log"
            file_handler = logging.handlers.RotatingFileHandler(
                root_log_file,
                maxBytes=self._config.max_bytes,
                backupCount=self._config.backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(self._config.level)
            file_handler.setFormatter(file_formatter)
            self._handlers.append(file_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器.

        Args:
            name: 日志记录器名称，通常使用模块名

        Returns:
            配置好的日志记录器
        """
        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(self._config.level)
        logger.propagate = False

        # 清除现有处理器
        logger.handlers.clear()

        # 添加通用处理器
        for handler in self._handlers:
            logger.addHandler(handler)

        # 添加模块专属文件处理器
        if self._config.file_output:
            module_file = self._config.log_dir / f"{name.replace('.', '_')}.log"
            module_handler = logging.handlers.RotatingFileHandler(
                module_file,
                maxBytes=self._config.max_bytes,
                backupCount=self._config.backup_count,
                encoding="utf-8",
            )
            module_handler.setLevel(self._config.level)
            module_handler.setFormatter(
                ColoredFormatter(
                    self._config.format_str,
                    self._config.date_format,
                    use_colors=False,
                )
            )
            logger.addHandler(module_handler)

        self._loggers[name] = logger
        return logger

    def reload(self) -> None:
        """重新加载日志配置(热重载)."""
        self._setup_handlers()
        for logger in self._loggers.values():
            logger.handlers.clear()
            for handler in self._handlers:
                logger.addHandler(handler)

    def shutdown(self) -> None:
        """关闭所有日志处理器.

        清理所有日志记录器的handler，关闭文件句柄。
        在应用程序退出或测试结束时调用。
        """
        # 关闭所有缓存的logger的handlers
        for logger in list(self._loggers.values()):
            for handler in logger.handlers[:]:
                try:
                    handler.flush()
                    handler.close()
                except Exception:
                    pass
                logger.removeHandler(handler)

        # 关闭通用handlers
        for handler in self._handlers[:]:
            try:
                handler.flush()
                handler.close()
            except Exception:
                pass

        # 清理根logger的handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            try:
                handler.flush()
                handler.close()
            except Exception:
                pass
            root_logger.removeHandler(handler)

        self._handlers.clear()
        self._loggers.clear()
        self._initialized = False
        LoggingManager._instance = None


# 全局日志管理器实例
_manager = LoggingManager()


def setup_logging(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
    log_dir: Path | str = "logs",
    console_output: bool = True,
    file_output: bool = True,
    **kwargs: Any,
) -> None:
    """设置日志系统.

    这是配置日志系统的主入口函数。

    Args:
        level: 日志级别
        log_dir: 日志目录路径
        console_output: 是否输出到控制台
        file_output: 是否输出到文件
        **kwargs: 其他配置参数

    Example:
        >>> setup_logging(level="DEBUG", log_dir="logs")
    """
    config = LogConfig(
        level=level,
        log_dir=log_dir,
        console_output=console_output,
        file_output=file_output,
        **kwargs,
    )
    _manager.configure(config)

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(config.level)
    root_logger.handlers.clear()

    for handler in _manager._handlers:
        root_logger.addHandler(handler)

    # 记录初始化信息
    logger = get_logger(__name__)
    logger.info(f"Logging system initialized with level={level}, log_dir={log_dir}")


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器.

    Args:
        name: 日志记录器名称，建议使用__name__

    Returns:
        配置好的日志记录器

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("This is an info message")
    """
    return _manager.get_logger(name)


def reload_logging() -> None:
    """重新加载日志配置(热重载).

    在开发模式下修改配置后调用此函数使配置生效。
    """
    _manager.reload()
    logger = get_logger(__name__)
    logger.info("Logging configuration reloaded")


def shutdown_logging() -> None:
    """关闭日志系统.

    清理所有日志处理器，关闭文件句柄。
    在应用程序退出时调用。
    """
    _manager.shutdown()
