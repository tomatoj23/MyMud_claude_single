# 内容包热加载机制设计

> 实现游戏内容与程序的完全分离，支持运行时动态加载、热更新和MOD扩展
> 版本: 1.0
> 日期: 2026-02-26

---

## 目录

1. [设计目标](#一设计目标)
2. [核心概念](#二核心概念)
3. [系统架构](#三系统架构)
4. [内容包格式](#四内容包格式)
5. [加载器设计](#五加载器设计)
6. [热更新机制](#六热更新机制)
7. [MOD支持](#七mod支持)
8. [工具链](#八工具链)
9. [实施计划](#九实施计划)

---

## 一、设计目标

### 1.1 目标概述

| 目标 | 描述 | 优先级 |
|:---|:---|:---:|
| **运行时加载** | 游戏启动后才加载内容，程序本身不含内容 | P0 |
| **热更新** | 不重启游戏即可更新内容 | P0 |
| **多版本共存** | 支持内容包版本管理 | P1 |
| **MOD支持** | 玩家/开发者可制作扩展内容 | P1 |
| **增量更新** | 只传输变更内容 | P2 |
| **沙盒安全** | 第三方内容隔离运行 | P2 |

### 1.2 使用场景

```
场景1: 基础游戏发布
    游戏程序: JYMUD.exe (20MB)
    内容包:   jinyong_world_v1.0.jpk (100MB)
    
场景2: 内容更新
    玩家启动游戏 → 检测到v1.1更新 → 下载差异(5MB) → 热更新内容
    
场景3: MOD安装
    玩家下载mod_wuxia_world.jpk → 放入mods/目录 → 游戏识别并加载
    
场景4: 开发者测试
    开发者修改rooms/city/yangzhou.json → 保存 → 游戏自动重载房间
```

---

## 二、核心概念

### 2.1 术语定义

| 术语 | 定义 | 类比 |
|:---|:---|:---|
| **内容包 (Content Pack)** | 包含游戏内容的压缩包或目录 | Minecraft的Resource Pack |
| **清单 (Manifest)** | 描述内容包元数据的JSON文件 | package.json |
| **加载器 (Loader)** | 负责读取和解析内容的组件 | 类加载器 |
| **提供者 (Provider)** | 内容的来源（文件系统/网络/内存） | 数据源 |
| **命名空间 (Namespace)** | 内容的唯一标识前缀，避免冲突 | Java包名 |
| **覆盖 (Override)** | MOD替换原有内容 | CSS覆盖 |
| **补丁 (Patch)** | 增量更新文件 | Git diff |

### 2.2 内容分层

```
┌─────────────────────────────────────────────────────────┐
│  Layer 3: 运行时层 (Runtime)                             │
│  ├─ 已加载的房间实例                                     │
│  ├─ 已加载的NPC实例                                      │
│  └─ 游戏状态（玩家位置、物品等）                           │
├─────────────────────────────────────────────────────────┤
│  Layer 2: 内容定义层 (Content Definition)                │
│  ├─ 房间定义 (JSON)                                     │
│  ├─ NPC定义 (JSON)                                      │
│  ├─ 武功定义 (JSON)                                     │
│  └─ 任务定义 (JSON)                                     │
├─────────────────────────────────────────────────────────┤
│  Layer 1: 内容包层 (Content Pack)                        │
│  ├─ 官方内容包: jinyong@1.0.0                          │
│  ├─ DLC内容包: jinyong-expansion@1.0.0                 │
│  └─ MOD: wuxia-universe@2.1.0                          │
├─────────────────────────────────────────────────────────┤
│  Layer 0: 提供层 (Provider)                              │
│  ├─ 文件系统: ./content/                                │
│  ├─ 压缩包: *.jpk                                       │
│  └─ 网络: http://cdn.example.com/content/               │
└─────────────────────────────────────────────────────────┘
```

---

## 三、系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         Game Engine                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   ContentManager                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │   Loader    │  │   Cache     │  │   Events    │     │   │
│  │  │             │  │             │  │             │     │   │
│  │  │ load()      │  │ get()       │  │ on_reload() │     │   │
│  │  │ unload()    │  │ set()       │  │ on_change() │     │   │
│  │  │ reload()    │  │ invalidate()│  │             │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Typeclass System                      │   │
│  │         (创建游戏对象实例)                               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Content Registry                            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │   RoomRegistry  │ │   NPCRegistry   │ │  SkillRegistry  │   │
│  │                 │ │                 │ │                 │   │
│  │ city/yangzhou →│ │ city/guard →    │ │ force/neigong →│   │
│  │ shaolin/damen →│ │ shaolin/seng →  │ │ sword/jianfa → │   │
│  │ wudang/gate →  │ │ boss/dongfang → │ │ ...             │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Content Providers                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │FileProvider  │  │ZipProvider   │  │HttpProvider  │          │
│  │              │  │              │  │              │          │
│  │./content/    │  │*.jpk         │  │http://...    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 核心组件

| 组件 | 职责 | 关键类 |
|:---|:---|:---|
| **ContentManager** | 内容管理入口 | `ContentManager` |
| **ContentRegistry** | 内容索引和查询 | `RoomRegistry`, `NPCRegistry`... |
| **ContentLoader** | 解析内容文件 | `JSONLoader`, `YAMLLoader` |
| **ContentProvider** | 内容来源抽象 | `FileProvider`, `ZipProvider` |
| **HotReloader** | 热更新检测 | `FileWatcher`, `ReloadScheduler` |
| **ModManager** | MOD管理 | `ModLoader`, `ModConflictResolver` |

---

## 四、内容包格式

### 4.1 内容包结构

```
content_pack.jpk (ZIP格式)
├── manifest.json           # 包元数据
├── content/                # 内容目录
│   ├── rooms/              # 房间定义
│   │   ├── city/
│   │   │   ├── yangzhou.json
│   │   │   └── beijing.json
│   │   ├── shaolin/
│   │   └── wudang/
│   ├── npcs/               # NPC定义
│   │   ├── city/
│   │   └── shaolin/
│   ├── skills/             # 武功定义
│   │   ├── force/
│   │   └── sword/
│   ├── items/              # 物品定义
│   └── quests/             # 任务定义
├── scripts/                # 可选：脚本扩展
│   └── custom_logic.py
├── assets/                 # 可选：资源文件
│   ├── images/
│   └── sounds/
└── _meta/                  # 内部元数据
    └── checksums.json      # 文件校验和
```

### 4.2 清单文件 (manifest.json)

```json
{
  "format_version": "1.0",
  "manifest_version": 1,
  
  "package": {
    "id": "jinyong",
    "namespace": "com.jymud",
    "name": "金庸武侠世界",
    "version": "1.0.0",
    "description": "金庸武侠世界基础内容包",
    "author": "JYMUD Team",
    "license": "CC-BY-NC-SA-4.0",
    "homepage": "https://jymud.example.com",
    "icon": "assets/icon.png"
  },
  
  "engine": {
    "min_version": "1.0.0",
    "max_version": "2.0.0"
  },
  
  "dependencies": {
    "required": [],
    "optional": [
      {
        "id": "jinyong-expansion",
        "version": ">=1.0.0",
        "description": "扩展包，增加更多门派"
      }
    ]
  },
  
  "conflicts": [
    {
      "id": "wuxia-universe",
      "reason": "与武侠宇宙的世界观冲突"
    }
  ],
  
  "content": {
    "rooms": {
      "path": "content/rooms",
      "count": 1500,
      "format": "json"
    },
    "npcs": {
      "path": "content/npcs",
      "count": 800,
      "format": "json"
    },
    "skills": {
      "path": "content/skills",
      "count": 200,
      "format": "json"
    },
    "items": {
      "path": "content/items",
      "count": 500,
      "format": "json"
    },
    "quests": {
      "path": "content/quests",
      "count": 50,
      "format": "json"
    }
  },
  
  "overrides": {
    "description": "允许MOD覆盖的内容",
    "allowed": ["rooms/*", "npcs/*", "items/*"],
    "blocked": ["quests/main_story/*"]
  },
  
  "scripts": {
    "enabled": false,
    "sandbox": true,
    "permissions": ["read_content", "register_hooks"]
  }
}
```

### 4.3 内容文件格式 (房间示例)

```json
{
  "$schema": "https://jymud.example.com/schemas/room-v1.json",
  "format_version": "1.0",
  
  "id": "city/yangzhou/center",
  "type": "room",
  
  "name": "扬州城中央广场",
  "aliases": ["中央广场", "广场"],
  
  "description": "这里是扬州城的中央广场，青石铺地，四周店铺林立。...",
  
  "room_type": "outdoor",
  "tags": ["city", "public", "safe"],
  
  "position": {
    "x": 0,
    "y": 0,
    "z": 0,
    "region": "yangzhou"
  },
  
  "exits": [
    {
      "direction": "north",
      "direction_name": "北",
      "target": "city/yangzhou/north_street",
      "type": "normal",
      "visible": true
    },
    {
      "direction": "south",
      "target": "city/yangzhou/south_street",
      "conditions": [
        {
          "type": "time",
          "min_hour": 6,
          "max_hour": 22,
          "fail_message": "夜深了，南门已经关闭了。"
        }
      ]
    },
    {
      "direction": "enter",
      "target": "city/yangzhou/inn",
      "description": "悦来客栈"
    }
  ],
  
  "spawners": [
    {
      "id": "city_guard",
      "template": "npcs/city/guard",
      "count": 2,
      "respawn": true,
      "respawn_delay": 300,
      "wander": true,
      "wander_radius": 3
    }
  ],
  
  "features": [
    {
      "type": "examinable",
      "keywords": ["青石", "地面"],
      "description": "青石铺成的地面，经过多年踩踏已经十分光滑。"
    },
    {
      "type": "scent",
      "description": "空气中混杂着各种食物的香味。"
    }
  ],
  
  "events": {
    "on_enter": [
      {
        "type": "message",
        "target": "player",
        "text": "你来到了扬州城中央广场。"
      }
    ],
    "on_tick": [
      {
        "type": "spawn",
        "condition": "random(100) < 10",
        "template": "npcs/random/pedestrian"
      }
    ]
  },
  
  "meta": {
    "author": "JYMUD Team",
    "created": "2026-01-15",
    "modified": "2026-02-20",
    "source": "xkx100-converted",
    "tags": ["verified", "balanced"]
  }
}
```

---

## 五、加载器设计

### 5.1 ContentManager 核心类

```python
# src/game/content/manager.py

from typing import Dict, List, Optional, Type, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum, auto
import asyncio


class ContentType(Enum):
    """内容类型"""
    ROOM = auto()
    NPC = auto()
    SKILL = auto()
    ITEM = auto()
    QUEST = auto()


@dataclass
class ContentPack:
    """内容包数据"""
    id: str
    namespace: str
    name: str
    version: str
    path: Path
    manifest: Dict[str, Any]
    enabled: bool = True
    priority: int = 100


class ContentManager:
    """
    内容管理器
    
    职责:
    - 管理所有内容包
    - 协调内容加载
    - 提供内容查询接口
    - 处理热更新
    """
    
    def __init__(self, engine):
        self.engine = engine
        self._packs: Dict[str, ContentPack] = {}
        self._registries: Dict[ContentType, ContentRegistry] = {}
        self._providers: List[ContentProvider] = []
        self._loaders: Dict[str, ContentLoader] = {}
        self._hot_reloader: Optional[HotReloader] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """初始化内容管理器"""
        if self._initialized:
            return
        
        # 1. 注册内置加载器
        self._register_builtin_loaders()
        
        # 2. 初始化内容注册表
        self._registries = {
            ContentType.ROOM: RoomRegistry(),
            ContentType.NPC: NPCRegistry(),
            ContentType.SKILL: SkillRegistry(),
            ContentType.ITEM: ItemRegistry(),
            ContentType.QUEST: QuestRegistry(),
        }
        
        # 3. 扫描内容目录
        await self._scan_content_packs()
        
        # 4. 加载所有启用的内容包
        await self._load_all_packs()
        
        # 5. 启动热重载（开发模式）
        if self.engine.config.dev_mode:
            self._hot_reloader = HotReloader(self)
            await self._hot_reloader.start()
        
        self._initialized = True
        self.engine.logger.info("ContentManager initialized")
    
    def _register_builtin_loaders(self) -> None:
        """注册内置加载器"""
        self._loaders = {
            ".json": JSONLoader(),
            ".yaml": YAMLLoader(),
            ".yml": YAMLLoader(),
        }
    
    async def _scan_content_packs(self) -> None:
        """扫描内容包目录"""
        content_dir = self.engine.config.content_path
        
        # 扫描目录
        for pack_dir in content_dir.iterdir():
            if not pack_dir.is_dir():
                continue
            
            manifest_path = pack_dir / "manifest.json"
            if manifest_path.exists():
                try:
                    pack = await self._load_manifest(pack_dir)
                    self._packs[pack.id] = pack
                except Exception as e:
                    self.engine.logger.error(f"Failed to load pack {pack_dir}: {e}")
        
        # 扫描压缩包
        for pack_file in content_dir.glob("*.jpk"):
            try:
                pack = await self._load_manifest_from_zip(pack_file)
                self._packs[pack.id] = pack
            except Exception as e:
                self.engine.logger.error(f"Failed to load pack {pack_file}: {e}")
    
    async def _load_all_packs(self) -> None:
        """加载所有启用的内容包"""
        # 按优先级排序
        sorted_packs = sorted(
            self._packs.values(),
            key=lambda p: p.priority
        )
        
        for pack in sorted_packs:
            if pack.enabled:
                await self._load_pack(pack)
    
    async def _load_pack(self, pack: ContentPack) -> None:
        """加载单个内容包"""
        self.engine.logger.info(f"Loading content pack: {pack.id} v{pack.version}")
        
        manifest = pack.manifest
        content_config = manifest.get("content", {})
        
        # 加载各类内容
        for content_type_name, config in content_config.items():
            try:
                content_type = ContentType[content_type_name.upper()]
                registry = self._registries[content_type]
                
                await self._load_content_type(
                    pack, 
                    content_type, 
                    registry, 
                    config
                )
            except Exception as e:
                self.engine.logger.error(
                    f"Failed to load {content_type_name} from {pack.id}: {e}"
                )
    
    async def _load_content_type(
        self,
        pack: ContentPack,
        content_type: ContentType,
        registry: ContentRegistry,
        config: Dict[str, Any]
    ) -> None:
        """加载特定类型的内容"""
        content_path = pack.path / config["path"]
        if not content_path.exists():
            return
        
        # 查找所有内容文件
        pattern = f"**/*{self._get_format_extension(config['format'])}"
        files = list(content_path.glob(pattern))
        
        # 批量加载
        for file_path in files:
            try:
                content_data = await self._load_file(file_path)
                if content_data:
                    # 添加命名空间
                    content_id = f"{pack.namespace}:{content_data['id']}"
                    content_data['id'] = content_id
                    content_data['_pack'] = pack.id
                    
                    registry.register(content_id, content_data)
            except Exception as e:
                self.engine.logger.warning(f"Failed to load {file_path}: {e}")
    
    async def _load_file(self, file_path: Path) -> Optional[Dict]:
        """加载单个内容文件"""
        extension = file_path.suffix.lower()
        loader = self._loaders.get(extension)
        
        if not loader:
            return None
        
        return await loader.load(file_path)
    
    # ===== 查询接口 =====
    
    def get_room(self, room_id: str) -> Optional[RoomDefinition]:
        """获取房间定义"""
        registry = self._registries[ContentType.ROOM]
        data = registry.get(room_id)
        if data:
            return RoomDefinition.from_data(data)
        return None
    
    def get_npc(self, npc_id: str) -> Optional[NPCDefinition]:
        """获取NPC定义"""
        registry = self._registries[ContentType.NPC]
        data = registry.get(npc_id)
        if data:
            return NPCDefinition.from_data(data)
        return None
    
    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        """获取武功定义"""
        registry = self._registries[ContentType.SKILL]
        data = registry.get(skill_id)
        if data:
            return SkillDefinition.from_data(data)
        return None
    
    def find_rooms_by_region(self, region: str) -> List[RoomDefinition]:
        """按区域查找房间"""
        registry = self._registries[ContentType.ROOM]
        results = []
        
        for content_id, data in registry.all_items():
            position = data.get("position", {})
            if position.get("region") == region:
                room = RoomDefinition.from_data(data)
                results.append(room)
        
        return results
    
    # ===== 热更新接口 =====
    
    async def reload_pack(self, pack_id: str) -> None:
        """重新加载内容包"""
        if pack_id not in self._packs:
            raise ValueError(f"Pack not found: {pack_id}")
        
        pack = self._packs[pack_id]
        
        # 1. 卸载旧内容
        await self._unload_pack(pack)
        
        # 2. 重新加载
        await self._load_pack(pack)
        
        self.engine.logger.info(f"Reloaded pack: {pack_id}")
    
    async def reload_content(self, content_type: ContentType, content_id: str) -> None:
        """重新加载单个内容"""
        registry = self._registries[content_type]
        data = registry.get(content_id)
        
        if not data:
            return
        
        pack_id = data.get('_pack')
        pack = self._packs.get(pack_id)
        
        if not pack:
            return
        
        # 重新加载文件
        file_path = pack.path / data.get('_file_path', '')
        if file_path.exists():
            new_data = await self._load_file(file_path)
            if new_data:
                registry.update(content_id, new_data)
                
                # 触发更新事件
                self.engine.events.emit(
                    ContentEvents.CONTENT_RELOADED,
                    content_type=content_type,
                    content_id=content_id
                )
    
    async def _unload_pack(self, pack: ContentPack) -> None:
        """卸载内容包"""
        for registry in self._registries.values():
            registry.remove_by_pack(pack.id)
```

### 5.2 内容注册表 (ContentRegistry)

```python
# src/game/content/registry.py

from typing import Dict, List, Optional, Iterator, Tuple
from collections import OrderedDict


class ContentRegistry:
    """
    内容注册表
    
    提供内容索引和查询功能
    """
    
    def __init__(self):
        self._items: OrderedDict[str, Dict] = OrderedDict()
        self._by_pack: Dict[str, List[str]] = {}
        self._by_tag: Dict[str, List[str]] = {}
    
    def register(self, content_id: str, data: Dict) -> None:
        """注册内容"""
        self._items[content_id] = data
        
        # 按包索引
        pack_id = data.get('_pack', 'unknown')
        self._by_pack.setdefault(pack_id, []).append(content_id)
        
        # 按标签索引
        for tag in data.get('tags', []):
            self._by_tag.setdefault(tag, []).append(content_id)
    
    def get(self, content_id: str) -> Optional[Dict]:
        """获取内容"""
        return self._items.get(content_id)
    
    def update(self, content_id: str, data: Dict) -> None:
        """更新内容"""
        if content_id in self._items:
            old_data = self._items[content_id]
            
            # 更新标签索引
            old_tags = set(old_data.get('tags', []))
            new_tags = set(data.get('tags', []))
            
            for tag in old_tags - new_tags:
                if tag in self._by_tag and content_id in self._by_tag[tag]:
                    self._by_tag[tag].remove(content_id)
            
            for tag in new_tags - old_tags:
                self._by_tag.setdefault(tag, []).append(content_id)
            
            # 更新数据
            self._items[content_id] = data
    
    def remove(self, content_id: str) -> None:
        """移除内容"""
        if content_id not in self._items:
            return
        
        data = self._items[content_id]
        
        # 从包索引移除
        pack_id = data.get('_pack', 'unknown')
        if pack_id in self._by_pack:
            if content_id in self._by_pack[pack_id]:
                self._by_pack[pack_id].remove(content_id)
        
        # 从标签索引移除
        for tag in data.get('tags', []):
            if tag in self._by_tag:
                if content_id in self._by_tag[tag]:
                    self._by_tag[tag].remove(content_id)
        
        # 移除内容
        del self._items[content_id]
    
    def remove_by_pack(self, pack_id: str) -> None:
        """移除包的所有内容"""
        if pack_id not in self._by_pack:
            return
        
        for content_id in self._by_pack[pack_id][:]:
            self.remove(content_id)
        
        del self._by_pack[pack_id]
    
    def all_items(self) -> Iterator[Tuple[str, Dict]]:
        """遍历所有内容"""
        return iter(self._items.items())
    
    def find_by_tag(self, tag: str) -> List[Dict]:
        """按标签查找"""
        return [
            self._items[cid]
            for cid in self._by_tag.get(tag, [])
            if cid in self._items
        ]
    
    def count(self) -> int:
        """获取内容数量"""
        return len(self._items)
```

---

## 六、热更新机制

### 6.1 热重载器 (HotReloader)

```python
# src/game/content/hot_reload.py

import asyncio
from pathlib import Path
from typing import Set, Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent


class ContentFileHandler(FileSystemEventHandler):
    """文件系统事件处理器"""
    
    def __init__(self, reloader: 'HotReloader'):
        self.reloader = reloader
        self._pending_changes: Set[Path] = set()
        self._debounce_task: Optional[asyncio.Task] = None
    
    def on_modified(self, event):
        if isinstance(event, FileModifiedEvent):
            path = Path(event.src_path)
            if path.suffix in {'.json', '.yaml', '.yml'}:
                self._pending_changes.add(path)
                self._schedule_reload()
    
    def _schedule_reload(self):
        """防抖处理"""
        if self._debounce_task:
            self._debounce_task.cancel()
        
        self._debounce_task = asyncio.create_task(self._debounce_reload())
    
    async def _debounce_reload(self):
        """延迟重载（500ms防抖）"""
        await asyncio.sleep(0.5)
        
        changes = self._pending_changes.copy()
        self._pending_changes.clear()
        
        for path in changes:
            await self.reloader.reload_file(path)


class HotReloader:
    """
    热重载器
    
    监控文件变化并触发内容重载
    """
    
    def __init__(self, content_manager: ContentManager):
        self.cm = content_manager
        self.observer: Optional[Observer] = None
        self.handler: Optional[ContentFileHandler] = None
        self._watch_paths: Set[Path] = set()
    
    async def start(self) -> None:
        """启动热重载监控"""
        self.handler = ContentFileHandler(self)
        self.observer = Observer()
        
        # 监控所有内容包目录
        for pack in self.cm._packs.values():
            watch_path = pack.path / "content"
            if watch_path.exists() and watch_path not in self._watch_paths:
                self.observer.schedule(
                    self.handler,
                    str(watch_path),
                    recursive=True
                )
                self._watch_paths.add(watch_path)
        
        self.observer.start()
        self.cm.engine.logger.info("HotReloader started")
    
    async def stop(self) -> None:
        """停止热重载监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
    
    async def reload_file(self, file_path: Path) -> None:
        """重载单个文件"""
        try:
            # 确定内容类型
            content_type = self._detect_content_type(file_path)
            if not content_type:
                return
            
            # 找到对应的内容ID
            content_id = self._find_content_id(file_path)
            if not content_id:
                return
            
            # 执行重载
            await self.cm.reload_content(content_type, content_id)
            
            self.cm.engine.logger.info(f"Hot reloaded: {content_id}")
            
        except Exception as e:
            self.cm.engine.logger.error(f"Failed to reload {file_path}: {e}")
    
    def _detect_content_type(self, file_path: Path) -> Optional[ContentType]:
        """从路径检测内容类型"""
        path_str = str(file_path)
        
        if "/rooms/" in path_str:
            return ContentType.ROOM
        elif "/npcs/" in path_str:
            return ContentType.NPC
        elif "/skills/" in path_str:
            return ContentType.SKILL
        elif "/items/" in path_str:
            return ContentType.ITEM
        elif "/quests/" in path_str:
            return ContentType.QUEST
        
        return None
    
    def _find_content_id(self, file_path: Path) -> Optional[str]:
        """从文件路径查找内容ID"""
        # 从文件名推断ID
        relative = file_path.relative_to(file_path.parents[2])
        content_id = str(relative.with_suffix(''))
        
        # 查找匹配的内容
        content_type = self._detect_content_type(file_path)
        if content_type:
            registry = self.cm._registries[content_type]
            
            # 尝试找到匹配的内容
            for cid in registry._items.keys():
                if cid.endswith(content_id):
                    return cid
        
        return None
```

### 6.2 运行时实例更新

```python
# src/game/content/instance_updater.py

from typing import List, Dict


class InstanceUpdater:
    """
    实例更新器
    
    处理内容定义更新时，如何更新已存在的游戏实例
    """
    
    def __init__(self, engine):
        self.engine = engine
    
    async def update_room_instances(self, room_id: str, new_definition: RoomDefinition) -> None:
        """
        更新房间实例
        
        策略：
        - 名称、描述：立即更新
        - 出口：同步更新
        - 生成器：不清理已存在，新配置影响下次刷新
        """
        # 找到所有该房间的实例
        instances = self.engine.object_manager.find_by_definition(room_id)
        
        for instance in instances:
            # 更新名称和描述
            instance.name = new_definition.name
            instance.description = new_definition.description
            
            # 更新出口
            instance.exits.clear()
            for exit_def in new_definition.exits:
                instance.add_exit(exit_def)
            
            # 通知房间内的玩家
            instance.emit_message(
                f"房间 '{instance.name}' 已更新。"
            )
    
    async def update_npc_instances(self, npc_id: str, new_definition: NPCDefinition) -> None:
        """
        更新NPC实例
        
        策略：
        - 基础属性：不修改已存在的NPC（保持游戏稳定性）
        - 对话：立即更新
        - 刷新配置：影响下次刷新
        """
        instances = self.engine.object_manager.find_by_definition(npc_id)
        
        for instance in instances:
            # 只更新对话
            if new_definition.dialogue:
                instance.dialogue = new_definition.dialogue
            
            # 更新行为配置
            if new_definition.behaviors:
                instance.behaviors = new_definition.behaviors
    
    async def update_skill_definitions(self, skill_id: str, new_definition: SkillDefinition) -> None:
        """
        更新武功定义
        
        策略：
        - 定义立即更新
        - 已学习的技能不受影响
        - 新学习的技能使用新定义
        """
        # 武功定义更新自动生效
        # 不需要更新实例
        pass
```

---

## 七、MOD支持

### 7.1 MOD管理器

```python
# src/game/content/mod_manager.py

from typing import List, Dict
from dataclasses import dataclass
from enum import Enum


class ModConflictType(Enum):
    """MOD冲突类型"""
    CONTENT_OVERRIDE = "content_override"  # 内容覆盖
    DEPENDENCY_MISSING = "dependency_missing"  # 依赖缺失
    VERSION_MISMATCH = "version_mismatch"  # 版本不匹配
    ENGINE_INCOMPATIBLE = "engine_incompatible"  # 引擎不兼容


@dataclass
class ModConflict:
    """MOD冲突"""
    type: ModConflictType
    mod_a: str
    mod_b: str
    description: str


class ModManager:
    """
    MOD管理器
    
    管理第三方内容包（MOD）
    """
    
    def __init__(self, content_manager: ContentManager):
        self.cm = content_manager
        self._mods: Dict[str, ContentPack] = {}
        self._load_order: List[str] = []
    
    async def scan_mods(self) -> None:
        """扫描MOD目录"""
        mods_dir = self.cm.engine.config.mods_path
        
        for mod_file in mods_dir.glob("*.jpk"):
            try:
                pack = await self.cm._load_manifest_from_zip(mod_file)
                self._mods[pack.id] = pack
            except Exception as e:
                self.cm.engine.logger.error(f"Failed to load mod {mod_file}: {e}")
    
    def check_conflicts(self) -> List[ModConflict]:
        """检查MOD冲突"""
        conflicts = []
        
        mod_list = list(self._mods.values())
        
        for i, mod_a in enumerate(mod_list):
            for mod_b in mod_list[i+1:]:
                # 检查内容覆盖冲突
                conflicts.extend(
                    self._check_content_conflicts(mod_a, mod_b)
                )
                
                # 检查依赖冲突
                conflicts.extend(
                    self._check_dependency_conflicts(mod_a, mod_b)
                )
        
        return conflicts
    
    def _check_content_conflicts(
        self, 
        mod_a: ContentPack, 
        mod_b: ContentPack
    ) -> List[ModConflict]:
        """检查内容覆盖冲突"""
        conflicts = []
        
        # 检查是否有相同ID的内容
        content_a = set(self._get_content_ids(mod_a))
        content_b = set(self._get_content_ids(mod_b))
        
        overlapping = content_a & content_b
        
        for content_id in overlapping:
            conflicts.append(ModConflict(
                type=ModConflictType.CONTENT_OVERRIDE,
                mod_a=mod_a.id,
                mod_b=mod_b.id,
                description=f"Both mods override content: {content_id}"
            ))
        
        return conflicts
    
    def resolve_load_order(self) -> List[str]:
        """解析MOD加载顺序"""
        # 拓扑排序处理依赖关系
        # 基础内容包 -> 依赖包 -> 覆盖包
        
        graph: Dict[str, List[str]] = {}
        in_degree: Dict[str, int] = {}
        
        # 构建依赖图
        for mod_id, pack in self._mods.items():
            graph[mod_id] = []
            in_degree[mod_id] = 0
            
            deps = pack.manifest.get("dependencies", {}).get("required", [])
            for dep in deps:
                if dep in self._mods:
                    graph[dep].append(mod_id)
                    in_degree[mod_id] += 1
        
        # 拓扑排序
        queue = [mid for mid, deg in in_degree.items() if deg == 0]
        result = []
        
        while queue:
            mod_id = queue.pop(0)
            result.append(mod_id)
            
            for dependent in graph[mod_id]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        return result
```

### 7.2 MOD覆盖规则

```python
class ModOverrideResolver:
    """
    MOD覆盖解析器
    
    处理MOD之间的内容覆盖
    """
    
    def __init__(self, load_order: List[str]):
        self.load_order = load_order
        self._override_rules: Dict[str, str] = {}  # content_id -> mod_id
    
    def register_override(self, mod_id: str, content_id: str) -> None:
        """注册覆盖"""
        # 后加载的MOD优先
        if content_id in self._override_rules:
            current_winner = self._override_rules[content_id]
            
            # 比较加载顺序
            if self.load_order.index(mod_id) > self.load_order.index(current_winner):
                self._override_rules[content_id] = mod_id
        else:
            self._override_rules[content_id] = mod_id
    
    def get_effective_source(self, content_id: str) -> Optional[str]:
        """获取内容的有效来源MOD"""
        return self._override_rules.get(content_id)
```

---

## 八、工具链

### 8.1 内容包打包工具

```bash
#!/bin/bash
# tools/pack_content.sh

# 打包内容目录为.jpk文件
CONTENT_DIR=$1
OUTPUT_FILE=$2

# 创建临时目录
TMP_DIR=$(mktemp -d)

# 复制内容
cp -r "$CONTENT_DIR"/* "$TMP_DIR/"

# 生成校验和
cd "$TMP_DIR"
find . -type f -exec sha256sum {} \; > _meta/checksums.json

# 打包为ZIP
zip -r "$OUTPUT_FILE" .

# 清理
cd -
rm -rf "$TMP_DIR"

echo "Packed: $OUTPUT_FILE"
```

### 8.2 内容验证工具

```python
# tools/validate_content.py

import json
import jsonschema
from pathlib import Path


def validate_content_pack(pack_path: Path) -> bool:
    """验证内容包"""
    
    # 1. 检查manifest
    manifest_path = pack_path / "manifest.json"
    if not manifest_path.exists():
        print("ERROR: manifest.json not found")
        return False
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    # 2. 验证manifest结构
    required_fields = ["format_version", "package.id", "package.version"]
    for field in required_fields:
        keys = field.split(".")
        value = manifest
        for key in keys:
            if key not in value:
                print(f"ERROR: Missing field: {field}")
                return False
            value = value[key]
    
    # 3. 验证内容文件
    content_config = manifest.get("content", {})
    
    for content_type, config in content_config.items():
        content_dir = pack_path / config["path"]
        if not content_dir.exists():
            print(f"WARNING: Content directory not found: {content_dir}")
            continue
        
        # 加载schema
        schema_path = Path("schemas") / f"{content_type}-v1.json"
        if schema_path.exists():
            with open(schema_path) as f:
                schema = json.load(f)
            
            # 验证每个文件
            for file_path in content_dir.rglob("*.json"):
                with open(file_path) as f:
                    data = json.load(f)
                
                try:
                    jsonschema.validate(data, schema)
                except jsonschema.ValidationError as e:
                    print(f"ERROR in {file_path}: {e.message}")
                    return False
    
    print("Validation passed!")
    return True
```

### 8.3 内容编辑器集成

```python
# 游戏内开发者命令

class DevCommands:
    """开发者命令"""
    
    async def cmd_content_reload(self, args: str) -> str:
        """
        重新加载内容
        
        用法: /content reload [room|npc|skill|all] [id]
        """
        parts = args.split()
        
        if not parts:
            return "Usage: /content reload [type] [id]"
        
        content_type = parts[0]
        
        if content_type == "all":
            # 重载所有内容
            for pack_id in self.engine.content_manager._packs:
                await self.engine.content_manager.reload_pack(pack_id)
            return "All content reloaded."
        
        if len(parts) < 2:
            return "Please specify content id"
        
        content_id = parts[1]
        
        # 重载特定内容
        type_map = {
            "room": ContentType.ROOM,
            "npc": ContentType.NPC,
            "skill": ContentType.SKILL,
        }
        
        if content_type in type_map:
            await self.engine.content_manager.reload_content(
                type_map[content_type],
                content_id
            )
            return f"Reloaded {content_type}: {content_id}"
        
        return f"Unknown content type: {content_type}"
    
    async def cmd_content_status(self, args: str) -> str:
        """查看内容加载状态"""
        cm = self.engine.content_manager
        
        lines = ["Content Status:", "-" * 40]
        
        # 内容包状态
        lines.append(f"Packs loaded: {len(cm._packs)}")
        for pack_id, pack in cm._packs.items():
            lines.append(f"  [{pack_id}] v{pack.version} - {'enabled' if pack.enabled else 'disabled'}")
        
        # 内容统计
        lines.append("")
        lines.append("Content counts:")
        for content_type, registry in cm._registries.items():
            lines.append(f"  {content_type.name}: {registry.count()}")
        
        return "\n".join(lines)
```

---

## 九、实施计划

### 9.1 开发阶段

| 阶段 | 任务 | 工期 | 产出 |
|:---|:---|:---:|:---|
| **Phase 1** | 内容包格式设计 | 2天 | manifest.json schema |
| **Phase 2** | ContentManager基础 | 3天 | manager.py, registry.py |
| **Phase 3** | 文件加载器 | 2天 | JSON/YAML loaders, providers |
| **Phase 4** | 热重载 | 2天 | hot_reload.py, file watcher |
| **Phase 5** | MOD支持 | 3天 | mod_manager.py, conflict resolver |
| **Phase 6** | 工具链 | 2天 | pack, validate, editor tools |
| **Phase 7** | 集成测试 | 2天 | test suite, documentation |
| **总计** | | **16天** | |

### 9.2 与转换器的集成

```
转换器输出 ──→ 内容包格式 ──→ 游戏加载
    ↓              ↓              ↓
LPC文件      manifest.json    ContentManager
                content/          ↓
                  rooms/      游戏世界
                  npcs/
                  skills/
```

### 9.3 配置示例

```yaml
# config.yaml
content:
  # 内容路径
  content_path: "./content"
  mods_path: "./mods"
  cache_path: "./cache"
  
  # 热重载
  hot_reload:
    enabled: true
    debounce_ms: 500
    auto_reload: true
  
  # MOD
  mods:
    enabled: true
    load_order: "auto"  # auto 或指定列表
    conflict_resolution: "priority"  # priority/error/merge
  
  # 缓存
  cache:
    enabled: true
    ttl: 3600
    max_size: "100MB"
```

---

## 十、总结

### 10.1 关键设计决策

| 决策 | 选择 | 理由 |
|:---|:---|:---|
| 内容包格式 | ZIP (JPK) | 压缩、校验、易分发 |
| 清单格式 | JSON | 标准化、易解析 |
| 内容格式 | JSON | 类型安全、Schema验证 |
| 热更新 | 文件监听 | 简单、通用 |
| MOD隔离 | 命名空间 | 避免冲突 |
| 加载顺序 | 优先级+依赖 | 灵活但可控 |

### 10.2 文件清单

```
src/game/content/
├── __init__.py
├── manager.py          # ContentManager
├── registry.py         # ContentRegistry
├── loaders.py          # JSON/YAMLLoader
├── providers.py        # File/ZipProvider
├── hot_reload.py       # HotReloader
├── mod_manager.py      # ModManager
├── instance_updater.py # InstanceUpdater
├── schemas/            # JSON Schemas
│   ├── room-v1.json
│   ├── npc-v1.json
│   ├── skill-v1.json
│   └── manifest-v1.json
└── definitions.py      # 定义类

tools/
├── pack_content.py     # 打包工具
├── validate_content.py # 验证工具
└── content_editor/     # 内容编辑器
```

---

*文档版本: 1.0*
*最后更新: 2026-02-26*
