# How to Talk About Technical Debt in Engineering Interviews

Technical debt questions are among the most revealing in any engineering interview — and among the most mishandled. Candidates either treat them as a chance to vent about a terrible codebase, or they go the other direction and pretend debt doesn't exist in software they've touched. Both approaches signal immaturity. The interviewers asking these questions are watching for something specific: do you understand the trade-offs inherent in software development, and can you reason about them with the same clarity you'd bring to a system design problem?

## Why Technical Debt Questions Are Traps in Both Directions

If you spend five minutes complaining about the unmaintainable mess your last team left behind, you've told the interviewer two things. First, you don't take ownership — it was always someone else's fault. Second, you may not understand that technical debt is often a rational choice, not a failure.

But the opposite trap is just as damaging. If you claim you've never accumulated technical debt, or that your codebases were always clean, experienced interviewers will assume one of two things: you haven't shipped anything under real pressure, or you lack the self-awareness to recognize debt when you've created it.

The interviewers want you to occupy the middle ground. They want to hear that you understand debt as a tool — one that can be used deliberately and paid back strategically, or one that accumulates accidentally and needs to be managed before it compounds.

## The Vocabulary Interviewers Expect

Ward Cunningham coined the technical debt metaphor in 1992, and he was careful about what he meant. In his original framing, debt was the extra work caused by choosing an easier solution now instead of a better approach that would have taken longer. The key word is *choosing* — it was a deliberate decision with an expected payback.

The distinction interviewers care about is between **deliberate debt** and **accidental debt**.

Deliberate debt is a trade-off you made consciously: you shipped a hard-coded configuration because the launch date was fixed, with a ticket already written to generalize it in the next sprint. This shows judgment.

Accidental debt accumulates without awareness: you didn't know about the better pattern, the architecture grew without a plan, or nobody noticed the coupling spreading through the codebase until it was everywhere. This isn't shameful, but recognizing it when you see it — and having a plan for it — is what separates senior engineers from junior ones.

Two other terms worth knowing: **interest payments** (the ongoing cost of working around the debt — slower development, more bugs, harder onboarding) and **principal** (the work required to eliminate the debt entirely). When you frame it this way in an interview, you're using the same financial analogy the interviewer has in their head, and that shared vocabulary signals experience.

## The STAR Framework Adapted for Debt Stories

When you're asked "describe a time you dealt with technical debt," don't just narrate what happened. Use a structure that demonstrates systems thinking:

**Situation:** What was the debt, how did it originate, and how did you discover it? Be specific. "We had a monolithic payment processing module that had grown to 8,000 lines over three years" is more credible than "we had a lot of legacy code."

**Impact:** Quantify the interest payments. How many hours per sprint were lost to working around it? How many bugs originated from this area? What features couldn't be built because of the coupling? Numbers matter here.

**Decision point:** What was the trade-off analysis? Why hadn't it been paid down before? What changed to make it worth addressing now?

**Action:** What did you do, and crucially, how did you prioritize it against other work? Did you negotiate with product? Did you propose a strangler fig migration, a big rewrite, or incremental refactoring?

**Result:** What improved, and how did you measure it? Cycle time reduction, defect rate changes, onboarding speed — concrete outcomes carry weight.

## When to Advocate for Paying Down Debt vs. Shipping Features

This is where interviews separate senior engineers from everyone else. The question is essentially: do you understand product-engineering trade-offs, and can you make the business case for technical work?

The strongest signal you can send is that you can frame debt remediation in business terms. Not "the code is bad and we need to fix it" but "this module is responsible for 40% of our production incidents and it's blocking two features the sales team wants — here's the ROI on spending two sprints cleaning it up."

When debt is blocking features directly, the case is easy. When it's accumulating interest gradually, you need to track and surface the cost explicitly — because product managers aren't experiencing the slowdown the way engineers are. Making that invisible cost visible is an act of leadership.

On the other side, knowing when *not* to push for debt remediation is equally important. If the company is six weeks from a funding deadline, the deliberate debt you take on to hit that milestone is a rational choice. The mark of maturity is being intentional about it: write the ticket, note the trade-off, and don't let the temporary shortcut become permanent through neglect.

## Language Patterns That Signal Maturity

Interviewers listen for specific phrases. Here are patterns that land well:

"We made a deliberate choice to [shortcut], and we documented the trade-off because we knew we'd need to revisit it."

"The interest payments were starting to exceed the principal — every sprint we were spending more time working around it than the original fix would have taken."

"I proposed we treat it as an investment: two sprints of focused remediation to unlock three quarters of cleaner velocity."

"We couldn't justify a full rewrite, so we introduced a seam and migrated incrementally over six months."

What unites these patterns is that they show you were thinking about debt as a system — something with costs, trade-offs, and options — rather than as a problem that just existed around you. That framing is what experienced engineering managers are looking for, and it's what separates candidates who've shipped real software from those who've only worked in ideal conditions.

Technical debt is not a confession. It's a signal that you've worked on real products under real constraints — and the way you talk about it tells interviewers whether you're someone who can be trusted to make those trade-offs wisely.
