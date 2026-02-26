# Mixin 命名规范

**版本**: 1.0  
**日期**: 2026-02-25  
**适用范围**: Phase 1 Week 3-4 Mixin 方法前缀规范

---

## 规则

1. **方法前缀**: 每个 Mixin 的所有公共方法必须添加前缀
2. **前缀格式**: `{mixin_name}_`
3. **统一接口**: Character 类负责聚合各 Mixin 功能

---

## 当前 Mixin 前缀表

| Mixin | 前缀 | 示例 |
|:------|:-----|:-----|
| CharacterEquipmentMixin | `equipment_` | `equipment_get_stats` |
| CharacterWuxueMixin | `wuxue_` | `wuxue_get_available_moves` |

---

## 重命名清单

### CharacterEquipmentMixin

| 原方法名 | 新方法名 | 说明 |
|:---------|:---------|:-----|
| `_invalidate_equipment_cache` | `_equipment_invalidate_cache` | 内部方法，添加下划线前缀 |
| `equipped` (property) | `equipment_slots` (property) | 已装备物品字典 |
| `get_equipped` | `equipment_get_item` | 获取指定槽位装备 |
| `equip` | `equipment_equip` | 装备物品 |
| `unequip` | `equipment_unequip` | 卸下装备 |
| `get_total_stats` | `equipment_get_stats` | 获取所有装备属性总和 |
| `get_set_bonuses` | `equipment_get_set_bonuses` | 计算套装效果 |
| `get_total_set_stats` | `equipment_get_set_stats` | 获取套装总属性 |
| `get_set_info` | `equipment_get_set_info` | 获取套装信息列表 |
| `get_attack_bonus` | `equipment_get_attack_bonus` | 获取攻击加成 |
| `get_defense_bonus` | `equipment_get_defense_bonus` | 获取防御加成 |
| `at_equip` | `equipment_on_equip` | 装备时生命周期钩子 |
| `at_unequip` | `equipment_on_unequip` | 卸下时生命周期钩子 |

### CharacterWuxueMixin

| 原方法名 | 新方法名 | 说明 |
|:---------|:---------|:-----|
| `learned_wuxue` (property) | `wuxue_learned` (property) | 已学武功字典 |
| `learn_wuxue` | `wuxue_learn` | 学习武功 |
| `has_learned` | `wuxue_has_learned` | 检查是否已学 |
| `get_wuxue_level` | `wuxue_get_level` | 获取武功层数 |
| `practice_move` | `wuxue_practice` | 练习招式 |
| `_calculate_practice_gain` | `_wuxue_calc_practice_gain` | 内部方法 |
| `_check_wuxue_level_up` | `_wuxue_check_level_up` | 内部方法 |
| `get_available_moves` | `wuxue_get_moves` | 获取所有可用招式 |
| `get_move_mastery` | `wuxue_get_move_mastery` | 获取招式熟练度 |
| `get_total_mastery` | `wuxue_get_total_mastery` | 获取武功总熟练度 |

---

## Character 统一接口

Character 类负责提供统一的公共接口，内部调用各 Mixin 的前缀方法：

```python
class Character(...):
    # ===== 统一属性接口 =====
    
    def get_attack(self) -> int:
        """获取总攻击力（聚合所有来源）"""
        base = self.attributes.get("strength", 10) * 2
        equipment = self.equipment_get_stats().get("attack", 0)
        wuxue = self.wuxue_get_stats().get("attack", 0)  # 需要添加
        return base + equipment + wuxue
    
    def get_defense(self) -> int:
        """获取总防御力"""
        base = self.attributes.get("constitution", 10)
        equipment = self.equipment_get_stats().get("defense", 0)
        return base + equipment
    
    def get_stats(self) -> dict[str, int]:
        """获取所有属性（聚合）"""
        stats = {
            "strength": self.attributes.get("strength", 10),
            "agility": self.attributes.get("agility", 10),
            "constitution": self.attributes.get("constitution", 10),
        }
        stats.update(self.equipment_get_stats())
        # stats.update(self.wuxue_get_stats())  # 需要添加
        return stats
```

---

## 迁移检查清单

- [ ] 所有 Mixin 方法已添加前缀
- [ ] Character 类提供统一接口
- [ ] 所有调用点已更新
- [ ] 所有测试通过
