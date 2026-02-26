"""状态验证模块测试."""

import pytest
from unittest.mock import MagicMock

from src.game.typeclasses.validation import (
    ValidationError,
    StateValidator,
    CharacterValidator,
)


class TestValidationError:
    """测试验证错误类"""
    
    def test_error_creation(self):
        """测试错误对象创建"""
        error = ValidationError(
            field="hp",
            message="HP为负数",
            current_value=-10,
            expected_range="0-100"
        )
        assert error.field == "hp"
        assert error.message == "HP为负数"
        assert error.current_value == -10
        assert error.expected_range == "0-100"


class TestStateValidator:
    """测试状态验证器基类"""
    
    def test_validator_init(self):
        """测试验证器初始化"""
        validator = StateValidator()
        assert validator._rules == []
    
    def test_add_rule(self):
        """测试添加规则"""
        validator = StateValidator()
        validator.add_rule("hp", lambda v: v >= 0, "HP不能为负")
        assert len(validator._rules) == 1
        assert validator._rules[0][0] == "hp"
    
    def test_validate_no_errors(self):
        """测试验证通过"""
        validator = StateValidator()
        validator.add_rule("hp", lambda v: v >= 0, "HP不能为负")
        
        obj = MagicMock()
        obj.hp = 100
        
        errors = validator.validate(obj)
        assert len(errors) == 0
    
    def test_validate_with_errors(self):
        """测试验证失败"""
        validator = StateValidator()
        validator.add_rule("hp", lambda v: v >= 0, "HP不能为负")
        
        obj = MagicMock()
        obj.hp = -10
        
        errors = validator.validate(obj)
        assert len(errors) == 1
        assert errors[0].field == "hp"
        assert errors[0].message == "HP不能为负"


class TestCharacterValidator:
    """测试角色状态验证器"""
    
    def test_validator_init(self):
        """测试验证器初始化"""
        validator = CharacterValidator()
        assert len(validator._rules) >= 5  # HP, MP, EP, level, exp
    
    def test_validate_valid_state(self):
        """测试有效状态验证"""
        validator = CharacterValidator()
        
        char = MagicMock()
        char.hp = 100
        char.mp = 50
        char.ep = 50
        char.level = 10
        char.exp = 1000
        char.max_hp = 100
        char.max_mp = 50
        char.max_ep = 50
        
        errors = validator.validate(char)
        assert len(errors) == 0
    
    def test_validate_negative_hp(self):
        """测试HP为负"""
        validator = CharacterValidator()
        
        char = MagicMock()
        char.hp = -10
        char.mp = 50
        char.ep = 50
        char.level = 10
        char.exp = 1000
        
        errors = validator.validate(char)
        assert any(e.field == "hp" for e in errors)
    
    def test_validate_hp_exceeds_max(self):
        """测试HP超过上限"""
        validator = CharacterValidator()
        
        char = MagicMock()
        char.hp = 150
        char.mp = 50
        char.ep = 50
        char.level = 10
        char.exp = 1000
        char.max_hp = 100
        char.max_mp = 50
        char.max_ep = 50
        
        errors = validator.validate(char)
        assert any(e.field == "hp" and "超过上限" in e.message for e in errors)
    
    def test_validate_negative_mp(self):
        """测试MP为负"""
        validator = CharacterValidator()
        
        char = MagicMock()
        char.hp = 100
        char.mp = -10
        char.ep = 50
        char.level = 10
        char.exp = 1000
        
        errors = validator.validate(char)
        assert any(e.field == "mp" for e in errors)
    
    def test_validate_level_too_low(self):
        """测试等级过低"""
        validator = CharacterValidator()
        
        char = MagicMock()
        char.hp = 100
        char.mp = 50
        char.ep = 50
        char.level = 0
        char.exp = 1000
        
        errors = validator.validate(char)
        assert any(e.field == "level" for e in errors)
    
    def test_validate_level_too_high(self):
        """测试等级过高"""
        validator = CharacterValidator()
        
        char = MagicMock()
        char.hp = 100
        char.mp = 50
        char.ep = 50
        char.level = 1001
        char.exp = 1000
        
        errors = validator.validate(char)
        assert any(e.field == "level" for e in errors)
    
    def test_fix_negative_hp(self):
        """测试修复负HP"""
        validator = CharacterValidator()
        
        char = MagicMock()
        char.hp = -10
        char.max_hp = 100
        
        fixes = validator.fix(char)
        assert char.hp == 0
        assert any("HP" in f for f in fixes)
    
    def test_fix_hp_exceeds_max(self):
        """测试修复HP超过上限"""
        validator = CharacterValidator()
        
        char = MagicMock()
        char.hp = 150
        char.max_hp = 100
        
        fixes = validator.fix(char)
        assert char.hp == 100
        assert any("上限" in f for f in fixes)
    
    def test_fix_level_too_low(self):
        """测试修复等级过低"""
        validator = CharacterValidator()
        
        char = MagicMock()
        char.level = 0
        
        fixes = validator.fix(char)
        assert char.level == 1
        assert any("等级" in f for f in fixes)


class TestCharacterValidationIntegration:
    """角色验证集成测试"""
    
    def test_character_validate_state_method(self):
        """测试角色的validate_state方法"""
        from src.game.typeclasses.character import Character
        
        char = MagicMock(spec=Character)
        char.hp = -10
        char.mp = 50
        char.ep = 50
        char.level = 10
        char.exp = 1000
        char.max_hp = 100
        char.max_mp = 50
        char.max_ep = 50
        
        # 手动设置验证器（因为MagicMock不会调用__init__）
        char._validator = CharacterValidator()
        char.validate_state = lambda: [
            f"[{e.field}] {e.message}: 当前={e.current_value}"
            for e in char._validator.validate(char)
        ]
        
        errors = char.validate_state()
        assert len(errors) >= 1
        assert any("HP" in e for e in errors)
    
    def test_character_fix_state_method(self):
        """测试角色的fix_state方法"""
        from src.game.typeclasses.character import Character
        
        char = MagicMock(spec=Character)
        char.hp = -10
        char.max_hp = 100
        char.mp = -5
        char.max_mp = 50
        char.ep = 50
        char.level = 10
        char.exp = 1000
        
        char._validator = CharacterValidator()
        char.fix_state = lambda: char._validator.fix(char)
        
        fixes = char.fix_state()
        assert char.hp == 0
        assert char.mp == 0
        assert len(fixes) >= 2
