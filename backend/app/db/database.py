# -*- coding: utf-8 -*-
"""数据库引擎与会话管理。

- SQLite（默认本地）/ MySQL（线上）双兼容：仅通过 DATABASE_URL 切换。
- SQLite 开启 WAL + busy_timeout，规避异步批量任务并发写锁冲突。
- 每个请求 / 后台线程独立 Session，无共享会话污染。
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def _build_engine() -> Engine:
    url = settings.DATABASE_URL
    kwargs: dict = {"pool_pre_ping": True, "future": True}
    if url.startswith("sqlite"):
        # 确保 data 目录存在（剥离 sqlite:/// 前缀后取真实路径）
        db_path = url.split("///", 1)[-1]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
    else:
        kwargs["pool_recycle"] = 3600
        kwargs["pool_size"] = 10
    return create_engine(url, **kwargs)


engine = _build_engine()


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _record):
    """SQLite 专项：WAL 提升并发、busy_timeout 等待锁释放。"""
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db():
    """FastAPI 依赖注入：请求级会话，异常回滚，最终关闭。"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """首次启动建表 + 轻量迁移（老库补 is_admin 等新列，无需 Alembic 开箱即用）。"""
    from sqlalchemy import text

    from app.db import models  # noqa: F401  注册模型

    Base.metadata.create_all(bind=engine)

    # ---------- 轻量迁移：为既有库补充新增列 ----------
    with engine.connect() as conn:
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(user)"))}
        if "is_admin" not in existing:
            conn.execute(text("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
            conn.commit()

    # ---------- 初始管理员播种：幂等处理 ----------
    # 系统无管理员时：存在名为 admin 的用户则提升为管理员并重置默认密码，
    # 否则创建 admin/admin123 —— 保证开箱即可用 admin/admin123 登录（请尽快修改密码）
    from app.core.logging import get_logger
    from app.core.security import hash_password
    from app.db.models import User

    logger = get_logger("db.seed")
    with SessionLocal() as db:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            if not existing.is_admin:
                existing.is_admin = True
            existing.password_hash = hash_password("admin123")
            db.commit()
            logger.info("已初始化管理员账号 admin/admin123（原密码已重置，请尽快修改）")
        else:
            db.add(User(username="admin", password_hash=hash_password("admin123"), is_admin=True))
            db.commit()
            logger.info("已创建初始管理员账号：admin / admin123（请尽快在右上角修改密码）")
