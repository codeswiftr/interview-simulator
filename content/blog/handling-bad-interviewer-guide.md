# How to Handle a Bad Interviewer (Without Derailing Your Chances)

Not every interviewer is skilled. Some are distracted, some are hostile, some are unclear, and some ask questions that feel unfair or poorly designed. The uncomfortable truth is that the interviewer's performance can affect your outcome even when their behavior is not your fault — and knowing how to navigate it is a real skill.

This guide covers the most common bad interviewer patterns and how to handle each one without derailing your chances.

## Why Bad Interviewers Happen

Interviewing is a skill that most engineers receive no training in. At most companies, engineers are pulled into interview loops with minimal preparation, given a generic rubric, and expected to evaluate candidates fairly. Many do not. The patterns that result — unclear questions, moving goalposts, hostile or dismissive behavior, interruptions, lack of feedback — are mostly the product of inexperience, not malice.

Understanding this reframing is useful. "Bad interviewer" usually means "undertrained interviewer." They are not trying to trap you; they are struggling with the same problem you are, from the other side. This reframing changes how you respond: with patience and professionalism rather than defensiveness.

## Pattern 1: The Silent Interviewer

**What it looks like:** You finish answering and get nothing — no acknowledgment, no follow-up, no indication of whether your answer was right, wrong, or interesting. You are left guessing whether to continue or stop.

**What is probably happening:** They are taking notes, or they are uncertain what to say, or they are evaluating quietly. Most interviewers are not intentionally withholding reactions — they are just not skilled at keeping the conversational loop alive.

**How to handle it:**

After completing your answer, offer a natural continuation: "That's my initial approach — I can walk through the time complexity if that's useful, or I can start on the implementation." This gives them a clear choice and surfaces whether they want to go deeper or move on.

If silence continues after a pause, it is appropriate to ask: "Does that address what you were looking for, or would you like me to go in a different direction?" This is not needy — it is professional communication.

Avoid filling silence with rambling. A five-second pause after finishing an answer is normal. Ten seconds is when you offer a prompt; never fill silence by repeating what you already said.

## Pattern 2: The Moving Goalpost

**What it looks like:** You answer a question, then the interviewer says "yes, but what about..." in a way that suggests you were wrong, then when you address that concern, a new concern appears. You never feel like you're getting the right answer.

**What is probably happening:** Two possibilities. First, they are genuinely exploring — leading you toward a more complex version of the problem, which is legitimate and common. Second, they are not sure what they want and are asking for it through the interview, which is poor practice.

**How to handle it:**

Accept that exploring constraints is expected. If each new "what about..." feels like a natural extension of the problem (e.g., "now add fault tolerance" → "now handle distributed state" → "now optimize for p99 latency"), you are being led through progressive complexity. This is good; engage with each layer.

If the constraints feel contradictory — "make it fast, but also make it consistent, but also make it simple, and now make it scale globally" — it is legitimate to surface the tension: "Those are somewhat competing constraints — fast and consistent typically trade off in distributed systems. Can you tell me which is higher priority in this scenario?" This is not pushback; it is exactly the reasoning engineers need to do in real work.

## Pattern 3: The Interrupting Interviewer

**What it looks like:** You are mid-explanation and the interviewer cuts you off, redirects, or starts talking over you. Your train of thought is broken repeatedly.

**What is probably happening:** They are often trying to help — they think they know where you're going and want to accelerate, or they noticed you going off track and are trying to course-correct. Rarely is it intentional rudeness.

**How to handle it:**

Let them redirect. If an interviewer interrupts with "can you focus on the database layer," accept the redirect: "Sure — for the database layer, I'd..." You lose nothing by being flexible.

If you feel you were cut off before making a critical point, it is appropriate to return to it: "Before I do — I just want to flag one thing about the caching layer that affects this, and then I'll go to the database." Keep it brief and get back on track quickly.

Do not express frustration. Do not say "I was getting to that." Even if you were, saying so reads as defensive.

## Pattern 4: The Hostile or Dismissive Interviewer

**What it looks like:** The interviewer challenges your answers in a way that feels disproportionate, dismisses your ideas quickly, or uses a tone that feels condescending or adversarial.

**What is probably happening:** Some interviewers run intentionally challenging interviews to test how you respond under pressure. Others are genuinely having a bad day. A small number are poor fits for the interviewing role.

**How to handle it:**

Stay professionally engaged. If an interviewer says "that won't work" or "that's not how we do it here," the right response is curiosity, not defensiveness: "That's useful to know — what issue would you see with that approach?" This surfaces their reasoning without ceding ground or escalating.

If you believe your answer is correct and they are pushing back incorrectly, it is appropriate to hold your position with evidence: "I think this approach works here because of X and Y — is there a specific constraint I'm missing that changes that?" You can be confident without being combative.

If the interview feels genuinely hostile (aggressive tone, dismissive comments about your experience), take note. You are evaluating them as much as they are evaluating you. A hostile interviewer is a data point about the company culture.

## Pattern 5: The Unclear Question

**What it looks like:** You receive a question that is so vague or poorly formed that you genuinely do not know what is being asked. "How would you design a good system?" "What do you know about concurrency?"

**What is probably happening:** The interviewer is asking a broad opener, expecting you to direct the conversation. Broad questions are often invitations, not full prompts.

**How to handle it:**

Clarify before answering. "When you ask about designing a good system, are you thinking about a specific scale or domain? I can go broad or focus on distributed systems trade-offs — what would be most useful?" This demonstrates structured thinking and prevents you from answering the wrong question.

If clarification is not forthcoming, make your assumptions explicit: "I'll assume we're talking about a distributed system at medium scale — I can adjust if you'd like a different angle." State the assumption, answer specifically, then offer to expand.

## After the Interview

Not every bad interview is recoverable. If an interview went sideways because of the interviewer, it is appropriate to address it in a follow-up email to the recruiter — briefly and professionally: "I felt the conversation was less structured than usual, and I'm not sure I was able to show my full capability in that format. If there's an opportunity for a follow-up conversation with a different interviewer, I'd welcome it."

This rarely works, but it occasionally does, and it costs nothing. It also signals self-awareness rather than making excuses.

The goal in a bad interview is to exit without having made it worse. Stay calm, stay curious, stay professional. You may not get the offer — but you will have conducted yourself in a way that preserves your reputation and your own sense of competence.
