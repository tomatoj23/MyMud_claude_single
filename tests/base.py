"""测试基类.

提供公共的测试固件和基类.
"""

from __future__ import annotations

from unittest.mock import Mock
import pytest


class MockDBModel:
    """Mock数据库模型."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.key = kwargs.get("key", "test_key")
        self.typeclass_path = kwargs.get("typeclass_path", "src.game.typeclasses.character.Character")
        self.location_id = kwargs.get("location_id", None)
        self.attributes = kwargs.get("attributes", {})
        self.contents = []


class MockManager:
    """Mock对象管理器."""

    def __init__(self):
        self.dirty_objects = set()
        self._cache = {}

    def mark_dirty(self, obj):
        self.dirty_objects.add(getattr(obj, 'id', id(obj)))

    def get(self, obj_id):
        return self._cache.get(obj_id)

    def get_contents_sync(self, obj_id):
        """同步获取对象内容."""
        return [
            obj for obj in self._cache.values()
            if getattr(getattr(obj, '_db_model', None), 'location_id', None) == obj_id
        ]

    async def find(self, **kwargs):
        """Mock find method."""
        return []


@pytest.fixture
def mock_manager():
    """创建Mock管理器."""
    return MockManager()


@pytest.fixture
def mock_db_model():
    """创建Mock数据库模型."""
    return MockDBModel()
