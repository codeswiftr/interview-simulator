"""Seed data for initial question bank."""

from app.models.question import Difficulty, Question, QuestionCategory

SEED_QUESTIONS = [
    # ========== BEHAVIORAL QUESTIONS (30 total: 10 easy, 10 medium, 10 hard) ==========
    Question(
        content="Tell me about a time you led a project under a tight deadline.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["startup", "Amazon", "Microsoft"],
        topic_tags=["leadership", "delivery", "time_management"],
        sample_answer="""**Situation**: Our company needed to integrate with a major partner's API before their promotional campaign launch - we had 3 weeks instead of the planned 6 weeks due to a contract timing issue.

**Task**: As the tech lead, I needed to deliver a reliable integration in half the normal time while maintaining quality standards.

**Action**: I immediately re-scoped the project with stakeholders, identifying must-have versus nice-to-have features. I broke the work into parallel workstreams: API integration, error handling, and testing. I assigned the two other developers to integration while I handled error handling and set up the test harness. We did daily 15-minute standups to unblock quickly and used feature flags to ship incrementally. I also negotiated with the partner for a 2-day testing buffer.

**Result**: We delivered the core integration on day 18, with the remaining 2 days for integration testing. The launch was successful with zero critical bugs in the first month. The project taught me that tight deadlines require ruthless prioritization and parallel execution, not just working longer hours.""",
    ),
    Question(
        content="How do you handle conflicts within a team?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
        company_tags=["enterprise", "Google", "Meta"],
        topic_tags=["communication", "teamwork", "conflict_resolution"],
        sample_answer="""**Situation**: On my previous team, two senior engineers had strongly opposing views on our API design approach - one wanted REST, the other GraphQL - and the disagreement was affecting team morale.

**Task**: As the team lead, I needed to resolve this conflict constructively while ensuring we made the right technical decision for our project.

**Action**: I scheduled a meeting with both engineers and established ground rules for respectful discussion. I asked each to present their case with specific pros and cons for our use case. I then facilitated a discussion focused on our actual requirements: client flexibility, caching needs, and team expertise. We created a simple decision matrix together.

**Result**: The team chose a REST approach with plans to add GraphQL for specific high-flexibility endpoints later. Both engineers felt heard, and one even mentioned it was the most productive technical discussion he'd had. The decision was implemented smoothly with full team buy-in.""",
    ),
    Question(
        content="Describe a situation where you failed and what you learned from it.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Amazon", "Netflix", "Apple"],
        topic_tags=["failure", "growth_mindset", "learning"],
        sample_answer="""**Situation**: I was leading a database migration project and underestimated the complexity of data transformation. I gave stakeholders a 4-week timeline that turned out to be unrealistic.

**Task**: By week 3, it was clear we wouldn't make the deadline. I had to address the failure, reset expectations, and deliver successfully.

**Action**: I immediately communicated the delay to stakeholders, taking full responsibility rather than making excuses. I explained what I had underestimated and presented a revised 6-week plan with more realistic milestones. I also implemented checkpoints to catch future estimation errors early. I did a personal retrospective to understand why I'd been overconfident: I had not prototyped the hardest transformation before estimating.

**Result**: We delivered in week 5, one week ahead of the revised schedule. While the stakeholders were initially disappointed, they appreciated my transparency and the quality of the final delivery. I now always prototype the riskiest part of any project before committing to timelines, and I've added buffer time for unknown unknowns. This failure made me a better estimator and communicator.""",
    ),
    Question(
        content="Tell me about a time when you had to influence a stakeholder without direct authority.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        company_tags=["Amazon", "Microsoft", "Salesforce"],
        topic_tags=["leadership", "influence", "stakeholder_management"],
        sample_answer="""**Situation**: Our VP of Sales wanted to launch a major feature in 4 weeks that my engineering assessment said would take 12 weeks to build properly. He had already promised clients, and I had no authority to change the timeline.

**Task**: I needed to influence the decision without direct authority while maintaining a positive relationship and finding a path forward that worked for both engineering and sales.

**Action**: I started by understanding his perspective deeply - I learned the client commitments and the revenue at stake. Instead of saying "no," I presented three options with trade-offs: Option A (full feature in 12 weeks, best quality), Option B (core feature in 6 weeks with follow-up phase), Option C (minimal viable feature in 4 weeks with significant limitations). I quantified the technical debt and bug risk for each option. I also proposed a compromise: a 5-week timeline with the VP's help prioritizing which features were truly essential for the client demo. I framed everything in terms of his goals - client satisfaction and revenue.

**Result**: The VP chose the 5-week option and helped me cut 40% of the original scope. We delivered on time, the clients were satisfied, and we avoided the quality issues that rushed development would have caused. The VP later said he appreciated that I came with solutions rather than objections. I learned that influence without authority requires understanding what matters to the other person and finding creative solutions that serve their interests.""",
    ),
    Question(
        content="Describe a complex technical decision you made and how you approached it.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        company_tags=["Google", "Meta", "Netflix"],
        topic_tags=["decision_making", "technical_leadership", "architecture"],
        sample_answer="""**Situation**: Our monolithic application was struggling to scale. We needed to decide whether to refactor the monolith, adopt microservices, or take a hybrid approach. Each option had significant implications for the team, timeline, and architecture.

**Task**: As the tech lead, I needed to make a recommendation that balanced technical soundness with business reality - team skills, timeline constraints, and operational complexity.

**Action**: I structured the decision using a weighted criteria matrix. The criteria included: team expertise (our team had no microservices experience), operational overhead (we had minimal DevOps support), time to market (business needed improvements in 6 months), and long-term scalability. I prototyped two critical paths in both architectures, measuring development velocity and complexity. I wrote an Architecture Decision Record (ADR) documenting the trade-offs. For the final decision, I involved senior engineers to stress-test my reasoning and ensure buy-in.

**Result**: We chose a hybrid approach: the modular monolith pattern with well-defined bounded contexts and the option to extract services later. This gave us 80% of the organizational benefits of microservices without the operational complexity our team wasn't ready for. Six months later, we had successfully modularized the system, and two high-traffic modules were extracted into services when the team was ready. The ADR became a template for future architectural decisions. I learned that the best technical decision considers not just technical merit but team readiness and business context.""",
    ),
    Question(
        content="Give an example of when you had to prioritize multiple competing deadlines.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["startup", "Amazon", "Uber"],
        topic_tags=["prioritization", "time_management", "pressure"],
        sample_answer="""**Situation**: I had three critical items due in the same week: a major feature for a client demo, a production bug affecting 5% of users, and a compliance audit document that was legally required.

**Task**: I needed to prioritize effectively because doing all three to full quality was impossible in the time available.

**Action**: I used a framework considering impact, urgency, and consequences of delay. The production bug was affecting real users now, so that became priority one - I fixed it in 4 hours. The compliance document had an immovable legal deadline, so that was priority two - I spent two focused days completing it. For the feature demo, I contacted the client, explained the situation, and negotiated a 3-day extension by offering to include an extra feature they'd requested. I communicated my priorities and reasoning to my manager upfront.

**Result**: All three were completed successfully: bug fixed same day, compliance met, and the demo went well with the extra feature earning positive client feedback. My manager appreciated the proactive communication and said my prioritization framework would be shared as a team best practice. I learned that competing deadlines often have more flexibility than initially apparent if you communicate early.""",
    ),
    Question(
        content="Tell me about a time you received critical feedback and how you responded.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
        company_tags=["Meta", "Google", "Apple"],
        topic_tags=["feedback", "growth_mindset", "adaptability"],
        sample_answer="""**Situation**: During a code review, a senior engineer pointed out that my code was difficult to test and too tightly coupled. Initially, I felt defensive because I had worked hard on the feature.

**Task**: I needed to receive this feedback constructively and improve my approach to writing testable code.

**Action**: Instead of responding defensively, I asked the reviewer for a 30-minute pairing session to understand their concerns better. They showed me specific examples of how dependency injection would make my code more modular. I took notes, asked clarifying questions, and then spent time studying SOLID principles and testing patterns.

**Result**: I refactored my code following their suggestions, and the test coverage went from 40% to 85%. More importantly, I internalized these patterns and started applying them proactively. Three months later, my code reviews rarely had structural feedback, and I even started helping newer engineers with testable design patterns.""",
    ),
    Question(
        content="Describe a situation where you had to work with a difficult colleague or team member.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Amazon", "Microsoft", "enterprise"],
        topic_tags=["teamwork", "conflict_resolution", "communication"],
        sample_answer="""**Situation**: I worked with a senior developer who was dismissive of others' ideas and would often reject code reviews with minimal feedback like "this is wrong" without explanation.

**Task**: I needed to maintain a productive working relationship while getting my work reviewed and merged, and ideally improve collaboration for the whole team.

**Action**: Instead of escalating or avoiding them, I approached them directly but diplomatically. I asked for a 1:1 to understand their perspective better. I learned they were frustrated with the codebase's technical debt and felt pressure to maintain quality. I started asking them specific questions like "What approach would you suggest?" rather than defending my solutions. I also acknowledged their expertise and asked them to share it during our team's tech talks.

**Result**: Our working relationship improved significantly. They began providing more constructive feedback, and I learned a lot from their experience. They even thanked me for the invitation to present, saying it helped them feel valued. The approach of seeking to understand rather than to be understood transformed what could have been an ongoing conflict into a mentorship opportunity.""",
    ),
    Question(
        content="Tell me about the most innovative solution you've implemented in your career.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        company_tags=["Google", "Tesla", "startup"],
        topic_tags=["innovation", "problem_solving", "creativity"],
        sample_answer="""**Situation**: Our e-commerce platform processed millions of product searches daily, but our search ranking was static and didn't adapt to user behavior. Customers often couldn't find what they were looking for despite us having the products.

**Task**: I wanted to create a search ranking system that learned from user behavior in real-time, improving results automatically without manual tuning.

**Action**: I designed a novel approach combining implicit user feedback with bandit algorithms. Instead of traditional A/B testing, I implemented a Thompson Sampling system that continuously balanced exploration (trying new rankings) with exploitation (using known good rankings). The system learned from click-through rates, add-to-cart actions, and purchases to adjust rankings in near real-time. I built it to be self-correcting - it would demote rankings that led to returns or complaints. I prototyped with 5% of traffic first, measuring key metrics carefully.

**Result**: After full rollout, search-to-purchase conversion improved by 23%, and customer satisfaction scores for search increased from 3.2 to 4.1 out of 5. The system reduced manual merchandising effort by 60% as it self-optimized. It was the first such implementation at our company and became a competitive differentiator. I published an internal paper on the approach, and the patent application was filed. The innovation came from combining concepts from different domains - bandits from recommendation systems with search ranking.""",
    ),
    Question(
        content="Describe a time when you had to advocate for a technical improvement that wasn't immediately visible to business stakeholders.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        company_tags=["Netflix", "Stripe", "Airbnb"],
        topic_tags=["technical_debt", "advocacy", "business_alignment"],
        sample_answer="""**Situation**: Our application had accumulated significant technical debt in the authentication system - it was a tangled mess of legacy code that made every security update take 3x longer than necessary. Business stakeholders saw no immediate value in refactoring since "it works."

**Task**: I needed to convince leadership to invest 6 weeks of engineering time in refactoring that would produce no visible features.

**Action**: I translated technical debt into business language. I calculated the cost: every security patch took 3 weeks instead of 1, we'd had 2 security incidents traceable to the complexity, and new feature development touching auth took 40% longer. I created a risk projection showing the probability of a major security incident increasing each quarter. I proposed a phased approach where we'd see measurable improvement after each 2-week sprint. I also identified an upcoming compliance requirement that would be nearly impossible to meet with the current system. Finally, I framed it as risk mitigation rather than "cleaning up."

**Result**: Leadership approved the refactoring. After 6 weeks, auth-related development time dropped by 50%, we passed the compliance audit easily, and we had zero auth-related incidents in the following year. The CTO mentioned my approach to "selling" technical work as a model for other engineers. I learned that advocating for technical improvements requires speaking the language of risk, cost, and business outcomes - not technical elegance.""",
    ),
    # Additional BEHAVIORAL EASY questions
    Question(
        content="Tell me about a time you helped a colleague with their work.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
        company_tags=["Google", "Meta", "startup"],
        topic_tags=["teamwork", "collaboration", "helping_others"],
        sample_answer="""**Situation**: A junior developer on my team was struggling to debug a performance issue in our payment processing service. They had been stuck for two days and were becoming frustrated.

**Task**: I wanted to help them solve the problem while also teaching them debugging skills they could use independently in the future.

**Action**: Instead of just fixing it myself, I sat down with them and walked through my debugging approach. We used profiling tools together to identify that the bottleneck was N+1 queries in the database layer. I explained the concept, showed them how to recognize it in the logs, and guided them to implement eager loading as the solution.

**Result**: We fixed the issue together in about 2 hours, improving response times by 80%. More importantly, my colleague learned a new debugging technique and went on to identify and fix two similar issues on their own in the following weeks. They told me in their next 1:1 that it was a turning point in their confidence as a developer.""",
    ),
    Question(
        content="Describe a project you're most proud of.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
        company_tags=["Amazon", "Microsoft", "Apple"],
        topic_tags=["achievement", "pride", "accomplishment"],
        sample_answer="""**Situation**: Our company's mobile app had a 2.8-star rating due to slow performance and frequent crashes. Customer complaints were increasing, and it was affecting user retention.

**Task**: I volunteered to lead the performance optimization initiative with the goal of improving the app rating to 4+ stars within three months.

**Action**: I started by analyzing crash reports and user feedback to prioritize issues. I implemented a systematic approach: first fixing the top 5 crash-causing bugs, then optimizing image loading with lazy loading and caching, and finally reducing app startup time by deferring non-critical initialization. I also established performance monitoring dashboards and set up alerts for regression.

**Result**: Within three months, crash rates dropped by 90%, app startup time improved from 4 seconds to 1.2 seconds, and our rating increased from 2.8 to 4.4 stars. The app was featured in the "Apps We Love" section, and monthly active users increased by 25%. This project showed me the direct impact engineering decisions have on user experience and business outcomes.""",
    ),
    Question(
        content="How do you stay organized when working on multiple tasks?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
        company_tags=["enterprise", "startup", "Meta"],
        topic_tags=["organization", "time_management", "multitasking"],
        sample_answer="""**Situation**: During a busy quarter, I was simultaneously working on a major feature release, supporting an on-call rotation, and mentoring two interns. I needed a system to manage these competing priorities effectively.

**Task**: I had to create an organization system that would help me stay on top of all responsibilities without dropping any balls.

**Action**: I implemented a three-part system: First, I used time-blocking on my calendar, dedicating mornings to deep work on the feature and afternoons for meetings and mentoring. Second, I maintained a prioritized task list in Notion with deadlines and dependencies visible. Third, I established "office hours" for intern questions to batch interruptions. I also reviewed and adjusted priorities every Monday morning.

**Result**: I delivered the feature on time, maintained our team's SLA for on-call response, and both interns received "exceeds expectations" ratings. My manager highlighted my organization skills in my performance review, and I've since shared this system with several teammates who adopted parts of it.""",
    ),
    Question(
        content="Tell me about a time you had to learn something new quickly.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
        company_tags=["Google", "Amazon", "startup"],
        topic_tags=["learning", "adaptability", "quick_learner"],
        sample_answer="""**Situation**: Our team was asked to integrate with a Kubernetes-based infrastructure, but I had no experience with container orchestration. The deadline was two weeks, and I was the only backend engineer available.

**Task**: I needed to learn Kubernetes fundamentals quickly enough to successfully deploy our service and set up CI/CD pipelines.

**Action**: I created a structured learning plan. The first three days, I completed an online Kubernetes course focusing on core concepts: pods, services, deployments, and ConfigMaps. Days 4-7, I set up a local minikube environment and practiced deploying sample applications. Week 2, I applied this knowledge to our actual service, pairing with a DevOps engineer for one hour daily to get feedback and learn best practices.

**Result**: I successfully deployed our service to Kubernetes on time, including health checks, resource limits, and rolling deployments. The DevOps team was impressed enough to ask me to present what I learned at a team knowledge-sharing session. This experience taught me that breaking learning into structured phases and combining theory with hands-on practice is my most effective learning approach.""",
    ),
    Question(
        content="What motivates you to do your best work?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
        company_tags=["Meta", "Netflix", "Microsoft"],
        topic_tags=["motivation", "drive", "values"],
        sample_answer="""**Situation**: In my previous role, I noticed that some of my best work came during certain projects, while I felt less engaged during others. I took time to reflect on what drove that difference.

**Task**: I wanted to understand my core motivations so I could seek out work that energizes me and contribute most effectively.

**Action**: I identified three key motivators through self-reflection: First, solving problems that directly impact users - I get energized when I can see how my code improves someone's experience. Second, learning and growth - I'm motivated by projects that stretch my skills into new areas. Third, collaboration - I do my best work when brainstorming and building with teammates who bring different perspectives.

**Result**: Understanding these motivators helped me seek out user-facing projects and volunteer for cross-functional initiatives. For example, I recently led a project to rebuild our onboarding flow, which combined all three: direct user impact, learning React Native, and collaborating with design and product. My engagement and productivity increased noticeably, and my manager mentioned seeing a "new level of energy" in my work.""",
    ),
    Question(
        content="Describe your ideal work environment.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
        company_tags=["Google", "Apple", "startup"],
        topic_tags=["culture_fit", "work_style", "preferences"],
        sample_answer="""**Situation**: Having worked in both fast-paced startups and larger enterprises, I've had the opportunity to experience different work environments and understand what helps me thrive.

**Task**: I want to be thoughtful about the environment where I can contribute most effectively and grow professionally.

**Action**: Based on my experience, I've identified key elements that define my ideal environment: First, a culture of psychological safety where people can propose ideas, ask questions, and admit mistakes without fear. Second, clear goals with autonomy in how to achieve them - I appreciate knowing the "what" and "why" while having flexibility in the "how." Third, a balance of collaboration and focused work time - I value team discussions and pairing sessions, but also need uninterrupted blocks for deep technical work.

**Result**: In my last role, I found these conditions and it showed in my work - I shipped features 20% faster than my previous position, proactively proposed three process improvements that were adopted, and consistently received feedback about being an engaged team member. I've learned that environment fit significantly impacts my effectiveness, which is why I'm thoughtful about finding the right match.""",
    ),
    Question(
        content="How do you handle stress and pressure at work?",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
        company_tags=["Amazon", "Meta", "enterprise"],
        topic_tags=["stress_management", "resilience", "pressure"],
        sample_answer="""**Situation**: During a product launch, we discovered a critical security vulnerability 48 hours before go-live. The pressure was intense - executives were watching, customers were waiting, and the team was already exhausted from weeks of crunch.

**Task**: I needed to lead the fix while keeping myself and the team functioning effectively under extreme pressure.

**Action**: I applied my stress management framework. First, I took 10 minutes to assess the situation calmly and create a prioritized action plan - panic never helps. Second, I broke the problem into smaller, manageable tasks and assigned clear owners. Third, I encouraged short breaks every two hours and ordered dinner for the team - sustainable pace matters even in crises. I also kept stakeholders updated hourly to reduce "are we there yet?" interruptions.

**Result**: We fixed the vulnerability and launched only 6 hours late. Post-mortem, the team said my calm approach helped them stay focused rather than panicked. I've learned that under pressure, the most important thing I can do is stay composed, communicate clearly, and take care of my team. Stress is inevitable; how we respond to it is a choice.""",
    ),
    Question(
        content="Tell me about a time you went above and beyond for a project.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.EASY,
        company_tags=["Netflix", "Apple", "startup"],
        topic_tags=["dedication", "initiative", "extra_effort"],
        sample_answer="""**Situation**: Our team was building an internal tool for the support team, and during user testing, I noticed the support agents were struggling with the interface even though it met all the specified requirements.

**Task**: The project was technically "done" but I felt we could deliver more value with some additional work that wasn't in the original scope.

**Action**: On my own initiative, I scheduled 30-minute shadowing sessions with three support agents to understand their actual workflows. I discovered they needed quick keyboard shortcuts and the ability to see customer history at a glance. Over a weekend, I built these improvements - not because I was asked, but because I knew it would make a real difference for daily users. I also created a short training video.

**Result**: The support team's ticket resolution time dropped by 15%, and agents specifically mentioned the keyboard shortcuts and history view as "game changers." My manager appreciated the initiative, and this became a case study in our team about understanding user needs beyond requirements. The extra effort was minimal compared to the ongoing value delivered.""",
    ),
    # Additional BEHAVIORAL MEDIUM questions
    Question(
        content="Tell me about a time you had to make a decision without all the information you needed.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Amazon", "startup", "Meta"],
        topic_tags=["decision_making", "ambiguity", "judgment"],
        sample_answer="""**Situation**: During a product launch, our analytics pipeline went down 4 hours before a major marketing campaign. We had two options: delay the campaign (expensive, contractual penalties) or launch without real-time analytics (flying blind on campaign performance).

**Task**: As the engineering lead, I had 30 minutes to make a decision. I didn't have time to fully diagnose the pipeline issue or know how long a fix would take.

**Action**: I gathered the known facts: the pipeline failure was in a third-party service, our historical data was intact, and we had manual workarounds for critical metrics. I assessed the risks: launching without real-time data was uncomfortable but manageable; the contractual penalties were significant and certain. I made a framework-based decision: "What's the reversible vs. irreversible option?" We could always pause the campaign mid-flight if needed, but we couldn't un-pay penalties. I decided to launch with manual monitoring.

**Result**: We launched on time. The pipeline recovered 2 hours later, and we captured 90% of our normal analytics. The campaign performed well. My manager praised the decision-making process, and I documented the framework for future ambiguous situations. I learned that waiting for perfect information often costs more than acting on good-enough information with a backup plan.""",
    ),
    Question(
        content="Describe a situation where you had to adapt to a major change at work.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Microsoft", "enterprise"],
        topic_tags=["adaptability", "change_management", "flexibility"],
        sample_answer="""**Situation**: Our company was acquired, and we learned that our entire backend would be migrated to the parent company's tech stack within 6 months - from Python/Django to Java/Spring Boot, a language I had never used professionally.

**Task**: I needed to maintain productivity during the transition while learning a completely new technology stack, and help my team do the same.

**Action**: I embraced the change rather than resisting it. I created a personal learning plan: mornings for Spring Boot tutorials, afternoons for parallel implementation of our features in the new stack. I proposed a "learning cohort" where 5 team members met weekly to share what we'd learned and help each other with blockers. I also identified my Django patterns and actively looked for Java equivalents, which accelerated my learning. I documented gotchas and tips in a shared wiki.

**Result**: I became proficient in Java/Spring within 3 months and was one of the first on the team to complete my service migration. The learning cohort grew to 12 members across teams. My manager mentioned in my review that my attitude toward the change helped shift the team's mindset from "this is happening to us" to "this is an opportunity." The migration completed on schedule, and I gained a valuable new skill set.""",
    ),
    Question(
        content="Tell me about a time you disagreed with your manager or team lead.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Netflix", "Meta", "Apple"],
        topic_tags=["disagreement", "communication", "assertiveness"],
        sample_answer="""**Situation**: My manager wanted to ship a feature without comprehensive error handling because we were behind schedule. I believed this would create significant technical debt and customer-facing issues.

**Task**: I needed to express my disagreement professionally while respecting my manager's authority and the business pressure they were facing.

**Action**: I asked for a private 1:1 rather than disagreeing in a team meeting. I came prepared with data: I showed three similar past incidents where missing error handling caused production issues, estimated the remediation time (40 hours), and compared it to the upfront investment (8 hours). I acknowledged the deadline pressure and proposed a compromise: ship with basic error handling for critical paths only, then complete the rest in the following sprint with specific tickets created upfront.

**Result**: My manager appreciated the data-driven approach and agreed to the compromise. We shipped on time with critical error handling in place. The follow-up work was completed as planned, and we had zero production issues. My manager later told me they valued engineers who push back constructively with evidence. I learned that disagreeing effectively means making it easy for the other person to say yes - by proposing solutions, not just problems.""",
    ),
    Question(
        content="Describe a time when you had to convince a team to adopt a new approach.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Amazon", "Google", "Uber"],
        topic_tags=["influence", "persuasion", "change_agent"],
        sample_answer="""**Situation**: Our team was manually deploying code, which took 2-3 hours per release and caused frequent human errors. I wanted to introduce CI/CD but faced resistance from teammates who were comfortable with the existing process.

**Task**: I needed to convince a skeptical team to adopt automated deployments without having the authority to mandate the change.

**Action**: Instead of pushing the idea in meetings, I started by building a small proof of concept on a non-critical service. I documented the time savings and error reduction. Then I invited interested colleagues to pair with me on extending it, building allies one by one. When I had 3 team members successfully using it, I presented results to the full team: deployment time dropped from 2.5 hours to 15 minutes, and deployment errors went to zero. I addressed concerns directly - I created rollback procedures for those worried about automation failures and offered to pair with anyone uncomfortable with the new process.

**Result**: Within a month, the team voted unanimously to adopt CI/CD for all services. Within three months, we had full pipeline coverage. The key insight was that showing beats telling - a working proof of concept with real metrics was more persuasive than any presentation. I also learned to build coalitions rather than trying to convince everyone at once.""",
    ),
    Question(
        content="Tell me about a time you improved a process or system.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Microsoft", "Netflix", "startup"],
        topic_tags=["improvement", "optimization", "initiative"],
        sample_answer="""**Situation**: Our code review process was a bottleneck - PRs sat for 2-3 days on average, which slowed delivery and frustrated developers. Reviews were assigned randomly, leading to context-switching and delays.

**Task**: I wanted to improve the code review turnaround time without adding more burden to the team.

**Action**: I analyzed our PR data and found that 60% of delays came from reviewers unfamiliar with the changed codebase areas. I proposed a CODEOWNERS-based assignment system that would route PRs to developers who had recently worked on those files. I created the CODEOWNERS file by analyzing git history, set up GitHub to auto-assign reviewers, and added a Slack notification for assigned reviews. I also established a team norm: reviews should be started within 4 hours during work hours.

**Result**: Average PR review time dropped from 2.5 days to 6 hours. Review quality improved because reviewers had context. Developer satisfaction surveys showed a 40% increase in satisfaction with the review process. The improvement was adopted by two other teams in the organization. I learned that often the best process improvements come from data analysis revealing unexpected bottlenecks.""",
    ),
    Question(
        content="Describe a challenging bug or issue you debugged and how you solved it.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Meta", "Apple"],
        topic_tags=["debugging", "problem_solving", "persistence"],
        sample_answer="""**Situation**: Our application had an intermittent memory leak that only appeared in production under high load. The app would slowly consume memory over 24-48 hours until it crashed. We couldn't reproduce it in staging.

**Task**: I needed to identify and fix the root cause while the bug was actively impacting production stability.

**Action**: I started by adding detailed memory profiling to production using async-profiler with minimal overhead. After collecting 48 hours of data, I identified that memory grew specifically during peak API traffic. I narrowed it down to our caching layer - we were caching database connections that weren't being properly released. The leak only manifested under connection pool exhaustion scenarios. I wrote a reproduction test that simulated pool exhaustion and confirmed the leak. The fix was implementing proper connection lifecycle management with explicit cleanup in finally blocks.

**Result**: The fix eliminated the memory leak entirely - our production instances now run for weeks without memory growth. I documented the debugging approach in our runbook and added monitoring alerts for memory growth patterns. I also added integration tests that simulate high-load scenarios. This bug taught me the value of production-grade profiling tools and the importance of reproducing issues in controlled environments before attempting fixes.""",
    ),
    # Additional BEHAVIORAL HARD questions
    Question(
        content="Describe a time when you had to lead a team through a crisis or major setback.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        company_tags=["Amazon", "Netflix", "enterprise"],
        topic_tags=["crisis_management", "leadership", "resilience"],
        sample_answer="""**Situation**: Our primary database experienced a catastrophic failure during Black Friday - our highest traffic day. We lost 4 hours of transaction data, and the site was down. The team was panicking, leadership was demanding updates every 5 minutes, and customers were flooding social media with complaints.

**Task**: As the engineering lead, I needed to restore service, recover data, manage the team's stress, and coordinate communication - all simultaneously.

**Action**: I immediately established a clear command structure. I assigned one person to external communication only, freeing others to focus. I broke the crisis into parallel workstreams: one team on database restoration, one on data recovery from logs, one on customer impact assessment. I enforced 30-minute check-ins instead of constant interruptions and insisted team members take 15-minute breaks every 2 hours - exhausted engineers make mistakes. I remained visibly calm even when I wasn't, because I knew the team was looking to me for cues. I also made the call to focus on service restoration first, data recovery second.

**Result**: We restored service in 6 hours (vs. the 24+ it could have taken with panic-driven decisions). We recovered 95% of lost transactions from application logs. Post-mortem, we implemented database replication that would have prevented the issue. My manager highlighted my crisis leadership in my review, and I was asked to create a crisis response playbook for the team. I learned that in a crisis, your job is to reduce chaos, not solve every problem yourself.""",
    ),
    Question(
        content="Tell me about a time you had to balance technical excellence with business constraints.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        company_tags=["Google", "Meta", "Stripe"],
        topic_tags=["tradeoffs", "pragmatism", "business_acumen"],
        sample_answer="""**Situation**: We had 8 weeks to build a payment integration for a major enterprise client. Doing it "right" with full abstraction, comprehensive test coverage, and clean architecture would take 12 weeks. But this deal was worth $2M annually.

**Task**: I needed to find the right balance between shipping on time and not creating an unmaintainable mess that would cost us more in the long run.

**Action**: I identified which aspects of technical excellence were non-negotiable (security, data integrity, core error handling) versus which could be deferred (abstraction, edge case handling, full test coverage). I created a "technical debt budget" - we could cut corners, but I documented exactly what was cut and estimated the cost to fix later. I negotiated with stakeholders: we'd ship an MVP in 8 weeks, but the contract should include a post-launch optimization phase. I implemented the critical paths with high quality and used simpler solutions for less critical paths.

**Result**: We shipped on time and won the client. The technical debt I had documented was paid down over the following quarter without incident. The client has since expanded their contract twice. My approach of "explicit debt with a payoff plan" became a template for similar time-constrained projects. I learned that technical excellence isn't absolute - it's about making conscious tradeoffs and being honest about them.""",
    ),
    Question(
        content="Describe a situation where you had to mentor or develop a struggling team member.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        company_tags=["Microsoft", "Amazon", "Apple"],
        topic_tags=["mentoring", "leadership", "people_development"],
        sample_answer="""**Situation**: A mid-level engineer on my team was consistently missing deadlines and producing code that required significant rework. Other team members had started avoiding collaborating with them, and their confidence was visibly declining.

**Task**: I needed to help this engineer improve their performance while preserving their dignity and keeping them engaged - or help them transition out gracefully if improvement wasn't possible.

**Action**: I started with a candid but supportive conversation, asking open-ended questions about what was happening. I learned they were overwhelmed by the codebase complexity and afraid to ask for help. I created a structured improvement plan together - not imposed. We identified specific skills gaps and set bi-weekly milestones. I paired with them on their next feature, modeling how I approach unfamiliar code. I gave frequent, specific feedback - both positive and constructive. I also assigned them a smaller, well-defined project where they could succeed and rebuild confidence.

**Result**: Over 3 months, their code quality improved dramatically. They started asking questions proactively and even began helping newer team members. Their deadline adherence went from 60% to 95%. At their year-end review, they were promoted. They later told me it was a turning point in their career. I learned that underperformance often has underlying causes that standard performance management misses - and that investing in people can yield remarkable returns.""",
    ),
    Question(
        content="Tell me about a time you had to make an unpopular decision and stand by it.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        company_tags=["Netflix", "startup", "enterprise"],
        topic_tags=["decision_making", "courage", "conviction"],
        sample_answer="""**Situation**: Our team had been using a homegrown testing framework that everyone loved but that had become a maintenance burden. I determined that we needed to migrate to a standard framework, which would require rewriting 2,000+ tests. The team was strongly opposed - they had invested years in the current framework.

**Task**: I needed to make and defend a decision that I believed was right for the long term, even though it was deeply unpopular with the team.

**Action**: I was transparent about my reasoning and open about the costs. I created a detailed analysis showing: 80 hours/quarter spent on framework maintenance, increasing difficulty hiring engineers familiar with our custom tools, and growing incompatibility with modern testing patterns. I also acknowledged what we'd lose - some custom features the team valued. I offered to lead the migration myself and committed to preserving the most valuable custom functionality. I gave the team space to voice concerns and genuinely considered them, but ultimately stood firm when I believed the data supported my decision.

**Result**: The migration took 6 weeks, and initial sentiment was negative. But within 3 months, the team saw the benefits: faster CI runs, better IDE integration, and no more framework maintenance. Several team members thanked me for "ripping off the bandaid." I learned that leadership sometimes means making decisions that serve long-term health even when they're short-term unpopular - but you must do so transparently and be willing to own the consequences.""",
    ),
    Question(
        content="Describe the most complex cross-functional project you've led or been a key part of.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        company_tags=["Google", "Amazon", "Meta"],
        topic_tags=["cross_functional", "collaboration", "complexity"],
        sample_answer="""**Situation**: Our company decided to implement GDPR compliance across all systems - a project touching every product, database, and process. I was asked to lead the technical implementation coordinating with legal, product, marketing, customer support, and 8 engineering teams across 3 time zones.

**Task**: I needed to coordinate a company-wide initiative with hard legal deadlines, multiple stakeholders with different priorities, and significant technical complexity - all while teams continued their regular work.

**Action**: I started by creating a shared understanding: I organized a kickoff with all stakeholders to align on requirements and constraints. I created a central project tracker visible to everyone, breaking work into team-specific deliverables with clear dependencies. I established weekly cross-functional syncs and created a Slack channel for quick questions. To manage competing priorities, I worked with each team lead to integrate GDPR work into their existing sprints rather than treating it as separate. I identified and escalated blockers early, and I maintained a risk register that I reviewed with leadership bi-weekly.

**Result**: We achieved GDPR compliance two weeks before the deadline with zero legal findings in subsequent audits. The project required changes across 23 services and coordination with 40+ people. Leadership highlighted the project as a model for future cross-functional initiatives. I learned that the key to cross-functional success is creating shared visibility, respecting each team's constraints, and being the "connective tissue" that keeps information flowing.""",
    ),
    Question(
        content="Tell me about a time you identified and addressed a significant risk to a project.",
        category=QuestionCategory.BEHAVIORAL,
        difficulty=Difficulty.HARD,
        company_tags=["Apple", "Microsoft", "Uber"],
        topic_tags=["risk_management", "foresight", "proactive"],
        sample_answer="""**Situation**: We were 3 weeks into a 12-week project to migrate from a monolithic database to a microservices architecture. While reviewing the migration plan, I noticed that our planned cutover strategy assumed near-zero downtime, but we had never tested failover under realistic data volumes.

**Task**: I needed to validate whether this risk was real, quantify its potential impact, and propose mitigation - all without derailing the project timeline.

**Action**: I carved out 2 days to set up a production-like environment and ran migration tests at scale. The results were alarming: actual migration time was 4x our estimate due to data validation bottlenecks. I documented the risk with evidence and presented three mitigation options to leadership: (1) accept planned downtime of 6 hours, (2) invest 3 weeks in a parallel-write system for zero-downtime migration, or (3) use a phased migration over 2 weeks. I quantified the cost of each option in engineering time versus customer impact.

**Result**: Leadership chose the phased migration approach. We added 2 weeks to the timeline but avoided what would have been a catastrophic 6-hour production outage affecting thousands of customers. The project ultimately succeeded, and my manager credited early risk identification with saving the project. I now schedule "risk review" checkpoints in every major project, and this has become a team practice.""",
    ),

    # ========== TECHNICAL QUESTIONS (20 total) ==========
    Question(
        content="Implement a function to detect cycles in a linked list.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        company_tags=["Google", "Amazon", "Microsoft"],
        topic_tags=["linked_list", "algorithms", "two_pointers"],
    ),
    Question(
        content="Explain the difference between optimistic and pessimistic locking.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["enterprise", "Oracle", "Microsoft"],
        topic_tags=["databases", "transactions", "concurrency"],
    ),
    Question(
        content="Write a function to find the longest palindromic substring in a given string.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Amazon", "Meta", "Google"],
        topic_tags=["strings", "dynamic_programming", "algorithms"],
    ),
    Question(
        content="Implement a LRU (Least Recently Used) cache with O(1) operations.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        company_tags=["Google", "Amazon", "Microsoft"],
        topic_tags=["data_structures", "hashmap", "linked_list", "caching"],
    ),
    Question(
        content="Given a binary tree, write a function to serialize and deserialize it.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        company_tags=["Google", "Meta", "Amazon"],
        topic_tags=["trees", "recursion", "serialization", "dfs"],
    ),
    Question(
        content="Find the kth largest element in an unsorted array.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Amazon", "Microsoft", "Apple"],
        topic_tags=["arrays", "heap", "quickselect", "sorting"],
    ),
    Question(
        content="Implement a function to reverse a linked list iteratively and recursively.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        company_tags=["Google", "Amazon", "startup"],
        topic_tags=["linked_list", "recursion", "iteration"],
    ),
    Question(
        content="Given an array of integers, find all triplets that sum to zero.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Meta", "Amazon", "Bloomberg"],
        topic_tags=["arrays", "two_pointers", "sorting", "algorithms"],
    ),
    Question(
        content="Implement a function to validate if a binary tree is a valid binary search tree.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Microsoft", "Amazon"],
        topic_tags=["trees", "bst", "recursion", "validation"],
    ),
    Question(
        content="Write a function to merge k sorted linked lists into one sorted list.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        company_tags=["Google", "Amazon", "Uber"],
        topic_tags=["linked_list", "heap", "merge_sort", "divide_conquer"],
    ),
    Question(
        content="Implement a function to find the minimum window substring containing all characters of a pattern.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        company_tags=["Google", "Amazon", "Meta"],
        topic_tags=["strings", "sliding_window", "hashmap", "two_pointers"],
    ),
    Question(
        content="Given a 2D matrix, find the maximum path sum from top-left to bottom-right.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Amazon", "Microsoft", "Apple"],
        topic_tags=["dynamic_programming", "matrix", "path_finding"],
    ),
    Question(
        content="Implement a function to detect if two strings are anagrams of each other.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        company_tags=["Amazon", "startup", "Meta"],
        topic_tags=["strings", "hashmap", "sorting"],
    ),
    Question(
        content="Write a function to find the longest increasing subsequence in an array.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Microsoft", "Netflix"],
        topic_tags=["dynamic_programming", "arrays", "algorithms"],
    ),
    Question(
        content="Implement a trie (prefix tree) with insert, search, and startsWith operations.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Amazon", "Microsoft"],
        topic_tags=["trees", "trie", "data_structures", "strings"],
    ),
    Question(
        content="Given a graph, implement depth-first search (DFS) and breadth-first search (BFS).",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        company_tags=["Meta", "Google", "Amazon"],
        topic_tags=["graphs", "dfs", "bfs", "traversal"],
    ),
    Question(
        content="Find the median of two sorted arrays in O(log(m+n)) time complexity.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        company_tags=["Google", "Amazon", "Microsoft"],
        topic_tags=["arrays", "binary_search", "divide_conquer", "algorithms"],
    ),
    Question(
        content="Implement a function to rotate a matrix 90 degrees clockwise in-place.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Amazon", "Microsoft", "Apple"],
        topic_tags=["matrix", "arrays", "in_place_algorithms"],
    ),
    Question(
        content="Write a function to find all permutations of a given string.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Meta", "startup"],
        topic_tags=["strings", "backtracking", "recursion", "permutations"],
    ),
    Question(
        content="Implement Dijkstra's algorithm to find the shortest path in a weighted graph.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        company_tags=["Google", "Amazon", "Uber"],
        topic_tags=["graphs", "algorithms", "shortest_path", "heap"],
    ),
    # ========== ADDITIONAL TECHNICAL QUESTIONS (30 more to reach 50 total) ==========
    # Concurrency & Multithreading (6 questions)
    Question(
        content="Explain the difference between threads and processes. When would you use one over the other?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        company_tags=["Google", "Microsoft", "Amazon"],
        topic_tags=["concurrency", "operating_systems", "multithreading"],
    ),
    Question(
        content="Implement a thread-safe singleton pattern in your preferred language.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Amazon", "Microsoft", "enterprise"],
        topic_tags=["design_patterns", "concurrency", "synchronization"],
    ),
    Question(
        content="What is a deadlock? How would you detect and prevent deadlocks in a multi-threaded application?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Amazon", "Oracle"],
        topic_tags=["concurrency", "deadlock", "debugging"],
    ),
    Question(
        content="Implement a producer-consumer queue with proper synchronization.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        company_tags=["Microsoft", "Amazon", "Netflix"],
        topic_tags=["concurrency", "queues", "synchronization", "threads"],
    ),
    Question(
        content="Explain the difference between mutex, semaphore, and monitor. Provide use cases for each.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Microsoft", "enterprise"],
        topic_tags=["concurrency", "synchronization", "operating_systems"],
    ),
    Question(
        content="Implement a read-write lock that allows multiple readers but only one writer.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        company_tags=["Amazon", "Google", "Oracle"],
        topic_tags=["concurrency", "locks", "synchronization"],
    ),
    # Database & SQL (6 questions)
    Question(
        content="Explain database normalization forms (1NF, 2NF, 3NF). When would you denormalize?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        company_tags=["enterprise", "Oracle", "Microsoft"],
        topic_tags=["databases", "normalization", "sql"],
    ),
    Question(
        content="Write a SQL query to find the second highest salary in an employees table.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        company_tags=["Amazon", "Microsoft", "startup"],
        topic_tags=["sql", "databases", "subqueries"],
    ),
    Question(
        content="Explain the difference between INNER JOIN, LEFT JOIN, RIGHT JOIN, and FULL OUTER JOIN with examples.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        company_tags=["enterprise", "Amazon", "Google"],
        topic_tags=["sql", "databases", "joins"],
    ),
    Question(
        content="Explain database indexing. How do B-trees work and when would you use different index types?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Amazon", "Oracle"],
        topic_tags=["databases", "indexing", "performance", "b_trees"],
    ),
    Question(
        content="What are ACID properties in databases? How does eventual consistency differ from strong consistency?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Amazon", "Google", "Netflix"],
        topic_tags=["databases", "acid", "consistency", "distributed_systems"],
    ),
    Question(
        content="Design a database schema for a social media platform with users, posts, comments, and likes.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Meta", "Twitter", "LinkedIn"],
        topic_tags=["databases", "schema_design", "sql"],
    ),
    # Web & API (6 questions)
    Question(
        content="Explain the differences between REST and GraphQL. When would you choose one over the other?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        company_tags=["Meta", "startup", "enterprise"],
        topic_tags=["api_design", "rest", "graphql"],
    ),
    Question(
        content="What is CORS and why is it important? How would you configure it for a production API?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        company_tags=["startup", "enterprise", "Amazon"],
        topic_tags=["security", "web", "api_design"],
    ),
    Question(
        content="Explain the HTTP request lifecycle. What happens when you type a URL in your browser?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Meta", "Amazon"],
        topic_tags=["networking", "http", "dns", "web"],
    ),
    Question(
        content="What are WebSockets? How do they differ from HTTP and when would you use them?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Slack", "Meta", "startup"],
        topic_tags=["websockets", "real_time", "networking"],
    ),
    Question(
        content="Explain OAuth 2.0 flow. How would you implement secure authentication for a mobile app?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Meta", "Okta"],
        topic_tags=["security", "authentication", "oauth"],
    ),
    Question(
        content="Design an API versioning strategy. What are the trade-offs between URL versioning, header versioning, and query parameter versioning?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Stripe", "Twilio", "enterprise"],
        topic_tags=["api_design", "versioning", "best_practices"],
    ),
    # Data Structures Advanced (6 questions)
    Question(
        content="Implement a hash table from scratch with collision handling using chaining.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Amazon", "Meta"],
        topic_tags=["data_structures", "hashmap", "implementation"],
    ),
    Question(
        content="Implement a min-heap from scratch with insert, extractMin, and heapify operations.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Microsoft", "Amazon"],
        topic_tags=["data_structures", "heap", "implementation"],
    ),
    Question(
        content="Implement a bloom filter and explain its use cases and trade-offs.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        company_tags=["Google", "Amazon", "Netflix"],
        topic_tags=["data_structures", "probabilistic", "bloom_filter"],
    ),
    Question(
        content="Implement a skip list and explain when you would use it over a balanced BST.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        company_tags=["Google", "Microsoft", "startup"],
        topic_tags=["data_structures", "skip_list", "probabilistic"],
    ),
    Question(
        content="Design and implement a circular buffer with thread-safe operations.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Amazon", "Microsoft", "Spotify"],
        topic_tags=["data_structures", "buffers", "concurrency"],
    ),
    Question(
        content="Implement a disjoint set (union-find) data structure with path compression and union by rank.",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Amazon", "Meta"],
        topic_tags=["data_structures", "union_find", "graphs"],
    ),
    # System & Performance (6 questions)
    Question(
        content="Explain memory management in your preferred language. How does garbage collection work?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Amazon", "enterprise"],
        topic_tags=["memory_management", "garbage_collection", "performance"],
    ),
    Question(
        content="What is a memory leak? How would you detect and debug memory leaks in production?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Microsoft", "Amazon", "Netflix"],
        topic_tags=["debugging", "memory_management", "performance"],
    ),
    Question(
        content="Explain the difference between stack and heap memory. When does stack overflow occur?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.EASY,
        company_tags=["Google", "Microsoft", "startup"],
        topic_tags=["memory_management", "operating_systems", "debugging"],
    ),
    Question(
        content="Profile and optimize a slow function. What tools and techniques would you use?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Netflix", "Google", "Amazon"],
        topic_tags=["performance", "profiling", "optimization"],
    ),
    Question(
        content="Explain cache invalidation strategies. How would you handle cache coherence in a distributed system?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        company_tags=["Amazon", "Google", "Meta"],
        topic_tags=["caching", "distributed_systems", "consistency"],
    ),
    Question(
        content="What are the CAP theorem and PACELC? How do they affect system design decisions?",
        category=QuestionCategory.TECHNICAL,
        difficulty=Difficulty.HARD,
        company_tags=["Google", "Amazon", "Netflix"],
        topic_tags=["distributed_systems", "cap_theorem", "consistency"],
    ),

    # ========== SYSTEM DESIGN QUESTIONS (25 total: 5 easy, 8 medium, 12 hard) ==========
    # EASY system design questions
    Question(
        content="Design a simple key-value store for a single machine.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.EASY,
        company_tags=["startup", "enterprise", "Google"],
        topic_tags=["system_design", "data_structures", "storage"],
    ),
    Question(
        content="Design a basic user authentication system.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.EASY,
        company_tags=["startup", "Amazon", "Microsoft"],
        topic_tags=["system_design", "security", "authentication"],
    ),
    Question(
        content="Design a simple task queue system.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.EASY,
        company_tags=["startup", "enterprise", "Uber"],
        topic_tags=["system_design", "queues", "async_processing"],
    ),
    Question(
        content="Design a basic caching layer for a web application.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.EASY,
        company_tags=["startup", "Google", "Meta"],
        topic_tags=["system_design", "caching", "performance"],
    ),
    Question(
        content="Design a simple blog platform with posts and comments.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.EASY,
        company_tags=["startup", "Medium", "WordPress"],
        topic_tags=["system_design", "databases", "crud"],
    ),
    # MEDIUM system design questions
    Question(
        content="Design a URL shortener service.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Amazon", "enterprise"],
        topic_tags=["system_design", "scalability", "distributed_systems"],
    ),
    Question(
        content="Design a real-time chat application like WhatsApp or Slack.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        company_tags=["Meta", "Slack", "Microsoft"],
        topic_tags=["real_time", "websockets", "scalability", "messaging"],
    ),
    Question(
        content="Design a rate limiter for an API gateway.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Amazon", "Google", "Stripe"],
        topic_tags=["rate_limiting", "distributed_systems", "algorithms"],
    ),
    Question(
        content="Design a distributed cache system like Redis or Memcached.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        company_tags=["Google", "Meta", "Netflix"],
        topic_tags=["caching", "distributed_systems", "consistency", "scalability"],
    ),
    Question(
        content="Design a notification service that supports push notifications, emails, and SMS.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Amazon", "Uber", "Airbnb"],
        topic_tags=["messaging", "scalability", "queues", "reliability"],
    ),
    Question(
        content="Design a payment processing system like Stripe or PayPal.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        company_tags=["Stripe", "PayPal", "Square"],
        topic_tags=["transactions", "security", "distributed_systems", "idempotency"],
    ),
    Question(
        content="Design a content delivery network (CDN).",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        company_tags=["Cloudflare", "Amazon", "Google"],
        topic_tags=["cdn", "caching", "distributed_systems", "edge_computing"],
    ),
    Question(
        content="Design a news feed system like Twitter or Facebook.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        company_tags=["Meta", "Twitter", "Instagram"],
        topic_tags=["feed_generation", "scalability", "caching", "fan_out"],
    ),
    Question(
        content="Design a video streaming platform like YouTube or Netflix.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        company_tags=["Netflix", "YouTube", "Amazon"],
        topic_tags=["streaming", "cdn", "scalability", "video_processing"],
    ),
    Question(
        content="Design a distributed key-value store.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        company_tags=["Amazon", "Google", "Meta"],
        topic_tags=["distributed_systems", "consistency", "partitioning", "replication"],
    ),
    Question(
        content="Design an autocomplete or typeahead system.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Google", "Amazon", "Microsoft"],
        topic_tags=["trie", "caching", "scalability", "search"],
    ),
    Question(
        content="Design a ride-sharing service like Uber or Lyft.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        company_tags=["Uber", "Lyft", "Google"],
        topic_tags=["geospatial", "real_time", "matching", "scalability"],
    ),
    Question(
        content="Design a search engine like Google.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        company_tags=["Google", "Microsoft", "Amazon"],
        topic_tags=["search", "indexing", "ranking", "distributed_systems"],
    ),
    Question(
        content="Design a distributed task scheduler.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Amazon", "Airbnb", "Uber"],
        topic_tags=["scheduling", "queues", "distributed_systems", "reliability"],
    ),
    Question(
        content="Design a file storage system like Dropbox or Google Drive.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        company_tags=["Dropbox", "Google", "Microsoft"],
        topic_tags=["storage", "sync", "distributed_systems", "versioning"],
    ),
    Question(
        content="Design an API gateway for a microservices architecture.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Amazon", "Netflix", "Uber"],
        topic_tags=["api_gateway", "microservices", "routing", "load_balancing"],
    ),
    Question(
        content="Design a recommendation system like Amazon or Netflix uses.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        company_tags=["Amazon", "Netflix", "YouTube"],
        topic_tags=["machine_learning", "scalability", "personalization", "batch_processing"],
    ),
    Question(
        content="Design a logging and monitoring system.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Datadog", "Splunk", "Google"],
        topic_tags=["logging", "monitoring", "time_series", "scalability"],
    ),
    Question(
        content="Design a distributed database with strong consistency guarantees.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.HARD,
        company_tags=["Google", "Amazon", "CockroachDB"],
        topic_tags=["databases", "consistency", "distributed_systems", "consensus"],
    ),
    Question(
        content="Design a social media analytics dashboard.",
        category=QuestionCategory.SYSTEM_DESIGN,
        difficulty=Difficulty.MEDIUM,
        company_tags=["Meta", "Twitter", "LinkedIn"],
        topic_tags=["analytics", "real_time", "aggregation", "scalability"],
    ),
]


async def seed_questions(session) -> None:
    """Insert seed questions if none exist."""
    from sqlmodel import select

    existing = await session.exec(select(Question))
    if existing.first():
        return
    session.add_all(SEED_QUESTIONS)
    await session.commit()
