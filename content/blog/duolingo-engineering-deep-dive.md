# Duolingo Engineering Deep Dive: Learning Science Meets Product Engineering at Scale

Duolingo has 500 million registered users, 40 million daily actives, and a product that somehow makes people feel guilty about a cartoon owl. Behind that product is an engineering organization that runs more simultaneous A/B experiments than most companies run in a decade, invented their own machine learning algorithm for memory science, and built a notification system so well-tuned it became a cultural meme. If you're interviewing at Duolingo — or just want to understand how a learning platform operates at scale — this is what their engineers actually work on.

## The A/B Testing Machine

Duolingo runs over 500 simultaneous experiments. That number isn't a typo. At any given moment, the app you're using is a composite of hundreds of feature flags, variant assignments, and holdout groups.

The engineering challenge here isn't running individual experiments — that's solved infrastructure. The hard problem is **experiment interference**. When you're testing a new lesson format, a new streak mechanic, and a new notification copy all at the same time on the same users, how do you attribute outcome changes to the right experiment? Duolingo uses a form of orthogonal experiment assignment where experiments are bucketed into independent namespaces, reducing cross-contamination. Users are assigned to experiment groups using a hash of their user ID plus an experiment seed — deterministic, so assignment is consistent across sessions without storing it server-side.

The guardrail metrics are the most interesting part. Duolingo's north-star metric is DAU, but no experiment is allowed to ship if it causes statistically significant degradation to retention (7-day, 28-day), or to "active days" — a composite that weights days where a user completed at least one lesson. Every experiment runs against these guardrails automatically. An experiment that lifts a local metric (say, lessons started) but hurts 28-day retention gets killed regardless of how promising the primary metric looks.

**For your interview:** If Duolingo asks you to design an experimentation platform, the interesting design decisions are in assignment consistency (same user gets same variant across devices/sessions), guardrail enforcement, and handling novelty effects — users engaging with a new feature simply because it's new, not because it's better.

## The Streak and Gamification Engine

Duolingo's streak is the product's most powerful retention mechanism. Users will pay for Streak Freeze. They'll come back after months away specifically to protect a streak. This behavior is intentional and engineered.

The streak backend is an event-driven system. When a user completes a qualifying learning session, a `session_completed` event is published. A streak service consumes this event, evaluates whether it qualifies (minimum XP threshold, within the user's "day" window as defined by their timezone), and updates the streak state. The streak is stored as a simple count plus a `last_qualifying_day` timestamp.

The complexity is in edge cases. Timezone handling: a user who completes a lesson at 11:59pm in Tokyo shouldn't lose their streak if the server processes the event at 12:01am UTC. Duolingo uses user-local calendar days, not UTC. Streak Freeze is stored as a credit that the streak service automatically applies when a day is missed — the service runs a nightly job that sweeps users who haven't completed a session and applies freezes where eligible before marking streaks broken.

Streak Repair (paying gems to restore a recently-broken streak) adds another layer: the service needs to reconstruct what the streak *would have been* had the user not missed a day, which means keeping a session history queryable by date.

## ML for Lesson Difficulty: Half-Life Regression

Duolingo's researchers published their "Half-Life Regression" (HLR) algorithm in 2016, and it's genuinely clever. Classical spaced repetition (Anki, SuperMemo) uses fixed interval schedules based on self-reported recall difficulty. Duolingo replaced this with a learned model.

HLR models memory as exponential decay: your probability of correctly recalling a word at time *t* after your last exposure is `p = 2^(-t/h)`, where *h* is the "half-life" — how long until you have a 50% chance of recall. Half-life is not fixed; it grows with each successful review. The HLR model learns the parameters from billions of actual recall events in Duolingo's data, personalizing half-life to each user-word pair based on the user's historical performance on that word.

At scale, this runs as a batch prediction system. After each session, updated recall events are logged. A batch job re-scores words for review priority. The "next review due" queue is pre-computed and stored so the app can surface it without running inference at request time.

The user never sees a "review this word in 3 days" timer — it surfaces as the app choosing which lesson to give them next. That invisibility is intentional UX, not an accident.

## Push Notification Personalization

Duolingo's owl notifications became a meme, but the engineering behind them is sophisticated. The "passive-aggressive" copy variants ("You said you would practice today...") are one part of it. The deeper system is **send-time optimization**.

For each user, Duolingo maintains a model of their historical app opens by hour of day and day of week. This is combined with timezone, device type, and notification permission status. The send-time optimizer outputs a predicted optimal delivery window for each user — the time when they're most likely to open the app if prompted.

The notification pipeline works as follows: a batch job identifies users who haven't completed a session for the day and are eligible for a notification (not already sent one, not in a holdout, not opted out). It scores each user's optimal send time and enqueues the notifications in a priority queue keyed by scheduled delivery time. A delivery service pulls from this queue and dispatches through APNs/FCM.

Copy selection is a separate ML problem. Duolingo runs continuous experiments on notification copy with multi-armed bandit allocation — copy variants that generate higher open rates get more traffic. The copy also varies by streak length, days-since-last-session, and user segment.

## Interview Implications

Duolingo engineers work on product experimentation, ML personalization, gamification systems, and mobile client performance. Their interviews reflect this.

**Common system design questions:**
- *Design a spaced repetition system* — focus on how you model and store the decay function, handle review queuing efficiently, and scale to hundreds of millions of words across millions of users
- *Design a push notification optimization system* — the interesting parts are send-time personalization, rate limiting (you can't send 40M notifications at 9am), and attribution (how do you know the notification caused the open?)
- *Design a streak system* — timezone edge cases, freeze credits, and the nightly streak evaluation job are all worth discussing

Duolingo's culture is data-driven to an unusual degree. Every product decision is expected to be validated with an experiment, and engineers are expected to understand statistical significance, not just ship features. Showing comfort with experimentation thinking — guardrails, novelty effects, minimum detectable effect sizing — will stand out.

The interview is just the start. Duolingo's engineering blog has papers and posts going deep on all of these systems, and reading them before your interview loop is worth the time.
