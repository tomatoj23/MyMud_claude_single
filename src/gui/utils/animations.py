"""GUI 动画效果工具."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QSequentialAnimationGroup,
)
from PySide6.QtWidgets import QGraphicsOpacityEffect

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class AnimationHelper:
    """动画辅助类.

    提供常用的动画效果。
    """

    @staticmethod
    def fade_in(widget: QWidget, duration: int = 300) -> QPropertyAnimation:
        """淡入动画.

        Args:
            widget: 目标控件
            duration: 持续时间（毫秒）

        Returns:
            动画对象
        """
        # 创建透明度效果
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

        # 创建动画
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        return animation

    @staticmethod
    def fade_out(widget: QWidget, duration: int = 300) -> QPropertyAnimation:
        """淡出动画.

        Args:
            widget: 目标控件
            duration: 持续时间（毫秒）

        Returns:
            动画对象
        """
        # 创建透明度效果
        effect = widget.graphicsEffect()
        if not effect:
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)

        # 创建动画
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        return animation

    @staticmethod
    def slide_in(
        widget: QWidget,
        direction: str = "left",
        duration: int = 300,
        distance: int = 100,
    ) -> QPropertyAnimation:
        """滑入动画.

        Args:
            widget: 目标控件
            direction: 方向 (left/right/top/bottom)
            duration: 持续时间（毫秒）
            distance: 滑动距离

        Returns:
            动画对象
        """
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        current_pos = widget.pos()

        if direction == "left":
            start_pos = current_pos - QPoint(distance, 0)
        elif direction == "right":
            start_pos = current_pos + QPoint(distance, 0)
        elif direction == "top":
            start_pos = current_pos - QPoint(0, distance)
        else:  # bottom
            start_pos = current_pos + QPoint(0, distance)

        animation.setStartValue(start_pos)
        animation.setEndValue(current_pos)

        return animation

    @staticmethod
    def pulse(widget: QWidget, duration: int = 500) -> QSequentialAnimationGroup:
        """脉冲动画（放大缩小）.

        Args:
            widget: 目标控件
            duration: 持续时间（毫秒）

        Returns:
            动画组
        """
        # 创建透明度效果
        effect = widget.graphicsEffect()
        if not effect:
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)

        # 创建动画组
        group = QSequentialAnimationGroup()

        # 淡出
        fade_out_anim = QPropertyAnimation(effect, b"opacity")
        fade_out_anim.setDuration(duration // 2)
        fade_out_anim.setStartValue(1.0)
        fade_out_anim.setEndValue(0.5)
        fade_out_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # 淡入
        fade_in_anim = QPropertyAnimation(effect, b"opacity")
        fade_in_anim.setDuration(duration // 2)
        fade_in_anim.setStartValue(0.5)
        fade_in_anim.setEndValue(1.0)
        fade_in_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        group.addAnimation(fade_out_anim)
        group.addAnimation(fade_in_anim)

        return group

    @staticmethod
    def shake(widget: QWidget, duration: int = 500, distance: int = 10) -> QSequentialAnimationGroup:
        """震动动画.

        Args:
            widget: 目标控件
            duration: 持续时间（毫秒）
            distance: 震动距离

        Returns:
            动画组
        """
        group = QSequentialAnimationGroup()
        current_pos = widget.pos()

        # 创建多个小幅度移动
        steps = 4
        step_duration = duration // steps

        for i in range(steps):
            anim = QPropertyAnimation(widget, b"pos")
            anim.setDuration(step_duration)

            if i % 2 == 0:
                target_pos = current_pos + QPoint(distance, 0)
            else:
                target_pos = current_pos - QPoint(distance, 0)

            anim.setEndValue(target_pos)
            group.addAnimation(anim)

        # 最后回到原位
        final_anim = QPropertyAnimation(widget, b"pos")
        final_anim.setDuration(step_duration)
        final_anim.setEndValue(current_pos)
        group.addAnimation(final_anim)

        return group

    @staticmethod
    def smooth_scroll(widget: QWidget, target_value: int, duration: int = 300) -> QPropertyAnimation:
        """平滑滚动动画.

        Args:
            widget: 滚动条控件
            target_value: 目标值
            duration: 持续时间（毫秒）

        Returns:
            动画对象
        """
        animation = QPropertyAnimation(widget, b"value")
        animation.setDuration(duration)
        animation.setEndValue(target_value)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        return animation


class LoadingAnimation:
    """加载动画.

    显示加载指示器。
    """

    def __init__(self, widget: QWidget) -> None:
        """初始化加载动画.

        Args:
            widget: 目标控件
        """
        self.widget = widget
        self._animation: QPropertyAnimation | None = None
        self._effect: QGraphicsOpacityEffect | None = None

    def start(self) -> None:
        """开始加载动画."""
        # 创建透明度效果
        self._effect = QGraphicsOpacityEffect(self.widget)
        self.widget.setGraphicsEffect(self._effect)

        # 创建循环动画
        self._animation = QPropertyAnimation(self._effect, b"opacity")
        self._animation.setDuration(1000)
        self._animation.setStartValue(0.3)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._animation.setLoopCount(-1)  # 无限循环

        self._animation.start()

    def stop(self) -> None:
        """停止加载动画."""
        if self._animation:
            self._animation.stop()
            self._animation = None

        if self._effect:
            self.widget.setGraphicsEffect(None)
            self._effect = None


class TransitionHelper:
    """过渡效果辅助类."""

    @staticmethod
    def cross_fade(
        old_widget: QWidget,
        new_widget: QWidget,
        duration: int = 300,
    ) -> QParallelAnimationGroup:
        """交叉淡入淡出.

        Args:
            old_widget: 旧控件
            new_widget: 新控件
            duration: 持续时间（毫秒）

        Returns:
            动画组
        """
        group = QParallelAnimationGroup()

        # 旧控件淡出
        fade_out = AnimationHelper.fade_out(old_widget, duration)
        group.addAnimation(fade_out)

        # 新控件淡入
        fade_in = AnimationHelper.fade_in(new_widget, duration)
        group.addAnimation(fade_in)

        return group

    @staticmethod
    def slide_transition(
        old_widget: QWidget,
        new_widget: QWidget,
        direction: str = "left",
        duration: int = 300,
    ) -> QParallelAnimationGroup:
        """滑动过渡.

        Args:
            old_widget: 旧控件
            new_widget: 新控件
            direction: 方向
            duration: 持续时间（毫秒）

        Returns:
            动画组
        """
        group = QParallelAnimationGroup()

        # 旧控件滑出
        old_anim = QPropertyAnimation(old_widget, b"pos")
        old_anim.setDuration(duration)
        old_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        current_pos = old_widget.pos()
        if direction == "left":
            end_pos = current_pos - QPoint(old_widget.width(), 0)
        else:  # right
            end_pos = current_pos + QPoint(old_widget.width(), 0)

        old_anim.setEndValue(end_pos)
        group.addAnimation(old_anim)

        # 新控件滑入
        new_anim = AnimationHelper.slide_in(new_widget, direction, duration)
        group.addAnimation(new_anim)

        return group
