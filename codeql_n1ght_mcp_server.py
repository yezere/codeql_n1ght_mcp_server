import asyncio
import logging
import os
from typing import List, Optional, Dict, Any

from mcp.server import FastMCP

# 注意：STDIO 模式下不要向 stdout 打印任何非协议内容，使用 logging（写入 stderr）记录日志
logging.basicConfig(level=logging.INFO)

APP_NAME = "codeql_n1ght_mcp"
# 默认可执行文件路径（兼容传入 "/j:/mcp/codeql-n1ght.exe" 的写法）
EXE_PATH = r"J:\\mcp\\codeql-n1ght.exe"

app = FastMCP(APP_NAME)


def _resolve_exe_path(custom_path: Optional[str]) -> str:
    """返回可执行文件的绝对路径，优先使用传入路径。兼容类似 "/j:/mcp/codeql-n1ght.exe" 的写法。"""
    path = (custom_path or EXE_PATH).strip()
    if path.startswith("/") and len(path) > 2 and path[2] == ":":
        path = path[1:]
    return os.path.abspath(path)


async def _run_subprocess(cmd: List[str], cwd: Optional[str], timeout: Optional[float]) -> Dict[str, Any]:
    """以异步方式运行子进程，捕获 stdout/stderr，返回 {returncode, stdout, stderr, timeout}."""
    logging.info("Running command: %s", " ".join(cmd))
    if cwd:
        logging.info("Working directory: %s", cwd)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        timed_out = False
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        return {
            "returncode": None,
            "stdout": "",
            "stderr": f"Process timeout after {timeout} seconds",
            "timeout": True,
        }

    stdout = stdout_b.decode(errors="replace") if stdout_b else ""
    stderr = stderr_b.decode(errors="replace") if stderr_b else ""

    return {
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "timeout": timed_out,
    }


@app.tool()
async def run_codeql_n1ght(
    args: Optional[List[str]] = None,
    exe_path: Optional[str] = None,
    cwd: Optional[str] = None,
    timeout_seconds: Optional[float] = 600.0,
) -> Dict[str, Any]:
    """
    通用执行接口：直接传入参数数组，运行 codeql-n1ght.exe。

    - args 例如：["-install"]、["-database", "your.jar", "-decompiler", "fernflower"] 等。
    - exe_path 可选，覆盖默认可执行路径。
    - cwd 可选，子进程工作目录。
    - timeout_seconds 超时（秒）。
    """
    resolved_path = _resolve_exe_path(exe_path)
    if not os.path.exists(resolved_path):
        return {
            "returncode": None,
            "stdout": "",
            "stderr": f"Executable not found: {resolved_path}",
            "timeout": False,
        }

    args = args or []
    cmd = [resolved_path, *args]
    return await _run_subprocess(cmd, cwd=cwd, timeout=timeout_seconds)


@app.tool()
async def version(
    exe_path: Optional[str] = None,
    timeout_seconds: Optional[float] = 60.0,
) -> Dict[str, Any]:
    """获取可执行文件版本或帮助信息：先尝试 --version，失败回退 --help。"""
    resolved_path = _resolve_exe_path(exe_path)
    if not os.path.exists(resolved_path):
        return {
            "returncode": None,
            "stdout": "",
            "stderr": f"Executable not found: {resolved_path}",
            "timeout": False,
        }

    # 先尝试 --version
    res = await _run_subprocess([resolved_path, "--version"], cwd=None, timeout=timeout_seconds)
    if res.get("returncode") == 0 and res.get("stdout"):
        return res

    # 回退 --help
    return await _run_subprocess([resolved_path, "--help"], cwd=None, timeout=timeout_seconds)


@app.tool()
async def install_environment(
    jdk_url: Optional[str] = None,
    ant_url: Optional[str] = None,
    codeql_url: Optional[str] = None,
    exe_path: Optional[str] = None,
    cwd: Optional[str] = None,
    timeout_seconds: Optional[float] = 3600.0,
) -> Dict[str, Any]:
    """
    一键安装环境：等价于命令行
      ./codeql_n1ght -install [-jdk <url>] [-ant <url>] [-codeql <url>]
    """
    resolved_path = _resolve_exe_path(exe_path)
    if not os.path.exists(resolved_path):
        return {
            "returncode": None,
            "stdout": "",
            "stderr": f"Executable not found: {resolved_path}",
            "timeout": False,
        }

    args: List[str] = ["-install"]
    if jdk_url:
        args += ["-jdk", jdk_url]
    if ant_url:
        args += ["-ant", ant_url]
    if codeql_url:
        args += ["-codeql", codeql_url]

    return await _run_subprocess([resolved_path, *args], cwd=cwd, timeout=timeout_seconds)


@app.tool()
async def create_database(
    target: str,
    decompiler: Optional[str] = None,  # procyon | fernflower
    extra_src_dir: Optional[str] = None,  # -dir
    deps: Optional[str] = None,  # none | all | None(进入交互TUI)
    goroutine: bool = False,  # -goroutine
    max_goroutines: Optional[int] = None,  # -max-goroutines N
    threads: Optional[int] = None,  # -threads N
    clean_cache: bool = False,  # -clean-cache
    exe_path: Optional[str] = None,
    cwd: Optional[str] = None,
    timeout_seconds: Optional[float] = 72000.0,
) -> Dict[str, Any]:
    """
    创建 CodeQL 数据库：等价命令
      ./codeql_n1ght -database <JAR|WAR|ZIP> [-decompiler procyon|fernflower] [-dir <path>] [-deps none|all] 
                     [-goroutine] [-max-goroutines N] [-threads N] [-clean-cache]
    """
    resolved_path = _resolve_exe_path(exe_path)
    if not os.path.exists(resolved_path):
        return {
            "returncode": None,
            "stdout": "",
            "stderr": f"Executable not found: {resolved_path}",
            "timeout": False,
        }

    args: List[str] = ["-database", target]

    if decompiler:
        dec = decompiler.lower().strip()
        if dec not in {"procyon", "fernflower"}:
            return {
                "returncode": None,
                "stdout": "",
                "stderr": f"Invalid decompiler: {decompiler}. Expected 'procyon' or 'fernflower'",
                "timeout": False,
            }
        args += ["-decompiler", dec]

    if extra_src_dir:
        args += ["-dir", extra_src_dir]

    if deps:
        d = deps.lower().strip()
        if d not in {"none", "all"}:
            return {
                "returncode": None,
                "stdout": "",
                "stderr": f"Invalid deps: {deps}. Expected 'none' or 'all' or leave empty to use interactive TUI",
                "timeout": False,
            }
        args += ["-deps", d]

    # 新增：并行与缓存控制参数
    if goroutine:
        args += ["-goroutine"]
    if isinstance(max_goroutines, int):
        args += ["-max-goroutines", str(max_goroutines)]
    if isinstance(threads, int):
        args += ["-threads", str(threads)]
    if clean_cache:
        args += ["-clean-cache"]

    return await _run_subprocess([resolved_path, *args], cwd=cwd, timeout=timeout_seconds)


@app.tool()
async def scan_database(
    db: Optional[str] = None,
    ql: Optional[str] = None,
    goroutine: bool = False,
    max_goroutines: Optional[int] = None,
    threads: Optional[int] = None,
    clean_cache: bool = False,
    exe_path: Optional[str] = None,
    cwd: Optional[str] = None,
    timeout_seconds: Optional[float] = 720000.0,
) -> Dict[str, Any]:
    """
    执行安全扫描：等价命令
      ./codeql_n1ght -scan [-db <path>] [-ql <path>] [-goroutine] [-max-goroutines N] [-threads N] [-clean-cache]
    """
    resolved_path = _resolve_exe_path(exe_path)
    if not os.path.exists(resolved_path):
        return {
            "returncode": None,
            "stdout": "",
            "stderr": f"Executable not found: {resolved_path}",
            "timeout": False,
        }

    args: List[str] = ["-scan"]
    if db:
        args += ["-db", db]
    if ql:
        args += ["-ql", ql]
    if goroutine:
        args += ["-goroutine"]
    if isinstance(max_goroutines, int):
        args += ["-max-goroutines", str(max_goroutines)]
    if isinstance(threads, int):
        args += ["-threads", str(threads)]
    if clean_cache:
        args += ["-clean-cache"]

    return await _run_subprocess([resolved_path, *args], cwd=cwd, timeout=timeout_seconds)


if __name__ == "__main__":
    # 以 STDIO 方式启动 MCP 服务
    print("MCP server started in STDIO mode")
    app.run(transport="stdio")