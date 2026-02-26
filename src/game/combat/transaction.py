"""战斗事务保护模块.

提供战斗操作的事务保护，支持回滚机制。
"""

from __future__ import annotations

import copy
import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .core import Combatant


logger = logging.getLogger(__name__)


@dataclass
class StateSnapshot:
    """状态快照"""
    obj_id: int
    attributes: dict[str, Any]


@dataclass
class TransactionLog:
    """事务日志"""
    snapshots: list[StateSnapshot] = field(default_factory=list)
    operations: list[str] = field(default_factory=list)
    committed: bool = False
    rolled_back: bool = False


class CombatTransaction:
    """战斗事务.
    
    支持快照、回滚、部分失败处理。
    
    使用示例:
        with session.transaction() as txn:
            target.hp -= damage
            attacker.mp -= cost
            txn.commit()  # 明确提交
    """
    
    def __init__(self):
        self._log = TransactionLog()
        self._snapshots: dict[int, dict[str, Any]] = {}
        self._object_refs: dict[int, Any] = {}  # 保存对象引用以便回滚
    
    def snapshot(self, obj: Any, attributes: list[str] | None = None):
        """记录对象状态快照.
        
        Args:
            obj: 要快照的对象
            attributes: 要记录的属性列表，None表示自动检测关键属性
        """
        obj_id = id(obj)
        if obj_id in self._snapshots:
            return  # 已记录过
        
        if attributes is None:
            # 自动检测关键属性
            attributes = ['hp', 'mp', 'ep', 'status']
        
        snapshot = {}
        for attr in attributes:
            if hasattr(obj, attr):
                value = getattr(obj, attr)
                # 深拷贝防止引用问题
                try:
                    snapshot[attr] = copy.deepcopy(value)
                except (TypeError, copy.Error):
                    snapshot[attr] = value
        
        self._snapshots[obj_id] = snapshot
        self._object_refs[obj_id] = obj  # 保存引用
        self._log.snapshots.append(StateSnapshot(obj_id, snapshot))
        logger.debug(f"Snapshot recorded for {type(obj).__name__}({obj_id}): {list(snapshot.keys())}")
    
    def commit(self):
        """提交事务，清除快照"""
        self._log.committed = True
        self._snapshots.clear()
        self._object_refs.clear()
        logger.debug("Transaction committed")
    
    def rollback(self):
        """回滚到快照状态"""
        rollback_count = 0
        for obj_id, snapshot in self._snapshots.items():
            obj = self._object_refs.get(obj_id)
            if obj:
                for attr, value in snapshot.items():
                    try:
                        setattr(obj, attr, value)
                        rollback_count += 1
                    except AttributeError as e:
                        logger.warning(f"Failed to rollback {attr} on {type(obj).__name__}: {e}")
        
        self._log.rolled_back = True
        self._snapshots.clear()
        self._object_refs.clear()
        logger.info(f"Transaction rolled back, {rollback_count} attributes restored")
    
    @contextmanager
    def auto_rollback(self):
        """自动回滚上下文管理器.
        
        使用示例:
            with txn.auto_rollback():
                txn.snapshot(obj, ['hp'])
                obj.hp -= damage
                # 如果抛出异常，自动回滚
        """
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise
    
    def is_committed(self) -> bool:
        """检查事务是否已提交"""
        return self._log.committed
    
    def is_rolled_back(self) -> bool:
        """检查事务是否已回滚"""
        return self._log.rolled_back


class TransactionManager:
    """事务管理器"""
    
    def __init__(self):
        self._active_transactions: list[CombatTransaction] = []
    
    @contextmanager
    def begin(self):
        """开始新事务.
        
        使用示例:
            with manager.begin() as txn:
                txn.snapshot(obj, ['hp'])
                obj.hp -= damage
                # 正常退出时自动提交
        """
        txn = CombatTransaction()
        self._active_transactions.append(txn)
        try:
            yield txn
            # 如果未手动提交且未回滚，自动提交
            if not txn._log.committed and not txn._log.rolled_back:
                txn.commit()
        except Exception:
            txn.rollback()
            raise
        finally:
            self._active_transactions.remove(txn)
    
    def get_active_count(self) -> int:
        """获取当前活动事务数量"""
        return len(self._active_transactions)
