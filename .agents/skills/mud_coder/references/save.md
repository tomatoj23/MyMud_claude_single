# 存档系统

## 概述

存档系统使用 MessagePack 序列化游戏状态，支持压缩、加密、版本兼容性和自动存档。

## 核心实现

```python
# src/engine/save/manager.py
from __future__ import annotations

import msgpack
import gzip
import json
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.engine import GameEngine


@dataclass
class SaveInfo:
    """存档信息"""
    slot: str
    name: str
    timestamp: datetime
    version: str
    play_time: int  # 秒
    level: int
    location: str
    checksum: str   # 校验和
    compressed_size: int


class SaveManager:
    """存档管理器
    
    功能：
    - MessagePack序列化
    - Gzip压缩
    - 可选加密
    - 自动存档轮转
    - 版本兼容性检查
    """
    
    SAVE_DIR = Path("saves")
    AUTO_SAVE_SLOTS = 10
    QUICK_SAVE_SLOT = "quick"
    SAVE_VERSION = 1  # 存档格式版本
    
    def __init__(self, engine: GameEngine):
        self.engine = engine
        self._ensure_save_dir()
        self._play_time_start = datetime.now()
    
    def _ensure_save_dir(self) -> None:
        """确保存档目录存在"""
        self.SAVE_DIR.mkdir(parents=True, exist_ok=True)
    
    async def save(
        self, 
        slot: str, 
        name: str = "", 
        screenshot: Optional[bytes] = None
    ) -> Path:
        """保存游戏
        
        Args:
            slot: 存档槽位
            name: 存档名称
            screenshot: 截图数据（可选）
            
        Returns:
            存档文件路径
        """
        # 序列化游戏数据
        data = await self._serialize_game_state()
        
        # MessagePack编码
        packed = msgpack.packb(data, use_bin_type=True)
        
        # Gzip压缩
        compressed = gzip.compress(packed, compresslevel=6)
        
        # 可选：加密
        # compressed = self._encrypt(compressed)
        
        # 计算校验和
        checksum = hashlib.sha256(compressed).hexdigest()[:16]
        
        # 保存文件
        save_path = self.SAVE_DIR / f"{slot}.save"
        with open(save_path, "wb") as f:
            f.write(compressed)
        
        # 保存元数据
        meta = {
            "slot": slot,
            "name": name or f"存档 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "timestamp": datetime.now().isoformat(),
            "version": self.SAVE_VERSION,
            "play_time": self._get_play_time(),
            "level": data["player"].get("level", 1),
            "location": data["player"].get("location", "未知"),
            "checksum": checksum,
            "compressed_size": len(compressed),
        }
        
        meta_path = self.SAVE_DIR / f"{slot}.meta"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        
        return save_path
    
    async def load(self, slot: str) -> bool:
        """加载存档
        
        Args:
            slot: 存档槽位
            
        Returns:
            是否成功加载
        """
        save_path = self.SAVE_DIR / f"{slot}.save"
        if not save_path.exists():
            return False
        
        try:
            # 读取存档
            with open(save_path, "rb") as f:
                compressed = f.read()
            
            # 校验
            meta_path = self.SAVE_DIR / f"{slot}.meta"
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                
                checksum = hashlib.sha256(compressed).hexdigest()[:16]
                if checksum != meta.get("checksum"):
                    raise ValueError("存档校验失败，可能已损坏")
            
            # 可选：解密
            # compressed = self._decrypt(compressed)
            
            # 解压
            packed = gzip.decompress(compressed)
            
            # 反序列化
            data = msgpack.unpackb(packed, raw=False)
            
            # 版本检查
            if not self._check_version(data):
                return False
            
            # 加载游戏状态
            await self._deserialize_game_state(data)
            
            return True
            
        except Exception as e:
            print(f"加载存档失败: {e}")
            return False
    
    async def auto_save(self) -> Path:
        """自动存档（轮转）
        
        使用 10 个槽位轮转，覆盖最旧的存档
        """
        # 找到最旧的自动存档
        oldest_slot = 1
        oldest_time = None
        
        for i in range(1, self.AUTO_SAVE_SLOTS + 1):
            meta_path = self.SAVE_DIR / f"auto_{i:02d}.meta"
            if not meta_path.exists()():
                oldest_slot = i
                break
            
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            
            save_time = datetime.fromisoformat(meta["timestamp"])
            if oldest_time is None or save_time < oldest_time:
                oldest_time = save_time
                oldest_slot = i
        
        slot = f"auto_{oldest_slot:02d}"
        return await self.save(slot, name="自动存档")
    
    def get_save_list(self) -> list[SaveInfo]:
        """获取所有存档信息
        
        Returns:
            存档信息列表
        """
        saves = []
        
        for meta_path in self.SAVE_DIR.glob("*.meta"):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                
                saves.append(SaveInfo(
                    slot=meta["slot"],
                    name=meta["name"],
                    timestamp=datetime.fromisoformat(meta["timestamp"]),
                    version=meta["version"],
                    play_time=meta["play_time"],
                    level=meta["level"],
                    location=meta["location"],
                    checksum=meta["checksum"],
                    compressed_size=meta["compressed_size"],
                ))
            except Exception:
                continue
        
        # 按时间排序（最新的在前）
        saves.sort(key=lambda x: x.timestamp, reverse=True)
        return saves
    
    def delete_save(self, slot: str) -> bool:
        """删除存档
        
        Args:
            slot: 存档槽位
            
        Returns:
            是否成功删除
        """
        try:
            save_path = self.SAVE_DIR / f"{slot}.save"
            meta_path = self.SAVE_DIR / f"{slot}.meta"
            
            if save_path.exists():
                save_path.unlink()
            if meta_path.exists():
                meta_path.unlink()
            
            return True
        except Exception:
            return False
    
    async def _serialize_game_state(self) -> dict:
        """序列化游戏状态
        
        Returns:
            游戏状态字典
        """
        # 获取玩家角色
        player = await self._get_player_character()
        
        return {
            "version": self.SAVE_VERSION,
            "timestamp": datetime.now().isoformat(),
            "engine": {
                "time_scale": self.engine.events._time_scale,
            },
            "player": {
                "id": player.id if player else None,
                "key": player.key if player else "",
                "level": player.level if player else 1,
                "location": player.location.key if player and player.location else "",
                "coords": player.location.coords if player and player.location else [0, 0, 0],
                "data": self._serialize_character(player) if player else {},
            },
            "world_state": await self._serialize_world_state(),
            "quests": await self._serialize_quests(),
        }
    
    def _serialize_character(self, character) -> dict:
        """序列化角色数据"""
        return {
            "birth_talents": character.birth_talents,
            "attributes": character.attributes,
            "status": character.status,
            "level": character.level,
            "exp": character.exp,
            "menpai": character.menpai,
            "menpai_contrib": getattr(character, "menpai_contrib", 0),
            "learned_wuxue": character.learned_wuxue,
            "equipped": {
                slot: item.id 
                for slot, item in character.equipped.items() 
                if item
            },
            "inventory": [
                item.id for item in character.contents 
                if not hasattr(item, "slot")  # 非装备物品
            ],
            "internal_type": getattr(character, "internal_type", "neutral"),
            "meridians": getattr(character, "meridians", {}),
            "karma": {},  # TODO: 因果点
        }
    
    async def _serialize_world_state(self) -> dict:
        """序列化世界状态"""
        return {
            "active_rooms": self.engine.world_loader.get_active_rooms(),
            "time": datetime.now().isoformat(),
            # TODO: 其他世界状态
        }
    
    async def _serialize_quests(self) -> dict:
        """序列化任务状态"""
        # TODO: 从任务系统获取
        return {
            "active": [],
            "completed": [],
        }
    
    async def _deserialize_game_state(self, data: dict) -> None:
        """反序列化游戏状态"""
        # 恢复引擎状态
        if "engine" in data:
            self.engine.events.set_time_scale(
                data["engine"].get("time_scale", 1.0)
            )
        
        # 恢复玩家状态
        if "player" in data and data["player"]:
            await self._deserialize_player(data["player"])
        
        # 恢复世界状态
        if "world_state" in data:
            await self._deserialize_world_state(data["world_state"])
        
        # 恢复任务状态
        if "quests" in data:
            await self._deserialize_quests(data["quests"])
    
    async def _deserialize_player(self, player_data: dict) -> None:
        """恢复玩家数据"""
        # 获取或创建玩家角色
        player_id = player_data.get("id")
        if player_id:
            player = await self.engine.objects.get(player_id)
        else:
            player = None
        
        if player:
            # 恢复属性
            data = player_data.get("data", {})
            player.db.set("birth_talents", data.get("birth_talents", {}))
            player.db.set("attributes", data.get("attributes", {}))
            player.db.set("status", data.get("status", {}))
            player.db.set("level", data.get("level", 1))
            player.db.set("exp", data.get("exp", 0))
            player.db.set("menpai", data.get("menpai"))
            player.db.set("learned_wuxue", data.get("learned_wuxue", {}))
            
            # 恢复位置
            location_key = player_data.get("location")
            if location_key:
                rooms = await self.engine.objects.find(key_contains=location_key)
                if rooms:
                    player.location = rooms[0]
    
    async def _deserialize_world_state(self, world_data: dict) -> None:
        """恢复世界状态"""
        # 加载活跃房间
        active_rooms = world_data.get("active_rooms", [])
        for room_id in active_rooms:
            await self.engine.objects.get(room_id)
    
    async def _deserialize_quests(self, quest_data: dict) -> None:
        """恢复任务状态"""
        # TODO: 恢复任务进度
        pass
    
    def _check_version(self, data: dict) -> bool:
        """检查存档版本兼容性
        
        Args:
            data: 存档数据
            
        Returns:
            是否兼容
        """
        version = data.get("version", 0)
        
        if version > self.SAVE_VERSION:
            print(f"存档版本(v{version})高于游戏版本(v{self.SAVE_VERSION})")
            return False
        
        if version < self.SAVE_VERSION:
            print(f"存档版本(v{version})低于当前版本，将尝试迁移")
            # TODO: 版本迁移
            return self._migrate_version(data, version)
        
        return True
    
    def _migrate_version(self, data: dict, from_version: int) -> bool:
        """迁移旧版本存档"""
        # 版本迁移逻辑
        migrations = {
            # 0: self._migrate_v0_to_v1,
        }
        
        for v in range(from_version, self.SAVE_VERSION):
            if v in migrations:
                data = migrations[v](data)
        
        return True
    
    def _get_play_time(self) -> int:
        """获取游戏时间（秒）"""
        delta = datetime.now() - self._play_time_start
        return int(delta.total_seconds())
    
    async def _get_player_character(self):
        """获取玩家角色（TODO: 实际项目中需要正确获取）"""
        # 这里简化处理，实际应该从引擎状态获取
        return None
    
    def _encrypt(self, data: bytes) -> bytes:
        """加密数据（可选）"""
        # TODO: 实现加密
        return data
    
    def _decrypt(self, data: bytes) -> bytes:
        """解密数据"""
        # TODO: 实现解密
        return data
```

## 自动存档触发点

```python
# src/engine/save/auto_save_triggers.py

class AutoSaveTriggers:
    """自动存档触发器"""
    
    def __init__(self, save_manager: SaveManager):
        self.save_manager = save_manager
    
    async def on_area_enter(self, area_key: str) -> None:
        """进入新区域时触发"""
        await self.save_manager.auto_save()
    
    async def on_quest_complete(self, quest_key: str) -> None:
        """完成任务时触发"""
        await self.save_manager.auto_save()
    
    async def on_combat_win(self, combat_result: dict) -> None:
        """战斗胜利时触发"""
        # 只在大胜利时存档
        if combat_result.get("is_major"):
            await self.save_manager.auto_save()
    
    async def on_level_up(self, new_level: int) -> None:
        """升级时触发"""
        await self.save_manager.auto_save()
    
    async def on_game_exit(self) -> None:
        """退出游戏时触发"""
        await self.save_manager.auto_save()
```

## 使用示例

```python
# 创建存档管理器
save_manager = SaveManager(engine)

# 手动存档
save_path = await save_manager.save(
    slot="slot_01",
    name="通关前存档"
)
print(f"存档已保存: {save_path}")

# 自动存档
await save_manager.auto_save()

# 加载存档
success = await save_manager.load("slot_01")
if success:
    print("存档加载成功")
else:
    print("存档加载失败")

# 获取存档列表
saves = save_manager.get_save_list()
for save in saves:
    print(f"{save.slot}: {save.name} (Lv.{save.level})")

# 删除存档
save_manager.delete_save("auto_01")
```
