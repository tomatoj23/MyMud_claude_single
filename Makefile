# 金庸武侠MUD开发Makefile
# 提供便捷的命令别名

.PHONY: help init install fmt lint test clean check run

# 默认目标
help:
	@echo "金庸武侠MUD开发工具"
	@echo ""
	@echo "可用命令:"
	@echo "  make init     - 初始化项目结构"
	@echo "  make install  - 安装开发依赖"
	@echo "  make fmt      - 格式化代码"
	@echo "  make lint     - 运行静态检查"
	@echo "  make test     - 运行测试"
	@echo "  make check    - 运行所有检查"
	@echo "  make clean    - 清理临时文件"
	@echo "  make run      - 运行游戏"

# 初始化项目
init:
	python -m tools.dev init

# 安装依赖
install:
	python -m tools.dev install

# 格式化代码
fmt:
	python -m tools.dev fmt

# 静态检查
lint:
	python -m tools.dev lint

# 运行测试
test:
	python -m tools.dev test

# 运行单元测试
test-unit:
	python -m tools.dev test -m unit

# 运行集成测试
test-integration:
	python -m tools.dev test -m integration

# 运行所有检查
check: lint test
	@echo "All checks passed!"

# 清理临时文件
clean:
	python -m tools.dev clean

# 运行游戏
run:
	python -m src.gui.main_window
