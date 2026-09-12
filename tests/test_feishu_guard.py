import unittest

from scripts.feishu_guard import (
    GuardError,
    classify_feishu_url,
    identity_parameters,
    make_preview,
    missing_tools,
    validate_feishu_tool,
    validate_mode,
    validate_preview,
)


READ_TOOL = "mcp__feishu__docx_v1_document_get"
WRITE_TOOL = "mcp__feishu__docx_v1_documentBlock_patch"
CREATE_TOOL = "mcp__feishu__wiki_v2_spaceNode_create"
CREATE_BLOCKS_TOOL = "mcp__feishu__docx_v1_documentBlockChildren_create"


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


if __name__ == "__main__":
    unittest.main()
