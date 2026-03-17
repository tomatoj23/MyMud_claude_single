"""BUFF/DEBUFF系统."""

from __future__ import annotations

import time
from enum import Enum
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from src.game.typeclasses.character import Character


class BuffType(Enum):
    """BUFF类型."""

    BUFF = "buff"  # 增益
    DEBUFF = "debuff"  # 减益
    NEUTRAL = "neutral"  # 中性


class Buff:
    """状态效果.

    Attributes:
        key: 唯一标识
        name: 显示名
        duration: 持续时间（秒）
        buff_type: BUFF类型
        stack_limit: 叠加上限
        stats_mod: 属性修正
        on_apply: 应用时回调
        on_tick: 每tick回调
        on_remove: 移除时回调
    """

    def __init__(
        self,
        key: str,
        name: str,
        duration: float,  # 持续时间（秒）
        buff_type: BuffType = BuffType.NEUTRAL,
        stack_limit: int = 1,
        stats_mod: dict[str, int] | None = None,
        on_apply: Callable[[Character], None] | None = None,
        on_tick: Callable[[Character], None] | None = None,
        on_remove: Callable[[Character], None] | None = None,
    ):
        self.key = key
        self.name = name
        self.duration = duration
        self.buff_type = buff_type
        self.stack_limit = stack_limit
        self.stats_mod = stats_mod or {}

        # 回调函数
        self._on_apply = on_apply
        self._on_tick = on_tick
        self._on_remove = on_remove

        # 运行时状态
        self.stacks = 1
        self.applied_at = time.time()
        self.expires_at = self.applied_at + duration

    def is_expired(self, now: float | None = None) -> bool:
        """检查是否已过期."""
        if now is None:
            now = time.time()
        return now >= self.expires_at

    def get_remaining_time(self, now: float | None = None) -> float:
        """获取剩余时间（秒）."""
        if now is None:
            now = time.time()
        return max(0.0, self.expires_at - now)

    async def apply(self, character: Character) -> None:
        """应用BUFF效果."""
        if self._on_apply:
            self._on_apply(character)

    async def tick(self, character: Character) -> None:
        """执行tick效果."""
        if self._on_tick:
            self._on_tick(character)

    async def remove(self, character: Character) -> None:
        """移除BUFF效果."""
        if self._on_remove:
            self._on_remove(character)


class BuffManager:
    """角色BUFF管理.

    管理角色身上的所有BUFF/DEBUFF：
    - 添加/移除BUFF
    - 定时结算
    - 属性修正计算

    Example:
        buff = Buff("poison", "中毒", duration=10, buff_type=BuffType.DEBUFF)
        await character.buff_manager.add(buff)

        # 在战斗循环中调用
        await character.buff_manager.tick()
    """

    def __init__(self, character: Character):
        self.character = character
        self._buffs: dict[str, Buff] = {}
        self._last_tick = time.time()

    async def add(self, buff: Buff) -> bool:
        """添加BUFF.

        Args:
            buff: BUFF对象

        Returns:
            是否成功添加
        """
        existing = self._buffs.get(buff.key)

        if existing:
            # 叠加逻辑
            if existing.stacks < existing.stack_limit:
                existing.stacks += 1
                # 刷新持续时间
                existing.expires_at = time.time() + buff.duration
                return True
            else:
                # 已达上限，仅刷新持续时间
                existing.expires_at = time.time() + buff.duration
                return True

        # 新BUFF
        self._buffs[buff.key] = buff
        await buff.apply(self.character)
        return True

    async def remove(self, buff_key: str) -> bool:
        """移除BUFF.

        Args:
            buff_key: BUFF标识

        Returns:
            是否成功移除
        """
        buff = self._buffs.pop(buff_key, None)
        if buff:
            await buff.remove(self.character)
            return True
        return False

    async def tick(self) -> list[str]:
        """执行BUFF结算.

        清理过期BUFF，执行tick效果。

        Returns:
            结算消息列表
        """
        now = time.time()
        expired = []
        messages = []

        for key, buff in list(self._buffs.items()):
            # 执行tick效果
            await buff.tick(self.character)

            # 检查是否过期
            if buff.is_expired(now):
                expired.append(key)

        # 移除过期BUFF
        for key in expired:
            buff = self._buffs.pop(key)
            await buff.remove(self.character)
            messages.append(f"{buff.name}效果消失了。")

        self._last_tick = now
        return messages

    def get_stats_modifier(self) -> dict[str, int]:
        """获取所有BUFF的属性修正总和.

        Returns:
            属性修正字典
        """
        total: dict[str, int] = {}

        for buff in self._buffs.values():
            for stat, value in buff.stats_mod.items():
                total[stat] = total.get(stat, 0) + value * buff.stacks

        return total

    def has_buff(self, buff_key: str) -> bool:
        """检查是否有指定BUFF."""
        buff = self._buffs.get(buff_key)
        if buff and not buff.is_expired():
            return True
        return False

    def get_buffs(self, buff_type: BuffType | None = None) -> list[Buff]:
        """获取BUFF列表.

        Args:
            buff_type: 过滤类型，None表示全部

        Returns:
            BUFF列表
        """
        buffs = list(self._buffs.values())

        if buff_type:
            buffs = [b for b in buffs if b.buff_type == buff_type]

        # 过滤过期BUFF
        now = time.time()
        return [b for b in buffs if not b.is_expired(now)]

    def clear(self) -> None:
        """清除所有BUFF."""
        self._buffs.clear()

    def get_summary(self) -> list[dict]:
        """获取BUFF摘要信息.

        Returns:
            BUFF信息列表，用于UI显示
        """
        now = time.time()
        return [
            {
                "key": b.key,
                "name": b.name,
                "type": b.buff_type.value,
                "stacks": b.stacks,
                "remaining": b.get_remaining_time(now),
            }
            for b in self._buffs.values()
            if not b.is_expired(now)
        ]

    @property
    def active_buffs(self) -> list[Buff]:
        """获取所有活跃BUFF."""
        now = time.time()
        return [b for b in self._buffs.values() if not b.is_expired(now)]

    async def update(self, elapsed: float) -> list[str]:
        """更新BUFF持续时间并清理过期BUFF.

        Args:
            elapsed: 经过的时间（秒）

        Returns:
            结算消息列表
        """
        return await self.tick()

    def serialize(self) -> list[dict]:
        """序列化所有活跃BUFF用于持久化."""
        now = time.time()
        return [
            {
                "key": b.key,
                "name": b.name,
                "duration": b.get_remaining_time(now),
                "buff_type": b.buff_type.value,
                "stack_limit": b.stack_limit,
                "stacks": b.stacks,
                "stats_mod": b.stats_mod,
            }
            for b in self._buffs.values()
            if not b.is_expired(now)
        ]

    def deserialize(self, data: list[dict]) -> None:
        """从序列化数据恢复BUFF."""
        self._buffs.clear()
        for item in data:
            buff = Buff(
                key=item["key"],
                name=item["name"],
                duration=item.get("duration", 0),
                buff_type=BuffType(item.get("buff_type", "neutral")),
                stack_limit=item.get("stack_limit", 1),
                stats_mod=item.get("stats_mod", {}),
            )
            buff.stacks = item.get("stacks", 1)
            self._buffs[buff.key] = buff


# 常用BUFF定义

BUFF_DEFENDING = Buff(
    key="defending",
    name="防御姿态",
    duration=3.0,
    buff_type=BuffType.BUFF,
    stats_mod={"defense": 20},
)

BUFF_STUN = Buff(
    key="stun",
    name="眩晕",
    duration=2.0,
    buff_type=BuffType.DEBUFF,
    stats_mod={"agility": -50},
)

BUFF_POISON = Buff(
    key="poison",
    name="中毒",
    duration=10.0,
    buff_type=BuffType.DEBUFF,
)


def create_poison_buff(damage_per_tick: int = 5) -> Buff:
    """创建中毒BUFF.

    Args:
        damage_per_tick: 每跳伤害

    Returns:
        中毒BUFF实例
    """

    def on_tick(character: Character) -> None:
        character.modify_hp(-damage_per_tick)

    return Buff(
        key="poison",
        name="中毒",
        duration=10.0,
        buff_type=BuffType.DEBUFF,
        on_tick=on_tick,
    )


def create_regen_buff(heal_per_tick: int = 5) -> Buff:
    """创建生命恢复BUFF.

    Args:
        heal_per_tick: 每跳恢复量

    Returns:
        恢复BUFF实例
    """

    def on_tick(character: Character) -> None:
        character.modify_hp(heal_per_tick)

    return Buff(
        key="regen",
        name="生命恢复",
        duration=10.0,
        buff_type=BuffType.BUFF,
        on_tick=on_tick,
    )
