# 性能优化详细设计文档

## 1. 概述

### 1.1 目标
- 减少数据库查询次数（N+1问题）
- 降低对象加载延迟
- 提高批量操作性能
- 优化内存使用

### 1.2 优化范围
- `ObjectManager` - 对象加载和缓存
- `TypeclassBase` - contents属性访问
- `Room` - 房间内容物渲染
- `CharacterEquipmentMixin` - 装备属性计算

---

## 2. 详细设计方案

### 2.1 P0优化：批量加载接口 `load_many`

#### 问题描述
当前 `find()` 方法逐个加载对象，导致N+1查询问题。

#### 设计方案

```python
async def load_many(
    self, 
    obj_ids: list[int],
    skip_missing: bool = True
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
```

#### 实现细节

**步骤1：缓存分层检查**
```python
# L1命中对象
cached_objs = []
# 需要查询的对象ID
need_fetch_ids = []

for obj_id in obj_ids:
    obj = self._get_from_l1(obj_id)
    if obj:
        cached_objs.append((obj_id, obj))
    else:
        need_fetch_ids.append(obj_id)
```

**步骤2：批量SQL查询**
```sql
-- 使用参数化IN查询避免SQL注入
SELECT * FROM objects WHERE id IN (?, ?, ?, ...)
```

**步骤3：批量反序列化**
- 使用 `asyncio.gather()` 并行创建对象
- 复用现有 `_get_from_db` 的JSON解析逻辑

**复杂度分析**
- 时间复杂度：O(N) → O(1) 数据库查询次数
- 空间复杂度：O(N) 临时存储

---

### 2.2 P0优化：`Room.get_contents_async` 预加载

#### 问题描述
`Room.contents` 通过 `location_id` 反向查询，当前实现可能逐个加载。

#### 设计方案

```python
async def get_contents_async(
    self,
    typeclass_filter: type | None = None
) -> list[TypeclassBase]:
    """异步获取房间内容物（批量加载优化）.
    
    Args:
        typeclass_filter: 可选的类型过滤
        
    Returns:
        内容物对象列表
    """
```

#### 实现细节

**批量查询策略**
```python
# 1. 查询所有 location_id = self.id 的对象ID
rows = await self._manager.db.fetchall(
    "SELECT id FROM objects WHERE location_id = ?",
    (self.id,)
)
obj_ids = [row["id"] for row in rows]

# 2. 使用批量加载
contents = await self._manager.load_many(obj_ids)

# 3. 可选类型过滤
if typeclass_filter:
    contents = [obj for obj in contents if isinstance(obj, typeclass_filter)]
```

---

### 2.3 P1优化：装备属性缓存

#### 问题描述
`get_total_stats()` 每次遍历12个槽位并查询装备，战斗场景频繁调用。

#### 设计方案

```python
class CharacterEquipmentMixin:
    def __init__(self):
        self._cached_total_stats: dict[str, int] | None = None
        self._cache_version = 0  # 缓存版本号
        
    def _invalidate_equipment_cache(self) -> None:
        """装备变更时使缓存失效."""
        self._cached_total_stats = None
        self._cache_version += 1
        
    def get_total_stats(self) -> dict[str, int]:
        """计算所有装备属性总和（带缓存）."""
        if self._cached_total_stats is not None:
            return self._cached_total_stats.copy()
            
        # 计算并缓存
        self._cached_total_stats = self._calculate_total_stats()
        return self._cached_total_stats.copy()
```

#### 缓存失效策略
- **触发时机**：装备/卸下、装备耐久变化、装备损坏
- **线程安全**：单线程asyncio环境天然安全
- **内存开销**：O(1) 小型字典

---

### 2.4 P1优化：查询结果缓存

#### 问题描述
相同条件的 `find()` 查询重复执行。

#### 设计方案

```python
class ObjectManager:
    def __init__(self):
        # 查询缓存: (查询条件哈希) -> (结果IDs, 过期时间)
        self._query_result_cache: dict[str, tuple[list[int], float]] = {}
        self._query_cache_ttl = 5.0  # 5秒TTL
        
    async def find(
        self,
        typeclass_path: str | None = None,
        location: TypeclassBase | None = None,
        key_contains: str | None = None,
        limit: int = 100,
        use_cache: bool = True,  # 新增参数
    ) -> list[TypeclassBase]:
        # 生成缓存键
        cache_key = f"{typeclass_path}:{location.id if location else None}:{key_contains}:{limit}"
        
        # 检查缓存
        if use_cache and cache_key in self._query_result_cache:
            obj_ids, expire_time = self._query_result_cache[cache_key]
            if time.time() < expire_time:
                return await self.load_many(obj_ids)
```

#### 缓存失效策略
- **TTL过期**：5秒自动过期（可配置）
- **主动失效**：对象创建/删除时清理相关缓存

---

## 3. 实施计划

### 阶段1：基础设施
1. 实现 `load_many()` 批量加载
2. 添加性能测试基准

### 阶段2：核心优化
3. 实现 `get_contents_async()`
4. 装备属性缓存

### 阶段3：高级优化
5. 查询结果缓存
6. 预加载策略

---

## 4. 测试策略

### 4.1 性能基准测试
```python
# 测试批量加载性能
@pytest.mark.benchmark
async def test_load_many_performance():
    # 创建100个对象
    obj_ids = [await create_test_object() for _ in range(100)]
    
    # 清除缓存
    manager.clear_cache()
    
    # 测量逐个加载
    start = time.time()
    for obj_id in obj_ids:
        await manager.load(obj_id)
    time_one_by_one = time.time() - start
    
    # 测量批量加载
    manager.clear_cache()
    start = time.time()
    await manager.load_many(obj_ids)
    time_batch = time.time() - start
    
    # 断言批量加载快5倍以上
    assert time_batch < time_one_by_one / 5
```

### 4.2 正确性测试
- 缓存命中率测试
- 批量加载顺序保持测试
- 缓存失效正确性测试

---

## 5. 风险评估

| 优化点 | 风险 | 缓解措施 |
|--------|------|----------|
| load_many | 内存峰值 | 分批处理大量ID |
| 装备缓存 | 数据不一致 | 严格失效策略 |
| 查询缓存 | 过期数据 | 合理TTL+主动失效 |
