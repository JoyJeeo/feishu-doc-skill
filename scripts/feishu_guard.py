#!/usr/bin/env python3
"""Deterministic local guards for the Feishu document skill. No network access."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


class GuardError(ValueError):
    """Raised when a requested action violates a skill invariant."""


RESOURCE_SEGMENTS = {
    "docx": "docx",
    "sheets": "sheets",
    "base": "bitable",
    "wiki": "wiki",
    "drive": "drive",
    "file": "drive",
    "minutes": "minutes",
    "board": "board",
    "slides": "slides",
    "mindnote": "mindnote",
    "mindnotes": "mindnote",
}
RESOURCE_TYPES = set(RESOURCE_SEGMENTS.values())
MODES = {"analyze", "preview", "apply", "verify"}
WRITE_OPERATIONS = {"create", "append", "insert", "replace", "move", "update"}
DISABLED_OPERATIONS = {"delete", "transfer_owner", "public_permission_change"}
PREVIEW_FIELDS = {
    "target",
    "resource_type",
    "operation",
    "scope",
    "changes",
    "before_state",
    "required_tools",
    "verification",
}
PREVIEW_OUTPUT_FIELDS = PREVIEW_FIELDS - {"before_state"} | {
    "preview_id",
    "identity",
    "application_identity_explicit",
    "before_fingerprint",
    "risks",
    "status",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def classify_feishu_url(url: str) -> dict[str, str]:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (host == "feishu.cn" or host.endswith(".feishu.cn")):
        raise GuardError("只支持 HTTPS 飞书中国版链接")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2 or parts[0] not in RESOURCE_SEGMENTS:
        raise GuardError("无法识别飞书资源类型或资源 Token")

    token_index = 2 if parts[0] == "drive" and len(parts) > 2 and parts[1] in {"folder", "file"} else 1
    if len(parts) <= token_index:
        raise GuardError("飞书资源链接缺少 Token")

    return {
        "resource_type": RESOURCE_SEGMENTS[parts[0]],
        "token": parts[token_index],
        "host": host,
    }


def identity_parameters(identity: str = "user", *, explicit_application: bool = False) -> dict[str, Any]:
    if identity == "user":
        return {"identity": "user", "useUAT": True}
    if identity == "application" and explicit_application:
        return {"identity": "application", "useUAT": False}
    if identity == "application":
        raise GuardError("应用身份需要用户明确指定，禁止自动降级")
    raise GuardError(f"不支持的身份：{identity}")


def validate_mode(mode: str, *, mutating: bool = False) -> None:
    if mode not in MODES:
        raise GuardError(f"不支持的模式：{mode}")
    if mutating and mode != "apply":
        raise GuardError(f"{mode} 模式禁止写入")


def validate_feishu_tool(tool_name: str) -> None:
    if not isinstance(tool_name, str) or not tool_name.startswith("mcp__feishu__"):
        raise GuardError("飞书远端操作只允许使用 mcp__feishu__ 工具")


def missing_tools(required: Iterable[str], available: Iterable[str]) -> list[str]:
    required_set = set(required)
    for tool_name in required_set:
        validate_feishu_tool(tool_name)
    return sorted(required_set - set(available))


def _preview_payload(preview: dict[str, Any]) -> dict[str, Any]:
    return {
        "target": preview["target"],
        "resource_type": preview["resource_type"],
        "identity": preview["identity"],
        "application_identity_explicit": preview["application_identity_explicit"],
        "operation": preview["operation"],
        "scope": preview["scope"],
        "before_fingerprint": preview["before_fingerprint"],
        "changes": preview["changes"],
        "risks": preview["risks"],
        "required_tools": preview["required_tools"],
        "verification": preview["verification"],
    }


def make_preview(spec: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(PREVIEW_FIELDS - spec.keys())
    if missing:
        raise GuardError(f"预览缺少字段：{', '.join(missing)}")

    if not isinstance(spec["target"], str) or not spec["target"].strip():
        raise GuardError("预览目标不能为空")
    if not isinstance(spec["resource_type"], str) or spec["resource_type"] not in RESOURCE_TYPES:
        raise GuardError(f"不支持的资源类型：{spec['resource_type']}")
    if not isinstance(spec["required_tools"], list) or not spec["required_tools"]:
        raise GuardError("required_tools 必须是非空数组")

    operation = spec["operation"]
    if not isinstance(operation, str):
        raise GuardError("写入操作必须是字符串")
    if operation in DISABLED_OPERATIONS:
        raise GuardError(f"操作默认关闭：{operation}")
    if operation not in WRITE_OPERATIONS:
        raise GuardError(f"不支持的写入操作：{operation}")

    identity = spec.get("identity", "user")
    explicit_application = bool(spec.get("application_identity_explicit", False))
    identity_parameters(identity, explicit_application=explicit_application)

    required_tools = sorted(set(spec["required_tools"]))
    for tool_name in required_tools:
        validate_feishu_tool(tool_name)

    preview = {
        "target": spec["target"],
        "resource_type": spec["resource_type"],
        "identity": identity,
        "application_identity_explicit": explicit_application,
        "operation": operation,
        "scope": spec["scope"],
        "before_fingerprint": fingerprint(spec["before_state"]),
        "changes": spec["changes"],
        "risks": spec.get("risks", []),
        "required_tools": required_tools,
        "verification": spec["verification"],
        "status": "pending_confirmation",
    }
    preview["preview_id"] = "fs-" + fingerprint(_preview_payload(preview))[:16]
    return preview


def validate_preview(
    preview: dict[str, Any],
    current_state: Any,
    confirmed_preview_id: str,
    available_tools: Iterable[str],
    applied_preview_ids: Iterable[str] = (),
) -> dict[str, Any]:
    validate_mode("apply", mutating=True)

    missing = sorted(PREVIEW_OUTPUT_FIELDS - preview.keys())
    if missing:
        raise GuardError(f"预览缺少字段：{', '.join(missing)}")
    if preview.get("status") != "pending_confirmation":
        raise GuardError("预览状态不是 pending_confirmation")
    if preview.get("preview_id") != confirmed_preview_id:
        raise GuardError("用户确认的 preview_id 与待执行预览不一致")
    if preview.get("preview_id") in set(applied_preview_ids):
        raise GuardError("该预览已经执行，禁止重复写入")
    operation = preview["operation"]
    if not isinstance(operation, str):
        raise GuardError("写入操作必须是字符串")
    if operation in DISABLED_OPERATIONS:
        raise GuardError(f"操作默认关闭：{operation}")
    if operation not in WRITE_OPERATIONS:
        raise GuardError(f"不支持的写入操作：{operation}")
    if not isinstance(preview["resource_type"], str) or preview["resource_type"] not in RESOURCE_TYPES:
        raise GuardError(f"不支持的资源类型：{preview['resource_type']}")
    if not isinstance(preview["required_tools"], list) or not preview["required_tools"]:
        raise GuardError("required_tools 必须是非空数组")

    identity_parameters(
        preview.get("identity", "user"),
        explicit_application=bool(preview.get("application_identity_explicit", False)),
    )

    expected_id = "fs-" + fingerprint(_preview_payload(preview))[:16]
    if expected_id != preview.get("preview_id"):
        raise GuardError("预览内容已被修改")
    if fingerprint(current_state) != preview.get("before_fingerprint"):
        raise GuardError("目标在预览后发生变化，必须重新生成预览")

    unavailable = missing_tools(preview.get("required_tools", []), available_tools)
    if unavailable:
        raise GuardError(f"缺少飞书 MCP 工具：{', '.join(unavailable)}")

    return {
        "valid": True,
        "preview_id": preview["preview_id"],
        "identity": preview["identity"],
        "operation": preview["operation"],
    }


def load_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open(encoding="utf-8") as file:
        return json.load(file)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    classify = commands.add_parser("classify-url")
    classify.add_argument("url")

    identity = commands.add_parser("identity")
    identity.add_argument("identity", choices=("user", "application"), nargs="?", default="user")
    identity.add_argument("--explicit", action="store_true")

    preview = commands.add_parser("make-preview")
    preview.add_argument("spec", help="JSON file path, or - for stdin")

    validate = commands.add_parser("validate-preview")
    validate.add_argument("preview")
    validate.add_argument("current_state")
    validate.add_argument("--confirmed", required=True)
    validate.add_argument("--tools", required=True, help="JSON array of available tool names")
    validate.add_argument("--applied", help="optional JSON array of applied preview IDs")

    args = parser.parse_args(argv)
    try:
        if args.command == "classify-url":
            result = classify_feishu_url(args.url)
        elif args.command == "identity":
            result = identity_parameters(args.identity, explicit_application=args.explicit)
        elif args.command == "make-preview":
            result = make_preview(load_json(args.spec))
        else:
            result = validate_preview(
                load_json(args.preview),
                load_json(args.current_state),
                args.confirmed,
                load_json(args.tools),
                load_json(args.applied) if args.applied else (),
            )
    except (GuardError, json.JSONDecodeError, OSError) as error:
        print(json.dumps({"valid": False, "error": str(error)}, ensure_ascii=False))
        return 2

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
