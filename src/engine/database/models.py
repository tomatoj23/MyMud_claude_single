"""ORM模型定义.

定义游戏对象的SQLAlchemy 2.0模型。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Index, String, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """ORM基类."""

    pass


class ObjectModel(Base):
    """游戏对象数据库模型.

    所有游戏对象的持久化表示，支持类型类继承和属性扩展。

    Attributes:
        id: 唯一标识符
        key: 对象标识名
        typeclass_path: 类型类导入路径
        location_id: 所在位置ID（自引用外键）
        attributes: 扩展属性（JSON存储）
        created_at: 创建时间
        updated_at: 更新时间
    """

    __tablename__ = "objects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    typeclass_path: Mapped[str] = mapped_column(
        String(512), nullable=False, index=True
    )

    # 容器关系 - 自引用外键
    location_id: Mapped[int | None] = mapped_column(
        ForeignKey("objects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # 扩展属性（JSON存储）
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
    )

    # 关系定义
    location: Mapped[ObjectModel | None] = relationship(
        "ObjectModel",
        remote_side=[id],
        back_populates="contents",
    )
    contents: Mapped[list[ObjectModel]] = relationship(
        "ObjectModel",
        back_populates="location",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_typeclass_key", "typeclass_path", "key"),
    )

    def __repr__(self) -> str:  # noqa: D105
        return f"<ObjectModel(id={self.id}, key={self.key}, type={self.typeclass_path})>"


class PlayerModel(Base):
    """玩家数据模型.

    存储玩家账户相关的持久化数据。

    Attributes:
        id: 唯一标识符
        account_name: 账户名
        object_id: 关联的游戏对象ID
        last_login: 最后登录时间
        created_at: 创建时间
    """

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    object_id: Mapped[int] = mapped_column(
        ForeignKey("objects.id", ondelete="CASCADE"),
        nullable=False,
    )
    last_login: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # 关系
    object: Mapped[ObjectModel] = relationship("ObjectModel")


class ScriptModel(Base):
    """脚本数据模型.

    存储游戏脚本/事件的持久化状态。

    Attributes:
        id: 唯一标识符
        key: 脚本标识名
        typeclass_path: 类型类导入路径
        object_id: 关联的游戏对象ID（可选）
        attributes: 扩展属性
        is_active: 是否激活
        interval: 执行间隔（秒）
        next_run: 下次执行时间
    """

    __tablename__ = "scripts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    typeclass_path: Mapped[str] = mapped_column(String(512), nullable=False)
    object_id: Mapped[int | None] = mapped_column(
        ForeignKey("objects.id", ondelete="CASCADE"),
        nullable=True,
    )
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True)
    interval: Mapped[float] = mapped_column(default=0.0)
    next_run: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
