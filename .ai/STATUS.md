# 仓库状态

> 最近更新：2026-09-11
> 状态口径：截至本文件最近一次维护时，经仓库文件、Git 状态和测试结果核对后的项目快照。

## 当前阶段

- 当前里程碑：M1 安全执行闭环，状态为“已完成”。
- M0 产品基线：已完成。
- M1-A 本地安全骨架：已完成。
- M1-B 真实飞书 MCP 集成验证：已完成。
- 当前父项：产品需求 `M1-B`，三个 Spec 均已完成；预览 `fs-e25f22ab13739ae6` 已执行并通过回读验证。
- M2 至 M6：未开始。

## 已完成

- 产品资料：`.ai/README.md`、`.ai/DECISIONS.md`、`.ai/PRODUCT.md`、`.ai/ROADMAP.md`。
- Skill 入口：`SKILL.md`。
- 公共规则：MCP 能力、身份、预览、安全和质量规则。
- 工作流：`analyze`、`preview`、`apply`、`verify`。
- 本地安全辅助脚本：`scripts/feishu_guard.py`。
- 本地安全行为测试：`tests/test_feishu_guard.py`。
- AI 接续规范：根目录 `AGENTS.md` 要求新任务读取产品资料、核对仓库状态并持续维护本文件。
- AI 开发规范：产品需求与本地 Issue 均可作为开发入口；同一时间只实施一个父项，大任务按 Spec 拆分并逐段确认授权。
- AI 执行环境规范：所有仓库相关 shell 命令必须在 Conda `leju` 环境中执行，并优先使用可审计的 `conda run -n leju <command>` 形式。
- M1-B 能力发现：已核对当前云文档 MCP 前缀、用户身份参数和最小文档读写验证链路。
- M1-B Spec 映射：`SPEC-M1B-01` 至 `SPEC-M1B-03` 已记录在路线图和独立 Spec 文件中，三个 Spec 均已完成。
- M1-B 真实闭环：已完成 Wiki 解析、用户身份读取、预览确认、冲突检查、局部文本写入和回读验证。

## 验证结果

- `conda run -n leju python -m unittest discover -s tests -v`：2026-09-11 复跑，18 项测试通过。
- `conda run -n leju python scripts/feishu_guard.py --help`：命令入口可用。
- `conda run -n leju python .../skill-creator/scripts/quick_validate.py .`：`Skill is valid!`。
- `conda run -n leju git diff --check`：通过。
- `AGENTS.md` 与 `.ai/STATUS.md` 结构和空白格式检查：通过。
- Issue/Spec 开发门禁已写入 `AGENTS.md`；已创建首个产品需求 Spec，尚未创建本地 Issue。
- `SPEC-M1B-01` 的能力数量、必需工具和授权边界已完成静态核对；未调用真实飞书资源。
- `SPEC-M1B-01` 已由用户确认；`SPEC-M1B-02` 已获只读授权，已完成一次用户身份读取。
- 已通过 `useUAT: true` 解析 Wiki 节点并读取其挂载新版文档的基本信息与全部块。
- 预览 `fs-e25f22ab13739ae6` 经用户确认后通过写前指纹校验；局部更新返回文档版本 `4`。
- 写后分别回读文档信息、目标块、完整块列表和纯文本：标题保持“TEST”，目标正文为“M1-B 集成测试”，未发现非目标变化。

## 未完成与阻塞项

- M2 尚未获得实施授权。
- 后续任何真实写入仍必须先生成独立预览，再由用户确认对应的 `preview_id`。
- 本次只验证了新版文档的最小局部文本更新链路；其他资源和复杂文档结构仍未进行真实集成验证。

## 下一步

等待用户确认 M1 / `SPEC-M1B-03` 的完成结果，并明确授权 M2“飞书文档”产品需求后，再开始 M2；当前不提前修改 M2 文件。

## 维护说明

- 本文件保存当前状态，不充当历史日志；旧结论失效后应直接更新。
- 里程碑定义和退出条件以 `.ai/ROADMAP.md` 为准，稳定产品决策以 `.ai/DECISIONS.md` 为准。
- 每次仓库状态发生实质变化时，负责该变更的 AI 必须在结束前同步更新本文件。
- 如果本文件与 Git、实现或最新测试证据不一致，先核验事实，再修正本文件。
