# Full-Stack Engineer Interview Guide 2024: What's Actually Tested

Full-stack interviews are uniquely broad. You're expected to be competent across frontend (React, TypeScript, browser APIs), backend (APIs, databases, caching), and sometimes infrastructure (deployment, CI/CD). The interview process varies significantly by company, but there are consistent patterns. Here's what to prepare.

## What "Full-Stack" Actually Means in Interviews

Full-stack is a spectrum. At startups and mid-size companies, full-stack engineers genuinely own both frontend and backend. At larger companies, "full-stack" often means a backend engineer who writes some React, or a frontend engineer who writes some APIs.

**Know which you're interviewing for:**
- **True full-stack (startups/scaleups)**: Equal frontend + backend depth tested
- **Backend-leaning full-stack**: System design + backend coding, some React
- **Frontend-leaning full-stack**: Component design + React depth, some API work

Read the job description carefully. The relative emphasis tells you where to invest preparation time.

## Coding Rounds: Double the Breadth

Full-stack interviews often include both frontend and backend coding questions. Prepare for both.

### Backend Coding

Same fundamentals as pure backend engineering:
- Data structures and algorithms (LeetCode medium floor)
- API design and implementation
- Database schema design and queries

**Common backend patterns tested:**

*REST API implementation:*
```python
# FastAPI example — interviewers may ask you to design an endpoint
@router.post("/posts", response_model=PostRead, status_code=201)
async def create_post(
    post: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PostRead:
    new_post = Post(**post.model_dump(), author_id=current_user.id)
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return PostRead.model_validate(new_post)
```

*Database query with joins:*
```sql
-- Posts with author info and comment count
SELECT
    p.id,
    p.title,
    p.created_at,
    u.username AS author,
    COUNT(c.id) AS comment_count
FROM posts p
JOIN users u ON p.author_id = u.id
LEFT JOIN comments c ON c.post_id = p.id
WHERE p.published = true
GROUP BY p.id, u.username
ORDER BY p.created_at DESC
LIMIT 20;
```

### Frontend Coding

React and TypeScript are the standard. Know them at depth.

**Common frontend patterns tested:**

*Custom hooks:*
```typescript
// Reusable data fetching hook with loading/error state
function useApi<T>(url: string) {
    const [state, setState] = useState<{
        data: T | null;
        loading: boolean;
        error: string | null;
    }>({ data: null, loading: true, error: null });

    useEffect(() => {
        let cancelled = false;
        fetch(url)
            .then(res => res.json())
            .then(data => {
                if (!cancelled) setState({ data, loading: false, error: null });
            })
            .catch(err => {
                if (!cancelled) setState({ data: null, loading: false, error: err.message });
            });
        return () => { cancelled = true; };
    }, [url]);

    return state;
}
```

*Controlled form with validation:*
```typescript
function LoginForm({ onSubmit }: { onSubmit: (email: string, password: string) => void }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [errors, setErrors] = useState<Record<string, string>>({});

    const validate = (): boolean => {
        const newErrors: Record<string, string> = {};
        if (!email.includes('@')) newErrors.email = 'Invalid email';
        if (password.length < 8) newErrors.password = 'Password must be 8+ characters';
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (validate()) onSubmit(email, password);
    };

    return (
        <form onSubmit={handleSubmit}>
            <input value={email} onChange={e => setEmail(e.target.value)} type="email" />
            {errors.email && <span>{errors.email}</span>}
            <input value={password} onChange={e => setPassword(e.target.value)} type="password" />
            {errors.password && <span>{errors.password}</span>}
            <button type="submit">Login</button>
        </form>
    );
}
```

## System Design: The Full-Stack Version

Full-stack system design rounds cover the complete architecture of a web application: frontend, API layer, data layer, and infrastructure.

**Common questions:**
- Design a social media feed (Twitter/Instagram-style)
- Design a real-time collaborative tool (Google Docs-lite)
- Design an e-commerce product page with cart
- Design a dashboard with real-time charts
- Design a file sharing service (Dropbox-lite)

**Full-stack design framework:**

**1. Frontend architecture**
- Component hierarchy and data flow
- State management (local state vs. React Context vs. Redux/Zustand)
- Data fetching strategy (React Query for server state, polling vs. WebSocket for real-time)
- Performance: code splitting, lazy loading, memoization

**2. API layer**
- REST vs. GraphQL trade-offs (REST for simple CRUD, GraphQL for flexible data requirements)
- Authentication flow (JWT, session cookies, refresh token rotation)
- Rate limiting and abuse prevention
- API versioning strategy

**3. Data layer**
- Schema design for your domain
- Indexing strategy for query patterns
- Caching layer (Redis for hot reads, CDN for static assets)
- Search (Elasticsearch if full-text search required)

**4. Infrastructure and deployment**
- Container orchestration or serverless
- CI/CD pipeline: lint → test → build → deploy
- Environment management (dev/staging/prod)
- Monitoring and logging

**5. Security surface**
- HTTPS everywhere, CORS policy
- Input validation (both client and server — never trust client)
- SQL injection prevention (parameterized queries)
- XSS prevention (sanitize user-generated HTML)
- CSRF protection

**Worked example: Design a real-time collaborative note-taking app**

*Frontend*:
- React + TypeScript; Slate.js or ProseMirror for rich text editing
- WebSocket connection for real-time collaboration; operational transforms or CRDT for conflict resolution
- Optimistic updates for local edits; server reconciliation on conflict

*API*:
- REST for document CRUD + user management
- WebSocket server for real-time event distribution
- Authentication: JWT with refresh tokens; documents scoped by owner/collaborator list

*Data*:
- PostgreSQL: `documents` (id, content_snapshot, version, owner_id), `document_collaborators`, `users`
- Redis: active editing sessions + pending operations buffer
- S3: document media attachments

*Real-time sync*:
- Client sends operation (insert/delete/format at position) → WebSocket → server transforms against concurrent operations → broadcast transformed operation to all collaborators
- Periodic snapshot to PostgreSQL (every 100 ops or 30 seconds)

## TypeScript: What Full-Stack Interviews Specifically Test

TypeScript depth is expected for 2024 full-stack roles.

**Union types and type narrowing:**
```typescript
type ApiResponse<T> =
    | { status: 'success'; data: T }
    | { status: 'error'; message: string }
    | { status: 'loading' };

function handleResponse<T>(response: ApiResponse<T>): T | null {
    switch (response.status) {
        case 'success': return response.data;  // TypeScript knows .data exists
        case 'error': console.error(response.message); return null;
        case 'loading': return null;
    }
}
```

**Generic utility types:**
```typescript
// Make all properties optional and nullable
type Nullable<T> = { [K in keyof T]: T[K] | null };

// Extract the resolved type of a Promise
type UnwrappedPromise<T> = T extends Promise<infer U> ? U : T;
```

**`as const` for literal types:**
```typescript
const ROUTES = {
    HOME: '/',
    PROFILE: '/profile',
    SETTINGS: '/settings',
} as const;

type Route = typeof ROUTES[keyof typeof ROUTES]; // '/' | '/profile' | '/settings'
```

## Node.js / Express Patterns

Many full-stack roles use Node.js for the backend. Key patterns:

**Middleware chain:**
```javascript
// Authentication middleware
const requireAuth = async (req, res, next) => {
    const token = req.headers.authorization?.replace('Bearer ', '');
    if (!token) return res.status(401).json({ error: 'No token provided' });

    try {
        req.user = await verifyToken(token);
        next();
    } catch {
        res.status(401).json({ error: 'Invalid token' });
    }
};
```

**Error handling middleware:**
```javascript
// Global error handler (must have 4 parameters)
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(err.status || 500).json({
        error: err.message || 'Internal server error',
        ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
    });
});
```

## The Full-Stack Breadth Challenge

The hardest part of full-stack interviews is avoiding shallow coverage of everything. Interviewers will probe depth.

**Strategy:**
- Be honest about your stronger side and lead with it
- When asked about your weaker side, show solid fundamentals + how you'd learn what you need
- Don't pretend equal depth — it reads as dishonest and interviewers probe until they find the ceiling

**Signs of strong full-stack depth vs. surface coverage:**
- Can explain React reconciliation, not just "React re-renders on state change"
- Can explain database indexing trade-offs, not just "add an index"
- Can explain async/await under the hood, not just use it
- Can discuss CDN edge caching vs. server-side caching trade-offs

## Preparation Timeline

**Week 1: Solidify your weaker side**
If backend-strong: spend the week on React patterns, TypeScript generics, browser APIs
If frontend-strong: spend the week on SQL queries, REST design, caching patterns

**Week 2: System design**
Design 3 full-stack systems with frontend + backend + data layer each
Practice explaining each layer's trade-offs clearly

**Week 3: Algorithms + DSA**
20 LeetCode medium problems
Focus on array/string/hashmap (most applicable to full-stack problems)

**Week 4: Behavioral + Polish**
STAR stories for: shipped a full-stack feature, diagnosed a production bug, made an architecture decision
Practice switching contexts from frontend to backend in the same conversation

## What Sets Full-Stack Candidates Apart

The best full-stack candidates have one trait: **they think in data flow**. They trace a user action from browser click → React event handler → API call → database query → response → state update → DOM re-render. Every step is connected, every failure mode is accounted for.

This end-to-end mental model — owning the complete path of a feature — is the actual value proposition of a full-stack engineer. Show it clearly, and you'll stand out.
