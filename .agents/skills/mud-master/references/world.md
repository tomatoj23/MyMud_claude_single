# 地图系统

## 概述

地图系统提供房间（Room）、出口（Exit）、区域（Area）定义，支持三维坐标和A*寻路。

## Room 房间类

```python
# src/game/typeclasses/room.py
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .character import Character


class Room(TypeclassBase):
    """房间类型
    
    属性：
    - coords: 三维坐标 (x, y, z)
    - area: 所属区域
    - description: 房间描述
    - environment: 环境属性（光照、天气等）
    
    Attributes:
        typeclass_path: 类型路径
    """
    
    typeclass_path = "src.game.typeclasses.room.Room"
    
    @property
    def coords(self) -> tuple[int, int, int]:
        """三维坐标 (x, y, z)"""
        return self.db.get("coords", (0, 0, 0))
    
    @coords.setter
    def coords(self, value: tuple[int, int, int]) -> None:
        self.db.set("coords", value)
    
    @property
    def area(self) -> str:
        """所属区域"""
        return self.db.get("area", "未知区域")
    
    @area.setter
    def area(self, value: str) -> None:
        self.db.set("area", value)
    
    @property
    def description(self) -> str:
        """房间描述"""
        return self.db.get("description", "这里什么也没有。")
    
    @description.setter
    def description(self, value: str) -> None:
        self.db.set("description", value)
    
    @property
    def environment(self) -> dict:
        """环境属性（光照、天气等）"""
        return self.db.get("environment", {
            "light": 100,      # 光照度 0-100
            "weather": "clear",  # 天气
            "terrain": "normal",  # 地形
        })
    
    @environment.setter
    def environment(self, value: dict) -> None:
        self.db.set("environment", value)
    
    # ===== 出口相关 =====
    def get_exits(self) -> list["Exit"]:
        """获取所有出口"""
        exits = []
        for obj in self.contents:
            if isinstance(obj, Exit):
                exits.append(obj)
        return exits
    
    def get_exit(self, direction: str) -> Optional["Exit"]:
        """获取指定方向出口
        
        Args:
            direction: 方向（n/ne/e/se/s/sw/w/nw/up/down）
            
        Returns:
            出口对象，不存在返回None
        """
        for exit_obj in self.get_exits():
            if exit_obj.direction == direction:
                return exit_obj
        return None
    
    def get_exit_names(self) -> list[str]:
        """获取所有出口方向名称"""
        return [exit_obj.direction_name for exit_obj in self.get_exits()]
    
    # ===== 内容物相关 =====
    def get_characters(self) -> list["Character"]:
        """获取房间内的角色（不包括玩家自己）"""
        from .character import Character
        return [obj for obj in self.contents if isinstance(obj, Character)]
    
    def get_items(self) -> list["Item"]:
        """获取房间内的物品"""
        from .item import Item
        return [obj for obj in self.contents if isinstance(obj, Item)]
    
    # ===== 描述渲染 =====
    def at_desc(self, looker: "Character") -> str:
        """渲染房间描述（可被子类重写）
        
        Args:
            looker: 观察者
            
        Returns:
            描述文本
        """
        desc = f"\n{self.key}\n"
        desc += "=" * 40 + "\n"
        desc += self.description + "\n"
        
        # 出口
        exits = self.get_exits()
        if exits:
            exit_names = [ex.direction_name for ex in exits]
            desc += f"\n[出口] {' '.join(exit_names)}"
        
        # 物品
        items = self.get_items()
        if items:
            item_names = [item.key for item in items]
            desc += f"\n[物品] {', '.join(item_names)}"
        
        # 其他角色
        characters = self.get_characters()
        others = [c for c in characters if c != looker]
        if others:
            char_names = [c.key for c in others]
            desc += f"\n[人物] {', '.join(char_names)}"
        
        return desc
```

## Exit 出口类

```python
# src/game/typeclasses/room.py

# 方向常量
DIRECTIONS = {
    "n": (0, 1, 0),
    "ne": (1, 1, 0),
    "e": (1, 0, 0),
    "se": (1, -1, 0),
    "s": (0, -1, 0),
    "sw": (-1, -1, 0),
    "w": (-1, 0, 0),
    "nw": (-1, 1, 0),
    "up": (0, 0, 1),
    "down": (0, 0, -1),
}

DIRECTION_NAMES = {
    "n": "北",
    "ne": "东北",
    "e": "东",
    "se": "东南",
    "s": "南",
    "sw": "西南",
    "w": "西",
    "nw": "西北",
    "up": "上",
    "down": "下",
}

DIRECTION_OPPOSITES = {
    "n": "s", "ne": "sw", "e": "w", "se": "nw",
    "s": "n", "sw": "ne", "w": "e", "nw": "se",
    "up": "down", "down": "up",
}


class Exit(TypeclassBase):
    """出口类型
    
    Attributes:
        typeclass_path: 类型路径
    """
    
    typeclass_path = "src.game.typeclasses.room.Exit"
    
    @property
    def direction(self) -> str:
        """方向（n/ne/e/se/s/sw/w/nw/up/down）"""
        return self.db.get("direction", "n")
    
    @direction.setter
    def direction(self, value: str) -> None:
        self.db.set("direction", value)
    
    @property
    def direction_name(self) -> str:
        """方向中文名"""
        return DIRECTION_NAMES.get(self.direction, "未知")
    
    @property
    def destination_id(self) -> Optional[int]:
        """目标房间ID"""
        return self.db.get("destination_id")
    
    @destination_id.setter
    def destination_id(self, value: int) -> None:
        self.db.set("destination_id", value)
    
    @property
    def destination(self) -> Optional[Room]:
        """目标房间对象"""
        dest_id = self.destination_id
        if dest_id and self.manager:
            return self.manager.get(dest_id)
        return None
    
    @destination.setter
    def destination(self, room: Room) -> None:
        self.destination_id = room.id if room else None
    
    @property
    def is_hidden(self) -> bool:
        """是否隐藏"""
        return self.db.get("is_hidden", False)
    
    @is_hidden.setter
    def is_hidden(self, value: bool) -> None:
        self.db.set("is_hidden", value)
    
    @property
    def lock_str(self) -> str:
        """通行条件（锁字符串）"""
        return self.db.get("lock_str", "")
    
    async def can_pass(self, character: "Character") -> tuple[bool, str]:
        """检查是否可以通过
        
        Args:
            character: 角色
            
        Returns:
            (是否可以通过, 原因)
        """
        # 检查锁
        if self.lock_str:
            # TODO: 解析锁字符串，检查条件
            # 例如："key:golden_key" 需要持有金钥匙
            # 例如："level:10" 需要等级10
            pass
        
        # 检查目的地
        if not self.destination:
            return False, "出口似乎通向虚无..."
        
        return True, ""
    
    def get_desc(self) -> str:
        """获取出口描述"""
        if self.is_hidden:
            return ""
        
        desc = f"{self.direction_name}"
        if self.destination:
            desc += f" - {self.destination.key}"
        return desc
```

## 区域 Area 定义

```python
# src/game/world/area.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class Area:
    """区域定义
    
    Attributes:
        key: 唯一标识
        name: 显示名
        description: 区域描述
        rooms: 房间ID列表
        load_range: 预加载范围
        unload_delay: 卸载延迟（秒）
    """
    
    key: str
    name: str
    description: str = ""
    rooms: list[int] = None
    load_range: int = 3      # 预加载范围
    unload_delay: int = 60   # 卸载延迟（秒）
    
    def __post_init__(self):
        if self.rooms is None:
            self.rooms = []
```

## 世界动态加载管理器

```python
# src/game/world/loader.py
import time
import asyncio
from typing import Optional
from pathlib import Path

import yaml


class WorldLoader:
    """世界动态加载管理器
    
    负责：
    - 按需加载区域
    - 根据玩家位置预加载相邻区域
    - 卸载长时间未访问的区域
    """
    
    def __init__(self, object_manager: "ObjectManager"):
        self.obj_mgr = object_manager
        self._loaded_areas: dict[str, Area] = {}
        self._active_rooms: dict[int, float] = {}  # room_id -> last_access_time
        self._unload_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """初始化世界加载器"""
        # 启动后台卸载任务
        self._unload_task = asyncio.create_task(self._unload_loop())
    
    async def shutdown(self) -> None:
        """关闭世界加载器"""
        if self._unload_task:
            self._unload_task.cancel()
            try:
                await self._unload_task
            except asyncio.CancelledError:
                pass
    
    async def on_player_move(self, from_room: Room, to_room: Room) -> None:
        """玩家移动时触发加载/卸载
        
        Args:
            from_room: 起始房间
            to_room: 目标房间
        """
        # 更新活跃时间
        now = time.time()
        self._active_rooms[to_room.id] = now
        
        # 加载新区域
        await self._load_area(to_room.area)
        
        # 预加载相邻区域
        await self._preload_adjacent_areas(to_room)
    
    async def _load_area(self, area_key: str) -> None:
        """加载区域
        
        Args:
            area_key: 区域key
        """
        if area_key in self._loaded_areas:
            return
        
        # 从YAML文件加载区域数据
        area_data = self._load_area_from_file(area_key)
        if not area_data:
            return
        
        area = Area(**area_data)
        
        # 加载区域内的房间
        for room_id in area.rooms:
            room = await self.obj_mgr.get(room_id)
            if room:
                self._active_rooms[room_id] = time.time()
        
        self._loaded_areas[area_key] = area
    
    def _load_area_from_file(self, area_key: str) -> Optional[dict]:
        """从文件加载区域数据"""
        file_path = Path(f"resources/world/{area_key}.yaml")
        if not file_path.exists():
            return None
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        return data.get("area")
    
    async def _preload_adjacent_areas(self, room: Room) -> None:
        """预加载相邻区域"""
        # TODO: 根据区域连接配置预加载
        pass
    
    async def _unload_loop(self) -> None:
        """后台卸载循环"""
        while True:
            await asyncio.sleep(60)  # 每分钟检查一次
            await self._check_and_unload()
    
    async def _check_and_unload(self) -> None:
        """检查并卸载不活跃区域"""
        now = time.time()
        
        # 找出长时间未访问的房间
        to_unload = []
        for room_id, last_access in self._active_rooms.items():
            if now - last_access > 300:  # 5分钟未访问
                to_unload.append(room_id)
        
        # 卸载房间
        for room_id in to_unload:
            del self._active_rooms[room_id]
            # TODO: 从缓存中移除，但不删除数据库记录
    
    def get_active_rooms(self) -> list[int]:
        """获取当前活跃房间"""
        return list(self._active_rooms.keys())
    
    def is_room_active(self, room_id: int) -> bool:
        """检查房间是否活跃"""
        return room_id in self._active_rooms
```

## A* 寻路算法

```python
# src/game/world/pathfinding.py
import heapq
from typing import Optional


class PathFinder:
    """A*寻路
    
    使用三维曼哈顿距离作为启发函数
    """
    
    def __init__(self, world_loader: WorldLoader):
        self.world = world_loader
    
    async def find_path(
        self, 
        start: Room, 
        goal: Room
    ) -> Optional[list[tuple[str, Room]]]:
        """寻找路径
        
        Args:
            start: 起始房间
            goal: 目标房间
            
        Returns:
            路径列表 [(方向, 房间), ...]，无路径返回None
        """
        # A*算法
        open_set = [(0, start.id)]  # (f_score, room_id)
        came_from: dict[int, tuple[str, int]] = {}  # room_id -> (direction, prev_room_id)
        
        g_score: dict[int, float] = {start.id: 0}
        f_score: dict[int, float] = {start.id: self._heuristic(start, goal)}
        
        open_set_hash = {start.id}
        
        while open_set:
            _, current_id = heapq.heappop(open_set)
            open_set_hash.remove(current_id)
            
            if current_id == goal.id:
                # 找到路径，重建
                return await self._reconstruct_path(came_from, current_id, goal)
            
            current_room = await self.world.obj_mgr.get(current_id)
            if not current_room:
                continue
            
            # 遍历邻居
            for exit_obj in current_room.get_exits():
                if not exit_obj.destination:
                    continue
                
                neighbor_id = exit_obj.destination_id
                
                # 计算 tentative_g_score
                tentative_g_score = g_score[current_id] + 1
                
                if neighbor_id not in g_score or tentative_g_score < g_score[neighbor_id]:
                    came_from[neighbor_id] = (exit_obj.direction, current_id)
                    g_score[neighbor_id] = tentative_g_score
                    f_score[neighbor_id] = tentative_g_score + self._heuristic(
                        exit_obj.destination, goal
                    )
                    
                    if neighbor_id not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor_id], neighbor_id))
                        open_set_hash.add(neighbor_id)
        
        # 无路径
        return None
    
    def _heuristic(self, a: Room, b: Room) -> float:
        """启发函数 - 三维曼哈顿距离
        
        Z轴权重更高（上下移动通常更难）
        """
        ax, ay, az = a.coords
        bx, by, bz = b.coords
        return abs(ax - bx) + abs(ay - by) + abs(az - bz) * 2
    
    async def _reconstruct_path(
        self, 
        came_from: dict, 
        current_id: int,
        goal: Room
    ) -> list[tuple[str, Room]]:
        """重建路径"""
        path = []
        
        while current_id in came_from:
            direction, prev_id = came_from[current_id]
            room = await self.world.obj_mgr.get(current_id)
            if room:
                path.append((direction, room))
            current_id = prev_id
        
        path.reverse()
        return path
    
    async def find_path_to_key(
        self,
        start: Room,
        goal_key: str
    ) -> Optional[list[tuple[str, Room]]]:
        """根据房间key寻路"""
        # 通过key查找房间
        rooms = await self.world.obj_mgr.find(key_contains=goal_key)
        if not rooms:
            return None
        
        return await self.find_path(start, rooms[0])
```

## 世界数据 YAML 格式

```yaml
# resources/world/shaolin.yaml
area:
  key: shaolin
  name: 少林寺
  description: 天下武功出少林，武林泰山北斗
  load_range: 3
  unload_delay: 120

rooms:
  - key: shaolin_shanmen
    name: 少林寺山门
    description: |
      你站在少林寺山门之前。两尊石狮威武雄壮，
      朱红山门上方悬挂"少林寺"金字匾额。
      山门两侧松柏森森，钟声悠扬。
    coords: [100, 100, 0]
    area: shaolin
    environment:
      light: 100
      weather: clear
      terrain: normal
    
  - key: shaolin_daxiong
    name: 大雄宝殿
    description: |
      少林寺主殿，供奉释迦牟尼佛。
      殿内香火鼎盛，僧众诵经声不绝于耳。
    coords: [100, 101, 0]
    area: shaolin

exits:
  - from: shaolin_shanmen
    direction: n
    to: shaolin_daxiong
    
  - from: shaolin_daxiong
    direction: s
    to: shaolin_shanmen
    
  - from: shaolin_shanmen
    direction: s
    to: luoyang_shaolin_road
    lock_str: ""
```

## 使用示例

```python
# 创建房间
room1 = await object_manager.create(
    typeclass_path="src.game.typeclasses.room.Room",
    key="少林寺山门",
    attributes={
        "coords": (100, 100, 0),
        "area": "shaolin",
        "description": "你站在少林寺山门之前...",
    }
)

room2 = await object_manager.create(
    typeclass_path="src.game.typeclasses.room.Room",
    key="大雄宝殿",
    attributes={
        "coords": (100, 101, 0),
        "area": "shaolin",
        "description": "少林寺主殿...",
    }
)

# 创建出口
exit_n = await object_manager.create(
    typeclass_path="src.game.typeclasses.room.Exit",
    key="北出口",
    location=room1,
    attributes={
        "direction": "n",
        "destination_id": room2.id,
    }
)

exit_s = await object_manager.create(
    typeclass_path="src.game.typeclasses.room.Exit",
    key="南出口",
    location=room2,
    attributes={
        "direction": "s",
        "destination_id": room1.id,
    }
)

# 查看房间描述
print(room1.at_desc(character))

# 寻路
path_finder = PathFinder(world_loader)
path = await path_finder.find_path(room1, room2)
if path:
    for direction, room in path:
        print(f"向{direction}走 -> {room.key}")
```
