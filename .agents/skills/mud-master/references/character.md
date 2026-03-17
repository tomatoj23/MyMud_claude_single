> 状态说明：
> - 阶段二已完成，当前实现以 `src/game/typeclasses/character.py` 为中心。
> - 文中 `menpai.py`、`internal_power.py` 等路径表示可选拆分蓝图；当前仓库未单独落地时，请回到 `character.py`、相关测试和调用点实现。

# Character 角色系统

## 概述

武侠角色系统，包含先天资质、后天属性、动态状态三层结构，以及门派、内力、装备、武学等子系统。

## 角色属性三层结构

```
┌─────────────────────────────────────────────┐
│  先天资质（birth_talents）                    │
│  - 根骨、悟性、福缘、容貌                       │
│  - 创建时随机，几乎不变                         │
├─────────────────────────────────────────────┤
│  后天属性（attributes）                       │
│  - 力量、敏捷、体质、精神                       │
│  - 可通过修炼提升                              │
├─────────────────────────────────────────────┤
│  动态状态（status）                           │
│  - 气血、内力、精力                           │
│  - 战斗中实时变化                              │
└─────────────────────────────────────────────┘
```

## Character 类完整实现

```python
# src/game/typeclasses/character.py
from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from src.engine.core.typeclass import TypeclassBase


class Character(TypeclassBase):
    """武侠角色类型
    
    属性结构：
    - 先天资质：birth_talents {gengu, wuxing, fuyuan, rongmao}
    - 后天属性：attributes {strength, agility, constitution, spirit}
    - 动态状态：status {hp, mp, ep}
    
    Attributes:
        typeclass_path: 类型路径
    """
    
    typeclass_path = "src.game.typeclasses.character.Character"
    
    # ===== 先天资质（创建时随机，1-30，几乎不变） =====
    @property
    def birth_talents(self) -> dict[str, int]:
        """先天资质
        
        Returns:
            {
                "gengu": 根骨 - 影响体质、气血上限,
                "wuxing": 悟性 - 影响武学领悟速度,
                "fuyuan": 福缘 - 影响奇遇概率,
                "rongmao": 容貌 - 影响NPC态度,
            }
        """
        return self.db.get("birth_talents", {
            "gengu": 15,
            "wuxing": 15,
            "fuyuan": 15,
            "rongmao": 15,
        })
    
    @birth_talents.setter
    def birth_talents(self, value: dict[str, int]) -> None:
        self.db.set("birth_talents", value)
    
    # 便捷访问
    @property
    def gengu(self) -> int:
        """根骨"""
        return self.birth_talents.get("gengu", 15)
    
    @property
    def wuxing(self) -> int:
        """悟性"""
        return self.birth_talents.get("wuxing", 15)
    
    # ===== 后天属性（可通过修炼提升） =====
    @property
    def attributes(self) -> dict[str, int]:
        """后天属性
        
        Returns:
            {
                "strength": 力量 - 影响外功伤害,
                "agility": 敏捷 - 影响闪避、命中,
                "constitution": 体质 - 影响气血上限,
                "spirit": 精神 - 影响内力上限、抗性,
            }
        """
        return self.db.get("attributes", {
            "strength": 10,
            "agility": 10,
            "constitution": 10,
            "spirit": 10,
        })
    
    @attributes.setter
    def attributes(self, value: dict[str, int]) -> None:
        self.db.set("attributes", value)
    
    # ===== 动态状态（战斗中实时变化） =====
    @property
    def status(self) -> dict[str, tuple[int, int]]:
        """动态状态 - (当前值, 最大值)
        
        Returns:
            {
                "hp": (当前气血, 最大气血),
                "mp": (当前内力, 最大内力),
                "ep": (当前精力, 最大精力),
            }
        """
        default = {
            "hp": (100, 100),
            "mp": (50, 50),
            "ep": (100, 100),
        }
        return self.db.get("status", default)
    
    @status.setter
    def status(self, value: dict[str, tuple[int, int]]) -> None:
        self.db.set("status", value)
    
    # ===== 状态访问方法 =====
    def get_hp(self) -> tuple[int, int]:
        """获取当前/最大气血"""
        return self.status.get("hp", (100, 100))
    
    def modify_hp(self, delta: int) -> int:
        """修改气血，返回实际变化值
        
        Args:
            delta: 变化值（正为治疗，负为伤害）
            
        Returns:
            实际变化值
        """
        current, max_hp = self.get_hp()
        new_hp = max(0, min(current + delta, max_hp))
        actual_delta = new_hp - current
        
        status = self.status
        status["hp"] = (new_hp, max_hp)
        self.status = status
        
        return actual_delta
    
    def get_mp(self) -> tuple[int, int]:
        """获取当前/最大内力"""
        return self.status.get("mp", (50, 50))
    
    def modify_mp(self, delta: int) -> int:
        """修改内力"""
        current, max_mp = self.get_mp()
        new_mp = max(0, min(current + delta, max_mp))
        actual_delta = new_mp - current
        
        status = self.status
        status["mp"] = (new_mp, max_mp)
        self.status = status
        
        return actual_delta
    
    # ===== 属性计算 =====
    def get_max_hp(self) -> int:
        """计算最大气血 = 基础值 + 体质*10 + 根骨*5"""
        base = 100
        from_constitution = self.attributes.get("constitution", 10) * 10
        from_gengu = self.gengu * 5
        return base + from_constitution + from_gengu
    
    def get_max_mp(self) -> int:
        """计算最大内力 = 基础值 + 精神*8 + 根骨*3"""
        base = 50
        from_spirit = self.attributes.get("spirit", 10) * 8
        from_gengu = self.gengu * 3
        return base + from_spirit + from_gengu
    
    def get_attack(self) -> int:
        """计算攻击力（基础 + 装备 + BUFF）"""
        base = self.attributes.get("strength", 10) * 2
        
        # TODO: 加上装备加成
        # equipment_bonus = self.get_equipment_attack_bonus()
        
        # TODO: 加上BUFF加成
        # buff_bonus = self.buff_manager.get_stats_modifier().get("attack", 0)
        
        return base
    
    def get_defense(self) -> int:
        """计算防御力"""
        base = self.attributes.get("constitution", 10)
        return base
    
    def get_agility(self) -> int:
        """计算敏捷（影响闪避、命中）"""
        base = self.attributes.get("agility", 10)
        return base
    
    # ===== 角色成长 =====
    @property
    def level(self) -> int:
        """等级"""
        return self.db.get("level", 1)
    
    @level.setter
    def level(self, value: int) -> None:
        self.db.set("level", value)
    
    @property
    def exp(self) -> int:
        """经验值"""
        return self.db.get("exp", 0)
    
    def add_exp(self, amount: int) -> bool:
        """增加经验，返回是否升级
        
        Args:
            amount: 经验值
            
        Returns:
            是否升级
        """
        self.db.set("exp", self.exp + amount)
        
        # 检查升级
        required = self._get_exp_for_level(self.level + 1)
        if self.exp >= required:
            self.level_up()
            return True
        return False
    
    def _get_exp_for_level(self, level: int) -> int:
        """获取升级所需经验"""
        return level * level * 100
    
    def level_up(self) -> None:
        """升级处理"""
        self.level += 1
        
        # 恢复状态
        self._recalculate_status()
        
        # 触发升级事件
        self.at_level_up()
    
    def _recalculate_status(self) -> None:
        """重新计算状态（升级或属性变化时调用）"""
        max_hp = self.get_max_hp()
        max_mp = self.get_max_mp()
        
        self.status = {
            "hp": (max_hp, max_hp),  # 满血
            "mp": (max_mp, max_mp),  # 满蓝
            "ep": (100, 100),
        }
    
    # ===== 生命周期钩子 =====
    def at_level_up(self) -> None:
        """升级时调用（子类可重写）"""
        pass
    
    def at_death(self) -> None:
        """死亡时调用"""
        # 扣除经验
        exp_loss = self.exp // 10
        self.db.set("exp", max(0, self.exp - exp_loss))
        
        # 恢复状态
        self._recalculate_status()
```

## 门派系统 Mixin

```python
# planned split: src/game/typeclasses/menpai.py
# current repo anchor: src/game/typeclasses/character.py
class Menpai:
    """门派定义"""
    
    key: str              # 门派名
    name: str             # 显示名
    desc: str             # 门派描述
    location_id: int      # 门派驻地房间ID
    
    # 入门条件
    requirements: dict    # {min_gengu: 15, max_good_evil: -100, ...}
    
    # 武学路线
    wuxue_list: list[str]  # 可学武功列表
    
    # 门派特色
    special_bonus: dict   # 属性加成


class CharacterMenpaiMixin:
    """角色的门派相关方法（通过多继承混入Character）"""
    
    @property
    def menpai(self) -> Optional[str]:
        """当前门派"""
        return self.db.get("menpai")
    
    @menpai.setter
    def menpai(self, value: Optional[str]) -> None:
        self.db.set("menpai", value)
    
    @property
    def menpai_contrib(self) -> int:
        """门派贡献"""
        return self.db.get("menpai_contrib", 0)
    
    @property
    def menpai_position(self) -> str:
        """门派职位"""
        return self.db.get("menpai_position", "弟子")
    
    async def join_menpai(self, menpai: Menpai) -> bool:
        """加入门派（检查条件）
        
        Args:
            menpai: 门派对象
            
        Returns:
            是否成功加入
        """
        # 检查条件
        reqs = menpai.requirements
        
        if "min_gengu" in reqs:
            if self.gengu < reqs["min_gengu"]:
                return False
        
        if "max_good_evil" in reqs:
            # TODO: 检查善恶值
            pass
        
        # 设置门派
        self.menpai = menpai.key
        return True
    
    async def leave_menpai(self) -> bool:
        """离开/叛师（可能有惩罚）
        
        Returns:
            是否成功离开
        """
        if not self.menpai:
            return False
        
        # TODO: 叛师惩罚
        # 扣除大量贡献、降低属性等
        
        self.menpai = None
        self.menpai_contrib = 0
        self.menpai_position = "弟子"
        
        return True
    
    def add_contrib(self, amount: int, reason: str = "") -> None:
        """增加门派贡献"""
        self.db.set("menpai_contrib", self.menpai_contrib + amount)
```

## 内力系统 Mixin

```python
# planned split: src/game/typeclasses/internal_power.py
# current repo anchor: src/game/typeclasses/character.py
from enum import Enum


class InternalType(Enum):
    """内力属性"""
    YIN = "yin"           # 阴
    YANG = "yang"         # 阳
    GANG = "gang"         # 刚
    ROU = "rou"           # 柔
    NEUTRAL = "neutral"   # 中性


class Meridian:
    """经脉节点"""
    
    key: str              # 经脉名（如"手太阴肺经"）
    name: str             # 显示名
    xuewei: list[str]     # 穴位列表
    is_opened: bool = False
    
    # 冲穴条件
    requirements: dict    # {min_mp: 100, min_level: 30}
    
    # 效果
    effects: dict         # 冲开后属性加成


class CharacterInternalPowerMixin:
    """角色的内力系统"""
    
    @property
    def internal_type(self) -> str:
        """内力属性 - 阴/阳/刚/柔"""
        return self.db.get("internal_type", "neutral")
    
    @internal_type.setter
    def internal_type(self, value: str) -> None:
        self.db.set("internal_type", value)
    
    @property
    def dantian_capacity(self) -> int:
        """丹田容量"""
        return self.get_max_mp() * 2
    
    @property
    def meridians(self) -> dict[str, dict]:
        """经脉状态"""
        return self.db.get("meridians", {})
    
    async def open_meridian(self, meridian_key: str) -> tuple[bool, str]:
        """冲开经脉（可能失败）
        
        Args:
            meridian_key: 经脉key
            
        Returns:
            (是否成功, 消息)
        """
        if meridian_key in self.meridians:
            return False, "该经脉已冲开"
        
        # TODO: 检查冲穴条件
        # TODO: 计算成功率
        # TODO: 扣除内力
        
        # 记录已冲开
        meridians = self.meridians
        meridians[meridian_key] = {"opened_at": "timestamp"}
        self.db.set("meridians", meridians)
        
        return True, "冲穴成功！"
    
    def get_deviation_risk(self) -> float:
        """计算走火入魔风险（0-1）
        
        Returns:
            风险值
        """
        # TODO: 根据内力属性不匹配度、冲穴数量计算
        return 0.0
```

## 使用示例

```python
# 创建角色
character = await object_manager.create(
    typeclass_path="src.game.typeclasses.character.Character",
    key="张三",
    attributes={
        "birth_talents": {"gengu": 20, "wuxing": 18, "fuyuan": 15, "rongmao": 12},
        "attributes": {"strength": 12, "agility": 10, "constitution": 14, "spirit": 11},
        "menpai": "少林",
        "level": 1,
    }
)

# 访问属性
print(character.gengu)  # 20
print(character.get_max_hp())  # 100 + 14*10 + 20*5 = 340

# 修改状态
character.modify_hp(-50)  # 受伤
character.modify_hp(30)   # 治疗

# 门派操作
menpai = Menpai(key="少林", name="少林寺", ...)
await character.join_menpai(menpai)
print(character.menpai)  # "少林"
```



