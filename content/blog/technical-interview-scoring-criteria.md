# How Technical Interviews Are Actually Scored (The Real Rubric)

Most candidates prepare for technical interviews by trying to solve problems correctly. That's not wrong — but it's incomplete. And the gap between "solved it correctly" and "got the offer" is where most rejections live.

Here's what actually happens when an interviewer walks out of your session and sits down to write their feedback.

## The Myth vs. Reality of Technical Interview Scoring

**The myth:** The interviewer checks whether you got the right answer and passes or fails you accordingly.

**The reality:** Most structured interview loops use a rubric with 4-6 dimensions, and raw correctness is only one of them. At companies with rigorous hiring processes, interviewers fill out scorecards with specific ratings per dimension. A candidate who reaches a correct solution but can't explain their reasoning, or who gets stuck on edge cases, or who communicates poorly throughout — that candidate fails even if the code compiles.

Interviewers are also not robots. The overall impression you create — whether the session felt collaborative, whether you seemed confident in your approach, whether you'd be someone enjoyable to whiteboard with — influences how they interpret ambiguous evidence.

Understanding the rubric doesn't mean gaming it. It means knowing what you're actually being evaluated on so you can practice the right things.

## The 5 Dimensions Interviewers Actually Evaluate

### 1. Problem Understanding (approximately 10%)

Before you write a single line, the interviewer is watching whether you understand what's being asked. This includes clarifying ambiguous requirements, identifying constraints (input size, data types, edge cases), and restating the problem in your own words.

Candidates who jump straight into coding without this step consistently underperform — not because they're wrong, but because they signal that they don't think through problems before acting. In a real job, that's expensive.

What good looks like: 2-3 clarifying questions, a brief restatement of your understanding, and explicit statement of constraints before you begin.

### 2. Approach and Problem Decomposition (approximately 25%)

This is the dimension where strong engineers most clearly separate themselves from average ones. Can you break a complex problem into tractable subproblems? Can you articulate why one approach is better than another?

Interviewers want to see that you're not just pattern-matching to memorized solutions. They want evidence of structured thinking. Even if your first approach isn't optimal, proposing it, explaining its tradeoffs, and then improving it is stronger than jumping directly to an optimal solution without articulating why.

What good looks like: "My first thought is a brute-force O(n²) scan. That works but we can do better — if I use a hash map to track what I've seen, I can reduce this to O(n) time with O(n) space. The tradeoff is memory, which seems acceptable here given the input constraints."

### 3. Implementation Correctness (approximately 25%)

Yes, this matters — but probably less than you think relative to the other dimensions. Clean, working code that handles the base case counts. Buggy code with elegant architecture doesn't.

What interviewers are looking for: code that actually solves the stated problem, readable variable names, reasonable structure (not a single 80-line function), and minimal unnecessary complexity.

What tanks you here: syntax errors that suggest unfamiliarity with the language, logic errors you don't catch, and code that solves a different problem than the one stated.

### 4. Communication While Coding (approximately 25%)

This is the most commonly underweighted dimension among candidates who prep through silent Leetcode practice. While you're coding, the interviewer expects you to narrate your thinking.

Not a running monologue — that's exhausting. But consistent updates: what you're implementing, why you're making the choices you're making, where you're uncertain, and what you'll check when you're done.

Why does this matter so much? Because the interview is a simulation of collaborative technical work. If you go silent for 10 minutes while you implement a solution, the interviewer has no signal about what's happening in your head. That uncertainty reads as either confusion or aloofness — neither is what you want.

What good looks like: "I'm writing the helper function here to handle the base case — I'll call it recursively from the main loop. Once I have this working I'll trace through the edge case where the array is empty."

### 5. Edge Cases and Testing (approximately 15%)

Strong candidates finish their implementation and immediately start probing it. What happens if the input is empty? What if there are duplicates? What if n equals zero or one? What about negative numbers?

This is a signal of engineering maturity. Junior engineers solve the happy path. Senior engineers instinctively ask "what breaks this."

You don't need to write formal test cases unless asked — walking through edge cases verbally while tracing through your code is sufficient.

## Red Flags That Tank Otherwise-Correct Solutions

These are the patterns that turn "probably hire" into "no hire" even when the solution is technically correct:

- **Silence for 5+ minutes.** Even when you're thinking hard, narrate it: "I'm working through the recursion here, give me a moment."
- **Not asking for help when you're stuck.** Asking for a hint is not failure. Going in circles for 10 minutes because you won't ask is.
- **Explaining the code you wrote instead of the thinking behind it.** "Here I'm iterating over the array" is not useful commentary. "I'm iterating here because I need to find all pairs, and this approach gives me O(n) since I'm checking each element once" is.
- **Arguing when the interviewer suggests an alternative.** They may be testing how you handle feedback. Engage with the suggestion: "That's a good point — the approach you're describing would also work. The tradeoff I see is..."

## How to Practice Scoring Yourself

Most self-practice involves reviewing whether your answer was correct. Almost no one reviews the other four dimensions.

Try this instead: record your next practice session (audio is fine). Then review it against the rubric above. Listen specifically for:

- Did you clarify the problem before diving in?
- Did you articulate your approach and tradeoffs before implementing?
- Did you narrate while coding, or go silent?
- Did you check edge cases at the end?

One session reviewed this way is worth five sessions where you just check if the code ran.

## When Your Feedback Mirrors the Real Rubric

AI scoring tools that give you generic feedback ("your answer was incomplete") aren't particularly useful for this kind of calibration. The feedback needs to map to the actual dimensions interviewers use.

CodeSwiftr's Interview Simulator scores your technical and behavioral answers along the dimensions that mirror real interview rubrics — communication clarity, problem decomposition, STAR structure for behavioral questions, and edge case coverage for technical ones. The goal is to give you the same signal a good interviewer would, before the real interview.

[Try a free session at app.codeswiftr.com](https://app.codeswiftr.com) and see how your answers score against the actual rubric — not just whether the solution is correct.
