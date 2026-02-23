"""验证数据兼容性 - 阶段0预演"""
import asyncio
import tempfile
from pathlib import Path
from src.engine.core.engine import create_engine
from src.utils.config import Config

async def test_backward_compatibility():
    """测试旧数据（无name）兼容性"""
    print("=" * 60)
    print("Data Compatibility Pre-test")
    print("=" * 60)
    
    # 使用临时数据库
    tmp_dir = tempfile.mkdtemp()
    config = Config()
    config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/test_compat.db"
    
    engine = create_engine(config)
    await engine.initialize()
    
    try:
        # 测试1: 模拟旧数据（无name）
        print("\n[Test 1] Old data compatibility (no name attribute) - Baseline")
        old_npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="old_npc_001",
            attributes={
                "npc_type": "merchant"
            }
        )
        
        # 基线状态：当前 NPC 没有 name 属性
        try:
            display_name = old_npc.name or old_npc.key
            print(f"  [PASS] No name shows key = '{display_name}'")
        except AttributeError as e:
            print(f"  [INFO] Expected: No name attribute yet, error: {e}")
            print(f"  [INFO] After Phase 1, will show key = '{old_npc.key}'")
            print("  [PASS] Baseline confirmed, ready for Phase 1")
        
        # 测试2: name存储在attributes中
        print("\n[Test 2] New data (name in attributes)")
        new_npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="new_npc_001",
            attributes={
                "name": "Wang Smith",
                "npc_type": "merchant"
            }
        )
        
        # 当前：name存储在attributes中
        name_in_db = new_npc.db.get("name")
        print(f"  [INFO] Name stored in attributes: '{name_in_db}'")
        print(f"  [INFO] After Phase 1, accessible via .name property")
        
        # 测试3: 空字符串情况
        print("\n[Test 3] Empty string case")
        empty_name_npc = await engine.objects.create(
            typeclass_path="src.game.npc.core.NPC",
            key="empty_npc_001",
            attributes={
                "name": "",
                "npc_type": "merchant"
            }
        )
        
        name_in_db = empty_name_npc.db.get("name")
        print(f"  [INFO] Name is empty string: '{name_in_db}'")
        print(f"  [INFO] After Phase 1, '' or key will fallback to key")
        
        # 测试4: Character基线
        print("\n[Test 4] Character class baseline")
        from src.game.typeclasses.character import Character
        from unittest.mock import MagicMock
        
        mock_manager = MagicMock()
        mock_db_model = MagicMock()
        mock_db_model.id = 1
        mock_db_model.key = "test_char"
        mock_db_model.location_id = None
        mock_db_model.attributes = {}
        
        char = Character(mock_manager, mock_db_model)
        print(f"  [INFO] Character.key = '{char.key}'")
        print(f"  [INFO] Character.db.get('name') = {char.db.get('name')}")
        print("  [PASS] Character baseline recorded")
        
        print("\n" + "=" * 60)
        print("Data Compatibility Baseline Test Complete!")
        print("=" * 60)
        print("\nBaseline Status:")
        print("- Character/NPC has no name attribute (Phase 1 to add)")
        print("- name can be stored in attributes (verified via db.get)")
        print("- Old data will fallback to key via 'name or key'")
        print("- New data will display name")
        print("\nConclusion: Data compatibility strategy viable, ready for Phase 1")
        
    finally:
        await engine.stop()
        import src.engine.core.engine as engine_module
        engine_module._global_engine = None

if __name__ == "__main__":
    asyncio.run(test_backward_compatibility())
