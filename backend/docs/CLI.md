# Interview Simulator CLI

Agent-friendly CLI for automating Interview Simulator operations.

## Installation

```bash
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/backend
uv sync
uv pip install -e .
```

## Quick Start

```bash
# Check version
interview-sim version

# Generate questions for a topic
interview-sim generate-questions --topic leadership --count 5

# Analyze transcript
interview-sim analyze-transcript --file transcript.txt --session-id <uuid>

# Export metrics
interview-sim export-metrics --period weekly

# Batch feedback generation
interview-sim batch-feedback --session-ids sessions.txt
```

## Commands

### 1. `generate-questions`

Generate interview questions for a specific topic.

**Usage:**
```bash
interview-sim generate-questions --topic TOPIC [OPTIONS]
```

**Options:**
- `--topic`, `-t` (required): Question topic (e.g., "leadership", "arrays", "scalability")
- `--count`, `-n`: Number of questions to generate (default: 5)
- `--difficulty`, `-d`: Question difficulty - `easy`, `medium`, `hard` (default: medium)
- `--category`, `-c`: Question category - `behavioral`, `technical`, `system_design` (default: behavioral)
- `--json`: Output as JSON

**Examples:**
```bash
# Generate 5 medium behavioral questions on leadership
interview-sim generate-questions --topic leadership --count 5

# Generate 3 hard technical questions on arrays with JSON output
interview-sim generate-questions -t arrays -n 3 -d hard -c technical --json

# Generate system design questions
interview-sim generate-questions -t scalability -c system_design --json
```

**JSON Output Schema:**
```json
{
  "success": true,
  "data": {
    "questions": [
      {
        "id": "uuid",
        "content": "Question text",
        "category": "behavioral",
        "difficulty": "medium",
        "topic_tags": ["leadership", "conflict"],
        "company_tags": ["google", "amazon"],
        "expected_duration_seconds": 180
      }
    ],
    "count": 5,
    "topic": "leadership",
    "difficulty": "medium",
    "category": "behavioral"
  },
  "error": null,
  "error_code": null,
  "timestamp": "2026-02-05T14:30:00Z",
  "duration_ms": 234.56,
  "metadata": {
    "command": "interview-sim generate-questions ...",
    "version": "0.1.0"
  }
}
```

---

### 2. `analyze-transcript`

Analyze interview transcript and generate AI feedback.

**Usage:**
```bash
interview-sim analyze-transcript --file PATH [OPTIONS]
```

**Options:**
- `--file`, `-f` (required): Path to transcript file
- `--session-id`, `-s`: Interview session ID (optional, enables full analysis)
- `--json`: Output as JSON

**Examples:**
```bash
# Analyze standalone transcript (basic word count)
interview-sim analyze-transcript --file transcript.txt

# Analyze all responses for a session (generates AI feedback)
interview-sim analyze-transcript -f transcript.txt -s 123e4567-e89b-12d3-a456-426614174000

# JSON output for agent consumption
interview-sim analyze-transcript -f transcript.txt -s <uuid> --json
```

**JSON Output Schema (with session-id):**
```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "response_count": 3,
    "analyses": [
      {
        "response_id": "uuid",
        "question_id": "uuid",
        "overall_score": 78.5,
        "technical_accuracy": 85.0,
        "star_adherence": 72.0,
        "answer_structure": 80.0,
        "completeness": 75.0,
        "relevance": 82.0,
        "strengths": ["Clear communication", "Good examples"],
        "improvements": ["Add more technical depth", "Quantify impact"],
        "detailed_feedback": "Full feedback text..."
      }
    ]
  },
  "error": null,
  "timestamp": "2026-02-05T14:30:00Z",
  "duration_ms": 1234.56
}
```

---

### 3. `export-metrics`

Export usage and performance metrics for a time period.

**Usage:**
```bash
interview-sim export-metrics [OPTIONS]
```

**Options:**
- `--period`, `-p`: Time period - `weekly`, `monthly` (default: weekly)
- `--output`, `-o`: Output file path (optional, saves JSON to file)
- `--user-id`, `-u`: Filter by specific user ID (optional)
- `--json`: Output as JSON

**Examples:**
```bash
# Export weekly metrics (human-readable)
interview-sim export-metrics --period weekly

# Export monthly metrics to file with JSON format
interview-sim export-metrics -p monthly -o metrics.json --json

# Export metrics for specific user
interview-sim export-metrics -p weekly -u <user-uuid> --json

# Export and save to file (no console output needed)
interview-sim export-metrics -p monthly -o /tmp/metrics.json --json
```

**JSON Output Schema:**
```json
{
  "success": true,
  "data": {
    "period": "weekly",
    "start_date": "2026-01-29T00:00:00Z",
    "end_date": "2026-02-05T14:30:00Z",
    "user_id": null,
    "sessions": {
      "total": 45,
      "completed": 38,
      "analyzed": 35,
      "completion_rate": 84.4
    },
    "responses": {
      "total": 225,
      "transcribed": 215,
      "transcription_rate": 95.6
    },
    "performance": {
      "average_score": 76.3,
      "scored_sessions": 35
    },
    "category_breakdown": {
      "behavioral": 25,
      "technical": 15,
      "system_design": 5
    }
  },
  "error": null,
  "timestamp": "2026-02-05T14:30:00Z",
  "duration_ms": 456.78
}
```

---

### 4. `batch-feedback`

Generate feedback for multiple interview sessions in batch.

**Usage:**
```bash
interview-sim batch-feedback --session-ids FILE [OPTIONS]
```

**Options:**
- `--session-ids`, `-f` (required): File containing session IDs (one per line)
- `--json`: Output as JSON

**Session IDs File Format:**
```
123e4567-e89b-12d3-a456-426614174000
987fcdeb-51a2-43d9-8765-123456789abc
456789ab-cdef-0123-4567-89abcdef0123
```

**Examples:**
```bash
# Process batch of sessions
interview-sim batch-feedback --session-ids sessions.txt

# JSON output for automation
interview-sim batch-feedback -f sessions.txt --json
```

**JSON Output Schema:**
```json
{
  "success": true,
  "data": {
    "total": 3,
    "successful": 2,
    "failed": 1,
    "generated": 1,
    "already_exists": 1,
    "results": [
      {
        "session_id": "uuid-1",
        "success": true,
        "status": "generated",
        "overall_score": 78.5,
        "audio_score": 82.0,
        "content_score": 75.0
      },
      {
        "session_id": "uuid-2",
        "success": true,
        "status": "already_exists",
        "overall_score": 85.0
      },
      {
        "session_id": "invalid-uuid",
        "success": false,
        "error": "Invalid UUID format"
      }
    ]
  },
  "error": null,
  "timestamp": "2026-02-05T14:30:00Z",
  "duration_ms": 2345.67
}
```

---

### 5. `version`

Display CLI version information.

**Usage:**
```bash
interview-sim version [--json]
```

**Examples:**
```bash
# Human-readable version
interview-sim version

# JSON output
interview-sim version --json
```

---

## Agent Consumption Pattern

All commands support `--json` for structured output following the [FORGE Agent-Friendly CLI Standard](../../../docs/standards/AGENT_FRIENDLY_CLI.md).

### Python Example

```python
import subprocess
import json

def run_cli(cmd: list[str]) -> dict:
    """Run CLI command and parse JSON output."""
    result = subprocess.run(
        cmd + ["--json"],
        capture_output=True,
        text=True,
        check=False
    )

    response = json.loads(result.stdout)

    if not response["success"]:
        raise Exception(f"{response['error_code']}: {response['error']}")

    return response["data"]

# Generate questions
questions = run_cli([
    "interview-sim", "generate-questions",
    "--topic", "leadership",
    "--count", "5"
])

# Export metrics
metrics = run_cli([
    "interview-sim", "export-metrics",
    "--period", "weekly"
])
```

### Shell Example

```bash
#!/bin/bash

# Generate questions and extract count
QUESTION_COUNT=$(interview-sim generate-questions \
  --topic leadership \
  --count 5 \
  --json | jq -r '.data.count')

echo "Generated $QUESTION_COUNT questions"

# Export metrics and check completion rate
COMPLETION_RATE=$(interview-sim export-metrics \
  --period weekly \
  --json | jq -r '.data.sessions.completion_rate')

if (( $(echo "$COMPLETION_RATE < 80" | bc -l) )); then
  echo "Warning: Completion rate below 80% ($COMPLETION_RATE%)"
fi
```

---

## Error Codes

| Code | Category | Meaning |
|------|----------|---------|
| `SUCCESS` | Success | Operation completed successfully |
| `INVALID_INPUT` | Input | Bad arguments or invalid options |
| `NOT_FOUND` | Resource | File/entity doesn't exist |
| `PERMISSION_DENIED` | Auth | Insufficient permissions |
| `TIMEOUT` | Network | Operation timed out |
| `RATE_LIMITED` | API | Rate limit exceeded |
| `SERVICE_UNAVAILABLE` | External | External dependency unavailable |
| `INTERNAL_ERROR` | System | Unexpected failure |

---

## Environment Variables

The CLI uses the same configuration as the FastAPI backend:

- `DATABASE_URL`: PostgreSQL connection string
- `ANTHROPIC_API_KEY`: For AI feedback generation
- `OPENAI_API_KEY`: For transcription (Whisper)

Ensure your `.env` file is configured properly in the `backend/` directory.

---

## Integration with FastAPI Backend

The CLI directly uses the service layer from the FastAPI backend:

- `app.services.interview_service.InterviewService`
- `app.services.feedback_service.FeedbackService`
- `app.services.question_recommender`
- `app.models.*` (database models)

This ensures consistency between API and CLI operations.

---

## Testing

```bash
# Install in development mode
cd backend
uv pip install -e .

# Test commands
interview-sim version
interview-sim generate-questions --topic leadership --count 3 --json

# Validate JSON output
interview-sim export-metrics --period weekly --json | jq '.success'
```

---

## Roadmap

Future enhancements:

- [ ] `interview-sim create-session` - Create interview session from CLI
- [ ] `interview-sim upload-audio` - Upload audio file for transcription
- [ ] `interview-sim recommend-questions` - Get personalized question recommendations
- [ ] `interview-sim export-report` - Generate PDF reports
- [ ] `interview-sim sync-analytics` - Sync analytics to PostHog

---

## Support

For issues or feature requests, contact: bogdan@codeswiftr.com
