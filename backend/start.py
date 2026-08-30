# -*- coding: utf-8 -*-
"""
AI 内容工场 · 一键启动器（start.py）
================================================
自动完成：环境校验 -> 虚拟环境自举 -> 依赖安装 -> .env 加载 ->
数据库初始化 -> 模型链健康检查 -> 前端拉起 -> 后端服务启动 -> 浏览器打开。

用法（任选其一）：
    python start.py                    # 一键启动整套项目（前端 + 后端 + 自动开浏览器）
    python start.py --no-frontend      # 仅启动后端 API
    python start.py --port 8080        # 指定后端端口（默认 8000，被占用时自动顺延）
    python start.py --check            # 只做环境体检，不启动服务
    python start.py --install-only     # 只装环境后退出

后台隐藏运行：
    - 双击根目录快捷方式「AI内容工场-后台启动.lnk」：以 pythonw（无控制台）运行本脚本，
      日志写入 backend/logs/launcher.log，控制台窗口完全隐藏；
    - 双击根目录 start-hidden.vbs 亦可（需系统允许运行 VBS 脚本）。

说明：
    - 首次运行自动创建 backend/.venv 并安装依赖，全程无手工命令；
    - 配置读取 backend/.env（不存在时自动从 .env.example 复制生成）；
    - 前端所在端口默认 5173（被占用时 Vite 自动顺延），后端端口被占用自动顺延 8000-8009。
"""
from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent          # backend/
ROOT_DIR = BASE_DIR.parent                           # 项目根
VENV_DIR = BASE_DIR / ".venv"
REQ_FILE = BASE_DIR / "requirements.txt"
ENV_FILE = BASE_DIR / ".env"
ENV_TEMPLATE = BASE_DIR / ".env.example"
DEPS_STAMP = VENV_DIR / ".acp_deps_ok"
FRONTEND_DIR = ROOT_DIR / "frontend"

LINUX = os.name != "nt"
PYTHON_MIN = (3, 10)

# ---------------------------------------------------------------- 无控制台适配
# 1) 统一 UTF-8 流：避免 GBK 代码页下打印 ✔/✘/⚠ 等符号 UnicodeEncodeError
for _s in (sys.stdout, sys.stderr):
    if _s is not None and hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass

# 2) pythonw（无控制台宿主）下 stdout/stderr 为 None，任何 print 都会崩溃：
#    接管到 backend/logs/launcher.log，并标记静默模式（子进程隐藏窗口、跳过 pause）。
if sys.stdout is None or sys.stderr is None:
    try:
        _log_dir = BASE_DIR / "logs"
        _log_dir.mkdir(parents=True, exist_ok=True)
        _stream = open(_log_dir / "launcher.log", "a", encoding="utf-8", buffering=1)
        if sys.stdout is None:
            sys.stdout = _stream
        if sys.stderr is None:
            sys.stderr = _stream
    except Exception:  # noqa: BLE001 极少数情况兜底为 devnull
        _null = open(os.devnull, "w")
        sys.stdout = sys.stdout or _null
        sys.stderr = sys.stderr or _null
    os.environ.setdefault("ACP_SILENT", "1")
    # venv 子进程继承本环境：非交互流默认块缓冲，日志会滞留缓冲区 → 强制无缓冲
    os.environ.setdefault("PYTHONUNBUFFERED", "1")


def _creationflags_silent() -> int:
    """静默模式下子进程不弹出新控制台窗口（Windows CREATE_NO_WINDOW）。"""
    if LINUX is False and os.environ.get("ACP_SILENT") == "1":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0) or 0x08000000
    return 0


# ---------------------------------------------------------------- 工具
def log(msg: str, level: str = "INFO") -> None:
    tag = {"INFO": "◆", "OK": "✔", "WARN": "⚠", "ERR": "✘", "STEP": "▶"}.get(level, "◆")
    print(f"  {tag} {msg}", flush=True)


def banner(msg: str) -> None:
    print("\n" + "=" * 62, flush=True)
    print(f"  {msg}", flush=True)
    print("=" * 62, flush=True)


def venv_python() -> Path:
    return VENV_DIR / ("Scripts/python.exe" if LINUX is False else "bin/python")


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    if LINUX is False:
        kw.setdefault("creationflags", _creationflags_silent())
    return subprocess.run(cmd, **kw)


def port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) != 0


def pick_port(host: str, preferred: int, try_count: int = 10) -> int:
    for p in range(preferred, preferred + try_count):
        if port_free(host, p):
            return p
    return preferred


# ---------------------------------------------------------------- 1. 环境校验
def check_python() -> None:
    print("\n[1/6] 环境校验", flush=True)
    py = sys.version_info
    if (py.major, py.minor) < PYTHON_MIN:
        log(f"Python {py.major}.{py.minor} 过旧，需要 {PYTHON_MIN[0]}.{PYTHON_MIN[1]}+", "ERR")
        sys.exit(1)
    log(f"Python {py.major}.{py.minor}.{py.micro} OK")


def check_node() -> str | None:
    npm = shutil.which("npm")
    if not npm:
        log("未检测到 Node.js / npm —— 前端将跳过，仅启动后端（用 {BACKEND}/docs 或前端构建产物）", "WARN")
        return None
    log(f"Node/npm OK（{npm}）")
    return npm


def check_ports(host: str, backend_port: int, frontend_port: int) -> tuple[int, int]:
    bp = pick_port(host, backend_port)
    log(f"后端端口 {backend_port} -> {bp}" + ("" if bp == backend_port else "（原端口被占用，自动顺延）"))
    fp = pick_port(host, frontend_port)
    if fp != frontend_port:
        log(f"前端端口 {frontend_port} -> {fp}（原端口被占用，自动顺延）")
    return bp, fp


# ---------------------------------------------------------------- 2. 虚拟环境自举
def ensure_venv() -> bool:
    """返回 True 表示当前已运行在自建 venv 内。"""
    if VENV_DIR.exists() and venv_python().exists():
        if sys.prefix and str(VENV_DIR).lower() in str(Path(sys.prefix).resolve()).lower():
            return True
        return False

    print("\n[2/6] 虚拟环境自举", flush=True)
    log(f"创建虚拟环境 {VENV_DIR} ...")
    try:
        r = run([sys.executable, "-m", "venv", str(VENV_DIR)])
        if r.returncode != 0 or not venv_python().exists():
            run([sys.executable, "-m", "venv", "--without-pip", str(VENV_DIR)])
        # 确保 pip 可用（ensurepip 失败时降级到系统 pip 引导）
        if run([str(venv_python()), "-m", "pip", "--version"]).returncode != 0:
            r2 = run([str(venv_python()), "-m", "ensurepip", "--default-pip", "--upgrade"])
            if r2.returncode != 0:
                run([sys.executable, "-m", "pip", "--python", str(venv_python()),
                     "install", "-U", "pip"])
        if run([str(venv_python()), "-m", "pip", "--version"]).returncode != 0:
            log("pip 引导失败：请手动执行  python -m pip install -U pip", "ERR")
            sys.exit(1)
        log("虚拟环境创建完成")
    except Exception as exc:  # noqa: BLE001
        log(f"虚拟环境创建失败: {exc}", "ERR")
        sys.exit(1)
    return False


def deps_ready() -> bool:
    """快速校验核心依赖是否已可用（不触网）。"""
    probe = (
        "import fastapi, sqlalchemy, httpx, jwt, docx, openpyxl, uvicorn, multipart"
    )
    r = run([str(venv_python()), "-c", probe], capture_output=True)
    return r.returncode == 0


def ensure_deps() -> None:
    print("[3/6] 依赖检查与安装", flush=True)
    if deps_ready():
        DEPS_STAMP.write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
        log("依赖已就绪，跳过安装")
        return
    log("安装后端依赖（首次约 1-2 分钟）...")
    index = os.environ.get("ACP_PIP_INDEX", "https://pypi.org/simple")
    r = run([str(venv_python()), "-m", "pip", "install", "-i", index,
             "-r", str(REQ_FILE)], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-1500:], r.stderr[-1500:], flush=True)
        log("依赖安装失败，可设置 ACP_PIP_INDEX 指定镜像源后重试", "ERR")
        sys.exit(1)
    DEPS_STAMP.write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
    log("依赖安装完成")


def ensure_env_file() -> None:
    if ENV_FILE.exists():
        log("检测到 backend/.env，使用现有配置", "OK")
        return
    if ENV_TEMPLATE.exists():
        shutil.copyfile(ENV_TEMPLATE, ENV_FILE)
        log("已从 .env.example 生成 backend/.env（模型 Key / 端口 / 超时 / 批量参数均可在此修改）")


# ---------------------------------------------------------------- 3. 应用启动（venv 内）
def app_bootstrap(args) -> None:
    """以下代码运行在 venv 解释器内：加载配置、初始化数据库、检查模型链。"""
    backend_port = args.backend_port
    frontend_port = args.frontend_port or 5173
    host = args.host

    from app.core.logging import get_logger  # noqa: PLC0415
    from app.db.database import init_db  # noqa: PLC0415
    from app.services.llm.router import router  # noqa: PLC0415

    log("加载配置 ...", "STEP")
    from app.config import settings  # noqa: PLC0415
    log(f"配置加载完成：Provider 链 {settings.provider_chain} · 模型 {settings.OLLAMA_MODEL}")

    log("初始化数据库 ...", "STEP")
    init_db()
    log(f"数据库就绪（{settings.DATABASE_URL.split('///')[-1]}）", "OK")

    log("模型链健康检查 ...", "STEP")
    status = router.status()
    for p in status["providers"]:
        log(f"  {p['provider']:<8} {'✓ 可用' if p['ok'] else '✗ 不可用'}  {p['detail']}")
    if status["active_provider"]:
        log(f"当前主推理 Provider：{status['active_provider']}", "OK")
    else:
        log("全部 Provider 不可用：请检查 Ollama（ollama serve）或配置云端 Key；当前仍可用 Mock 演示模式", "WARN")

    # ---------- 启动前端（子进程） ----------
    frontend_proc = None
    npm = None if args.no_frontend else check_node()
    if npm:
        print("[5/6] 前端服务", flush=True)
        if not (FRONTEND_DIR / "node_modules").exists():
            log("首次运行：安装前端依赖 npm install ...")
            reg = os.environ.get("ACP_NPM_REGISTRY", "https://registry.npmmirror.com")
            r = run(f'"{npm}" install --registry={reg} --no-audit --no-fund', shell=True, cwd=FRONTEND_DIR)
            if r.returncode != 0:
                log("前端依赖安装失败，跳过前端（可到 frontend/ 目录手动 npm install）", "WARN")
            else:
                log("前端依赖安装完成")
        if (FRONTEND_DIR / "node_modules").exists():
            cmd = (f'"{npm}" run dev -- --host {host} --port {frontend_port}')
            log(f"启动前端（http://{host}:{frontend_port or 5173}，被占用时 Vite 自动顺延）...")
            frontend_proc = subprocess.Popen(
                cmd, shell=True, cwd=FRONTEND_DIR,
                creationflags=_creationflags_silent() if LINUX is False else 0,
            )
            _wait_http(f"http://{host}:{frontend_port}", tries=40)
            if frontend_proc.poll() is not None:
                log("前端启动失败（端口冲突或编译错误请查看上方日志），继续仅启动后端", "WARN")
                frontend_proc = None

    # ---------- 启动后端 ----------
    print("[6/6] 后端服务", flush=True)
    backend_url = f"http://{host}:{backend_port}"
    log(f"FastAPI 启动：{backend_url}  ·  接口文档 {backend_url}/docs")

    def open_browser() -> None:
        if args.no_browser:
            return
        time.sleep(2.5)
        target = backend_url if frontend_proc is None or frontend_port is None else f"http://{host}:{frontend_port}"
        try:
            webbrowser.open(target)
        except Exception:  # noqa: BLE001
            pass

    threading.Thread(target=open_browser, daemon=True).start()
    try:
        import uvicorn  # noqa: PLC0415
        uvicorn.run("app.main:app", host=host, port=backend_port, log_level="info")
    except KeyboardInterrupt:
        log("收到退出信号，正在关闭 ...", "WARN")
    finally:
        if frontend_proc and frontend_proc.poll() is None:
            _kill_tree(frontend_proc)
        log("服务已全部退出，感谢使用 👋", "OK")


def _wait_http(url: str, tries: int = 20, interval: float = 1.0) -> None:
    for _ in range(tries):
        try:
            urllib.request.urlopen(url, timeout=1.5)
            return
        except (urllib.error.URLError, OSError):
            time.sleep(interval)


def _kill_tree(proc: subprocess.Popen) -> None:
    try:
        if LINUX is False:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           capture_output=True, shell=True,
                           creationflags=_creationflags_silent())
        else:
            proc.terminate()
    except Exception:  # noqa: BLE001
        try:
            proc.terminate()
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------- 4. 体检模式
def check_only(args) -> None:
    banner("环境体检")
    check_python()
    npm = check_node()
    print("-" * 62)
    log(f"后端端口 {args.backend_port} 空闲：{'是' if port_free(args.host, args.backend_port) else '否（将被顺延）'}")
    if npm and port_free(args.host, args.frontend_port or 5173):
        log(f"前端端口 {args.frontend_port or 5173} 空闲：是")
    print("-" * 62)
    if (VENV_DIR / "Scripts/python.exe").exists() or (VENV_DIR / "bin/python").exists():
        log("虚拟环境 .venv 已存在", "OK")
    else:
        log("虚拟环境 .venv 不存在（启动时将自动创建）", "WARN")
    if ENV_FILE.exists():
        log("配置文件 backend/.env 已存在", "OK")
    else:
        log("配置文件 backend/.env 不存在（启动时将自动生成）", "WARN")
    if LINUX is False:
        log("Ollama 探测：", "STEP")
        try:
            import socket as _s
            s = _s.create_connection(("127.0.0.1", 11434), timeout=1.5)
            s.close()
            log("  Ollama 服务运行中 ✓（模型链首选）")
        except OSError:
            log("  Ollama 未运行（系统将自动降级到云端/Mock 演示模式）", "WARN")
    banner("体检完成")


# ---------------------------------------------------------------- 入口
def main() -> None:
    if hasattr(sys, "frozen"):
        print("直接运行 start.py 即可", flush=True)
    parser = argparse.ArgumentParser(description="AI 内容工场 一键启动器")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址（默认 127.0.0.1）")
    parser.add_argument("--port", dest="backend_port", type=int, default=8000, help="后端端口（默认 8000）")
    parser.add_argument("--frontend-port", dest="frontend_port", type=int, default=5173, help="前端端口（默认 5173）")
    parser.add_argument("--no-frontend", action="store_true", help="仅启动后端，不拉起前端")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    parser.add_argument("--check", action="store_true", help="仅环境体检")
    args = parser.parse_args()

    banner("AI 内容工场 · 一键启动器")

    check_python()
    if args.check:
        check_only(args)
        sys.exit(0)

    if not ensure_venv():
        # 主进程完成引导后，切到 venv 解释器重新执行本脚本
        log("切换到虚拟环境解释器 ...")
        # 静默模式：子进程无控制台时 stdio 不可信，显式重定向到日志文件（append + 行缓冲）
        _spawn_kwargs: dict = {}
        if os.environ.get("ACP_SILENT") == "1":
            _log_dir = BASE_DIR / "logs"
            _log_dir.mkdir(parents=True, exist_ok=True)
            _spawn_kwargs = {
                "stdout": open(_log_dir / "launcher.log", "a", encoding="utf-8", buffering=1),
                "stderr": subprocess.STDOUT,
            }
        r = run([str(venv_python()), str(Path(__file__).resolve()), *sys.argv[1:]],
                **_spawn_kwargs)
        sys.exit(r.returncode)

    ensure_deps()
    ensure_env_file()

    # ---------- 运行前端口规划 ----------
    backend_port, frontend_port = check_ports(args.host, args.backend_port, args.frontend_port or 5173)
    args.backend_port = backend_port
    args.frontend_port = frontend_port
    if not args.no_frontend and frontend_port != args.frontend_port:
        log("前端端口被占用，改为自动顺延端口运行", "WARN")

    banner("AI 内容工场 启动中")
    app_bootstrap(args)


if __name__ == "__main__":
    main()
