"""动画效果测试."""

from __future__ import annotations

import os

import pytest
from PySide6.QtWidgets import QApplication, QWidget

from src.gui.utils import AnimationHelper, LoadingAnimation, TransitionHelper

# 设置无头模式
os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture
def app():
    """创建Qt应用."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def widget(app):
    """创建测试控件."""
    widget = QWidget()
    widget.resize(200, 200)
    yield widget
    widget.close()


class TestAnimationHelper:
    """动画辅助类测试."""

    def test_fade_in(self, widget):
        """测试淡入动画."""
        animation = AnimationHelper.fade_in(widget, duration=100)
        assert animation is not None
        assert animation.duration() == 100
        assert animation.startValue() == 0.0
        assert animation.endValue() == 1.0

    def test_fade_out(self, widget):
        """测试淡出动画."""
        animation = AnimationHelper.fade_out(widget, duration=100)
        assert animation is not None
        assert animation.duration() == 100
        assert animation.startValue() == 1.0
        assert animation.endValue() == 0.0

    def test_slide_in_left(self, widget):
        """测试左侧滑入."""
        animation = AnimationHelper.slide_in(widget, direction="left", duration=100)
        assert animation is not None
        assert animation.duration() == 100

    def test_slide_in_right(self, widget):
        """测试右侧滑入."""
        animation = AnimationHelper.slide_in(widget, direction="right", duration=100)
        assert animation is not None

    def test_slide_in_top(self, widget):
        """测试顶部滑入."""
        animation = AnimationHelper.slide_in(widget, direction="top", duration=100)
        assert animation is not None

    def test_slide_in_bottom(self, widget):
        """测试底部滑入."""
        animation = AnimationHelper.slide_in(widget, direction="bottom", duration=100)
        assert animation is not None

    def test_pulse(self, widget):
        """测试脉冲动画."""
        animation = AnimationHelper.pulse(widget, duration=100)
        assert animation is not None
        assert animation.animationCount() == 2

    def test_shake(self, widget):
        """测试震动动画."""
        animation = AnimationHelper.shake(widget, duration=100, distance=5)
        assert animation is not None
        assert animation.animationCount() > 0


class TestLoadingAnimation:
    """加载动画测试."""

    def test_create_loading(self, widget):
        """测试创建加载动画."""
        loading = LoadingAnimation(widget)
        assert loading is not None
        assert loading.widget is widget

    def test_start_stop(self, widget):
        """测试启动和停止."""
        loading = LoadingAnimation(widget)
        loading.start()
        assert loading._animation is not None
        assert loading._effect is not None

        loading.stop()
        assert loading._animation is None
        assert loading._effect is None


class TestTransitionHelper:
    """过渡效果测试."""

    def test_cross_fade(self, app):
        """测试交叉淡入淡出."""
        old_widget = QWidget()
        new_widget = QWidget()

        animation = TransitionHelper.cross_fade(old_widget, new_widget, duration=100)
        assert animation is not None
        assert animation.animationCount() == 2

        old_widget.close()
        new_widget.close()

    def test_slide_transition(self, app):
        """测试滑动过渡."""
        old_widget = QWidget()
        new_widget = QWidget()
        old_widget.resize(200, 200)
        new_widget.resize(200, 200)

        animation = TransitionHelper.slide_transition(
            old_widget, new_widget, direction="left", duration=100
        )
        assert animation is not None
        assert animation.animationCount() == 2

        old_widget.close()
        new_widget.close()
