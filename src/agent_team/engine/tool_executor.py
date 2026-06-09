"""Bash/Read/Write 工具执行器"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from agent_team.exceptions import ToolExecutionError


# 只读命令白名单（READ_BASH 权限）
READ_ONLY_PREFIXES = frozenset(
    {
        "ls",
        "cat",
        "head",
        "tail",
        "find",
        "grep",
        "rg",
        "fd",
        "git log",
        "git diff",
        "git show",
        "git status",
        "git branch",
        "git blame",
        "wc",
        "file",
        "stat",
        "tree",
        "pwd",
        "echo",
        "which",
        "env",
        "printenv",
        "whoami",
        "date",
        "uname",
        "du",
        "df",
        "sort",
        "uniq",
        "cut",
        "tr",
        "awk",
        "sed",  # sed without -i is read-only
        "diff",
        "md5sum",
        "sha256sum",
        "python --version",
        "python3 --version",
        "node --version",
        "npm --version",
        "pip list",
        "pip show",
        "uv",
        "cargo --version",
        "go version",
    }
)


class ToolExecutor:
    """工具执行器"""

    def __init__(self, working_dir: str | None = None):
        self.working_dir = working_dir or os.getcwd()

    async def execute(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """执行工具调用"""
        if tool_name == "bash":
            return await self._execute_bash(tool_input.get("command", ""))
        elif tool_name == "read_file":
            return self._execute_read(tool_input.get("path", ""), tool_input.get("offset", 0), tool_input.get("limit", 2000))
        elif tool_name == "write_file":
            return self._execute_write(tool_input.get("path", ""), tool_input.get("content", ""))
        else:
            raise ToolExecutionError(f"未知工具: {tool_name}")

    async def _execute_bash(self, command: str) -> str:
        """执行 Bash 命令"""
        if not command.strip():
            return "(空命令)"

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

            output_parts: list[str] = []
            if stdout:
                output_parts.append(stdout.decode("utf-8", errors="replace"))
            if stderr:
                output_parts.append(f"[stderr]\n{stderr.decode('utf-8', errors='replace')}")
            if proc.returncode != 0:
                output_parts.append(f"[exit code: {proc.returncode}]")

            result = "\n".join(output_parts) if output_parts else "(无输出)"

            # 截断过长输出
            if len(result) > 50000:
                result = result[:50000] + f"\n\n... (输出已截断，共 {len(result)} 字符)"

            return result

        except asyncio.TimeoutError:
            return "[错误] 命令执行超时（60秒）"
        except Exception as e:
            return f"[错误] 命令执行失败: {e}"

    def _execute_read(self, path: str, offset: int = 0, limit: int = 2000) -> str:
        """读取文件内容"""
        try:
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = Path(self.working_dir) / file_path

            if not file_path.is_file():
                return f"[错误] 文件不存在: {path}"

            with open(file_path, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            total = len(lines)
            selected = lines[offset : offset + limit]
            content = "".join(selected)

            if offset + limit < total:
                content += f"\n\n... (显示 {offset+1}-{min(offset+limit, total)} 行，共 {total} 行)"

            return content

        except Exception as e:
            return f"[错误] 读取文件失败: {e}"

    def _execute_write(self, path: str, content: str) -> str:
        """写入文件"""
        try:
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = Path(self.working_dir) / file_path

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

            return f"文件已写入: {file_path} ({len(content)} 字符)"

        except Exception as e:
            return f"[错误] 写入文件失败: {e}"


def is_read_only_command(command: str) -> bool:
    """检查命令是否为只读命令"""
    stripped = command.strip()
    if not stripped:
        return True

    # 检查管道中的每个命令
    # 简化处理：检查第一个 token
    first_token = stripped.split()[0]

    # 特殊处理 git 子命令
    if first_token == "git" and len(stripped.split()) > 1:
        git_cmd = f"git {stripped.split()[1]}"
        return git_cmd in READ_ONLY_PREFIXES

    return first_token in READ_ONLY_PREFIXES
