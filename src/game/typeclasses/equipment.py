"""装备系统.

提供12+装备槽位、属性加成、套装效果、耐久度和绑定机制.
"""

from __future__ import annotations

from enum import Enum, IntEnum
from typing import TYPE_CHECKING, Any, Optional

from src.engine.core.typeclass import TypeclassBase

if TYPE_CHECKING:
    from .character import Character


class EquipmentSlot(Enum):
    """装备槽位."""

    MAIN_HAND = "main_hand"  # 主手武器
    OFF_HAND = "off_hand"  # 副手（盾牌/暗器）
    HEAD = "head"  # 头
    BODY = "body"  # 身（衣服）
    WAIST = "waist"  # 腰（腰带）
    LEGS = "legs"  # 腿
    FEET = "feet"  # 足（鞋）
    NECK = "neck"  # 项链
    RING1 = "ring1"  # 戒指1
    RING2 = "ring2"  # 戒指2
    JADE = "jade"  # 玉佩
    HANDS = "hands"  # 手（手套/护腕）


# 槽位中文名
SLOT_NAMES = {
    EquipmentSlot.MAIN_HAND: "主手",
    EquipmentSlot.OFF_HAND: "副手",
    EquipmentSlot.HEAD: "头部",
    EquipmentSlot.BODY: "身体",
    EquipmentSlot.WAIST: "腰部",
    EquipmentSlot.LEGS: "腿部",
    EquipmentSlot.FEET: "足部",
    EquipmentSlot.NECK: "项链",
    EquipmentSlot.RING1: "戒指",
    EquipmentSlot.RING2: "戒指",
    EquipmentSlot.JADE: "玉佩",
    EquipmentSlot.HANDS: "手部",
}


class EquipmentQuality(IntEnum):
    """装备品质."""

    COMMON = 1  # 普通（白色）
    UNCOMMON = 2  # 优秀（绿色）
    RARE = 3  # 精良（蓝色）
    EPIC = 4  # 史诗（紫色）
    LEGENDARY = 5  # 传说（橙色）


QUALITY_NAMES = {
    EquipmentQuality.COMMON: "普通",
    EquipmentQuality.UNCOMMON: "优秀",
    EquipmentQuality.RARE: "精良",
    EquipmentQuality.EPIC: "史诗",
    EquipmentQuality.LEGENDARY: "传说",
}


class Equipment(TypeclassBase):
    """装备类型.

    Attributes:
        typeclass_path: 类型路径
    """

    typeclass_path = "src.game.typeclasses.equipment.Equipment"

    @property
    def slot(self) -> EquipmentSlot:
        """装备槽位."""
        return EquipmentSlot(self.db.get("slot", "main_hand"))

    @slot.setter
    def slot(self, value: EquipmentSlot) -> None:
        self.db.set("slot", value.value)

    @property
    def quality(self) -> EquipmentQuality:
        """品质 1-5."""
        return EquipmentQuality(self.db.get("quality", 1))

    @quality.setter
    def quality(self, value: EquipmentQuality) -> None:
        self.db.set("quality", int(value))

    @property
    def quality_name(self) -> str:
        """品质名称."""
        return QUALITY_NAMES.get(self.quality, "未知")

    @property
    def stats_bonus(self) -> dict[str, int]:
        """属性加成.

        Returns:
            {"strength": 5, "attack": 20, ...}
        """
        return self.db.get("stats_bonus", {})

    @stats_bonus.setter
    def stats_bonus(self, value: dict[str, int]) -> None:
        self.db.set("stats_bonus", value)

    @property
    def durability(self) -> tuple[int, int]:
        """(当前, 最大)耐久."""
        return self.db.get("durability", (100, 100))

    @durability.setter
    def durability(self, value: tuple[int, int]) -> None:
        self.db.set("durability", value)

    def modify_durability(self, delta: int) -> int:
        """修改耐久度.

        Args:
            delta: 变化值（负数为消耗）

        Returns:
            当前耐久度
        """
        current, max_dur = self.durability
        new_dur = max(0, min(current + delta, max_dur))
        was_broken = self.is_broken
        self.durability = (new_dur, max_dur)

        # 如果装备从正常变为损坏，通知持有者使缓存失效
        if not was_broken and self.is_broken:
            if self.location and hasattr(self.location, '_invalidate_equipment_cache'):
                self.location._invalidate_equipment_cache()

        return new_dur

    @property
    def is_broken(self) -> bool:
        """是否损坏（耐久为0）."""
        if isinstance(self.durability, (list, tuple)):
            return self.durability[0] <= 0
        return self.durability <= 0

    @property
    def is_bound(self) -> bool:
        """是否绑定."""
        return self.db.get("is_bound", False)

    def bind(self) -> None:
        """绑定装备."""
        self.db.set("is_bound", True)

    @property
    def name(self) -> str:
        """装备显示名称.

        人类可读的显示名称。如果未设置，则回退到 key。
        存储在 attributes 中，无需数据库迁移。

        Returns:
            显示名称，或 key（如果 name 未设置）
        """
        return self.db.get("name") or self.key

    @name.setter
    def name(self, value: str) -> None:
        """设置装备显示名称."""
        self.db.set("name", value)

    @property
    def set_name(self) -> Optional[str]:
        """所属套装."""
        return self.db.get("set_name")

    @set_name.setter
    def set_name(self, value: Optional[str]) -> None:
        self.db.set("set_name", value)

    @property
    def level_requirement(self) -> int:
        """等级要求."""
        return self.db.get("level_requirement", 1)

    @level_requirement.setter
    def level_requirement(self, value: int) -> None:
        self.db.set("level_requirement", value)

    @property
    def menpai_requirement(self) -> Optional[str]:
        """门派要求."""
        return self.db.get("menpai_requirement")

    @menpai_requirement.setter
    def menpai_requirement(self, value: Optional[str]) -> None:
        self.db.set("menpai_requirement", value)

    def can_equip_by(self, character: "Character") -> tuple[bool, str]:
        """检查角色是否可以装备.

        Args:
            character: 角色

        Returns:
            (是否可以, 原因)
        """
        # 等级检查
        if character.level < self.level_requirement:
            return False, f"等级不足（需要{self.level_requirement}级）"

        # 门派检查
        if self.menpai_requirement:
            if character.menpai != self.menpai_requirement:
                return False, f"仅限{self.menpai_requirement}弟子装备"

        return True, ""

    def get_desc(self) -> str:
        """获取装备描述."""
        desc = f"[{self.quality_name}] {self.name}\n"
        desc += f"部位: {SLOT_NAMES.get(self.slot, '未知')}\n"

        # 属性加成
        if self.stats_bonus:
            desc += "属性:\n"
            for stat, value in self.stats_bonus.items():
                desc += f"  +{value} {stat}\n"

        # 耐久
        current, max_dur = self.durability
        desc += f"耐久: {current}/{max_dur}\n"

        # 套装
        if self.set_name:
            desc += f"套装: {self.set_name}\n"

        # 绑定状态
        if self.is_bound:
            desc += "[已绑定]\n"

        return desc

    # ===== 生命周期钩子 =====
    def at_equipped(self, character: "Character") -> None:
        """被装备时调用."""
        pass

    def at_unequipped(self, character: "Character") -> None:
        """被卸下时调用."""
        pass


class CharacterEquipmentMixin:
    """角色的装备管理（混入Character类）."""

    def __init__(self, *args, **kwargs) -> None:
        """初始化装备管理."""
        super().__init__(*args, **kwargs)
        # 装备属性缓存
        self._cached_total_stats: Optional[dict[str, int]] = None

    def _equipment_invalidate_cache(self) -> None:
        """使装备属性缓存失效.

        在装备变更、卸下、装备属性变化时调用。
        """
        self._cached_total_stats = None

    @property
    def equipment_slots(self) -> dict[str, Optional[int]]:
        """已装备物品 {slot_value: equipment_id}.

        Returns:
            {slot_key: Equipment ID or None}
        """
        return self.db.get("equipped", {})

    @equipment_slots.setter
    def equipment_slots(self, value: dict[str, Optional[int]]) -> None:
        self.db.set("equipped", value)

    def equipment_get_item(self, slot: EquipmentSlot) -> Optional[Equipment]:
        """获取指定槽位装备.

        Args:
            slot: 装备槽位

        Returns:
            装备对象，未装备返回None
        """
        from src.engine.core.typeclass import TypeclassBase

        equipped = self.equipment_slots
        obj_id = equipped.get(slot.value)
        if obj_id and hasattr(self, "_manager"):
            obj = self._manager.get(obj_id)
            if isinstance(obj, Equipment):
                return obj
        return None

    async def equipment_equip(self, item: Equipment) -> tuple[bool, str]:
        """装备物品.

        Args:
            item: 装备物品

        Returns:
            (是否成功, 消息)
        """
        # 检查是否可以装备
        can_equip, reason = item.can_equip_by(self)
        if not can_equip:
            return False, reason

        # 检查物品是否在背包中（location 是 self）
        if item.location != self:
            return False, "物品不在背包中"

        slot = item.slot

        # 如果槽位已有装备，先卸下
        current = self.equipment_get_item(slot)
        if current:
            await self.equipment_unequip(slot)

        # 装备新物品
        equipped = self.equipment_slots
        equipped[slot.value] = item.id
        self.equipment_slots = equipped

        # 绑定装备
        if not item.is_bound:
            item.bind()

        # 触发装备钩子
        item.at_equipped(self)
        self.equipment_on_equip(item)

        # 使属性缓存失效
        self._equipment_invalidate_cache()

        return True, f"装备成功：{item.name}"

    async def equipment_unequip(self, slot: EquipmentSlot) -> tuple[bool, str]:
        """卸下装备.

        Args:
            slot: 装备槽位

        Returns:
            (是否成功, 消息)
        """
        current = self.equipment_get_item(slot)
        if not current:
            return False, "该槽位未装备物品"

        # 从装备栏移除
        equipped = self.equipment_slots
        del equipped[slot.value]
        self.equipment_slots = equipped

        # 触发卸下钩子
        current.at_unequipped(self)
        self.equipment_on_unequip(current)

        # 使属性缓存失效
        self._equipment_invalidate_cache()

        return True, f"卸下成功：{current.name}"

    def equipment_get_stats(self) -> dict[str, int]:
        """计算所有装备属性总和（带缓存）.

        Returns:
            属性加成总和
        """
        # 检查缓存
        if self._cached_total_stats is not None:
            return self._cached_total_stats.copy()

        # 计算属性
        total: dict[str, int] = {}

        for slot in EquipmentSlot:
            item = self.equipment_get_item(slot)
            if item and not item.is_broken:
                for stat, value in item.stats_bonus.items():
                    total[stat] = total.get(stat, 0) + value

        # 缓存结果
        self._cached_total_stats = total.copy()

        return total

    def equipment_get_set_bonuses(self) -> dict[str, Any]:
        """计算套装效果.

        Returns:
            套装效果，格式: {
                "套装名称": {
                    "count": 件数,
                    "level": SetBonusLevel对象,
                    "stats": {属性加成},
                    "special": 特殊效果
                }
            }
        """
        from src.game.data.set_bonuses import get_set_bonus_config
        
        # 统计各套装件数
        set_counts: dict[str, int] = {}
        for slot in EquipmentSlot:
            item = self.equipment_get_item(slot)
            if item and item.set_name:
                set_counts[item.set_name] = set_counts.get(item.set_name, 0) + 1

        # 计算套装效果
        bonuses: dict[str, Any] = {}
        for set_name, count in set_counts.items():
            config = get_set_bonus_config(set_name)
            if config:
                bonus_level = config.get_bonus_for_count(count)
                if bonus_level:
                    bonuses[set_name] = {
                        "count": count,
                        "level": bonus_level,
                        "stats": bonus_level.stats_bonus or {},
                        "special": bonus_level.special_effect
                    }

        return bonuses
    
    def equipment_get_set_stats(self) -> dict[str, int | float]:
        """获取所有套装效果提供的总属性加成.
        
        Returns:
            合并后的属性加成字典
        """
        total_stats: dict[str, int | float] = {}
        set_bonuses = self.equipment_get_set_bonuses()
        
        for set_name, bonus_info in set_bonuses.items():
            stats = bonus_info.get("stats", {})
            for stat, value in stats.items():
                if stat in total_stats:
                    total_stats[stat] += value
                else:
                    total_stats[stat] = value
        
        return total_stats
    
    def equipment_get_set_info(self) -> list[dict]:
        """获取套装信息列表（用于显示）.
        
        Returns:
            套装信息列表
        """
        from src.game.data.set_bonuses import get_set_bonus_config
        
        # 统计各套装件数
        set_counts: dict[str, int] = {}
        for slot in EquipmentSlot:
            item = self.equipment_get_item(slot)
            if item and item.set_name:
                set_counts[item.set_name] = set_counts.get(item.set_name, 0) + 1
        
        result = []
        for set_name, count in set_counts.items():
            config = get_set_bonus_config(set_name)
            info = {
                "name": set_name,
                "count": count,
                "max_pieces": config.max_pieces if config else 0,
                "active_bonus": None,
                "next_bonus": None
            }
            
            if config:
                # 当前激活的效果
                active = config.get_bonus_for_count(count)
                if active:
                    info["active_bonus"] = {
                        "description": active.description,
                        "required": active.required_count
                    }
                
                # 下一个效果
                for level in sorted(config.bonus_levels, key=lambda b: b.required_count):
                    if level.required_count > count:
                        info["next_bonus"] = {
                            "description": level.description,
                            "required": level.required_count
                        }
                        break
            
            result.append(info)
        
        return result

    def equipment_get_attack_bonus(self) -> int:
        """获取装备提供的攻击力加成."""
        return self.equipment_get_stats().get("attack", 0)

    def equipment_get_defense_bonus(self) -> int:
        """获取装备提供的防御力加成."""
        return self.equipment_get_stats().get("defense", 0)

    # ===== 生命周期钩子 =====
    def equipment_on_equip(self, item: Equipment) -> None:
        """装备时调用."""
        pass

    def equipment_on_unequip(self, item: Equipment) -> None:
        """卸下时调用."""
        pass
