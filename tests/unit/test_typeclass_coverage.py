"""TypeclassBase 补充测试 - 提高覆盖率.

测试typeclass.py中未被覆盖的代码路径。
"""

from __future__ import annotations

from unittest.mock import MagicMock, Mock

import pytest
from unittest import mock

from src.engine.core.typeclass import TypeclassBase, TypeclassLoader


class TestAttributeHandlerErrors:
    """AttributeHandler错误处理测试."""

    def test_get_nonexistent_attribute(self, mock_manager, mock_db_model):
        """测试获取不存在的属性."""
        obj = TypeclassBase(mock_manager, mock_db_model)
        
        # 获取不存在的属性应返回None
        result = obj.db.get("nonexistent")
        assert result is None

    def test_get_with_default(self, mock_manager, mock_db_model):
        """测试获取属性带默认值."""
        obj = TypeclassBase(mock_manager, mock_db_model)
        
        result = obj.db.get("nonexistent", default="default_value")
        assert result == "default_value"


class TestTypeclassProperties:
    """Typeclass属性测试."""

    def test_location_none(self, mock_manager, mock_db_model):
        """测试location为None."""
        mock_db_model.location_id = None
        obj = TypeclassBase(mock_manager, mock_db_model)
        
        assert obj.location is None

    def test_location_setter_invalid_type(self, mock_manager, mock_db_model):
        """测试设置无效类型的location."""
        obj = TypeclassBase(mock_manager, mock_db_model)
        
        with pytest.raises(TypeError, match="location必须是TypeclassBase实例或None"):
            obj.location = "invalid"

    def test_location_setter_with_at_move_false(self, mock_manager, mock_db_model):
        """测试at_move返回False时阻止移动."""
        obj = TypeclassBase(mock_manager, mock_db_model)
        
        # 创建目标对象
        target = MagicMock(spec=TypeclassBase)
        target.id = 2
        
        # 重写at_move返回False
        obj.at_move = lambda dest: False
        
        old_location = obj.location
        obj.location = target
        
        # 位置应该没有变化
        assert obj.location == old_location

    def test_location_setter_triggers_hooks(self, mock_manager, mock_db_model):
        """测试移动触发钩子函数."""
        obj = TypeclassBase(mock_manager, mock_db_model)
        
        moved_called = []
        obj.at_moved = lambda src: moved_called.append(src)
        
        target = MagicMock(spec=TypeclassBase)
        target.id = 2
        
        obj.location = target
        
        assert len(moved_called) == 1

    def test_contents_with_invalid_id(self, mock_manager, mock_db_model):
        """测试contents包含无效ID."""
        # 模拟一个无效的content ID
        content_model = MagicMock()
        content_model.id = 999
        mock_db_model.contents = [content_model]
        
        mock_manager.get.return_value = None  # 返回None表示对象不存在
        
        obj = TypeclassBase(mock_manager, mock_db_model)
        contents = obj.contents
        
        assert len(contents) == 0


class TestSearchContents:
    """search_contents测试."""

    async def test_search_contents_found(self, mock_manager, mock_db_model):
        """测试找到内容."""
        obj = TypeclassBase(mock_manager, mock_db_model)
        
        # 创建mock内容
        content = MagicMock(spec=TypeclassBase)
        content.key = "target_key"
        
        # Mock manager.find 方法返回包含content的列表
        async def async_find(**kwargs):
            return [content]
        mock_manager.find = async_find
        
        result = await obj.search_contents("target_key")
        assert result == content

    async def test_search_contents_not_found(self, mock_manager, mock_db_model):
        """测试未找到内容."""
        obj = TypeclassBase(mock_manager, mock_db_model)
        
        # Mock空contents
        with mock.patch.object(
            TypeclassBase, 'contents',
            new_callable=mock.PropertyMock,
            return_value=[]
        ):
            result = await obj.search_contents("nonexistent")
            assert result is None


class TestDirtyMechanism:
    """脏数据机制测试."""

    def test_clean_dirty(self, mock_manager, mock_db_model):
        """测试清除脏数据标记."""
        obj = TypeclassBase(mock_manager, mock_db_model)
        
        obj.mark_dirty()
        assert obj.is_dirty() is True
        
        obj.clean_dirty()
        assert obj.is_dirty() is False


class TestSerialization:
    """序列化测试."""

    def test_to_db_dict(self, mock_manager, mock_db_model):
        """测试转换为数据库字典."""
        mock_db_model.id = 1
        mock_db_model.key = "test"
        mock_db_model.location_id = None
        mock_db_model.attributes = {}
        
        obj = TypeclassBase(mock_manager, mock_db_model)
        result = obj.to_db_dict()
        
        assert result["id"] == 1
        assert result["key"] == "test"
        assert "typeclass_path" in result


class TestLifecycleHooks:
    """生命周期钩子测试."""

    def test_at_init_default(self, mock_manager, mock_db_model):
        """测试默认at_init."""
        obj = TypeclassBase(mock_manager, mock_db_model)
        # 默认实现应该不抛出异常
        obj.at_init()

    def test_at_delete_default(self, mock_manager, mock_db_model):
        """测试默认at_delete."""
        obj = TypeclassBase(mock_manager, mock_db_model)
        obj.at_delete()

    def test_at_move_default(self, mock_manager, mock_db_model):
        """测试默认at_move返回True."""
        obj = TypeclassBase(mock_manager, mock_db_model)
        result = obj.at_move(MagicMock())
        assert result is True

    def test_at_moved_default(self, mock_manager, mock_db_model):
        """测试默认at_moved."""
        obj = TypeclassBase(mock_manager, mock_db_model)
        obj.at_moved(None)

    def test_at_desc_default(self, mock_manager, mock_db_model):
        """测试默认at_desc."""
        mock_db_model.key = "test_object"
        obj = TypeclassBase(mock_manager, mock_db_model)
        result = obj.at_desc(MagicMock())
        assert result == "test_object"

    def test_msg_default(self, mock_manager, mock_db_model):
        """测试默认msg."""
        obj = TypeclassBase(mock_manager, mock_db_model)
        # 默认实现应该不抛出异常
        obj.msg("test message")


class TestRepr:
    """__repr__测试."""

    def test_repr(self, mock_manager, mock_db_model):
        """测试字符串表示."""
        mock_db_model.id = 42
        mock_db_model.key = "test"
        obj = TypeclassBase(mock_manager, mock_db_model)
        
        result = repr(obj)
        assert "TypeclassBase" in result
        assert "42" in result
        assert "test" in result


class TestTypeclassLoaderErrors:
    """TypeclassLoader错误测试."""

    def test_load_invalid_path_format(self):
        """测试无效路径格式."""
        with pytest.raises(ImportError, match="无效的类型路径"):
            TypeclassLoader.load("invalidpath")

    def test_load_nonexistent_module(self):
        """测试不存在的模块."""
        with pytest.raises(ImportError, match="无法导入模块"):
            TypeclassLoader.load("nonexistent.module.Class")

    def test_load_nonexistent_class(self):
        """测试不存在的类."""
        with pytest.raises(AttributeError, match="类不存在"):
            TypeclassLoader.load("src.engine.core.typeclass.NonExistentClass")

    def test_load_not_typeclass_subclass(self):
        """测试不是TypeclassBase子类的类."""
        with pytest.raises(TypeError, match="不是TypeclassBase的子类"):
            TypeclassLoader.load("src.utils.config.Config")


class TestTypeclassLoaderRegistry:
    """TypeclassLoader注册表测试."""

    def test_get_all_typeclasses(self):
        """测试获取所有注册的Typeclass."""
        result = TypeclassLoader.get_all_typeclasses()
        assert isinstance(result, dict)


# Fixtures
@pytest.fixture
def mock_manager():
    """创建mock管理器."""
    manager = MagicMock()
    manager.mark_dirty = MagicMock()
    # 使find方法返回一个可等待的空列表
    async def async_find(**kwargs):
        return []
    manager.find = async_find
    return manager


@pytest.fixture
def mock_db_model():
    """创建mock数据库模型."""
    model = MagicMock()
    model.id = 1
    model.key = "test"
    model.location_id = None
    model.attributes = {}
    model.contents = []
    return model
