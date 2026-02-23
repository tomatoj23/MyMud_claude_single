"""输入验证工具.

提供参数验证和输入清理功能.
"""

import re
from typing import Any


class ValidationError(ValueError):
    """验证错误."""
    pass


class Validator:
    """验证器基类."""
    
    def validate(self, value: Any) -> Any:
        """验证值，返回转换后的值或抛出异常."""
        raise NotImplementedError


class LengthValidator(Validator):
    """长度验证器."""
    
    def __init__(self, min_len: int = 0, max_len: int = None):
        self.min_len = min_len
        self.max_len = max_len
    
    def validate(self, value: str) -> str:
        if not isinstance(value, str):
            raise ValidationError(f"Expected string, got {type(value).__name__}")
        
        length = len(value)
        
        if length < self.min_len:
            raise ValidationError(f"Min length {self.min_len}")
        
        if self.max_len and length > self.max_len:
            raise ValidationError(f"Max length {self.max_len}")
        
        return value


class RegexValidator(Validator):
    """正则验证器."""
    
    def __init__(self, pattern: str, message: str = None):
        self.pattern = re.compile(pattern)
        self.message = message
    
    def validate(self, value: str) -> str:
        if not self.pattern.match(value):
            raise ValidationError(self.message or f"Format error")
        return value


class RangeValidator(Validator):
    """范围验证器."""
    
    def __init__(self, min_val: int = None, max_val: int = None):
        self.min_val = min_val
        self.max_val = max_val
    
    def validate(self, value: int | float) -> int | float:
        try:
            num = float(value)
        except (TypeError, ValueError):
            raise ValidationError(f"Expected number")
        
        if self.min_val is not None and num < self.min_val:
            raise ValidationError(f"Min value {self.min_val}")
        
        if self.max_val is not None and num > self.max_val:
            raise ValidationError(f"Max value {self.max_val}")
        
        return value


# 预定义验证器
KeyValidator = RegexValidator(
    r'^[a-zA-Z_][a-zA-Z0-9_]*$',
    "Key must start with letter/underscore, contain only alphanumeric"
)

NameValidator = LengthValidator(min_len=1, max_len=50)

PositiveIntValidator = RangeValidator(min_val=1)


class InputSanitizer:
    """输入清理器."""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """清理字符串输入."""
        if not isinstance(value, str):
            value = str(value)
        
        # 移除控制字符（保留换行制表）
        value = "".join(c for c in value if c.isprintable() or c in "\n\t")
        
        return value[:max_length]
    
    @staticmethod
    def sanitize_command_args(args: str) -> str:
        """清理命令参数."""
        args = InputSanitizer.sanitize_string(args, max_length=1000)
        
        # 防止命令注入
        dangerous = [';', '&&', '||', '|', '`', '$', '<', '>']
        for char in dangerous:
            args = args.replace(char, '')
        
        return args.strip()
