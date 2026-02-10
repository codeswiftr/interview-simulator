# Changelog

All notable changes to the Interview Simulator project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **LinkedIn Posts**: 5 LinkedIn posts for marketing content
- **Typer CLI**: Command-line interface for interview automation
- **Revenue Sprint**: Assets and pricing updates for revenue features
- **Content**: 5 blog posts and social media content
- **Analytics**: Activation and upgrade event tracking
- **Test Coverage**: 92 new frontend tests for components and analytics
- **Sharing**: Share functionality with PDF export
- **Question Recommender**: AI-powered question recommendations

### Changed
- **Feedback Service**: Decomposed into focused services via XP pairing
- **Documentation**: Security audit report updated (2026-02)

### Fixed
- **Mobile**: Improved touch targets and accessibility
- **Dependencies**: Updated vulnerable packages
- **Security**: Added non-root Docker user, enhanced .gitignore
- **Tests**: Improved coverage from 66% to 68% with 56 new tests

### Security
- **Password Hashing**: Upgraded from PBKDF2-SHA256 to bcrypt
- **CORS**: Secure configuration implemented
- **Headers**: Security headers added to responses

---

## [2026-02-10]

### Affiliate Program Integration
- **Affiliate Program Integration**: Complete affiliate marketing toolkit with Rewardful tracking integration
  - Rewardful tracking script for referral and conversion tracking
  - Affiliate landing page (/affiliates) with program details
  - Email templates (5): newsletter, promo, story, career, follow-up
  - Social media copy for LinkedIn, Twitter, Instagram, and thread formats
  - Banner specifications with brand guidelines
  - Affiliate quick-start guide with strategies
  - useAffiliateTracking hook for conversion tracking
  - Stripe checkout integration with referral code support
  - Footer component with affiliate program link

- **Shared UI Components & Root Structure**:
  - Centralized UI components library (badge, button, card, score-ring, field, toast, skeleton)
  - ErrorBoundary and ThemeSlider components
  - Dashboard, feedback, interview, layout components
  - Comprehensive view pages (Dashboard, Feedback, Interview, Preparation, Settings, auth pages)
  - State management contexts
  - Auth and utility hooks
  - Type definitions for entire app

- **PWA & Offline Support**:
  - PWA support with offline capability
  - Micro-animations for enhanced UX
  - Service worker integration

- **Content Analysis & Skills Gap**:
  - Skills Gap Analysis with real API data
  - Content sanitizer service for XSS prevention
  - OpenRouter and Groq provider support for AI analysis
  - Structured sample answers (30 behavioral, 20 technical, 20 system design questions)

- **Frontend Enhancements**:
  - Mobile bottom navigation and progress page
  - Shadcn-style Card component system with Card API
  - HSL design tokens for consistent theming
  - Skeleton loading screens for improved UX
  - Route-based code splitting for performance
  - Password strength indicator component
  - Dark mode support with system preference detection
  - Component test suite (DashboardPage, HomePage, LoginPage, RegisterPage, ProgressPage, QuestionsPage, SettingsPage)
  - ImprovementsByCriteria dashboard component
  - ExitConfirmationModal for interview flow
  - TranscriptionPanel component
  - Dashboard charts (ActivityHeatmap, CategoryBreakdown, ProgressChart)
  - Feedback components (MetricCard, SampleAnswerModal)
  - Interview components enhancements (NewInterviewModal, RecordButton, TranscriptionDisplay)
  - Auth pages polish (Login, Register, ForgotPassword, ResetPassword)
  - Settings and Progress pages improvements

- **Backend Enhancements**:
  - Rate limiting for coaching hints
  - Streaming support for coaching hints
  - Gemini 2.0 Flash integration for coaching hints
  - Coaching hint endpoint with real-time AI suggestions
  - Email configuration validation to prevent regressions
  - PostHog analytics for full funnel tracking
  - Health check implementation with database/Redis connectivity
  - Stripe subscription management system
  - Audio upload endpoint with session validation
  - Question assignment on interview start
  - User progress tracking and observability
  - Beta user onboarding flow support

- **Testing Infrastructure**:
  - Vitest test framework with React Testing Library
  - MSW (Mock Service Worker) mock infrastructure
  - OpenAPI contract validation tests
  - Comprehensive service-level tests (interview_service, video_service)
  - Database setup script for coverage runs
  - Backend test coverage expanded to 627 tests
  - Frontend test suite foundation
  - Comprehensive API tests
  - Hook tests (useAudioRecording)
  - Email service integration tests

- **Security & Authentication**:
  - JWT refresh token system with rotation
  - Automatic JWT token refresh with queue handling
  - Secure CORS configuration
  - Password hashing upgrade from PBKDF2-SHA256 to bcrypt
  - Email verification
  - Security headers implementation
  - Password reset functionality
  - Auth API endpoints with proper validation

- **Audio & Media Features**:
  - Audio preview before submit
  - Safari audio compatibility
  - Real Librosa audio analysis
  - Audio playback and enhanced response review
  - Recording deck and transcription feedback

- **Data Visualization & Analytics**:
  - ActivityHeatmap component
  - SkillsRadar component
  - Progress charts and category breakdown
  - Interview readiness score display on dashboard
  - Interview readiness score endpoint

- **Content Expansion**:
  - 70 seed questions (30 behavioral, 20 technical, 20 system design)
  - STAR-format sample answers for behavioral questions
  - Structured sample answers for technical questions
  - System design question sample answers
  - Company targeting UI for interviews
  - Target company field for company-targeted interviews
  - Experience level personalization
  - 1 and 2 question count options for testing

### Changed
- **UI/UX Updates**:
  - Simplified dashboard visual design
  - Migrated remaining components to Card API
  - Updated styling with theme-appropriate elements
  - Improved dark mode contrast and audio error UX
  - Whitespace and formatting fixes
  - Modal dark mode background using inline styles
  - Design alignment strategy for CodeSwiftr brand consistency

- **Backend Updates**:
  - Improved feedback service error handling
  - Enhanced interview API endpoints
  - Updated preparation API
  - Improved content analyzer prompts
  - Fixed enum-to-string serialization for SQLModel columns
  - Enhanced structured logging and health checks
  - Improved state loading and question context display

- **Frontend TypeScript Build**:
  - Resolved all TypeScript build errors
  - Migrated to proper React hooks usage
  - Updated component types and API integration

- **Dependency Updates**:
  - Updated backend dependencies (pyproject.toml, uv.lock)
  - Updated root package dependencies
  - Updated Stripe API for new library version
  - Updated Resend SDK API usage to v2+ format
  - Switched from free tier to regular Gemini 2.5 Flash

- **Documentation Updates**:
  - Updated active context and planning documents
  - Added frontend quality plan
  - Added UI polish plan (phase 2)
  - Added comprehensive deployment guide
  - Updated soft launch review and readiness assessment
  - Updated codebase audit with current metrics
  - Updated CLAUDE.md with deployment and audit information

### Fixed
- **Test Infrastructure**:
  - Repaired 31 failing backend tests
  - Fixed test fixtures and infrastructure
  - Fixed useAudioRecording tests and coverage reporting
  - Resolved all ESLint errors (28 → 0)
  - Resolved all ruff linting errors (158 → 0)
  - Updated test mocks for ContentAnalyzer and Stripe API
  - Fixed vi.fn() mock warnings in useAudioRecording tests
  - Fixed password validation tests to use valid test passwords
  - Fixed background task tests
  - Fixed test_submit_response_wrong_question_id_fails logic
  - Removed incorrect assertions in response model tests
  - Fixed edge case tests for interviews.py error paths

- **API & Endpoint Issues**:
  - Fixed field name mismatch (transcription -> transcript)
  - Fixed login/register flow to fetch user after auth
  - Fixed auth API endpoints and database schema issues
  - Added trailing slashes to all API endpoints
  - Removed trailing slashes from auth endpoints
  - Fixed API endpoint access on Railway deployment

- **Email Service**:
  - Fixed email from field validation for Resend
  - Updated Resend SDK API usage to v2+ format
  - Fixed subject line branding
  - Updated password reset template branding and link formatting
  - Use verified sender (hello@codeswiftr.com) for Resend emails
  - Fixed email template alignment with DESIGN_SYSTEM.md

- **Database Issues**:
  - Fixed broken migration chain and revision ID length
  - Merged migration heads for video and comparison features
  - Fixed SQLModel Field definition for foreign keys

- **Audio & Recording**:
  - Fixed TTS canceled error and transcript disappearing
  - Resolved conversation mode STT conflicts with VoiceInputButton
  - Fixed audio upload 422 error by removing Content-Type override
  - Added browser support check and better microphone error messages
  - Fixed question count logic in feedback

- **Subscription & Stripe**:
  - Fixed duplicate subscriptions prevention
  - Prioritize active subscriptions in sync
  - Fixed Stripe API access for new library version
  - Properly detect scheduled cancellation in sync
  - Fixed frontend_url for checkout redirects
  - Fixed Stripe return parameter handling
  - Fixed subscription status detection for UI

- **UI & Modal Issues**:
  - Fixed dark mode background in modals using inline styles
  - Fixed infinite polling loop in transcription status
  - Fixed infinite polling on Stripe success redirect
  - Fixed CoachOverlay hook ordering
  - Fixed difficulty handling as string not enum
  - Improved dark mode support with auto-switching CSS variables

- **Deployment Issues**:
  - Fixed Dockerfile uv sync for Railway deployment
  - Fixed healthcheck configuration for startup
  - Removed alembic from start command
  - Fixed PORT env var expansion with shell form CMD
  - Added proxy-headers to uvicorn for HTTPS redirect fix
  - Added logging to email service for troubleshooting

### Security
- Upgrade password hashing from PBKDF2-SHA256 to bcrypt
- Add JWT refresh token system with automatic rotation
- Implement secure CORS configuration
- Add email verification process
- Add security headers to responses
- Implement rate limiting for coaching hints
- Add content sanitizer for XSS prevention
- Enhance password validation requirements

### Performance
- Optimize image loading for performance
- Route-based code splitting for faster initial load
- Skeleton loading screens for perceived performance
- Health check optimization

### Documentation
- Add comprehensive developer onboarding documentation
- Add detailed Sprint plans (2-10) with epic breakdowns
- Add comprehensive codebase audit (2025-12-07)
- Add DESIGN_SYSTEM.md for brand consistency
- Add Soft Launch Readiness Assessment
- Add production deployment section to CLAUDE.md
- Update gitignore and add root .gitignore
- Add environment setup instructions in README

## Release History

### Sprint 10 - Quality Improvements (Dec 2025)
- Focus on affiliate program integration
- Enhanced UI components with shared library
- Expanded test coverage
- Content sanitizer and security improvements

### Sprint 9 - Conversational Voice Mentor (Dec 2025)
- Voice quality assessment
- Conversation mode integration
- Free tier prepare access with usage tracking
- STT conflict resolution

### Sprint 8 - Onboarding & Mentor Mode (Dec 2025)
- Complete settings page implementation
- UI polish and final enhancements
- Card API migration
- Mobile bottom navigation

### Sprint 7 - Voice Integration (Dec 2025)
- Speech recognition hook foundation
- Voice input component
- Detective Q&A voice integration
- Practice coaching integration with voice

### Sprint 6 - Production Readiness (Dec 2025)
- Test coverage finalization
- Security headers and observability
- Email verification
- Production deployment configuration

### Sprint 5 - AI-Powered Preparation (Nov 2025)
- AI Ghostwriter frontend implementation
- Skills Gap Analysis
- Coaching hints with streaming support
- Gemini 2.0 Flash integration

### Sprint 4 - Technical Debt & Refactoring (Nov 2025)
- Component test suites
- E2E test infrastructure
- Lint error resolution
- Design system alignment

### Sprint 3 - Content & Learning (Oct 2025)
- Expanded question bank (50 technical questions)
- STAR-format sample answers
- JWT refresh token system
- Readiness score implementation

### Sprint 2 - Personalization & Subscriptions (Oct 2025)
- Experience level selection for personalized feedback
- Dark mode support
- Stripe subscription management
- Interview company targeting

### Sprint 1 - Core MVP (Sep 2025)
- Initial Interview Simulator MVP
- Basic interview flow
- Audio recording and analysis
- Feedback generation
- Dashboard and progress tracking

---

## Key Milestones

- **2025-12-22**: Affiliate program integration complete
- **2025-12-20**: Content strategy and CTO review complete
- **2025-12-12**: Codebase audit and quality metrics
- **2025-11-30**: Sprint 10 quality improvements begun
- **2025-11-20**: Conversational voice mentor features
- **2025-11-10**: PWA and offline support
- **2025-10-31**: AI coaching hints and content analysis
- **2025-10-15**: Test infrastructure complete
- **2025-10-01**: Production readiness features
- **2025-09-15**: Core MVP launch
