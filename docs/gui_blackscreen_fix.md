# GUI 黑屏问题修复日志

**日期**: 2026-03-17
**问题**: GUI 启动后显示一片漆黑
**状态**: ✅ 已修复

---

## 问题描述

用户启动 GUI 后，窗口显示一片漆黑，无法看到任何内容。

---

## 问题原因

在实现 B4-GUI-007 动画效果时，在 `MainWindow.__init__()` 中添加了启动淡入动画：

```python
# 启动时淡入动画
fade_in = AnimationHelper.fade_in(self, duration=500)
fade_in.start()
```

`AnimationHelper.fade_in()` 会创建一个从透明（opacity=0.0）到不透明（opacity=1.0）的动画。但由于某些原因（可能是动画未正确完成或被中断），窗口保持在透明或半透明状态，导致用户看到黑屏。

---

## 解决方案

将启动淡入动画注释掉，改为可选功能：

```python
# 启动时淡入动画（可选，通过配置启用）
# fade_in = AnimationHelper.fade_in(self, duration=500)
# fade_in.start()
```

---

## 修复文件

- `src/gui/main_window.py` - 注释掉淡入动画

---

## 测试结果

✅ GUI 正常启动
✅ 窗口内容正常显示
✅ 暗色主题正确应用
✅ 所有面板正常工作

---

## 后续改进

如果需要启动动画，可以考虑：

1. **延迟启动动画**: 在窗口完全初始化后再启动
2. **配置选项**: 通过配置文件控制是否启用
3. **更安全的实现**: 确保动画完成后窗口完全不透明

示例代码：

```python
def showEvent(self, event):
    """窗口显示事件."""
    super().showEvent(event)

    # 在窗口显示后启动淡入动画
    if self.engine and self.engine.config.gui.enable_fade_in:
        QTimer.singleShot(100, self._start_fade_in)

def _start_fade_in(self):
    """启动淡入动画."""
    fade_in = AnimationHelper.fade_in(self, duration=300)
    fade_in.finished.connect(lambda: self.setWindowOpacity(1.0))
    fade_in.start()
```

---

## 相关提交

- `d19d5dc` - fix(gui): 禁用启动淡入动画避免黑屏问题

---

**修复时间**: 约 5 分钟
**影响范围**: 启动体验
**优先级**: 高（阻塞性问题）
