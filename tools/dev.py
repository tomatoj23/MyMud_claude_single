"""开发工具脚本.

提供代码格式化、静态检查、测试运行、项目初始化等开发辅助功能。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """运行命令.

    Args:
        cmd: 命令列表
        cwd: 工作目录
        check: 是否检查返回码

    Returns:
        命令执行结果

    Raises:
        subprocess.CalledProcessError: 命令执行失败
    """
    print(f">>> {' '.join(cmd)}")
    return subprocess.run(
        cmd,
        cwd=cwd or PROJECT_ROOT,
        check=check,
        capture_output=False,
        text=True,
    )


def check_black(files: list[str] | None = None, fix: bool = False) -> int:
    """运行Black代码格式化检查.

    Args:
        files: 要检查的文件列表，None则检查整个项目
        fix: 是否自动修复

    Returns:
        返回码
    """
    cmd = ["black"]
    if not fix:
        cmd.append("--check")
    cmd.append("--diff")
    cmd.append("--line-length")
    cmd.append("100")

    if files:
        cmd.extend(files)
    else:
        cmd.append(".")

    try:
        result = run_command(cmd, check=False)
        if result.returncode != 0:
            if not fix:
                print("\n[!] Black check failed. Run 'python -m tools.dev fmt' to fix.")
        return result.returncode
    except FileNotFoundError:
        print("[!] Black not found. Install with: pip install black")
        return 1


def check_ruff(files: list[str] | None = None, fix: bool = False) -> int:
    """运行Ruff静态检查.

    Args:
        files: 要检查的文件列表，None则检查整个项目
        fix: 是否自动修复

    Returns:
        返回码
    """
    cmd = ["ruff", "check"]
    if fix:
        cmd.append("--fix")
    cmd.append("--show-source")

    if files:
        cmd.extend(files)
    else:
        cmd.append(".")

    try:
        result = run_command(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("[!] Ruff not found. Install with: pip install ruff")
        return 1


def check_mypy(files: list[str] | None = None) -> int:
    """运行MyPy类型检查.

    Args:
        files: 要检查的文件列表，None则检查整个项目

    Returns:
        返回码
    """
    cmd = ["mypy"]

    if files:
        cmd.extend(files)
    else:
        cmd.append("src")

    try:
        result = run_command(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("[!] MyPy not found. Install with: pip install mypy")
        return 1


def run_tests(
    marker: str | None = None,
    verbose: bool = True,
    coverage: bool = True,
    files: list[str] | None = None,
) -> int:
    """运行测试.

    Args:
        marker: 测试标记过滤
        verbose: 是否详细输出
        coverage: 是否生成覆盖率报告
        files: 要运行的测试文件

    Returns:
        返回码
    """
    cmd = ["pytest"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing", "--cov-report=html"])

    if marker:
        cmd.extend(["-m", marker])

    if files:
        cmd.extend(files)
    else:
        cmd.append("tests/")

    try:
        result = run_command(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("[!] Pytest not found. Install with: pip install pytest pytest-cov")
        return 1


def format_code(files: list[str] | None = None) -> int:
    """格式化代码.

    使用Black和Ruff自动修复代码格式问题。

    Args:
        files: 要格式化的文件列表，None则格式化整个项目

    Returns:
        返回码
    """
    print("=" * 50)
    print("Running Black...")
    print("=" * 50)
    black_result = check_black(files, fix=True)

    print("\n" + "=" * 50)
    print("Running Ruff with auto-fix...")
    print("=" * 50)
    ruff_result = check_ruff(files, fix=True)

    # 再次运行black确保格式一致
    print("\n" + "=" * 50)
    print("Re-running Black for consistency...")
    print("=" * 50)
    black_result = check_black(files, fix=True)

    return max(black_result, ruff_result)


def lint(files: list[str] | None = None) -> int:
    """运行所有静态检查.

    Args:
        files: 要检查的文件列表，None则检查整个项目

    Returns:
        返回码
    """
    results: list[int] = []

    print("=" * 50)
    print("Running Black check...")
    print("=" * 50)
    results.append(check_black(files, fix=False))

    print("\n" + "=" * 50)
    print("Running Ruff check...")
    print("=" * 50)
    results.append(check_ruff(files, fix=False))

    print("\n" + "=" * 50)
    print("Running MyPy check...")
    print("=" * 50)
    results.append(check_mypy(files))

    return max(results)


def init_project() -> int:
    """初始化项目.

    创建必要的目录结构和配置文件。

    Returns:
        返回码
    """
    print("Initializing JinYong MUD project...")

    # 创建目录
    directories = [
        "logs",
        "data",
        "saves",
        "resources/maps",
        "resources/quests",
        "resources/dialogs",
    ]

    for directory in directories:
        path = PROJECT_ROOT / directory
        path.mkdir(parents=True, exist_ok=True)
        print(f"  Created directory: {path}")

    # 创建默认配置文件
    config_file = PROJECT_ROOT / "config.yaml"
    if not config_file.exists():
        config_content = '''# 金庸武侠MUD游戏配置
environment: development
debug: true

database:
  url: sqlite+aiosqlite:///data/jinyong_mud.db
  echo: false
  pool_size: 5
  max_overflow: 10
  pool_pre_ping: true

game:
  name: "金庸武侠MUD"
  version: "0.1.0"
  tick_rate: 0.1
  auto_save_interval: 300
  max_players: 1

gui:
  theme: "default"
  font_family: "Microsoft YaHei"
  font_size: 14
  window_width: 1200
  window_height: 800
  fullscreen: false
  locale: "zh_CN"

logging:
  level: "DEBUG"
  log_dir: "logs"
  console_output: true
  file_output: true
  max_bytes: 10485760
  backup_count: 5
'''
        config_file.write_text(config_content, encoding="utf-8")
        print(f"  Created config file: {config_file}")

    print("\nProject initialization complete!")
    print("\nNext steps:")
    print("  1. pip install -e .")
    print("  2. python -m tools.dev check")

    return 0


def install_dev() -> int:
    """安装开发依赖.

    Returns:
        返回码
    """
    print("Installing development dependencies...")
    return run_command(
        ["pip", "install", "-e", ".[dev]"],
        check=False,
    ).returncode


def clean() -> int:
    """清理临时文件.

    Returns:
        返回码
    """
    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.pyd",
        "**/.pytest_cache",
        "**/.mypy_cache",
        "**/.coverage",
        "htmlcov",
        "build",
        "dist",
        "*.egg-info",
        ".eggs",
    ]

    print("Cleaning temporary files...")

    for pattern in patterns:
        for path in PROJECT_ROOT.rglob(pattern):
            if path.is_dir():
                import shutil

                shutil.rmtree(path, ignore_errors=True)
                print(f"  Removed directory: {path}")
            elif path.is_file():
                path.unlink()
                print(f"  Removed file: {path}")

    print("Clean complete!")
    return 0


def main() -> NoReturn:
    """主函数.

    解析命令行参数并执行相应命令。
    """
    parser = argparse.ArgumentParser(
        prog="jy-dev",
        description="JinYong MUD development tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s init              # Initialize project
  %(prog)s fmt               # Format all code
  %(prog)s check             # Run all checks
  %(prog)s test              # Run tests
  %(prog)s test -m unit      # Run unit tests only
  %(prog)s lint src/utils    # Lint specific directory
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize project structure")

    # install
    subparsers.add_parser("install", help="Install development dependencies")

    # fmt
    fmt_parser = subparsers.add_parser("fmt", help="Format code with Black and Ruff")
    fmt_parser.add_argument("files", nargs="*", help="Files to format")

    # check / lint
    lint_parser = subparsers.add_parser(
        "check", aliases=["lint"], help="Run all static checks"
    )
    lint_parser.add_argument("files", nargs="*", help="Files to check")

    # test
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("-m", "--marker", help="Run tests with specific marker")
    test_parser.add_argument("--no-cov", action="store_true", help="Disable coverage")
    test_parser.add_argument("files", nargs="*", help="Test files to run")

    # black
    black_parser = subparsers.add_parser("black", help="Run Black formatter")
    black_parser.add_argument("--check", action="store_true", help="Check only")
    black_parser.add_argument("files", nargs="*", help="Files to format")

    # ruff
    ruff_parser = subparsers.add_parser("ruff", help="Run Ruff linter")
    ruff_parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    ruff_parser.add_argument("files", nargs="*", help="Files to check")

    # mypy
    mypy_parser = subparsers.add_parser("mypy", help="Run MyPy type checker")
    mypy_parser.add_argument("files", nargs="*", help="Files to check")

    # clean
    subparsers.add_parser("clean", help="Clean temporary files")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    result = 0

    try:
        if args.command == "init":
            result = init_project()
        elif args.command == "install":
            result = install_dev()
        elif args.command in ("fmt", "format"):
            result = format_code(args.files if args.files else None)
        elif args.command in ("check", "lint"):
            result = lint(args.files if args.files else None)
        elif args.command == "test":
            result = run_tests(
                marker=args.marker,
                coverage=not args.no_cov,
                files=args.files if args.files else None,
            )
        elif args.command == "black":
            result = check_black(
                args.files if args.files else None,
                fix=not args.check,
            )
        elif args.command == "ruff":
            result = check_ruff(
                args.files if args.files else None,
                fix=args.fix,
            )
        elif args.command == "mypy":
            result = check_mypy(args.files if args.files else None)
        elif args.command == "clean":
            result = clean()
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        result = 130
    except Exception as e:
        print(f"\n[!] Error: {e}")
        result = 1

    sys.exit(result)


if __name__ == "__main__":
    main()
