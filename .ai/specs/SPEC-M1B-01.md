# SPEC-M1B-01：能力发现与集成契约

- 父项类型：产品需求
- 父项 ID：`M1-B`
- 状态：已完成
- 用户确认：已确认（2026-09-10）
- 执行顺序：1 / 3
- 更新时间：2026-09-10

## 目标

核对当前连接环境中的飞书云文档 MCP 元数据，并为 M1-B 定义一个最小、可授权、可验证的新版文档集成链路。

## 范围

- 统计 `docx`、`drive`、`sheets`、`bitable`、`wiki`、`minutes`、`board`、`slides` 和 `mindnote` 工具前缀。
- 确认 M1-B 所需文档工具是否可见以及是否暴露 `useUAT` 参数。
- 定义后续只读、预览、局部写入和回读验证的工具链与授权门禁。
- 将能力快照写入 `references/common/mcp-capabilities.md`。

## 非目标

- 不读取或修改任何真实飞书资源。
- 不验证账号权限、实际返回结构或写入载荷。
- 不调用应用身份、Chrome、CUA、OpenAPI、HTTP 或其他连接器。
- 不提前实施 `SPEC-M1B-02` 或 `SPEC-M1B-03`。

## 依赖

- 已连接的飞书 MCP 工具元数据可见。
- M1-A 的身份、预览、冲突检测和回读规则已存在。

## 交付物

- `.ai/ROADMAP.md` 中的 M1-B Spec 双向映射。
- `references/common/mcp-capabilities.md` 中的当前能力快照和最小文档契约。
- `.ai/STATUS.md` 中的当前进度、验证边界和下一授权点。

## 验证

- 当前元数据显示：`docx` 21、`drive` 52、`sheets` 27、`bitable` 46、`wiki` 16、`minutes` 3、`board` 1、`slides` 0、`mindnote` 0。
- M1-B 最小链路所需的 `document_get`、`documentBlock_list`、`documentBlock_get` 和 `documentBlock_patch` 均可见。
- 上述四个工具均暴露 `useUAT` 参数。
- `python3 -m unittest discover -s tests -v`：18 项测试通过。
- Skill Creator `quick_validate.py`：`Skill is valid!`。
- `git diff --check`：通过。

## 验收标准

- 能力数量与当前工具元数据一致。
- 最小链路明确区分读取、预览、写入和验证阶段。
- 写入限定为用户指定测试文档中的单个专用文本块。
- 下一 Spec 的资源输入和只读授权要求明确。
- 本 Spec 未发生真实飞书调用。

## 下一门禁

用户确认本 Spec 后，需提供一个可安全编辑的飞书中国版新版文档链接，并明确授权 `SPEC-M1B-02` 使用用户身份进行只读检查。该授权不包含任何写入。
