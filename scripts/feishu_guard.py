#!/usr/bin/env python3
"""Deterministic local guards for the Feishu document skill. No network access."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
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
PROJECT_SOURCE_TYPES = {"docx", "wiki", "drive", "bitable", "sheets"}
PROJECT_CLAIM_KINDS = {"fact", "finding", "recommendation", "pending_confirmation"}
PROJECT_RESOURCE_STATUSES = {"verified", "failed", "unattempted"}
PROJECT_DOCUMENT_ROLES = {
    "project_home",
    "prd",
    "technical_design",
    "meeting_notes",
    "weekly_report",
    "retrospective",
    "other",
}
PROJECT_REGISTER_SCHEMAS = {
    "action_items": {
        "business_key_field": "行动项编号",
        "source_field": "来源链接",
        "fields": [
            {"field_name": "行动项编号", "type": 1, "ui_type": "Text"},
            {"field_name": "事项", "type": 1, "ui_type": "Text"},
            {"field_name": "负责人", "type": 1, "ui_type": "Text"},
            {
                "field_name": "状态",
                "type": 3,
                "ui_type": "SingleSelect",
                "property": {
                    "options": [
                        {"name": "未开始"},
                        {"name": "进行中"},
                        {"name": "已完成"},
                        {"name": "受阻"},
                    ]
                },
            },
            {"field_name": "截止日期", "type": 5, "ui_type": "DateTime"},
            {"field_name": "来源链接", "type": 15, "ui_type": "Url"},
        ],
    },
    "risks": {
        "business_key_field": "风险编号",
        "source_field": "来源链接",
        "fields": [
            {"field_name": "风险编号", "type": 1, "ui_type": "Text"},
            {"field_name": "风险", "type": 1, "ui_type": "Text"},
            {
                "field_name": "影响",
                "type": 3,
                "ui_type": "SingleSelect",
                "property": {"options": [{"name": "低"}, {"name": "中"}, {"name": "高"}]},
            },
            {
                "field_name": "概率",
                "type": 3,
                "ui_type": "SingleSelect",
                "property": {"options": [{"name": "低"}, {"name": "中"}, {"name": "高"}]},
            },
            {
                "field_name": "状态",
                "type": 3,
                "ui_type": "SingleSelect",
                "property": {
                    "options": [{"name": "开放"}, {"name": "监控中"}, {"name": "已关闭"}]
                },
            },
            {"field_name": "负责人", "type": 1, "ui_type": "Text"},
            {"field_name": "应对措施", "type": 1, "ui_type": "Text"},
            {"field_name": "来源链接", "type": 15, "ui_type": "Url"},
        ],
    },
    "decisions": {
        "business_key_field": "决策编号",
        "source_field": "来源链接",
        "fields": [
            {"field_name": "决策编号", "type": 1, "ui_type": "Text"},
            {"field_name": "结论", "type": 1, "ui_type": "Text"},
            {"field_name": "原因", "type": 1, "ui_type": "Text"},
            {"field_name": "决策人", "type": 1, "ui_type": "Text"},
            {"field_name": "决策日期", "type": 5, "ui_type": "DateTime"},
            {"field_name": "来源链接", "type": 15, "ui_type": "Url"},
        ],
    },
    "metrics": {
        "business_key_field": "指标编号",
        "source_field": "来源链接",
        "fields": [
            {"field_name": "指标编号", "type": 1, "ui_type": "Text"},
            {"field_name": "指标名称", "type": 1, "ui_type": "Text"},
            {"field_name": "当前值", "type": 2, "ui_type": "Number"},
            {"field_name": "单位", "type": 1, "ui_type": "Text"},
            {"field_name": "状态日期", "type": 5, "ui_type": "DateTime"},
            {"field_name": "来源链接", "type": 15, "ui_type": "Url"},
        ],
    },
}
MODES = {"analyze", "preview", "apply", "verify"}
WRITE_OPERATIONS = {"create", "append", "insert", "replace", "copy", "move", "update"}
DOCX_WRITE_OPERATIONS = {"create", "append", "insert", "replace"}
DISABLED_OPERATIONS = {"delete", "transfer_owner", "public_permission_change"}
DOCX_EDIT_OPERATIONS = {"append", "insert", "replace"}
WIKI_WRITE_OPERATIONS = {"create", "copy", "move", "update"}
WIKI_IMPORT_SOURCE_TYPES = {"doc", "sheet", "bitable", "mindnote", "docx", "file", "slides"}
DRIVE_WRITE_OPERATIONS = {"create", "copy", "move", "update"}
DRIVE_COPY_SOURCE_TYPES = {"file", "doc", "sheet", "bitable", "docx", "mindnote", "slides"}
DRIVE_MOVE_SOURCE_TYPES = DRIVE_COPY_SOURCE_TYPES | {"folder"}
DRIVE_VERSION_SOURCE_TYPES = {"docx", "sheet"}
DRIVE_EXPORT_FORMATS = {
    "doc": {"docx", "pdf"},
    "docx": {"docx", "pdf"},
    "sheet": {"xlsx"},
    "bitable": {"xlsx"},
}
DRIVE_IMPORT_FORMATS = {"docx": {"docx"}}
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
SHEETS_RANGE_RE = re.compile(r"^([^!]+)!([A-Z]+)([1-9]\d*):([A-Z]+)([1-9]\d*)$")
SHEETS_CELL_RE = re.compile(r"^([^!]+)!([A-Z]+)([1-9]\d*)$")
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


def validate_default_locations(config: Any) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise GuardError("默认位置配置必须是对象")
    wiki = config.get("wiki")
    drive = config.get("drive")
    if not isinstance(wiki, dict) or any(
        not isinstance(wiki.get(field), str) or not wiki[field].strip()
        for field in ("space_id", "parent_node_token")
    ):
        raise GuardError("默认 Wiki 位置必须包含 space_id 和 parent_node_token")
    if not isinstance(drive, dict) or not isinstance(drive.get("folder_token"), str):
        raise GuardError("默认 Drive 位置必须包含字符串 folder_token，空字符串表示根目录")
    return {
        "wiki": {
            "space_id": wiki["space_id"],
            "parent_node_token": wiki["parent_node_token"],
        },
        "drive": {"folder_token": drive["folder_token"]},
    }


def validate_project_audit(audit: Any) -> dict[str, Any]:
    audit = _require_dict(audit, "项目审计")
    project_name = _require_non_empty_str(audit.get("project_name"), "project_name")
    as_of = _require_non_empty_str(audit.get("as_of"), "as_of")
    try:
        date.fromisoformat(as_of)
    except ValueError as error:
        raise GuardError("as_of 必须是有效的 YYYY-MM-DD 日期") from error

    sources = audit.get("sources")
    if not isinstance(sources, list) or not sources:
        raise GuardError("sources 必须是非空数组")
    source_ids: set[str] = set()
    partial_source_ids: list[str] = []
    for source in sources:
        source = _require_dict(source, "source")
        source_id = _require_non_empty_str(source.get("source_id"), "source.source_id")
        if source_id in source_ids:
            raise GuardError(f"source_id 不能重复：{source_id}")
        source_ids.add(source_id)
        resource_type = _require_non_empty_str(source.get("resource_type"), "source.resource_type")
        if resource_type not in PROJECT_SOURCE_TYPES:
            raise GuardError(f"项目审计不支持来源类型：{resource_type}")
        url = _require_non_empty_str(source.get("url"), "source.url")
        if classify_feishu_url(url)["resource_type"] != resource_type:
            raise GuardError(f"来源链接与资源类型不一致：{source_id}")
        _require_non_empty_str(source.get("title"), "source.title")
        _require_non_empty_str(source.get("read_scope"), "source.read_scope")
        if not isinstance(source.get("read_complete"), bool):
            raise GuardError("source.read_complete 必须是布尔值")
        if not source["read_complete"]:
            _require_non_empty_str(source.get("limitation"), "source.limitation")
            partial_source_ids.append(source_id)

    claims = audit.get("claims")
    if not isinstance(claims, list) or not claims:
        raise GuardError("claims 必须是非空数组")
    claim_ids: set[str] = set()
    for claim in claims:
        claim = _require_dict(claim, "claim")
        claim_id = _require_non_empty_str(claim.get("claim_id"), "claim.claim_id")
        if claim_id in claim_ids:
            raise GuardError(f"claim_id 不能重复：{claim_id}")
        claim_ids.add(claim_id)
        kind = _require_non_empty_str(claim.get("kind"), "claim.kind")
        if kind not in PROJECT_CLAIM_KINDS:
            raise GuardError(f"不支持的项目审计结论类型：{kind}")
        _require_non_empty_str(claim.get("category"), "claim.category")
        _require_non_empty_str(claim.get("text"), "claim.text")
        cited = _string_list(
            claim.get("source_ids"),
            "claim.source_ids",
            allow_empty=kind == "pending_confirmation",
        )
        unknown = sorted(set(cited) - source_ids)
        if unknown:
            raise GuardError(f"结论引用了未知来源：{', '.join(unknown)}")

    return {
        "valid": True,
        "project_name": project_name,
        "as_of": as_of,
        "source_count": len(sources),
        "claim_count": len(claims),
        "partial_source_ids": sorted(partial_source_ids),
    }


def validate_project_preview_plan(plan: Any) -> dict[str, Any]:
    plan = _require_dict(plan, "项目预览计划")
    project_name = _require_non_empty_str(plan.get("project_name"), "project_name")
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        raise GuardError("steps 必须是非空数组")

    seen_step_ids: set[str] = set()
    preview_ids: set[str] = set()
    prior_steps_by_resource: dict[str, set[str]] = {}
    for step in steps:
        step = _require_dict(step, "step")
        step_id = _require_non_empty_str(step.get("step_id"), "step.step_id")
        if step_id in seen_step_ids:
            raise GuardError(f"step_id 不能重复：{step_id}")
        resource_key = _require_non_empty_str(step.get("resource_key"), "step.resource_key")
        role = _require_non_empty_str(step.get("role"), "step.role")
        if role not in PROJECT_DOCUMENT_ROLES:
            raise GuardError(f"不支持的项目文档角色：{role}")
        if step.get("resource_type") != "docx":
            raise GuardError("M5-03 项目文档预览只支持 docx")
        if step.get("operation") not in DOCX_WRITE_OPERATIONS:
            raise GuardError("项目文档步骤只支持 create/append/insert/replace")

        preview_id = _require_non_empty_str(step.get("preview_id"), "step.preview_id")
        if not re.fullmatch(r"fs-[0-9a-f]{16}", preview_id):
            raise GuardError("step.preview_id 格式无效")
        if preview_id in preview_ids:
            raise GuardError("每个资源步骤必须使用独立 preview_id")

        depends_on = _string_list(step.get("depends_on"), "step.depends_on", allow_empty=True)
        unknown_dependencies = sorted(set(depends_on) - seen_step_ids)
        if unknown_dependencies:
            raise GuardError(f"依赖步骤必须已在前序声明：{', '.join(unknown_dependencies)}")

        source_urls = _string_list(step.get("source_urls"), "step.source_urls", allow_empty=True)
        for url in source_urls:
            if classify_feishu_url(url)["resource_type"] not in PROJECT_SOURCE_TYPES:
                raise GuardError(f"项目文档不支持来源链接：{url}")

        linked_resource_keys = _string_list(
            step.get("linked_resource_keys"),
            "step.linked_resource_keys",
            allow_empty=True,
        )
        for linked_key in linked_resource_keys:
            linked_steps = prior_steps_by_resource.get(linked_key, set())
            if not linked_steps or not linked_steps.intersection(depends_on):
                raise GuardError(f"链接资源必须先完成并声明直接依赖：{linked_key}")

        if role == "weekly_report":
            period = _require_dict(step.get("period"), "step.period")
            period_start = _require_non_empty_str(period.get("start"), "step.period.start")
            period_end = _require_non_empty_str(period.get("end"), "step.period.end")
            try:
                start_date = date.fromisoformat(period_start)
                end_date = date.fromisoformat(period_end)
            except ValueError as error:
                raise GuardError("周报周期必须是有效的 YYYY-MM-DD 日期") from error
            if start_date > end_date:
                raise GuardError("周报周期开始日期不能晚于结束日期")

        seen_step_ids.add(step_id)
        preview_ids.add(preview_id)
        prior_steps_by_resource.setdefault(resource_key, set()).add(step_id)

    return {
        "valid": True,
        "project_name": project_name,
        "step_count": len(steps),
        "execution_order": [step["step_id"] for step in steps],
    }


def validate_project_integration(result: Any) -> dict[str, Any]:
    result = _require_dict(result, "项目集成结果")
    project_name = _require_non_empty_str(result.get("project_name"), "project_name")
    resources = result.get("resources")
    if not isinstance(resources, list) or not resources:
        raise GuardError("resources 必须是非空数组")

    statuses: dict[str, str] = {}
    urls: dict[str, str] = {}
    counts = {status: 0 for status in PROJECT_RESOURCE_STATUSES}
    for resource in resources:
        resource = _require_dict(resource, "resource")
        resource_key = _require_non_empty_str(resource.get("resource_key"), "resource.resource_key")
        if resource_key in statuses:
            raise GuardError(f"resource_key 不能重复：{resource_key}")
        resource_type = _require_non_empty_str(
            resource.get("resource_type"), "resource.resource_type"
        )
        if resource_type not in PROJECT_SOURCE_TYPES:
            raise GuardError(f"项目集成不支持资源类型：{resource_type}")
        url = _require_non_empty_str(resource.get("url"), "resource.url")
        if classify_feishu_url(url)["resource_type"] != resource_type:
            raise GuardError(f"资源链接与类型不一致：{resource_key}")
        status = _require_non_empty_str(resource.get("status"), "resource.status")
        if status not in PROJECT_RESOURCE_STATUSES:
            raise GuardError(f"不支持的项目资源状态：{status}")
        if not isinstance(resource.get("read_complete"), bool):
            raise GuardError("resource.read_complete 必须是布尔值")
        if status == "verified" and not resource["read_complete"]:
            raise GuardError(f"资源未完整回读，不能标记 verified：{resource_key}")

        depends_on = _string_list(
            resource.get("depends_on"), "resource.depends_on", allow_empty=True
        )
        unknown_dependencies = sorted(set(depends_on) - statuses.keys())
        if unknown_dependencies:
            raise GuardError(f"资源依赖必须已在前序声明：{', '.join(unknown_dependencies)}")
        blocked_by = [key for key in depends_on if statuses[key] != "verified"]
        if blocked_by and status != "unattempted":
            raise GuardError(f"依赖未验证的资源必须标记 unattempted：{resource_key}")
        if status in {"failed", "unattempted"}:
            _require_non_empty_str(resource.get("reason"), "resource.reason")

        statuses[resource_key] = status
        urls[resource_key] = url
        counts[status] += 1

    links = result.get("links")
    if not isinstance(links, list):
        raise GuardError("links 必须是数组")
    seen_links: set[tuple[str, str]] = set()
    for link in links:
        link = _require_dict(link, "link")
        source_key = _require_non_empty_str(
            link.get("source_resource_key"), "link.source_resource_key"
        )
        target_key = _require_non_empty_str(
            link.get("target_resource_key"), "link.target_resource_key"
        )
        if source_key not in statuses or target_key not in statuses:
            raise GuardError("跨资源链接引用了未知资源")
        if source_key == target_key or (source_key, target_key) in seen_links:
            raise GuardError("跨资源链接不能自引用或重复")
        if statuses[source_key] != "verified" or statuses[target_key] != "verified":
            raise GuardError("跨资源链接两端必须完成验证")
        observed_url = _require_non_empty_str(link.get("observed_url"), "link.observed_url")
        if observed_url != urls[target_key]:
            raise GuardError(f"跨资源链接目标不一致：{source_key} -> {target_key}")
        seen_links.add((source_key, target_key))

    if counts["verified"] == len(resources):
        overall_status = "complete"
    elif counts["verified"]:
        overall_status = "partial"
    else:
        overall_status = "failed"
    return {
        "valid": True,
        "project_name": project_name,
        "overall_status": overall_status,
        "resource_count": len(resources),
        "link_count": len(links),
        "counts": counts,
    }


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


def _require_non_empty_str(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise GuardError(f"{field} 必须是字符串")
    if value == "":
        if allow_empty:
            return value
        raise GuardError(f"{field} 不能为空")
    if not value.strip():
        raise GuardError(f"{field} 不能是空白字符串")
    return value


def _require_dict(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GuardError(f"{field} 必须是对象")
    return value


def _collect_named_children(
    items: Any,
    field: str,
    token_field: str,
    *,
    title_field: str = "title",
    allow_empty_titles: bool = False,
) -> tuple[set[str], set[str]]:
    if not isinstance(items, list):
        raise GuardError(f"{field} 必须是数组")
    titles = set()
    tokens = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise GuardError(f"{field}[{index}] 必须是对象")
        token = _require_non_empty_str(item.get(token_field), f"{field}[{index}].{token_field}")
        title = item.get(title_field)
        if not (allow_empty_titles and title == ""):
            title = _require_non_empty_str(title, f"{field}[{index}].{title_field}")
        if token in tokens:
            raise GuardError(f"{field} 包含重复 token")
        if title and title in titles:
            raise GuardError(f"{field} 包含重复标题")
        tokens.add(token)
        if title:
            titles.add(title)
    return titles, tokens


def _validate_wiki_plan(scope: Any, before_state: Any, changes: Any, operation: str) -> None:
    if operation not in WIKI_WRITE_OPERATIONS:
        raise GuardError("Wiki 写预览只支持 create/copy/move/update")
    scope = _require_dict(scope, "scope")
    before_state = _require_dict(before_state, "before_state")
    changes = _require_dict(changes, "changes")
    if not isinstance(changes.get("pending_confirmations"), list):
        raise GuardError("Wiki 预览必须包含 changes.pending_confirmations 数组")

    space_id = _require_non_empty_str(scope.get("space_id"), "scope.space_id")
    if before_state.get("space_id") != space_id:
        raise GuardError("Wiki 当前状态中的 space_id 与 scope 不一致")

    if operation == "move" and scope.get("entity") == "drive_document":
        source_token = _require_non_empty_str(scope.get("source_token"), "scope.source_token")
        source_type = _require_non_empty_str(scope.get("source_type"), "scope.source_type")
        if source_type not in WIKI_IMPORT_SOURCE_TYPES:
            raise GuardError(f"Wiki 文档入库不支持源类型 {source_type}")
        source_parent_token = _require_non_empty_str(
            scope.get("source_parent_folder_token"), "scope.source_parent_folder_token"
        )
        target_parent_token = _require_non_empty_str(
            scope.get("target_parent_node_token"), "scope.target_parent_node_token"
        )
        source = _require_dict(before_state.get("source_document"), "before_state.source_document")
        target_parent = _require_dict(before_state.get("target_parent"), "before_state.target_parent")
        if source.get("token") != source_token or source.get("type") != source_type:
            raise GuardError("Wiki 文档入库的源 token/type 与当前状态不一致")
        if source.get("parent_folder_token") != source_parent_token:
            raise GuardError("Wiki 文档入库的源目录与当前状态不一致")
        source_title = _require_non_empty_str(source.get("title"), "before_state.source_document.title")
        if target_parent.get("space_id") != space_id:
            raise GuardError("Wiki 文档入库的目标 space_id 与当前状态不一致")
        if target_parent.get("parent_node_token") != target_parent_token:
            raise GuardError("Wiki 文档入库的目标父节点与当前状态不一致")
        child_titles, _ = _collect_named_children(
            target_parent.get("children", []),
            "before_state.target_parent.children",
            "node_token",
            title_field="title",
        )
        if source_title in child_titles:
            raise GuardError("目标父节点已有同名子节点")
        expected_arguments = {
            "path": {"space_id": space_id},
            "data": {
                "obj_token": source_token,
                "obj_type": source_type,
                "parent_wiki_token": target_parent_token,
                "apply": False,
            },
            "useUAT": True,
        }
        if changes.get("apply_arguments") != expected_arguments:
            raise GuardError("Wiki 文档入库调用参数与预览范围不一致")
        return

    if operation == "create":
        parent_node_token = _require_non_empty_str(scope.get("parent_node_token"), "scope.parent_node_token")
        if before_state.get("parent_node_token") != parent_node_token:
            raise GuardError("Wiki 创建预览的父节点与当前状态不一致")
        _require_non_empty_str(changes.get("title"), "changes.title")
        _require_non_empty_str(changes.get("node_type"), "changes.node_type")
        child_titles, _ = _collect_named_children(
            before_state.get("children", []),
            "before_state.children",
            "node_token",
            title_field="title",
        )
        if _require_non_empty_str(changes.get("title"), "changes.title") in child_titles:
            raise GuardError("目标父节点已有同名子节点")
        return

    if operation == "update":
        node_token = _require_non_empty_str(scope.get("node_token"), "scope.node_token")
        parent_node_token = _require_non_empty_str(scope.get("parent_node_token"), "scope.parent_node_token")
        node = _require_dict(before_state.get("node"), "before_state.node")
        if node.get("node_token") != node_token:
            raise GuardError("scope.node_token 与 before_state 不一致")
        if node.get("parent_node_token") != parent_node_token:
            raise GuardError("scope.parent_node_token 与 before_state 不一致")
        new_title = _require_non_empty_str(changes.get("title"), "changes.title")
        if new_title == _require_non_empty_str(node.get("title"), "before_state.node.title"):
            raise GuardError("Wiki 标题未发生变化")
        return

    if operation not in {"move", "copy"}:
        raise GuardError("Wiki 写预览只支持 create/copy/move/update")

    source_node_token = _require_non_empty_str(scope.get("source_node_token"), "scope.source_node_token")
    source_parent_token = _require_non_empty_str(scope.get("source_parent_node_token"), "scope.source_parent_node_token")
    target_parent_token = _require_non_empty_str(scope.get("target_parent_node_token"), "scope.target_parent_node_token")
    source_node = _require_dict(before_state.get("source_node"), "before_state.source_node")
    target_parent = _require_dict(before_state.get("target_parent"), "before_state.target_parent")
    if source_node.get("space_id") and source_node.get("space_id") != space_id:
        raise GuardError("Wiki 源节点 space_id 与 scope 不一致")
    if source_node.get("node_token") != source_node_token:
        raise GuardError("scope.source_node_token 与 before_state 不一致")
    if source_node.get("parent_node_token") != source_parent_token:
        raise GuardError("scope.source_parent_node_token 与 before_state 不一致")

    _require_non_empty_str(source_node.get("node_type"), "before_state.source_node.node_type")
    if target_parent.get("space_id") and target_parent.get("space_id") != space_id:
        raise GuardError("目标父节点 space_id 与 scope 不一致")
    if target_parent.get("parent_node_token") != target_parent_token:
        raise GuardError("scope.target_parent_node_token 与 before_state 不一致")

    title = changes.get("title", source_node.get("title"))
    if title is None:
        raise GuardError("changes.title 或 before_state.source_node.title 必须存在")
    title = _require_non_empty_str(title, "changes.title")
    child_titles, _ = _collect_named_children(
        target_parent.get("children", []),
        "before_state.target_parent.children",
        "node_token",
        title_field="title",
    )
    if operation == "move" and source_parent_token == target_parent_token and title == source_node.get("title"):
        raise GuardError("Wiki 移动预览目标未发生变化")
    if title != source_node.get("title") and title in child_titles:
        raise GuardError("目标父节点已有同名子节点")
    if title == source_node.get("title") and operation == "copy" and title in child_titles:
        raise GuardError("目标父节点已有同名子节点")


def _validate_drive_plan(scope: Any, before_state: Any, changes: Any, operation: str) -> None:
    if operation not in DRIVE_WRITE_OPERATIONS:
        raise GuardError("Drive 写预览只支持 create/copy/move/update")
    scope = _require_dict(scope, "scope")
    before_state = _require_dict(before_state, "before_state")
    changes = _require_dict(changes, "changes")
    if not isinstance(changes.get("pending_confirmations"), list):
        raise GuardError("Drive 预览必须包含 changes.pending_confirmations 数组")

    if operation == "create" and scope.get("entity") == "import_task":
        source_file_token = _require_non_empty_str(scope.get("source_file_token"), "scope.source_file_token")
        file_extension = _require_non_empty_str(scope.get("file_extension"), "scope.file_extension")
        target_type = _require_non_empty_str(scope.get("target_type"), "scope.target_type")
        target_folder_token = _require_non_empty_str(
            scope.get("target_folder_token"), "scope.target_folder_token"
        )
        if target_type not in DRIVE_IMPORT_FORMATS.get(file_extension, set()):
            raise GuardError(f"Drive 不支持将 {file_extension} 导入为 {target_type}")
        source_file = _require_dict(before_state.get("source_file"), "before_state.source_file")
        if source_file.get("token") != source_file_token or source_file.get("file_extension") != file_extension:
            raise GuardError("Drive 导入的源文件 token/扩展名与当前状态不一致")
        source_provenance = _require_non_empty_str(
            source_file.get("provenance"), "before_state.source_file.provenance"
        )
        if source_provenance == "export_task":
            raise GuardError("Drive 导出任务返回的文件 token 不能直接用于导入")
        if source_provenance not in {"file_upload", "media_upload", "existing_drive_file"}:
            raise GuardError("Drive 导入源文件缺少可验证的上传或现有文件来源")
        if source_file.get("type") != "file":
            raise GuardError("Drive 导入源必须是普通 file 类型")
        file_name = _require_non_empty_str(source_file.get("file_name"), "before_state.source_file.file_name")
        if not file_name.lower().endswith(f".{file_extension.lower()}"):
            raise GuardError("Drive 导入源文件名后缀与扩展名不一致")
        file_size = source_file.get("file_size")
        if source_provenance == "existing_drive_file":
            if file_size is not None and (not isinstance(file_size, int) or file_size <= 0):
                raise GuardError("Drive 导入源文件大小必须为正整数或未知")
        elif not isinstance(file_size, int) or file_size <= 0:
            raise GuardError("Drive 导入的上传结果必须包含正文件大小")
        target_parent = _require_dict(before_state.get("target_parent"), "before_state.target_parent")
        if target_parent.get("folder_token") != target_folder_token:
            raise GuardError("Drive 导入的目标文件夹与当前状态不一致")
        file_name = _require_non_empty_str(changes.get("file_name"), "changes.file_name")
        target_titles, _ = _collect_named_children(
            target_parent.get("children", []),
            "before_state.target_parent.children",
            "token",
            title_field="name",
            allow_empty_titles=True,
        )
        if file_name in target_titles:
            raise GuardError("目标文件夹已有同名子项")
        expected_arguments = {
            "data": {
                "file_extension": file_extension,
                "file_name": file_name,
                "file_token": source_file_token,
                "point": {"mount_key": target_folder_token, "mount_type": 1},
                "type": target_type,
            },
            "useUAT": True,
        }
        if changes.get("apply_arguments") != expected_arguments:
            raise GuardError("Drive 导入调用参数与预览范围不一致")
        return

    if operation == "create" and scope.get("entity") == "export_task":
        source_token = _require_non_empty_str(scope.get("source_token"), "scope.source_token")
        source_type = _require_non_empty_str(scope.get("source_type"), "scope.source_type")
        file_extension = _require_non_empty_str(scope.get("file_extension"), "scope.file_extension")
        if file_extension not in DRIVE_EXPORT_FORMATS.get(source_type, set()):
            raise GuardError(f"Drive 不支持将 {source_type} 导出为 {file_extension}")
        source = _require_dict(before_state.get("source"), "before_state.source")
        if source.get("token") != source_token or source.get("type") != source_type:
            raise GuardError("Drive 导出的源 token/type 与当前状态不一致")
        _require_non_empty_str(source.get("title"), "before_state.source.title")
        expected_arguments = {
            "data": {"token": source_token, "type": source_type, "file_extension": file_extension},
            "useUAT": True,
        }
        if changes.get("apply_arguments") != expected_arguments:
            raise GuardError("Drive 导出调用参数与预览范围不一致")
        return

    if operation == "create":
        parent_folder_token = _require_non_empty_str(
            scope.get("parent_folder_token"), "scope.parent_folder_token", allow_empty=True
        )
        if _require_non_empty_str(scope.get("resource_type"), "scope.resource_type") != "folder":
            raise GuardError("Drive 创建写预览仅支持文件夹")
        if before_state.get("folder_token") != parent_folder_token:
            raise GuardError("Drive 创建预览的父文件夹与当前状态不一致")
        name = _require_non_empty_str(changes.get("name"), "changes.name")
        child_titles, _ = _collect_named_children(
            before_state.get("children", []),
            "before_state.children",
            "token",
            title_field="name",
            allow_empty_titles=True,
        )
        if name in child_titles:
            raise GuardError("目标文件夹已有同名子项")
        expected_arguments = {
            "data": {"folder_token": parent_folder_token, "name": name},
            "useUAT": True,
        }
        if changes.get("apply_arguments") != expected_arguments:
            raise GuardError("Drive 创建调用参数与预览范围不一致")
        return

    if operation == "update":
        return

    source_token = _require_non_empty_str(scope.get("source_token"), "scope.source_token")
    source_type = _require_non_empty_str(scope.get("source_type"), "scope.source_type")
    allowed_source_types = DRIVE_COPY_SOURCE_TYPES if operation == "copy" else DRIVE_MOVE_SOURCE_TYPES
    if source_type not in allowed_source_types:
        raise GuardError(f"Drive {operation} 不支持源类型 {source_type}")
    source_parent_folder_token = None
    if operation == "move" or "source_parent_folder_token" in scope:
        source_parent_folder_token = _require_non_empty_str(
            scope.get("source_parent_folder_token"), "scope.source_parent_folder_token"
        )
    target_parent_folder_token = _require_non_empty_str(
        scope.get("target_parent_folder_token"), "scope.target_parent_folder_token"
    )

    source = _require_dict(before_state.get("source"), "before_state.source")
    if source.get("token") != source_token:
        raise GuardError("scope.source_token 与 before_state 不一致")
    if source.get("type") != source_type:
        raise GuardError("scope.source_type 与 before_state 不一致")
    if source_parent_folder_token is not None and source.get("parent_folder_token") != source_parent_folder_token:
        raise GuardError("source_parent_folder_token 与 before_state 不一致")
    source_name = _require_non_empty_str(source.get("name"), "before_state.source.name")

    target_parent = _require_dict(before_state.get("target_parent"), "before_state.target_parent")
    if target_parent.get("folder_token") != target_parent_folder_token:
        raise GuardError("target_parent_folder_token 与 before_state 不一致")

    title = changes.get("name", source_name)
    title = _require_non_empty_str(title, "changes.name")
    target_titles, _ = _collect_named_children(
        target_parent.get("children", []),
        "before_state.target_parent.children",
        "token",
        title_field="name",
        allow_empty_titles=True,
    )
    if operation == "move" and source_parent_folder_token == target_parent_folder_token and title == source_name:
        raise GuardError("Drive 移动预览目标未发生变化")
    if title in target_titles:
        raise GuardError("目标文件夹已有同名子项")
    expected_data = {"folder_token": target_parent_folder_token, "type": source_type}
    if operation == "copy":
        expected_data["name"] = title
    expected_arguments = {
        "path": {"file_token": source_token},
        "data": expected_data,
        "useUAT": True,
    }
    if changes.get("apply_arguments") != expected_arguments:
        raise GuardError(f"Drive {operation} 调用参数与预览范围不一致")


def _validate_drive_version_plan(scope: Any, before_state: Any, changes: Any) -> None:
    _validate_drive_plan(scope, before_state, changes, "update")
    resource = _require_dict(before_state.get("resource"), "before_state.resource")
    resource_token = _require_non_empty_str(scope.get("resource_token"), "scope.resource_token")
    resource_type = _require_non_empty_str(scope.get("resource_type"), "scope.resource_type")
    if resource_type not in DRIVE_VERSION_SOURCE_TYPES:
        raise GuardError(f"Drive 版本创建不支持资源类型 {resource_type}")
    if resource.get("token") != resource_token:
        raise GuardError("scope.resource_token 与 before_state.resource.token 不一致")
    if resource.get("type") != resource_type:
        raise GuardError("scope.resource_type 与 before_state.resource.type 不一致")
    versions = before_state.get("versions")
    if not isinstance(versions, list) or before_state.get("versions_complete") is not True:
        raise GuardError("Drive 版本列表必须完整")
    version_name = _require_non_empty_str(changes.get("name"), "changes.name")
    existing_names = {
        _require_non_empty_str(item.get("name"), f"before_state.versions[{index}].name")
        for index, item in enumerate(versions)
        if isinstance(item, dict)
    }
    if len(existing_names) != len(versions):
        raise GuardError("Drive 版本列表包含无效或重复条目")
    if version_name in existing_names:
        raise GuardError("目标文档已有同名版本")
    expected_arguments = {
        "path": {"file_token": resource_token},
        "data": {"name": version_name, "obj_type": resource_type},
        "useUAT": True,
    }
    if changes.get("apply_arguments") != expected_arguments:
        raise GuardError("Drive 版本创建调用参数与预览范围不一致")


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


def _column_number(label: str) -> int:
    value = 0
    for character in label:
        value = value * 26 + ord(character) - ord("A") + 1
    return value


def _sheets_range_bounds(value: Any, expected_sheet_id: str) -> tuple[int, int, int, int]:
    match = SHEETS_RANGE_RE.fullmatch(value) if isinstance(value, str) else None
    if not match or match.group(1) != expected_sheet_id:
        raise GuardError("Sheets 范围必须是当前工作表的矩形 A1 区域")
    start_column, start_row = _column_number(match.group(2)), int(match.group(3))
    end_column, end_row = _column_number(match.group(4)), int(match.group(5))
    if start_column > end_column or start_row > end_row:
        raise GuardError("Sheets 范围起点不能晚于终点")
    return start_column, start_row, end_column, end_row


def _validate_sheets_cells(cells: Any, field: str, sheet_id: str, bounds: tuple[int, int, int, int]) -> list[str]:
    values = _string_list(cells, field, allow_empty=True)
    start_column, start_row, end_column, end_row = bounds
    for cell in values:
        match = SHEETS_CELL_RE.fullmatch(cell)
        if not match or match.group(1) != sheet_id:
            raise GuardError(f"{field} 包含其他工作表或无效单元格")
        column, row = _column_number(match.group(2)), int(match.group(3))
        if not (start_column <= column <= end_column and start_row <= row <= end_row):
            raise GuardError(f"{field} 包含预览范围外单元格")
    return values


def _validate_sheets_replace_plan(
    scope: Any,
    before_state: Any,
    changes: Any,
    verification: Any,
    operation: str,
) -> None:
    required_scope = ("spreadsheet_token", "spreadsheet_title", "sheet_id", "sheet_title", "range")
    if operation != "replace":
        raise GuardError("Sheets 预览当前只支持限定范围 replace")
    if not isinstance(scope, dict) or scope.get("entity") != "cells" or any(
        not isinstance(scope.get(field), str) or not scope[field].strip() for field in required_scope
    ):
        raise GuardError("Sheets 预览必须唯一指定电子表格、工作表和范围")
    bounds = _sheets_range_bounds(scope["range"], scope["sheet_id"])
    if not isinstance(before_state, dict) or any(
        before_state.get(field) != scope[field] for field in required_scope
    ):
        raise GuardError("Sheets 当前状态与预览目标不一致")

    sheets = before_state.get("sheets")
    if not isinstance(sheets, list) or not sheets:
        raise GuardError("Sheets 当前状态必须包含完整工作表清单")
    selected = []
    sheet_ids = set()
    for sheet in sheets:
        if not isinstance(sheet, dict) or any(
            not isinstance(sheet.get(field), str) or not sheet[field].strip()
            for field in ("sheet_id", "title")
        ):
            raise GuardError("Sheets 工作表清单不完整")
        if sheet["sheet_id"] in sheet_ids:
            raise GuardError("Sheets 工作表清单包含重复 sheet_id")
        sheet_ids.add(sheet["sheet_id"])
        if sheet["sheet_id"] == scope["sheet_id"]:
            selected.append(sheet)
    if len(selected) != 1 or selected[0]["title"] != scope["sheet_title"]:
        raise GuardError("Sheets 工作表 ID 与标题不能唯一对应")

    condition = before_state.get("find_condition")
    if not isinstance(condition, dict) or any(
        not isinstance(condition.get(field), bool)
        for field in ("match_case", "match_entire_cell", "search_by_regex", "include_formulas")
    ):
        raise GuardError("Sheets 查找条件必须显式指定四个布尔选项")
    if condition["search_by_regex"] or condition["include_formulas"] or not condition["match_entire_cell"]:
        raise GuardError("Sheets 当前仅支持纯文本整格匹配")
    find = before_state.get("find")
    replacement = before_state.get("replacement")
    if not isinstance(find, str) or not find or not isinstance(replacement, str) or find == replacement:
        raise GuardError("Sheets 查找值必须非空且与替换值不同")
    if not before_state.get("find_complete") or not before_state.get("replacement_find_complete"):
        raise GuardError("Sheets 查找结果必须完整")
    matches = _validate_sheets_cells(
        before_state.get("matches"), "before_state.matches", scope["sheet_id"], bounds
    )
    replacement_matches = _validate_sheets_cells(
        before_state.get("replacement_matches"),
        "before_state.replacement_matches",
        scope["sheet_id"],
        bounds,
    )
    if not matches or set(matches) & set(replacement_matches):
        raise GuardError("Sheets 替换必须有匹配项，且新旧值匹配单元格不能重叠")
    if scope.get("match_count") != len(matches):
        raise GuardError("Sheets 匹配数量与预览范围不一致")

    if not isinstance(changes, dict) or any(
        changes.get(field) != before_state[field]
        for field in ("find", "replacement", "find_condition")
    ):
        raise GuardError("Sheets 替换内容或条件与当前状态不一致")
    if changes.get("matched_cells") != matches or changes.get(
        "preexisting_replacement_cells"
    ) != replacement_matches:
        raise GuardError("Sheets 预览匹配清单与当前查找结果不一致")
    if changes.get("replacement_count") != len(matches):
        raise GuardError("Sheets 替换数量与匹配清单不一致")
    expected_arguments = {
        "path": {
            "spreadsheet_token": scope["spreadsheet_token"],
            "sheet_id": scope["sheet_id"],
        },
        "data": {
            "find": find,
            "replacement": replacement,
            "find_condition": {**condition, "range": scope["range"]},
        },
        "useUAT": True,
    }
    if changes.get("apply_arguments") != expected_arguments:
        raise GuardError("Sheets 替换调用参数与预览范围或条件不一致")
    if not isinstance(changes.get("pending_confirmations"), list):
        raise GuardError("Sheets 预览必须包含 changes.pending_confirmations 数组")

    expected_replacement_matches = sorted(set(matches) | set(replacement_matches))
    if not isinstance(verification, dict) or verification != {
        "range": scope["range"],
        "old_value_matches": [],
        "replacement_matches": expected_replacement_matches,
        "outside_range_check": "manual",
    }:
        raise GuardError("Sheets 写后验证必须固定旧值、新值和范围外人工检查")


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


def _validate_project_register_table_plan(
    scope: Any,
    before_state: Any,
    changes: Any,
    verification: Any,
    operation: str,
) -> None:
    if operation != "create":
        raise GuardError("项目台账表结构预览只支持 create")
    if not isinstance(scope, dict) or scope.get("entity") != "table":
        raise GuardError("项目台账表结构预览必须指定 scope.entity=table")
    app_token = _require_non_empty_str(scope.get("app_token"), "scope.app_token")
    table_name = _require_non_empty_str(scope.get("table_name"), "scope.table_name")
    role = _require_non_empty_str(scope.get("register_role"), "scope.register_role")
    if role not in PROJECT_REGISTER_SCHEMAS:
        raise GuardError(f"不支持的项目台账类型：{role}")

    before_state = _require_dict(before_state, "Bitable 当前状态")
    if before_state.get("app_token") != app_token:
        raise GuardError("Bitable 当前状态与项目台账目标不一致")
    if before_state.get("tables_pagination_complete") is not True:
        raise GuardError("Bitable 数据表清单必须完成完整分页")
    tables = before_state.get("tables")
    if not isinstance(tables, list):
        raise GuardError("Bitable 当前状态必须包含数据表清单")
    table_ids: set[str] = set()
    for table in tables:
        table = _require_dict(table, "table")
        table_id = _require_non_empty_str(table.get("table_id"), "table.table_id")
        _require_non_empty_str(table.get("table_name"), "table.table_name")
        if table_id in table_ids:
            raise GuardError("Bitable 数据表清单包含重复 table_id")
        table_ids.add(table_id)
    if any(table["table_name"] == table_name for table in tables):
        raise GuardError(f"Bitable 已存在同名项目台账：{table_name}")

    changes = _require_dict(changes, "项目台账变更")
    table_plan = _require_dict(changes.get("table"), "changes.table")
    if table_plan.get("name") != table_name:
        raise GuardError("项目台账名称与预览目标不一致")
    _require_non_empty_str(table_plan.get("default_view_name"), "changes.table.default_view_name")
    schema = PROJECT_REGISTER_SCHEMAS[role]
    if canonical_json(table_plan.get("fields")) != canonical_json(schema["fields"]):
        raise GuardError(f"项目台账字段契约不匹配：{role}")
    if changes.get("business_key_field") != schema["business_key_field"]:
        raise GuardError("项目台账业务主键与字段契约不一致")
    if changes.get("source_field") != schema["source_field"]:
        raise GuardError("项目台账来源字段与字段契约不一致")
    if not isinstance(changes.get("pending_confirmations"), list):
        raise GuardError("项目台账预览必须包含 changes.pending_confirmations 数组")

    verification = _require_dict(verification, "项目台账回读计划")
    expected_verification = {
        "table_name": table_name,
        "field_names": [field["field_name"] for field in schema["fields"]],
        "business_key_field": schema["business_key_field"],
        "source_field": schema["source_field"],
    }
    if verification != expected_verification:
        raise GuardError("项目台账回读计划与字段契约不一致")


def _validate_bitable_plan(
    scope: Any,
    before_state: Any,
    changes: Any,
    verification: Any,
    operation: str,
) -> None:
    if isinstance(scope, dict) and scope.get("entity") == "table":
        _validate_project_register_table_plan(
            scope, before_state, changes, verification, operation
        )
        return
    _validate_bitable_record_plan(scope, before_state, changes, operation)


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
    if spec["resource_type"] == "docx":
        if operation not in DOCX_WRITE_OPERATIONS:
            raise GuardError("docx 写预览只支持 create/append/insert/replace")
        if operation == "create":
            _validate_docx_create(spec["scope"], spec["changes"])
        elif operation in DOCX_EDIT_OPERATIONS:
            _validate_docx_edit(spec["scope"], spec["before_state"], spec["changes"], spec.get("risks", []))
    if spec["resource_type"] == "bitable":
        _validate_bitable_plan(
            spec["scope"],
            spec["before_state"],
            spec["changes"],
            spec["verification"],
            operation,
        )
    if spec["resource_type"] == "sheets":
        _validate_sheets_replace_plan(
            spec["scope"],
            spec["before_state"],
            spec["changes"],
            spec["verification"],
            operation,
        )
    if spec["resource_type"] == "wiki":
        _validate_wiki_plan(spec["scope"], spec["before_state"], spec["changes"], operation)
    if spec["resource_type"] == "drive":
        if operation == "update":
            _validate_drive_version_plan(spec["scope"], spec["before_state"], spec["changes"])
        else:
            _validate_drive_plan(spec["scope"], spec["before_state"], spec["changes"], operation)

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
    expected_id = "fs-" + fingerprint(_preview_payload(preview))[:16]
    if expected_id != preview.get("preview_id"):
        raise GuardError("预览内容已被修改")
    if fingerprint(current_state) != preview.get("before_fingerprint"):
        raise GuardError("目标在预览后发生变化，必须重新生成预览")

    if preview["resource_type"] == "docx":
        if operation not in DOCX_WRITE_OPERATIONS:
            raise GuardError("docx 写预览只支持 create/append/insert/replace")
        if operation == "create":
            _validate_docx_create(preview["scope"], preview["changes"])
        elif operation in DOCX_EDIT_OPERATIONS:
            _validate_docx_edit(preview["scope"], current_state, preview["changes"], preview.get("risks", []))
    if not isinstance(preview["required_tools"], list) or not preview["required_tools"]:
        raise GuardError("required_tools 必须是非空数组")

    identity_parameters(
        preview.get("identity", "user"),
        explicit_application=bool(preview.get("application_identity_explicit", False)),
    )

    if preview["resource_type"] == "bitable":
        _validate_bitable_plan(
            preview["scope"],
            current_state,
            preview["changes"],
            preview["verification"],
            operation,
        )
    if preview["resource_type"] == "sheets":
        _validate_sheets_replace_plan(
            preview["scope"],
            current_state,
            preview["changes"],
            preview["verification"],
            operation,
        )
    if preview["resource_type"] == "wiki":
        _validate_wiki_plan(preview["scope"], current_state, preview["changes"], operation)
    if preview["resource_type"] == "drive":
        if operation == "update":
            _validate_drive_version_plan(preview["scope"], current_state, preview["changes"])
        else:
            _validate_drive_plan(preview["scope"], current_state, preview["changes"], operation)

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

    defaults = commands.add_parser("validate-defaults")
    defaults.add_argument("config", help="JSON file path, or - for stdin")

    project_audit = commands.add_parser("validate-project-audit")
    project_audit.add_argument("audit", help="JSON file path, or - for stdin")

    project_preview_plan = commands.add_parser("validate-project-preview-plan")
    project_preview_plan.add_argument("plan", help="JSON file path, or - for stdin")

    project_integration = commands.add_parser("validate-project-integration")
    project_integration.add_argument("result", help="JSON file path, or - for stdin")

    args = parser.parse_args(argv)
    try:
        if args.command == "classify-url":
            result = classify_feishu_url(args.url)
        elif args.command == "identity":
            result = identity_parameters(args.identity, explicit_application=args.explicit)
        elif args.command == "make-preview":
            result = make_preview(load_json(args.spec))
        elif args.command == "validate-defaults":
            result = validate_default_locations(load_json(args.config))
        elif args.command == "validate-project-audit":
            result = validate_project_audit(load_json(args.audit))
        elif args.command == "validate-project-preview-plan":
            result = validate_project_preview_plan(load_json(args.plan))
        elif args.command == "validate-project-integration":
            result = validate_project_integration(load_json(args.result))
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
