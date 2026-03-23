---
title: "What Interviewers Actually Write Down About You"
description: "Ever wonder what's in that mysterious interview feedback? A former FAANG interviewer reveals the exact rubrics, scoring systems, and notes that determine your fate."
author: "Interview Simulator Team"
date: "2026-01-29"
tags: ["interview prep", "FAANG interviews", "interview feedback", "hiring process", "technical interviews"]
---

# What Interviewers Actually Write Down About You

*A behind-the-scenes look at the notes that decide your fate.*

---

You finish the interview. The recruiter says, "You'll hear back in a week."

What happens in that week?

Your interviewer opens a feedback form and writes... something. Those words will determine whether you get an offer, a rejection, or a "maybe" that leads to another round.

**But what actually goes in that form?**

I've been on both sides. I've written hundreds of interview feedback forms at a FAANG company. I've also obsessed over what interviewers wrote about me when I was the candidate.

Here's what they're really noting—and how to influence it.

---

## The Standard Feedback Structure

Most top tech companies use some version of this format:

### 1. The Overall Rating

Usually a 1-4 or 1-5 scale:

| Rating | Meaning |
|--------|---------|
| 1 | Strong No Hire |
| 2 | Lean No Hire |
| 3 | Lean Hire |
| 4 | Strong Hire |

At most companies, you need mostly 3s and 4s to get an offer. A single 1 can tank your candidacy entirely.

### 2. The Dimension Scores

Interviewers rate you on specific dimensions. Common ones:

- **Problem-Solving**: Did you identify the right approach?
- **Coding Ability**: Could you translate your idea into working code?
- **Communication**: Did you explain your thinking clearly?
- **Technical Knowledge**: Did you demonstrate depth in relevant areas?
- **Design Sense** (for senior roles): Did you consider trade-offs, scalability, edge cases?

### 3. The Narrative Feedback

This is the free-form text. It typically includes:

- A summary of what problems were asked
- How the candidate performed on each
- Specific strengths observed
- Specific concerns raised
- A recommendation with justification

---

## What Interviewers Actually Write (Real Examples)

These are representative examples (anonymized) of real feedback:

### Strong Hire Feedback

> "Asked the candidate to design a rate limiter. They immediately identified the key constraints (distributed vs. single server, precision requirements) and proposed three approaches: token bucket, sliding window, and leaky bucket. Clearly explained trade-offs for each. Implementation was clean and handled edge cases without prompting. When I added a constraint mid-problem (multi-region), they adapted smoothly and discussed consistency trade-offs.
>
> **Communication**: Excellent—explained thinking before coding, summarized approach clearly.
>
> **Technical depth**: Strong. Understood both theoretical and practical considerations.
>
> **Recommendation**: Strong Hire. Would want them on my team."

### Lean Hire Feedback

> "Asked a medium-difficulty tree problem. Candidate eventually reached the optimal solution but needed hints to recognize the recursive structure. Code was correct but took longer than expected (~35 min). Communication was good—they verbalized their thinking throughout.
>
> **Communication**: Good—kept me informed of their thought process.
>
> **Problem-solving**: Adequate but not exceptional. Needed guidance.
>
> **Recommendation**: Lean Hire. Meets the bar but not significantly above it."

### Lean No Hire Feedback

> "Candidate struggled with a standard sliding window problem. They recognized it was a window problem but couldn't implement the shrinking logic correctly. After 30 minutes and multiple hints, they had a partially working solution with bugs.
>
> **Communication**: Fair—went quiet when stuck, had to prompt for their thinking.
>
> **Coding ability**: Below expectations. Basic syntax was fine but logic was confused.
>
> **Recommendation**: Lean No Hire. May be having a bad day, but didn't demonstrate the skills we need."

### Strong No Hire Feedback

> "Candidate was dismissive of the problem ('this is just a toy example'). When I asked clarifying questions, they seemed annoyed. They started coding before discussing approach. Code was messy and they blamed the IDE when bugs appeared.
>
> **Communication**: Poor—defensive, didn't accept feedback well.
>
> **Attitude**: Concerning. Not collaborative.
>
> **Recommendation**: Strong No Hire. Technical skills are potentially salvageable but interpersonal concerns are serious."

---

## The Hidden Factors That Influence Ratings

Here's what's not in the official rubric but absolutely affects your scores:

### 1. The First 5 Minutes Set the Tone

Interviewers form initial impressions fast. If you start confident and engaged, they interpret ambiguity in your favor later. If you start nervous and scattered, they're primed to see problems.

> "I try to fight this bias, but it's real. A candidate who starts strong and then makes a mistake gets 'they were working through a tricky edge case.' A candidate who starts weak and makes the same mistake gets 'they don't understand the fundamentals.'" — Senior Interviewer at Amazon

### 2. How You Handle Hints

Every interviewer gives hints sometimes. What they're watching is **how you receive them**.

**Good response**: "Ah, I see—I was thinking about this as a traversal problem, but you're right that memoization would help here. Let me reconsider."

**Bad response**: "Oh... okay... so you want me to use DP? I guess I can try that..."

The first candidate is **coachable**. The second is **dependent**.

### 3. What Happens After You Solve It

Many candidates relax after getting a working solution. But interviewers keep watching.

Do you:
- Test your code with edge cases?
- Discuss complexity without being asked?
- Mention how you'd improve it with more time?

These "extras" are often the difference between Lean Hire and Strong Hire.

### 4. Your Questions at the End

"Do you have any questions for me?"

This is not a formality. It's being evaluated.

**Strong signals**: Thoughtful questions about the team, technical challenges, or the role.

**Weak signals**: "No, I think I'm good" or only asking about compensation/benefits.

---

## What Happens in the Hiring Committee

Your individual feedback goes into a packet. Then a hiring committee (usually senior engineers and managers who didn't interview you) reviews it.

Here's what they're looking for:

### Consistency Across Interviewers

If one interviewer says "Strong Hire" and another says "Strong No Hire," that's a red flag. The committee will dig into why.

Inconsistency often means you had one bad interview (everyone does) or you're borderline. Neither is fatal, but both mean extra scrutiny.

### Specific Evidence

"The candidate was good at coding" doesn't move the needle. "The candidate solved a hard graph problem optimally in 20 minutes while clearly explaining the BFS traversal" does.

Interviewers who advocate for candidates bring receipts.

### Red Flags

Certain notes sink candidates regardless of other signals:

- "Dismissive" or "arrogant"
- "Blamed the tools/language/problem"
- "Couldn't explain their own code"
- "Went silent under pressure"

One Strong Hire with a red flag often loses to a consistent set of Lean Hires.

---

## How to Influence What Gets Written

Now that you know the rubric, here's how to play to it:

### 1. Verbalize Your Framework First

Before coding, say: "I'm going to approach this as a [pattern] problem. My plan is to [high-level steps]. Before I start coding, does this direction make sense?"

This gets written down as: "Candidate demonstrated strong problem-solving by identifying the approach before implementation."

### 2. Test Your Own Code

When you finish, say: "Let me trace through this with an example. If the input is [X], then... [walk through]. And let me check an edge case: what if [Y]? ... That should return [Z]. Looks correct."

This gets written down as: "Candidate proactively tested their solution and caught edge cases."

### 3. Acknowledge Trade-offs

Even if you solve the problem optimally, say: "This is O(n) time and O(n) space. If space were a constraint, we could trade off for O(1) space with O(n²) time by..."

This gets written down as: "Candidate demonstrated design sense by discussing trade-offs."

### 4. Respond to Hints Gracefully

If you get a hint, say: "That's a good point—I was overcomplicating this. Let me simplify."

This gets written down as: "Candidate was receptive to feedback and adjusted approach."

---

## Practice Getting Good Feedback

The challenge is that you can't see your interview feedback until it's too late.

The solution: get feedback during practice, so you can adjust before it matters.

**Use our [Interview Simulator](/dashboard)**: The AI interviewer generates feedback in the same format real interviewers use—dimension scores, specific observations, and overall recommendation. You'll see exactly what would get written about you before you're in the real thing.

---

## The Bottom Line

Interview feedback isn't mysterious. It's systematic.

Interviewers are looking for specific signals:
- Problem-solving approach
- Code quality
- Communication clarity
- Technical depth
- Coachability
- Attitude

Every word you say, every line you type, every reaction to a hint—it's all getting noted.

Now that you know what they're writing, you can practice giving them something good to write about.

---

*The best way to get positive feedback is to know what interviewers are looking for. Now you do.*
