# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

金庸武侠MUD (JinYong Wuxia MUD) — a single-player text MUD game engine built on Python 3.11+ (recommended 3.13). Wuxia-themed game world based on Jin Yong novels, with a PySide6 GUI, async engine, and SQLite persistence.

## Common Commands

```bash
make fmt              # Format code (Black + Ruff)
make lint             # Static checks (Ruff + MyPy)
make test             # Run all tests with coverage
make check            # lint + test
make run              # Launch game GUI (python -m src.gui.main_window)

# Run specific test subsets
pytest tests/unit/                        # Unit tests only
pytest tests/integration/                 # Integration tests only
pytest tests/unit/test_combat.py          # Single test file
pytest -m chaos                           # By marker (unit/integration/slow/chaos/security/etc.)
pytest tests/unit/test_combat.py::TestCombat::test_damage  # Single test

# Direct tool usage
black src/ tests/                         # Format
ruff check src/ tests/                    # Lint
mypy src/                                 # Type check
```

## Architecture

Three-layer design:

```
GUI (PySide6 + qasync)  →  Engine (asyncio)  →  Data (SQLAlchemy 2.0 + aiosqlite/SQLite WAL)
```

### Engine Layer (`src/engine/`)
- `core/engine.py` — `GameEngine` class: orchestrates all subsystems (db, objects, commands, events, message bus)
- `core/typeclass.py` — Dynamic typeclass system with `AttributeHandler` for transparent DB attribute proxying and dirty-object tracking
- `core/messages.py` — `MessageBus` for decoupled GUI↔Engine communication
- `objects/manager.py` — `ObjectManager` with L1 cache, dirty tracking, batch saves
- `commands/` — Command parsing: `Command` base class, `CmdSet`, `CommandHandler`
- `events/scheduler.py` — `EventScheduler` + `qt_scheduler.py` for Qt integration
- `database/connection.py` — `DatabaseManager`, async SQLAlchemy with connection pooling

### Game Layer (`src/game/`)
- `typeclasses/` — Game object types: `Character`, `Equipment`, `Room`, `Item`, wuxue (martial arts)
- `combat/` — Combat system with `CombatTransaction`, strategy pattern AI, buff/debuff
- `npc/` — Behavior tree AI, dialogue system, reputation tracking
- `quest/` — Quest system with karma and world state
- `world/` — World loader, pathfinding
- `commands/` — Game-specific command implementations

### GUI Layer (`src/gui/`)
- `main_window.py` — Entry point, bridges Qt event loop with asyncio via qasync
- `panels/` — UI panels
- `themes/` — Theme system

### Key Patterns
- **Typeclass system**: Game objects are loaded dynamically by `typeclass_path` string (e.g. `"src.game.typeclasses.character.Character"`)
- **Mixin naming**: Equipment and Wuxue mixins prefix all public methods — `equipment_*` and `wuxue_*` (see `docs/standards/mixin_naming.md`)
- **Message bus**: Decoupled pub/sub between GUI and engine — never call GUI from engine directly
- **Transaction pattern**: Combat operations wrapped in `CombatTransaction` for atomicity
- **Attribute access**: `obj.db.attr_name` proxies to DB JSON field with local caching; modifications auto-mark object dirty

## Code Style

- Line length: 100
- Formatter: Black
- Linter: Ruff (rules: E, W, F, I, N, D, UP, B, C4, SIM, ARG)
- Docstrings: Google convention, required on public classes/functions (D100/D104/D107 ignored)
- Type checker: MyPy strict mode
- All source uses `from __future__ import annotations`
- Serialization: MessagePack (never Pickle)
- Async: pure asyncio, no blocking in event loop

## Testing

- Framework: pytest + pytest-asyncio (asyncio_mode = "auto")
- `tests/conftest.py` — shared fixtures: `engine`, `object_manager`, `npc`, auto-`reset_singletons`
- `tests/base.py` — `MockDBModel`, `MockManager` for unit tests that don't need a real engine
- Singletons are auto-reset between tests via the `reset_singletons` autouse fixture
- Engine fixture uses a temp SQLite DB per module

## Configuration

YAML config files loaded by priority: `config.development.yaml` > `config.testing.yaml` > `config.production.yaml` > `config.yaml`

## Project Status

Phases 1-3 complete (engine, world, game systems). Phase 4 (GUI) in progress. See `TODO.md` and `DEVELOPMENT_PLAN.md` for current status.
