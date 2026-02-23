"""数据迁移与兼容性测试.

测试不同版本间的数据迁移、格式转换、向后兼容性。
"""
import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from datetime import datetime

from src.utils.config import Config
from src.engine.core import GameEngine
from src.game.typeclasses.character import Character
from src.game.typeclasses.equipment import Equipment
from src.game.npc.core import NPC, NPCType


class TestDatabaseSchemaEvolution:
    """数据库模式演进测试."""
    
    @pytest.fixture
    async def engine_v1(self):
        """模拟旧版本引擎."""
        tmp_dir = tempfile.mkdtemp()
        config = Config()
        config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/migration_v1.db"
        
        engine = GameEngine(config)
        await engine.initialize()
        
        yield engine, tmp_dir
        
        try:
            await engine.stop()
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_add_new_field_to_existing_objects(self, engine_v1):
        """测试向现有对象添加新字段."""
        engine, tmp_dir = engine_v1
        
        # 创建旧版本数据（缺少某些新字段）
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="migration_char",
            attributes={
                "name": "迁移测试角色",
                "level": 50,
                # 缺少新字段：reputation, title, faction
            }
        )
        
        # 模拟迁移：添加新字段的默认值
        char.db.set("reputation", 0)
        char.db.set("title", "")
        char.db.set("faction", None)
        
        # 验证迁移成功
        assert char.db.get("reputation") == 0
        assert char.db.get("title") == ""
        assert char.db.get("faction") is None
        
        # 旧字段仍然有效
        assert char.db.get("name") == "迁移测试角色"
    
    @pytest.mark.asyncio
    async def test_rename_field_migration(self, engine_v1):
        """测试字段重命名迁移."""
        engine, tmp_dir = engine_v1
        
        # 使用旧字段名创建数据
        char = await engine.objects.create(
            typeclass_path="src.game.typeclasses.character.Character",
            key="rename_char",
            attributes={
                "name": "重命名字段测试",
                "hp": 100,  # 旧名称
            }
        )
        
        # 模拟迁移：复制旧字段到新字段
        old_hp = char.db.get("hp")
        char.db.set("current_hp", old_hp)
        char.db.set("max_hp", old_hp)
        
        # 可选：删除旧字段
        # char.db.delete("hp")
        
        # 验证新字段存在
        assert char.db.get("current_hp") == 100
        assert char.db.get("max_hp") == 100


class TestDataFormatConversion:
    """数据格式转换测试."""
    
    @pytest.mark.asyncio
    async def test_list_to_dict_conversion(self):
        """测试列表到字典的格式转换."""
        # 旧格式：简单列表
        old_format = [
            {"name": "任务1", "completed": True},
            {"name": "任务2", "completed": False},
        ]
        
        # 新格式：字典，以ID为键
        new_format = {}
        for i, item in enumerate(old_format):
            new_format[f"quest_{i}"] = {
                **item,
                "id": f"quest_{i}",
                "created_at": datetime.now().isoformat()
            }
        
        # 验证转换正确
        assert len(new_format) == len(old_format)
        assert "quest_0" in new_format
        assert new_format["quest_0"]["name"] == "任务1"
    
    @pytest.mark.asyncio
    async def test_string_to_enum_conversion(self):
        """测试字符串到枚举的转换."""
        # 旧格式：字符串
        old_rarity = "legendary"
        
        # 新格式：枚举值
        rarity_map = {
            "common": 1,
            "rare": 2,
            "epic": 3,
            "legendary": 4
        }
        
        new_rarity = rarity_map.get(old_rarity, 1)
        assert new_rarity == 4
    
    @pytest.mark.asyncio
    async def test_flat_to_nested_conversion(self):
        """测试扁平结构到嵌套结构的转换."""
        # 旧格式：扁平
        old_data = {
            "str": 10,
            "agi": 15,
            "int": 12,
            "con": 14,
        }
        
        # 新格式：嵌套
        new_data = {
            "attributes": {
                "primary": {
                    "strength": old_data["str"],
                    "agility": old_data["agi"],
                },
                "secondary": {
                    "intelligence": old_data["int"],
                    "constitution": old_data["con"],
                }
            }
        }
        
        # 验证转换
        assert new_data["attributes"]["primary"]["strength"] == 10
        assert new_data["attributes"]["secondary"]["intelligence"] == 12


class TestBackwardCompatibility:
    """向后兼容性测试."""
    
    @pytest.mark.asyncio
    async def test_load_old_save_data(self):
        """测试加载旧版本存档数据."""
        # 模拟旧版本存档数据
        old_save_data = {
            "version": "1.0",
            "player": {
                "name": "老玩家",
                "level": 50,
                "exp": 50000,
                # 缺少新字段
            },
            "inventory": [
                {"item_id": "sword_001", "count": 1},
            ],
            # 缺少新系统数据
        }
        
        # 兼容性处理：为新字段提供默认值
        def migrate_save_data(old_data):
            new_data = {
                **old_data,
                "version": "2.0",
                "player": {
                    **old_data.get("player", {}),
                    "reputation": 0,  # 新增字段默认值
                    "achievements": [],  # 新增字段
                },
                "new_system": {
                    "feature_x": False,  # 新系统默认关闭
                }
            }
            return new_data
        
        new_data = migrate_save_data(old_save_data)
        
        # 验证兼容
        assert new_data["player"]["name"] == "老玩家"
        assert new_data["player"]["reputation"] == 0  # 默认值
        assert "new_system" in new_data
    
    @pytest.mark.asyncio
    async def test_api_backward_compatibility(self):
        """测试API向后兼容性."""
        # 旧API调用方式
        def old_api_call(character_name, level):
            return {"name": character_name, "level": level}
        
        # 新API保持兼容
        def new_api_call(character_name, level, **kwargs):
            # 新参数有默认值，不影响旧调用
            return {
                "name": character_name,
                "level": level,
                "title": kwargs.get("title", ""),
                "faction": kwargs.get("faction", None),
            }
        
        # 旧调用方式仍然有效
        result = new_api_call("测试", 50)
        assert result["name"] == "测试"
        assert result["level"] == 50
        assert result["title"] == ""  # 默认值


class TestCrossVersionDataIntegrity:
    """跨版本数据完整性测试."""
    
    @pytest.mark.asyncio
    async def test_checksum_verification(self):
        """测试数据校验和验证."""
        import hashlib
        
        data = {
            "player_name": "测试玩家",
            "level": 50,
            "gold": 10000,
        }
        
        # 计算校验和
        data_str = json.dumps(data, sort_keys=True)
        checksum = hashlib.md5(data_str.encode()).hexdigest()
        
        # 验证数据完整性
        verified_data_str = json.dumps(data, sort_keys=True)
        verified_checksum = hashlib.md5(verified_data_str.encode()).hexdigest()
        
        assert checksum == verified_checksum
    
    @pytest.mark.asyncio
    async def test_data_validation_rules(self):
        """测试数据验证规则."""
        def validate_character_data(data):
            """验证角色数据完整性."""
            errors = []
            
            # 必填字段
            required = ["name", "level", "hp", "mp"]
            for field in required:
                if field not in data:
                    errors.append(f"缺少必填字段: {field}")
            
            # 数值范围
            if "level" in data and not (1 <= data["level"] <= 100):
                errors.append("等级超出范围")
            
            if "hp" in data and data["hp"] < 0:
                errors.append("HP不能为负")
            
            return len(errors) == 0, errors
        
        # 有效数据
        valid_data = {"name": "测试", "level": 50, "hp": 100, "mp": 50}
        is_valid, errors = validate_character_data(valid_data)
        assert is_valid
        assert len(errors) == 0
        
        # 无效数据
        invalid_data = {"name": "测试", "level": 150, "hp": -10}
        is_valid, errors = validate_character_data(invalid_data)
        assert not is_valid
        assert len(errors) > 0


class TestSerializationCompatibility:
    """序列化兼容性测试."""
    
    @pytest.mark.asyncio
    async def test_json_serialization_roundtrip(self):
        """测试JSON序列化往返."""
        original = {
            "name": "测试",
            "level": 50,
            "stats": {"str": 10, "agi": 15},
            "inventory": [
                {"id": "sword", "durability": 100},
            ],
            "created_at": datetime.now().isoformat(),
        }
        
        # 序列化
        json_str = json.dumps(original, ensure_ascii=False)
        
        # 反序列化
        restored = json.loads(json_str)
        
        # 验证数据一致
        assert restored["name"] == original["name"]
        assert restored["level"] == original["level"]
        assert restored["stats"]["str"] == 10
    
    @pytest.mark.asyncio
    async def test_binary_serialization_compatibility(self):
        """测试二进制序列化兼容性."""
        import pickle
        
        data = {
            "name": "测试",
            "values": [1, 2, 3, 4, 5],
        }
        
        # Pickle序列化
        pickled = pickle.dumps(data)
        unpickled = pickle.loads(pickled)
        
        assert unpickled["name"] == data["name"]
        assert unpickled["values"] == data["values"]


class TestConfigurationMigration:
    """配置迁移测试."""
    
    @pytest.mark.asyncio
    async def test_config_version_upgrade(self):
        """测试配置版本升级."""
        old_config = {
            "version": "1.0",
            "database": {
                "path": "game.db",
            },
            # 缺少新配置项
        }
        
        def migrate_config(old_cfg):
            """迁移配置到新版本."""
            new_cfg = {
                "version": "2.0",
                "database": {
                    **old_cfg.get("database", {}),
                    "pool_size": 5,  # 新增配置
                    "timeout": 30,   # 新增配置
                },
                "features": {
                    "new_feature_x": True,  # 新增功能默认开启
                }
            }
            return new_cfg
        
        new_config = migrate_config(old_config)
        
        assert new_config["version"] == "2.0"
        assert new_config["database"]["pool_size"] == 5
        assert "features" in new_config


# 标记测试
pytestmark = [
    pytest.mark.integration,
    pytest.mark.migration
]
