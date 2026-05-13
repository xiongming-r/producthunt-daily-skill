# Product Hunt Skill 模块化设计文档

## 背景

当前项目已经实现 v0.2：`ph-daily` CLI 支持 Product Hunt 日榜、周榜、月榜、年榜采集，支持官方过滤、本地关键词过滤、OpenAI-compatible LLM 富化，以及 Markdown/HTML/JSON 输出。

用户在 `/Users/xiongming/Documents/skill分发包/producthunt-daily/producthunt-daily` 中让其他 agent 基于 v0.2 创建了一个可运行的 skill 分发包，并已验证放到其他 agent 上运行有效。该分发包包含：

- `SKILL.md`：Agent 使用入口。
- `references/config-reference.md`：配置说明。
- `references/agent-templates.md`：不同 Agent 的调用模板。
- `references/enrichment-prompt.md`：Agent 自执行中文解读规范。
- `scripts/setup.sh`：一键安装脚本。
- `scripts/src/ph_daily/`：一份内置的 `ph-daily` CLI 源码副本。
- 分发残留：`.git`、`.DS_Store`、`__pycache__`、`egg-info` 等。

该 skill 的核心价值是把项目从“一个脚本工具”推进到“Agent 可分发能力包”。后续迭代应以 skill 体验为主线，同时保持脚本内核稳定。

## 结论

采用方案 B：

> 项目内维护独立的 `skills/producthunt-daily/` skill 源模块；`src/ph_daily` 继续作为唯一 CLI 源码真源；通过导出/打包流程把当前 CLI 内核复制进 skill 分发包。

不直接把外部分发包原样放进项目，因为外部分发包中已经包含完整 CLI 源码副本和运行残留。如果原样纳入，会形成两个长期维护的源码真源，后续很容易出现 skill 可运行但项目测试不通过，或项目已升级但 skill 仍停留旧版本的问题。

## 设计目标

1. **Skill 是主要产品形态**  
   后续路线以 Agent 使用体验为核心，包括安装、调度、失败诊断、二次分析、Agent 自执行富化、跨 Agent 模板。

2. **CLI 是稳定执行内核**  
   `src/ph_daily` 负责确定性能力：Product Hunt API、周期窗口、质量过滤、关键词过滤、LLM HTTP 适配、输出文件、CLI 参数、测试。

3. **单一源码真源**  
   项目仓库内只有 `src/ph_daily` 是 Python CLI 源码真源。skill 分发包里的 `scripts/src/ph_daily` 必须由导出脚本生成，不允许手工长期维护。

4. **分发包可自包含**  
   最终导出的 skill 包可以继续包含 `scripts/src/ph_daily`，这样放到其他 agent 平台时不依赖用户额外 clone 本仓库。

5. **不提交运行残留**  
   `.git`、`.DS_Store`、`__pycache__`、`egg-info`、本地 `.env`、生成报告等不能进入项目内 skill 源模块。

## 模块边界

### CLI 内核：`src/ph_daily`

职责：

- 调用 Product Hunt 官方 GraphQL API。
- 计算 daily/weekly/monthly/yearly 时间窗口。
- 应用周期化质量过滤。
- 应用 Product Hunt 官方过滤参数。
- 应用本地 include/exclude 关键词过滤。
- 调用 OpenAI-compatible LLM 进行富化。
- 写入 raw JSON、processed JSON、Markdown、HTML。
- 保持完整 pytest 覆盖。

不负责：

- 解释不同 Agent 平台如何安装 skill。
- 维护 WorkBuddy、Qclaw、Hermes、Codex、Claude Code 的提示词。
- 把报告改写成运营摘要、趋势摘要或通知消息。

### Skill 源模块：`skills/producthunt-daily`

建议结构：

```text
skills/producthunt-daily/
  SKILL.md
  references/
    config-reference.md
    agent-templates.md
    enrichment-prompt.md
  scripts/
    setup.sh
    .env.example
```

职责：

- 告诉 Agent 什么时候触发 Product Hunt skill。
- 告诉 Agent 如何安装、配置、调用 `ph-daily`。
- 约束 Agent 不要重写 Product Hunt 抓取、过滤、报告逻辑。
- 提供调度、一次性执行、失败诊断、二次分析模板。
- 提供 Agent 自执行富化规范。

不负责：

- 长期手写维护一份 `scripts/src/ph_daily`。
- 保存真实 token、API key 或用户环境配置。
- 保存运行产物。
- 直接修改 `data/raw`、`data/processed`、`reports` 作为修复手段。

### Skill 分发包：导出产物

导出产物可以包含：

```text
producthunt-daily/
  SKILL.md
  references/
  scripts/
    setup.sh
    .env.example
    pyproject.toml
    src/ph_daily/
```

导出产物的 `scripts/src/ph_daily` 从项目根目录的 `src/ph_daily` 复制而来。它不是仓库内的人工维护源文件。

## 关键能力：Agent Mode / `--no-enrichment`

外部 skill 分发包已经引入一个重要能力：`--no-enrichment`。

该模式含义：

- CLI 只负责 Product Hunt 抓取、过滤、结构化输出。
- CLI 不调用外部 LLM。
- `LLM_API_KEY` 可以不是必填。
- Agent 读取 `data/processed/...json`，根据 `references/enrichment-prompt.md` 自己完成中文解读。

这非常符合 skill-first 的路线，因为很多 Agent 本身已经有模型能力，不一定需要再额外付费调用一个 OpenAI-compatible endpoint。

设计决策：

- `--no-enrichment` 应进入下一阶段 CLI 内核，而不是只存在于 skill 分发包。
- 它需要正式测试覆盖，包括：
  - CLI 参数解析。
  - 缺少 `LLM_API_KEY` 时允许 healthcheck 通过的条件。
  - no-enrichment 采集不会触发 LLM client。
  - selected products 保留 `enrichment=None`，但不触发“All selected products failed enrichment”错误。
- 默认模式仍保持 v0.2 行为：有 `LLM_API_KEY` 时由 CLI 自己富化并输出完整报告。

## 版本与迭代方式

后续版本应拆成两个维度记录：

### Core 维度

示例：

- `core v0.3`：加入 `--no-enrichment`、LLM key 可选逻辑、Agent mode 测试。
- `core v0.4`：增加失败重跑、指定 processed JSON 富化、通知 hook。

### Skill 维度

示例：

- `skill v0.1`：项目内引入 `skills/producthunt-daily` 源模块。
- `skill v0.2`：增加导出脚本和分发包校验。
- `skill v0.3`：增加 agent 自执行富化流程和跨 Agent 模板验收。

项目 release notes 可以同时记录：

```text
Core: 0.3.0
Skill: 0.1.0
```

## 推荐实施阶段

### 阶段 1：引入 skill 源模块

- 创建 `skills/producthunt-daily/`。
- 从外部分发包迁移 `SKILL.md` 和 `references/`。
- 清理不适合入仓库的内容：
  - `.git`
  - `.DS_Store`
  - `__pycache__`
  - `egg-info`
  - 生成报告
  - 本地 `.env`
- 暂不迁移 `scripts/src/ph_daily`。
- 迁移并调整 `scripts/setup.sh`，让它面向未来导出产物。

### 阶段 2：增加导出脚本

建议新增：

```text
tools/export_producthunt_skill.py
```

职责：

- 读取项目内 `skills/producthunt-daily`。
- 复制 `SKILL.md`、`references/`、`scripts/setup.sh`、`.env.example`。
- 从项目根复制 `pyproject.toml` 和 `src/ph_daily/` 到导出目录的 `scripts/` 下。
- 排除缓存和运行产物。
- 输出一个可分发目录，例如：

```text
dist/skills/producthunt-daily/
```

### 阶段 3：增加 skill 校验

建议新增最小校验：

- 检查 `SKILL.md` frontmatter 包含 `name` 和 `description`。
- 检查 references 文件存在。
- 检查导出包没有 `.DS_Store`、`__pycache__`、`.git`。
- 检查导出包中的 CLI version 与项目 `pyproject.toml` 一致。

### 阶段 4：回流 Agent Mode

- 把外部分发包中的 `--no-enrichment` 能力正式合入 `src/ph_daily`。
- 更新测试。
- 更新 README、deployment、skill references。

## 风险与约束

### 风险 1：双源码真源

如果把 `scripts/src/ph_daily` 作为项目内长期维护文件，会导致 CLI 内核和 skill 内核漂移。解决方式是只在导出产物里生成源码副本。

### 风险 2：Skill 过度膨胀

`SKILL.md` 不应承载全部配置和模板。应保持入口简洁，细节放入 `references/`，按需加载。

### 风险 3：Agent Mode 破坏现有部署

`--no-enrichment` 必须是显式参数。默认路径继续走 v0.2 的 CLI LLM 富化流程，避免影响云服务器 cron。

### 风险 4：密钥泄露

Skill 文档和 setup 输出必须反复强调：

- 不打印 `.env`。
- 不提交 token。
- 失败诊断只输出错误摘要，不输出密钥原文。

## 验收标准

设计落地后应满足：

- 项目中存在独立 `skills/producthunt-daily/` 源模块。
- 项目中不存在手工维护的第二份 `src/ph_daily`。
- 可以从项目真源导出一个自包含 skill 分发包。
- 导出包可安装并调用 `ph-daily healthcheck`。
- 后续 roadmap 明确区分 core 迭代和 skill 迭代。
- `--no-enrichment` 被纳入下一阶段实现计划，而不是只停留在外部分发包。

## 当前决策

- 采用方案 B。
- Skill 是后续主要迭代对象。
- CLI 保持唯一执行内核。
- 外部分发包作为参考来源，不原样导入。
- 下一步应先编写实现计划，再开始迁移 skill 源模块和导出流程。
