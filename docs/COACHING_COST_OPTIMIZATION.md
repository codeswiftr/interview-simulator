# Coaching Hints Cost Optimization

## Current Implementation

### Model Selection
- **Model**: Gemini 2.0 Flash (via OpenRouter)
- **Model ID**: `google/gemini-2.0-flash-exp:free`
- **Cost**: $0.10/M input tokens, $0.40/M output tokens
- **Latency**: ~200ms average

### Prompt Structure
```
You are an interview coach. Based on the question and the candidate's current answer transcript, provide a brief, actionable hint (1-2 sentences) to help them improve their answer.

Question: {question}
Question Type: {question_type}
Current Transcript: {transcript}

Provide a specific, contextual hint. Focus on: {focus_areas}

Hint (max 100 words):
```

### Token Usage Estimate
- **Input**: ~150-200 tokens per hint (question + transcript + prompt)
- **Output**: ~50-100 tokens per hint (1-2 sentences)
- **Total**: ~200-300 tokens per hint

### Cost Per Hint
- Input: 200 tokens × $0.10/M = $0.00002
- Output: 75 tokens × $0.40/M = $0.00003
- **Total**: ~$0.00005 per hint

### Cost Per Interview Session
- **Assumptions**: 5 hints per session (average)
- **Cost**: 5 × $0.00005 = **$0.00025 per session**
- **Monthly (100 users, 10 sessions each)**: 1,000 sessions × $0.00025 = **$0.25/month**

## Optimization Strategies

### 1. Prompt Optimization ✅
**Current**: 150-200 input tokens
**Optimized**: Can reduce to 100-150 tokens by:
- Shortening system prompt
- Using abbreviations for question types
- Truncating long transcripts (keep last 200 words)

**Savings**: ~25% reduction in input tokens

### 2. Response Length Control ✅
**Current**: max_tokens=150
**Optimized**: max_tokens=100 (hints should be 1-2 sentences anyway)

**Savings**: ~20% reduction in output tokens

### 3. Transcript Truncation
**Current**: Full transcript sent
**Optimized**: Send only last 200 words (most relevant context)

**Implementation**:
```python
# Truncate transcript to last 200 words
words = transcript.split()
if len(words) > 200:
    transcript = " ".join(words[-200:])
```

**Savings**: Significant for long answers (can reduce input by 50%+)

### 4. Caching Common Hints
**Current**: Every hint is generated fresh
**Optimized**: Cache hints for common question + transcript patterns

**Implementation**:
- Cache key: hash(question_id + transcript_hash)
- TTL: 1 hour
- Hit rate estimate: 20-30% (similar questions/answers)

**Savings**: 20-30% reduction in API calls

### 5. Debouncing Optimization ✅
**Current**: 2 seconds of silence OR 50+ new words
**Optimized**: Already optimized - prevents excessive calls

**Current Behavior**: Good balance between responsiveness and cost

## Recommended Optimizations

### Priority 1: Transcript Truncation (High Impact, Low Effort)
- **Effort**: 15 minutes
- **Savings**: 20-50% reduction in input tokens
- **Impact**: Significant for long answers

### Priority 2: Response Length Reduction (High Impact, Low Effort)
- **Effort**: 1 minute (change max_tokens)
- **Savings**: 20% reduction in output tokens
- **Impact**: Immediate cost reduction

### Priority 3: Prompt Optimization (Medium Impact, Low Effort)
- **Effort**: 30 minutes
- **Savings**: 10-15% reduction in input tokens
- **Impact**: Moderate cost reduction

### Priority 4: Caching (Medium Impact, Medium Effort)
- **Effort**: 2-3 hours
- **Savings**: 20-30% reduction in API calls
- **Impact**: Good for scale, but current costs are already very low

## Cost Monitoring

### Current Costs (Baseline)
- Per hint: $0.00005
- Per session: $0.00025
- Per month (100 users): $0.25

### Target Costs (After Optimization)
- Per hint: $0.00003-0.00004 (20-40% reduction)
- Per session: $0.00015-0.00020
- Per month (100 users): $0.15-0.20

### Monitoring Metrics
- Track API calls per user per session
- Track average tokens per hint
- Track cache hit rate (if implemented)
- Monitor monthly costs via OpenRouter dashboard

## Implementation Status

### Completed ✅
- [x] Model selection (Gemini 2.0 Flash - cheapest option)
- [x] Rate limiting (5 hints/min per user)
- [x] Debouncing (2s silence or 50+ words)
- [x] Streaming (reduces perceived latency)

### Recommended Next Steps
- [ ] Implement transcript truncation (Priority 1)
- [ ] Reduce max_tokens to 100 (Priority 2)
- [ ] Optimize prompt length (Priority 3)
- [ ] Add caching for common patterns (Priority 4)

## Cost Justification

**Current costs are already extremely low**:
- $0.25/month for 1,000 sessions
- This is negligible compared to other infrastructure costs
- User value (real-time coaching) far exceeds cost

**Recommendation**: 
- Implement Priority 1-2 optimizations (easy wins)
- Monitor costs as user base grows
- Re-evaluate if costs exceed $10/month

## Notes

- Gemini 2.0 Flash is already the cheapest option available
- Rate limiting prevents abuse
- Debouncing prevents excessive calls
- Current implementation is cost-effective
- Optimization is nice-to-have, not critical
