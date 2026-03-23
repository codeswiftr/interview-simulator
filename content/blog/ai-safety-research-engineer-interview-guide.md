---
title: "AI Safety Research Engineer Interview Guide"
description: "Technical interview preparation for AI safety research engineering roles at Anthropic, DeepMind, ARC Evals, METR, and safety-focused teams at OpenAI: interpretability, alignment research infrastructure, evaluation engineering, and red-teaming."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

AI safety engineering is not the same as AI safety research. Researchers develop theories, run experiments, and write papers. Engineers build the infrastructure that makes that research possible: evaluation frameworks, interpretability tooling, red-teaming pipelines, monitoring systems, and model analysis platforms. If you are an ML engineer considering a pivot into safety work, this is the distinction that matters most going into interviews.

## The Landscape: Who Is Hiring

The safety-focused orgs with active engineering roles as of early 2026:

**Anthropic** — Interpretability (mechanistic analysis of transformer internals), red-teaming (systematic probing for harmful behaviors and policy violations), Constitutional AI infrastructure, and the evals team that measures model behavior against safety-relevant metrics.

**DeepMind Safety** — Specification research (reward modeling, scalable oversight), robustness, and alignment-adjacent infrastructure embedded across research teams.

**ARC Evals / METR** — Now operating as METR, this team focuses specifically on dangerous capability evaluations: autonomous replication and adaptation (ARA), persuasion, and deception evals. Their engineering roles involve building rigorous measurement systems for capabilities that should not exist yet.

**Apollo Research**, **Redwood Research**, **Center for AI Safety** — Smaller teams, often more research-adjacent, but with real infrastructure needs. Redwood in particular has done significant interpretability and adversarial training work requiring strong engineering support.

## Four Technical Domains You Need to Know

### Interpretability Engineering

This means building tools to understand what is happening inside neural networks. Concretely: activation patching (intervening on model internals to trace causal pathways), circuit discovery (finding the minimal subgraph of a network responsible for a specific behavior), and sparse autoencoders (decomposing residual stream activations into interpretable features, as in Anthropic's Scaling Monosemanticity work).

The engineering requirements are specific: deep PyTorch internals, hooks and forward-pass manipulation, tensor shape bookkeeping across attention layers, and visualization infrastructure for communicating findings. If you have not read Anthropic's Toy Models of Superposition and Scaling Monosemanticity papers, do that before any interpretability interview. Then implement a basic activation patching experiment on a small transformer — not to show the result, but to demonstrate you understand what you are actually measuring.

### Evaluation Engineering

Evals for safety are not benchmarks. They are adversarial test cases designed to measure specific dangerous capabilities: can this model assist in acquiring dangerous biological materials? Can it replicate itself across infrastructure? Does it behave differently when it believes it is being evaluated?

Building these requires adversarial thinking (you need to want the model to fail), statistical rigor (false negatives matter more than false positives here), and systematic red-teaming methodology. METR's approach to ARA evals is worth studying as a concrete example of how this is done at the frontier.

### RLHF and Alignment Infrastructure

Models do not become safer on their own. Building RLHF pipelines, DPO training infrastructure, Constitutional AI self-critique loops, and reward model training systems is engineering work with safety-specific requirements. The difference from standard ML engineering: your training pipeline needs to handle adversarial prompts, your reward model needs to be robust to distribution shift, and your data pipeline decisions have direct implications for model behavior in deployment.

The skills are similar to ML platform engineering, but the threat model is different. Interviewers will probe whether you understand why those differences matter.

### Red-Teaming

Systematic model probing occupies a middle ground between research and operations. Good red-teaming requires creative adversarial thinking to find failure modes, plus measurement infrastructure to quantify them reliably. Jailbreaks matter, but what interviewers at safety orgs care more about is deceptive alignment — does the model behave differently in contexts where it believes oversight is relaxed? Building detection infrastructure for that is an open research problem, and being able to discuss your approach coherently is valuable.

## What the Interview Process Actually Looks Like

Expect four to five rounds at most orgs:

**Research paper discussion** — You will be asked to discuss a safety or interpretability paper in depth. Not summarize it: discuss it. What are the limitations? What would the next experiment be? Where might the conclusions fail to generalize? Prepare two or three papers you can discuss at this level.

**Coding** — Python and PyTorch. Expect transformer internals questions, not LeetCode. Implement a thing, explain what it does at the tensor level.

**Open-ended research discussion** — "How would you design an evaluation for deceptive alignment?" There is no right answer. The interviewer wants to see how you think through an underspecified problem with real stakes.

**Values and motivations discussion** — This is not a formality. Safety orgs do genuinely assess whether you understand the problem and have thought seriously about it. Interviewers at these organizations talk to a lot of candidates, and surface-level interest is easy to detect. You do not need to be an AI doomer, but you need to have an actual view and be able to defend it.

## Breaking In Without a Safety Background

The most direct path is contributing to open interpretability research. The TransformerLens library, Neel Nanda's open problems list, and Alignment Forum are active communities where you can publish small projects and get feedback. Building a small LLM evaluation framework, even on toy tasks, demonstrates the relevant engineering skills more concretely than claims of interest.

Write about safety topics technically, not philosophically. A blog post implementing activation patching on GPT-2 is more useful to your candidacy than an essay about why safety matters.

Prior work on alignment-adjacent problems — robustness, anomaly detection, interpretability in other domains — transfers better than it might seem. The core skill is building rigorous measurement systems for hard-to-define properties, and that generalizes.

One practical note: most safety engineering roles require working with closed-weight models through APIs, not just open-weight ones. Familiarity with evaluation infrastructure that works at the API level, without access to internals, is increasingly relevant.
