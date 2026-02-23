"""配置管理单元测试."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from src.utils.config import (
    Config,
    ConfigError,
    ConfigManager,
    ConfigNotFoundError,
    DatabaseConfig,
    GameConfig,
    GuiConfig,
    LoggingConfig,
    load_config,
)


@pytest.fixture(autouse=True)
def reset_config_manager():
    """每个测试后重置配置管理器."""
    yield
    # 重置单例状态
    ConfigManager._instance = None
    ConfigManager._initialized = False


@pytest.fixture
def temp_config_file():
    """创建临时配置文件."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config_data = {
            "environment": "testing",
            "debug": True,
            "database": {
                "url": "sqlite+aiosqlite:///test.db",
                "echo": True,
                "pool_size": 3,
                "max_overflow": 5,
                "pool_pre_ping": True,
            },
            "game": {
                "name": "Test MUD",
                "version": "0.0.1",
                "tick_rate": 0.05,
                "auto_save_interval": 60,
                "max_players": 1,
            },
            "gui": {
                "theme": "dark",
                "font_family": "SimHei",
                "font_size": 16,
                "window_width": 800,
                "window_height": 600,
                "fullscreen": False,
                "locale": "zh_CN",
            },
            "logging": {
                "level": "DEBUG",
                "log_dir": "test_logs",
                "console_output": True,
                "file_output": False,
                "max_bytes": 1024,
                "backup_count": 1,
            },
            "extra": {"custom_key": "custom_value"},
        }
        yaml.dump(config_data, f)
        temp_path = f.name

    yield temp_path

    # 清理
    Path(temp_path).unlink(missing_ok=True)


class TestConfigDataclasses:
    """测试配置数据类."""

    def test_database_config_defaults(self):
        """测试数据库配置默认值."""
        config = DatabaseConfig()
        assert "sqlite" in config.url
        assert config.echo is False
        assert config.pool_size == 5

    def test_game_config_defaults(self):
        """测试游戏配置默认值."""
        config = GameConfig()
        assert config.name == "金庸武侠MUD"
        assert config.tick_rate == 0.1

    def test_gui_config_defaults(self):
        """测试GUI配置默认值."""
        config = GuiConfig()
        assert config.theme == "default"
        assert config.font_family == "Microsoft YaHei"

    def test_logging_config_defaults(self):
        """测试日志配置默认值."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.max_bytes == 10 * 1024 * 1024


class TestConfig:
    """测试主配置类."""

    def test_config_defaults(self):
        """测试配置默认值."""
        config = Config()
        assert config.environment == "development"
        assert config.debug is True
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.game, GameConfig)
        assert isinstance(config.gui, GuiConfig)
        assert isinstance(config.logging, LoggingConfig)

    def test_config_to_dict(self):
        """测试配置转字典."""
        config = Config()
        data = config.to_dict()
        assert data["environment"] == "development"
        assert "database" in data
        assert "game" in data

    def test_config_from_dict(self):
        """测试从字典创建配置."""
        data = {
            "environment": "production",
            "debug": False,
            "database": {"url": "test.db", "echo": True},
            "extra": {"key": "value"},
        }
        config = Config.from_dict(data)
        assert config.environment == "production"
        assert config.debug is False
        assert config.database.url == "test.db"
        assert config.extra == {"key": "value"}


class TestConfigManager:
    """测试配置管理器."""

    def test_singleton(self):
        """测试单例模式."""
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        assert manager1 is manager2

    def test_load_from_file(self, temp_config_file):
        """测试从文件加载配置."""
        manager = ConfigManager()
        config = manager.load(temp_config_file)

        assert config.environment == "testing"
        assert config.game.name == "Test MUD"
        assert config.gui.theme == "dark"
        assert config.logging.level == "DEBUG"

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件."""
        manager = ConfigManager()
        with pytest.raises(ConfigNotFoundError):
            manager.load("/nonexistent/path/config.yaml")

    def test_save_and_load(self, temp_config_file):
        """测试保存和加载配置."""
        manager = ConfigManager()

        # 修改配置
        config = Config()
        config.game.name = "Saved Game"
        manager._config = config

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_save:
            temp_path = temp_save.name
        manager.save(temp_path)

        # 重新加载
        manager2 = ConfigManager()
        loaded_config = manager2.load(temp_path)

        assert loaded_config.game.name == "Saved Game"

        # 清理
        Path(temp_path).unlink(missing_ok=True)

    def test_get_config_value(self, temp_config_file):
        """测试获取配置值."""
        manager = ConfigManager()
        manager.load(temp_config_file)

        assert manager.get("game.name") == "Test MUD"
        assert manager.get("database.pool_size") == 3
        assert manager.get("nonexistent.key", "default") == "default"
        assert manager.get("nonexistent.key") is None

    def test_get_typed_value(self, temp_config_file):
        """测试获取指定类型的配置值."""
        manager = ConfigManager()
        manager.load(temp_config_file)

        assert manager.get_typed("game.max_players", int) == 1
        assert manager.get_typed("debug", bool) is True
        assert manager.get_typed("nonexistent", str, "default") == "default"

    def test_update_config(self):
        """测试更新配置."""
        manager = ConfigManager()
        manager.load()

        manager.set("game.name", "Updated Game")
        assert manager.get("game.name") == "Updated Game"

        manager.update(environment="staging", debug=False)
        assert manager.get("environment") == "staging"
        assert manager.get("debug") is False


class TestConfigHelperFunctions:
    """测试配置辅助函数."""

    def test_load_config(self, temp_config_file):
        """测试load_config函数."""
        config = load_config(temp_config_file)
        assert config.environment == "testing"

    def test_detect_environment(self):
        """测试环境检测."""
        import os

        manager = ConfigManager()

        # 测试环境变量
        original_env = os.environ.get("JINYONG_MUD_ENV")
        os.environ["JINYONG_MUD_ENV"] = "production"
        assert manager._detect_environment() == "production"

        os.environ["JINYONG_MUD_ENV"] = "testing"
        assert manager._detect_environment() == "testing"

        # 恢复
        if original_env:
            os.environ["JINYONG_MUD_ENV"] = original_env
        else:
            del os.environ["JINYONG_MUD_ENV"]

    def test_config_error(self):
        """测试配置异常."""
        with pytest.raises(ConfigError):
            raise ConfigError("Test error")

        with pytest.raises(ConfigNotFoundError):
            raise ConfigNotFoundError("Not found")
