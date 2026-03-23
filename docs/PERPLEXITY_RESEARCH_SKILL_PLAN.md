# Perplexity Research Skill Implementation Plan

## Executive Summary

Create a powerful research skill for Claude Code that leverages Perplexity's Sonar API models for real-time, citation-backed research. The skill will support quick lookups, deep research, and structured analysis with automatic source tracking.

---

## Research Findings

### Perplexity API Models (2025)

| Model | Use Case | Speed | Cost |
|-------|----------|-------|------|
| `sonar` | Quick factual queries, summaries | 1200 tok/s | Low |
| `sonar-pro` | Complex queries, follow-ups | Fast | Medium |
| `sonar-reasoning` | Real-time reasoning + search | Fast | Medium |
| `sonar-reasoning-pro` | Advanced reasoning (DeepSeek-R1) | Medium | Higher |
| `sonar-deep-research` | Long-form reports, async | Slow (async) | Higher |

### Key API Features

1. **Search Modes** (for sonar/sonar-pro):
   - `high` - Maximum depth for complex queries
   - `medium` - Balanced approach
   - `low` - Cost-efficient for simple queries

2. **Async API** (for deep-research):
   - POST `/async/chat/completions` - Create job
   - GET `/async/chat/completions/{id}` - Poll status
   - 7-day TTL for results

3. **Pricing Updates**:
   - Citation tokens now FREE (except deep-research)
   - Searches: $5/1000 searches
   - Deep research includes reasoning step costs

### Best Practices Identified

1. **Model Selection**: Match model to task complexity
2. **Rate Limiting**: Implement exponential backoff
3. **Error Handling**: Handle timeouts, API errors gracefully
4. **Citation Tracking**: Always capture and format sources
5. **Cost Monitoring**: Track token usage via response `usage` field

---

## Architecture Design

### Option A: Skill + MCP Server (Recommended)

```
┌─────────────────────────────────────────────────────────┐
│                    Claude Code                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐     ┌─────────────────────────┐   │
│  │ /perplexity     │     │ Perplexity MCP Server   │   │
│  │ research skill  │────▶│ (API integration)       │   │
│  │ (SKILL.md)      │     │                         │   │
│  └─────────────────┘     └───────────┬─────────────┘   │
│                                      │                  │
│           Instructions               │ API Calls        │
│           + Workflows                ▼                  │
│                           ┌─────────────────────────┐   │
│                           │ Perplexity Sonar API    │   │
│                           │ - sonar (quick)         │   │
│                           │ - sonar-pro (deep)      │   │
│                           │ - sonar-deep-research   │   │
│                           └─────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Option B: Skill-Only (Bash + curl)

Uses direct API calls via curl - simpler but less integrated.

---

## Implementation Plan

### Phase 1: MCP Server Setup

**Effort**: 15 minutes

#### 1.1 Install Official Perplexity MCP Server

```bash
# Option A: CLI command (recommended)
claude mcp add perplexity \
  --env PERPLEXITY_API_KEY="pplx-xxx" \
  -- npx -yq @perplexity-ai/mcp-server

# Option B: Manual JSON config
claude mcp add-json --scope user perplexity '{
  "type": "stdio",
  "command": "npx",
  "args": ["-yq", "@perplexity-ai/mcp-server"],
  "env": {
    "PERPLEXITY_API_KEY": "pplx-xxx",
    "PERPLEXITY_MODEL": "sonar-pro",
    "PERPLEXITY_TIMEOUT_MS": "300000"
  }
}'
```

#### 1.2 Verify Installation

```bash
claude mcp list
# Should show: perplexity (running)
```

---

### Phase 2: Create SKILL.md

**Effort**: 30 minutes

#### 2.1 Directory Structure

```
~/.claude/skills/perplexity-researcher/
├── SKILL.md              # Main skill instructions
├── references/
│   ├── models.md         # Model selection guide
│   └── templates.md      # Research prompt templates
└── scripts/
    └── deep-research.sh  # Async polling helper (optional)
```

#### 2.2 SKILL.md Content

```markdown
---
name: perplexity-researcher
description: Conduct real-time web research with citations using Perplexity Sonar API. Supports quick lookups, deep analysis, and async research reports.
---

# Perplexity Researcher

AI-powered research with real-time web search and automatic citations.

## When to Use

- Researching current events, news, or recent developments
- Technical documentation, API references, best practices
- Market research, competitor analysis
- Fact-checking and verification with sources
- Deep research reports requiring extensive sourcing

## Prerequisites

- Perplexity MCP server installed and configured
- Valid PERPLEXITY_API_KEY in environment

## Research Modes

### Quick Research (sonar)
For simple factual queries and summaries:
```
Use Perplexity to quickly look up: [topic]
```

### Standard Research (sonar-pro)
For complex queries with follow-up capability:
```
Research [topic] using Perplexity sonar-pro:
- Current state
- Key findings
- Recommendations
Include all sources with URLs.
```

### Deep Research (sonar-deep-research)
For comprehensive reports (async, takes 2-5 minutes):
```
Conduct deep research on [topic]:
- Comprehensive analysis
- Multiple perspectives
- Extensive sourcing
Use sonar-deep-research model.
```

## Workflow

### 1. Quick Lookup
Use the MCP perplexity_search tool directly for fast answers.

### 2. Structured Research
1. Define research question and scope
2. Use appropriate Perplexity model via MCP
3. Capture response with citations
4. Format output:
   - **Summary**: 2-3 sentence overview
   - **Key Findings**: Bullet points
   - **Sources**: URLs with titles
   - **Next Actions**: Specific follow-ups

### 3. Save Research
Store findings in project documentation:
```
docs/research/YYYY-MM-DD-topic.md
```

## Prompt Templates

### Technology Evaluation
```
Evaluate [TECHNOLOGY] for [USE CASE]:
1. What problems does it solve?
2. Current alternatives and comparisons
3. Pros and cons
4. Community and maintenance status
5. Integration complexity
6. Recommendation with reasoning
Include sources from 2024-2025.
```

### Best Practices Research
```
Research current best practices for [DOMAIN]:
- Industry standards (2024-2025)
- Common implementation patterns
- Pitfalls to avoid
- Recommended tools and frameworks
Cite authoritative sources.
```

### API/Library Investigation
```
Investigate [API/LIBRARY]:
- Official documentation links
- Key features and capabilities
- Usage examples
- Known limitations
- Version compatibility
Prioritize official docs and recent sources.
```

### Competitive Analysis
```
Analyze competitors in [MARKET]:
- Top 5 players with market position
- Feature comparison matrix
- Pricing models
- Strengths and weaknesses
- Market trends
Include recent news and announcements.
```

## Model Selection Guide

| Query Type | Model | When to Use |
|------------|-------|-------------|
| Quick facts | sonar | Simple lookups, definitions |
| Analysis | sonar-pro | Complex queries, comparisons |
| Reasoning | sonar-reasoning | Technical decisions, trade-offs |
| Reports | sonar-deep-research | Comprehensive documentation |

## Tips

- **Recency**: Perplexity excels at recent information (last 24-48 hours)
- **Citations**: Always include sources in output for verification
- **Iteration**: Use follow-up queries to drill deeper
- **Cross-reference**: For critical decisions, verify with multiple queries
- **Cost awareness**: deep-research is expensive; use sparingly
```

---

### Phase 3: Reference Files

**Effort**: 20 minutes

#### 3.1 references/models.md

```markdown
# Perplexity Model Reference

## Model Specifications

### sonar
- **Base**: Llama 3.3 70B
- **Speed**: 1200 tokens/second
- **Context**: 128K tokens
- **Best for**: Quick lookups, summaries
- **SimpleQA Score**: 0.773

### sonar-pro
- **Speed**: Fast
- **Context**: Extended
- **Best for**: Complex multi-step queries
- **SimpleQA Score**: 0.858 (industry leading)

### sonar-reasoning
- **Base**: Custom reasoning model
- **Best for**: Technical decisions, analysis

### sonar-reasoning-pro
- **Base**: DeepSeek-R1
- **Best for**: Advanced reasoning with search

### sonar-deep-research
- **Mode**: Asynchronous
- **Time**: 2-5 minutes typical
- **Output**: Long-form reports with extensive citations
- **Best for**: Comprehensive research reports

## Search Modes

| Mode | Depth | Cost | Use Case |
|------|-------|------|----------|
| low | Minimal | $ | Simple factual queries |
| medium | Balanced | $$ | General research |
| high | Maximum | $$$ | Complex analysis |
```

#### 3.2 references/templates.md

```markdown
# Research Prompt Templates

## Template 1: Technical Deep Dive
```
Provide a comprehensive technical analysis of [TOPIC]:

1. **Overview**: What is it and why does it matter?
2. **Architecture**: How does it work internally?
3. **Implementation**: How to use it in practice?
4. **Performance**: Benchmarks and optimization tips
5. **Ecosystem**: Related tools and integrations
6. **Future**: Roadmap and community direction

Include code examples where relevant.
Cite official documentation and recent articles (2024-2025).
```

## Template 2: Decision Matrix
```
Help me decide between [OPTION A] vs [OPTION B] for [USE CASE]:

Create a comparison matrix covering:
- Features
- Performance
- Pricing/Cost
- Learning curve
- Community support
- Long-term viability

Provide a clear recommendation with reasoning.
Include sources for claims.
```

## Template 3: Implementation Guide
```
Research how to implement [FEATURE/PATTERN]:

1. Prerequisites and dependencies
2. Step-by-step implementation
3. Common gotchas and solutions
4. Testing strategies
5. Production considerations

Focus on [LANGUAGE/FRAMEWORK] if applicable.
Include links to authoritative guides.
```
```

---

### Phase 4: Optional Async Helper Script

**Effort**: 15 minutes

#### 4.1 scripts/deep-research.sh

```bash
#!/bin/bash
# Deep research with async polling

API_KEY="${PERPLEXITY_API_KEY}"
BASE_URL="https://api.perplexity.ai"

if [ -z "$1" ]; then
  echo "Usage: deep-research.sh 'research query'"
  exit 1
fi

QUERY="$1"

# Create async job
echo "Starting deep research..."
RESPONSE=$(curl -s -X POST "${BASE_URL}/async/chat/completions" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"sonar-deep-research\",
    \"messages\": [{\"role\": \"user\", \"content\": \"${QUERY}\"}]
  }")

REQUEST_ID=$(echo "$RESPONSE" | jq -r '.id')

if [ "$REQUEST_ID" == "null" ]; then
  echo "Error creating job: $RESPONSE"
  exit 1
fi

echo "Job created: $REQUEST_ID"
echo "Polling for results..."

# Poll for completion
while true; do
  sleep 10
  STATUS=$(curl -s "${BASE_URL}/async/chat/completions/${REQUEST_ID}" \
    -H "Authorization: Bearer ${API_KEY}")

  STATE=$(echo "$STATUS" | jq -r '.status')

  if [ "$STATE" == "completed" ]; then
    echo "$STATUS" | jq -r '.choices[0].message.content'
    exit 0
  elif [ "$STATE" == "failed" ]; then
    echo "Research failed: $(echo "$STATUS" | jq -r '.error')"
    exit 1
  fi

  echo "Status: $STATE - waiting..."
done
```

---

### Phase 5: Testing & Validation

**Effort**: 15 minutes

#### 5.1 Test MCP Integration

```bash
# In Claude Code
> Use Perplexity to look up: "What are the latest React 19 features?"
```

#### 5.2 Test Skill Activation

```bash
# Skill should auto-trigger for research requests
> Research best practices for API rate limiting in FastAPI
```

#### 5.3 Validate Output Format

Check that responses include:
- [ ] Clear summary
- [ ] Bullet-pointed findings
- [ ] Source URLs with titles
- [ ] Actionable next steps

---

## Comparison: Perplexity vs Existing Options

| Feature | Perplexity | Gemini CLI | WebSearch |
|---------|------------|------------|-----------|
| Real-time data | Yes | Yes | Yes |
| Citation quality | Excellent | Good | Good |
| Deep research | Yes (async) | Limited | No |
| Reasoning modes | 4 models | 1 model | N/A |
| Cost | Pay per query | Free tier | Free |
| Speed | Very fast | Fast | Fast |
| MCP support | Official | No | Built-in |

---

## Recommended Configuration

### Environment Variables

```bash
# ~/.zshrc or ~/.bashrc
export PERPLEXITY_API_KEY="pplx-xxxxxxxxxxxx"
export PERPLEXITY_MODEL="sonar-pro"  # Default model
export PERPLEXITY_TIMEOUT_MS="300000"  # 5 minutes
```

### MCP Configuration

```json
{
  "mcpServers": {
    "perplexity": {
      "command": "npx",
      "args": ["-yq", "@perplexity-ai/mcp-server"],
      "env": {
        "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}",
        "PERPLEXITY_MODEL": "sonar-pro",
        "PERPLEXITY_TIMEOUT_MS": "300000"
      }
    }
  }
}
```

---

## Implementation Checklist

- [ ] Get Perplexity API key from https://sonar.perplexity.ai/
- [ ] Add $5 credits (or use Pro subscription)
- [ ] Install MCP server with `claude mcp add`
- [ ] Verify with `claude mcp list`
- [ ] Create skill directory `~/.claude/skills/perplexity-researcher/`
- [ ] Write SKILL.md with frontmatter
- [ ] Add reference files
- [ ] Test quick research query
- [ ] Test deep research (async)
- [ ] Document in personal skill catalog

---

## Cost Estimation

| Use Case | Model | Est. Cost |
|----------|-------|-----------|
| 10 quick lookups/day | sonar | ~$0.05/day |
| 5 deep queries/day | sonar-pro | ~$0.25/day |
| 1 research report/week | deep-research | ~$0.50/report |

**Monthly estimate for active use**: $10-20

---

## Sources

- [Perplexity API Documentation](https://docs.perplexity.ai/)
- [Perplexity Models Reference](https://docs.perplexity.ai/getting-started/models)
- [Sonar Deep Research](https://docs.perplexity.ai/getting-started/models/models/sonar-deep-research)
- [Perplexity MCP Server](https://docs.perplexity.ai/guides/mcp-server)
- [Official MCP GitHub](https://github.com/perplexityai/modelcontextprotocol)
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)
- [Sonar Pro Announcement](https://www.perplexity.ai/hub/blog/introducing-the-sonar-pro-api)
- [Async API Announcement](https://community.perplexity.ai/t/new-async-mode-for-sonar-deep-research/424)
