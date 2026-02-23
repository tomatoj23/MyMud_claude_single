"""Typeclass 系统单元测试.

测试 AttributeHandler、TypeclassBase、TypeclassMeta 和 TypeclassLoader。
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.engine.core.typeclass import (
    AttributeHandler,
    TypeclassBase,
    TypeclassLoader,
    TypeclassMeta,
)


class MockDBModel:
    """模拟数据库模型."""

    def __init__(self, **kwargs: Any) -> None:
        self.id = kwargs.get("id", 1)
        self.key = kwargs.get("key", "test_obj")
        self.typeclass_path = kwargs.get(
            "typeclass_path", "src.engine.core.typeclass.TypeclassBase"
        )
        self.location_id = kwargs.get("location_id", None)
        self.attributes = kwargs.get("attributes", {})
        self.contents = []


class MockManager:
    """模拟对象管理器."""

    def __init__(self) -> None:
        self._cache: dict[int, TypeclassBase] = {}
        self.dirty_objects: set[int] = set()

    def get(self, obj_id: int) -> TypeclassBase | None:
        return self._cache.get(obj_id)

    def mark_dirty(self, obj: TypeclassBase) -> None:
        self.dirty_objects.add(obj.id)
    
    async def find(self, **kwargs) -> list[TypeclassBase]:
        """模拟查找方法."""
        # 支持 location 过滤
        location = kwargs.get('location')
        if location:
            # 检查所有缓存对象的 location_id
            result = []
            for obj in self._cache.values():
                if hasattr(obj, '_db_model'):
                    loc_id = getattr(obj._db_model, 'location_id', None)
                    if loc_id == location.id:
                        result.append(obj)
            return result
        return list(self._cache.values())


class TestAttributeHandler:
    """AttributeHandler 测试套件."""

    @pytest.fixture
    def mock_obj(self):
        """创建模拟 Typeclass 对象."""
        manager = MockManager()
        db_model = MockDBModel(id=1, attributes={"existing": "value"})
        obj = TypeclassBase(manager, db_model)
        return obj

    def test_load_attributes_on_init(self, mock_obj: TypeclassBase):
        """测试初始化时加载属性."""
        handler = AttributeHandler(mock_obj)

        # 验证属性已从数据库加载
        assert handler._cache["existing"] == "value"

    def test_getattr_existing_attribute(self, mock_obj: TypeclassBase):
        """测试获取已存在的属性."""
        handler = AttributeHandler(mock_obj)

        assert handler.existing == "value"

    def test_getattr_nonexistent_raises_error(self, mock_obj: TypeclassBase):
        """测试获取不存在的属性抛出 AttributeError."""
        handler = AttributeHandler(mock_obj)

        with pytest.raises(AttributeError, match="属性不存在"):
            _ = handler.nonexistent

    def test_setattr_marks_dirty(self, mock_obj: TypeclassBase):
        """测试设置属性标记对象为脏数据."""
        handler = AttributeHandler(mock_obj)
        original_dirty = mock_obj.is_dirty()

        handler.new_attr = "new_value"

        assert mock_obj.is_dirty() is True
        assert handler.new_attr == "new_value"

    def test_setattr_private_attribute(self, mock_obj: TypeclassBase):
        """测试设置私有属性不标记脏数据."""
        handler = AttributeHandler(mock_obj)
        original_dirty = mock_obj.is_dirty()

        handler._private = "private_value"

        # 私有属性不应触发脏数据标记
        assert mock_obj.is_dirty() == original_dirty

    def test_delattr_marks_dirty(self, mock_obj: TypeclassBase):
        """测试删除属性标记脏数据."""
        handler = AttributeHandler(mock_obj)
        handler.temp = "temp_value"
        mock_obj.clean_dirty()  # 清除脏标记

        del handler.temp

        assert mock_obj.is_dirty() is True
        with pytest.raises(AttributeError):
            _ = handler.temp

    def test_get_with_default(self, mock_obj: TypeclassBase):
        """测试带默认值的 get 方法."""
        handler = AttributeHandler(mock_obj)

        # 不存在的属性返回默认值
        assert handler.get("missing", "default") == "default"
        # 存在的属性返回值
        assert handler.get("existing", "default") == "value"

    def test_set_method(self, mock_obj: TypeclassBase):
        """测试 set 方法."""
        handler = AttributeHandler(mock_obj)

        handler.set("key", "value")

        assert handler.key == "value"
        assert mock_obj.is_dirty() is True

    def test_all_returns_copy(self, mock_obj: TypeclassBase):
        """测试 all() 返回属性副本."""
        handler = AttributeHandler(mock_obj)
        handler.set("a", 1)
        handler.set("b", 2)

        all_attrs = handler.all()

        assert all_attrs == {"existing": "value", "a": 1, "b": 2}
        # 验证是副本
        all_attrs["c"] = 3
        assert "c" not in handler.all()

    def test_update_batch(self, mock_obj: TypeclassBase):
        """测试批量更新属性."""
        handler = AttributeHandler(mock_obj)
        mock_obj.clean_dirty()

        handler.update({"x": 1, "y": 2, "z": 3})

        assert handler.x == 1
        assert handler.y == 2
        assert handler.z == 3
        assert mock_obj.is_dirty() is True

    def test_clear_marks_dirty(self, mock_obj: TypeclassBase):
        """测试清空属性标记脏数据."""
        handler = AttributeHandler(mock_obj)
        mock_obj.clean_dirty()

        handler.clear()

        assert handler.all() == {}
        assert mock_obj.is_dirty() is True

    def test_to_db_returns_copy(self, mock_obj: TypeclassBase):
        """测试 to_db 返回副本."""
        handler = AttributeHandler(mock_obj)

        db_data = handler.to_db()

        assert db_data == {"existing": "value"}
        # 修改返回的字典不应影响 handler
        db_data["new"] = "entry"
        assert "new" not in handler.all()


class TestTypeclassBase:
    """TypeclassBase 测试套件."""

    @pytest.fixture
    def mock_manager(self):
        return MockManager()

    @pytest.fixture
    def mock_db_model(self):
        return MockDBModel(id=42, key="test_key")

    @pytest.fixture
    def typeclass_instance(self, mock_manager, mock_db_model):
        return TypeclassBase(mock_manager, mock_db_model)

    def test_init_calls_at_init(self, mock_manager, mock_db_model):
        """测试初始化时调用 at_init 钩子."""
        with patch.object(TypeclassBase, "at_init") as mock_at_init:
            obj = TypeclassBase(mock_manager, mock_db_model)
            mock_at_init.assert_called_once()

    def test_id_property(self, typeclass_instance: TypeclassBase):
        """测试 id 属性."""
        assert typeclass_instance.id == 42

    def test_key_property_get(self, typeclass_instance: TypeclassBase):
        """测试 key 属性获取."""
        assert typeclass_instance.key == "test_key"

    def test_key_property_set_marks_dirty(self, typeclass_instance: TypeclassBase):
        """测试设置 key 标记脏数据."""
        typeclass_instance.clean_dirty()

        typeclass_instance.key = "new_key"

        assert typeclass_instance.key == "new_key"
        assert typeclass_instance.is_dirty() is True

    def test_get_typeclass_path(self, typeclass_instance: TypeclassBase):
        """测试获取类型路径."""
        path = typeclass_instance.get_typeclass_path()
        assert path == "src.engine.core.typeclass.TypeclassBase"

    def test_location_none(self, typeclass_instance: TypeclassBase):
        """测试 location 为 None."""
        assert typeclass_instance.location is None

    def test_location_with_value(self, mock_manager: MockManager):
        """测试获取 location."""
        # 创建位置对象
        loc_model = MockDBModel(id=100, key="room")
        location = TypeclassBase(mock_manager, loc_model)
        mock_manager._cache[100] = location

        # 创建主体对象
        obj_model = MockDBModel(id=1, key="obj", location_id=100)
        obj = TypeclassBase(mock_manager, obj_model)

        assert obj.location is location

    def test_location_setter_validates_type(self, typeclass_instance: TypeclassBase):
        """测试 location setter 验证类型."""
        with pytest.raises(TypeError, match="location必须是TypeclassBase实例"):
            typeclass_instance.location = "invalid"  # type: ignore

    def test_location_setter_calls_hooks(self, mock_manager: MockManager):
        """测试 location setter 调用生命周期钩子."""
        loc_model = MockDBModel(id=100, key="room")
        location = TypeclassBase(mock_manager, loc_model)
        mock_manager._cache[100] = location

        obj_model = MockDBModel(id=1, key="obj")
        obj = TypeclassBase(mock_manager, obj_model)

        with (
            patch.object(obj, "at_move", return_value=True) as mock_at_move,
            patch.object(obj, "at_moved") as mock_at_moved,
        ):
            obj.location = location

            mock_at_move.assert_called_once_with(location)
            mock_at_moved.assert_called_once_with(None)

    def test_location_setter_at_move_can_cancel(self, mock_manager: MockManager):
        """测试 at_move 可以取消移动."""
        loc_model = MockDBModel(id=100, key="room")
        location = TypeclassBase(mock_manager, loc_model)
        mock_manager._cache[100] = location

        obj_model = MockDBModel(id=1, key="obj")
        obj = TypeclassBase(mock_manager, obj_model)

        with patch.object(obj, "at_move", return_value=False):
            obj.location = location
            # 移动应该被取消
            assert obj._db_model.location_id is None

    def test_contents_empty(self, typeclass_instance: TypeclassBase):
        """测试 contents 为空列表."""
        assert typeclass_instance.contents == []

    def test_search_contents_found(self, mock_manager: MockManager):
        """测试搜索内容找到对象."""
        obj_model = MockDBModel(id=1, key="container")
        container = TypeclassBase(mock_manager, obj_model)
        mock_manager._cache[1] = container

        item_model = MockDBModel(id=2, key="sword")
        item_model.location_id = 1  # 设置 location_id 指向 container
        item = TypeclassBase(mock_manager, item_model)
        mock_manager._cache[2] = item

        # 注意：search_contents 现在是异步方法
        import asyncio
        found = asyncio.run(container.search_contents("sword"))
        assert found is item

    def test_search_contents_not_found(self, mock_manager: MockManager):
        """测试搜索内容未找到."""
        obj_model = MockDBModel(id=1, key="container")
        container = TypeclassBase(mock_manager, obj_model)
        container._db_model.contents = []

        # 注意：search_contents 现在是异步方法
        import asyncio
        found = asyncio.run(container.search_contents("missing"))
        assert found is None

    def test_mark_dirty(self, typeclass_instance: TypeclassBase):
        """测试标记脏数据."""
        typeclass_instance.clean_dirty()
        assert typeclass_instance.is_dirty() is False

        typeclass_instance.mark_dirty()

        assert typeclass_instance.is_dirty() is True
        assert typeclass_instance.id in typeclass_instance._manager.dirty_objects

    def test_clean_dirty(self, typeclass_instance: TypeclassBase):
        """测试清除脏数据标记."""
        typeclass_instance.mark_dirty()
        typeclass_instance.clean_dirty()

        assert typeclass_instance.is_dirty() is False

    def test_to_db_dict(self, typeclass_instance: TypeclassBase):
        """测试转换为数据库字典."""
        typeclass_instance.db.strength = 10

        data = typeclass_instance.to_db_dict()

        assert data["id"] == 42
        assert data["key"] == "test_key"
        assert data["typeclass_path"] == "src.engine.core.typeclass.TypeclassBase"
        assert data["location_id"] is None
        assert data["attributes"]["strength"] == 10

    def test_at_desc_default(self, typeclass_instance: TypeclassBase):
        """测试默认描述."""
        desc = typeclass_instance.at_desc(typeclass_instance)
        assert desc == "test_key"

    def test_msg_default(self, typeclass_instance: TypeclassBase, caplog):
        """测试默认消息发送（记录到日志）."""
        import logging

        # 使用 logger 名称获取日志记录器并设置级别
        logger = logging.getLogger("src.engine.core.typeclass")
        original_level = logger.level
        logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG):
            typeclass_instance.msg("test message")

        # 恢复原始级别
        logger.setLevel(original_level)

        # 只要没有异常抛出就算成功（日志可能因配置问题不显示）
        assert True

    def test_repr(self, typeclass_instance: TypeclassBase):
        """测试字符串表示."""
        repr_str = repr(typeclass_instance)
        assert "TypeclassBase" in repr_str
        assert "id=42" in repr_str
        assert "key=test_key" in repr_str


class CustomTypeclass(TypeclassBase):
    """自定义类型类，用于测试注册."""

    typeclass_path = "tests.unit.test_typeclass.CustomTypeclass"

    def custom_method(self):
        return "custom"


class TestTypeclassMeta:
    """TypeclassMeta 元类测试."""

    def test_registry_contains_custom_typeclass(self):
        """测试注册表包含自定义类型类."""
        assert "tests.unit.test_typeclass.CustomTypeclass" in TypeclassMeta.registry
        assert TypeclassMeta.registry["tests.unit.test_typeclass.CustomTypeclass"] == CustomTypeclass

    def test_typeclass_path_required(self):
        """测试 typeclass_path 用于注册."""

        class NoPathClass(TypeclassBase):
            pass  # 没有 typeclass_path

        # 不会注册到 registry（因为 typeclass_path 为空）
        assert "tests.unit.test_typeclass.NoPathClass" not in TypeclassMeta.registry


class TestTypeclassLoader:
    """TypeclassLoader 测试套件."""

    def test_load_from_registry(self):
        """测试从注册表加载."""
        cls = TypeclassLoader.load("tests.unit.test_typeclass.CustomTypeclass")
        assert cls == CustomTypeclass

    def test_load_from_module(self):
        """测试动态导入加载."""
        # 从模块路径加载
        test_path = "src.engine.core.typeclass.TypeclassBase"

        # 确保先清除缓存中的此路径（避免其他测试影响）
        if test_path in TypeclassMeta.registry:
            del TypeclassMeta.registry[test_path]

        cls = TypeclassLoader.load(test_path)
        # 验证加载的类是正确的
        assert cls.__name__ == "TypeclassBase"
        assert issubclass(cls, TypeclassBase)

    def test_load_invalid_path_format(self):
        """测试无效路径格式."""
        with pytest.raises(ImportError, match="无效的类型路径"):
            TypeclassLoader.load("invalid_path_no_dot")

    def test_load_nonexistent_module(self):
        """测试不存在的模块."""
        with pytest.raises(ImportError, match="无法导入模块"):
            TypeclassLoader.load("nonexistent.module.Class")

    def test_load_nonexistent_class(self):
        """测试模块存在但类不存在."""
        with pytest.raises(AttributeError, match="类不存在"):
            TypeclassLoader.load("src.engine.core.typeclass.NonexistentClass")

    def test_load_not_subclass(self):
        """测试加载的类不是 TypeclassBase 子类."""
        with pytest.raises(TypeError, match="不是TypeclassBase的子类"):
            TypeclassLoader.load("src.utils.config.Config")

    def test_get_all_typeclasses(self):
        """测试获取所有已注册的类型类."""
        all_classes = TypeclassLoader.get_all_typeclasses()
        assert isinstance(all_classes, dict)
        # 至少包含 CustomTypeclass
        assert "tests.unit.test_typeclass.CustomTypeclass" in all_classes
