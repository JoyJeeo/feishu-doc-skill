# SPEC-M5-01：跨资源能力基线与实施契约

- 父项类型：产品需求
- 父项 ID：`M5`
- 状态：已完成
- 用户授权：已授权（2026-09-13，“开始执行M5”）
- 执行顺序：1 / 5
- 更新时间：2026-09-13

## 目标

核对 M5 所需的现有飞书 MCP 能力，确定项目工作区的数据落点、跨资源依赖顺序和缺失能力处理。

## 范围

- FR-T09、FR-P01 至 FR-P08 所依赖的 Docx、Wiki、Drive、Bitable 和 Sheets 工具元数据。
- 项目主页、文档集、周报、行动项、风险、决策和指标的资源落点。
- 跨资源读取、分资源预览、依赖执行、部分失败和回读验证契约。

## 非目标

- 不访问真实飞书资源，不新增运行时能力。
- 不生成或执行远端写入预览。
- 不扩展 MCP，不把 Sheets 任意区域读写或妙记重新纳入范围。

## 交付物与验收标准

- M5 的五个有序 Spec 已记录在路线图和独立 Spec 文件中。
- `PRODUCT.md` 与 MCP 能力参考明确记录资源落点、已验证能力、未验证能力和依赖顺序。
- 本地测试、Skill 校验与 `git diff --check` 通过。

## 验证结果

- 2026-09-13 元数据核对：Docx 21 个、Sheets 27 个、Bitable 46 个、Wiki 16 个、Drive 52 个工具可见，均继续支持显式用户身份参数。
- `conda run -n leju python -m unittest discover -s tests -v`：49 项测试通过。
- `conda run -n leju python /Users/yutaozhang/.codex/skills/.system/skill-creator/scripts/quick_validate.py .`：`Skill is valid!`。
- `conda run -n leju git diff --check`：通过。
