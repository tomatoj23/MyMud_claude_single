"""存档管理器."""

from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import msgpack

if TYPE_CHECKING:
    from src.engine.core.engine import GameEngine


@dataclass
class SaveInfo:
    """存档信息."""

    slot: str
    name: str
    timestamp: str
    version: int
    play_time: int  # 秒
    level: int
    location: str
    checksum: str
    compressed_size: int


class SaveManager:
    """存档管理器.

    功能：
    - MessagePack序列化
    - Gzip压缩
    - 自动存档轮转
    - 版本兼容性检查
    """

    SAVE_DIR = Path("saves")
    SAVE_VERSION = 1  # 存档格式版本

    def __init__(self, engine: GameEngine) -> None:
        """初始化存档管理器.

        Args:
            engine: 游戏引擎实例
        """
        self.engine = engine
        self._ensure_save_dir()
        self._play_time_start = datetime.now()

    def _ensure_save_dir(self) -> None:
        """确保存档目录存在."""
        self.SAVE_DIR.mkdir(parents=True, exist_ok=True)

    async def save(self, slot: str, name: str = "") -> Path:
        """保存游戏.

        Args:
            slot: 存档槽位
            name: 存档名称

        Returns:
            存档文件路径
        """
        # 序列化游戏数据
        data = await self._serialize_game_state()

        # 添加元数据
        save_data = {
            "version": self.SAVE_VERSION,
            "timestamp": datetime.now().isoformat(),
            "name": name or f"存档_{slot}",
            "slot": slot,
            "data": data,
        }

        # MessagePack编码
        packed = msgpack.packb(save_data, use_bin_type=True)

        # Gzip压缩
        compressed = gzip.compress(packed, compresslevel=6)

        # 计算校验和
        checksum = hashlib.sha256(compressed).hexdigest()

        # 保存到文件
        save_path = self.SAVE_DIR / f"{slot}.sav"
        save_path.write_bytes(compressed)

        # 保存元信息
        info = SaveInfo(
            slot=slot,
            name=save_data["name"],
            timestamp=save_data["timestamp"],
            version=self.SAVE_VERSION,
            play_time=int((datetime.now() - self._play_time_start).total_seconds()),
            level=data.get("player", {}).get("level", 1),
            location=data.get("player", {}).get("location", "未知"),
            checksum=checksum,
            compressed_size=len(compressed),
        )

        info_path = self.SAVE_DIR / f"{slot}.json"
        info_path.write_text(json.dumps(asdict(info), ensure_ascii=False, indent=2))

        return save_path

    async def load(self, slot: str) -> dict[str, Any]:
        """读取游戏.

        Args:
            slot: 存档槽位

        Returns:
            游戏数据

        Raises:
            FileNotFoundError: 存档不存在
            ValueError: 存档损坏或版本不兼容
        """
        save_path = self.SAVE_DIR / f"{slot}.sav"
        if not save_path.exists():
            raise FileNotFoundError(f"存档不存在: {slot}")

        # 读取文件
        compressed = save_path.read_bytes()

        # 验证校验和
        info = self.get_save_info(slot)
        if info:
            checksum = hashlib.sha256(compressed).hexdigest()
            if checksum != info.checksum:
                raise ValueError("存档校验失败，文件可能已损坏")

        # 解压缩
        packed = gzip.decompress(compressed)

        # MessagePack解码
        save_data = msgpack.unpackb(packed, raw=False)

        # 版本检查
        if save_data["version"] != self.SAVE_VERSION:
            raise ValueError(
                f"存档版本不兼容: {save_data['version']} != {self.SAVE_VERSION}"
            )

        # 恢复游戏状态
        await self._deserialize_game_state(save_data["data"])

        return save_data

    def get_save_info(self, slot: str) -> SaveInfo | None:
        """获取存档信息.

        Args:
            slot: 存档槽位

        Returns:
            存档信息，不存在返回None
        """
        info_path = self.SAVE_DIR / f"{slot}.json"
        if not info_path.exists():
            return None

        data = json.loads(info_path.read_text())
        return SaveInfo(**data)

    def list_saves(self) -> list[SaveInfo]:
        """列出所有存档.

        Returns:
            存档信息列表
        """
        saves = []
        for info_file in self.SAVE_DIR.glob("*.json"):
            try:
                data = json.loads(info_file.read_text())
                saves.append(SaveInfo(**data))
            except Exception:
                continue

        # 按时间倒序排序
        saves.sort(key=lambda x: x.timestamp, reverse=True)
        return saves

    def delete_save(self, slot: str) -> None:
        """删除存档.

        Args:
            slot: 存档槽位
        """
        save_path = self.SAVE_DIR / f"{slot}.sav"
        info_path = self.SAVE_DIR / f"{slot}.json"

        if save_path.exists():
            save_path.unlink()
        if info_path.exists():
            info_path.unlink()

    async def _serialize_game_state(self) -> dict[str, Any]:
        """序列化游戏状态.

        Returns:
            游戏状态数据
        """
        # 获取所有对象
        objects = await self.engine.objects.get_all()

        # 序列化对象
        serialized_objects = []
        for obj in objects:
            obj_data = {
                "id": obj.id,
                "key": obj.key,
                "typeclass_path": obj.typeclass_path,
                "attributes": dict(obj.db._attributes) if hasattr(obj.db, "_attributes") else {},
            }
            serialized_objects.append(obj_data)

        # 提取玩家信息
        player_data = {}
        if hasattr(self.engine, "_player_ref"):
            player = self.engine._player_ref
            if player:
                player_data = {
                    "id": player.id,
                    "key": player.key,
                    "level": getattr(player.db, "level", 1),
                    "location": player.location.key if player.location else "未知",
                }

        return {
            "objects": serialized_objects,
            "player": player_data,
        }

    async def _deserialize_game_state(self, data: dict[str, Any]) -> None:
        """反序列化游戏状态.

        Args:
            data: 游戏状态数据
        """
        # 清空当前对象
        await self.engine.objects.clear_all()

        # 重建对象
        for obj_data in data.get("objects", []):
            await self.engine.objects.create(
                typeclass_path=obj_data["typeclass_path"],
                key=obj_data["key"],
                attributes=obj_data["attributes"],
            )

        # 恢复玩家引用
        player_data = data.get("player", {})
        if player_data:
            player = await self.engine.objects.get(player_data["id"])
            if player:
                self.engine._player_ref = player
