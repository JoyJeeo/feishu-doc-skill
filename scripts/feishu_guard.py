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
DOCX_EDIT_OPERATIONS = {"append", "insert", "replace"}
DOCX_BLOCK_KINDS = {f"heading{level}" for level in range(1, 10)} | {
    "text",
    "bullet",
    "ordered",
    "quote",
    "code",
    "table",
    "callout",
    "columns",
}
BITABLE_READ_ONLY_FIELD_TYPES = {
    "Formula",
    "CreatedTime",
    "ModifiedTime",
    "CreatedUser",
    "ModifiedUser",
    "AutoNumber",
}
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


def _validate_docx_create(scope: Any, changes: Any) -> None:
    if not isinstance(scope, dict) or not isinstance(scope.get("parent"), str) or not scope["parent"].strip():
        raise GuardError("docx 创建预览必须指定 scope.parent")
    if not isinstance(changes, dict) or not isinstance(changes.get("title"), str) or not changes["title"].strip():
        raise GuardError("docx 创建预览必须包含非空 changes.title")
    blocks = changes.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise GuardError("docx 创建预览必须包含完整的非空 changes.blocks")
    if any(not isinstance(block, dict) or not isinstance(block.get("kind"), str) for block in blocks):
        raise GuardError("docx 创建预览的每个块必须包含 kind")
    if not isinstance(changes.get("pending_confirmations"), list):
        raise GuardError("docx 创建预览必须包含 changes.pending_confirmations 数组")


def _string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise GuardError(f"{field} 必须是{'可为空的' if allow_empty else '非空'}字符串数组")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise GuardError(f"{field} 必须是{'可为空的' if allow_empty else '非空'}字符串数组")
    if len(value) != len(set(value)):
        raise GuardError(f"{field} 不能包含重复项")
    return value


def summarize_batch_outcomes(
    planned_keys: Any,
    successful_keys: Any,
    failed_by_key: Any,
) -> dict[str, Any]:
    planned = _string_list(planned_keys, "planned_keys")
    successful = set(_string_list(successful_keys, "successful_keys", allow_empty=True))
    if not isinstance(failed_by_key, dict) or any(
        not isinstance(key, str)
        or not key.strip()
        or not isinstance(reason, str)
        or not reason.strip()
        for key, reason in failed_by_key.items()
    ):
        raise GuardError("failed_by_key 必须将业务主键映射到非空失败原因")
    planned_set = set(planned)
    failed = set(failed_by_key)
    if not (successful | failed) <= planned_set:
        raise GuardError("批量结果包含计划外业务主键")
    if successful & failed:
        raise GuardError("同一业务主键不能同时成功和失败")

    unattempted = planned_set - successful - failed
    return {
        "status": "success" if successful == planned_set else "partial" if successful else "failed",
        "successful": [key for key in planned if key in successful],
        "failed": [
            {"business_key": key, "reason": failed_by_key[key]} for key in planned if key in failed
        ],
        "unattempted": [key for key in planned if key in unattempted],
    }


def _validate_docx_block_plan(blocks: Any) -> None:
    if not isinstance(blocks, list) or not blocks:
        raise GuardError("docx 编辑预览必须包含非空 changes.after_blocks")
    for index, block in enumerate(blocks):
        if not isinstance(block, dict) or block.get("kind") not in DOCX_BLOCK_KINDS:
            raise GuardError(f"changes.after_blocks[{index}] 包含不支持的块类型")
        if block["kind"] == "table":
            content = block.get("content")
            rows = content.get("rows") if isinstance(content, dict) else None
            if (
                not isinstance(rows, list)
                or not rows
                or any(not isinstance(row, list) or not row for row in rows)
                or len({len(row) for row in rows}) != 1
                or any(not isinstance(cell, str) for row in rows for cell in row)
            ):
                raise GuardError("轻量表格必须包含非空且列数一致的 content.rows")


def _validate_docx_edit(scope: Any, before_state: Any, changes: Any, risks: Any) -> None:
    if not isinstance(scope, dict):
        raise GuardError("docx 编辑预览必须包含结构化 scope")
    selector = scope.get("selector")
    if not isinstance(selector, dict):
        raise GuardError("docx 编辑预览必须包含 scope.selector")
    heading_id = selector.get("heading_block_id")
    heading_path = selector.get("heading_path")
    has_heading_id = isinstance(heading_id, str) and bool(heading_id.strip())
    has_heading_path = (
        isinstance(heading_path, list)
        and bool(heading_path)
        and all(isinstance(item, str) and item.strip() for item in heading_path)
    )
    if not has_heading_id and not has_heading_path:
        raise GuardError("章节必须使用标题块 ID 或完整标题路径定位")
    if selector.get("match_count") != 1:
        raise GuardError("章节定位结果必须唯一")

    target_ids = set(_string_list(scope.get("target_block_ids"), "scope.target_block_ids"))
    if has_heading_id and heading_id not in target_ids:
        raise GuardError("标题块 ID 必须包含在章节目标块中")
    boundary = scope.get("boundary")
    if not isinstance(boundary, dict) or not {"before", "after"}.issubset(boundary):
        raise GuardError("docx 编辑预览必须包含前后章节边界")
    if any(value is not None and (not isinstance(value, str) or not value.strip()) for value in boundary.values()):
        raise GuardError("章节边界必须是块 ID 或 null")

    if not isinstance(before_state, dict) or not isinstance(before_state.get("blocks"), list):
        raise GuardError("docx 编辑预览必须保留 before_state.blocks")
    inventory = {}
    for block in before_state["blocks"]:
        if not isinstance(block, dict) or not isinstance(block.get("block_id"), str):
            raise GuardError("before_state.blocks 必须包含 block_id")
        if block["block_id"] in inventory:
            raise GuardError("before_state.blocks 不能包含重复 block_id")
        inventory[block["block_id"]] = block
    if not target_ids.issubset(inventory):
        raise GuardError("章节目标块不完整或不在当前文档清单中")
    boundary_ids = {value for value in boundary.values() if value is not None}
    if not boundary_ids.issubset(inventory) or boundary_ids & target_ids:
        raise GuardError("章节边界必须存在且位于目标章节之外")

    if (
        not isinstance(changes, dict)
        or not isinstance(changes.get("before_blocks"), list)
        or not changes["before_blocks"]
    ):
        raise GuardError("docx 编辑预览必须展示非空 changes.before_blocks")
    _validate_docx_block_plan(changes.get("after_blocks"))
    affected_ids = set(
        _string_list(changes.get("affected_block_ids"), "changes.affected_block_ids", allow_empty=True)
    )
    if not affected_ids.issubset(target_ids):
        raise GuardError("编辑计划包含章节范围外的块")

    preserved_ids = set(
        _string_list(changes.get("preserved_block_ids"), "changes.preserved_block_ids", allow_empty=True)
    )
    if not preserved_ids.issubset(target_ids):
        raise GuardError("保留块必须位于目标章节内")
    protected_ids = {
        block_id
        for block_id in target_ids
        if inventory[block_id].get("kind") == "unknown" or inventory[block_id].get("support") == "opaque"
    }
    if protected_ids & affected_ids or not protected_ids.issubset(preserved_ids):
        raise GuardError("未知或不透明块必须原位保留，不能隐式覆盖")

    fallbacks = changes.get("format_fallbacks")
    if not isinstance(fallbacks, list):
        raise GuardError("docx 编辑预览必须包含 changes.format_fallbacks 数组")
    for fallback in fallbacks:
        if not isinstance(fallback, dict) or any(
            not isinstance(fallback.get(field), str) or not fallback[field].strip()
            for field in ("requested_kind", "rendered_as", "reason")
        ):
            raise GuardError("格式降级必须说明 requested_kind、rendered_as 和 reason")
    if fallbacks and not (
        isinstance(risks, list)
        and any(isinstance(risk, dict) and risk.get("type") == "format_degradation" for risk in risks)
    ):
        raise GuardError("存在格式降级时，risks 必须包含 format_degradation")
    if not isinstance(changes.get("pending_confirmations"), list):
        raise GuardError("docx 编辑预览必须包含 changes.pending_confirmations 数组")


def _validate_bitable_value(field: dict[str, Any], value: Any) -> None:
    field_name = field["field_name"]
    ui_type = field["ui_type"]
    valid = False
    if ui_type in {"Text", "Email", "Barcode", "SingleSelect", "Phone"}:
        valid = isinstance(value, str)
    elif ui_type in {"Number", "Progress", "Currency", "Rating"}:
        valid = isinstance(value, (int, float)) and not isinstance(value, bool)
    elif ui_type == "MultiSelect":
        valid = (
            isinstance(value, list)
            and all(isinstance(item, str) for item in value)
            and len(value) == len(set(value))
        )
    elif ui_type == "DateTime":
        valid = isinstance(value, int) and not isinstance(value, bool)
    elif ui_type == "Checkbox":
        valid = isinstance(value, bool)
    elif ui_type == "Url":
        valid = (
            isinstance(value, dict)
            and isinstance(value.get("link"), str)
            and bool(value["link"].strip())
            and ("text" not in value or isinstance(value["text"], str))
        )
    elif ui_type in BITABLE_READ_ONLY_FIELD_TYPES:
        raise GuardError(f"Bitable 只读字段不能写入：{field_name}")
    else:
        raise GuardError(f"Bitable 字段类型尚未支持写入校验：{field_name} ({ui_type})")
    if not valid:
        raise GuardError(f"Bitable 字段类型不匹配：{field_name} ({ui_type})")
    if ui_type in {"SingleSelect", "MultiSelect"}:
        options = field.get("options")
        values = [value] if ui_type == "SingleSelect" else value
        if (
            not isinstance(options, list)
            or any(not isinstance(option, str) or not option for option in options)
            or any(item not in options for item in values)
        ):
            raise GuardError(f"Bitable 选项字段包含未确认的新选项：{field_name}")


def _validate_bitable_record_plan(scope: Any, before_state: Any, changes: Any, operation: str) -> None:
    if operation not in {"create", "update"}:
        raise GuardError("Bitable 记录预览只支持 create 或 update")
    required_scope = ("app_token", "table_id", "table_name", "business_key_field")
    if not isinstance(scope, dict) or scope.get("entity") != "records" or any(
        not isinstance(scope.get(field), str) or not scope[field].strip() for field in required_scope
    ):
        raise GuardError("Bitable 记录预览必须唯一指定应用、数据表和业务主键")
    if not isinstance(before_state, dict) or any(
        before_state.get(field) != scope[field] for field in ("app_token", "table_id", "table_name")
    ):
        raise GuardError("Bitable 当前状态与预览目标不一致")
    if not before_state.get("fields_pagination_complete") or not before_state.get(
        "records_pagination_complete"
    ):
        raise GuardError("Bitable 字段和业务主键匹配结果必须完成完整分页")

    fields = before_state.get("fields")
    if not isinstance(fields, list) or not fields:
        raise GuardError("Bitable 当前状态必须包含字段清单")
    field_schema = {}
    field_ids = set()
    for field in fields:
        if not isinstance(field, dict) or any(
            not isinstance(field.get(key), str) or not field[key].strip()
            for key in ("field_id", "field_name", "ui_type")
        ):
            raise GuardError("Bitable 字段清单不完整")
        if field["field_name"] in field_schema or field["field_id"] in field_ids:
            raise GuardError("Bitable 字段清单包含重复字段")
        field_schema[field["field_name"]] = field
        field_ids.add(field["field_id"])
    business_key = scope["business_key_field"]
    if business_key not in field_schema:
        raise GuardError("Bitable 业务主键不在字段清单中")

    current_records = before_state.get("records")
    if not isinstance(current_records, list):
        raise GuardError("Bitable 当前状态必须包含记录匹配结果")
    records_by_id = {}
    for record in current_records:
        if (
            not isinstance(record, dict)
            or not isinstance(record.get("record_id"), str)
            or not record["record_id"].strip()
            or not isinstance(record.get("fields"), dict)
        ):
            raise GuardError("Bitable 记录匹配结果不完整")
        if record["record_id"] in records_by_id:
            raise GuardError("Bitable 记录匹配结果包含重复 record_id")
        records_by_id[record["record_id"]] = record["fields"]

    if not isinstance(changes, dict) or not isinstance(changes.get("records"), list) or not changes["records"]:
        raise GuardError("Bitable 预览必须包含非空记录变更")
    if scope.get("record_count") != len(changes["records"]):
        raise GuardError("Bitable 预览记录数量与范围不一致")
    if not isinstance(changes.get("quality_issues"), list) or not isinstance(
        changes.get("pending_confirmations"), list
    ):
        raise GuardError("Bitable 预览必须包含数据质量问题和待确认项数组")

    planned_keys = set()
    for record in changes["records"]:
        if not isinstance(record, dict):
            raise GuardError("Bitable 记录变更必须是结构化对象")
        key_value = record.get("business_key_value")
        if not isinstance(key_value, str) or not key_value.strip() or key_value in planned_keys:
            raise GuardError("Bitable 预览中的业务主键必须非空且不重复")
        planned_keys.add(key_value)
        matches = [
            record_id
            for record_id, values in records_by_id.items()
            if values.get(business_key) == key_value
        ]

        before_fields = record.get("before_fields")
        after_fields = record.get("after_fields")
        if not isinstance(before_fields, dict) or not isinstance(after_fields, dict) or not after_fields:
            raise GuardError("Bitable 记录变更必须包含前后字段值")
        if operation == "create":
            if matches:
                raise GuardError("Bitable 创建要求业务主键零匹配")
            if record.get("record_id") is not None or before_fields:
                raise GuardError("Bitable 创建记录不能带现有 record_id 或字段值")
            if after_fields.get(business_key) != key_value:
                raise GuardError("Bitable 创建记录必须写入业务主键")
        else:
            if len(matches) != 1:
                raise GuardError("Bitable 更新要求业务主键唯一匹配")
            if record.get("record_id") != matches[0]:
                raise GuardError("Bitable 更新 record_id 与业务主键匹配结果不一致")
            if set(before_fields) != set(after_fields):
                raise GuardError("Bitable 更新必须逐字段展示前后值")
            current_fields = records_by_id[matches[0]]
            if any(
                field not in current_fields or canonical_json(current_fields[field]) != canonical_json(value)
                for field, value in before_fields.items()
            ):
                raise GuardError("Bitable 更新前字段值与当前记录不一致")

        for field_name, value in after_fields.items():
            if field_name not in field_schema:
                raise GuardError(f"Bitable 字段不在当前字段清单中：{field_name}")
            _validate_bitable_value(field_schema[field_name], value)
        expected_differences = [
            {"field": field_name, "before": before_fields.get(field_name), "after": after_fields[field_name]}
            for field_name in sorted(after_fields)
            if field_name not in before_fields
            or canonical_json(before_fields[field_name]) != canonical_json(after_fields[field_name])
        ]
        if not expected_differences or record.get("field_differences") != expected_differences:
            raise GuardError("Bitable 字段差异与前后值不一致")

    for issue in changes["quality_issues"]:
        if not isinstance(issue, dict) or any(
            not isinstance(issue.get(field), str) or not issue[field].strip() for field in ("type", "detail")
        ):
            raise GuardError("Bitable 数据质量问题必须说明 type 和 detail")


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
    if spec["resource_type"] == "docx" and operation == "create":
        _validate_docx_create(spec["scope"], spec["changes"])
    if spec["resource_type"] == "docx" and operation in DOCX_EDIT_OPERATIONS:
        _validate_docx_edit(spec["scope"], spec["before_state"], spec["changes"], spec.get("risks", []))
    if spec["resource_type"] == "bitable":
        _validate_bitable_record_plan(spec["scope"], spec["before_state"], spec["changes"], operation)

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
    if preview["resource_type"] == "docx" and operation == "create":
        _validate_docx_create(preview["scope"], preview["changes"])
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
    if preview["resource_type"] == "docx" and operation in DOCX_EDIT_OPERATIONS:
        _validate_docx_edit(preview["scope"], current_state, preview["changes"], preview.get("risks", []))
    if preview["resource_type"] == "bitable":
        _validate_bitable_record_plan(preview["scope"], current_state, preview["changes"], operation)

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
