# Behavioral Analytics API

The Behavioral Analytics API provides detailed insights into interview performance, tracking speech patterns, filler words, speaking pace, and STAR method compliance.

## Overview

Analytics are automatically generated when session feedback is created. The system analyzes interview transcripts to extract behavioral metrics that help users improve their interview skills.

## Endpoints

### GET /api/v1/analytics/sessions/{session_id}

Get behavioral analytics for a specific interview session.

**Authentication:** Required (JWT)

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "session_id": "uuid",
  "filler_word_count": 12,
  "filler_words_per_minute": 2.4,
  "speaking_pace_wpm": 135.5,
  "total_duration_seconds": 300.0,
  "pause_count": 5,
  "avg_pause_duration": 1.5,
  "star_compliance_score": 85.0,
  "overall_confidence_score": 78.5,
  "created_at": "2026-02-06T20:00:00Z"
}
```

### GET /api/v1/analytics/progress

Get user's progress over time across all interview sessions.

**Authentication:** Required (JWT)

**Response:**
```json
{
  "data_points": [
    {
      "session_id": "uuid",
      "created_at": "2026-02-01T10:00:00Z",
      "filler_words_per_minute": 3.5,
      "speaking_pace_wpm": 125.0,
      "star_compliance_score": 65.0,
      "overall_confidence_score": 70.0
    },
    {
      "session_id": "uuid",
      "created_at": "2026-02-05T14:00:00Z",
      "filler_words_per_minute": 2.1,
      "speaking_pace_wpm": 135.0,
      "star_compliance_score": 80.0,
      "overall_confidence_score": 85.0
    }
  ],
  "total_sessions": 2
}
```

### GET /api/v1/analytics/summary

Get aggregated analytics summary with averages and improvement trends.

**Authentication:** Required (JWT)

**Response:**
```json
{
  "avg_filler_words_per_minute": 2.8,
  "avg_speaking_pace_wpm": 130.0,
  "avg_star_compliance_score": 72.5,
  "avg_confidence_score": 77.5,
  "total_sessions_analyzed": 4,
  "improvement_filler_words": -28.6,
  "improvement_star_compliance": 23.1,
  "improvement_confidence": 21.4
}
```

**Note:** Improvement percentages compare the first half of sessions to the second half. Requires at least 4 sessions for trend calculation. Negative improvement in filler words indicates improvement (fewer fillers).

### POST /api/v1/analytics/generate/{session_id}

Manually trigger analytics generation for a session.

**Authentication:** Required (JWT)

**Response:** Same as GET /api/v1/analytics/sessions/{session_id}

**Note:** Analytics are usually generated automatically when session feedback is created. This endpoint is useful for regenerating analytics or generating them for older sessions.

## Metrics Explained

### Filler Words

Tracked filler words:
- um, uh
- like
- you know
- basically, actually, literally
- right, so

**filler_word_count**: Total filler words detected across all responses
**filler_words_per_minute**: Normalized rate (lower is better)

### Speaking Pace

**speaking_pace_wpm**: Words per minute

Optimal range: 120-150 WPM
- < 100 WPM: Too slow, may seem unprepared
- 100-120 WPM: Good, but can improve
- 120-150 WPM: Ideal, confident and clear
- 150-180 WPM: Fast but acceptable
- > 180 WPM: Too fast, may seem nervous

### Pauses

**pause_count**: Number of significant pauses detected
**avg_pause_duration**: Average duration of pauses in seconds

Pauses are detected from:
- Multiple consecutive spaces
- Ellipsis (...)
- [pause] markers in transcripts

### STAR Method Compliance

**star_compliance_score**: 0-100 score measuring STAR method adherence

The algorithm detects keywords for each component:
- **Situation**: situation, context, background, when, at the time
- **Task**: task, challenge, problem, goal, objective, needed to, had to
- **Action**: action, did, implemented, created, developed, led, designed
- **Result**: result, outcome, achieved, success, improved, increased, delivered

**Scoring:**
- Each component: up to 25 points
- Partial credit for 1 keyword: 15 points
- Full credit for 2+ keywords: 25 points
- Bonus for all 4 components: 10% boost (capped at 100)

### Overall Confidence Score

**overall_confidence_score**: 0-100 composite metric

Weighted calculation:
- Filler word score (40%): Lower filler rate = higher score
- Speaking pace score (30%): Optimal WPM range scores highest
- STAR compliance (30%): Higher adherence = higher score

## Integration

Analytics are automatically generated during the feedback flow:

```python
# After interview completion
POST /api/v1/feedback/generate/session/{session_id}
# This endpoint generates both feedback AND analytics

# Then retrieve analytics
GET /api/v1/analytics/sessions/{session_id}
```

## Frontend Integration Example

```typescript
// Fetch progress data for visualization
const { data } = await api.get('/analytics/progress');

// Display in Recharts line chart
<LineChart data={data.data_points}>
  <Line dataKey="star_compliance_score" stroke="#8884d8" />
  <Line dataKey="filler_words_per_minute" stroke="#82ca9d" />
  <Line dataKey="overall_confidence_score" stroke="#ffc658" />
</LineChart>
```

## Error Responses

**404 Not Found:**
- Session doesn't exist
- Analytics not yet generated
- User doesn't own the session

**400 Bad Request:**
- No responses found for session
- No valid transcripts available

**401 Unauthorized:**
- Missing or invalid JWT token

## Database Schema

```sql
CREATE TABLE interview_analytics (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES interview_sessions(id) UNIQUE,
    filler_word_count INTEGER NOT NULL,
    filler_words_per_minute FLOAT NOT NULL,
    speaking_pace_wpm FLOAT NOT NULL,
    total_duration_seconds FLOAT NOT NULL,
    pause_count INTEGER NOT NULL,
    avg_pause_duration FLOAT NOT NULL,
    star_compliance_score FLOAT NOT NULL,
    overall_confidence_score FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX ix_interview_analytics_user_id ON interview_analytics(user_id);
CREATE UNIQUE INDEX ix_interview_analytics_session_id ON interview_analytics(session_id);
```
