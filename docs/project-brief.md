# CareerSwiftr - AI Interview Simulator

## Vision
AI-powered interview simulator for software engineers with multimodal feedback analysis.

## Problem Statement

**Challenges**:
- 68% lack practice partners
- No objective feedback (body language, filler words, pacing)
- High-stakes pressure, limited second chances
- Generic tools (static Q&A, no simulation)

## Target Audience

**Primary**: Software engineers (2-10 YOE) actively job hunting
- 2.3M interviews/year (US)
- 3-6 month job searches, 40+ hours prep time

**Secondary**: Bootcamp graduates, career changers
- 100K+ bootcamp graduates/year

## Solution

### Core Features
1. **Realistic Mock Interviews** - AI interviewer (behavioral, system design, coding), adaptive difficulty
2. **Multimodal Feedback** - Audio (Librosa), Video (EmotiEffLib), Content (LLM)
3. **Personalized Coaching** - Weakness identification, targeted recommendations, progress tracking
4. **Question Bank** - 500+ curated questions by company/role/difficulty

### Ethical Positioning
**"Simulator" not "Copilot"** - We train candidates, don't cheat for them.

## Market Analysis

| Competitor | Approach | Gap |
|------------|----------|-----|
| Pramp | Peer matching | Unreliable partners, no AI feedback |
| InterviewBit | Static Q&A | No simulation, no multimodal |
| Exponent | Video courses | Passive learning, no practice |
| Interviewing.io | Human coaches | Expensive ($225/session) |

**Differentiation**: Multimodal AI feedback, 24/7 availability, affordable ($29-79/month)

## Business Model

### B2C Pricing
| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | 5 interviews/month, basic feedback |
| Pro | $29/month | Unlimited, full multimodal |
| Premium | $79/month | + Company prep, 1:1 coaching |

### B2B Pricing
| Tier | Price | Features |
|------|-------|----------|
| Team | $199/month | 10 seats, admin dashboard |
| Enterprise | $499/month | Unlimited, SSO, custom questions |

**Revenue Targets**: Month 6: $15K MRR → Year 2: $240K MRR

## Technical Architecture

**Backend**: FastAPI + SQLModel + PostgreSQL + Redis  
**Frontend**: React 19 + Vite + TailwindCSS v4 + shadcn/ui  
**AI**: Claude (content), Whisper (transcription), Librosa (audio), Gemini 2.5 Flash (coaching)

### AI Pipeline
1. **Audio** (Librosa): Speech rate, filler words, confidence scoring
2. **Video** (EmotiEffLib): Emotion, eye contact, body language
3. **Content** (Claude): Technical accuracy, STAR method, completeness
4. **Transcription** (Whisper): Timestamped transcript with speaker diarization

## Development Status

**Current**: Launch-ready (v2 UI complete)  
**Next**: Frontend testing, production deployment

See docs/progress.md for detailed milestone tracking.

## Success Metrics

**Kill Criteria** (stop if):
- < 50 signups in 30 days
- < 10% signup → paid conversion
- NPS < 20

**Success Criteria** (continue if):
- > 100 signups in 30 days
- > 15% signup → paid conversion
- NPS > 40
- 3+ practice sessions/user/week

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| WebRTC complexity | Audio-first, video later |
| AI costs | Batch processing, caching |
| Content moderation | Pre-approved question bank |
| Ethical concerns | Clear "simulator" positioning |
