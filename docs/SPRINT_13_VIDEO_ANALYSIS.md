# Sprint 13: Video Analysis MVP — Scope & Architecture

_Status: PLANNED — awaiting LinkedIn traffic signal before implementation_
_Last updated: 2026-03-10 (S112)_

---

## Executive Summary

Wire the existing VideoAnalyzer infrastructure into the feedback pipeline so users
can record video during an interview session and receive camera presence metrics
alongside the existing audio/text feedback. The backend is ~40% complete; the
remaining work is pipeline integration, DB persistence, and a thin frontend layer.

**Trigger condition**: Do NOT start implementation until LinkedIn traffic campaign
(GATE-CONTENT) produces measurable user signal. This sprint is specced, not scheduled.

---

## What Already Exists (Do Not Rebuild)

| Component | Location | Status |
|-----------|----------|--------|
| `VideoAnalyzer` class | `backend/app/ai/video_analyzer.py` | ✅ Complete |
| `VideoMetrics` dataclass | `backend/app/ai/video_analyzer.py` | ✅ Complete |
| Video upload endpoint | `backend/app/api/upload.py` (`POST /upload/video`) | ✅ Complete, gated |
| `video_url` field on response | `backend/app/models/interview.py` | ✅ In DB + schema |
| Feature flag guard | `backend/app/api/upload.py` (`require_video_features_enabled`) | ✅ Wired |
| OpenCV fallback | `video_analyzer.py` `_neutral_metrics()` | ✅ Graceful |

**VideoMetrics output fields:**
- `confidence_score` (0–1)
- `nervousness_score` (0–1)
- `engagement_score` (0–1)
- `eye_contact_percentage` (0–1)
- `looking_away_count` (int)
- `fidget_count` (int | None)
- `hand_gesture_frequency` (float | None)
- `processing_duration_ms` (int)
- `frame_count` (int)

---

## What Needs to Be Built

### Backend (3 units of work)

**B1 — DB column: VideoMetrics on InterviewResponse**

Add columns to the `interview_response` table via Alembic migration:

```sql
ALTER TABLE interview_response ADD COLUMN video_confidence_score FLOAT;
ALTER TABLE interview_response ADD COLUMN video_nervousness_score FLOAT;
ALTER TABLE interview_response ADD COLUMN video_engagement_score FLOAT;
ALTER TABLE interview_response ADD COLUMN video_eye_contact_percentage FLOAT;
ALTER TABLE interview_response ADD COLUMN video_looking_away_count INTEGER;
```

Update `InterviewResponse` SQLModel with the new nullable columns.
Update `InterviewResponseRead` Pydantic schema to include them.

**B2 — Pipeline wiring: call analyze() after upload**

In `backend/app/services/interview_service.py` (or wherever `video_url` gets
stored after upload), add a background task call:

```python
from app.ai.video_analyzer import VideoAnalyzer

async def _store_video_metrics(response_id: int, video_path: str, db: AsyncSession):
    analyzer = VideoAnalyzer(sample_stride=15)
    metrics = await analyzer.analyze(video_path)
    await db.execute(
        update(InterviewResponse)
        .where(InterviewResponse.id == response_id)
        .values(
            video_confidence_score=metrics.confidence_score,
            video_nervousness_score=metrics.nervousness_score,
            video_engagement_score=metrics.engagement_score,
            video_eye_contact_percentage=metrics.eye_contact_percentage,
            video_looking_away_count=metrics.looking_away_count,
        )
    )
    await db.commit()
```

Schedule via `BackgroundTasks` in the upload endpoint — do NOT block the HTTP
response on video processing (it can take 5–30s for a 5-min clip).

**B3 — Enable feature flag for video**

Set `VIDEO_FEATURES_ENABLED=true` in Railway env once B1+B2 are deployed and
smoke-tested. Until then, the upload endpoint remains gated.

---

### Frontend (2 units of work)

**F1 — Video recording UI in InterviewSession**

Add an optional video recording toggle to the interview session page. When enabled:

1. Request `getUserMedia({ video: true, audio: true })`
2. Record with `MediaRecorder` (prefer `video/webm;codecs=vp9`)
3. On session stop, POST the blob to `POST /upload/video` with the `response_id`
4. Show a "Video processing…" indicator; resolve when metrics appear

The recording UI should be:
- Off by default (privacy-first)
- A small camera icon / toggle in the session controls bar
- Non-blocking: if denied or unsupported, interview continues as audio-only

**F2 — Video metrics in FeedbackPage**

On the feedback display, if `video_confidence_score` is non-null, show a
"Camera Presence" card alongside the existing audio metrics:

| Metric | Display |
|--------|---------|
| `video_confidence_score` | Confidence ring (same style as audio confidence) |
| `video_eye_contact_percentage` | "Eye contact: X%" |
| `video_engagement_score` | Engagement bar |
| `video_nervousness_score` | Only shown if > 0.6 ("Signs of nervousness detected") |

Keep the card optional — it only renders if `video_url` exists on the response.

---

## Implementation Sequence

```
B1 (migration) → B2 (pipeline wiring) → smoke test locally
                                        ↓
                               B3 (enable flag in Railway)
                                        ↓
                               F1 (recording UI)
                                        ↓
                               F2 (feedback display)
```

Do not start F1 before B2 is verified in Railway staging.

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| OpenCV not installed in Railway | Medium | Fallback to neutral metrics already implemented — no blocking |
| Video processing time > 30s for long clips | Medium | Background task pattern (B2) — HTTP response is instant |
| Browser `getUserMedia` denied | Low | Recording is opt-in; interview continues without video |
| Privacy concerns (user video stored) | Medium | Add 30-day deletion policy (same as audio), document in privacy policy |
| Large video files (5-min @ 1080p = 200–500MB) | High | Enforce 200MB cap (already in upload.py); recommend 480p recording in UI |

---

## Acceptance Criteria

- [ ] A recorded 2-minute test interview produces non-null `video_confidence_score` in DB
- [ ] FeedbackPage renders Camera Presence card when `video_url` is present
- [ ] If OpenCV is absent (Railway), metrics are 0.5 neutral (no 500 error)
- [ ] Feature flag off = upload endpoint returns 403, no UI recording toggle shown
- [ ] Video upload does not increase interview submission latency (background task verified)

---

## Out of Scope (Sprint 13)

- ML-based gaze estimation (beyond Haar cascade proxy) — post-MVP
- Real-time video analysis during the interview — post-MVP
- Video playback in feedback — post-MVP
- Multi-camera or screen share — post-MVP

---

## Dependencies

- Alembic migration runner working in Railway (`alembic upgrade head` on deploy)
- `opencv-python-headless` added to `pyproject.toml` optional deps (or Railway env)
- Cloudflare Pages deploy unblocked for F1/F2 frontend changes
