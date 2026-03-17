"""配置管理单元测试."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import yaml

from src.utils.config import (
    Config,
    ConfigError,
    ConfigFileHandler,
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


# --- Merged from test_config_coverage.py ---

class TestConfigFromDict:
    """Config.from_dict测试."""

    def test_from_dict(self):
        """测试从字典创建配置."""
        data = {
            "database": {"url": "sqlite:///test.db"},
            "game": {"tick_rate": 2.0},
            "gui": {"theme": "dark"},
            "logging": {"level": "DEBUG"},
        }
        config = Config.from_dict(data)
        
        assert config.database.url == "sqlite:///test.db"
        assert config.game.tick_rate == 2.0
        assert config.gui.theme == "dark"
        assert config.logging.level == "DEBUG"


class TestConfigFileHandler:
    """ConfigFileHandler测试."""

    def test_on_modified(self):
        """测试文件修改处理."""
        callback = Mock()
        handler = ConfigFileHandler(Path("test.yaml"), callback)
        
        # 模拟文件修改事件
        event = MagicMock()
        event.is_directory = False
        event.src_path = "test.yaml"
        
        handler.on_modified(event)
        callback.assert_called_once()

    def test_on_modified_bytes_path(self):
        """测试bytes路径处理."""
        callback = Mock()
        handler = ConfigFileHandler(Path("test.yaml"), callback)
        
        event = MagicMock()
        event.is_directory = False
        event.src_path = b"test.yaml"
        
        handler.on_modified(event)
        callback.assert_called_once()

    def test_on_modified_wrong_file(self):
        """测试修改其他文件."""
        callback = Mock()
        handler = ConfigFileHandler(Path("test.yaml"), callback)
        
        event = MagicMock()
        event.is_directory = False
        event.src_path = "other.yaml"
        
        handler.on_modified(event)
        callback.assert_not_called()


class TestConfigManagerEnvironment:
    """ConfigManager环境检测测试."""

    def test_detect_environment_dev(self):
        """测试开发环境检测."""
        manager = ConfigManager()
        
        with patch.dict(os.environ, {"JINYONG_MUD_ENV": "dev"}):
            result = manager._detect_environment()
            assert result == "development"

    def test_detect_environment_test(self):
        """测试测试环境检测."""
        manager = ConfigManager()
        
        with patch.dict(os.environ, {"JINYONG_MUD_ENV": "test"}):
            result = manager._detect_environment()
            assert result == "testing"

    def test_detect_environment_prod(self):
        """测试生产环境检测."""
        manager = ConfigManager()
        
        with patch.dict(os.environ, {"JINYONG_MUD_ENV": "production"}):
            result = manager._detect_environment()
            assert result == "production"

    def test_detect_environment_frozen(self):
        """测试frozen检测生产环境."""
        manager = ConfigManager()
        
        with patch("sys.frozen", True, create=True):
            result = manager._detect_environment()
            assert result == "production"

    def test_detect_environment_default(self):
        """测试默认环境."""
        manager = ConfigManager()
        
        with patch.dict(os.environ, {}, clear=True):
            with patch("sys.frozen", False, create=True):
                result = manager._detect_environment()
                assert result == "development"


class TestConfigManagerCallbacks:
    """ConfigManager回调测试."""

    def test_config_property(self):
        """测试配置属性."""
        ConfigManager._instance = None
        ConfigManager._initialized = False
        
        manager = ConfigManager()
        config = manager.config
        assert config is not None
        assert isinstance(config, Config)


class TestConfigManagerSaveLoad:
    """ConfigManager保存加载测试."""

    def test_save_yaml(self, tmp_path: Path):
        """测试保存YAML配置."""
        ConfigManager._instance = None
        ConfigManager._initialized = False
        
        manager = ConfigManager()
        config_path = tmp_path / "test_config.yaml"
        
        result = manager.save(config_path)
        assert result is True or result is None  # None表示成功但没有返回值
        assert config_path.exists()

    def test_save_json(self, tmp_path: Path):
        """测试保存JSON配置."""
        ConfigManager._instance = None
        ConfigManager._initialized = False
        
        manager = ConfigManager()
        config_path = tmp_path / "test_config.json"
        
        result = manager.save(config_path)
        assert result is True or result is None
        assert config_path.exists()

    def test_save_invalid_extension(self, tmp_path: Path):
        """测试保存无效扩展名."""
        ConfigManager._instance = None
        ConfigManager._initialized = False
        
        manager = ConfigManager()
        config_path = tmp_path / "test_config.txt"
        
        from src.utils.config import ConfigError
        with pytest.raises(ConfigError):
            manager.save(config_path)

    def test_load_file_not_found(self):
        """测试加载不存在的文件."""
        ConfigManager._instance = None
        ConfigManager._initialized = False
        
        manager = ConfigManager()
        from src.utils.config import ConfigNotFoundError
        with pytest.raises(ConfigNotFoundError):
            manager.load("/nonexistent/config.yaml")


class TestConfigHelperFunctions:
    """辅助函数测试."""

    def test_load_config(self, tmp_path: Path):
        """测试load_config函数."""
        from src.utils.config import load_config
        
        config_path = tmp_path / "config.yaml"
        config_path.write_text("database:\n  url: sqlite:///test.db\n")
        
        with patch.object(ConfigManager, 'load') as mock_load:
            mock_load.return_value = True
            config = load_config(config_path)
            assert config is not None

    def test_get_config(self):
        """测试get_config函数."""
        from src.utils.config import get_config
        
        config = get_config()
        assert config is not None
        assert isinstance(config, Config)

    def test_config_error(self):
        """测试ConfigError异常."""
        from src.utils.config import ConfigError
        
        error = ConfigError("test error")
        assert str(error) == "test error"


class TestConfigNestedAccess:
    """Config嵌套访问测试."""

    def test_nested_attribute_access(self):
        """测试嵌套属性访问."""
        config = Config()
        
        # 访问嵌套属性
        assert hasattr(config.database, 'url')
        assert hasattr(config.game, 'tick_rate')
        assert hasattr(config.gui, 'theme')
        assert hasattr(config.logging, 'level')


# 清理单例状态
@pytest.fixture(autouse=True)
def reset_singleton():
    """重置ConfigManager单例状态."""
    ConfigManager._instance = None
    ConfigManager._initialized = False
    yield
    ConfigManager._instance = None
    ConfigManager._initialized = False
