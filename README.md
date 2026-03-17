# 金庸武侠文字MUD

单机版金庸武侠文字MUD游戏引擎，基于 Python 3.11+ 开发，推荐 Python 3.13。

## 特性

- 🎮 **经典MUD体验**：还原传统文字MUD游戏体验
- 🗡️ **金庸武侠世界**：基于金庸小说的武侠世界观
- 🖥️ **图形界面**：基于PySide6的现代化GUI，支持主题切换
- ⚡ **异步架构**：基于asyncio的高性能引擎
- 💾 **存档系统**：MessagePack + Gzip压缩，支持多存档槽位
- ⌨️ **快捷键支持**：完整的键盘快捷键体系
- 🔧 **模块化设计**：易于扩展和定制

## 当前状态

- ✅ **Phase 1-3**: 引擎核心、武侠世界、玩法系统（100%）
- 🔄 **Phase 4**: GUI客户端（60%）
  - ✅ MVP完成（启动、输入、输出、状态）
  - ✅ 右侧信息面板（地图/任务/装备/背包）
  - ✅ 主题系统（dark/light）
  - ✅ 快捷键支持
  - ✅ 存档/读档功能
- ⏳ **Phase 5**: 内容制作（待开始）
- ⏳ **Phase 6**: 系统功能（待开始）

**测试**: 1,812个测试，100%通过

## 快速开始

### 环境要求

推荐使用 Python 3.13。Python 3.14 在本地已有可用环境时可以继续使用，但 `qasync` 官方当前仍只声明支持 `<3.14`，所以全新环境和可复现安装仍建议优先使用 Python 3.13。

- Python 3.11+（推荐 3.13）
- pip

### 安装

```bash
# 克隆仓库
git clone https://github.com/jinyong-mud/jinyong-mud.git
cd jinyong-mud

# Windows（推荐使用 Python 3.13）
py -3.13 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1

# macOS / Linux
python3.13 -m venv .venv
source .venv/bin/activate

# 初始化项目
make init

# 安装依赖
python -m pip install -e ".[dev]"

# 或者直接运行仓库脚本（会优先选择 3.13/3.12/3.11）
powershell -ExecutionPolicy Bypass -File .\scripts\setup_venv.ps1 -InstallDev
```

### 运行

```bash
# 启动游戏（GUI模式）
make run

# 或使用Python模块
python -m src.gui.main_window

# 或使用安装的命令
jinyong-mud
```

### GUI 功能

- **输入/输出**: 命令输入框和彩色输出区
- **状态显示**: HP/MP进度条、房间信息
- **信息面板**: 地图、任务、装备、背包四个标签页
- **主题切换**: 支持暗色/亮色主题
- **快捷键**:
  - `Ctrl+L` - 焦点到输入框
  - `Ctrl+K` - 清空输出区
  - `Ctrl+S` - 保存游戏
  - `Ctrl+O` - 读取游戏
  - `Ctrl+Q` - 退出
  - `F1/F2/F3` - 快速命令（look/inventory/status）
- **存档系统**: 多槽位存档，支持保存/读取/删除

## 开发

### 常用命令

```bash
# 格式化代码
make fmt

# 运行静态检查
make lint

# 运行测试
make test

# 运行所有检查
make check

# 清理临时文件
make clean
```

### 项目结构

```
jinyong_mud/
├── src/
│   ├── engine/          # 游戏引擎核心
│   ├── gui/             # PySide6图形界面
│   ├── game/            # 游戏具体实现
│   └── utils/           # 工具函数
├── tests/               # 单元测试和集成测试
├── docs/                # 文档
├── tools/               # 开发工具
├── resources/           # 资源文件
└── scripts/             # 辅助脚本
```

## 配置

配置文件支持YAML和JSON格式，默认从以下位置加载(按优先级)：

1. `config.development.yaml` (开发环境)
2. `config.testing.yaml` (测试环境)
3. `config.production.yaml` (生产环境)
4. `config.yaml` (通用配置)

配置示例：

```yaml
environment: development
debug: true

game:
  name: "金庸武侠MUD"
  tick_rate: 0.1
  auto_save_interval: 300

gui:
  theme: "default"
  font_family: "Microsoft YaHei"
  font_size: 14

logging:
  level: "INFO"
  log_dir: "logs"
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
