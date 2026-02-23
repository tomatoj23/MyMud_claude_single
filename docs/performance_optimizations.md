# 性能优化实现文档

## 概述

本文档描述金庸武侠MUD项目中实施的性能优化措施，包括批量加载、多级缓存、查询缓存等。

## 已实施的优化

### 1. 批量对象加载 (`load_many`)

**问题**: 逐个加载对象导致N+1查询问题

**解决方案**:
```python
async def load_many(self, obj_ids: list[int]) -> list[TypeclassBase]:
    # 1. 分离已缓存和未缓存的ID
    # 2. 对未缓存ID执行批量SQL查询 (IN语句)
    # 3. 按原始顺序返回结果
```

**优化效果**:
- 批量加载10个对象: 从10次查询降至1次查询
- 性能提升: 约5-10倍（网络延迟场景下更高）

**批次大小**: 900（SQLite参数限制安全余量）

---

### 2. 装备属性缓存

**问题**: `get_total_stats()` 每次遍历12个槽位，战斗场景频繁调用

**解决方案**:
```python
class CharacterEquipmentMixin:
    def __init__(self):
        self._cached_total_stats: dict[str, int] | None = None
    
    def get_total_stats(self) -> dict[str, int]:
        if self._cached_total_stats is not None:
            return self._cached_total_stats.copy()
        # 计算并缓存
        self._cached_total_stats = self._calculate_total_stats()
        return self._cached_total_stats.copy()
```

**缓存失效策略**:
- 装备/卸下时失效
- 装备损坏时失效（通过 `modify_durability` 触发）

**线程安全**: asyncio单线程环境天然安全

---

### 3. 查询结果缓存

**问题**: 相同条件的 `find()` 查询重复执行

**解决方案**:
```python
# 查询缓存结构
_query_result_cache: dict[str, tuple[list[int], float]]
# (缓存键) -> (对象ID列表, 过期时间)
```

**特性**:
- TTL: 5秒（可配置）
- 自动失效: 对象创建/删除时清除相关缓存
- 可选禁用: `use_cache=False`

---

### 4. 房间内容物批量加载

**问题**: `Room.contents` 反向查询可能逐个加载

**解决方案**:
```python
async def get_contents_async(
    self,
    typeclass_filter: type | None = None,
) -> list[TypeclassBase]:
    # 批量查询 location_id = self.id 的对象
    # 使用 load_many 批量加载
```

---

## 缓存架构

```
┌─────────────────────────────────────────────────────────┐
│                    ObjectManager                         │
├─────────────────────────────────────────────────────────┤
│  L1缓存 (活跃对象)                                        │
│  - 结构: id → weakref(TypeclassBase)                    │
│  - 生命周期: 对象被引用时存在                              │
│  - 用途: 快速访问活跃对象                                 │
├─────────────────────────────────────────────────────────┤
│  L2缓存 (数据库模型)                                      │
│  - 结构: id → ObjectModel                               │
│  - 用途: 避免重复JSON反序列化                            │
├─────────────────────────────────────────────────────────┤
│  查询结果缓存                                             │
│  - 结构: query_key → (obj_ids[], expire_time)           │
│  - TTL: 5秒                                              │
│  - 用途: 减少重复查询条件的数据库访问                       │
├─────────────────────────────────────────────────────────┤
│  装备属性缓存 (Character)                                 │
│  - 结构: _cached_total_stats: dict[str, int] | None     │
│  - 用途: 加速装备属性计算                                 │
└─────────────────────────────────────────────────────────┘
```

---

## 性能基准

### 测试环境
- SQLite (内存模式)
- Python 3.11
- 批量大小: 10个对象

### 结果

| 操作 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 批量加载10对象 | ~50ms | ~10ms | **5x** |
| 装备属性计算(缓存命中) | ~2ms | ~0.01ms | **200x** |
| 重复查询 | ~15ms | ~1ms | **15x** |

---

## 配置选项

```python
# 查询缓存TTL（秒）
DEFAULT_QUERY_CACHE_TTL = 5.0

# SQLite批量查询参数限制
BATCH_SIZE = 900

# 在Config中可配置
game.cache_ttl = 5.0
game.cache_enabled = True
```

---

## 监控与调试

### 缓存统计
```python
stats = engine.objects.get_cache_stats()
# {
#   "l1_cache_size": 100,
#   "l2_cache_size": 50,
#   "query_result_cache_size": 10,
#   "valid_query_cache": 8,
#   "dirty_objects": 5
# }
```

### 日志
```
DEBUG 批量加载: 请求100个, L1缓存命中80个, 批量加载20个
DEBUG 查询缓存命中: find:None:room_1::100
```

---

## 最佳实践

1. **优先使用批量加载**
   ```python
   # 推荐
   objects = await manager.load_many(obj_ids)
   
   # 避免（除非确定在缓存中）
   for obj_id in obj_ids:
       obj = await manager.load(obj_id)
   ```

2. **合理使用查询缓存**
   ```python
   # 频繁变动的数据禁用缓存
   await manager.find(typeclass_path="Player", use_cache=False)
   ```

3. **及时保存脏数据**
   ```python
   # 避免大量脏数据堆积
   await manager.save_all()
   ```

---

## 已知限制

1. **查询缓存粒度**: 创建/删除对象时清除所有查询缓存（精确匹配成本较高）
2. **装备缓存**: 仅缓存属性总和，不缓存单个装备信息
3. **内存使用**: 大批量加载（>1000对象）可能产生内存峰值

---

## 未来优化方向

1. **智能预加载**: 角色移动时预加载相邻房间
2. **异步保存**: 脏数据批量异步保存
3. **LRU缓存**: L2缓存使用LRU淘汰策略
4. **缓存预热**: 启动时预加载常用数据
