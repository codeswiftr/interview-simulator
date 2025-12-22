# Agent Continuation Prompt

## Project Overview
**Project**: FORGE Portfolio - Interview Simulator (Primary Focus)
**Purpose**: AI-powered interview practice platform for software engineers with transcription and Claude-generated feedback
**Tech Stack**: FastAPI + SQLModel + PostgreSQL (backend), React 19 + Vite + TailwindCSS v4 (frontend), OpenAI Whisper + Claude (AI)
**Repository**: `/Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator`

---

## Current State

### Branch
`feat/content-strategy-cto-review` - CTO strategic review of content strategies across 7 domains, plus Sprint 1-2 execution

### Recent Progress
- ✅ CTO Strategic Review completed for 7 domain content strategies
- ✅ Sprint 1 completed (5 high-priority tasks):
  - T1.1: CodeSwiftr content library (50 pieces)
  - T1.2: LeanVibe content library (50 pieces)
  - T1.3: NeoForge content library (50 pieces)
  - T2.1: COPPA compliance playbook (TheBrightHarbor)
  - T3.1: Security audit (Interview Simulator)
- ✅ Sprint 2 tasks completed (5 tasks):
  - T1.4: CodeSwiftr LinkedIn posts
  - T1.5: LeanVibe LinkedIn posts
  - T3.2: Codebase review with repomix
  - T4.1: GraphRAG market research
  - T5.1: Docker staging configs

### Current Focus
All Sprint 1 and Sprint 2 delegatable tasks are complete. The next phase requires:
1. Human review of strategic decisions in HUMAN.md files
2. Stripe pricing configuration
3. Content publishing approval
4. COPPA attorney review for TheBrightHarbor

### Blockers/Issues
- **Human Decision Required**: Stripe pricing configuration blocks revenue tracking
- **Human Decision Required**: Content publishing approval blocks distribution
- **Legal Review Required**: COPPA attorney review blocks TheBrightHarbor child-focused products

---

## Active Plan
**Plan File**: `/Users/bogdan/work/FORGE/docs/PLAN.md`
**Current Phase**: Sprint 2 Complete
**Current Task**: Awaiting human decisions
**Status**: Ready for Next Sprint / Human Review

### Immediate Next Steps
1. Commit all Sprint 1-2 deliverables (uncommitted changes pending)
2. Review HUMAN.md strategic decision requests
3. Configure Stripe pricing for Interview Simulator
4. Approve content for publishing (LinkedIn, blogs)

---

## Key Context

### Important Files
| File | Purpose |
|------|---------|
| `docs/PLAN.md` | Portfolio execution plan with sprint tracking |
| `docs/CTO_STRATEGY_REVIEW.md` | CTO analysis of content strategies |
| `docs/IMMEDIATE_ACTION_PLAN.md` | Prioritized action items |
| `HUMAN.md` | Strategic decisions requiring human input |
| `codeswiftr-com/interview-simulator/backend/app/main.py` | Backend entry point |
| `codeswiftr-com/interview-simulator/frontend/src/main.tsx` | Frontend entry point |

### Sprint 1-2 Deliverables Created
| Location | Content |
|----------|---------|
| `codeswiftr-com/interview-simulator/docs/marketing/content/` | 5 files (50 pieces): strategy, blogs, social, email, resources |
| `codeswiftr-com/interview-simulator/docs/marketing/linkedin/` | LINKEDIN_POSTS.md |
| `codeswiftr-com/interview-simulator/docker/` | Complete staging Docker setup (Dockerfile, compose, nginx) |
| `codeswiftr-com/interview-simulator/docs/CODEBASE_REVIEW.md` | Repomix codebase analysis |
| `leanvibe-dev/docs/marketing/content/` | 5 files (50 pieces): B2B technical debt content |
| `leanvibe-dev/docs/marketing/linkedin/` | LINKEDIN_POSTS.md |
| `neoforge-dev/docs/marketing/content/` | 5 files (50 pieces): GraphRAG content |
| `neoforge-dev/docs/research/GRAPHRAG_MARKET.md` | Market research |
| `thebrightharbor-com/docs/compliance/` | 5 files: COPPA playbook, privacy policy, consent workflow |

### Recent Decisions
- **Tiered Focus Strategy**: CodeSwiftr 60%, LeanVibe/NeoForge 25%, Others 15%
- **Content-First Revenue**: Generate 150+ content pieces before heavy development
- **Security Validated**: Interview Simulator passed audit with LOW risk rating

### Gotchas Discovered
- Content is created but requires human approval before publishing
- COPPA compliance playbook is informational; requires attorney review before TheBrightHarbor launch
- Stripe not configured - blocks any monetization tracking
- Many uncommitted files across the repository

### Patterns to Follow
- **Conventional Commits**: Use `feat:`, `docs:`, `fix:` prefixes
- **Never commit to main**: Feature branches only
- **80/20 Content Philosophy**: 80% problem exploration, 20% actionable advice
- **CAR+ Framework**: For behavioral interview content (Conflict > Context > Action > Result + Insight)

### Things to Avoid
- Don't auto-commit - only commit when explicitly requested
- Don't use pip - always use `uv` for Python dependencies
- Don't start child-focused products without COPPA legal review
- Don't make breaking API changes without human gate approval

---

## Commands to Run

### Verify Environment
```bash
# Backend
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/backend
uv sync

# Frontend
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/frontend
npm install
```

### Run Tests
```bash
# Backend (385 tests)
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/backend
uv run pytest

# Frontend build check
cd /Users/bogdan/work/FORGE/codeswiftr-com/interview-simulator/frontend
npm run build
```

### Start Development
```bash
# Backend
uv run uvicorn app.main:app --reload

# Frontend
npm run dev
```

### Check Git Status
```bash
cd /Users/bogdan/work/FORGE
git status
git branch --show-current  # Should be feat/content-strategy-cto-review
```

---

## Instructions for New Agent

### Mindset
You are a pragmatic senior engineer continuing CTO-level strategic work. Your approach:
- Apply Pareto principle - 20% effort for 80% value
- Content and revenue focus (Interview Simulator is LIVE)
- Delegate to subagents when skills are available
- Track all work in docs/PLAN.md

### Workflow
1. Read this context and the plan file
2. Check git status for uncommitted work
3. Review HUMAN.md for pending decisions
4. Continue with next priority task
5. Update plan status as you progress

### Available Skills for Delegation
- `content-library-producer`: 50-piece content libraries
- `content-publisher`: Transform content for specific platforms
- `compliance-playbook-writer`: Policy and compliance docs
- `dependency-auditor`: Security/dependency audits
- `repo-reviewer`: Codebase analysis
- `docker-composer`: Container configurations
- `gemini-researcher` / `perplexity-researcher`: Deep research

### Quality Gates
After each change:
1. Run affected tests
2. Ensure no regressions
3. Commit with conventional message (when requested)
4. Continue to next task

### If Stuck
- Use `/debug` for complex issues
- Use `/feedback` to review approach
- Check `docs/PLAN.md` for context
- Ask for clarification if requirements unclear

---

## Resume Command

To continue work, start with:
```
Read docs/PROMPT.md and /Users/bogdan/work/FORGE/docs/PLAN.md, verify tests pass, then help me decide next priorities.

Key decisions needed:
1. Commit all Sprint 1-2 deliverables?
2. Start Sprint 3 tasks?
3. Focus on human decisions (Stripe, publishing approval)?

DO NOT STOP! Continue with the plan like an empowered, pragmatic senior engineer.
```

---

## Quick Reference: Uncommitted Deliverables

```
Sprint 1-2 content created (150+ pieces total):
├── codeswiftr-com/interview-simulator/
│   ├── docs/marketing/content/ (5 files)
│   ├── docs/marketing/linkedin/ (1 file)
│   ├── docs/CODEBASE_REVIEW.md
│   └── docker/ (14 files)
├── leanvibe-dev/docs/marketing/
│   ├── content/ (5 files)
│   └── linkedin/ (1 file)
├── neoforge-dev/docs/
│   ├── marketing/content/ (5 files)
│   └── research/ (1 file)
└── thebrightharbor-com/docs/compliance/ (5 files)
```

---

## Frontend-Specific Context (Previous Work)

### Frontend Design System Status
All 5 epics of the Frontend Design System Unification were completed previously:
- Epic 5: Design Token Unification (HSL color system)
- Epic 6: Navigation Modernization (BottomNav, /practice route)
- Epic 7: Component API Migration (Shadcn-style Cards)
- Epic 8: Dashboard Simplification
- Epic 9: Settings & Polish

### Frontend Quality
- Build: Passes
- Tests: 263 passing, 7 pre-existing failures (useAudioRecording timing)
- Bundle sizes optimized

The frontend is production-ready and deployed to Cloudflare Pages at `app.codeswiftr.com`.
