"""Config 补充测试 - 提高覆盖率.

测试config.py中未被覆盖的代码路径。
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.utils.config import Config, ConfigFileHandler, ConfigManager


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
