"""游戏异常定义.

定义分层的异常体系，提供详细的错误信息.
"""


class GameException(Exception):
    """游戏基础异常."""
    
    def __init__(self, message: str, *, code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details or {}


class CombatException(GameException):
    """战斗相关异常."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="COMBAT_ERROR", **kwargs)


class InvalidTargetError(CombatException):
    """无效目标错误."""
    
    def __init__(self, target=None):
        self.target = target
        super().__init__(
            "无法攻击这个目标",
            code="INVALID_TARGET",
            details={"target": str(target)}
        )


class CombatNotStartedError(CombatException):
    """战斗未开始错误."""
    
    def __init__(self):
        super().__init__("你不在战斗中", code="COMBAT_NOT_STARTED")


class ItemException(GameException):
    """物品相关异常."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="ITEM_ERROR", **kwargs)


class CannotPickupError(ItemException):
    """无法拾取错误."""
    
    def __init__(self, item, reason: str):
        self.item = item
        self.reason = reason
        super().__init__(
            f"无法拾取{item.name}: {reason}",
            code="CANNOT_PICKUP",
            details={"item_key": item.key, "reason": reason}
        )


class OverweightError(ItemException):
    """超重错误."""
    
    def __init__(self, current: int, max_weight: int, item_weight: int):
        self.current = current
        self.max_weight = max_weight
        self.item_weight = item_weight
        super().__init__(
            f"负重已满 ({current}/{max_weight})",
            code="OVERWEIGHT",
            details={
                "current": current,
                "max": max_weight,
                "item_weight": item_weight
            }
        )


class ValidationError(GameException):
    """数据验证错误."""
    
    def __init__(self, field: str, message: str):
        super().__init__(
            f"验证失败 [{field}]: {message}",
            code="VALIDATION_ERROR",
            details={"field": field}
        )


class ConfigurationError(GameException):
    """配置错误."""
    
    def __init__(self, message: str):
        super().__init__(message, code="CONFIG_ERROR")
