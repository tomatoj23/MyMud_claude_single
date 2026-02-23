# 装备系统

## 概述

装备系统提供12+装备槽位、属性加成、套装效果、耐久度和绑定机制。

## 装备槽位定义

```python
# src/game/typeclasses/equipment.py
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .character import Character


class EquipmentSlot(Enum):
    """装备槽位"""
    MAIN_HAND = "main_hand"    # 主手武器
    OFF_HAND = "off_hand"      # 副手（盾牌/暗器）
    HEAD = "head"              # 头
    BODY = "body"              # 身（衣服）
    WAIST = "waist"            # 腰（腰带）
    LEGS = "legs"              # 腿
    FEET = "feet"              # 足（鞋）
    NECK = "neck"              # 项链
    RING1 = "ring1"            # 戒指1
    RING2 = "ring2"            # 戒指2
    JADE = "jade"              # 玉佩
    HANDS = "hands"            # 手（手套/护腕）


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
```

## 装备类实现

```python
# src/game/typeclasses/equipment.py
from enum import IntEnum
from typing import Optional
from ..item import Item, ItemType


class EquipmentQuality(IntEnum):
    """装备品质"""
    COMMON = 1      # 普通（白色）
    UNCOMMON = 2    # 优秀（绿色）
    RARE = 3        # 精良（蓝色）
    EPIC = 4        # 史诗（紫色）
    LEGENDARY = 5   # 传说（橙色）


QUALITY_NAMES = {
    EquipmentQuality.COMMON: "普通",
    EquipmentQuality.UNCOMMON: "优秀",
    EquipmentQuality.RARE: "精良",
    EquipmentQuality.EPIC: "史诗",
    EquipmentQuality.LEGENDARY: "传说",
}


class Equipment(Item):
    """装备类型
    
    Attributes:
        typeclass_path: 类型路径
    """
    
    typeclass_path = "src.game.typeclasses.equipment.Equipment"
    
    @property
    def item_type(self) -> ItemType:
        """物品类型"""
        return ItemType.EQUIPMENT
    
    @property
    def slot(self) -> EquipmentSlot:
        """装备槽位"""
        return EquipmentSlot(self.db.get("slot", "main_hand"))
    
    @property
    def quality(self) -> EquipmentQuality:
        """品质 1-5"""
        return EquipmentQuality(self.db.get("quality", 1))
    
    @property
    def quality_name(self) -> str:
        """品质名称"""
        return QUALITY_NAMES.get(self.quality, "未知")
    
    @property
    def stats_bonus(self) -> dict[str, int]:
        """属性加成
        
        Returns:
            {"strength": 5, "attack": 20, ...}
        """
        return self.db.get("stats_bonus", {})
    
    @property
    def durability(self) -> tuple[int, int]:
        """(当前, 最大)耐久"""
        return self.db.get("durability", (100, 100))
    
    def modify_durability(self, delta: int) -> int:
        """修改耐久度
        
        Args:
            delta: 变化值（负数为消耗）
            
        Returns:
            当前耐久度
        """
        current, max_dur = self.durability
        new_dur = max(0, min(current + delta, max_dur))
        self.db.set("durability", (new_dur, max_dur))
        return new_dur
    
    @property
    def is_broken(self) -> bool:
        """是否损坏（耐久为0）"""
        return self.durability[0] == 0
    
    @property
    def is_bound(self) -> bool:
        """是否绑定"""
        return self.db.get("is_bound", False)
    
    def bind(self) -> None:
        """绑定装备"""
        self.db.set("is_bound", True)
    
    @property
    def set_name(self) -> Optional[str]:
        """所属套装"""
        return self.db.get("set_name")
    
    @property
    def level_requirement(self) -> int:
        """等级要求"""
        return self.db.get("level_requirement", 1)
    
    @property
    def menpai_requirement(self) -> Optional[str]:
        """门派要求"""
        return self.db.get("menpai_requirement")
    
    def can_equip_by(self, character: "Character") -> tuple[bool, str]:
        """检查角色是否可以装备
        
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
        
        # 已绑定检查
        if self.is_bound:
            # TODO: 检查绑定者是否是当前角色
            pass
        
        return True, ""
    
    def get_desc(self) -> str:
        """获取装备描述"""
        desc = f"[{self.quality_name}] {self.key}\n"
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
```

## 角色装备管理 Mixin

```python
# src/game/typeclasses/equipment.py
class CharacterEquipmentMixin:
    """角色的装备管理（混入Character类）"""
    
    @property
    def equipped(self) -> dict[str, Optional[Equipment]]:
        """已装备物品
        
        Returns:
            {slot_key: Equipment or None}
        """
        return self.db.get("equipped", {})
    
    def get_equipped(self, slot: EquipmentSlot) -> Optional[Equipment]:
        """获取指定槽位装备
        
        Args:
            slot: 装备槽位
            
        Returns:
            装备对象，未装备返回None
        """
        equipped = self.equipped
        obj_id = equipped.get(slot.value)
        if obj_id:
            # TODO: 通过ObjectManager获取对象
            pass
        return None
    
    async def equip(self, item: Equipment) -> tuple[bool, str]:
        """装备物品
        
        Args:
            item: 装备物品
            
        Returns:
            (是否成功, 消息)
        """
        from .character import Character
        
        if not isinstance(self, Character):
            return False, "只有角色可以装备"
        
        # 检查是否可以装备
        can_equip, reason = item.can_equip_by(self)
        if not can_equip:
            return False, reason
        
        # 检查物品是否在背包中
        if item.location != self:
            return False, "物品不在背包中"
        
        slot = item.slot
        
        # 如果槽位已有装备，先卸下
        current = self.get_equipped(slot)
        if current:
            await self.unequip(slot)
        
        # 装备新物品
        equipped = self.equipped
        equipped[slot.value] = item.id
        self.db.set("equipped", equipped)
        
        # 绑定装备
        if not item.is_bound:
            item.bind()
        
        # 触发装备钩子
        item.at_equipped(self)
        self.at_equip(item)
        
        return True, f"装备成功：{item.key}"
    
    async def unequip(self, slot: EquipmentSlot) -> tuple[bool, str]:
        """卸下装备
        
        Args:
            slot: 装备槽位
            
        Returns:
            (是否成功, 消息)
        """
        current = self.get_equipped(slot)
        if not current:
            return False, "该槽位未装备物品"
        
        # 从装备栏移除
        equipped = self.equipped
        del equipped[slot.value]
        self.db.set("equipped", equipped)
        
        # 触发卸下钩子
        current.at_unequipped(self)
        self.at_unequip(current)
        
        return True, f"卸下成功：{current.key}"
    
    def get_total_stats(self) -> dict[str, int]:
        """计算所有装备属性总和
        
        Returns:
            属性加成总和
        """
        total = {}
        
        for slot in EquipmentSlot:
            item = self.get_equipped(slot)
            if item and not item.is_broken:
                for stat, value in item.stats_bonus.items():
                    total[stat] = total.get(stat, 0) + value
        
        return total
    
    def get_set_bonuses(self) -> dict[str, Any]:
        """计算套装效果
        
        Returns:
            套装效果
        """
        # 统计各套装件数
        set_counts = {}
        for slot in EquipmentSlot:
            item = self.get_equipped(slot)
            if item and item.set_name:
                set_counts[item.set_name] = set_counts.get(item.set_name, 0) + 1
        
        # 计算套装效果
        bonuses = {}
        # TODO: 根据套装件数计算效果
        
        return bonuses
    
    def get_attack_bonus(self) -> int:
        """获取装备提供的攻击力加成"""
        return self.get_total_stats().get("attack", 0)
    
    def get_defense_bonus(self) -> int:
        """获取装备提供的防御力加成"""
        return self.get_total_stats().get("defense", 0)
    
    # ===== 生命周期钩子 =====
    def at_equip(self, item: Equipment) -> None:
        """装备时调用"""
        pass
    
    def at_unequip(self, item: Equipment) -> None:
        """卸下时调用"""
        pass


# 装备的生命周期钩子
class EquipmentHooks:
    """装备的生命周期钩子"""
    
    def at_equipped(self, character: "Character") -> None:
        """被装备时调用"""
        pass
    
    def at_unequipped(self, character: "Character") -> None:
        """被卸下时调用"""
        pass
```

## 使用示例

```python
# 创建设备
sword = await object_manager.create(
    typeclass_path="src.game.typeclasses.equipment.Equipment",
    key="精铁长剑",
    attributes={
        "slot": "main_hand",
        "quality": 2,  # 优秀
        "stats_bonus": {"attack": 25, "strength": 3},
        "durability": (100, 100),
        "level_requirement": 5,
    }
)

# 装备物品
success, msg = await character.equip(sword)
print(msg)  # 装备成功：精铁长剑

# 查看装备
for slot in EquipmentSlot:
    item = character.get_equipped(slot)
    if item:
        print(f"{SLOT_NAMES[slot]}: {item.key}")

# 计算总属性
print(character.get_total_stats())  # {"attack": 25, "strength": 3}

# 卸下装备
success, msg = await character.unequip(EquipmentSlot.MAIN_HAND)
```
