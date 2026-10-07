"""Các tool đọc, ghi và liệt kê file trong workspace."""

from __future__ import annotations

import json
from pathlib import Path

from langchain_core.tools import tool

import paths

MAX_READ_BYTES = 200_000


def _error(code: str, message: str) -> dict:
    return {
        "ok": False,
        "error": {"code": code, "message": message},
    }


def _resolve(workspace: Path, path: str) -> tuple[Path | None, dict | None]:
    raw = (path or "").strip()

    if not raw:
        return None, _error(
            "INVALID_PATH",
            "Path rỗng. Dùng đường dẫn tương đối workspace.",
        )

    if Path(raw).is_absolute() or raw.startswith("~"):
        return None, _error(
            "PATH_OUTSIDE_WORKSPACE",
            f"Không chấp nhận đường dẫn tuyệt đối: {raw}",
        )

    root = workspace.resolve()
    target = (root / raw).resolve()

    if not target.is_relative_to(root):
        return None, _error(
            "PATH_OUTSIDE_WORKSPACE",
            f"Đường dẫn thoát ra ngoài workspace: {raw}",
        )

    return target, None


def _read(workspace: Path, path: str) -> dict:
    target, error = _resolve(workspace, path)
    if error:
        return error

    rel = target.relative_to(workspace.resolve()).as_posix()

    if not target.exists():
        return _error("FILE_NOT_FOUND", f"Không tìm thấy file: {rel}")

    if target.is_dir():
        return _error(
            "IS_A_DIRECTORY",
            f"Đây là thư mục, không phải file: {rel}",
        )

    size = target.stat().st_size
    if size > MAX_READ_BYTES:
        return _error(
            "FILE_TOO_LARGE",
            f"File {rel} có {size} bytes, vượt giới hạn "
            f"{MAX_READ_BYTES} bytes. Không đọc một phần.",
        )

    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return _error(
            "NOT_UTF8_TEXT",
            f"File {rel} không phải văn bản UTF-8.",
        )

    return {"ok": True, "path": rel, "content": content}


def _write(workspace: Path, path: str, content: str) -> dict:
    target, error = _resolve(workspace, path)
    if error:
        return error

    output_root = (workspace / paths.OUTPUT_SUBDIR).resolve()

    if not target.is_relative_to(output_root) or target == output_root:
        return _error(
            "PATH_OUTSIDE_OUTPUT",
            f"Chỉ được ghi file dưới {paths.OUTPUT_SUBDIR}/. "
            f"Path nhận được: {path}",
        )

    rel = target.relative_to(workspace.resolve()).as_posix()

    if target.is_dir():
        return _error(
            "IS_A_DIRECTORY",
            f"Đây là thư mục, không ghi đè được: {rel}",
        )

    status = "updated" if target.exists() else "created"
    target.parent.mkdir(parents=True, exist_ok=True)

    if not target.parent.resolve().is_relative_to(output_root):
        return _error(
            "PATH_OUTSIDE_OUTPUT",
            f"Thư mục đích thoát khỏi {paths.OUTPUT_SUBDIR}/: {path}",
        )

    data = content.encode("utf-8")
    target.write_bytes(data)

    return {
        "ok": True,
        "path": rel,
        "bytes": len(data),
        "status": status,
    }


def _list(workspace: Path, path: str) -> dict:
    """Liệt kê trực tiếp; chặn symlink dẫn ra ngoài workspace."""
    try:
        target, error = _resolve(workspace, path)
        if error:
            return error

        root = workspace.resolve()
        rel = target.relative_to(root).as_posix()

        if not target.exists():
            return _error(
                "DIRECTORY_NOT_FOUND",
                f"Không tìm thấy thư mục: {rel}",
            )

        if not target.is_dir():
            return _error(
                "NOT_A_DIRECTORY",
                f"Đường dẫn không phải thư mục: {rel}",
            )

        entries = []

        for child in sorted(target.iterdir(), key=lambda p: p.name):
            child_path = child.relative_to(root).as_posix()
            resolved, error = _resolve(workspace, child_path)

            if error:
                return error

            if not resolved.exists():
                return _error(
                    "BROKEN_SYMLINK",
                    f"Liên kết không có đích: {child.name}",
                )

            if not (resolved.is_dir() or resolved.is_file()):
                return _error(
                    "UNSUPPORTED_ENTRY",
                    f"Mục không phải file/thư mục: {child.name}",
                )

            entries.append({
                "name": child.name,
                "path": child_path,
                "type": "directory" if resolved.is_dir() else "file",
            })

        return {"ok": True, "path": rel, "entries": entries}

    except (OSError, RuntimeError, ValueError):
        return _error(
            "DIRECTORY_ACCESS_ERROR",
            "Không thể liệt kê thư mục; kiểm tra quyền truy cập và liên kết.",
        )


@tool
def read_file(path: str) -> str:
    """Đọc một file văn bản UTF-8 trong workspace và trả về JSON.

    path là đường dẫn tương đối workspace.
    Dùng để đọc dữ liệu đầu vào, SKILL.md và các file reference.

    QUY TẮC ĐỌC SKILL:
    - Các mục trong available_skills là tài liệu, không phải tool.
    - Muốn sử dụng skill, gọi tool read_file.
    - Truyền location của skill vào tham số path.
    - Không gọi tên skill như một tên tool.
    - Ví dụ: skill abc có location skills/abc/SKILL.md thì gọi
      read_file(path="skills/abc/SKILL.md"), không gọi abc(...).
    - Sau khi đọc thành công, thực hiện hướng dẫn trong nội dung file.

    Thành công: {"ok": true, "path": ..., "content": ...}.
    Lỗi: {"ok": false, "error": {"code": ..., "message": ...}}.
    """
    return json.dumps(
        _read(paths.WORKSPACE_DIR, path),
        ensure_ascii=False,
    )


@tool
def write_file(path: str, content: str) -> str:
    """Ghi văn bản UTF-8 vào một file dưới output/ của workspace.

    path là đường dẫn tương đối workspace, ví dụ output/summary.md.
    Tự tạo thư mục con. Ghi đè nếu file đã tồn tại.
    Thành công: {"ok": true, "path": ..., "bytes": ..., "status": ...}.
    Lỗi: {"ok": false, "error": {"code": ..., "message": ...}}.
    """
    return json.dumps(
        _write(paths.WORKSPACE_DIR, path, content),
        ensure_ascii=False,
    )


@tool
def list_files(path: str) -> str:
    """Liệt kê các mục trực tiếp trong thư mục để tìm file trước khi đọc.

    path tương đối workspace; dùng "." để liệt kê gốc.
    Không duyệt đệ quy. Kết quả sắp xếp theo tên.
    Mỗi mục có name, path tương đối workspace và type: file hoặc directory.
    Chỉ truy cập trong workspace, chặn symlink dẫn ra ngoài.
    Dùng đường dẫn tìm được làm tham số path cho tool read_file.

    Thành công: {"ok": true, "path": ..., "entries": [...]}.
    Lỗi: {"ok": false, "error": {"code": ..., "message": ...}}.
    """
    return json.dumps(
        _list(paths.WORKSPACE_DIR, path),
        ensure_ascii=False,
    )