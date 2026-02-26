"""战斗事务保护模块测试."""

import pytest
from unittest.mock import MagicMock, patch

from src.game.combat.transaction import CombatTransaction, TransactionManager, StateSnapshot


class TestStateSnapshot:
    """测试状态快照"""
    
    def test_snapshot_creation(self):
        """测试快照创建"""
        snapshot = StateSnapshot(
            obj_id=12345,
            attributes={'hp': 100, 'mp': 50}
        )
        assert snapshot.obj_id == 12345
        assert snapshot.attributes == {'hp': 100, 'mp': 50}


class TestCombatTransaction:
    """测试战斗事务"""
    
    def test_transaction_init(self):
        """测试事务初始化"""
        txn = CombatTransaction()
        assert txn._snapshots == {}
        assert txn._object_refs == {}
        assert not txn.is_committed()
        assert not txn.is_rolled_back()
    
    def test_snapshot_and_rollback(self):
        """测试快照和回滚"""
        obj = MagicMock()
        obj.hp = 100
        obj.mp = 50
        
        txn = CombatTransaction()
        txn.snapshot(obj, ['hp', 'mp'])
        
        # 修改对象
        obj.hp = 50
        obj.mp = 20
        
        # 回滚
        txn.rollback()
        
        # 验证恢复
        assert obj.hp == 100
        assert obj.mp == 50
        assert txn.is_rolled_back()
    
    def test_snapshot_only_records_once(self):
        """测试同一对象只记录一次快照"""
        obj = MagicMock()
        obj.hp = 100
        
        txn = CombatTransaction()
        txn.snapshot(obj, ['hp'])
        obj.hp = 80  # 修改后再次快照
        txn.snapshot(obj, ['hp'])  # 应该被忽略
        
        obj.hp = 50
        txn.rollback()
        
        # 应该恢复到第一次快照的值
        assert obj.hp == 100
    
    def test_commit_clears_snapshot(self):
        """测试提交后清除快照"""
        obj = MagicMock()
        obj.hp = 100
        
        txn = CombatTransaction()
        txn.snapshot(obj, ['hp'])
        
        obj.hp = 50
        txn.commit()
        
        # 提交后快照已清除，回滚无效
        txn.rollback()
        assert obj.hp == 50  # 未恢复
        assert txn.is_committed()
    
    def test_auto_rollback_on_exception(self):
        """测试异常时自动回滚"""
        obj = MagicMock()
        obj.hp = 100
        
        txn = CombatTransaction()
        
        try:
            with txn.auto_rollback():
                txn.snapshot(obj, ['hp'])
                obj.hp = 50
                raise ValueError("模拟异常")
        except ValueError:
            pass
        
        # 验证已回滚
        assert obj.hp == 100
        assert txn.is_rolled_back()
    
    def test_auto_commit_without_exception(self):
        """测试无异常时自动提交"""
        obj = MagicMock()
        obj.hp = 100
        
        txn = CombatTransaction()
        
        with txn.auto_rollback():
            txn.snapshot(obj, ['hp'])
            obj.hp = 50
        
        # 验证未回滚，修改保留
        assert obj.hp == 50
        assert txn.is_committed()
    
    def test_snapshot_with_none_attributes(self):
        """测试自动检测属性"""
        obj = MagicMock()
        obj.hp = 100
        obj.mp = 50
        obj.ep = 30
        obj.status = 'normal'
        obj.other = 'ignored'  # 不在默认列表中
        
        txn = CombatTransaction()
        txn.snapshot(obj)  # 不指定attributes
        
        obj.hp = 0
        obj.mp = 0
        obj.ep = 0
        obj.status = 'dead'
        
        txn.rollback()
        
        # 默认属性应该恢复
        assert obj.hp == 100
        assert obj.mp == 50
        assert obj.ep == 30
        assert obj.status == 'normal'
    
    def test_rollback_with_missing_object(self):
        """测试对象被删除时的回滚"""
        obj = MagicMock()
        obj.hp = 100
        
        txn = CombatTransaction()
        txn.snapshot(obj, ['hp'])
        
        # 删除对象引用
        del obj
        import gc
        gc.collect()
        
        # 回滚不应报错
        txn.rollback()  # 应该正常完成
    
    def test_rollback_with_unsettable_attribute(self):
        """测试无法设置的属性回滚"""
        class ReadOnlyAttr:
            def __init__(self):
                self._hp = 100
            
            @property
            def hp(self):
                return self._hp
        
        obj = ReadOnlyAttr()
        
        txn = CombatTransaction()
        txn.snapshot(obj, ['hp'])
        
        # 回滚应该处理异常
        with patch('src.game.combat.transaction.logger') as mock_logger:
            txn.rollback()
            mock_logger.warning.assert_called_once()


class TestTransactionManager:
    """测试事务管理器"""
    
    def test_manager_init(self):
        """测试管理器初始化"""
        manager = TransactionManager()
        assert manager.get_active_count() == 0
    
    def test_begin_creates_transaction(self):
        """测试begin创建事务"""
        manager = TransactionManager()
        
        with manager.begin() as txn:
            assert isinstance(txn, CombatTransaction)
            assert manager.get_active_count() == 1
        
        # 退出后事务移除
        assert manager.get_active_count() == 0
    
    def test_begin_auto_commit(self):
        """测试begin自动提交"""
        manager = TransactionManager()
        obj = MagicMock()
        obj.hp = 100
        
        with manager.begin() as txn:
            txn.snapshot(obj, ['hp'])
            obj.hp = 50
        
        # 修改应该保留（已提交）
        assert obj.hp == 50
        assert txn.is_committed()
    
    def test_begin_auto_rollback_on_exception(self):
        """测试begin异常时自动回滚"""
        manager = TransactionManager()
        obj = MagicMock()
        obj.hp = 100
        
        try:
            with manager.begin() as txn:
                txn.snapshot(obj, ['hp'])
                obj.hp = 50
                raise RuntimeError("测试异常")
        except RuntimeError:
            pass
        
        # 应该回滚
        assert obj.hp == 100
        assert txn.is_rolled_back()
        assert manager.get_active_count() == 0
    
    def test_nested_transactions(self):
        """测试嵌套事务"""
        manager = TransactionManager()
        obj = MagicMock()
        obj.hp = 100
        
        with manager.begin() as txn1:
            txn1.snapshot(obj, ['hp'])
            obj.hp = 80
            
            with manager.begin() as txn2:
                txn2.snapshot(obj, ['hp'])
                obj.hp = 50
            
            # txn2已提交，hp=50
            assert obj.hp == 50
        
        # 两个事务都提交了
        assert manager.get_active_count() == 0
        assert obj.hp == 50  # 最终值


class TestTransactionIntegration:
    """事务集成测试"""
    
    @pytest.mark.asyncio
    async def test_transaction_in_combat_scenario(self):
        """测试战斗场景中的事务使用"""
        attacker = MagicMock()
        attacker.hp = 100
        attacker.mp = 50
        
        defender = MagicMock()
        defender.hp = 100
        
        manager = TransactionManager()
        
        # 模拟一次攻击
        with manager.begin() as txn:
            # 记录快照
            txn.snapshot(attacker, ['mp'])
            txn.snapshot(defender, ['hp'])
            
            # 执行攻击
            damage = 20
            mp_cost = 10
            
            defender.hp -= damage
            attacker.mp -= mp_cost
            
            # 提交
            txn.commit()
        
        # 验证结果
        assert defender.hp == 80
        assert attacker.mp == 40
    
    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self):
        """测试战斗异常时回滚"""
        attacker = MagicMock()
        attacker.hp = 100
        attacker.mp = 50
        
        defender = MagicMock()
        defender.hp = 100
        
        manager = TransactionManager()
        
        try:
            with manager.begin() as txn:
                txn.snapshot(attacker, ['mp'])
                txn.snapshot(defender, ['hp'])
                
                # 先执行部分操作
                defender.hp -= 20
                attacker.mp -= 10
                
                # 模拟后续操作失败
                raise RuntimeError("战斗结算异常")
        except RuntimeError:
            pass
        
        # 验证回滚
        assert defender.hp == 100  # 恢复
        assert attacker.mp == 50  # 恢复
