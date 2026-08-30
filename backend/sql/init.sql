-- ============================================================
-- AI 内容工场 · 数据库初始化脚本（init.sql）
-- 四张核心表：user / content_record / custom_template / batch_task_log
--
-- 说明：
--   * 应用启动时 SQLAlchemy 会自动 create_all（SQLite 开箱即用），
--     本脚本用于：手动建库 / MySQL 生产环境初始化 / DBA 审查表结构；
--   * 默认给出 SQLite 方言（JSON 列存储为 TEXT）；MySQL 方言见文末注释块；
--   * 时间字段统一 DATETIME；业务表均带 user_id 外键（数据隔离）；
--   * batch_task_log.items / error_detail / meta 为 JSON 列（MySQL 用 JSON 类型）。
-- ============================================================

PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- 用户表：密码 PBKDF2 加密存储，首个用户自动为管理员
CREATE TABLE IF NOT EXISTS user (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      VARCHAR(64)  NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,               -- pbkdf2$迭代$盐$散列
    is_admin      BOOLEAN      NOT NULL DEFAULT 0,     -- 管理员标记
    created_at    DATETIME     NOT NULL,
    last_login_at DATETIME
);
CREATE INDEX IF NOT EXISTS idx_user_username ON user (username);

-- 内容生成记录：脚本 / 标题标签 / 文案改写 / TTS 统一归档
CREATE TABLE IF NOT EXISTS content_record (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER      NOT NULL REFERENCES user(id),
    topic        VARCHAR(255) NOT NULL,                 -- 生成主题
    record_type  VARCHAR(32)  NOT NULL DEFAULT 'script',-- script|titles|copywriting|tts
    platform     VARCHAR(32)  NOT NULL DEFAULT 'douyin',
    style        VARCHAR(64)  NOT NULL DEFAULT '通用',
    duration     INTEGER      NOT NULL DEFAULT 60,      -- 秒
    content      TEXT         NOT NULL DEFAULT '{}',    -- JSON：overview/segments/hook/ending...
    titles       TEXT         NOT NULL DEFAULT '[]',    -- JSON: ["标题1", ...]
    tags         TEXT         NOT NULL DEFAULT '[]',    -- JSON: [{tier,text}, ...]
    tts_text     TEXT         NOT NULL DEFAULT '',
    body_text    TEXT         NOT NULL DEFAULT '',
    source_model VARCHAR(64)  NOT NULL DEFAULT '',
    status       VARCHAR(16)  NOT NULL DEFAULT 'success',
    is_deleted   BOOLEAN      NOT NULL DEFAULT 0,       -- 软删除
    created_at   DATETIME     NOT NULL,
    updated_at   DATETIME     NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_content_user ON content_record (user_id, is_deleted, created_at);
CREATE INDEX IF NOT EXISTS idx_content_type ON content_record (record_type);

-- 自定义模板：脚本 / 风格 / Prompt 三类
CREATE TABLE IF NOT EXISTS custom_template (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER      NOT NULL REFERENCES user(id),
    name        VARCHAR(128) NOT NULL,
    scene_type  VARCHAR(32)  NOT NULL,                  -- script|style|prompt
    description VARCHAR(512) NOT NULL DEFAULT '',
    content     TEXT         NOT NULL,                  -- 模板正文 / Prompt
    created_at  DATETIME     NOT NULL,
    updated_at  DATETIME     NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_template_user ON custom_template (user_id, scene_type);

-- 批量任务日志：进度 / 成败统计 / 失败详情全量落库
CREATE TABLE IF NOT EXISTS batch_task_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER      NOT NULL REFERENCES user(id),
    name         VARCHAR(255) NOT NULL DEFAULT '批量生成任务',
    total        INTEGER      NOT NULL DEFAULT 0,
    success      INTEGER      NOT NULL DEFAULT 0,
    failed       INTEGER      NOT NULL DEFAULT 0,
    status       VARCHAR(16)  NOT NULL DEFAULT 'pending', -- pending|running|completed|partial|failed|cancelled
    duration     REAL,                                   -- 任务耗时（秒）
    meta         TEXT         NOT NULL DEFAULT '{}',     -- JSON: 统一生成参数
    items        TEXT         NOT NULL DEFAULT '[]',     -- JSON: 条目级状态/错误/结果ID
    error_detail TEXT         NOT NULL DEFAULT '{}',     -- JSON: {序号-主题: 错误原因}
    created_at   DATETIME     NOT NULL,
    finished_at  DATETIME
);
CREATE INDEX IF NOT EXISTS idx_task_user ON batch_task_log (user_id, created_at);

-- ============================================================
-- MySQL 8 方言（替换上方 SQLite 部分，JSON 列直接用 JSON 类型）：
--
-- CREATE TABLE user (
--   id BIGINT PRIMARY KEY AUTO_INCREMENT,
--   username VARCHAR(64) NOT NULL UNIQUE,
--   password_hash VARCHAR(256) NOT NULL,
--   is_admin TINYINT(1) NOT NULL DEFAULT 0,
--   created_at DATETIME NOT NULL,
--   last_login_at DATETIME NULL
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
--
-- content_record / custom_template / batch_task_log 结构同上，
-- 仅将对应的 TEXT NOT NULL DEFAULT '{}' 替换为 JSON NOT NULL，
-- 并追加：INDEX idx_content_user (user_id, is_deleted, created_at) 等。
-- 生产切换只需修改后端 DATABASE_URL 为 mysql+pymysql://...
-- ============================================================
