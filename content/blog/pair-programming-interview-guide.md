# The Pair Programming Interview: How to Collaborate While Being Evaluated

The pair programming interview is structurally different from the solo coding round, and most candidates underperform it for the same reason: they prepare for a solo coding interview and do not adjust their approach. In a solo round, thinking silently is acceptable — sometimes even preferred. In a pair programming round, silence is the primary failure mode. The format exists specifically to evaluate collaboration, communication, and how you work alongside another engineer. Treating it like a solo round with an observer is a category error.

## What the Pair Programming Format Is Testing

Companies that use pair programming interviews — Stripe, Shopify, Basecamp, many startups — are explicitly testing things that solo coding rounds cannot:

**How you work with someone else's code**: Pair programming often involves navigating an existing codebase, not starting from scratch. The interviewer may write the initial scaffold and ask you to extend it, or you may be asked to debug code together. Your ability to read unfamiliar code quickly and ask productive questions is being evaluated.

**How you receive feedback**: If you go down a wrong path and the interviewer hints at a better approach, how do you respond? Defensiveness is a failure. Adapting quickly and explaining your updated thinking is a pass.

**How you give feedback**: In true bidirectional pairing, you may be in the driver's seat and the interviewer may play the navigator role, suggesting approaches. Whether you engage with suggestions substantively or just implement them without discussion reveals your collaboration style.

**Whether you communicate your intent before coding**: In a pair, you narrate what you are about to do before you do it. Not as a verbal transcript ("now I'm writing a for loop"), but as a shared mental model ("I'm going to iterate through the array and keep track of the maximum sum I've seen so far — does that approach seem reasonable to you?").

## The Communication Pattern That Passes Pair Programming Interviews

The communication pattern for pair programming is fundamentally different from solo:

**Before writing code**: State your plan. "I'm thinking about doing X because Y. Does that seem like a reasonable direction?" This is not asking for permission — it is establishing shared context and opening a channel for the interviewer to redirect you efficiently if your direction is wrong.

**While writing code**: Narrate key decisions. Not every line, but anything non-obvious: "I'm using a set here instead of an array because I need O(1) lookup — the array approach would work but give us O(n) per check." This lets your partner (the interviewer) follow your reasoning and catch misunderstandings early.

**When stuck**: Ask a targeted question. "I'm not sure how to handle the case where X — is that something we need to worry about for this problem, or can we assume it away?" In pair programming, asking questions is not a weakness signal — it is how pairs work.

**When something is unclear**: Say so immediately. "I'm reading this function and I'm not sure what the `state` parameter represents — can you walk me through how it's used?" Asking clarifying questions about existing code is expected in pair programming; it would be strange not to.

## Navigating an Existing Codebase

Many pair programming interviews provide a partial implementation and ask you to extend it. This tests a skill that solo LeetCode prep does not: reading code you did not write.

**Start with structure, not details**: Before reading individual functions, understand the file structure and module organization. What are the main types? What are the main operations? Build a mental model of the architecture before diving into implementation details.

**Ask about intent, not implementation**: "What is this `EventBus` class responsible for?" is more efficient than trying to infer it from reading all its methods. Your interviewer knows the codebase — use that.

**Trace execution paths**: If you are asked to add a feature, trace the path of a similar existing feature first. "It looks like when a user subscribes, it goes through `SubscriptionService.create()` which calls `BillingAdapter.charge()` — is the flow I need to add similar to that?" This demonstrates systematic code reading rather than random exploration.

**Note what you do not understand and keep moving**: You will not understand everything in an unfamiliar codebase. Note the things you do not understand ("I see there's a `LockManager` here — I'm not sure why it's needed but I'll flag it and keep going") and continue. Do not get stuck trying to fully understand code that may not be relevant to your task.

## When You and the Interviewer Disagree

The pair programming interview sometimes creates genuine disagreement about approach. The interviewer may suggest a direction that seems worse to you. How you handle this is a signal.

**Wrong response**: Immediately defer. "Oh yeah, that's a better idea" without engaging with why. This signals you cannot hold technical positions.

**Wrong response**: Dismiss without engaging. "I think my approach is better." This signals you are not collaborative.

**Right response**: Engage substantively and then resolve. "Interesting — I see the appeal of that approach because it avoids the extra allocation. I went with X because I was worried about Y edge case. Do you think Y is a real concern here, or am I over-indexing on it?" Then, based on their answer, either update your position or explain why you still prefer your approach. Real pairs have this conversation all the time.

If you update your position, explain why: "That's a good point — if we can assume the input is always sorted, then the binary search approach is strictly better. Let me refactor." This demonstrates that you can be convinced by good reasoning, not just authority.

## Practical Tips for Remote Pair Programming

Most pair programming interviews happen in collaborative editors (CoderPad, VS Code Live Share, Replit). The mechanics matter:

**Let the interviewer navigate**: In VS Code Live Share, do not follow the interviewer's cursor around the file. Let them show you what they want to show you; if you need to look elsewhere, say so and move your cursor independently.

**Share your screen cursor clearly**: When you want to reference a specific line, move your cursor there and say "I'm looking at line 47 here." Do not assume your partner can see where you are focusing.

**Type at a readable speed**: In pair programming, typing too fast makes it hard for your partner to follow. You are not racing against a timer — you are collaborating. Slightly slower than your natural speed is appropriate.

**Verbalize compilation errors**: When you hit a type error or runtime exception, read it out loud and explain what it means: "Getting a NullPointerException on line 34 — looks like `users` can be null here, which I didn't account for." This keeps your partner in the loop and demonstrates your ability to debug out loud.

## The Meta-Skill: Genuine Collaboration

The companies that use pair programming interviews have deliberately chosen a format that is harder to fake than solo coding. You can grind LeetCode alone. You cannot grind genuine collaboration.

The best preparation is actual pair programming practice: find a friend, use a shared editor, work through a problem together. If you find yourself wanting to grab the keyboard and code alone, you have found the thing to fix. Pair programming interviews reward engineers who are genuinely energized by the collaborative process — who find thinking out loud natural, who are interested in their partner's perspective, and who make the session feel like work they would actually want to do every day.

Those engineers pass pair programming interviews not because they prepared for the format, but because the format was designed to find them.
