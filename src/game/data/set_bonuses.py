"""套装效果配置.

定义各套装的套装效果.
套装效果根据穿戴的件数触发不同级别的加成.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class SetBonusLevel:
    """套装效果等级.
    
    Attributes:
        required_count: 触发所需件数
        description: 效果描述
        stats_bonus: 属性加成 (属性名: 加成值)
        special_effect: 特殊效果描述
    """
    required_count: int
    description: str
    stats_bonus: dict[str, int | float] | None = None
    special_effect: str | None = None


@dataclass 
class SetBonusConfig:
    """套装效果配置.
    
    Attributes:
        set_name: 套装名称
        max_pieces: 最大件数
        bonus_levels: 各等级效果列表
    """
    set_name: str
    max_pieces: int
    bonus_levels: list[SetBonusLevel]
    
    def get_bonus_for_count(self, count: int) -> SetBonusLevel | None:
        """获取指定件数触发的最高等级效果.
        
        Args:
            count: 当前穿戴件数
            
        Returns:
            最高适用等级的效果，如果没有则返回None
        """
        applicable = [b for b in self.bonus_levels if count >= b.required_count]
        if not applicable:
            return None
        # 返回最高等级（要求件数最多的）
        return max(applicable, key=lambda b: b.required_count)


# ===== 少林套装 =====
SHAOLIN_ARMOR_SET = SetBonusConfig(
    set_name="少林僧衣",
    max_pieces=4,
    bonus_levels=[
        SetBonusLevel(
            required_count=2,
            description="2件：根骨+10",
            stats_bonus={"constitution": 10}
        ),
        SetBonusLevel(
            required_count=4,
            description="4件：根骨+20，防御+15%，习得少林金钟罩",
            stats_bonus={"constitution": 20, "defense_percent": 0.15},
            special_effect="习得少林金钟罩"
        ),
    ]
)

# ===== 武当套装 =====
WUDANG_ARMOR_SET = SetBonusConfig(
    set_name="武当道袍",
    max_pieces=4,
    bonus_levels=[
        SetBonusLevel(
            required_count=2,
            description="2件：悟性+10",
            stats_bonus={"intelligence": 10}
        ),
        SetBonusLevel(
            required_count=4,
            description="4件：悟性+20，内力+20%，习得武当太极劲",
            stats_bonus={"intelligence": 20, "max_mana_percent": 0.20},
            special_effect="习得武当太极劲"
        ),
    ]
)

# ===== 华山套装 =====
HUASHAN_ARMOR_SET = SetBonusConfig(
    set_name="华山剑袍",
    max_pieces=4,
    bonus_levels=[
        SetBonusLevel(
            required_count=2,
            description="2件：身法+10",
            stats_bonus={"dexterity": 10}
        ),
        SetBonusLevel(
            required_count=4,
            description="4件：身法+20，攻击+15%，习得华山剑气",
            stats_bonus={"dexterity": 20, "attack_percent": 0.15},
            special_effect="习得华山剑气"
        ),
    ]
)

# ===== 丐帮套装 =====
GAibang_ARMOR_SET = SetBonusConfig(
    set_name="丐帮破衣",
    max_pieces=4,
    bonus_levels=[
        SetBonusLevel(
            required_count=2,
            description="2件：臂力+10",
            stats_bonus={"strength": 10}
        ),
        SetBonusLevel(
            required_count=4,
            description="4件：臂力+20，气血+20%，习得降龙十八掌",
            stats_bonus={"strength": 20, "max_hp_percent": 0.20},
            special_effect="习得降龙十八掌"
        ),
    ]
)

# ===== 全真套装 =====
QUANZHEN_ARMOR_SET = SetBonusConfig(
    set_name="全真心法袍",
    max_pieces=4,
    bonus_levels=[
        SetBonusLevel(
            required_count=2,
            description="2件：内力回复+10%",
            stats_bonus={"mana_regen": 0.10}
        ),
        SetBonusLevel(
            required_count=4,
            description="4件：内力回复+20%，全属性+5",
            stats_bonus={"mana_regen": 0.20, "all_stats": 5}
        ),
    ]
)

# ===== 古墓套装 =====
GUMU_ARMOR_SET = SetBonusConfig(
    set_name="玉女素心袍",
    max_pieces=4,
    bonus_levels=[
        SetBonusLevel(
            required_count=2,
            description="2件：轻功+10%",
            stats_bonus={"dodge_bonus": 0.10}
        ),
        SetBonusLevel(
            required_count=4,
            description="4件：轻功+20%，闪避+15%，习得玉女心经",
            stats_bonus={"dodge_bonus": 0.20, "dodge_percent": 0.15},
            special_effect="习得玉女心经"
        ),
    ]
)

# ===== 逍遥套装 =====
XIAOYAO_ARMOR_SET = SetBonusConfig(
    set_name="逍遥羽衣",
    max_pieces=4,
    bonus_levels=[
        SetBonusLevel(
            required_count=2,
            description="2件：悟性+15",
            stats_bonus={"intelligence": 15}
        ),
        SetBonusLevel(
            required_count=4,
            description="4件：悟性+30，北冥神功效果+25%",
            stats_bonus={"intelligence": 30, "special_skill_boost": 0.25},
            special_effect="北冥神功效果提升"
        ),
    ]
)

# ===== 峨眉套装 =====
EMEI_ARMOR_SET = SetBonusConfig(
    set_name="峨眉禅衣",
    max_pieces=4,
    bonus_levels=[
        SetBonusLevel(
            required_count=2,
            description="2件：内力+100",
            stats_bonus={"max_mana": 100}
        ),
        SetBonusLevel(
            required_count=4,
            description="4件：内力+200，治疗效果+20%",
            stats_bonus={"max_mana": 200, "heal_bonus": 0.20}
        ),
    ]
)

# ===== 日月套装 =====
RIYUE_ARMOR_SET = SetBonusConfig(
    set_name="日月神教服",
    max_pieces=4,
    bonus_levels=[
        SetBonusLevel(
            required_count=2,
            description="2件：攻击+10",
            stats_bonus={"attack": 10}
        ),
        SetBonusLevel(
            required_count=4,
            description="4件：攻击+25，暴击率+10%",
            stats_bonus={"attack": 25, "crit_rate": 0.10}
        ),
    ]
)

# ===== 星宿套装 =====
XIUXIU_ARMOR_SET = SetBonusConfig(
    set_name="星宿毒袍",
    max_pieces=4,
    bonus_levels=[
        SetBonusLevel(
            required_count=2,
            description="2件：毒攻+10%",
            stats_bonus={"poison_damage": 0.10}
        ),
        SetBonusLevel(
            required_count=4,
            description="4件：毒攻+25%，化功大法效果+20%",
            stats_bonus={"poison_damage": 0.25, "special_skill_boost": 0.20},
            special_effect="化功大法效果提升"
        ),
    ]
)

# ===== 江湖套装 =====
JIANGHU_LIGHT_ARMOR_SET = SetBonusConfig(
    set_name="江湖轻甲",
    max_pieces=4,
    bonus_levels=[
        SetBonusLevel(
            required_count=2,
            description="2件：身法+5，臂力+5",
            stats_bonus={"dexterity": 5, "strength": 5}
        ),
        SetBonusLevel(
            required_count=4,
            description="4件：全属性+10",
            stats_bonus={"constitution": 10, "intelligence": 10, 
                        "strength": 10, "dexterity": 10}
        ),
    ]
)

# 套装配置注册表
SET_BONUS_REGISTRY: dict[str, SetBonusConfig] = {
    "少林僧衣": SHAOLIN_ARMOR_SET,
    "武当道袍": WUDANG_ARMOR_SET,
    "华山剑袍": HUASHAN_ARMOR_SET,
    "丐帮破衣": GAibang_ARMOR_SET,
    "全真心法袍": QUANZHEN_ARMOR_SET,
    "玉女素心袍": GUMU_ARMOR_SET,
    "逍遥羽衣": XIAOYAO_ARMOR_SET,
    "峨眉禅衣": EMEI_ARMOR_SET,
    "日月神教服": RIYUE_ARMOR_SET,
    "星宿毒袍": XIUXIU_ARMOR_SET,
    "江湖轻甲": JIANGHU_LIGHT_ARMOR_SET,
}


def get_set_bonus_config(set_name: str) -> SetBonusConfig | None:
    """获取套装效果配置.
    
    Args:
        set_name: 套装名称
        
    Returns:
        套装配置，如果不存在返回None
    """
    return SET_BONUS_REGISTRY.get(set_name)


def register_set_bonus(config: SetBonusConfig) -> None:
    """注册新的套装效果.
    
    Args:
        config: 套装效果配置
    """
    SET_BONUS_REGISTRY[config.set_name] = config
