"""组件系统测试."""

import pytest
from unittest.mock import MagicMock

from src.engine.components import Component, ComponentMixin


class MockComponent(Component):
    """测试用组件."""
    
    def __init__(self, owner, stats=None):
        super().__init__(owner)
        self._stats = stats or {}
        self.attached = False
        self.detached = False
    
    def get_stats(self):
        return self._stats
    
    def on_attach(self):
        self.attached = True
    
    def on_detach(self):
        self.detached = True


class TestComponent:
    """测试组件基类."""
    
    def test_component_init(self):
        """测试组件初始化."""
        owner = MagicMock()
        comp = MockComponent(owner, {"attack": 10})
        
        assert comp.owner == owner
        assert comp.get_stats() == {"attack": 10}


class TestComponentMixin:
    """测试组件混入类."""
    
    def test_add_component(self):
        """测试添加组件."""
        mixin = ComponentMixin()
        comp = MockComponent(None)
        
        mixin.add_component("test", comp)
        
        assert mixin.has_component("test")
        assert comp.attached is True
    
    def test_get_component(self):
        """测试获取组件."""
        mixin = ComponentMixin()
        comp = MockComponent(None)
        
        mixin.add_component("test", comp)
        got = mixin.get_component("test")
        
        assert got == comp
    
    def test_get_nonexistent_component(self):
        """测试获取不存在的组件."""
        mixin = ComponentMixin()
        
        got = mixin.get_component("nonexistent")
        
        assert got is None
    
    def test_remove_component(self):
        """测试移除组件."""
        mixin = ComponentMixin()
        comp = MockComponent(None)
        
        mixin.add_component("test", comp)
        removed = mixin.remove_component("test")
        
        assert removed == comp
        assert comp.detached is True
        assert not mixin.has_component("test")
    
    def test_aggregate_stats(self):
        """测试聚合属性."""
        mixin = ComponentMixin()
        
        comp1 = MockComponent(None, {"attack": 10, "defense": 5})
        comp2 = MockComponent(None, {"attack": 5, "hp": 100})
        
        mixin.add_component("comp1", comp1)
        mixin.add_component("comp2", comp2)
        
        stats = mixin.aggregate_stats()
        
        # 后面的覆盖前面的
        assert stats["attack"] == 5
        assert stats["defense"] == 5
        assert stats["hp"] == 100


class TestPetComponent:
    """测试宠物组件."""
    
    def test_pet_init(self):
        """测试宠物初始化."""
        from src.game.components.pet import PetComponent
        
        owner = MagicMock()
        pet = PetComponent(owner, "小白", "fox", level=5, loyalty=80)
        
        assert pet.name == "小白"
        assert pet.pet_type == "fox"
        assert pet.level == 5
        assert pet.loyalty == 80
    
    def test_pet_get_stats_fox(self):
        """测试狐狸属性加成."""
        from src.game.components.pet import PetComponent
        
        owner = MagicMock()
        pet = PetComponent(owner, "小白", "fox", level=5)
        
        stats = pet.get_stats()
        
        assert stats["agility"] == 10  # level * 2
        assert stats["wuxing"] == 5    # level
    
    def test_pet_gain_exp_level_up(self):
        """测试宠物升级."""
        from src.game.components.pet import PetComponent
        
        owner = MagicMock()
        pet = PetComponent(owner, "小白", "fox", level=1)
        pet.exp = 90
        
        msg = pet.gain_exp(20)  # 超过100，应该升级
        
        assert pet.level == 2
        assert "升级" in msg
    
    def test_pet_loyalty_change(self):
        """测试忠诚度变化."""
        from src.game.components.pet import PetComponent
        
        owner = MagicMock()
        pet = PetComponent(owner, "小白", "fox", loyalty=80)
        
        pet.change_loyalty(-10)
        assert pet.loyalty == 70
        
        pet.change_loyalty(50)  # 超过100，应该限制
        assert pet.loyalty == 100
    
    def test_pet_desc(self):
        """测试宠物描述."""
        from src.game.components.pet import PetComponent
        
        owner = MagicMock()
        pet = PetComponent(owner, "小白", "fox", level=5, loyalty=90)
        
        desc = pet.get_desc()
        
        assert "小白" in desc
        assert "等级: 5" in desc
        assert "非常忠诚" in desc
