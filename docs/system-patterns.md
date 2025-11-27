# System Patterns - CareerSwiftr Interview Simulator

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Interview  │  │  Feedback   │  │    Progress         │ │
│  │    Room     │  │  Dashboard  │  │    Tracker          │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                     │            │
│         └────────────────┼─────────────────────┘            │
│                          │                                  │
│                    ┌─────▼─────┐                            │
│                    │  WebRTC   │                            │
│                    │  Handler  │                            │
│                    └─────┬─────┘                            │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    API Layer                          │   │
│  │  /interviews  /questions  /feedback  /users  /auth   │   │
│  └─────────────────────────┬────────────────────────────┘   │
│                            │                                 │
│  ┌─────────────────────────▼────────────────────────────┐   │
│  │                  Service Layer                        │   │
│  │  InterviewService  FeedbackService  QuestionService  │   │
│  └─────────────────────────┬────────────────────────────┘   │
│                            │                                 │
│  ┌─────────────────────────▼────────────────────────────┐   │
│  │                    AI Layer                           │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │  │ Whisper  │  │ Librosa  │  │ Claude   │           │   │
│  │  │ (ASR)    │  │ (Audio)  │  │ (Content)│           │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘           │   │
│  │       └─────────────┼─────────────┘                  │   │
│  │                     ▼                                │   │
│  │              FeedbackAggregator                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Data Layer                           │   │
│  │        PostgreSQL (SQLModel)  │  Redis (Cache)       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Data Models

### Interview Session
```python
class InterviewSession(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    interview_type: InterviewType  # behavioral, technical, system_design
    company_style: str | None  # faang, startup, enterprise
    status: SessionStatus  # scheduled, in_progress, completed, analyzed
    scheduled_at: datetime | None
    started_at: datetime | None
    ended_at: datetime | None
    duration_seconds: int | None

    # Relations
    questions: list["InterviewQuestion"] = Relationship()
    responses: list["InterviewResponse"] = Relationship()
    feedback: "SessionFeedback" = Relationship()
```

### Interview Question
```python
class InterviewQuestion(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="interviewsession.id")
    question_id: UUID = Field(foreign_key="question.id")
    order: int
    asked_at: datetime | None
    time_limit_seconds: int = 180
```

### Question Bank
```python
class Question(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    content: str
    category: QuestionCategory  # behavioral, coding, system_design
    difficulty: Difficulty  # easy, medium, hard
    company_tags: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    topic_tags: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    expected_duration_seconds: int = 180
    sample_answer: str | None
    evaluation_criteria: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Interview Response
```python
class InterviewResponse(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="interviewsession.id")
    question_id: UUID = Field(foreign_key="question.id")

    # Media
    audio_url: str | None
    video_url: str | None

    # Transcription
    transcript: str | None
    transcript_with_timestamps: dict | None  # {word: timestamp}

    # Metrics
    duration_seconds: int
    word_count: int | None
    filler_word_count: int | None

    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Feedback Models
```python
class AudioFeedback(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    response_id: UUID = Field(foreign_key="interviewresponse.id")

    speech_rate_wpm: float  # Words per minute
    speech_rate_score: float  # 0-100 (optimal: 120-150 WPM)
    filler_words: dict  # {"um": 5, "uh": 3, "like": 8}
    filler_word_score: float  # 0-100
    volume_consistency: float  # 0-100
    confidence_score: float  # 0-100 (based on pitch variation)
    overall_audio_score: float  # 0-100

class ContentFeedback(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    response_id: UUID = Field(foreign_key="interviewresponse.id")

    technical_accuracy: float  # 0-100
    star_adherence: float  # 0-100 (for behavioral)
    answer_structure: float  # 0-100
    completeness: float  # 0-100
    relevance: float  # 0-100
    overall_content_score: float  # 0-100

    strengths: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    improvements: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    detailed_feedback: str

class SessionFeedback(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="interviewsession.id")

    overall_score: float  # 0-100
    audio_score: float
    content_score: float

    top_strengths: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    top_improvements: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))

    recommended_practice_areas: list[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    next_question_ids: list[UUID] = Field(default_factory=list, sa_column=Column(ARRAY(UUID)))

    created_at: datetime = Field(default_factory=datetime.utcnow)
```

## AI Pipeline Architecture

### 1. Audio Analysis Service (Librosa)
```python
class AudioAnalyzer:
    """Analyzes audio for speech patterns and confidence indicators."""

    def analyze(self, audio_path: str) -> AudioMetrics:
        # Load audio
        y, sr = librosa.load(audio_path)

        return AudioMetrics(
            speech_rate_wpm=self._calculate_speech_rate(y, sr),
            filler_words=self._detect_filler_words(transcript),
            volume_consistency=self._analyze_volume(y),
            confidence_score=self._analyze_pitch_confidence(y, sr)
        )

    def _analyze_pitch_confidence(self, y, sr) -> float:
        """Low pitch variation + steady volume = confidence."""
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        # Calculate coefficient of variation
        # Lower variation = higher confidence
        ...
```

### 2. Content Analysis Service (Claude)
```python
class ContentAnalyzer:
    """Analyzes answer content for technical accuracy and structure."""

    ANALYSIS_PROMPT = """
    Analyze this interview response:

    Question: {question}
    Question Type: {question_type}
    Answer: {transcript}

    Evaluate on:
    1. Technical Accuracy (0-100): Is the information correct?
    2. Structure (0-100): Is the answer well-organized?
    3. Completeness (0-100): Did they fully address the question?
    4. Relevance (0-100): Did they stay on topic?

    For behavioral questions, also evaluate:
    - STAR Method Adherence (0-100): Situation, Task, Action, Result

    Provide:
    - Scores for each dimension
    - 2-3 specific strengths
    - 2-3 actionable improvements
    - A detailed feedback paragraph

    Return as JSON.
    """

    async def analyze(self, question: str, transcript: str, question_type: str) -> ContentMetrics:
        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            messages=[{"role": "user", "content": self.ANALYSIS_PROMPT.format(...)}],
            response_format={"type": "json_object"}
        )
        return ContentMetrics.model_validate_json(response.content)
```

### 3. Feedback Aggregator
```python
class FeedbackAggregator:
    """Combines multimodal feedback into actionable insights."""

    def aggregate(
        self,
        audio_feedback: AudioFeedback,
        content_feedback: ContentFeedback
    ) -> SessionFeedback:
        # Weight scores
        overall = (
            audio_feedback.overall_audio_score * 0.3 +
            content_feedback.overall_content_score * 0.7
        )

        # Identify top areas for improvement
        improvements = self._prioritize_improvements(audio_feedback, content_feedback)

        # Generate practice recommendations
        recommendations = self._generate_recommendations(improvements)

        return SessionFeedback(
            overall_score=overall,
            audio_score=audio_feedback.overall_audio_score,
            content_score=content_feedback.overall_content_score,
            top_improvements=improvements[:3],
            recommended_practice_areas=recommendations
        )
```

## API Endpoints

### Interview Management
```
POST   /api/v1/interviews              # Create new interview session
GET    /api/v1/interviews              # List user's interviews
GET    /api/v1/interviews/{id}         # Get interview details
POST   /api/v1/interviews/{id}/start   # Start interview
POST   /api/v1/interviews/{id}/end     # End interview
DELETE /api/v1/interviews/{id}         # Cancel interview
```

### Question Bank
```
GET    /api/v1/questions               # List questions (with filters)
GET    /api/v1/questions/{id}          # Get question details
GET    /api/v1/questions/random        # Get random question by criteria
POST   /api/v1/questions               # Add question (admin)
```

### Responses & Feedback
```
POST   /api/v1/responses               # Submit interview response
GET    /api/v1/responses/{id}/feedback # Get feedback for response
GET    /api/v1/interviews/{id}/feedback # Get session feedback
```

### User Progress
```
GET    /api/v1/users/me/stats          # Get user statistics
GET    /api/v1/users/me/progress       # Get progress over time
GET    /api/v1/users/me/recommendations # Get practice recommendations
```

## WebRTC Integration

### Media Capture Flow
```
1. User clicks "Start Interview"
2. Frontend requests camera/mic permissions
3. WebRTC captures audio/video streams
4. On question completion:
   - Audio/video blobs sent to backend
   - Backend stores in S3/CloudflareR2
   - AI pipeline processes asynchronously
5. Feedback returned when analysis complete
```

### Audio Processing
```python
# Backend receives audio blob
async def process_audio(audio_blob: bytes, response_id: UUID):
    # 1. Save to object storage
    audio_url = await storage.upload(audio_blob, f"audio/{response_id}.webm")

    # 2. Transcribe with Whisper
    transcript = await whisper.transcribe(audio_url, timestamps=True)

    # 3. Analyze with Librosa
    audio_metrics = await audio_analyzer.analyze(audio_url)

    # 4. Update response record
    await response_repo.update(response_id, {
        "audio_url": audio_url,
        "transcript": transcript.text,
        "transcript_with_timestamps": transcript.segments
    })

    # 5. Save audio feedback
    await feedback_repo.create_audio_feedback(response_id, audio_metrics)
```

## Caching Strategy

### Redis Cache Keys
```
interview:{session_id}           # Active interview state
questions:category:{cat}         # Question lists by category
user:{user_id}:stats             # User statistics
feedback:{response_id}           # Computed feedback (24h TTL)
```

### Cache Invalidation
- User stats: Invalidate on new interview completion
- Questions: Invalidate on question add/update
- Feedback: Immutable, 24h TTL sufficient

## Security Considerations

### Data Privacy
- Audio/video stored encrypted at rest
- Automatic deletion after 30 days (configurable)
- User can request immediate data deletion
- No training on user data without explicit consent

### Authentication
- JWT-based authentication
- Refresh token rotation
- Rate limiting: 100 requests/minute per user

### Content Moderation
- Pre-approved question bank only (MVP)
- No user-generated content initially
- AI responses filtered for inappropriate content
