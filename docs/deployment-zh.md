# 云服务器部署说明

## 安装

在云服务器上准备 Python 3.11+ 环境，然后执行：

```bash
git clone <repo-url>
cd <repo-directory>
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
mkdir -p logs
```

编辑 `.env`，填入 Product Hunt 和大模型配置：

```bash
PRODUCT_HUNT_TOKEN=your_product_hunt_token
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_llm_api_key
LLM_MODEL=gpt-4.1-mini
MIN_VOTES=300
COMMENT_RATIO=0.04
MIN_COMMENTS=8
OUTPUT_DIR=.
HTTP_TIMEOUT_SECONDS=30
```

## 手动运行

部署后先运行健康检查：

```bash
ph-daily healthcheck
```

`healthcheck` 只验证必需配置可以加载，例如 `.env` 字段是否齐全；它不会联网验证 Product Hunt token 或 LLM 凭据是否真的可用。真实集成验证以一次成功的 `collect` 运行为准。

采集当天数据：

```bash
ph-daily collect --date today
```

也可以指定日期：

```bash
ph-daily collect --date 2026-05-12
```

回填最近 7 天：

```bash
ph-daily backfill --days 7
```

## Cron 定时任务

以下示例每天北京时间 09:15 运行采集任务：

```cron
15 9 * * * cd /path/to/repo && . .venv/bin/activate && mkdir -p logs && ph-daily collect --date today >> logs/cron.log 2>&1
```

服务器时区需要设置为 `Asia/Shanghai`。如果服务器使用其他时区，请按实际时区调整 cron 时间。

## 输出文件

采集任务会生成以下文件：

```text
data/raw/YYYY-MM-DD.json
data/processed/YYYY-MM-DD.json
reports/daily/YYYY-MM-DD.md
```

当前采集器不会自动创建 `logs/YYYY-MM-DD.log` 这类每日应用日志。上面的 cron 示例会把 stdout/stderr 追加到 `logs/cron.log`，便于排查定时任务失败；如果需要按日期切分日志，可在服务器侧额外配置 logrotate 或自己的 cron 包装脚本。

## 运维注意事项

- `.env` 已被 git 忽略，不要提交 token、API key 或其他密钥。
- 生成的数据、报告和本地日志目录默认被 git 忽略。
- 如果 `ph-daily healthcheck` 失败，先修复配置，再配置 cron 定时任务。
- 如果 `ph-daily healthcheck` 成功，仍然需要至少手动运行一次 `ph-daily collect --date today`，确认 Product Hunt 和 LLM 集成可用。
