# The Week-Of Interview Prep Guide: What to Do in the 7 Days Before Your Loop

Most interview preparation advice focuses on the months-long grind: build a LeetCode streak, study system design frameworks, practice STAR stories. That advice is correct. But it misses the final week — the most high-leverage period in your entire preparation arc. What you do in the seven days before your interview loop determines whether all that preparation translates into an offer, or evaporates under pressure.

This guide covers the week-of strategy: how to taper, what to review, how to prepare your logistics, and how to manage your mental state so you walk into the loop at peak performance.

## Day 7: Company Intelligence Sprint

One week out, shift from generic preparation to company-specific research. This is the day to read deeply about your target company, not to study data structures.

**What to read:**
- The company's engineering blog — look for their most-discussed architectural decisions and recurring themes (e.g., Netflix on chaos engineering, Stripe on API design, Discord on their Go-to-Rust migration)
- Recent tech talks on YouTube from the company's engineers (search "[Company] engineering [current year]")
- Their open-source repositories — the README and recent commits reveal what problems they're actively solving
- Glassdoor and Blind for recent interview reports from the last 3-6 months — patterns in questions asked are reliable

**What to document:**
Create a one-page company brief: 3-4 technical challenges they face, 2-3 architectural decisions they've made and why, their current tech stack, and anything that signals what they value in engineers. You will reference this brief throughout the week.

The company brief also feeds your behavioral answers. When they ask "Why Stripe?" or "What excites you about working here?" — a vague "I love fintech" is far weaker than "Your approach to API versioning, specifically the decision to never break backwards compatibility through URL versioning, is something I've thought about a lot after dealing with breaking changes at [previous company]."

## Day 6: Algorithm Warm-Up (Not Grinding)

Six days out is not the time to learn new patterns. It is the time to verify your comfort with patterns you already know.

Run one timed session of 3-4 medium problems you have solved before. The goal is not to score yourself — it is to confirm that under time pressure, your pattern recognition is working. Common failure mode: engineers who have studied for months find they freeze for the first 5-7 minutes on problems they theoretically know, because they've only solved them at leisure, not under interview conditions.

Focus your review on:
- The 2-3 patterns that come up most often in your target company's interviews (use your Glassdoor/Blind research from Day 7)
- Anything you marked as "shaky" during your preparation — give it one final pass, not a deep re-study

Do not try to cover everything. The marginal return on studying a new pattern this late is close to zero. The marginal return on being sharp on your strongest patterns is high.

## Day 5: System Design Rehearsal

Pick one system design question relevant to your target company and do a full 45-minute mock — ideally out loud, ideally with another person or a tool that gives feedback.

The point of this mock is not the quality of the design. It is rehearsing the process: clarifying requirements, estimating scale, choosing the right data stores, walking through trade-offs explicitly. If you have been doing system design in your head, doing it out loud will reveal gaps. The jump from "I know this" to "I can explain this clearly to a skeptical interviewer" is larger than most candidates expect.

After the mock, review one system design concept you feel weakest on. Common late-stage gaps:
- Database sharding strategies and their trade-offs
- Consensus algorithms (Raft basics, what quorum means)
- CDN architecture and cache invalidation
- Event-driven architecture trade-offs (Kafka vs. queues vs. pub/sub)

One concept, one hour. Then stop.

## Day 4: Behavioral Story Polishing

Day 4 is behavioral day. Write out your 5-7 core STAR stories in full. Not bullet points — full narratives with specific numbers, specific decisions, specific outcomes.

The most common behavioral failure mode is vagueness: "I led a project to improve performance" is not a story. "I reduced our checkout API's p99 latency from 2.3 seconds to 380 milliseconds by replacing synchronous inventory checks with an async cache-aside pattern, which directly improved our conversion rate by 4.2%" is a story.

For each story, prepare three angles:
- What you did technically
- How you worked with others / resolved conflict
- What you would do differently

Most behavioral questions are variations of five archetypes: leadership/influence, conflict/collaboration, failure/learning, ambiguity/judgment, and impact/scope. Map your stories to these archetypes. The same underlying story can often answer multiple archetypes depending on which aspect you emphasize.

Also prepare your answer to "Tell me about yourself" — this is the most underrated question in technical interviews. A good answer takes 90 seconds, covers your current role briefly, a recent accomplishment with a number, and why you are interested in this company specifically. Practice it until it sounds natural.

## Day 3: Logistics and Environment

Day 3 is operational. No studying. Get your environment right.

**For virtual interviews:**
- Test your audio and video — poor audio is more distracting to interviewers than anything
- Confirm the coding platform (CoderPad, HackerRank, Google Docs, whiteboard?) and practice in it for 20 minutes
- Check your internet connection — if it has been spotty, use a wired connection or move to a location with reliable wifi
- Set up your space: clean background or virtual background, lighting in front of you not behind, camera at eye level

**For in-person interviews:**
- Confirm the office address, transit time, and where to check in
- Plan to arrive 15 minutes early — 30 minutes for large campus locations
- Bring photo ID if the building requires it
- Prepare a printed copy of your resume

**For both:**
- Confirm the schedule and interviewer names
- Prepare questions for each interviewer (not generic — tailored to their role and public work if you can find it)
- Sleep.

## Day 2: Light Review and Mental Preparation

Day 2 is maintenance, not learning. Read through your company brief from Day 7. Glance at your STAR stories. Do one easy algorithm problem to keep your pattern recognition warm.

Then stop.

The most important thing you can do on Day 2 is not study. It is rest. Fatigue impairs working memory, pattern recognition, and communication clarity — exactly the skills interviews measure. An extra hour of sleep on Day 2 will outperform an extra hour of LeetCode by a measurable margin.

If you feel compelled to review something, re-read your strongest STAR story. The goal is to go into Day 1 confident, not anxious.

## Day 1: Interview Day Protocol

**Morning:**
- Eat a real breakfast — glucose depletion shows up in problem-solving ability within a few hours
- Avoid caffeine beyond your baseline — elevated anxiety makes the first problem harder to start
- Read your company brief one more time: 15 minutes to prime your mental context

**Before each interview:**
- Take 2-3 slow breaths. Not dramatic — just enough to lower cortisol briefly
- Remind yourself: interviewers want you to succeed. They are not adversaries. They are evaluating fit, not catching you in traps

**During the interview:**
- On algorithm questions: think out loud immediately. Do not go silent and think for 3 minutes. Say what you notice, say what you are considering, say what you are ruling out. Interviewers evaluate your reasoning process, not just your answer.
- On system design: clarify before you design. Spending 5 minutes on requirements feels slow but prevents 20 minutes of designing the wrong system.
- If you are stuck: say so explicitly and ask a targeted question ("I'm not sure how to handle the case where X — would a simpler approach like Y be acceptable for this problem, or is X a hard requirement?"). Asking for the right hint is a positive signal.

**After each interview:**
Write down what you remember — questions asked, your answers, anything you were uncertain about. This serves two purposes: it helps you improve for future loops, and it gives you accurate information if you need to follow up or address gaps in a later round.

## The Offer Is Not the End

One final note: prepare for success, not just for the interview. Know your target compensation range before Day 1. Know which competing offers you have or expect. Know your walk-away number. Engineers who are unprepared for the offer stage routinely leave 15-25% on the table by accepting the first number rather than negotiating.

The interview is a job. The negotiation is where the job pays off.
