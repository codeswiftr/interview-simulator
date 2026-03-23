---
title: "Amsterdam Advanced Tech Guide: Booking.com, ASML, and the Netherlands' Tech Ecosystem"
description: "Deep dive into Amsterdam's senior engineering market — what Booking.com really interviews for, why ASML is unlike any other tech employer, and how to navigate the Dutch tech scene."
date: "2026-03-20"
category: "City Guides"
---

# Amsterdam Advanced Tech Guide: Booking.com, ASML, and the Netherlands' Tech Ecosystem

Amsterdam's tech market has a split personality that catches many candidates off guard. On one side, you have Booking.com — one of Europe's most sophisticated product engineering organizations, built on A/B testing culture and data-driven decision-making at enormous scale. On the other, ASML: a semiconductor equipment company that is arguably the most strategically important tech employer on the continent, and whose engineering culture is as far from Silicon Valley as you can get while still writing software.

Understanding both — and the ecosystem around them — is how you position yourself well in the Netherlands.

## Booking.com: What the Interview Actually Tests

Booking.com processes over 1.5 million room nights per day and runs one of the largest A/B testing infrastructures in the world. Their engineering culture is shaped by this: everything is measured, everything is iterated, and engineers are expected to own outcomes — not just code.

**The technical interview format:**

Senior roles at Booking.com go through a multi-stage loop that includes:

- A take-home or live coding challenge focused on practical problem-solving (less LeetCode-style, more "here's a real dataset — answer this question")
- A system design round where they probe specifically for scale and observability. They are not impressed by theoretical designs — they want to know how you'd instrument the system, detect failures, and roll back safely
- A "product thinking" round that surprises engineers used to pure technical interviews. You will be asked to propose experiments, define success metrics, and reason about user behavior

**What trips people up:** Engineers who can't articulate the difference between correlation and causality in A/B test results struggle here. Booking.com has a stats literacy expectation that is higher than most product companies. Brush up on statistical significance, p-values, and common experimental design pitfalls (novelty effect, network effects in social features, etc.).

**Compensation at Booking.com** for senior engineers runs approximately €100,000–145,000 base in Amsterdam. Total compensation is lower than FAANG but the role is genuinely impactful — your code ships to hundreds of millions of users quickly.

## ASML: The Most Important Tech Company Most Engineers Have Never Seriously Considered

ASML makes the EUV lithography machines that manufacture every advanced chip in the world — from Apple Silicon to Nvidia's H100. There is no alternative supplier. Their Veldhoven HQ (45 minutes from Amsterdam) and Amsterdam-area offices employ thousands of software engineers working on real-time embedded control systems, computational lithography, and increasingly, machine learning for process optimization.

**Why ASML is different:**

The engineering culture is Dutch/German industrial — rigorous, process-oriented, and deeply concerned with correctness over speed. This is not a move-fast-and-break-things environment. When software controls a machine that costs $200 million and manufactures chips that nothing can replace, "we'll fix it in the next release" is not an acceptable answer.

**The interview focus:**

- Real-time systems and embedded constraints (C++, RTOS concepts, determinism)
- Model-based design: ASML uses tools like MATLAB/Simulink for modeling; familiarity is valued
- Fault tolerance and safety-critical software patterns
- For computational lithography roles: numerical methods, linear algebra at scale, and Python/C++ hybrid codebases

**Compensation:** ASML pays well but not at FAANG levels. Senior engineers earn €90,000–130,000 base with strong pension and benefits. The draw is stability, technical depth, and the genuine uniqueness of the domain.

## The Broader Amsterdam Tech Ecosystem

Beyond the headline employers, Amsterdam hosts a dense cluster of strong engineering organizations:

**Adyen:** The payments processor is known for exceptional engineering quality and one of the most rigorous interview processes in the city. Expect deep systems questions on transaction processing, idempotency, and failure modes in payment flows. Compensation is competitive with FAANG for Amsterdam.

**Uber ATG (maps/routing):** Uber's Amsterdam office focuses on mapping and routing infrastructure. Graph algorithms, geospatial indexing, and real-time optimization problems feature prominently in interviews.

**TomTom:** Older than the Amsterdam startup scene but still technically interesting — their HD maps team works on problems relevant to autonomous vehicles.

**Startups:** Messagebird (now Bird), Mollie, and Picnic have grown into substantial engineering organizations. These tend to interview with a stronger startup sensibility — autonomy, broad scope, and shipping velocity.

## Work Permits and the 30% Ruling

The Netherlands offers the "30% ruling" for international employees: 30% of salary is paid tax-free for up to 5 years. For a senior engineer earning €130,000, this meaningfully increases take-home pay. Eligibility requires a salary above a threshold (approximately €46,000 in 2026) and that you were recruited from outside the Netherlands.

EU citizens have unrestricted work rights. Non-EU nationals need a "highly skilled migrant" permit (kennismigrant), which employers sponsor. Processing typically takes 2–4 weeks — significantly faster than most other European countries.

## Interview Preparation by Employer

**For Booking.com:**
- Practice experimental design questions: "How would you test whether feature X increases conversion?"
- Study their engineering blog — they publish extensively about their technical decisions
- Prepare to talk about a feature you shipped and how you measured its impact

**For ASML:**
- Brush up on C++ memory model, RAII, and real-time scheduling concepts
- If targeting computational lithography: review numerical methods and optimization techniques
- Emphasize correctness, process, and documentation in your behavioral answers

**For Adyen:**
- Study distributed transaction patterns: two-phase commit, idempotency keys, compensating transactions
- Payment system failure modes: network partitions, duplicate processing, eventual consistency

Amsterdam rewards engineers who do their homework on the employer's specific domain. The market is less homogenous than London or Berlin — knowing which interview style you're walking into makes a significant difference.
