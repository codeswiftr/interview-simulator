---
title: "DoorDash Engineering Deep Dive: Logistics, Marketplace, and Real-Time Systems"
description: "What DoorDash's engineering team builds — marketplace matching, real-time logistics, restaurant integrations, and delivery optimization — and what their technical interviews focus on."
date: "2026-03-19"
category: "Company Deep Dives"
---

# DoorDash Engineering Deep Dive: Logistics, Marketplace, and Real-Time Systems

DoorDash is the US market leader in food delivery, with engineering challenges that span real-time marketplace matching, logistics optimization, restaurant POS integrations, financial infrastructure for millions of transactions, and increasingly a platform business (DoorDash Drive, Wolt). For engineers interested in marketplace systems, real-time logistics, or the complexity of coordinating a three-sided marketplace (customers, dashers, merchants), DoorDash is technically compelling.

## The Three-Sided Marketplace Problem

Most marketplace systems are two-sided: buyers and sellers. DoorDash coordinates three parties simultaneously: customers who want food, Dashers who want delivery work, and merchants who want orders. Matching a customer order to a Dasher, routing the Dasher optimally through pickup and dropoff, and managing the real-time status across all three parties requires a tightly integrated set of systems.

**Dispatch and matching**: When an order is placed, DoorDash's dispatch system must assign it to a Dasher. This is an optimization problem: minimize delivery time while considering Dasher proximity, current workload, and restaurant prep time. The system runs continuously, reassigning orders if better matches become available. This is essentially a real-time constrained optimization problem at scale.

**ETA prediction**: Customer experience depends heavily on accurate delivery time estimates. DoorDash's ML models predict restaurant prep time, Dasher drive time (accounting for traffic, weather, restaurant wait times), and handoff delays. Getting these estimates right requires continuous model retraining on real delivery outcomes.

**Merchant integration**: DoorDash integrates with hundreds of POS systems (Square, Toast, Olo) to receive orders programmatically. Building reliable, real-time integrations with a fragmented ecosystem of POS providers is an unsexy but critical engineering challenge.

## Tech Stack and Architecture

DoorDash runs primarily on Kotlin/Java (backend services), with Go for high-performance services. PostgreSQL is the primary database; Kafka is the event streaming backbone; Redis for real-time caching. They run on AWS and have invested significantly in their internal data infrastructure.

DoorDash has open-sourced several internal tools, including their Workflow Engine (for complex order state machines) and various data infrastructure components.

## Interview Focus Areas

**Real-time systems design**: Expect questions like "Design a real-time food delivery dispatch system" or "How would you build a live order tracking system?" Strong answers cover: how order state is managed, how Dashers receive and update their status, how the customer-facing ETA is computed and refreshed, and how the system handles failures (Dasher goes offline, restaurant closes unexpectedly).

**Marketplace and matching algorithms**: "How would you design a matching algorithm for drivers and orders?" is a direct DoorDash question. Expected depth: discuss the optimization criteria (minimize delivery time, maximize Dasher utilization), the constraints (Dasher capacity, geographic proximity), and practical implementation trade-offs (running exact optimization vs heuristic approaches at real-time latency requirements).

**Data and ML systems**: DoorDash uses ML extensively — for ETA prediction, fraud detection, menu item recommendations, and dynamic pricing. For ML-adjacent roles, system design questions often involve "Design a pipeline for training and serving real-time delivery time predictions."

## Behavioral Themes

DoorDash's culture emphasizes:
- **Moving with urgency**: DoorDash competed intensely against Uber Eats and Grubhub; engineers who operated under pressure and shipped quickly are valued
- **Low ego, high ownership**: Their values explicitly include "be a 10x teammate" and low-ego collaboration
- **Customer and Dasher empathy**: Both the customer experience and Dasher experience matter — framing your work in terms of impact on both groups is culturally resonant
