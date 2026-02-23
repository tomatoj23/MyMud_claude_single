"""日志系统单元测试."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import pytest

from src.utils.logging import (
    ColoredFormatter,
    LogConfig,
    LoggingManager,
    get_logger,
    setup_logging,
    shutdown_logging,
)


@pytest.fixture(autouse=True)
def reset_logging_manager():
    """每个测试后重置日志管理器."""
    yield
    # 测试结束后关闭所有日志处理器
    shutdown_logging()


class TestColoredFormatter:
    """测试彩色格式化器."""

    def test_format_with_colors(self):
        """测试带颜色的格式化."""
        formatter = ColoredFormatter(
            "%(levelname)s - %(message)s",
            use_colors=True,
        )
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert "INFO" in result
        assert "Test message" in result
        assert "\033[" in result  # ANSI颜色代码

    def test_format_without_colors(self):
        """测试不带颜色的格式化."""
        formatter = ColoredFormatter(
            "%(levelname)s - %(message)s",
            use_colors=False,
        )
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert "INFO" in result
        assert "Test message" in result
        assert "\033[" not in result  # 无ANSI颜色代码


class TestLogConfig:
    """测试日志配置."""

    def test_default_config(self):
        """测试默认配置."""
        config = LogConfig()
        assert config.level == logging.INFO
        assert config.log_dir == Path("logs")
        assert config.console_output is True
        assert config.file_output is True
        assert config.max_bytes == 10 * 1024 * 1024
        assert config.backup_count == 5

    def test_custom_config(self):
        """测试自定义配置."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LogConfig(
                level="DEBUG",
                log_dir=tmpdir,
                console_output=False,
                file_output=True,
                max_bytes=1024,
                backup_count=3,
            )
            assert config.level == logging.DEBUG
            assert config.console_output is False
            assert config.max_bytes == 1024
            assert config.backup_count == 3


class TestLoggingManager:
    """测试日志管理器."""

    def test_singleton(self):
        """测试单例模式."""
        # 注意: 由于单例模式，这里创建新实例实际上返回同一个对象
        manager1 = LoggingManager()
        manager2 = LoggingManager()
        assert manager1 is manager2

    def test_get_logger(self):
        """测试获取日志记录器."""
        tmpdir = tempfile.mkdtemp()
        try:
            setup_logging(
                level="DEBUG",
                log_dir=tmpdir,
                console_output=False,
                file_output=True,
            )

            logger = get_logger("test.module")
            assert logger.name == "test.module"
            assert logger.level == logging.DEBUG

            # 测试日志写入
            logger.info("Test message")

            # 验证日志文件创建
            log_file = Path(tmpdir) / "test_module.log"
            assert log_file.exists()

            content = log_file.read_text(encoding="utf-8")
            assert "Test message" in content
        finally:
            # 先关闭日志处理器，再清理临时目录
            shutdown_logging()
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_logger_caching(self):
        """测试日志记录器缓存."""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(
                level="INFO",
                log_dir=tmpdir,
                console_output=False,
                file_output=False,
            )

            logger1 = get_logger("cached.module")
            logger2 = get_logger("cached.module")

            # 由于单例模式，应该是同一个logger对象
            assert logger1 is logger2


class TestSetupLogging:
    """测试日志设置函数."""

    def test_setup_logging(self):
        """测试设置日志系统."""
        tmpdir = tempfile.mkdtemp()
        try:
            setup_logging(
                level="DEBUG",
                log_dir=tmpdir,
                console_output=False,
                file_output=True,
            )

            logger = get_logger("setup.test")
            logger.debug("Debug message")
            logger.info("Info message")

            # 验证根日志文件
            root_log = Path(tmpdir) / "jinyong_mud.log"
            assert root_log.exists()

            content = root_log.read_text(encoding="utf-8")
            # 验证日志内容写入
            assert "Debug message" in content
            assert "Info message" in content
        finally:
            # 先关闭日志处理器，再清理临时目录
            shutdown_logging()
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_setup_logging_levels(self):
        """测试不同日志级别."""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(
                level="WARNING",
                log_dir=tmpdir,
                console_output=False,
                file_output=False,
            )

            logger = get_logger("level.test")
            assert logger.level == logging.WARNING


class TestLoggingIntegration:
    """日志系统集成测试."""

    @pytest.mark.slow
    def test_log_rotation(self):
        """测试日志轮转功能."""
        tmpdir = tempfile.mkdtemp()
        try:
            setup_logging(
                level="DEBUG",
                log_dir=tmpdir,
                console_output=False,
                file_output=True,
                max_bytes=100,  # 很小的限制以便测试轮转
                backup_count=2,
            )

            logger = get_logger("rotation.test")

            # 写入足够大的内容触发轮转
            for i in range(20):
                logger.info(f"Large message {i}: " + "x" * 50)

            # 验证轮转文件创建
            log_dir = Path(tmpdir)
            log_files = list(log_dir.glob("rotation_test.log*"))
            assert len(log_files) > 1
        finally:
            # 先关闭日志处理器，再清理临时目录
            shutdown_logging()
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_multiple_modules(self):
        """测试多模块日志分离."""
        tmpdir = tempfile.mkdtemp()
        try:
            setup_logging(
                level="INFO",
                log_dir=tmpdir,
                console_output=False,
                file_output=True,
            )

            logger1 = get_logger("module.one")
            logger2 = get_logger("module.two")

            logger1.info("Message from module one")
            logger2.info("Message from module two")

            # 验证各自的日志文件
            log1 = Path(tmpdir) / "module_one.log"
            log2 = Path(tmpdir) / "module_two.log"

            assert log1.exists()
            assert log2.exists()

            content1 = log1.read_text(encoding="utf-8")
            content2 = log2.read_text(encoding="utf-8")

            assert "module one" in content1
            assert "module two" in content2
        finally:
            # 先关闭日志处理器，再清理临时目录
            shutdown_logging()
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
