# Project register model

Read this reference when creating or maintaining project action, risk, decision, or metric registers in Bitable.

## Resource boundary

Use four data tables in one existing, exactly resolved Bitable app. Each table is an independent write target with its own locally viewable preview, confirmation, pre-write reread, and post-write verification. Do not treat approval of one table as approval of another.

Creating a new Bitable app is not part of this verified path. If no exact existing app is available, stop and report that the app-creation path still needs separate validation.

## Table contracts

Use the first field as the stable, user-visible business key. Person-like fields remain `Text` because the exact `User` write payload has not passed integration validation. Dates use `DateTime`, sources use `Url`, and metric values use `Number`.

| Register role | Required fields in order | Fixed select options |
|---|---|---|
| `action_items` | 行动项编号, 事项, 负责人, 状态, 截止日期, 来源链接 | 状态：未开始、进行中、已完成、受阻 |
| `risks` | 风险编号, 风险, 影响, 概率, 状态, 负责人, 应对措施, 来源链接 | 影响/概率：低、中、高；状态：开放、监控中、已关闭 |
| `decisions` | 决策编号, 结论, 原因, 决策人, 决策日期, 来源链接 | 无 |
| `metrics` | 指标编号, 指标名称, 当前值, 单位, 状态日期, 来源链接 | 无 |

Every record must keep its exact source link. A missing key, owner, date, metric value, or source remains a pending confirmation; do not invent it.

## Table-creation state

Before creating one table, page through the complete table list and retain:

```yaml
app_token: exact existing Bitable app token
tables_pagination_complete: true
tables:
  - table_id: exact table ID
    table_name: current table name
```

The target name must have zero exact matches. The preview uses `resource_type: bitable`, `operation: create`, and `scope.entity: table`. Its `changes.table` must contain the exact MCP-ready name, default view, ordered fields, numeric field types, UI types, and select options. Run `scripts/feishu_guard.py make-preview`; it validates the role-specific contract, business key, source field, complete pagination, name conflict, and readback plan.

## Records and failures

After a table is created and its fields are verified, use [../bitable/data-model.md](../bitable/data-model.md) and [../../workflows/bitable-record-preview.md](../../workflows/bitable-record-preview.md) for record creates or updates. Keep each record preview homogeneous and use the table's declared business key.

If one table or record batch fails, report it separately and leave later writes unattempted unless they are independent and separately confirmed. Never replay a partially executed preview or report the four-register workspace as complete while any requested table is unverified.
