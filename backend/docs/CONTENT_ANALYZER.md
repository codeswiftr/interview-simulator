# Content Analyzer - Claude API Integration

## Overview

The `ContentAnalyzer` class provides AI-powered semantic analysis of interview responses using Anthropic's Claude API. It evaluates responses across multiple dimensions and provides structured feedback to help candidates improve their interview skills.

## Architecture

### Location
- **Module**: `app/ai/content_analyzer.py`
- **Tests**: `tests/test_content_analyzer.py`
- **Examples**: `examples/test_content_analyzer_live.py`

### Dependencies
- `anthropic>=0.37.0` - Anthropic Python SDK for Claude API
- Environment variable: `ANTHROPIC_API_KEY`

## Features

### 1. Multi-Dimensional Analysis

The analyzer evaluates responses across five key dimensions:

| Dimension | Description | Weight (Behavioral) | Weight (Technical) |
|-----------|-------------|---------------------|-------------------|
| **Technical Accuracy** | Correctness of information | 15% | 40% |
| **STAR Adherence** | Use of STAR method (Situation, Task, Action, Result) | 30% | N/A |
| **Answer Structure** | Organization and clarity | 20% | 20% |
| **Completeness** | Coverage of all question aspects | 20% | 25% |
| **Relevance** | Staying on topic | 15% | 15% |

### 2. Question Type Support

#### Behavioral Questions
- Evaluates STAR method adherence
- Focuses on storytelling and specific examples
- Checks for quantifiable results

#### Technical Questions
- Emphasizes technical accuracy (40% weight)
- Evaluates code correctness and efficiency
- Checks for consideration of edge cases

#### System Design Questions
- Assesses scalability considerations
- Evaluates trade-off analysis
- Checks for completeness of design

### 3. Structured Feedback

Each analysis returns:
- **Scores**: 0-100 for each dimension
- **Strengths**: 2-3 specific things done well
- **Improvements**: 2-3 actionable suggestions
- **Detailed Feedback**: Comprehensive paragraph of constructive feedback

## Usage

### Basic Usage

```python
from app.ai.content_analyzer import ContentAnalyzer

analyzer = ContentAnalyzer()

# Analyze a response
metrics = await analyzer.analyze(
    question="Tell me about a challenging project you worked on.",
    transcript="In my previous role, I led a team of five engineers...",
    question_type="behavioral"
)

# Calculate overall score
overall_score = analyzer.calculate_overall_score(metrics, "behavioral")

print(f"Overall Score: {overall_score:.1f}/100")
print(f"Technical Accuracy: {metrics.technical_accuracy:.1f}/100")
print(f"STAR Adherence: {metrics.star_adherence:.1f}/100")
print(f"Strengths: {metrics.strengths}")
print(f"Improvements: {metrics.improvements}")
```

### Integration with Feedback Service

```python
from app.ai.content_analyzer import ContentAnalyzer
from app.services.feedback_service import FeedbackService

# In your API endpoint or service
analyzer = ContentAnalyzer()
feedback_service = FeedbackService(session)

# Analyze content
metrics = await analyzer.analyze(
    question=question.content,
    transcript=response.transcript,
    question_type=question.category.value
)

# Calculate score
content_score = analyzer.calculate_overall_score(
    metrics,
    question.category.value
)

# Store feedback
await feedback_service.create_feedback(
    response_id=response.id,
    content_score=content_score,
    strengths=metrics.strengths,
    improvements=metrics.improvements,
    detailed_feedback=metrics.detailed_feedback
)
```

## Prompt Engineering

### Prompt Structure

The analyzer uses a carefully crafted prompt that:

1. **Sets Context**: "You are an expert interview coach..."
2. **Provides Input**: Question, question type, and transcript
3. **Defines Dimensions**: Clear scoring criteria for each dimension
4. **Conditional Instructions**: STAR method evaluation for behavioral questions only
5. **Output Format**: Strict JSON schema for consistent parsing

### STAR Method Instruction (Behavioral Questions Only)

```
For behavioral questions, also evaluate:
5. **STAR Adherence** (0-100): Did they use the STAR method effectively?
   - Situation: Did they set the context?
   - Task: Did they explain their responsibility?
   - Action: Did they describe specific actions they took?
   - Result: Did they share the outcome with metrics if possible?
```

### JSON Response Schema

```json
{
    "technical_accuracy": 85,
    "star_adherence": 75,
    "answer_structure": 80,
    "completeness": 90,
    "relevance": 88,
    "strengths": [
        "Clear and well-structured response",
        "Good use of specific examples",
        "Strong technical understanding"
    ],
    "improvements": [
        "Could add more quantifiable results",
        "Consider mentioning trade-offs",
        "Elaborate on the impact"
    ],
    "detailed_feedback": "Your response demonstrates strong technical knowledge..."
}
```

## Configuration

### Model Settings

```python
response = await self.client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2048,
    temperature=0.3,  # Lower temperature for consistent scoring
    messages=[{"role": "user", "content": prompt}],
)
```

- **Model**: Claude Sonnet 4 (latest stable version)
- **Max Tokens**: 2048 (sufficient for detailed feedback)
- **Temperature**: 0.3 (lower for more consistent scoring)

## Error Handling

### Graceful Degradation

The analyzer implements comprehensive error handling:

1. **API Errors**: Returns default 50/100 scores with error message
2. **JSON Parse Errors**: Handles markdown-wrapped responses
3. **Missing Fields**: Uses default values with `.get()`
4. **Network Failures**: Catches all exceptions and logs details

### Default Error Response

```python
ContentMetrics(
    technical_accuracy=50.0,
    star_adherence=0.0,
    answer_structure=50.0,
    completeness=50.0,
    relevance=50.0,
    strengths=["Unable to analyze due to error"],
    improvements=["Please try again"],
    detailed_feedback="Analysis failed: <error message>"
)
```

## Logging

The analyzer uses Python's `logging` module:

- **DEBUG**: Raw Claude API responses
- **INFO**: Analysis completion with key metrics
- **ERROR**: API failures, JSON parsing errors

Example:
```
INFO: Analysis complete: type=behavioral, accuracy=85.0, structure=80.0
ERROR: Failed to parse JSON response from Claude: Expecting value: line 1
```

## Testing

### Unit Tests

Comprehensive test suite covering:
- ✅ Behavioral question analysis
- ✅ Technical question analysis
- ✅ System design question analysis
- ✅ JSON markdown extraction
- ✅ API error handling
- ✅ Malformed JSON handling
- ✅ Overall score calculation
- ✅ STAR instruction inclusion/exclusion
- ✅ Prompt content verification

### Running Tests

```bash
# Run content analyzer tests
uv run pytest tests/test_content_analyzer.py -v

# Run with coverage
uv run pytest tests/test_content_analyzer.py --cov=app.ai.content_analyzer

# Run all tests
uv run pytest tests/ -v
```

### Live Testing

Test with real Claude API:

```bash
# Set API key
export ANTHROPIC_API_KEY=your_api_key

# Run example script
uv run python examples/test_content_analyzer_live.py
```

## Performance Considerations

### Response Time
- Typical analysis: 1-3 seconds (depends on Claude API latency)
- Max tokens: 2048 (sufficient for detailed feedback)
- Temperature: 0.3 (faster than higher temperatures)

### Cost Optimization
- Uses Claude Sonnet 4 (balanced cost/performance)
- Limited to 2048 tokens (prevents excessive API costs)
- Single API call per analysis (no multi-turn conversations)

### Rate Limiting
- Implement rate limiting at the API layer
- Consider caching for identical question/transcript pairs
- Queue analysis requests for batch processing

## Security & Privacy

### API Key Management
- Stored in environment variable (`ANTHROPIC_API_KEY`)
- Never logged or exposed in responses
- Should be rotated regularly in production

### Data Handling
- Transcripts sent to Claude API for analysis
- No data stored by Anthropic (per their API terms)
- Consider data retention policies for GDPR compliance

### PII Considerations
- Transcripts may contain personally identifiable information
- Implement PII detection/redaction if required
- Inform users their responses will be analyzed by AI

## Future Enhancements

### Potential Improvements
1. **Caching**: Cache analysis results for identical inputs
2. **Batch Processing**: Analyze multiple responses in parallel
3. **Custom Rubrics**: Allow per-company scoring criteria
4. **Trend Analysis**: Track improvement over time
5. **Multi-Language**: Support non-English responses
6. **Fine-Tuning**: Custom models for specific industries
7. **Real-Time Feedback**: Stream analysis during recording

### Model Upgrades
- Monitor for newer Claude models (Claude 3.5, etc.)
- Consider Claude Opus for highest quality analysis
- Evaluate Haiku model for cost-sensitive use cases

## Troubleshooting

### Common Issues

#### Issue: "ANTHROPIC_API_KEY not set"
**Solution**: Set environment variable:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

#### Issue: "JSON parsing failed"
**Solution**: Already handled gracefully with fallback metrics

#### Issue: "Rate limit exceeded"
**Solution**: Implement exponential backoff or request queuing

#### Issue: "Scores consistently low/high"
**Solution**: Adjust temperature or refine prompt instructions

## References

- [Anthropic API Documentation](https://docs.anthropic.com/claude/reference)
- [Claude Sonnet 4 Model Card](https://www.anthropic.com/news/claude-3-5-sonnet)
- [STAR Method Guide](https://www.indeed.com/career-advice/interviewing/how-to-use-the-star-interview-response-technique)

## Support

For issues or questions:
- **GitHub Issues**: [github.com/your-repo/issues](https://github.com/your-repo/issues)
- **Email**: support@careerswiftr.com
- **Documentation**: `/docs/` directory
