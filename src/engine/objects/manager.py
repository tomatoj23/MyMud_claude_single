"""对象管理器.

提供游戏对象的缓存管理、创建、查询和持久化功能。

性能优化特性:
- L1/L2多级缓存减少数据库访问
- 批量加载接口(load_many)解决N+1查询问题
- 查询结果缓存带TTL自动过期
- 脏数据追踪避免无效保存

使用示例:
    # 创建对象
    obj = await manager.create(
        typeclass_path="src.game.typeclasses.character.Character",
        key="玩家",
    )
    
    # 批量加载
    objects = await manager.load_many([1, 2, 3, 4, 5])
    
    # 条件查询（自动使用缓存）
    results = await manager.find(location=room)
    
    # 获取缓存统计
    stats = manager.get_cache_stats()
"""

from __future__ import annotations

import json
import time
import weakref
from typing import TYPE_CHECKING, Any

from src.engine.core.typeclass import TypeclassBase, TypeclassLoader
from src.engine.database.models import ObjectModel
from src.utils.logging import get_logger

if TYPE_CHECKING:
    from src.engine.database.connection import DatabaseManager

logger = get_logger(__name__)

# 默认查询缓存TTL（秒）
DEFAULT_QUERY_CACHE_TTL = 5.0


class ObjectManager:
    """游戏对象管理器.

    管理游戏对象的生命周期，提供L1/L2缓存和批量保存功能。

    Attributes:
        db: 数据库管理器
        _l1_cache: L1缓存（活跃对象）
        _l2_cache: L2缓存（数据库查询结果）
        _dirty_objects: 脏数据对象集合
    """

    def __init__(self, db: DatabaseManager) -> None:
        """初始化对象管理器.

        Args:
            db: 数据库管理器
        """
        self.db = db

        # L1缓存 - 活跃对象（id -> weakref）
        self._l1_cache: dict[int, weakref.ref[TypeclassBase]] = {}

        # L2缓存 - 数据库查询结果（id -> model）
        self._query_cache: dict[int, ObjectModel] = {}

        # 脏数据对象
        self._dirty_objects: set[int] = set()

        # 查询结果缓存: (查询条件哈希) -> (结果IDs, 过期时间)
        self._query_result_cache: dict[str, tuple[list[int], float]] = {}
        self._query_cache_ttl = DEFAULT_QUERY_CACHE_TTL

        self._initialized = False

    async def initialize(self) -> None:
        """初始化对象管理器."""
        if self._initialized:
            return

        logger.info("正在初始化对象管理器...")
        self._initialized = True
        logger.info("对象管理器初始化完成")

    def _get_from_l1(self, obj_id: int) -> TypeclassBase | None:
        """从L1缓存获取对象.

        Args:
            obj_id: 对象ID

        Returns:
            缓存的对象或None
        """
        ref = self._l1_cache.get(obj_id)
        if ref is not None:
            obj = ref()
            if obj is not None:
                return obj
            # 引用已失效，清理缓存
            del self._l1_cache[obj_id]
        return None

    def _add_to_l1(self, obj: TypeclassBase) -> None:
        """添加对象到L1缓存.

        Args:
            obj: 对象实例
        """
        self._l1_cache[obj.id] = weakref.ref(obj)

    async def _get_from_db(self, obj_id: int) -> ObjectModel | None:
        """从数据库获取对象模型.

        Args:
            obj_id: 对象ID

        Returns:
            数据库模型或None
        """
        # 检查查询缓存
        if obj_id in self._query_cache:
            return self._query_cache[obj_id]

        try:
            row = await self.db.fetchone(
                "SELECT * FROM objects WHERE id = ?",
                (obj_id,)
            )

            if row is None:
                return None

            # 转换为模型（JSON反序列化属性）
            attrs = row["attributes"]
            if isinstance(attrs, str):
                attrs = json.loads(attrs)
            model = ObjectModel(
                id=row["id"],
                key=row["key"],
                typeclass_path=row["typeclass_path"],
                location_id=row["location_id"],
                attributes=attrs or {},
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

            # 添加到查询缓存
            self._query_cache[obj_id] = model
            return model

        except Exception as e:
            logger.error(f"从数据库获取对象失败 (id={obj_id}): {e}")
            return None

    def get(self, obj_id: int | None) -> TypeclassBase | None:
        """获取对象（仅从L1缓存）.

        优先从L1缓存获取，如未命中则返回None。
        异步加载需要调用load()方法。

        Args:
            obj_id: 对象ID

        Returns:
            对象实例或None
        """
        if obj_id is None:
            return None

        # 优先L1缓存
        return self._get_from_l1(obj_id)

    async def load(self, obj_id: int) -> TypeclassBase | None:
        """从数据库加载对象.

        Args:
            obj_id: 对象ID

        Returns:
            对象实例或None
        """
        # 先检查L1缓存
        obj = self._get_from_l1(obj_id)
        if obj is not None:
            return obj

        # 从数据库加载
        db_model = await self._get_from_db(obj_id)
        if db_model is None:
            return None

        return self._create_instance(db_model)

    def _create_instance(self, db_model: ObjectModel) -> TypeclassBase:
        """从数据库模型创建对象实例.

        Args:
            db_model: 数据库模型

        Returns:
            对象实例
        """
        # 动态加载Typeclass类
        try:
            cls = TypeclassLoader.load(db_model.typeclass_path)
        except (ImportError, AttributeError, TypeError) as e:
            logger.error(f"加载Typeclass失败: {db_model.typeclass_path}, {e}")
            # 使用默认基类
            cls = TypeclassBase

        # 创建实例
        obj = cls(self, db_model)
        self._add_to_l1(obj)

        return obj

    async def load_many(
        self,
        obj_ids: list[int],
        skip_missing: bool = True,
    ) -> list[TypeclassBase]:
        """批量加载对象.

        优化策略：
        1. 先检查L1缓存，分离已缓存和未缓存ID
        2. 对未缓存ID执行批量SQL查询（IN语句）
        3. 统一反序列化并加入缓存
        4. 按原始顺序返回结果

        Args:
            obj_ids: 对象ID列表
            skip_missing: 是否跳过不存在的对象

        Returns:
            加载的对象列表（保持输入顺序）
        """
        if not obj_ids:
            return []

        # 步骤1：分层检查缓存
        cached_results: dict[int, TypeclassBase] = {}
        need_fetch_ids: list[int] = []

        for obj_id in obj_ids:
            obj = self._get_from_l1(obj_id)
            if obj is not None:
                cached_results[obj_id] = obj
            else:
                need_fetch_ids.append(obj_id)

        # 步骤2：批量查询未缓存的对象
        fetched_results: dict[int, TypeclassBase] = {}
        if need_fetch_ids:
            # 构建IN查询（SQLite限制999参数，分批处理）
            BATCH_SIZE = 900  # 留安全余量
            for i in range(0, len(need_fetch_ids), BATCH_SIZE):
                batch = need_fetch_ids[i:i + BATCH_SIZE]
                batch_results = await self._fetch_many_from_db(batch)
                fetched_results.update(batch_results)

        # 步骤3：按原始顺序组装结果
        results: list[TypeclassBase] = []
        for obj_id in obj_ids:
            if obj_id in cached_results:
                results.append(cached_results[obj_id])
            elif obj_id in fetched_results:
                results.append(fetched_results[obj_id])
            elif not skip_missing:
                # 不跳过缺失时，位置保留None
                results.append(None)  # type: ignore

        logger.debug(
            f"批量加载: 请求{len(obj_ids)}个, "
            f"L1缓存命中{len(cached_results)}个, "
            f"批量加载{len(fetched_results)}个"
        )

        return results

    async def _fetch_many_from_db(
        self,
        obj_ids: list[int],
    ) -> dict[int, TypeclassBase]:
        """从数据库批量获取对象.

        Args:
            obj_ids: 对象ID列表（已确认不在缓存中）

        Returns:
            id到对象的映射
        """
        if not obj_ids:
            return {}

        try:
            # 构建参数化查询
            placeholders = ",".join(["?"] * len(obj_ids))
            rows = await self.db.fetchall(
                f"SELECT * FROM objects WHERE id IN ({placeholders})",
                tuple(obj_ids),
            )

            results: dict[int, TypeclassBase] = {}
            for row in rows:
                # JSON反序列化属性
                attrs = row["attributes"]
                if isinstance(attrs, str):
                    attrs = json.loads(attrs)

                model = ObjectModel(
                    id=row["id"],
                    key=row["key"],
                    typeclass_path=row["typeclass_path"],
                    location_id=row["location_id"],
                    attributes=attrs or {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

                # 添加到查询缓存
                self._query_cache[model.id] = model

                # 创建实例
                obj = self._create_instance(model)
                results[obj.id] = obj

            return results

        except Exception as e:
            logger.error(f"批量从数据库获取对象失败: {e}")
            return {}

    async def create(
        self,
        typeclass_path: str,
        key: str,
        location: TypeclassBase | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> TypeclassBase:
        """创建新对象.

        Args:
            typeclass_path: 类型类路径
            key: 对象标识名
            location: 所在位置
            attributes: 初始属性

        Returns:
            新创建的对象
        """
        # 插入数据库（JSON序列化属性）
        cursor = await self.db.execute(
            """
            INSERT INTO objects (key, typeclass_path, location_id, attributes)
            VALUES (?, ?, ?, ?)
            """,
            (
                key,
                typeclass_path,
                location.id if location else None,
                json.dumps(attributes or {}),
            )
        )
        await self.db.commit()

        obj_id = cursor.lastrowid
        logger.debug(f"创建对象: id={obj_id}, key={key}, type={typeclass_path}")

        # 加载并返回
        obj = await self.load(obj_id)
        if obj is None:
            raise RuntimeError(f"创建对象后加载失败: id={obj_id}")

        # 使相关查询缓存失效
        self._invalidate_query_cache()

        return obj

    async def delete(self, obj: TypeclassBase) -> bool:
        """删除对象.

        Args:
            obj: 要删除的对象

        Returns:
            是否成功删除
        """
        # 调用删除前钩子
        obj.at_delete()

        obj_id = obj.id

        # 从缓存中移除
        if obj_id in self._l1_cache:
            del self._l1_cache[obj_id]
        if obj_id in self._query_cache:
            del self._query_cache[obj_id]
        if obj_id in self._dirty_objects:
            self._dirty_objects.discard(obj_id)

        # 从数据库删除
        try:
            await self.db.execute(
                "DELETE FROM objects WHERE id = ?",
                (obj_id,)
            )
            await self.db.commit()
            logger.debug(f"删除对象: id={obj_id}, key={obj.key}")

            # 使相关查询缓存失效
            self._invalidate_query_cache()

            return True
        except Exception as e:
            logger.error(f"删除对象失败: {e}")
            return False

    def _make_query_cache_key(
        self,
        typeclass_path: str | None,
        location: TypeclassBase | None,
        key_contains: str | None,
        limit: int,
    ) -> str:
        """生成查询缓存键.

        Args:
            typeclass_path: 类型类路径
            location: 位置对象
            key_contains: key包含字符串
            limit: 限制数量

        Returns:
            缓存键字符串
        """
        loc_id = location.id if location else None
        return f"find:{typeclass_path}:{loc_id}:{key_contains}:{limit}"

    def _invalidate_query_cache(self, obj: TypeclassBase | None = None) -> None:
        """使查询缓存失效.

        Args:
            obj: 可选，指定对象变更时只失效相关缓存
        """
        if obj is None:
            # 清除所有缓存
            self._query_result_cache.clear()
            logger.debug("查询缓存已完全清除")
        else:
            # 选择性清除（简化实现：清除所有，精确匹配成本较高）
            self._query_result_cache.clear()

    async def find(
        self,
        typeclass_path: str | None = None,
        location: TypeclassBase | None = None,
        key_contains: str | None = None,
        limit: int = 100,
        use_cache: bool = True,
    ) -> list[TypeclassBase]:
        """条件查询对象.

        Args:
            typeclass_path: 类型类路径筛选
            location: 位置筛选
            key_contains: key包含字符串
            limit: 最大返回数量
            use_cache: 是否使用查询缓存

        Returns:
            对象列表
        """
        # 生成缓存键
        cache_key = self._make_query_cache_key(
            typeclass_path, location, key_contains, limit
        )

        # 检查缓存
        if use_cache:
            cached = self._query_result_cache.get(cache_key)
            if cached:
                obj_ids, expire_time = cached
                if time.time() < expire_time:
                    logger.debug(f"查询缓存命中: {cache_key}")
                    return await self.load_many(obj_ids)
                else:
                    # 过期，删除
                    del self._query_result_cache[cache_key]

        # 构建查询条件
        conditions = []
        params: list[Any] = []

        if typeclass_path:
            conditions.append("typeclass_path = ?")
            params.append(typeclass_path)

        if location:
            conditions.append("location_id = ?")
            params.append(str(location.id))

        if key_contains:
            conditions.append("key LIKE ?")
            params.append(f"%{key_contains}%")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        rows = await self.db.fetchall(
            f"""
            SELECT id FROM objects
            WHERE {where_clause}
            LIMIT ?
            """,
            tuple(params) + (limit,)
        )

        # 使用批量加载替代逐个加载
        obj_ids = [row["id"] for row in rows]
        results = await self.load_many(obj_ids)

        # 写入缓存
        if use_cache:
            self._query_result_cache[cache_key] = (
                obj_ids,
                time.time() + self._query_cache_ttl,
            )

        return results

    async def save(self, obj: TypeclassBase, force: bool = False) -> bool:
        """保存对象状态.

        Args:
            obj: 要保存的对象
            force: 强制保存（忽略脏标记）

        Returns:
            是否成功保存
        """
        if not force and not obj.is_dirty():
            return True

        try:
            await self.db.execute(
                """
                UPDATE objects
                SET key = ?, location_id = ?, attributes = ?
                WHERE id = ?
                """,
                (
                    obj.key,
                    obj._db_model.location_id,
                    json.dumps(obj.db.to_db()),
                    obj.id,
                )
            )
            await self.db.commit()

            obj.clean_dirty()
            self._dirty_objects.discard(obj.id)

            logger.debug(f"保存对象: id={obj.id}, key={obj.key}")
            return True

        except Exception as e:
            logger.error(f"保存对象失败 (id={obj.id}): {e}")
            return False

    async def save_all(self) -> int:
        """批量保存所有脏数据对象.

        Returns:
            保存的对象数量
        """
        if not self._dirty_objects:
            return 0

        count = 0
        # 复制列表避免遍历时修改
        dirty_ids = list(self._dirty_objects)

        for obj_id in dirty_ids:
            obj = self._get_from_l1(obj_id)
            if obj and obj.is_dirty() and await self.save(obj):
                count += 1

        logger.info(f"批量保存完成: {count} 个对象")
        return count

    def mark_dirty(self, obj: TypeclassBase) -> None:
        """标记对象为脏数据.

        Args:
            obj: 对象实例
        """
        self._dirty_objects.add(obj.id)

    def get_contents_sync(self, location_id: int) -> list[TypeclassBase]:
        """同步获取指定位置的内容对象（仅从L1缓存）.

        从L1缓存中筛选出 location_id 等于指定值的所有对象。
        注意：此方法仅返回当前在L1缓存中的对象，可能不包含所有数据。
        如需完整数据请使用异步的 find(location=...)。

        Args:
            location_id: 位置对象ID

        Returns:
            包含的对象列表（仅从L1缓存）
        """
        contents: list[TypeclassBase] = []

        for obj_id, ref in self._l1_cache.items():
            obj = ref()
            if obj is not None:
                # 检查对象的 location_id
                if obj._db_model.location_id == location_id:
                    contents.append(obj)

        return contents

    def clear_cache(self) -> None:
        """清理缓存.

        释放非活跃对象，保留脏数据对象。
        """
        # 清理L1缓存中的失效引用
        dead_ids = [
            obj_id for obj_id, ref in self._l1_cache.items()
            if ref() is None
        ]
        for obj_id in dead_ids:
            del self._l1_cache[obj_id]

        # 清理查询缓存（保留脏数据对象的缓存）
        dirty_ids = set(self._dirty_objects)
        self._query_cache = {
            k: v for k, v in self._query_cache.items()
            if k in dirty_ids
        }

        logger.debug(f"缓存清理完成，释放 {len(dead_ids)} 个失效引用")

    def get_cache_stats(self) -> dict[str, int]:
        """获取缓存统计信息.

        Returns:
            统计信息字典
        """
        # 计算有效的查询缓存数量
        now = time.time()
        valid_query_cache = sum(
            1 for _, expire_time in self._query_result_cache.values()
            if expire_time > now
        )

        return {
            "l1_cache_size": len(self._l1_cache),
            "l2_cache_size": len(self._query_cache),
            "query_result_cache_size": len(self._query_result_cache),
            "valid_query_cache": valid_query_cache,
            "dirty_objects": len(self._dirty_objects),
        }
