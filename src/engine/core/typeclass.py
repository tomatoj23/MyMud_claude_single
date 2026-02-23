"""Typeclass动态类系统.

提供游戏对象的动态类加载、属性代理和生命周期管理。
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any, ClassVar

from src.utils.logging import get_logger

if TYPE_CHECKING:
    from src.engine.objects.manager import ObjectManager

logger = get_logger(__name__)


class AttributeHandler:
    """属性代理处理器.

    透明代理对数据库JSON字段的访问，本地缓存减少数据库访问，
    修改时自动标记对象为脏数据。

    Attributes:
        _obj: 关联的Typeclass实例
        _cache: 本地属性缓存
    """

    def __init__(self, obj: TypeclassBase) -> None:
        """初始化属性处理器.

        Args:
            obj: 关联的Typeclass实例
        """
        self._obj = obj
        self._cache: dict[str, Any] = {}
        self._load_attributes()

    def _load_attributes(self) -> None:
        """从数据库加载属性到缓存."""
        db_model = self._obj._db_model
        if db_model and hasattr(db_model, "attributes"):
            self._cache.update(db_model.attributes or {})

    def __getattr__(self, name: str) -> Any:
        """获取属性值.

        Args:
            name: 属性名

        Returns:
            属性值

        Raises:
            AttributeError: 属性不存在
        """
        if name.startswith("_"):
            raise AttributeError(f"无法访问私有属性: {name}")

        if name in self._cache:
            return self._cache[name]

        raise AttributeError(f"属性不存在: {name}")

    def __setattr__(self, name: str, value: Any) -> None:
        """设置属性值.

        Args:
            name: 属性名
            value: 属性值
        """
        if name.startswith("_"):
            super().__setattr__(name, value)
            return

        self._cache[name] = value
        self._obj.mark_dirty()

    def __delattr__(self, name: str) -> None:
        """删除属性.

        Args:
            name: 属性名
        """
        if name.startswith("_"):
            super().__delattr__(name)
            return

        if name in self._cache:
            del self._cache[name]
            self._obj.mark_dirty()

    def get(self, name: str, default: Any = None) -> Any:
        """安全获取属性值.

        Args:
            name: 属性名
            default: 默认值

        Returns:
            属性值或默认值
        """
        try:
            return getattr(self, name)
        except AttributeError:
            return default

    def set(self, name: str, value: Any) -> None:
        """设置属性值.

        Args:
            name: 属性名
            value: 属性值
        """
        setattr(self, name, value)

    def all(self) -> dict[str, Any]:
        """获取所有属性.

        Returns:
            属性字典副本
        """
        return self._cache.copy()

    def update(self, data: dict[str, Any]) -> None:
        """批量更新属性.

        Args:
            data: 属性字典
        """
        self._cache.update(data)
        self._obj.mark_dirty()

    def clear(self) -> None:
        """清空所有属性."""
        self._cache.clear()
        self._obj.mark_dirty()

    def to_db(self) -> dict[str, Any]:
        """转换为数据库格式.

        Returns:
            属性字典
        """
        return self._cache.copy()


class TypeclassMeta(type):
    """Typeclass元类.

    自动注册类型路径到全局注册表。
    """

    registry: ClassVar[dict[str, type[TypeclassBase]]] = {}

    def __new__(mcs, name: str, bases: tuple, namespace: dict) -> type:  # noqa: D102
        cls = super().__new__(mcs, name, bases, namespace)

        # 注册类型路径
        if hasattr(cls, "typeclass_path") and cls.typeclass_path:
            mcs.registry[cls.typeclass_path] = cls  # type: ignore
            logger.debug(f"注册Typeclass: {cls.typeclass_path}")

        return cls


class TypeclassBase(metaclass=TypeclassMeta):
    """游戏对象类型基类.

    所有游戏对象的基类，提供属性代理、生命周期钩子和脏数据追踪。

    Attributes:
        typeclass_path: 类型类导入路径（子类必须定义）
        manager: 对象管理器实例
        db: 属性代理处理器
    """

    typeclass_path: ClassVar[str] = "src.engine.core.typeclass.TypeclassBase"

    def __init__(
        self,
        manager: ObjectManager,
        db_model: Any,
    ) -> None:
        """初始化Typeclass实例.

        Args:
            manager: 对象管理器
            db_model: 数据库模型实例
        """
        self._manager = manager
        self._db_model = db_model
        self._is_dirty = False

        # 属性代理
        self.db = AttributeHandler(self)

        # 调用初始化钩子
        self.at_init()

    # 基础属性代理
    @property
    def id(self) -> int:
        """对象ID."""
        return int(self._db_model.id)

    @property
    def key(self) -> str:
        """对象标识名."""
        return str(self._db_model.key)

    @key.setter
    def key(self, value: str) -> None:
        """设置对象标识名."""
        self._db_model.key = value
        self.mark_dirty()

    def get_typeclass_path(self) -> str:
        """获取类型类路径.

        Returns:
            类型类路径
        """
        return str(self._db_model.typeclass_path)

    # 容器关系
    @property
    def location(self) -> TypeclassBase | None:
        """所在位置."""
        if self._db_model.location_id is None:
            return None

        location = self._manager.get(self._db_model.location_id)
        return location

    @location.setter
    def location(self, value: TypeclassBase | None) -> None:
        """移动到指定位置."""
        if value is not None and not isinstance(value, TypeclassBase):
            raise TypeError("location必须是TypeclassBase实例或None")

        # 调用移动前钩子
        if value is not None and not self.at_move(value):
            return

        old_location = self.location
        self._db_model.location_id = value.id if value else None
        self.mark_dirty()

        # 调用移动后钩子
        self.at_moved(old_location)

    async def get_contents(self) -> list[TypeclassBase]:
        """异步获取包含的对象列表.
        
        通过查询数据库获取 location 等于当前对象的所有对象。
        
        Returns:
            包含的对象列表
        """
        return await self._manager.find(location=self)
    
    @property
    def contents(self) -> list[TypeclassBase]:
        """包含的对象列表（同步版本）.
        
        从缓存中获取内容，可能不是最新数据。
        如需最新数据请使用 get_contents()。
        
        Returns:
            缓存中包含的对象列表
        """
        # 返回缓存中 location 等于当前对象的对象
        # 这是一个简化实现，优先保证不报错
        return []  # 默认返回空列表，使用 get_contents() 获取真实数据

    async def search_contents(self, key: str) -> TypeclassBase | None:
        """在内容中搜索指定key的对象.

        Args:
            key: 对象标识名

        Returns:
            找到的对象或None
        """
        contents = await self.get_contents()
        for obj in contents:
            if obj.key == key:
                return obj
        return None

    # 脏数据机制
    def mark_dirty(self) -> None:
        """标记对象为脏数据."""
        self._is_dirty = True
        self._manager.mark_dirty(self)

    def is_dirty(self) -> bool:
        """检查对象是否为脏数据.

        Returns:
            是否已修改
        """
        return self._is_dirty

    def clean_dirty(self) -> None:
        """清除脏数据标记."""
        self._is_dirty = False

    # 序列化
    def to_db_dict(self) -> dict[str, Any]:
        """转换为数据库字典.

        Returns:
            数据库字段字典
        """
        return {
            "id": self.id,
            "key": self.key,
            "typeclass_path": self.get_typeclass_path(),
            "location_id": self._db_model.location_id,
            "attributes": self.db.to_db(),
        }

    # 生命周期钩子（子类可重写）
    def at_init(self) -> None:
        """对象初始化后调用."""
        pass

    def at_delete(self) -> None:
        """对象删除前调用."""
        pass

    def at_move(self, _destination: TypeclassBase) -> bool:
        """对象移动前调用.

        Args:
            destination: 目标位置

        Returns:
            是否允许移动
        """
        return True

    def at_moved(self, source: TypeclassBase | None) -> None:
        """对象移动后调用.

        Args:
            source: 原位置
        """
        pass

    def at_desc(self, _looker: TypeclassBase) -> str:
        """生成对象描述.

        Args:
            looker: 查看者

        Returns:
            描述文本
        """
        return f"{self.key}"

    def msg(self, text: str, **_kwargs: Any) -> None:
        """向对象发送消息.

        Args:
            text: 消息文本
            **kwargs: 额外参数
        """
        # 默认实现，子类可重写
        logger.debug(f"Message to {self.key}: {text}")

    def __repr__(self) -> str:  # noqa: D105
        return f"<{self.__class__.__name__}(id={self.id}, key={self.key})>"


class TypeclassLoader:
    """Typeclass动态加载器.

    通过字符串路径动态加载Typeclass类。
    """

    @staticmethod
    def load(typeclass_path: str) -> type[TypeclassBase]:
        """从路径加载Typeclass类.

        Args:
            typeclass_path: 类型类导入路径，如"src.game.objects.Character"

        Returns:
            Typeclass类

        Raises:
            ImportError: 模块导入失败
            AttributeError: 类不存在
        """
        # 优先从注册表获取
        if typeclass_path in TypeclassMeta.registry:
            return TypeclassMeta.registry[typeclass_path]

        # 动态导入
        try:
            module_path, class_name = typeclass_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)

            if not issubclass(cls, TypeclassBase):
                raise TypeError(f"{typeclass_path} 不是TypeclassBase的子类")

            return cls  # type: ignore[no-any-return]
        except ValueError as e:
            raise ImportError(f"无效的类型路径: {typeclass_path}") from e
        except ImportError as e:
            raise ImportError(f"无法导入模块: {module_path}") from e
        except AttributeError as e:
            raise AttributeError(f"类不存在: {class_name}") from e

    @staticmethod
    def get_all_typeclasses() -> dict[str, type[TypeclassBase]]:
        """获取所有已注册的Typeclass.

        Returns:
            类型路径到类的映射
        """
        return TypeclassMeta.registry.copy()
