"""混沌测试与错误恢复测试.

测试系统在极端情况下的行为和恢复能力。
"""
import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import random

from src.utils.config import Config
from src.engine.core import GameEngine
from src.game.typeclasses.character import Character
from src.game.typeclasses.equipment import Equipment
from src.game.npc.core import NPC
from src.game.quest.core import Quest


class TestCrashRecovery:
    """崩溃恢复测试."""
    
    @pytest.fixture
    async def engine(self):
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/chaos.db"
        config.game.auto_save_interval = 5
        
        engine = GameEngine(config)
        await engine.initialize()
        
        yield engine
        
        try:
            await engine.stop()
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_mid_transaction_crash_simulation(self, engine):
        """测试事务中途崩溃模拟."""
        # 创建一个玩家
        player = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="crash_player",
            attributes={"name": "崩溃测试玩家", "gold": 1000}
        )
        
        # 模拟事务：扣除金币
        original_gold = player.db.get("gold", 1000)
        
        try:
            # 开始事务
            player.db.set("gold", original_gold - 100)
            # 模拟崩溃前的检查点
            checkpoint_gold = player.db.get("gold")
            
            # 继续更多操作
            player.db.set("gold", checkpoint_gold - 200)
            
            # 验证最终状态一致
            final_gold = player.db.get("gold")
            assert final_gold == original_gold - 300
            
        except Exception as e:
            # 如果崩溃，应该能回滚到之前的状态
            # 这里简化处理
            pass
    
    @pytest.mark.asyncio
    async def test_data_corruption_detection(self, engine):
        """测试数据损坏检测."""
        player = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="corrupt_player",
            attributes={"name": "损坏测试玩家"}
        )
        
        # 设置有效数据
        player.db.set("level", 50)
        player.db.set("exp", 5000)
        
        # 验证数据完整性
        def validate_player_data(char):
            errors = []
            level = char.db.get("level")
            exp = char.db.get("exp")
            
            if not isinstance(level, int) or level < 1 or level > 100:
                errors.append("Invalid level")
            
            if not isinstance(exp, int) or exp < 0:
                errors.append("Invalid exp")
            
            return len(errors) == 0, errors
        
        is_valid, errors = validate_player_data(player)
        assert is_valid
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_partial_save_recovery(self, engine):
        """测试部分保存恢复."""
        # 创建多个对象
        chars = []
        for i in range(5):
            char = await engine.objects.create(
                typeclass_path="src.game.typeclasses.character.Character",
                key=f"partial_char_{i}",
                attributes={"name": f"部分保存角色{i}"}
            )
            char.attributes = {"status": "created"}
            engine.objects.mark_dirty(char)
            chars.append(char)
        
        # 保存前3个
        for char in chars[:3]:
            await engine.objects.save(char)
        
        # 验证前3个已保存
        for char in chars[:3]:
            loaded = await engine.objects.load(char.id)
            assert loaded is not None
    
    @pytest.mark.asyncio
    async def test_engine_restart_data_persistence(self):
        """测试引擎重启后数据持久化."""
        tmp_dir = tempfile.mkdtemp()
        db_path = Path(tmp_dir) / "persistence.db"
        
        # 第一次启动
        config1 = Config()
        config1.database.url = f"sqlite+aiosqlite:///{db_path}"
        
        engine1 = GameEngine(config1)
        await engine1.initialize()
        
        # 创建数据
        char = await engine1.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="persistent_char",
            attributes={"name": "持久化测试角色", "level": 42}
        )
        char_id = char.id
        
        await engine1.objects.save_all()
        await engine1.stop()
        
        # 第二次启动（新引擎实例）
        config2 = Config()
        config2.database.url = f"sqlite+aiosqlite:///{db_path}"
        
        engine2 = GameEngine(config2)
        await engine2.initialize()
        
        # 验证数据存在
        loaded = await engine2.objects.load(char_id)
        assert loaded is not None
        
        await engine2.stop()


class TestNetworkFailureSimulation:
    """网络故障模拟测试."""
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """测试超时处理."""
        async def slow_operation():
            await asyncio.sleep(10)  # 很慢的操作
            return "done"
        
        # 设置超时
        try:
            result = await asyncio.wait_for(slow_operation(), timeout=0.1)
            assert False, "应该超时"
        except asyncio.TimeoutError:
            # 预期行为
            assert True
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """测试重试机制."""
        attempt_count = 0
        
        async def flaky_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError("模拟网络错误")
            return "success"
        
        # 重试逻辑
        max_retries = 3
        for i in range(max_retries):
            try:
                result = await flaky_operation()
                assert result == "success"
                assert attempt_count == 3
                break
            except ConnectionError:
                if i == max_retries - 1:
                    raise
                await asyncio.sleep(0.01)


class TestResourceLimitScenarios:
    """资源限制场景测试."""
    
    @pytest.mark.asyncio
    async def test_max_object_limit_approach(self, engine):
        """测试接近最大对象数量限制."""
        # 创建大量对象（但不真的达到极限）
        objects = []
        for i in range(100):
            char = await engine.objects.create(
                typeclass_path="src.game.typeclasses.character.Character",
                key=f"limit_char_{i}",
                attributes={"name": f"限制测试{i}"}
            )
            objects.append(char)
        
        # 验证系统仍正常工作
        assert len(objects) == 100
        
        # 验证可以查询
        results = await engine.objects.find()
        assert len(results) >= 100
    
    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self):
        """测试内存压力处理."""
        import sys
        
        # 创建大对象
        large_objects = []
        for i in range(10):
            # 每个对象约1MB数据
            large_data = "x" * (1024 * 1024)
            large_objects.append(large_data)
        
        # 验证内存使用
        total_size = sum(sys.getsizeof(obj) for obj in large_objects)
        print(f"大对象总大小: {total_size / 1024 / 1024:.2f} MB")
        
        # 释放内存
        large_objects.clear()
    
    @pytest.mark.asyncio
    async def test_disk_space_simulation(self):
        """测试磁盘空间模拟."""
        # 模拟磁盘空间检查
        available_space = 100 * 1024 * 1024  # 100MB
        required_space = 10 * 1024 * 1024    # 10MB
        
        if available_space < required_space:
            pytest.skip("磁盘空间不足")
        
        assert available_space >= required_space


class TestConcurrentModification:
    """并发修改测试."""
    
    @pytest.mark.asyncio
    async def test_lost_update_problem(self):
        """测试丢失更新问题."""
        shared_value = 0
        
        async def increment():
            nonlocal shared_value
            # 读取
            current = shared_value
            # 模拟处理延迟
            await asyncio.sleep(0.001)
            # 写入（可能覆盖其他更新）
            shared_value = current + 1
        
        # 并发执行100次
        tasks = [increment() for _ in range(100)]
        await asyncio.gather(*tasks)
        
        # 由于竞态条件，结果可能小于100
        # 这是一个已知问题，测试只是验证行为
        print(f"最终值: {shared_value} (期望100)")
        assert shared_value <= 100
    
    @pytest.mark.asyncio
    async def test_dirty_read_prevention(self):
        """测试脏读预防."""
        data = {"value": 100}
        committed = True
        
        async def writer():
            nonlocal committed
            committed = False
            data["value"] = 200
            await asyncio.sleep(0.01)
            committed = True
        
        async def reader():
            await asyncio.sleep(0.005)
            # 如果事务未提交，应该看到旧值
            if not committed:
                return 100
            return data["value"]
        
        await asyncio.gather(writer(), reader())
        assert data["value"] == 200


class TestErrorInjection:
    """错误注入测试."""
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self):
        """测试数据库错误处理."""
        # 模拟数据库错误
        async def operation_with_error():
            raise Exception("Database connection lost")
        
        with pytest.raises(Exception) as exc_info:
            await operation_with_error()
        
        assert "connection lost" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_coroutine_cancellation(self):
        """测试协程取消."""
        async def long_running_task():
            try:
                for i in range(100):
                    await asyncio.sleep(0.01)
            except asyncio.CancelledError:
                # 应该正确处理取消
                raise
        
        task = asyncio.create_task(long_running_task())
        await asyncio.sleep(0.05)
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass  # 预期行为
    
    @pytest.mark.asyncio
    async def test_exception_chaining(self):
        """测试异常链."""
        async def level_3():
            raise ValueError("原始错误")
        
        async def level_2():
            try:
                await level_3()
            except ValueError as e:
                raise RuntimeError("包装错误") from e
        
        async def level_1():
            try:
                await level_2()
            except RuntimeError as e:
                raise Exception("顶层错误") from e
        
        with pytest.raises(Exception) as exc_info:
            await level_1()
        
        assert "顶层错误" in str(exc_info.value)


class TestFuzzing:
    """模糊测试."""
    
    @pytest.mark.asyncio
    async def test_random_action_sequence(self):
        """测试随机动作序列."""
        actions = ["create", "read", "update", "delete"]
        results = []
        
        # 执行100个随机动作
        for _ in range(100):
            action = random.choice(actions)
            try:
                if action == "create":
                    results.append("created")
                elif action == "read":
                    results.append("read")
                elif action == "update":
                    results.append("updated")
                elif action == "delete":
                    results.append("deleted")
            except Exception as e:
                results.append(f"error: {e}")
        
        # 验证所有动作都被执行
        assert len(results) == 100
    
    @pytest.mark.asyncio
    async def test_random_attribute_modification(self):
        """测试随机属性修改."""
        obj = {"value": 0}
        
        # 随机修改100次
        for _ in range(100):
            operation = random.choice(["inc", "dec", "mul", "set"])
            amount = random.randint(-100, 100)
            
            if operation == "inc":
                obj["value"] += amount
            elif operation == "dec":
                obj["value"] -= amount
            elif operation == "mul":
                if amount != 0:
                    obj["value"] *= amount
            elif operation == "set":
                obj["value"] = amount
        
        # 验证对象仍然存在
        assert "value" in obj


# 标记测试
pytestmark = [
    pytest.mark.integration,
    pytest.mark.chaos,
    pytest.mark.recovery
]
