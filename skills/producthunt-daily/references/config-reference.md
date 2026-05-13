# Configuration Reference

## Required For Fetching

| Variable | Description |
| --- | --- |
| `PRODUCT_HUNT_TOKEN` | Product Hunt API token. A developer token is enough for read-only collection. |

## Required For CLI Enrichment

| Variable | Description |
| --- | --- |
| `LLM_BASE_URL` | OpenAI-compatible base URL ending at `/v1`. |
| `LLM_API_KEY` | Required only when not using `--no-enrichment`. |
| `LLM_MODEL` | Model name for `/chat/completions`. |

## Period Thresholds

| Variable | Default |
| --- | ---: |
| `DAILY_MIN_VOTES` | `300` |
| `WEEKLY_MIN_VOTES` | `800` |
| `MONTHLY_MIN_VOTES` | `1000` |
| `YEARLY_MIN_VOTES` | `5000` |

## Filters

| Variable | Description |
| --- | --- |
| `PRODUCT_HUNT_FEATURED` | Optional `true` or `false`. |
| `PRODUCT_HUNT_ORDER` | `VOTES`, `NEWEST`, or `FEATURED_AT`. |
| `PRODUCT_HUNT_TOPIC` | Product Hunt topic slug. |
| `INCLUDE_KEYWORDS` | Comma-separated local include keywords. |
| `EXCLUDE_KEYWORDS` | Comma-separated local exclude keywords. |

## Output

| Variable | Default |
| --- | --- |
| `OUTPUT_FORMATS` | `markdown` |
| `OUTPUT_DIR` | `.` |
| `HTTP_TIMEOUT_SECONDS` | `30` |
