# Interview Simulator API - Bruno Collection

This is a [Bruno](https://www.usebruno.com/) collection for testing the Interview Simulator API.

## Setup

1. Install Bruno from https://www.usebruno.com/
2. Open Bruno and select "Open Collection"
3. Navigate to this `bruno` folder

## Environment

The collection uses the `local` environment by default which connects to:
- Base URL: `http://localhost:8000/api/v1`

## Usage

### Quick Start Flow

1. **Register** - Create a new user account (`auth/Register`)
2. **Login** - Get access token (`auth/Login`) - token is auto-saved
3. **Get Questions** - Browse available questions (`questions/Get All Questions`)
4. **Create Interview** - Start a new session (`interviews/Create Interview`)
5. **Start Interview** - Begin the session (`interviews/Start Interview`)
6. **Get Interview Questions** - Get assigned questions (`interviews/Get Interview Questions`)
7. **Submit Response** - Submit your answers (`interviews/Submit Response`)
8. **End Interview** - Complete the session (`interviews/End Interview`)
9. **Generate Feedback** - Get AI feedback (`feedback/Generate Session Feedback`)

### Variables

The collection uses the following variables (auto-populated from responses):

| Variable | Description | Set By |
|----------|-------------|--------|
| `accessToken` | JWT auth token | Login |
| `userId` | Current user ID | Register |
| `interviewId` | Current interview session ID | Create Interview |
| `questionId` | Current question ID | Manual / Get Questions |
| `responseId` | Current response ID | Submit Response |

### Folder Structure

- `auth/` - Authentication endpoints (register, login)
- `users/` - User profile and stats endpoints
- `questions/` - Question bank endpoints
- `interviews/` - Interview session management
- `feedback/` - Feedback generation and retrieval

## API Endpoints

### Health
- `GET /health` - Health check

### Auth/Users
- `POST /api/v1/users/register` - Register new user
- `POST /api/v1/users/login` - Login and get token
- `GET /api/v1/users/me` - Get current user
- `PATCH /api/v1/users/me` - Update profile
- `POST /api/v1/users/me/change-password` - Change password
- `DELETE /api/v1/users/me` - Delete account
- `GET /api/v1/users/me/stats` - Get user statistics
- `GET /api/v1/users/me/progress` - Get user progress

### Questions
- `GET /api/v1/questions` - Get all questions (with filters)
- `GET /api/v1/questions/random` - Get random question
- `GET /api/v1/questions/{id}` - Get question by ID

### Interviews
- `POST /api/v1/interviews` - Create interview session
- `GET /api/v1/interviews` - List all interviews
- `GET /api/v1/interviews/{id}` - Get interview by ID
- `POST /api/v1/interviews/{id}/start` - Start interview
- `POST /api/v1/interviews/{id}/end` - End interview
- `GET /api/v1/interviews/{id}/questions` - Get interview questions
- `POST /api/v1/interviews/{id}/responses` - Submit response
- `GET /api/v1/interviews/{id}/responses` - Get responses
- `POST /api/v1/interviews/quick-practice` - Quick practice mode

### Feedback
- `GET /api/v1/feedback/session/{id}` - Get session feedback
- `GET /api/v1/feedback/session/{id}/all` - Get all feedback for session
- `GET /api/v1/feedback/session/{id}/status` - Get processing status
- `GET /api/v1/feedback/response/{id}` - Get response feedback
- `POST /api/v1/feedback/generate/session/{id}` - Generate session feedback
- `POST /api/v1/feedback/generate/response/{id}` - Generate response feedback
