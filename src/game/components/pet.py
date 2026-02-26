"""宠物系统组件.

使用组件模式实现的宠物系统示例。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.components import Component

if TYPE_CHECKING:
    from src.game.typeclasses.character import Character


class PetComponent(Component):
    """宠物组件.
    
    为角色添加宠物功能。
    
    Example:
        pet = PetComponent(character, "小狐狸", "fox")
        character.add_component("pet", pet)
    """
    
    def __init__(
        self,
        owner: Character,
        name: str,
        pet_type: str,
        level: int = 1,
        loyalty: int = 100
    ):
        super().__init__(owner)
        self.name = name
        self.pet_type = pet_type
        self.level = level
        self.loyalty = max(0, min(100, loyalty))
        self.exp = 0
    
    def get_stats(self) -> dict[str, int]:
        """获取宠物提供的属性加成.
        
        Returns:
            属性加成字典
        """
        # 根据宠物类型和等级提供不同加成
        base_bonus = self.level * 2
        
        pet_bonuses = {
            "fox": {"agility": base_bonus, "wuxing": self.level},
            "wolf": {"attack": base_bonus * 2, "strength": self.level},
            "tiger": {"attack": base_bonus * 3, "constitution": self.level},
            "bird": {"agility": base_bonus * 2, "fuyuan": self.level},
        }
        
        return pet_bonuses.get(self.pet_type, {"attack": base_bonus})
    
    def gain_exp(self, amount: int) -> str:
        """获得经验.
        
        Args:
            amount: 经验值
            
        Returns:
            消息
        """
        self.exp += amount
        
        # 检查升级
        required = self.level * 100
        if self.exp >= required:
            self.exp -= required
            self.level += 1
            return f"{self.name}升级了！当前等级：{self.level}"
        
        return f"{self.name}获得{amount}点经验"
    
    def change_loyalty(self, delta: int) -> None:
        """改变忠诚度.
        
        Args:
            delta: 变化值
        """
        self.loyalty = max(0, min(100, self.loyalty + delta))
    
    def get_desc(self) -> str:
        """获取宠物描述.
        
        Returns:
            描述文本
        """
        loyalty_desc = ""
        if self.loyalty >= 80:
            loyalty_desc = "非常忠诚"
        elif self.loyalty >= 50:
            loyalty_desc = "比较忠诚"
        elif self.loyalty >= 20:
            loyalty_desc = "有些疏远"
        else:
            loyalty_desc = "可能会逃跑"
        
        return (
            f"[{self.pet_type}] {self.name}\n"
            f"等级: {self.level}\n"
            f"经验: {self.exp}/{self.level * 100}\n"
            f"忠诚度: {self.loyalty}/100 ({loyalty_desc})"
        )
