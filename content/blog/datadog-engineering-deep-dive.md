# Datadog Engineering Deep Dive: Observability at Trillion-Point Scale

Datadog sits at a peculiar intersection of infrastructure: it must process more data than almost any system on Earth, in real time, with sub-second latency, while running inside the infrastructure of every major cloud provider simultaneously. The result is a company whose engineering problems are genuinely novel — not variations on familiar patterns, but original solutions to constraints that did not exist a decade ago. Understanding how Datadog built its platform, and why its engineers made the decisions they did, is essential preparation for anyone pursuing a role there.

## Time-Series Metrics Ingestion: Custom Storage Under Extreme Load

Datadog ingests trillions of data points per day. That number is worth sitting with for a moment. A typical large-scale analytics platform handles billions of events. Datadog handles thousands of times more, in real time, with query response times measured in seconds.

The naive approach — write raw metric samples to a general-purpose database — fails quickly. Time-series data has properties that make generic storage pathologically inefficient: values arrive in strict timestamp order, the most recent data is queried most frequently, and long-term storage can tolerate lossy compression that databases designed for exact-match queries cannot apply.

Datadog's storage layer is built on top of Apache Cassandra but heavily customized. Cassandra's wide-row model maps naturally to time-series data: metric name and tags form the partition key, timestamps become clustering columns, and values pack densely into a single wide row. This layout ensures that queries for a metric over a time range perform sequential reads rather than random I/O — critical at this volume.

The more technically interesting innovation is DDSketch, Datadog's algorithm for approximate percentile computation. Computing exact percentiles (p50, p95, p99) requires storing every data point and sorting them — impossible when you're ingesting billions of samples per metric per day. DDSketch maintains a compact sketch data structure using logarithmically spaced buckets that guarantee relative error bounds: a DDSketch with 1% relative accuracy will report a value within 1% of the true percentile, regardless of the data distribution. The sketch is mergeable — you can combine sketches from multiple hosts without loss of accuracy guarantees — which enables distributed percentile computation without a central aggregation bottleneck. For interviews, understanding why exact percentiles are infeasible at scale and how sketch-based approximations restore tractability is a common system design discussion.

## Distributed Tracing: APM Architecture and the Sampling Problem

Datadog APM implements distributed tracing — the ability to follow a single user request through every service, database call, and external API invocation it touches. The core challenge is scale: in a large microservices deployment, every request generates a trace consisting of potentially hundreds of spans. Capturing everything would generate more data than the metrics pipeline; capturing nothing defeats the purpose.

The Datadog trace agent runs as a sidecar process on every monitored host. Rather than sending raw spans directly to the backend, the trace agent makes local sampling decisions and performs span aggregation before transmission. This design is crucial: it means the backend never sees traffic proportional to request volume — it sees traffic proportional to the sampled subset, plus aggregated statistics computed locally.

Datadog implements both head-based and tail-based sampling strategies, and understanding the tradeoff is directly relevant to system design interviews. Head-based sampling decides at the start of a trace whether to capture it. This is simple and cheap — the decision propagates through the system via trace context headers, so all services agree on whether a given trace is sampled. The problem is that head-based sampling cannot preferentially retain interesting traces: an error that manifests at the fifth service in a chain is sampled at the same rate as a successful request, with no way to know upfront that it will be interesting.

Tail-based sampling holds spans in a buffer until the trace is complete, then makes a sampling decision based on the full trace. This allows error traces and high-latency outliers to be captured at 100% while routine successful requests are sampled at low rates. The cost is memory and latency: you must buffer incomplete traces waiting for their final spans, and you must handle the case where spans from a single trace arrive at different collector instances. Datadog's Tracing Without Limits feature implements adaptive sampling at the agent level, using a variant of this approach.

The observability platform's core value proposition is correlation between the three pillars — metrics, traces, and logs — without requiring manual join keys. Datadog achieves this by injecting trace and span IDs into log lines automatically (via APM auto-instrumentation) and by tagging metrics with the service and resource names that appear in traces. A spike in error rate on a service metric links directly to the traces from that time window, which link to the log lines emitted during those requests.

## The Datadog Agent: Go, Plugin Architecture, and Zero-Config Ambition

The Datadog Agent is open source (Apache 2.0), written in Go, and runs on every monitored host in the infrastructure. It is one of the most widely deployed pieces of software in the industry that most engineers have never studied.

Go was chosen deliberately: it compiles to a single static binary with no runtime dependencies, starts quickly, consumes predictable memory, and handles concurrency cleanly via goroutines. A monitoring agent that causes measurable overhead on the systems it monitors is self-defeating — the agent must be essentially invisible.

The agent's plugin architecture supports over 600 integrations: databases, web servers, message queues, cloud services, container runtimes, and custom applications. Each integration is a Go package implementing a standard check interface — a `Run()` method that collects metrics and emits them to the agent's aggregator. The aggregator handles timestamp alignment, rate computation, and local pre-aggregation before flushing to the Datadog backend at 15-second intervals.

The zero-configuration ambition is architecturally interesting. In containerized environments, services start and stop constantly. The agent uses Kubernetes API watch streams and Docker event streams to detect new containers and automatically apply relevant integrations based on image labels, annotations, and known service fingerprints. A container running MySQL with a standard image name will have MySQL metrics collected without any manual configuration — the agent infers what is running and applies the correct integration. This requires solving service discovery in environments where the topology changes continuously and no single source of truth exists.

Serverless monitoring presents a different problem: there is no persistent host to run an agent on. Datadog addresses this via a Lambda extension — a separate execution environment that runs alongside the function, collects invocation metrics and logs, and flushes them synchronously before the function's execution context is frozen. The extension must complete its flush within the Lambda's shutdown hook window, which imposes strict latency constraints on the telemetry pipeline.

## Real User Monitoring: Browser SDK, Session Replay, and Privacy

Datadog RUM (Real User Monitoring) captures performance data from actual end-user browsers rather than synthetic tests run from Datadog infrastructure. The browser SDK is a small JavaScript bundle injected into pages that automatically instruments navigation timing, resource loading, Core Web Vitals (LCP, FID, CLS), JavaScript errors, and custom user actions.

Session Replay is the technically distinctive feature. Rather than recording video of user sessions — which would require enormous bandwidth and raise obvious privacy concerns — Datadog captures DOM mutations as a structured event stream. The SDK uses a MutationObserver to record every change to the page's document object model: nodes added or removed, attribute changes, text content modifications. These events are timestamped and serialized compactly. Replay reconstructs the session by replaying the event stream against the initial page snapshot, effectively re-simulating the session in a sandboxed iframe.

This architecture has significant advantages. The event stream is far smaller than video: a typical session generates kilobytes of mutation events rather than megabytes of compressed video frames. The structured format is queryable — you can ask "show me sessions where users encountered a specific error" or "find sessions where the checkout button was clicked but no purchase was completed" using structured queries against the event data rather than frame-by-frame video analysis.

The privacy challenge is substantial. Session replay captures what users actually type, see, and interact with. Datadog's SDK includes several privacy controls: automatic masking of input fields (particularly password and card number inputs), configurable masking rules for elements containing PII, and privacy modes that mask all text content by default except for explicitly allowlisted elements. Sampling is built into the SDK — replay is typically enabled for a fraction of sessions to balance insight against storage cost and user privacy risk.

## Interview Implications: Culture, System Design, and What Datadog Evaluates

Datadog's engineering culture is shaped by the observability domain. Engineers must care deeply about correctness and reliability — a monitoring platform that gives wrong answers under load is worse than no monitoring at all, because it creates false confidence. The cultural emphasis on rigor in measurement reflects this.

The backend is Go-heavy, consistent with the industry trend toward Go for infrastructure and platform work. Frontend engineering (particularly for dashboards, the notebook interface, and session replay playback) uses TypeScript. Infrastructure work (agent, trace agent, log agent) is almost exclusively Go.

System design questions at Datadog tend to be directly relevant to the domain. Common prompts include:

Design a metrics ingestion system that handles one trillion data points per day. This question tests your understanding of write path design, the tradeoff between exact and approximate representations, cardinality constraints (high-cardinality tag values that explode storage), and query path optimization. Strong answers discuss time-series specific storage, pre-aggregation, and DDSketch-style approximations for percentiles.

Design a distributed tracing system. This question centers on the sampling problem, span collection architecture, and trace-metric correlation. The interviewer will probe your understanding of head-based vs. tail-based sampling tradeoffs and how you handle the case where a trace spans services deployed across different availability zones or cloud providers.

Design a monitoring alerting system. This question covers alert evaluation at scale (you cannot re-query all metrics every minute), anomaly detection approaches, alert noise reduction (flap detection, alert grouping), and notification delivery guarantees. Strong candidates discuss the difference between threshold-based alerting and statistical anomaly detection.

What Datadog evaluates consistently is the ability to reason about scale, failure modes, and measurement tradeoffs. The company's products live or die on whether they work correctly when the infrastructure they monitor is under stress — exactly the moment when monitoring data is most valuable and most difficult to produce correctly. Engineers who can articulate the failure modes of their own designs, propose mitigations, and accept constraints gracefully are the profile that succeeds here.

The preparation checklist for Datadog interviews: understand time-series data properties and why they require different storage strategies than relational data; know what DDSketch or similar quantile sketches are solving and why exact percentiles are infeasible at scale; understand distributed tracing context propagation (W3C TraceContext headers, how trace IDs flow through HTTP and async messaging); know the difference between push-based and pull-based metrics collection and the tradeoffs of each; understand cardinality as a concept in time-series monitoring and why it is the primary cost driver in metrics storage; and be able to design a rate limiter, a distributed counter, and a metrics aggregation pipeline from first principles.

Datadog has built infrastructure that most engineers interact with daily without thinking about it. The interviews reflect the depth of engineering required to make that invisibility possible.
