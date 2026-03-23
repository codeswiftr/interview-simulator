# Interview Simulator CLI - Quick Reference

One-page reference for the `interview-sim` CLI.

## Installation

```bash
cd backend
uv sync
uv pip install -e .
```

## Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `version` | Show CLI version | `interview-sim version` |
| `generate-questions` | Generate questions for a topic | `interview-sim generate-questions -t leadership -n 5` |
| `analyze-transcript` | Analyze interview transcript | `interview-sim analyze-transcript -f transcript.txt -s <uuid>` |
| `export-metrics` | Export usage/performance metrics | `interview-sim export-metrics -p weekly -o metrics.json` |
| `batch-feedback` | Generate feedback for multiple sessions | `interview-sim batch-feedback -f sessions.txt` |

## Common Flags

| Flag | Purpose | Commands |
|------|---------|----------|
| `--json` | JSON output (for automation) | ALL |
| `-t, --topic` | Question topic | `generate-questions` |
| `-n, --count` | Number of items | `generate-questions` |
| `-d, --difficulty` | Difficulty level (easy/medium/hard) | `generate-questions` |
| `-c, --category` | Category (behavioral/technical/system_design) | `generate-questions` |
| `-f, --file` | Input file path | `analyze-transcript`, `batch-feedback` |
| `-s, --session-id` | Interview session UUID | `analyze-transcript` |
| `-p, --period` | Time period (weekly/monthly) | `export-metrics` |
| `-o, --output` | Output file path | `export-metrics` |
| `-u, --user-id` | User UUID filter | `export-metrics` |

## One-Liners

### Generate 5 behavioral questions on leadership
```bash
interview-sim generate-questions -t leadership -n 5
```

### Generate technical questions with JSON output
```bash
interview-sim generate-questions -t arrays -c technical -d hard --json
```

### Analyze session transcript
```bash
interview-sim analyze-transcript -f transcript.txt -s <session-uuid>
```

### Export weekly metrics to file
```bash
interview-sim export-metrics -p weekly -o metrics.json --json
```

### Process batch of sessions
```bash
interview-sim batch-feedback -f sessions.txt --json
```

### Export user-specific metrics
```bash
interview-sim export-metrics -p monthly -u <user-uuid> --json
```

## JSON Output Pattern

All commands support `--json` and return this structure:

```json
{
  "success": true,
  "data": { /* command-specific */ },
  "error": null,
  "error_code": null,
  "timestamp": "2026-02-05T14:30:00Z",
  "duration_ms": 234.56,
  "metadata": {
    "command": "interview-sim ...",
    "version": "0.1.0"
  }
}
```

## Automation Examples

### Python
```python
import subprocess, json

def run_cli(cmd):
    result = subprocess.run(cmd + ["--json"], capture_output=True, text=True)
    return json.loads(result.stdout)["data"]

# Generate questions
questions = run_cli(["interview-sim", "generate-questions", "-t", "leadership", "-n", "5"])
```

### Shell
```bash
# Extract specific field with jq
SCORE=$(interview-sim export-metrics -p weekly --json | jq -r '.data.performance.average_score')
echo "Average score: $SCORE"

# Check completion rate
RATE=$(interview-sim export-metrics -p weekly --json | jq -r '.data.sessions.completion_rate')
if (( $(echo "$RATE < 80" | bc -l) )); then
  echo "Warning: Low completion rate"
fi
```

## Environment

Uses same `.env` as FastAPI backend:
- `DATABASE_URL` - PostgreSQL connection
- `ANTHROPIC_API_KEY` - For AI feedback
- `OPENAI_API_KEY` - For transcription

## Error Codes

| Code | Meaning |
|------|---------|
| `INVALID_INPUT` | Bad arguments |
| `NOT_FOUND` | File/resource missing |
| `INTERNAL_ERROR` | System error |
| `PERMISSION_DENIED` | Auth issue |

## Help

```bash
# General help
interview-sim --help

# Command-specific help
interview-sim generate-questions --help
interview-sim export-metrics --help
```

## Full Documentation

See [CLI.md](./CLI.md) for complete documentation.
