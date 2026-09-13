import unittest

from scripts.feishu_guard import (
    GuardError,
    classify_feishu_url,
    identity_parameters,
    make_preview,
    missing_tools,
    summarize_batch_outcomes,
    validate_default_locations,
    validate_feishu_tool,
    validate_mode,
    validate_preview,
    validate_project_audit,
    validate_project_integration,
    validate_project_preview_plan,
)


READ_TOOL = "mcp__feishu__docx_v1_document_get"
WRITE_TOOL = "mcp__feishu__docx_v1_documentBlock_patch"
CREATE_TOOL = "mcp__feishu__wiki_v2_spaceNode_create"
CREATE_BLOCKS_TOOL = "mcp__feishu__docx_v1_documentBlockChildren_create"
BITABLE_READ_TOOL = "mcp__feishu__bitable_v1_appTableRecord_search"
BITABLE_CREATE_TOOL = "mcp__feishu__bitable_v1_appTableRecord_create"
BITABLE_UPDATE_TOOL = "mcp__feishu__bitable_v1_appTableRecord_update"
BITABLE_TABLE_LIST_TOOL = "mcp__feishu__bitable_v1_appTable_list"
BITABLE_TABLE_CREATE_TOOL = "mcp__feishu__bitable_v1_appTable_create"
BITABLE_FIELD_LIST_TOOL = "mcp__feishu__bitable_v1_appTableField_list"
SHEETS_FIND_TOOL = "mcp__feishu__sheets_v3_spreadsheetSheet_find"
SHEETS_REPLACE_TOOL = "mcp__feishu__sheets_v3_spreadsheetSheet_replace"
WIKI_CREATE_TOOL = "mcp__feishu__wiki_v2_spaceNode_create"
WIKI_COPY_TOOL = "mcp__feishu__wiki_v2_spaceNode_copy"
WIKI_MOVE_TOOL = "mcp__feishu__wiki_v2_spaceNode_move"
WIKI_UPDATE_TOOL = "mcp__feishu__wiki_v2_spaceNode_updateTitle"
WIKI_IMPORT_TOOL = "mcp__feishu__wiki_v2_spaceNode_moveDocsToWiki"
WIKI_TASK_GET_TOOL = "mcp__feishu__wiki_v2_task_get"
DRIVE_FILE_LIST_TOOL = "mcp__feishu__drive_v1_file_list"
DRIVE_FOLDER_CREATE_TOOL = "mcp__feishu__drive_v1_file_createFolder"
DRIVE_FILE_COPY_TOOL = "mcp__feishu__drive_v1_file_copy"
DRIVE_FILE_MOVE_TOOL = "mcp__feishu__drive_v1_file_move"
DRIVE_VERSION_TOOL = "mcp__feishu__drive_v1_fileVersion_create"
DRIVE_VERSION_GET_TOOL = "mcp__feishu__drive_v1_fileVersion_get"
DRIVE_VERSION_LIST_TOOL = "mcp__feishu__drive_v1_fileVersion_list"
DRIVE_EXPORT_CREATE_TOOL = "mcp__feishu__drive_v1_exportTask_create"
DRIVE_EXPORT_GET_TOOL = "mcp__feishu__drive_v1_exportTask_get"
DRIVE_IMPORT_CREATE_TOOL = "mcp__feishu__drive_v1_importTask_create"
DRIVE_IMPORT_GET_TOOL = "mcp__feishu__drive_v1_importTask_get"


def preview_spec(**overrides):
    spec = {
        "target": "https://example.feishu.cn/docx/doccnTest",
        "resource_type": "docx",
        "identity": "user",
        "operation": "replace",
        "scope": {
            "selector": {
                "heading_block_id": "heading-test",
                "heading_path": ["测试章节"],
                "match_count": 1,
            },
            "target_block_ids": ["heading-test", "block-test", "unknown-test"],
            "boundary": {"before": None, "after": "heading-next"},
        },
        "before_state": {
            "revision_id": 1,
            "blocks": [
                {"block_id": "heading-test", "kind": "heading", "support": "readable"},
                {"block_id": "block-test", "kind": "text", "support": "readable"},
                {"block_id": "unknown-test", "kind": "unknown", "support": "opaque"},
                {"block_id": "heading-next", "kind": "heading", "support": "readable"},
            ],
        },
        "changes": {
            "before_blocks": [{"block_id": "block-test", "kind": "text", "content": "before"}],
            "after_blocks": [{"kind": "text", "content": "after"}],
            "affected_block_ids": ["block-test"],
            "preserved_block_ids": ["unknown-test"],
            "format_fallbacks": [],
            "pending_confirmations": [],
        },
        "risks": [],
        "required_tools": [WRITE_TOOL, READ_TOOL],
        "verification": {"text": "after"},
    }
    spec.update(overrides)
    return spec


def create_preview_spec(**overrides):
    spec = {
        "target": "https://example.feishu.cn/wiki/parent",
        "resource_type": "docx",
        "identity": "user",
        "operation": "create",
        "scope": {"parent": "https://example.feishu.cn/wiki/parent", "placement": "wiki_child"},
        "before_state": {"parent_revision": 1, "children": []},
        "changes": {
            "title": "测试技术方案",
            "template": "technical_design",
            "blocks": [{"kind": "heading1", "content": "摘要"}],
            "pending_confirmations": [],
        },
        "risks": [],
        "required_tools": [CREATE_TOOL, CREATE_BLOCKS_TOOL, READ_TOOL],
        "verification": {"title": "测试技术方案", "block_count": 1},
    }
    spec.update(overrides)
    return spec


def bitable_preview_spec(operation="create", **overrides):
    records = [
        {
            "record_id": None if operation == "create" else "rec-1",
            "business_key_value": "P-002" if operation == "create" else "P-001",
            "before_fields": {} if operation == "create" else {"状态": "进行中"},
            "after_fields": (
                {"项目编号": "P-002", "状态": "未开始"}
                if operation == "create"
                else {"状态": "已完成"}
            ),
            "field_differences": (
                [
                    {"field": "状态", "before": None, "after": "未开始"},
                    {"field": "项目编号", "before": None, "after": "P-002"},
                ]
                if operation == "create"
                else [{"field": "状态", "before": "进行中", "after": "已完成"}]
            ),
        }
    ]
    spec = {
        "target": "https://example.feishu.cn/base/bascnTest",
        "resource_type": "bitable",
        "identity": "user",
        "operation": operation,
        "scope": {
            "entity": "records",
            "app_token": "bascnTest",
            "table_id": "tblTest",
            "table_name": "项目台账",
            "business_key_field": "项目编号",
            "record_count": 1,
        },
        "before_state": {
            "app_token": "bascnTest",
            "table_id": "tblTest",
            "table_name": "项目台账",
            "fields_pagination_complete": True,
            "records_pagination_complete": True,
            "fields": [
                {"field_id": "fld-key", "field_name": "项目编号", "ui_type": "Text"},
                {
                    "field_id": "fld-status",
                    "field_name": "状态",
                    "ui_type": "SingleSelect",
                    "options": ["未开始", "进行中", "已完成"],
                },
                {"field_id": "fld-budget", "field_name": "预算", "ui_type": "Number"},
                {"field_id": "fld-formula", "field_name": "汇总", "ui_type": "Formula"},
            ],
            "records": [
                {"record_id": "rec-1", "fields": {"项目编号": "P-001", "状态": "进行中"}}
            ],
        },
        "changes": {
            "records": records,
            "quality_issues": [],
            "pending_confirmations": [],
        },
        "risks": [],
        "required_tools": [
            BITABLE_READ_TOOL,
            BITABLE_CREATE_TOOL if operation == "create" else BITABLE_UPDATE_TOOL,
        ],
        "verification": {"business_keys": [records[0]["business_key_value"]]},
    }
    spec.update(overrides)
    return spec


def project_register_preview_spec(role="action_items", **overrides):
    contracts = {
        "action_items": (
            "M5 行动项",
            "行动项编号",
            [
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
        ),
        "risks": (
            "M5 风险",
            "风险编号",
            [
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
        ),
        "decisions": (
            "M5 决策",
            "决策编号",
            [
                {"field_name": "决策编号", "type": 1, "ui_type": "Text"},
                {"field_name": "结论", "type": 1, "ui_type": "Text"},
                {"field_name": "原因", "type": 1, "ui_type": "Text"},
                {"field_name": "决策人", "type": 1, "ui_type": "Text"},
                {"field_name": "决策日期", "type": 5, "ui_type": "DateTime"},
                {"field_name": "来源链接", "type": 15, "ui_type": "Url"},
            ],
        ),
        "metrics": (
            "M5 指标",
            "指标编号",
            [
                {"field_name": "指标编号", "type": 1, "ui_type": "Text"},
                {"field_name": "指标名称", "type": 1, "ui_type": "Text"},
                {"field_name": "当前值", "type": 2, "ui_type": "Number"},
                {"field_name": "单位", "type": 1, "ui_type": "Text"},
                {"field_name": "状态日期", "type": 5, "ui_type": "DateTime"},
                {"field_name": "来源链接", "type": 15, "ui_type": "Url"},
            ],
        ),
    }
    table_name, business_key, fields = contracts[role]
    spec = {
        "target": "https://example.feishu.cn/base/bascnProject",
        "resource_type": "bitable",
        "identity": "user",
        "operation": "create",
        "scope": {
            "entity": "table",
            "app_token": "bascnProject",
            "register_role": role,
            "table_name": table_name,
        },
        "before_state": {
            "app_token": "bascnProject",
            "tables_pagination_complete": True,
            "tables": [{"table_id": "tblExisting", "table_name": "Table"}],
        },
        "changes": {
            "table": {"name": table_name, "default_view_name": "全部记录", "fields": fields},
            "business_key_field": business_key,
            "source_field": "来源链接",
            "pending_confirmations": [],
        },
        "risks": [],
        "required_tools": [
            BITABLE_TABLE_LIST_TOOL,
            BITABLE_TABLE_CREATE_TOOL,
            BITABLE_FIELD_LIST_TOOL,
        ],
        "verification": {
            "table_name": table_name,
            "field_names": [field["field_name"] for field in fields],
            "business_key_field": business_key,
            "source_field": "来源链接",
        },
    }
    spec.update(overrides)
    return spec


def sheets_preview_spec(**overrides):
    condition = {
        "match_case": True,
        "match_entire_cell": True,
        "search_by_regex": False,
        "include_formulas": False,
    }
    spec = {
        "target": "https://example.feishu.cn/sheets/shtcnTest",
        "resource_type": "sheets",
        "identity": "user",
        "operation": "replace",
        "scope": {
            "entity": "cells",
            "spreadsheet_token": "shtcnTest",
            "spreadsheet_title": "测试表格",
            "sheet_id": "sheet1",
            "sheet_title": "数据",
            "range": "sheet1!A2:B4",
            "match_count": 2,
        },
        "before_state": {
            "spreadsheet_token": "shtcnTest",
            "spreadsheet_title": "测试表格",
            "sheet_id": "sheet1",
            "sheet_title": "数据",
            "range": "sheet1!A2:B4",
            "sheets": [
                {"sheet_id": "sheet1", "title": "数据"},
                {"sheet_id": "sheet2", "title": "归档"},
            ],
            "find": "旧状态",
            "replacement": "新状态",
            "find_condition": condition,
            "find_complete": True,
            "replacement_find_complete": True,
            "matches": ["sheet1!A2", "sheet1!B4"],
            "replacement_matches": ["sheet1!A3"],
        },
        "changes": {
            "find": "旧状态",
            "replacement": "新状态",
            "find_condition": condition,
            "matched_cells": ["sheet1!A2", "sheet1!B4"],
            "preexisting_replacement_cells": ["sheet1!A3"],
            "replacement_count": 2,
            "apply_arguments": {
                "path": {"spreadsheet_token": "shtcnTest", "sheet_id": "sheet1"},
                "data": {
                    "find": "旧状态",
                    "replacement": "新状态",
                    "find_condition": {**condition, "range": "sheet1!A2:B4"},
                },
                "useUAT": True,
            },
            "pending_confirmations": [],
        },
        "risks": [],
        "required_tools": [SHEETS_FIND_TOOL, SHEETS_REPLACE_TOOL],
        "verification": {
            "range": "sheet1!A2:B4",
            "old_value_matches": [],
            "replacement_matches": ["sheet1!A2", "sheet1!A3", "sheet1!B4"],
            "outside_range_check": "manual",
        },
    }
    spec.update(overrides)
    return spec


def wiki_preview_spec(operation="create", **overrides):
    if operation == "create":
        scope = {
            "space_id": "spc123",
            "parent_node_token": "wiki-parent",
            "placement": "append",
        }
        before_state = {
            "space_id": "spc123",
            "parent_node_token": "wiki-parent",
            "parent_node_title": "测试知识库",
            "children": [
                {"node_token": "wiki-existing", "title": "已有子节点", "node_type": "docx"},
            ],
        }
        changes = {
            "title": "测试 Wiki 节点",
            "node_type": "docx",
            "pending_confirmations": [],
        }
        required_tools = [WIKI_CREATE_TOOL]
    elif operation in {"copy", "move"}:
        scope = {
            "space_id": "spc123",
            "source_node_token": "wiki-source",
            "source_parent_node_token": "wiki-source-parent",
            "target_parent_node_token": "wiki-target-parent",
        }
        before_state = {
            "space_id": "spc123",
            "source_node": {
                "node_token": "wiki-source",
                "title": "源节点",
                "node_type": "docx",
                "parent_node_token": "wiki-source-parent",
            },
            "target_parent": {
                "parent_node_token": "wiki-target-parent",
                "parent_node_title": "目标目录",
                "children": [
                    {"node_token": "wiki-existing", "title": "同名节点", "node_type": "docx"},
                ],
            },
        }
        changes = {"title": "复制后的源节点", "pending_confirmations": []}
        required_tools = [WIKI_COPY_TOOL] if operation == "copy" else [WIKI_MOVE_TOOL]
    elif operation == "update":
        scope = {
            "space_id": "spc123",
            "node_token": "wiki-source",
            "parent_node_token": "wiki-parent",
        }
        before_state = {
            "space_id": "spc123",
            "node": {
                "node_token": "wiki-source",
                "title": "原标题",
                "node_type": "docx",
                "parent_node_token": "wiki-parent",
            },
        }
        changes = {"title": "新标题", "pending_confirmations": []}
        required_tools = [WIKI_UPDATE_TOOL]
    else:
        raise ValueError("unsupported wiki operation")

    spec = {
        "target": "https://example.feishu.cn/wiki/wiki-source",
        "resource_type": "wiki",
        "identity": "user",
        "operation": operation,
        "scope": scope,
        "before_state": before_state,
        "changes": changes,
        "risks": [],
        "required_tools": required_tools,
        "verification": {"node_token": "wiki-source"},
    }
    spec.update(overrides)
    return spec


def drive_preview_spec(operation="create", **overrides):
    if operation == "create":
        scope = {
            "parent_folder_token": "",
            "resource_type": "folder",
        }
        before_state = {
            "folder_token": "",
            "folder_name": "根目录",
            "children": [
                {"token": "fld-existing", "name": "已有文件夹", "type": "folder"},
            ],
        }
        changes = {
            "name": "测试目录",
            "resource_type": "folder",
            "apply_arguments": {
                "data": {"folder_token": "", "name": "测试目录"},
                "useUAT": True,
            },
            "pending_confirmations": [],
        }
        required_tools = [DRIVE_FILE_LIST_TOOL, DRIVE_FOLDER_CREATE_TOOL]
    elif operation in {"copy", "move"}:
        scope = {
            "source_token": "file-source",
            "source_type": "file",
            "source_parent_folder_token": "fld-source",
            "target_parent_folder_token": "fld-target",
        }
        before_state = {
            "source": {
                "token": "file-source",
                "type": "file",
                "name": "原文件.docx",
                "parent_folder_token": "fld-source",
            },
            "target_parent": {
                "folder_token": "fld-target",
                "folder_name": "目标目录",
                "children": [
                    {"token": "file-other", "name": "其他文件.docx", "type": "file"},
                ],
            },
        }
        apply_data = {"folder_token": "fld-target", "type": "file"}
        if operation == "copy":
            apply_data["name"] = "复制后的原文件.docx"
        changes = {
            "name": "复制后的原文件.docx",
            "apply_arguments": {
                "path": {"file_token": "file-source"},
                "data": apply_data,
                "useUAT": True,
            },
            "pending_confirmations": [],
        }
        required_tools = [DRIVE_FILE_COPY_TOOL] if operation == "copy" else [DRIVE_FILE_MOVE_TOOL]
    elif operation == "update":
        scope = {
            "resource_token": "file-source",
            "resource_type": "docx",
        }
        before_state = {
            "resource": {
                "token": "file-source",
                "type": "docx",
                "name": "原文件.docx",
            },
            "versions": [],
            "versions_complete": True,
        }
        changes = {
            "name": "M4 版本能力验收",
            "apply_arguments": {
                "path": {"file_token": "file-source"},
                "data": {"name": "M4 版本能力验收", "obj_type": "docx"},
                "useUAT": True,
            },
            "pending_confirmations": [],
        }
        required_tools = [DRIVE_VERSION_LIST_TOOL, DRIVE_VERSION_TOOL, DRIVE_VERSION_GET_TOOL]
    else:
        raise ValueError("unsupported drive operation")

    spec = {
        "target": "https://example.feishu.cn/drive/folder/fld-source",
        "resource_type": "drive",
        "identity": "user",
        "operation": operation,
        "scope": scope,
        "before_state": before_state,
        "changes": changes,
        "risks": [],
        "required_tools": required_tools,
        "verification": {"folder_token": "fld-source"},
    }
    spec.update(overrides)
    return spec


def wiki_import_preview_spec(**overrides):
    scope = {
        "entity": "drive_document",
        "space_id": "spc123",
        "source_token": "docx-source",
        "source_type": "docx",
        "source_parent_folder_token": "fld-source",
        "target_parent_node_token": "wiki-parent",
    }
    before_state = {
        "space_id": "spc123",
        "source_document": {
            "token": "docx-source",
            "type": "docx",
            "title": "待入库文档",
            "parent_folder_token": "fld-source",
        },
        "target_parent": {
            "space_id": "spc123",
            "parent_node_token": "wiki-parent",
            "title": "测试知识库",
            "children": [{"node_token": "wiki-other", "title": "已有文档"}],
        },
    }
    changes = {
        "apply_arguments": {
            "path": {"space_id": "spc123"},
            "data": {
                "obj_token": "docx-source",
                "obj_type": "docx",
                "parent_wiki_token": "wiki-parent",
                "apply": False,
            },
            "useUAT": True,
        },
        "pending_confirmations": [],
    }
    spec = {
        "target": "https://example.feishu.cn/wiki/wiki-parent",
        "resource_type": "wiki",
        "identity": "user",
        "operation": "move",
        "scope": scope,
        "before_state": before_state,
        "changes": changes,
        "risks": [],
        "required_tools": [DRIVE_FILE_LIST_TOOL, WIKI_IMPORT_TOOL, WIKI_TASK_GET_TOOL],
        "verification": {"parent_node_token": "wiki-parent", "title": "待入库文档"},
    }
    spec.update(overrides)
    return spec


def drive_export_preview_spec(**overrides):
    spec = {
        "target": "https://example.feishu.cn/docx/docx-source",
        "resource_type": "drive",
        "identity": "user",
        "operation": "create",
        "scope": {
            "entity": "export_task",
            "source_token": "docx-source",
            "source_type": "docx",
            "file_extension": "docx",
        },
        "before_state": {
            "source": {"token": "docx-source", "type": "docx", "title": "待导出文档"}
        },
        "changes": {
            "apply_arguments": {
                "data": {"token": "docx-source", "type": "docx", "file_extension": "docx"},
                "useUAT": True,
            },
            "pending_confirmations": [],
        },
        "risks": [],
        "required_tools": [DRIVE_EXPORT_CREATE_TOOL, DRIVE_EXPORT_GET_TOOL],
        "verification": {"file_extension": "docx"},
    }
    spec.update(overrides)
    return spec


def drive_import_preview_spec(**overrides):
    spec = {
        "target": "https://example.feishu.cn/drive/folder/fld-target",
        "resource_type": "drive",
        "identity": "user",
        "operation": "create",
        "scope": {
            "entity": "import_task",
            "source_file_token": "exported-file",
            "file_extension": "docx",
            "target_type": "docx",
            "target_folder_token": "fld-target",
        },
        "before_state": {
            "source_file": {
                "token": "exported-file",
                "file_extension": "docx",
                "file_name": "源文件.docx",
                "file_size": 1024,
                "provenance": "file_upload",
                "type": "file",
            },
            "target_parent": {
                "folder_token": "fld-target",
                "folder_name": "测试目录",
                "children": [{"token": "other", "name": "已有文档", "type": "docx"}],
            },
        },
        "changes": {
            "file_name": "导入能力验收",
            "apply_arguments": {
                "data": {
                    "file_extension": "docx",
                    "file_name": "导入能力验收",
                    "file_token": "exported-file",
                    "point": {"mount_key": "fld-target", "mount_type": 1},
                    "type": "docx",
                },
                "useUAT": True,
            },
            "pending_confirmations": [],
        },
        "risks": [],
        "required_tools": [DRIVE_FILE_LIST_TOOL, DRIVE_IMPORT_CREATE_TOOL, DRIVE_IMPORT_GET_TOOL],
        "verification": {"file_name": "导入能力验收", "target_type": "docx"},
    }
    spec.update(overrides)
    return spec


class UrlTests(unittest.TestCase):
    def test_classifies_supported_feishu_links(self):
        cases = {
            "docx": "docx",
            "sheets": "sheets",
            "base": "bitable",
            "wiki": "wiki",
            "drive": "drive",
            "minutes": "minutes",
            "board": "board",
            "slides": "slides",
            "mindnotes": "mindnote",
        }
        for segment, expected in cases.items():
            with self.subTest(segment=segment):
                result = classify_feishu_url(f"https://example.feishu.cn/{segment}/token123?x=1")
                self.assertEqual(expected, result["resource_type"])
                self.assertEqual("token123", result["token"])

    def test_rejects_non_china_or_non_https_links(self):
        for url in (
            "https://example.larksuite.com/docx/token",
            "http://example.feishu.cn/docx/token",
            "https://example.com/docx/token",
        ):
            with self.subTest(url=url), self.assertRaises(GuardError):
                classify_feishu_url(url)

    def test_extracts_nested_drive_folder_token(self):
        result = classify_feishu_url("https://example.feishu.cn/drive/folder/fldcnTest")
        self.assertEqual("drive", result["resource_type"])
        self.assertEqual("fldcnTest", result["token"])

class IdentityAndTransportTests(unittest.TestCase):
    def test_user_identity_is_explicit_default(self):
        self.assertEqual({"identity": "user", "useUAT": True}, identity_parameters())

    def test_application_identity_requires_explicit_request(self):
        with self.assertRaises(GuardError):
            identity_parameters("application")
        self.assertEqual(
            {"identity": "application", "useUAT": False},
            identity_parameters("application", explicit_application=True),
        )

    def test_only_feishu_mcp_tools_are_allowed(self):
        validate_feishu_tool(READ_TOOL)
        for tool in ("web__run", "mcp__cua__click", "mcp__chrome__open", "direct_openapi"):
            with self.subTest(tool=tool), self.assertRaises(GuardError):
                validate_feishu_tool(tool)

    def test_only_apply_mode_can_mutate(self):
        for mode in ("analyze", "preview", "verify"):
            with self.subTest(mode=mode), self.assertRaises(GuardError):
                validate_mode(mode, mutating=True)
        validate_mode("apply", mutating=True)


class DefaultLocationTests(unittest.TestCase):
    def test_accepts_wiki_parent_and_drive_root(self):
        config = {
            "wiki": {"space_id": "7669390318399130909", "parent_node_token": "wiki-test"},
            "drive": {"folder_token": ""},
        }
        self.assertEqual(config, validate_default_locations(config))

    def test_rejects_incomplete_locations(self):
        for config in (
            {},
            {"wiki": {"space_id": "space", "parent_node_token": ""}, "drive": {"folder_token": ""}},
            {"wiki": {"space_id": "space", "parent_node_token": "node"}, "drive": {}},
        ):
            with self.subTest(config=config), self.assertRaises(GuardError):
                validate_default_locations(config)


class ProjectAuditTests(unittest.TestCase):
    def audit(self):
        return {
            "project_name": "M5 验收项目",
            "as_of": "2026-09-13",
            "sources": [
                {
                    "source_id": "SRC-001",
                    "resource_type": "docx",
                    "url": "https://example.feishu.cn/docx/doccnProject",
                    "title": "项目主页",
                    "read_scope": "完整文档块",
                    "read_complete": True,
                },
                {
                    "source_id": "SRC-002",
                    "resource_type": "bitable",
                    "url": "https://example.feishu.cn/base/bascnProject",
                    "title": "行动项台账",
                    "read_scope": "项目行动项筛选结果",
                    "read_complete": False,
                    "limitation": "仅有第一页，不能证明记录总数",
                },
            ],
            "claims": [
                {
                    "claim_id": "CLM-001",
                    "kind": "fact",
                    "category": "status",
                    "text": "项目主页存在",
                    "source_ids": ["SRC-001"],
                },
                {
                    "claim_id": "CLM-002",
                    "kind": "pending_confirmation",
                    "category": "action",
                    "text": "行动项总数待确认",
                    "source_ids": [],
                },
            ],
        }

    def test_accepts_source_traced_audit_and_reports_partial_sources(self):
        result = validate_project_audit(self.audit())
        self.assertEqual(2, result["source_count"])
        self.assertEqual(2, result["claim_count"])
        self.assertEqual(["SRC-002"], result["partial_source_ids"])

    def test_rejects_unsourced_or_unknown_claims(self):
        audit = self.audit()
        audit["claims"][0]["source_ids"] = []
        with self.assertRaisesRegex(GuardError, "非空"):
            validate_project_audit(audit)

        audit = self.audit()
        audit["claims"][0]["source_ids"] = ["SRC-999"]
        with self.assertRaisesRegex(GuardError, "未知来源"):
            validate_project_audit(audit)

    def test_rejects_mismatched_source_or_undisclosed_partial_read(self):
        audit = self.audit()
        audit["sources"][0]["resource_type"] = "wiki"
        with self.assertRaisesRegex(GuardError, "资源类型不一致"):
            validate_project_audit(audit)

        audit = self.audit()
        audit["sources"][1].pop("limitation")
        with self.assertRaisesRegex(GuardError, "limitation"):
            validate_project_audit(audit)


class ProjectPreviewPlanTests(unittest.TestCase):
    def plan(self):
        return {
            "project_name": "M5 验收项目",
            "steps": [
                {
                    "step_id": "STEP-001",
                    "resource_key": "HOME",
                    "role": "project_home",
                    "resource_type": "docx",
                    "operation": "create",
                    "preview_id": "fs-1111111111111111",
                    "depends_on": [],
                    "source_urls": ["https://example.feishu.cn/wiki/wikiProject"],
                    "linked_resource_keys": [],
                },
                {
                    "step_id": "STEP-002",
                    "resource_key": "PRD",
                    "role": "prd",
                    "resource_type": "docx",
                    "operation": "create",
                    "preview_id": "fs-2222222222222222",
                    "depends_on": ["STEP-001"],
                    "source_urls": ["https://example.feishu.cn/docx/doccnSource"],
                    "linked_resource_keys": [],
                },
                {
                    "step_id": "STEP-003",
                    "resource_key": "WEEKLY",
                    "role": "weekly_report",
                    "resource_type": "docx",
                    "operation": "create",
                    "preview_id": "fs-3333333333333333",
                    "depends_on": ["STEP-001"],
                    "source_urls": ["https://example.feishu.cn/base/bascnSource"],
                    "linked_resource_keys": [],
                    "period": {"start": "2026-09-07", "end": "2026-09-13"},
                },
                {
                    "step_id": "STEP-004",
                    "resource_key": "HOME",
                    "role": "project_home",
                    "resource_type": "docx",
                    "operation": "replace",
                    "preview_id": "fs-4444444444444444",
                    "depends_on": ["STEP-002", "STEP-003"],
                    "source_urls": [],
                    "linked_resource_keys": ["PRD", "WEEKLY"],
                },
            ],
        }

    def test_accepts_independent_previews_in_dependency_order(self):
        result = validate_project_preview_plan(self.plan())
        self.assertEqual(4, result["step_count"])
        self.assertEqual(["STEP-001", "STEP-002", "STEP-003", "STEP-004"], result["execution_order"])

    def test_rejects_reused_preview_or_forward_dependency(self):
        plan = self.plan()
        plan["steps"][1]["preview_id"] = plan["steps"][0]["preview_id"]
        with self.assertRaisesRegex(GuardError, "独立 preview_id"):
            validate_project_preview_plan(plan)

        plan = self.plan()
        plan["steps"][0]["depends_on"] = ["STEP-002"]
        with self.assertRaisesRegex(GuardError, "前序"):
            validate_project_preview_plan(plan)

    def test_requires_link_targets_and_valid_weekly_period(self):
        plan = self.plan()
        plan["steps"][3]["depends_on"] = ["STEP-002"]
        with self.assertRaisesRegex(GuardError, "链接资源"):
            validate_project_preview_plan(plan)

        plan = self.plan()
        plan["steps"][2]["period"] = {"start": "2026-09-14", "end": "2026-09-13"}
        with self.assertRaisesRegex(GuardError, "不能晚于"):
            validate_project_preview_plan(plan)


class ProjectIntegrationTests(unittest.TestCase):
    def result(self):
        return {
            "project_name": "M5 验收项目",
            "resources": [
                {
                    "resource_key": "HOME",
                    "resource_type": "wiki",
                    "url": "https://example.feishu.cn/wiki/wikiHome",
                    "status": "verified",
                    "read_complete": True,
                    "depends_on": [],
                },
                {
                    "resource_key": "ACTION",
                    "resource_type": "bitable",
                    "url": "https://example.feishu.cn/base/baseAction",
                    "status": "verified",
                    "read_complete": True,
                    "depends_on": [],
                },
            ],
            "links": [
                {
                    "source_resource_key": "HOME",
                    "target_resource_key": "ACTION",
                    "observed_url": "https://example.feishu.cn/base/baseAction",
                }
            ],
        }

    def test_accepts_complete_resources_and_exact_links(self):
        result = validate_project_integration(self.result())
        self.assertEqual("complete", result["overall_status"])
        self.assertEqual(2, result["resource_count"])
        self.assertEqual(1, result["link_count"])

    def test_partial_failure_keeps_dependent_resource_unattempted(self):
        result = self.result()
        result["resources"].extend(
            [
                {
                    "resource_key": "WEEKLY",
                    "resource_type": "wiki",
                    "url": "https://example.feishu.cn/wiki/wikiWeekly",
                    "status": "failed",
                    "read_complete": False,
                    "depends_on": ["HOME"],
                    "reason": "写入失败",
                },
                {
                    "resource_key": "SUMMARY",
                    "resource_type": "wiki",
                    "url": "https://example.feishu.cn/wiki/wikiSummary",
                    "status": "unattempted",
                    "read_complete": False,
                    "depends_on": ["WEEKLY"],
                    "reason": "前置周报未验证",
                },
            ]
        )
        validated = validate_project_integration(result)
        self.assertEqual("partial", validated["overall_status"])
        self.assertEqual(1, validated["counts"]["failed"])
        self.assertEqual(1, validated["counts"]["unattempted"])

    def test_rejects_verified_dependent_or_wrong_link(self):
        result = self.result()
        result["resources"][1].update(
            status="failed", read_complete=False, reason="读取失败"
        )
        result["resources"].append(
            {
                "resource_key": "SUMMARY",
                "resource_type": "wiki",
                "url": "https://example.feishu.cn/wiki/wikiSummary",
                "status": "verified",
                "read_complete": True,
                "depends_on": ["ACTION"],
            }
        )
        with self.assertRaisesRegex(GuardError, "unattempted"):
            validate_project_integration(result)

        result = self.result()
        result["links"][0]["observed_url"] = "https://example.feishu.cn/base/wrong"
        with self.assertRaisesRegex(GuardError, "目标不一致"):
            validate_project_integration(result)

class PreviewTests(unittest.TestCase):
    def test_preview_is_deterministic_and_complete(self):
        first = make_preview(preview_spec())
        second = make_preview(preview_spec(required_tools=[READ_TOOL, WRITE_TOOL, READ_TOOL]))
        self.assertEqual(first, second)
        self.assertTrue(first["preview_id"].startswith("fs-"))
        self.assertEqual("pending_confirmation", first["status"])
        self.assertEqual("user", first["identity"])

    def test_disabled_operations_are_rejected(self):
        for operation in ("delete", "transfer_owner", "public_permission_change"):
            with self.subTest(operation=operation), self.assertRaises(GuardError):
                make_preview(preview_spec(operation=operation))

    def test_non_feishu_required_tool_is_rejected(self):
        with self.assertRaises(GuardError):
            make_preview(preview_spec(required_tools=["mcp__chrome__click"]))
        with self.assertRaises(GuardError):
            make_preview(preview_spec(required_tools=[None]))

    def test_unknown_resource_type_is_rejected(self):
        with self.assertRaisesRegex(GuardError, "资源类型"):
            make_preview(preview_spec(resource_type="calendar"))

    def test_valid_preview_passes_preflight(self):
        spec = preview_spec()
        preview = make_preview(spec)
        result = validate_preview(
            preview,
            spec["before_state"],
            preview["preview_id"],
            [READ_TOOL, WRITE_TOOL],
        )
        self.assertTrue(result["valid"])

    def test_wrong_confirmation_is_rejected(self):
        spec = preview_spec()
        preview = make_preview(spec)
        with self.assertRaisesRegex(GuardError, "preview_id"):
            validate_preview(preview, spec["before_state"], "fs-wrong", [READ_TOOL, WRITE_TOOL])

    def test_changed_target_invalidates_preview(self):
        preview = make_preview(preview_spec())
        with self.assertRaisesRegex(GuardError, "发生变化"):
            validate_preview(preview, {"text": "changed"}, preview["preview_id"], [READ_TOOL, WRITE_TOOL])

    def test_tampered_preview_is_rejected(self):
        spec = preview_spec()
        preview = make_preview(spec)
        preview["changes"] = {"text": "tampered"}
        with self.assertRaisesRegex(GuardError, "已被修改"):
            validate_preview(preview, spec["before_state"], preview["preview_id"], [READ_TOOL, WRITE_TOOL])

    def test_missing_tool_is_reported_without_fallback(self):
        spec = preview_spec()
        preview = make_preview(spec)
        with self.assertRaisesRegex(GuardError, "缺少飞书 MCP 工具"):
            validate_preview(preview, spec["before_state"], preview["preview_id"], [READ_TOOL])
        self.assertEqual([WRITE_TOOL], missing_tools([READ_TOOL, WRITE_TOOL], [READ_TOOL]))

    def test_applied_preview_cannot_run_twice(self):
        spec = preview_spec(operation="append")
        preview = make_preview(spec)
        with self.assertRaisesRegex(GuardError, "已经执行"):
            validate_preview(
                preview,
                spec["before_state"],
                preview["preview_id"],
                [READ_TOOL, WRITE_TOOL],
                [preview["preview_id"]],
            )

    def test_malformed_preview_returns_guard_error(self):
        with self.assertRaisesRegex(GuardError, "预览缺少字段"):
            validate_preview({}, {}, "fs-missing", [READ_TOOL, WRITE_TOOL])

    def test_docx_edit_requires_unique_section(self):
        scope = preview_spec()["scope"]
        scope["selector"]["match_count"] = 2
        with self.assertRaisesRegex(GuardError, "必须唯一"):
            make_preview(preview_spec(scope=scope))

    def test_docx_edit_rejects_out_of_scope_change(self):
        changes = preview_spec()["changes"]
        changes["affected_block_ids"].append("heading-next")
        with self.assertRaisesRegex(GuardError, "范围外"):
            make_preview(preview_spec(changes=changes))

    def test_docx_edit_protects_unknown_blocks(self):
        changes = preview_spec()["changes"]
        changes["preserved_block_ids"] = []
        with self.assertRaisesRegex(GuardError, "原位保留"):
            make_preview(preview_spec(changes=changes))

    def test_docx_edit_discloses_format_fallback(self):
        changes = preview_spec()["changes"]
        changes["format_fallbacks"] = [
            {"requested_kind": "columns", "rendered_as": "heading2", "reason": "写入工具不支持分栏"}
        ]
        with self.assertRaisesRegex(GuardError, "format_degradation"):
            make_preview(preview_spec(changes=changes))

        preview = make_preview(
            preview_spec(changes=changes, risks=[{"type": "format_degradation", "detail": "分栏降级"}])
        )
        self.assertEqual(changes["format_fallbacks"], preview["changes"]["format_fallbacks"])

    def test_docx_edit_rejects_ragged_table(self):
        changes = preview_spec()["changes"]
        changes["after_blocks"] = [
            {"kind": "table", "content": {"rows": [["事项", "负责人"], ["待办"]]}}
        ]
        with self.assertRaisesRegex(GuardError, "列数一致"):
            make_preview(preview_spec(changes=changes))

    def test_docx_create_preview_requires_and_preserves_complete_structure(self):
        spec = create_preview_spec()
        preview = make_preview(spec)
        result = validate_preview(
            preview,
            spec["before_state"],
            preview["preview_id"],
            spec["required_tools"],
        )
        self.assertTrue(result["valid"])
        self.assertEqual(spec["changes"], preview["changes"])

    def test_docx_create_preview_rejects_incomplete_content(self):
        invalid_changes = (
            {"title": "", "blocks": [{"kind": "text"}], "pending_confirmations": []},
            {"title": "测试", "blocks": [], "pending_confirmations": []},
            {"title": "测试", "blocks": [{}], "pending_confirmations": []},
            {"title": "测试", "blocks": [{"kind": "text"}]},
        )
        for changes in invalid_changes:
            with self.subTest(changes=changes), self.assertRaises(GuardError):
                make_preview(create_preview_spec(changes=changes))

    def test_bitable_create_requires_zero_business_key_matches(self):
        spec = bitable_preview_spec()
        preview = make_preview(spec)
        self.assertEqual("bitable", preview["resource_type"])

        spec["changes"]["records"][0]["business_key_value"] = "P-001"
        spec["changes"]["records"][0]["after_fields"]["项目编号"] = "P-001"
        with self.assertRaisesRegex(GuardError, "零匹配"):
            make_preview(spec)

    def test_bitable_update_requires_one_exact_match(self):
        spec = bitable_preview_spec("update")
        preview = make_preview(spec)
        result = validate_preview(
            preview,
            spec["before_state"],
            preview["preview_id"],
            spec["required_tools"],
        )
        self.assertTrue(result["valid"])

        spec["before_state"]["records"].append(
            {"record_id": "rec-2", "fields": {"项目编号": "P-001", "状态": "进行中"}}
        )
        with self.assertRaisesRegex(GuardError, "唯一匹配"):
            make_preview(spec)

    def test_bitable_preview_requires_complete_pagination(self):
        spec = bitable_preview_spec()
        spec["before_state"]["records_pagination_complete"] = False
        with self.assertRaisesRegex(GuardError, "完整分页"):
            make_preview(spec)

    def test_bitable_preview_checks_field_types_and_writability(self):
        spec = bitable_preview_spec("update")
        record = spec["changes"]["records"][0]
        record["before_fields"] = {"预算": 100}
        record["after_fields"] = {"预算": "一百"}
        record["field_differences"] = [{"field": "预算", "before": 100, "after": "一百"}]
        spec["before_state"]["records"][0]["fields"]["预算"] = 100
        with self.assertRaisesRegex(GuardError, "字段类型"):
            make_preview(spec)

        record["before_fields"] = {"汇总": 100}
        record["after_fields"] = {"汇总": 200}
        record["field_differences"] = [{"field": "汇总", "before": 100, "after": 200}]
        spec["before_state"]["records"][0]["fields"]["汇总"] = 100
        with self.assertRaisesRegex(GuardError, "只读字段"):
            make_preview(spec)

    def test_bitable_preview_rejects_unplanned_select_option(self):
        spec = bitable_preview_spec("update")
        record = spec["changes"]["records"][0]
        record["after_fields"] = {"状态": "等待中"}
        record["field_differences"] = [{"field": "状态", "before": "进行中", "after": "等待中"}]
        with self.assertRaisesRegex(GuardError, "选项"):
            make_preview(spec)

    def test_bitable_preview_rejects_misleading_field_diff(self):
        spec = bitable_preview_spec("update")
        spec["changes"]["records"][0]["field_differences"][0]["after"] = "未开始"
        with self.assertRaisesRegex(GuardError, "字段差异"):
            make_preview(spec)

    def test_bitable_batch_result_distinguishes_every_planned_key(self):
        result = summarize_batch_outcomes(
            ["P-001", "P-002", "P-003"],
            ["P-001"],
            {"P-002": "字段类型不匹配"},
        )
        self.assertEqual("partial", result["status"])
        self.assertEqual(["P-001"], result["successful"])
        self.assertEqual(
            [{"business_key": "P-002", "reason": "字段类型不匹配"}], result["failed"]
        )
        self.assertEqual(["P-003"], result["unattempted"])

        with self.assertRaisesRegex(GuardError, "同时成功和失败"):
            summarize_batch_outcomes(["P-001"], ["P-001"], {"P-001": "冲突"})

    def test_project_register_table_contracts_are_previewable(self):
        preview_ids = set()
        for role in ("action_items", "risks", "decisions", "metrics"):
            with self.subTest(role=role):
                spec = project_register_preview_spec(role)
                preview = make_preview(spec)
                result = validate_preview(
                    preview,
                    spec["before_state"],
                    preview["preview_id"],
                    spec["required_tools"],
                )
                self.assertTrue(result["valid"])
                preview_ids.add(preview["preview_id"])
        self.assertEqual(4, len(preview_ids))

    def test_project_register_table_requires_complete_unique_target(self):
        spec = project_register_preview_spec()
        spec["before_state"]["tables_pagination_complete"] = False
        with self.assertRaisesRegex(GuardError, "完整分页"):
            make_preview(spec)

        spec = project_register_preview_spec()
        spec["before_state"]["tables"].append(
            {"table_id": "tblConflict", "table_name": "M5 行动项"}
        )
        with self.assertRaisesRegex(GuardError, "同名"):
            make_preview(spec)

    def test_project_register_table_rejects_schema_or_verification_drift(self):
        spec = project_register_preview_spec("metrics")
        spec["changes"]["table"]["fields"][2]["ui_type"] = "Text"
        with self.assertRaisesRegex(GuardError, "字段契约"):
            make_preview(spec)

        spec = project_register_preview_spec("metrics")
        spec["verification"]["business_key_field"] = "指标名称"
        with self.assertRaisesRegex(GuardError, "回读计划"):
            make_preview(spec)

    def test_sheets_replace_preview_is_range_bound_and_deterministic(self):
        spec = sheets_preview_spec()
        preview = make_preview(spec)
        result = validate_preview(
            preview,
            spec["before_state"],
            preview["preview_id"],
            spec["required_tools"],
        )
        self.assertTrue(result["valid"])

        spec["before_state"]["matches"].append("sheet1!C2")
        spec["scope"]["match_count"] = 3
        spec["changes"]["matched_cells"].append("sheet1!C2")
        spec["changes"]["replacement_count"] = 3
        with self.assertRaisesRegex(GuardError, "范围外"):
            make_preview(spec)

    def test_sheets_replace_requires_exact_text_matching(self):
        for field, value in (
            ("match_entire_cell", False),
            ("search_by_regex", True),
            ("include_formulas", True),
        ):
            spec = sheets_preview_spec()
            spec["before_state"]["find_condition"][field] = value
            spec["changes"]["find_condition"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(GuardError, "纯文本整格匹配"):
                make_preview(spec)

    def test_sheets_replace_requires_unique_sheet_and_complete_find(self):
        spec = sheets_preview_spec()
        spec["before_state"]["sheets"][0]["title"] = "其他"
        with self.assertRaisesRegex(GuardError, "唯一对应"):
            make_preview(spec)

        spec = sheets_preview_spec()
        spec["before_state"]["find_complete"] = False
        with self.assertRaisesRegex(GuardError, "查找结果必须完整"):
            make_preview(spec)

    def test_sheets_replace_locks_apply_arguments_and_verification(self):
        spec = sheets_preview_spec()
        spec["changes"]["apply_arguments"]["data"]["find_condition"]["range"] = "sheet1!A1:B4"
        with self.assertRaisesRegex(GuardError, "调用参数"):
            make_preview(spec)

        spec = sheets_preview_spec()
        spec["verification"]["replacement_matches"] = ["sheet1!A2", "sheet1!B4"]
        with self.assertRaisesRegex(GuardError, "写后验证"):
            make_preview(spec)

    def test_wiki_preview_supports_create_copy_move_update(self):
        for operation in ("create", "copy", "move", "update"):
            with self.subTest(operation=operation):
                spec = wiki_preview_spec(operation=operation)
                preview = make_preview(spec)
                result = validate_preview(
                    preview,
                    spec["before_state"],
                    preview["preview_id"],
                    spec["required_tools"],
                )
                self.assertTrue(result["valid"])

    def test_wiki_preview_rejects_unsupported_operation_and_noop_update(self):
        spec = wiki_preview_spec(operation="create")
        with self.assertRaisesRegex(GuardError, "只支持 create/copy/move/update"):
            spec["operation"] = "append"
            make_preview(spec)

        spec = wiki_preview_spec(operation="update")
        spec["changes"]["title"] = "原标题"
        with self.assertRaisesRegex(GuardError, "未发生变化"):
            make_preview(spec)

        spec = wiki_preview_spec(operation="move")
        spec["scope"]["target_parent_node_token"] = spec["scope"]["source_parent_node_token"]
        spec["before_state"]["target_parent"]["parent_node_token"] = spec["scope"]["source_parent_node_token"]
        spec["changes"]["title"] = spec["before_state"]["source_node"]["title"]
        with self.assertRaisesRegex(GuardError, "目标未发生变化"):
            make_preview(spec)

    def test_wiki_preview_checks_duplicate_child_names(self):
        spec = wiki_preview_spec(operation="create")
        spec["changes"]["title"] = "已有子节点"
        with self.assertRaisesRegex(GuardError, "同名子节点"):
            make_preview(spec)

    def test_wiki_document_import_preview_locks_source_target_and_arguments(self):
        spec = wiki_import_preview_spec()
        preview = make_preview(spec)
        self.assertTrue(
            validate_preview(preview, spec["before_state"], preview["preview_id"], spec["required_tools"])["valid"]
        )

        spec = wiki_import_preview_spec()
        spec["before_state"]["target_parent"]["children"].append(
            {"node_token": "wiki-duplicate", "title": "待入库文档"}
        )
        with self.assertRaisesRegex(GuardError, "同名子节点"):
            make_preview(spec)

        spec = wiki_import_preview_spec()
        spec["changes"]["apply_arguments"]["data"]["apply"] = True
        with self.assertRaisesRegex(GuardError, "调用参数"):
            make_preview(spec)

        spec = wiki_preview_spec(operation="copy")
        spec["before_state"]["target_parent"]["children"].append(
            {"node_token": "wiki-other", "title": "复制后的源节点", "node_type": "docx"},
        )
        with self.assertRaisesRegex(GuardError, "同名子节点"):
            make_preview(spec)

    def test_drive_preview_supports_create_copy_move_update(self):
        for operation in ("create", "copy", "move", "update"):
            with self.subTest(operation=operation):
                spec = drive_preview_spec(operation=operation)
                preview = make_preview(spec)
                result = validate_preview(
                    preview,
                    spec["before_state"],
                    preview["preview_id"],
                    spec["required_tools"],
                )
                self.assertTrue(result["valid"])

    def test_drive_export_preview_locks_format_source_and_arguments(self):
        spec = drive_export_preview_spec()
        preview = make_preview(spec)
        self.assertTrue(
            validate_preview(preview, spec["before_state"], preview["preview_id"], spec["required_tools"])["valid"]
        )

        spec = drive_export_preview_spec()
        spec["scope"]["file_extension"] = "xlsx"
        spec["changes"]["apply_arguments"]["data"]["file_extension"] = "xlsx"
        with self.assertRaisesRegex(GuardError, "不支持将 docx 导出为 xlsx"):
            make_preview(spec)

        spec = drive_export_preview_spec()
        spec["changes"]["apply_arguments"]["useUAT"] = False
        with self.assertRaisesRegex(GuardError, "调用参数"):
            make_preview(spec)

    def test_drive_import_preview_locks_source_target_name_and_arguments(self):
        spec = drive_import_preview_spec()
        preview = make_preview(spec)
        self.assertTrue(
            validate_preview(preview, spec["before_state"], preview["preview_id"], spec["required_tools"])["valid"]
        )

        spec = drive_import_preview_spec()
        spec["before_state"]["target_parent"]["children"].append(
            {"token": "duplicate", "name": "导入能力验收", "type": "docx"}
        )
        with self.assertRaisesRegex(GuardError, "同名子项"):
            make_preview(spec)

        spec = drive_import_preview_spec()
        spec["changes"]["apply_arguments"]["data"]["point"]["mount_type"] = 2
        with self.assertRaisesRegex(GuardError, "调用参数"):
            make_preview(spec)

        spec = drive_import_preview_spec()
        spec["before_state"]["source_file"]["provenance"] = "export_task"
        with self.assertRaisesRegex(GuardError, "导出任务返回的文件 token 不能直接用于导入"):
            make_preview(spec)

        spec = drive_import_preview_spec()
        spec["before_state"]["source_file"].update(
            {"provenance": "existing_drive_file", "file_size": None}
        )
        preview = make_preview(spec)
        self.assertTrue(
            validate_preview(
                preview,
                spec["before_state"],
                preview["preview_id"],
                spec["required_tools"],
            )["valid"]
        )

    def test_drive_preview_allows_unnamed_existing_items(self):
        spec = drive_preview_spec(operation="create")
        spec["before_state"]["children"].append(
            {"token": "unnamed-file", "name": "", "type": "docx"},
        )
        self.assertEqual("drive", make_preview(spec)["resource_type"])

    def test_drive_preview_rejects_invalid_source_type_and_version_conflicts(self):
        spec = drive_preview_spec(operation="copy")
        spec["scope"]["source_type"] = "bucket"
        with self.assertRaisesRegex(GuardError, "不支持源类型"):
            make_preview(spec)

        spec = drive_preview_spec(operation="copy")
        spec["scope"]["source_type"] = "folder"
        spec["before_state"]["source"]["type"] = "folder"
        with self.assertRaisesRegex(GuardError, "不支持源类型 folder"):
            make_preview(spec)

        spec = drive_preview_spec(operation="update")
        spec["scope"]["resource_type"] = "file"
        spec["before_state"]["resource"]["type"] = "file"
        spec["changes"]["apply_arguments"]["data"]["obj_type"] = "file"
        with self.assertRaisesRegex(GuardError, "不支持资源类型 file"):
            make_preview(spec)

        spec = drive_preview_spec(operation="update")
        spec["before_state"]["versions"] = [{"name": "M4 版本能力验收"}]
        with self.assertRaisesRegex(GuardError, "已有同名版本"):
            make_preview(spec)

        spec = drive_preview_spec(operation="update")
        spec["changes"]["apply_arguments"]["data"]["name"] = "被篡改的版本名"
        with self.assertRaisesRegex(GuardError, "调用参数"):
            make_preview(spec)

        spec = drive_preview_spec(operation="move")
        spec["before_state"]["source"]["parent_folder_token"] = "another-folder"
        with self.assertRaisesRegex(GuardError, "source_parent_folder_token 与 before_state 不一致"):
            make_preview(spec)

    def test_drive_copy_accepts_docx_without_source_parent(self):
        spec = drive_preview_spec(operation="copy")
        spec["scope"].pop("source_parent_folder_token")
        spec["scope"]["source_type"] = "docx"
        spec["before_state"]["source"].pop("parent_folder_token")
        spec["before_state"]["source"]["type"] = "docx"
        spec["changes"]["apply_arguments"]["data"]["type"] = "docx"
        self.assertEqual("copy", make_preview(spec)["operation"])

    def test_drive_preview_locks_apply_arguments(self):
        for operation in ("create", "copy", "move"):
            spec = drive_preview_spec(operation=operation)
            spec["changes"]["apply_arguments"]["useUAT"] = False
            with self.subTest(operation=operation), self.assertRaisesRegex(GuardError, "调用参数"):
                make_preview(spec)


if __name__ == "__main__":
    unittest.main()
