"""GUI集成测试 - 验证GUI与引擎交互."""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

# 设置无头模式
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from src.engine.core.engine import GameEngine
from src.engine.core.messages import MessageType
from src.gui.main_window import GUIManager
from src.utils.config import Config


@pytest.fixture
def qapp():
    """Qt应用fixture."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest_asyncio.fixture
async def gui_with_engine(qapp):
    """创建带引擎的GUI（独立引擎实例）."""
    tmp_dir = tempfile.mkdtemp()
    config = Config()
    config.database.url = f"sqlite+aiosqlite:///{Path(tmp_dir)}/test_gui.db"
    config.game.auto_save_interval = 3600

    engine = GameEngine(config)
    await engine.initialize()

    # 创建默认房间
    room = await engine.objects.create(
        typeclass_path="src.game.typeclasses.room.Room",
        key="测试房间",
        attributes={"description": "这是一个测试房间", "coords": (0, 0, 0)},
    )

    # 创建玩家
    player = await engine.objects.create(
        typeclass_path="src.game.typeclasses.character.Character",
        key="测试玩家",
        attributes={"location_id": room.id},
    )
    player._db_model.location_id = room.id
    player.message_bus = engine.message_bus

    # 创建GUI
    manager = GUIManager()
    window = manager.create_main_window(engine)
    manager.set_player(player)

    yield manager, window, player, engine

    # 清理
    window.close()
    if engine.running:
        await engine.stop()


class TestMessageBusToGUI:
    """测试MessageBus到GUI的消息转发."""

    @pytest.mark.asyncio
    async def test_message_forwarding(self, gui_with_engine):
        """测试消息转发到输出区."""
        manager, window, player, engine = gui_with_engine

        # 发送消息
        engine.message_bus.emit_text(MessageType.INFO, "测试消息")

        # 等待Qt事件处理
        await asyncio.sleep(0.1)

        # 检查输出区包含消息
        output_text = window._output_browser.toPlainText()
        assert "测试消息" in output_text

    @pytest.mark.asyncio
    async def test_error_message_color(self, gui_with_engine):
        """测试错误消息红色样式."""
        manager, window, player, engine = gui_with_engine

        # 发送错误消息
        engine.message_bus.emit_text(MessageType.ERROR, "错误消息")

        # 等待Qt事件处理
        await asyncio.sleep(0.1)

        # 检查输出区包含消息和红色样式
        output_html = window._output_browser.toHtml()
        assert "错误消息" in output_html
        assert "#cc0000" in output_html


class TestInputToEngine:
    """测试输入到引擎的命令处理."""

    @pytest.mark.asyncio
    async def test_look_command(self, gui_with_engine):
        """测试输入look命令后输出区包含房间信息."""
        manager, window, player, engine = gui_with_engine

        # 启动引擎
        await engine.start()

        # 模拟输入look命令
        window._input_field.setText("look")
        window._on_submit_command()

        # 等待命令执行
        await asyncio.sleep(0.5)

        # 检查输出区包含房间信息
        output_text = window._output_browser.toPlainText()
        assert "测试房间" in output_text or "房间" in output_text


class TestWindowCloseStopsEngine:
    """测试关闭窗口停止引擎."""

    @pytest.mark.asyncio
    async def test_close_stops_engine(self, gui_with_engine):
        """测试关闭窗口后引擎停止."""
        manager, window, player, engine = gui_with_engine

        # 启动引擎
        await engine.start()
        assert engine.running is True

        # 关闭窗口
        from PySide6.QtGui import QCloseEvent

        event = QCloseEvent()
        window.closeEvent(event)

        # 等待停止
        await asyncio.sleep(0.5)

        # 检查引擎已停止
        assert engine.running is False
