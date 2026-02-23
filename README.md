# 金庸武侠文字MUD

单机版金庸武侠文字MUD游戏引擎，基于Python 3.11+开发。

## 特性

- 🎮 **经典MUD体验**：还原传统文字MUD游戏体验
- 🗡️ **金庸武侠世界**：基于金庸小说的武侠世界观
- 🖥️ **图形界面**：基于PySide6的现代化GUI
- ⚡ **异步架构**：基于asyncio的高性能引擎
- 🔧 **模块化设计**：易于扩展和定制

## 快速开始

### 环境要求

- Python 3.11+
- pip

### 安装

```bash
# 克隆仓库
git clone https://github.com/jinyong-mud/jinyong-mud.git
cd jinyong-mud

# 初始化项目
make init

# 安装依赖
pip install -e ".[dev]"
```

### 运行

```bash
# 启动游戏
make run

# 或使用Python模块
python -m src.gui.main_window
```

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
